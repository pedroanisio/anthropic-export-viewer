#!/usr/bin/env python3
"""
code-patch applier — deterministic executor for code-patch envelopes.

Usage:
    python apply_code_patch.py <source_file> <patch_json> [--dry-run] [--output-dir DIR]

Reads a source code file and a patch envelope JSON, creates a ULID-named
working copy, applies all operations sequentially, and outputs STATUS,
EXECUTION_REPORT, and LAST_STABLE.

Supported languages: python, javascript, typescript, rust, html, css
Protocol version: 1.0
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


# ---------------------------------------------------------------------------
# ULID-like ID generator (timestamp + random, no deps)
# ---------------------------------------------------------------------------

def generate_ulid() -> str:
    """Generate a ULID-like identifier (26 chars, Crockford base32)."""
    ENCODING = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
    t = int(time.time() * 1000)
    ts_part = ""
    for _ in range(10):
        ts_part = ENCODING[t & 0x1F] + ts_part
        t >>= 5
    rand_bytes = os.urandom(10)
    rand_int = int.from_bytes(rand_bytes, "big")
    rand_part = ""
    for _ in range(16):
        rand_part = ENCODING[rand_int & 0x1F] + rand_part
        rand_int >>= 5
    return ts_part + rand_part


# ---------------------------------------------------------------------------
# String state tracker (safe brace-counting for JS/TS/Rust/CSS)
# ---------------------------------------------------------------------------

class StringStateTracker:
    """
    Tracks string/comment parser state for safe brace-counting.
    Call feed(ch, next_ch) per character; returns True when the character
    is in a position where braces should be counted (not inside a
    string, comment, or template literal).
    """
    NORMAL = 0
    IN_STRING_SINGLE = 1
    IN_STRING_DOUBLE = 2
    IN_TEMPLATE = 3         # backtick template literal
    IN_TEMPLATE_EXPR = 4    # inside ${ } within a template
    IN_COMMENT_LINE = 5     # // …
    IN_COMMENT_BLOCK = 6    # /* … */

    def __init__(self) -> None:
        self.state = self.NORMAL
        self.template_depth = 0
        self.prev = ""

    def reset(self) -> None:
        self.state = self.NORMAL
        self.template_depth = 0
        self.prev = ""

    def feed(self, ch: str, next_ch: str = "") -> bool:
        """
        Process one character.  Returns True if this character is in a
        'counting' position.  Call feed('\n', '') at end of each line to
        terminate line comments.
        """
        s = self.state
        p = self.prev
        counting = s in (self.NORMAL, self.IN_TEMPLATE_EXPR)

        if s == self.IN_COMMENT_LINE:
            if ch == "\n":
                self.state = self.NORMAL
            counting = False
        elif s == self.IN_COMMENT_BLOCK:
            if p == "*" and ch == "/":
                self.state = self.NORMAL
            counting = False
        elif s == self.IN_STRING_SINGLE:
            if ch == "'" and p != "\\":
                self.state = self.NORMAL
            counting = False
        elif s == self.IN_STRING_DOUBLE:
            if ch == '"' and p != "\\":
                self.state = self.NORMAL
            counting = False
        elif s == self.IN_TEMPLATE:
            if ch == "`" and p != "\\":
                self.state = self.NORMAL
            elif ch == "{" and p == "$":
                self.template_depth += 1
                self.state = self.IN_TEMPLATE_EXPR
            counting = False
        elif s == self.IN_TEMPLATE_EXPR:
            if ch == "{":
                self.template_depth += 1
            elif ch == "}":
                self.template_depth -= 1
                if self.template_depth <= 0:
                    self.state = self.IN_TEMPLATE
                    self.template_depth = 0
                    counting = False  # closing } of template expr is not counted
        else:  # NORMAL
            if ch == "/" and next_ch == "/":
                self.state = self.IN_COMMENT_LINE
                counting = False
            elif ch == "/" and next_ch == "*":
                self.state = self.IN_COMMENT_BLOCK
                counting = False
            elif ch == "'":
                self.state = self.IN_STRING_SINGLE
                counting = False
            elif ch == '"':
                self.state = self.IN_STRING_DOUBLE
                counting = False
            elif ch == "`":
                self.state = self.IN_TEMPLATE
                counting = False

        self.prev = ch
        return counting

    def feed_line(self, line: str) -> None:
        """Feed a complete line (handles implicit newline)."""
        for i, ch in enumerate(line):
            self.feed(ch, line[i + 1] if i + 1 < len(line) else "")
        self.feed("\n", "")


def net_brace_depth(lines: list[str], start: int, end: int,
                    tracker: Optional[StringStateTracker] = None) -> int:
    """Count net `{` minus `}` depth over lines[start:end], respecting strings."""
    if tracker is None:
        tracker = StringStateTracker()
    depth = 0
    for i in range(start, end):
        line = lines[i]
        for j, ch in enumerate(line):
            nch = line[j + 1] if j + 1 < len(line) else ""
            if tracker.feed(ch, nch):
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
        tracker.feed("\n", "")
    return depth


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class Symbol:
    """A parsed symbol (function, class, import, rule …) from a source file."""
    kind: str           # function|class|method|import|interface|enum|struct|
                        # trait|impl|mod|rule|tag|type|variable
    name: str           # bare name
    qualified: str      # dotted qualified name, e.g. "MyClass.foo"
    decl_line: int      # line index of declaration start (0-based)
    decl_end: int       # last line of declaration (inclusive; same as decl_line for 1-liners)
    body_start: int     # first body line (after opening delimiter)
    body_end: int       # exclusive end of body
    prefix_start: int   # first line of decorators/attributes above declaration
    children: list[Symbol] = field(default_factory=list)


@dataclass
class OpResult:
    index: int
    success: bool
    error_type: Optional[str] = None
    detail: Optional[str] = None
    closest_match: Optional[str] = None


@dataclass
class ExecutionReport:
    patch_id: str
    file_id: str
    status: str
    apply_mode: str
    source_hash: str
    result_hash: Optional[str] = None
    applied_ops: list[int] = field(default_factory=list)
    skipped_ops: list[dict] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)
    goals_actual: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    working_copy_path: Optional[str] = None
    dry_run: bool = False

    def to_dict(self) -> dict:
        d: dict[str, Any] = {
            "patch_id": self.patch_id,
            "file_id": self.file_id,
            "status": self.status,
            "apply_mode": self.apply_mode,
            "source_hash": self.source_hash,
        }
        if self.result_hash is not None:
            d["result_hash"] = self.result_hash
        if self.status not in ("not_attempted", "envelope_error"):
            d["applied_ops"] = self.applied_ops
            d["skipped_ops"] = self.skipped_ops
        if self.errors:
            d["errors"] = self.errors
        if self.status in ("full_success", "partial_success", "no_change"):
            d["goals_actual"] = self.goals_actual
        d["warnings"] = self.warnings
        if self.working_copy_path:
            d["working_copy_path"] = self.working_copy_path
        if self.dry_run:
            d["dry_run"] = True
        return d


# ---------------------------------------------------------------------------
# Language profiles
# ---------------------------------------------------------------------------

# --- Python ---
_PY_DEF_RE = re.compile(r'^(\s*)(async\s+def|def|class)\s+(\w+)')
_PY_DECO_RE = re.compile(r'^\s*@')
_PY_IMPORT_RE = re.compile(r'^\s*(import\s+\w|from\s+\S)')


class LanguageProfile:
    """Base language profile. Subclasses override as needed."""
    name: str = "base"
    extensions: tuple[str, ...] = ()
    comment_single: str = "//"
    block_marker_open: str = "// BLOCK:{name}"
    block_end_marker: str = "// END BLOCK:{name}"
    anchor_marker: str = "// ANCHOR:{name}"

    def find_symbols(self, lines: list[str]) -> list[Symbol]:  # pragma: no cover
        return []

    def find_imports(self, lines: list[str]) -> list[Symbol]:  # pragma: no cover
        return []

    def import_insert_point(self, lines: list[str]) -> int:
        imports = self.find_imports(lines)
        return max((s.body_end for s in imports), default=0)

    def rename_in_decl(self, line: str, old_name: str, new_name: str) -> str:
        return re.sub(rf'\b{re.escape(old_name)}\b', new_name, line, count=1)

    def is_import_duplicate(self, lines: list[str], statement: str) -> bool:
        norm = _normalize_ws(statement)
        for sym in self.find_imports(lines):
            existing = " ".join(lines[sym.decl_line:sym.body_end])
            if _normalize_ws(existing) == norm:
                return True
        return False


class PythonProfile(LanguageProfile):
    name = "python"
    extensions = (".py", ".pyw")
    comment_single = "#"
    block_marker_open = "# BLOCK:{name}"
    block_end_marker = "# END BLOCK:{name}"
    anchor_marker = "# ANCHOR:{name}"

    def find_symbols(self, lines: list[str]) -> list[Symbol]:
        symbols: list[Symbol] = []
        n = len(lines)
        for i, line in enumerate(lines):
            m = _PY_DEF_RE.match(line)
            if not m:
                continue
            indent = len(m.group(1))
            kw = m.group(2).rstrip()
            name = m.group(3)
            kind = "class" if kw == "class" else "function"

            # Collect decorator lines immediately above
            prefix_start = i
            j = i - 1
            while j >= 0 and _PY_DECO_RE.match(lines[j]):
                prefix_start = j
                j -= 1

            # Body ends at first non-blank line with indent ≤ symbol indent
            body_end = n
            for j in range(i + 1, n):
                stripped = lines[j].rstrip()
                if not stripped:
                    continue
                li = len(lines[j]) - len(lines[j].lstrip())
                if li <= indent:
                    body_end = j
                    break

            symbols.append(Symbol(
                kind=kind, name=name, qualified=name,
                decl_line=i, decl_end=i,
                body_start=i + 1, body_end=body_end,
                prefix_start=prefix_start,
            ))

        # Qualify methods inside classes (pick innermost parent)
        for sym in symbols:
            if sym.kind != "function":
                continue
            best_parent = None
            for parent in symbols:
                if (parent.kind == "class"
                        and parent.decl_line < sym.decl_line
                        and sym.body_end <= parent.body_end):
                    if (best_parent is None
                            or (parent.body_end - parent.decl_line)
                            < (best_parent.body_end - best_parent.decl_line)):
                        best_parent = parent
            if best_parent is not None:
                sym.qualified = f"{best_parent.name}.{sym.name}"
                sym.kind = "method"
                if sym not in best_parent.children:
                    best_parent.children.append(sym)

        return symbols

    def find_imports(self, lines: list[str]) -> list[Symbol]:
        result: list[Symbol] = []
        i = 0
        while i < len(lines):
            if not _PY_IMPORT_RE.match(lines[i]):
                i += 1
                continue
            body_end = i + 1
            if lines[i].rstrip().endswith("\\"):
                for j in range(i + 1, len(lines)):
                    body_end = j + 1
                    if not lines[j].rstrip().endswith("\\"):
                        break
            elif "(" in lines[i] and ")" not in lines[i]:
                for j in range(i + 1, len(lines)):
                    body_end = j + 1
                    if ")" in lines[j]:
                        break
            raw = " ".join(ln.rstrip("\\").strip() for ln in lines[i:body_end])
            result.append(Symbol(
                kind="import", name=raw.strip(), qualified=raw.strip(),
                decl_line=i, decl_end=body_end - 1,
                body_start=body_end, body_end=body_end,
                prefix_start=i,
            ))
            i = body_end
        return result

    def import_insert_point(self, lines: list[str]) -> int:
        imports = self.find_imports(lines)
        if imports:
            return max(s.body_end for s in imports)
        # Skip shebang / encoding comment / module docstring
        for i, line in enumerate(lines):
            s = line.strip()
            if s and not s.startswith("#") and not s.startswith('"""') and not s.startswith("'''"):
                return i
        return 0


# --- JavaScript / TypeScript ---
_JS_FUNC_RE = re.compile(
    r'^(\s*)(?:export\s+(?:default\s+)?)?(?:(async)\s+)?function\s*\*?\s*(\w+)\s*[(<]')
_JS_CLASS_RE = re.compile(
    r'^(\s*)(?:export\s+(?:default\s+)?)?class\s+(\w+)')
_JS_ARROW_RE = re.compile(
    r'^(\s*)(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:\([^)]*\)|\w+)\s*=>')
_JS_FUNC_EXPR_RE = re.compile(
    r'^(\s*)(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?function')
_JS_IMPORT_RE = re.compile(r'^\s*(import\s+|const\s+\w+\s*=\s*require)')
_JS_METHOD_SHORT_RE = re.compile(r'^(\s{2,})(?:async\s+)?(?:(?:get|set)\s+)?(\w+)\s*\([^)]*\)\s*\{')
_JS_CONTROL_KW = frozenset([
    'if', 'for', 'while', 'switch', 'try', 'catch', 'else', 'do',
    'return', 'new', 'delete', 'typeof', 'void', 'throw', 'case',
])
_TS_IFACE_RE = re.compile(r'^(\s*)(?:export\s+)?interface\s+(\w+)')
_TS_TYPE_RE = re.compile(r'^(\s*)(?:export\s+)?type\s+(\w+)\s*=')
_TS_ENUM_RE = re.compile(r'^(\s*)(?:export\s+)?(?:const\s+)?enum\s+(\w+)')


def _find_brace_end(lines: list[str], start_line: int) -> tuple[int, int]:
    """
    Find the opening and closing brace for a brace-delimited symbol.
    Returns (body_start, body_end) where body_start is the line after the
    opening brace and body_end is exclusive (the line after the closing brace).
    """
    tracker = StringStateTracker()
    depth = 0
    found_open = False
    body_start = start_line + 1

    for i in range(start_line, len(lines)):
        line = lines[i]
        for j, ch in enumerate(line):
            nch = line[j + 1] if j + 1 < len(line) else ""
            counting = tracker.feed(ch, nch)
            if counting:
                if ch == "{":
                    if not found_open:
                        found_open = True
                        body_start = i + 1
                    depth += 1
                elif ch == "}" and found_open:
                    depth -= 1
                    if depth == 0:
                        return (body_start, i + 1)
        tracker.feed("\n", "")

    return (body_start, len(lines))


class JavaScriptProfile(LanguageProfile):
    name = "javascript"
    extensions = (".js", ".mjs", ".cjs")

    def _detect(self, lines: list[str]) -> list[Symbol]:
        symbols: list[Symbol] = []
        n = len(lines)
        for i, line in enumerate(lines):
            sym = self._match_line(line, i, lines, n)
            if sym:
                symbols.append(sym)
        # Qualify methods (pick innermost parent)
        for sym in symbols:
            if sym.kind not in ("function",):
                continue
            best_parent = None
            for parent in symbols:
                if (parent.kind == "class"
                        and parent.decl_line < sym.decl_line
                        and sym.body_end <= parent.body_end):
                    if (best_parent is None
                            or (parent.body_end - parent.decl_line)
                            < (best_parent.body_end - best_parent.decl_line)):
                        best_parent = parent
            if best_parent is not None:
                sym.qualified = f"{best_parent.name}.{sym.name}"
                sym.kind = "method"
                if sym not in best_parent.children:
                    best_parent.children.append(sym)
        return symbols

    def _match_line(self, line: str, i: int, lines: list[str], n: int) -> Optional[Symbol]:
        for pattern, kind in [
            (_JS_CLASS_RE, "class"),
            (_JS_FUNC_RE, "function"),
            (_JS_ARROW_RE, "function"),
            (_JS_FUNC_EXPR_RE, "function"),
        ]:
            m = pattern.match(line)
            if m:
                name = m.group(2) if kind == "class" or pattern in (_JS_ARROW_RE, _JS_FUNC_EXPR_RE) else m.group(3)
                # Arrow functions without a brace body cannot be
                # reliably scoped — skip them entirely.
                if pattern is _JS_ARROW_RE:
                    arrow_idx = line.find('=>')
                    rest = line[arrow_idx + 2:].strip() if arrow_idx != -1 else ""
                    if not rest.startswith('{'):
                        return None
                body_start, body_end = _find_brace_end(lines, i)
                return Symbol(
                    kind=kind, name=name, qualified=name,
                    decl_line=i, decl_end=i,
                    body_start=body_start, body_end=body_end,
                    prefix_start=i,
                )
        # Method shorthand inside class: "  methodName(args) {"
        m = _JS_METHOD_SHORT_RE.match(line)
        if m and m.group(2) not in _JS_CONTROL_KW:
            body_start, body_end = _find_brace_end(lines, i)
            return Symbol(
                kind="function", name=m.group(2), qualified=m.group(2),
                decl_line=i, decl_end=i,
                body_start=body_start, body_end=body_end,
                prefix_start=i,
            )
        return None

    def find_symbols(self, lines: list[str]) -> list[Symbol]:
        return self._detect(lines)

    def find_imports(self, lines: list[str]) -> list[Symbol]:
        result: list[Symbol] = []
        i = 0
        while i < len(lines):
            if not _JS_IMPORT_RE.match(lines[i]):
                i += 1
                continue
            # Handle multi-line imports (scan for closing ; or })
            decl_start = i
            body_end = i + 1
            line_text = lines[i]
            if '{' in line_text and '}' not in line_text:
                for j in range(i + 1, len(lines)):
                    body_end = j + 1
                    if '}' in lines[j] or ';' in lines[j]:
                        # Closing brace found; keep scanning to end of statement
                        if ';' not in lines[j]:
                            for k in range(j + 1, len(lines)):
                                body_end = k + 1
                                if ';' in lines[k] or lines[k].strip():
                                    break
                        break
            elif ';' not in line_text:
                # Statement continues on next line(s)
                for j in range(i + 1, len(lines)):
                    body_end = j + 1
                    if ';' in lines[j]:
                        break
            raw = " ".join(ln.strip() for ln in lines[decl_start:body_end])
            result.append(Symbol(
                kind="import", name=raw.strip(), qualified=raw.strip(),
                decl_line=decl_start, decl_end=body_end - 1,
                body_start=body_end, body_end=body_end,
                prefix_start=decl_start,
            ))
            i = body_end
        return result


class TypeScriptProfile(JavaScriptProfile):
    name = "typescript"
    extensions = (".ts", ".tsx", ".mts", ".cts")

    def _match_line(self, line: str, i: int, lines: list[str], n: int) -> Optional[Symbol]:
        for pattern, kind in [
            (_TS_IFACE_RE, "interface"),
            (_TS_ENUM_RE, "enum"),
        ]:
            m = pattern.match(line)
            if m:
                body_start, body_end = _find_brace_end(lines, i)
                return Symbol(
                    kind=kind, name=m.group(2), qualified=m.group(2),
                    decl_line=i, decl_end=i,
                    body_start=body_start, body_end=body_end,
                    prefix_start=i,
                )
        m = _TS_TYPE_RE.match(line)
        if m:
            return Symbol(
                kind="type", name=m.group(2), qualified=m.group(2),
                decl_line=i, decl_end=i,
                body_start=i + 1, body_end=i + 1,
                prefix_start=i,
            )
        return super()._match_line(line, i, lines, n)

    def find_imports(self, lines: list[str]) -> list[Symbol]:
        result = super().find_imports(lines)
        for i, line in enumerate(lines):
            if re.match(r'^\s*import\s+type\s+', line):
                if not any(s.decl_line == i for s in result):
                    result.append(Symbol(
                        kind="import", name=line.strip(), qualified=line.strip(),
                        decl_line=i, decl_end=i,
                        body_start=i + 1, body_end=i + 1,
                        prefix_start=i,
                    ))
        return result


# --- Rust ---
_RS_FN_RE = re.compile(r'^(\s*)(?:pub(?:\([^)]*\))?\s+)?(?:async\s+)?(?:unsafe\s+)?fn\s+(\w+)')
_RS_STRUCT_RE = re.compile(r'^(\s*)(?:pub(?:\([^)]*\))?\s+)?struct\s+(\w+)')
_RS_ENUM_RE = re.compile(r'^(\s*)(?:pub(?:\([^)]*\))?\s+)?enum\s+(\w+)')
_RS_TRAIT_RE = re.compile(r'^(\s*)(?:pub(?:\([^)]*\))?\s+)?trait\s+(\w+)')
_RS_IMPL_RE = re.compile(r'^(\s*)impl(?:<[^>]*>)?\s+(?:\w+(?:<[^>]*>)?\s+for\s+)?(\w+(?:<[^>]*>)?)')
_RS_MOD_RE = re.compile(r'^(\s*)(?:pub(?:\([^)]*\))?\s+)?mod\s+(\w+)')
_RS_ATTR_RE = re.compile(r'^\s*#\[')
_RS_USE_RE = re.compile(r'^\s*(?:pub\s+)?use\s+')


class RustProfile(LanguageProfile):
    name = "rust"
    extensions = (".rs",)

    def find_symbols(self, lines: list[str]) -> list[Symbol]:
        symbols: list[Symbol] = []
        for i, line in enumerate(lines):
            for pattern, kind in [
                (_RS_FN_RE, "function"),
                (_RS_STRUCT_RE, "struct"),
                (_RS_ENUM_RE, "enum"),
                (_RS_TRAIT_RE, "trait"),
                (_RS_IMPL_RE, "impl"),
                (_RS_MOD_RE, "mod"),
            ]:
                m = pattern.match(line)
                if not m:
                    continue
                name = m.group(2)
                # Collect #[...] attribute lines above
                prefix_start = i
                j = i - 1
                while j >= 0 and _RS_ATTR_RE.match(lines[j]):
                    prefix_start = j
                    j -= 1
                # Brace-delimited or semicolon-terminated (e.g. mod foo;)
                if ";" in line and "{" not in line:
                    body_start, body_end = i + 1, i + 1
                else:
                    body_start, body_end = _find_brace_end(lines, i)
                symbols.append(Symbol(
                    kind=kind, name=name, qualified=name,
                    decl_line=i, decl_end=i,
                    body_start=body_start, body_end=body_end,
                    prefix_start=prefix_start,
                ))
                break  # only match first pattern per line

        # Qualify methods inside impl blocks
        for sym in symbols:
            if sym.kind != "function":
                continue
            for parent in symbols:
                if (parent.kind == "impl"
                        and parent.decl_line < sym.decl_line
                        and sym.body_end <= parent.body_end):
                    sym.qualified = f"{parent.name}.{sym.name}"
                    sym.kind = "method"
                    if sym not in parent.children:
                        parent.children.append(sym)
                    break

        return symbols

    def find_imports(self, lines: list[str]) -> list[Symbol]:
        result: list[Symbol] = []
        for i, line in enumerate(lines):
            if _RS_USE_RE.match(line):
                result.append(Symbol(
                    kind="import", name=line.strip(), qualified=line.strip(),
                    decl_line=i, decl_end=i,
                    body_start=i + 1, body_end=i + 1,
                    prefix_start=i,
                ))
        return result


# --- HTML ---
_HTML_TAG_RE = re.compile(r'^\s*<(\w[\w-]*)(\s[^>]*)?>', re.IGNORECASE)
_HTML_ID_RE = re.compile(r'\bid=["\']([^"\']+)["\']', re.IGNORECASE)
_HTML_CLOSE_RE = re.compile(r'</(\w[\w-]*)\s*>', re.IGNORECASE)
_HTML_SELFCLOSE_RE = re.compile(r'/>\s*$')
_HTML_LINK_RE = re.compile(r'<(?:link|script)\b[^>]*(?:href|src)\s*=', re.IGNORECASE)
_SEMANTIC_TAGS = frozenset(
    "section nav header footer main article aside form table figure".split()
)
_VOID_TAGS = frozenset(
    "area base br col embed hr img input link meta param source track wbr".split()
)


def _find_tag_end(lines: list[str], start_line: int, tag_name: str) -> int:
    """Return exclusive end line for tag_name opened at start_line."""
    depth = 0
    tag_lc = tag_name.lower()
    open_re = re.compile(rf'<{re.escape(tag_lc)}[\s>/]', re.IGNORECASE)
    close_re = re.compile(rf'</{re.escape(tag_lc)}\s*>', re.IGNORECASE)
    for i in range(start_line, len(lines)):
        line = lines[i]
        depth += len(open_re.findall(line))
        depth -= len(close_re.findall(line))
        if i > start_line and depth <= 0:
            return i + 1
    return len(lines)


class HtmlProfile(LanguageProfile):
    name = "html"
    extensions = (".html", ".htm")
    comment_single = ""
    block_marker_open = "<!-- BLOCK:{name} -->"
    block_end_marker = "<!-- END BLOCK:{name} -->"
    anchor_marker = "<!-- ANCHOR:{name} -->"

    def find_symbols(self, lines: list[str]) -> list[Symbol]:
        symbols: list[Symbol] = []
        for i, line in enumerate(lines):
            m = _HTML_TAG_RE.match(line)
            if not m:
                continue
            tag_name = m.group(1).lower()
            attrs = m.group(2) or ""
            if tag_name in _VOID_TAGS:
                continue
            id_m = _HTML_ID_RE.search(attrs)
            if id_m:
                name = id_m.group(1)
            elif tag_name in _SEMANTIC_TAGS:
                # Disambiguate multiple semantic tags of same kind
                count = sum(1 for s in symbols if s.name.startswith(tag_name))
                name = tag_name if count == 0 else f"{tag_name}_{count}"
            else:
                continue
            if _HTML_SELFCLOSE_RE.search(line):
                body_end = i + 1
            else:
                body_end = _find_tag_end(lines, i, tag_name)
            symbols.append(Symbol(
                kind="tag", name=name, qualified=name,
                decl_line=i, decl_end=i,
                body_start=i + 1, body_end=body_end,
                prefix_start=i,
            ))
        return symbols

    def find_imports(self, lines: list[str]) -> list[Symbol]:
        result: list[Symbol] = []
        for i, line in enumerate(lines):
            if _HTML_LINK_RE.search(line):
                result.append(Symbol(
                    kind="import", name=line.strip(), qualified=line.strip(),
                    decl_line=i, decl_end=i,
                    body_start=i + 1, body_end=i + 1,
                    prefix_start=i,
                ))
        return result

    def rename_in_decl(self, line: str, old_name: str, new_name: str) -> str:
        # Replace id="old_name" or id='old_name'
        return re.sub(
            rf'(\bid=["\'])({re.escape(old_name)})(["\'])',
            rf'\g<1>{new_name}\g<3>',
            line,
        )


# --- CSS ---
_CSS_RULE_RE = re.compile(r'^([^{/@\s][^{]*?)\s*\{')
_CSS_AT_RE = re.compile(r'^\s*(@[\w-]+)([^{;]*?)\s*(\{|;)')
_CSS_IMPORT_RE = re.compile(r'^\s*@import\b')


class CssProfile(LanguageProfile):
    name = "css"
    extensions = (".css", ".scss", ".less")
    comment_single = ""
    block_marker_open = "/* BLOCK:{name} */"
    block_end_marker = "/* END BLOCK:{name} */"
    anchor_marker = "/* ANCHOR:{name} */"

    def find_symbols(self, lines: list[str]) -> list[Symbol]:
        symbols: list[Symbol] = []
        for i, line in enumerate(lines):
            at_m = _CSS_AT_RE.match(line)
            if at_m:
                at_kw = at_m.group(1)
                at_arg = at_m.group(2).strip()
                terminator = at_m.group(3)
                name = f"{at_kw} {at_arg}".strip() if at_arg else at_kw
                if terminator == ";":
                    symbols.append(Symbol(
                        kind="rule", name=name, qualified=name,
                        decl_line=i, decl_end=i,
                        body_start=i + 1, body_end=i + 1,
                        prefix_start=i,
                    ))
                else:
                    _, body_end = _find_brace_end(lines, i)
                    symbols.append(Symbol(
                        kind="rule", name=name, qualified=name,
                        decl_line=i, decl_end=i,
                        body_start=i + 1, body_end=body_end,
                        prefix_start=i,
                    ))
                continue
            rule_m = _CSS_RULE_RE.match(line)
            if rule_m:
                selector = rule_m.group(1).strip()
                _, body_end = _find_brace_end(lines, i)
                symbols.append(Symbol(
                    kind="rule", name=selector, qualified=selector,
                    decl_line=i, decl_end=i,
                    body_start=i + 1, body_end=body_end,
                    prefix_start=i,
                ))
        return symbols

    def find_imports(self, lines: list[str]) -> list[Symbol]:
        result: list[Symbol] = []
        for i, line in enumerate(lines):
            if _CSS_IMPORT_RE.match(line):
                result.append(Symbol(
                    kind="import", name=line.strip(), qualified=line.strip(),
                    decl_line=i, decl_end=i,
                    body_start=i + 1, body_end=i + 1,
                    prefix_start=i,
                ))
        return result

    def rename_in_decl(self, line: str, old_name: str, new_name: str) -> str:
        return line.replace(old_name, new_name, 1)


# ---------------------------------------------------------------------------
# Profile registry
# ---------------------------------------------------------------------------

_PROFILES: dict[str, LanguageProfile] = {
    "python": PythonProfile(),
    "javascript": JavaScriptProfile(),
    "typescript": TypeScriptProfile(),
    "rust": RustProfile(),
    "html": HtmlProfile(),
    "css": CssProfile(),
}


def get_profile(language: str) -> Optional[LanguageProfile]:
    return _PROFILES.get(language.lower())


# ---------------------------------------------------------------------------
# Symbol resolver
# ---------------------------------------------------------------------------

class SymbolResolver:
    """Maps symbol identifiers to Symbol objects."""

    def __init__(self, symbols: list[Symbol]) -> None:
        self._by_name: dict[str, list[Symbol]] = {}
        self._by_qualified: dict[str, Symbol] = {}
        self._by_type_name: dict[str, Symbol] = {}
        self._index(symbols)

    def _index(self, symbols: list[Symbol]) -> None:
        self._by_name.clear()
        self._by_qualified.clear()
        self._by_type_name.clear()
        for sym in symbols:
            self._by_name.setdefault(sym.name, []).append(sym)
            self._by_qualified[sym.qualified] = sym
            self._by_type_name[f"{sym.kind}:{sym.name}"] = sym

    def reindex(self, symbols: list[Symbol]) -> None:
        self._index(symbols)

    # Aliases for common kind shorthands
    _KIND_ALIASES: dict[str, str] = {
        "fn": "function", "func": "function", "def": "function",
        "cls": "class",
    }

    def resolve(self, symbol_id: str) -> Optional[Symbol]:
        if not symbol_id:
            return None
        sid = symbol_id.strip()
        # Type-qualified: "fn:foo", "function:foo", "class:Foo", "rule:.hero"
        if ":" in sid and not sid.startswith("."):
            if sid in self._by_type_name:
                return self._by_type_name[sid]
            # Try alias expansion: "fn:foo" → "function:foo"
            kind_part, _, name_part = sid.partition(":")
            expanded = self._KIND_ALIASES.get(kind_part)
            if expanded:
                expanded_key = f"{expanded}:{name_part}"
                if expanded_key in self._by_type_name:
                    return self._by_type_name[expanded_key]
        # Qualified: "MyClass.foo"
        if sid in self._by_qualified:
            return self._by_qualified[sid]
        # Bare name (unambiguous only)
        matches = self._by_name.get(sid, [])
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            return None  # ambiguous
        return None


# ---------------------------------------------------------------------------
# String matching (3-tier: exact → whitespace-normalized → fuzzy)
# ---------------------------------------------------------------------------

def _normalize_ws(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip()


def _tokenize_words(text: str) -> list[str]:
    """Split text into alphanumeric word tokens for fuzzy comparison."""
    return [w for w in re.split(r'\W+', text.lower()) if w]


def _find_in_scope(lines: list[str], start: int, end: int,
                   target: str, allow_fuzzy: bool = False) -> Optional[tuple[int, int]]:
    """
    Find `target` in lines[start:end].
    Returns (line_start, line_end) inclusive, or None.
    """
    if not target:
        return None
    scope_text = "\n".join(lines[start:end])

    # Tier 1: exact
    idx = scope_text.find(target)
    if idx != -1:
        return _char_to_lines(lines, start, scope_text, idx, len(target))

    # Tier 2: whitespace-normalized
    norm_target = _normalize_ws(target)
    if not norm_target:
        return None
    norm_scope = _normalize_ws(scope_text)
    if norm_target in norm_scope:
        for i in range(start, end):
            accum = ""
            for j in range(i, end):
                accum = (accum + " " + _normalize_ws(lines[j])).strip()
                if norm_target in accum:
                    if j > i:
                        without_i = _normalize_ws(
                            " ".join(_normalize_ws(lines[k]) for k in range(i + 1, j + 1)))
                        if norm_target in without_i:
                            break
                    return (i, j)
                if len(accum) > len(norm_target) + 200:
                    break

    # Tier 3: fuzzy (opt-in) — sliding window of word tokens across lines
    if not allow_fuzzy:
        return None
    best_ratio = 0.0
    best_pos = None
    target_tokens = _tokenize_words(target)
    if not target_tokens:
        return None
    target_set = set(target_tokens)
    max_window = len(target_tokens) + 5
    for i in range(start, end):
        window_tokens: list[str] = []
        for j in range(i, min(i + max_window, end)):
            j_tokens = _tokenize_words(lines[j])
            if not j_tokens:
                continue
            window_tokens.extend(j_tokens)
            common = len(target_set & set(window_tokens))
            denom = max(len(target_tokens), len(window_tokens))
            ratio = common / denom if denom else 0.0
            if ratio > best_ratio and ratio > 0.75:
                best_ratio = ratio
                best_pos = (i, j)
    if best_pos is not None:
        return best_pos
    return None


def _char_to_lines(lines: list[str], offset: int, scope_text: str,
                   char_idx: int, char_len: int) -> tuple[int, int]:
    """Convert character position in scope_text back to (start_line, end_line) inclusive."""
    if char_len <= 0:
        pos = 0
        for i, line in enumerate(lines[offset:], start=offset):
            line_end = pos + len(line) + 1
            if pos <= char_idx < line_end:
                return (i, i)
            pos = line_end
        return (offset, offset)
    pos = 0
    start_line = offset
    end_line = offset
    found_start = False
    for i, line in enumerate(lines[offset:], start=offset):
        line_end = pos + len(line) + 1
        if not found_start and pos <= char_idx < line_end:
            start_line = i
            found_start = True
        if pos <= char_idx + char_len - 1 < line_end:
            end_line = i
            break
        pos = line_end
    return (start_line, end_line)


_BLOCK_START_RE = re.compile(r'(?:<!--\s*|//\s*|#\s*|/\*\s*)BLOCK:(\S+?)(?:\s*-->|\s*\*/|\s*$)')
_BLOCK_END_RE = re.compile(r'(?:<!--\s*|//\s*|#\s*|/\*\s*)END BLOCK:(\S+?)(?:\s*-->|\s*\*/|\s*$)')
_ANCHOR_RE = re.compile(r'(?:<!--\s*|//\s*|#\s*|/\*\s*)ANCHOR:(\S+?)(?:\s*-->|\s*\*/|\s*$)')


def _find_block_markers(lines: list[str], start: int, end: int,
                        name: str) -> Optional[tuple[int, int]]:
    block_start = None
    for i in range(start, end):
        if block_start is None:
            m = _BLOCK_START_RE.search(lines[i])
            if m and m.group(1) == name:
                block_start = i
        else:
            m = _BLOCK_END_RE.search(lines[i])
            if m and m.group(1) == name:
                return (block_start, i)
    return None


def _find_anchor(lines: list[str], start: int, end: int, name: str) -> Optional[int]:
    for i in range(start, end):
        m = _ANCHOR_RE.search(lines[i])
        if m and m.group(1) == name:
            return i
    return None


# ---------------------------------------------------------------------------
# Symbol helpers
# ---------------------------------------------------------------------------

def symbol_extent(sym: Symbol) -> tuple[int, int]:
    """Return (start, end) covering prefix through body_end."""
    return (sym.prefix_start, sym.body_end)


def extract_symbol_lines(lines: list[str], sym: Symbol) -> list[str]:
    start, end = symbol_extent(sym)
    return lines[start:end]


def remove_symbol_lines(lines: list[str], sym: Symbol) -> list[str]:
    start, end = symbol_extent(sym)
    return lines[:start] + lines[end:]


def find_symbol_insert_point(lines: list[str], symbols: list[Symbol],
                             after_id: str, resolver: SymbolResolver) -> Optional[int]:
    target = resolver.resolve(after_id)
    if target is None:
        return None
    _, end = symbol_extent(target)
    return end


# ---------------------------------------------------------------------------
# Patch applier
# ---------------------------------------------------------------------------

class CodePatchApplier:
    """Applies a code-patch envelope to a source file."""

    def __init__(self, source_text: str, patch: dict,
                 output_dir: str = ".", dry_run: bool = False,
                 verbose: bool = False) -> None:
        self.source_text = source_text
        self.patch = patch
        self.output_dir = output_dir
        self.dry_run = dry_run
        self.verbose = verbose
        self.lines: list[str] = source_text.splitlines()
        self.original_lines: list[str] = list(self.lines)
        self.symbols: list[Symbol] = []
        self.resolver: Optional[SymbolResolver] = None
        self.profile: Optional[LanguageProfile] = None
        self.warnings: list[str] = []
        self.assertion_failed = False

    def _reparse(self) -> None:
        if self.profile:
            self.symbols = self.profile.find_symbols(self.lines)
        if self.resolver:
            self.resolver.reindex(self.symbols)
        else:
            self.resolver = SymbolResolver(self.symbols)

    def _resolve(self, symbol_id: str) -> Optional[Symbol]:
        assert self.resolver is not None
        return self.resolver.resolve(symbol_id)

    def _scope(self, symbol_id: Optional[str]) -> tuple[int, int]:
        if symbol_id:
            sym = self._resolve(symbol_id)
            if sym:
                return symbol_extent(sym)
        return (0, len(self.lines))

    # ------------------------------------------------------------------
    # Operations
    # ------------------------------------------------------------------

    def _op_assert(self, op: dict) -> OpResult:
        symbol_id = op.get("symbol_id")
        contains = op.get("contains", "")
        orig_symbols = self.profile.find_symbols(self.original_lines) if self.profile else []
        orig_resolver = SymbolResolver(orig_symbols)
        if symbol_id:
            sym = orig_resolver.resolve(symbol_id)
            if sym is None:
                return OpResult(0, False, "SYMBOL_NOT_FOUND",
                                f"Symbol '{symbol_id}' not found in original.")
            start, end = symbol_extent(sym)
            scope_text = "\n".join(self.original_lines[start:end])
        else:
            scope_text = "\n".join(self.original_lines)
        if contains not in scope_text:
            if _normalize_ws(contains) not in _normalize_ws(scope_text):
                return OpResult(0, False, "ASSERTION_FAILED",
                                f"'{contains}' not found in scope.")
        return OpResult(0, True)

    def _op_rename_symbol(self, op: dict) -> OpResult:
        symbol_id = op.get("symbol_id", "")
        new_name = op.get("new_name", "")
        sym = self._resolve(symbol_id)
        if sym is None:
            return OpResult(0, False, "SYMBOL_NOT_FOUND",
                            f"Symbol '{symbol_id}' not found.")
        assert self.profile is not None
        self.lines[sym.decl_line] = self.profile.rename_in_decl(
            self.lines[sym.decl_line], sym.name, new_name)
        self._reparse()
        return OpResult(0, True)

    def _op_replace_symbol(self, op: dict) -> OpResult:
        symbol_id = op.get("symbol_id", "")
        new_body = op.get("new_body", "")
        sym = self._resolve(symbol_id)
        if sym is None:
            return OpResult(0, False, "SYMBOL_NOT_FOUND",
                            f"Symbol '{symbol_id}' not found.")
        new_lines = new_body.splitlines() if new_body else []
        self.lines = (self.lines[:sym.body_start]
                      + new_lines
                      + self.lines[sym.body_end:])
        self._reparse()
        return OpResult(0, True)

    def _op_delete_symbol(self, op: dict) -> OpResult:
        symbol_id = op.get("symbol_id", "")
        sym = self._resolve(symbol_id)
        if sym is None:
            return OpResult(0, False, "SYMBOL_NOT_FOUND",
                            f"Symbol '{symbol_id}' not found.")
        self.lines = remove_symbol_lines(self.lines, sym)
        self._reparse()
        return OpResult(0, True)

    def _op_move_symbol(self, op: dict) -> OpResult:
        symbol_id = op.get("symbol_id", "")
        to_after = op.get("to_after", "")
        sym = self._resolve(symbol_id)
        if sym is None:
            return OpResult(0, False, "SYMBOL_NOT_FOUND",
                            f"Symbol '{symbol_id}' not found.")
        target = self._resolve(to_after)
        if target is None:
            return OpResult(0, False, "SYMBOL_NOT_FOUND",
                            f"Target '{to_after}' not found.")
        extracted = extract_symbol_lines(self.lines, sym)
        self.lines = remove_symbol_lines(self.lines, sym)
        self._reparse()
        insert_at = find_symbol_insert_point(
            self.lines, self.symbols, to_after, self.resolver)
        if insert_at is None:
            return OpResult(0, False, "SYMBOL_NOT_FOUND",
                            f"Could not find insert point after '{to_after}'.")
        self.lines = self.lines[:insert_at] + extracted + self.lines[insert_at:]
        self._reparse()
        return OpResult(0, True)

    def _op_swap_symbols(self, op: dict) -> OpResult:
        sid_a = op.get("symbol_a", "")
        sid_b = op.get("symbol_b", "")
        sym_a = self._resolve(sid_a)
        sym_b = self._resolve(sid_b)
        if sym_a is None:
            return OpResult(0, False, "SYMBOL_NOT_FOUND", f"Symbol '{sid_a}' not found.")
        if sym_b is None:
            return OpResult(0, False, "SYMBOL_NOT_FOUND", f"Symbol '{sid_b}' not found.")
        if sym_a.prefix_start > sym_b.prefix_start:
            sym_a, sym_b = sym_b, sym_a
        lines_a = extract_symbol_lines(self.lines, sym_a)
        lines_b = extract_symbol_lines(self.lines, sym_b)
        a_start, a_end = symbol_extent(sym_a)
        b_start, b_end = symbol_extent(sym_b)
        self.lines = (self.lines[:a_start] + lines_b
                      + self.lines[a_end:b_start] + lines_a
                      + self.lines[b_end:])
        self._reparse()
        return OpResult(0, True)

    def _op_edit_text(self, op: dict) -> OpResult:
        symbol_id = op.get("symbol_id", "")
        find_str = op.get("find", "")
        replace_str = op.get("replace", "")
        allow_fuzzy = op.get("allow_fuzzy", False)
        start, end = self._scope(symbol_id)
        match = _find_in_scope(self.lines, start, end, find_str,
                               allow_fuzzy=allow_fuzzy)
        if match is None:
            # Closest match for error reporting
            closest = None
            best_overlap = 0
            find_words = set(_normalize_ws(find_str).lower().split())
            for i in range(start, end):
                line_words = set(_normalize_ws(self.lines[i]).lower().split())
                overlap = len(find_words & line_words)
                if overlap > best_overlap:
                    best_overlap = overlap
                    closest = self.lines[i].strip()
            return OpResult(0, False, "FIND_NOT_MATCHED",
                            f"No match for '{find_str[:60]}'.", closest)
        m_start, m_end = match
        scope_text = "\n".join(self.lines[m_start:m_end + 1])
        new_text = scope_text.replace(find_str, replace_str, 1)
        if new_text == scope_text:
            norm_find = _normalize_ws(find_str)
            replaced = False
            for ts in range(m_start, m_end + 1):
                for te in range(ts, m_end + 1):
                    candidate = "\n".join(self.lines[ts:te + 1])
                    if norm_find in _normalize_ws(candidate):
                        new_lines = replace_str.splitlines() if replace_str else []
                        self.lines = self.lines[:ts] + new_lines + self.lines[te + 1:]
                        replaced = True
                        break
                if replaced:
                    break
            if not replaced:
                new_lines = replace_str.splitlines() if replace_str else []
                self.lines = self.lines[:m_start] + new_lines + self.lines[m_end + 1:]
        else:
            new_lines = new_text.splitlines()
            self.lines = self.lines[:m_start] + new_lines + self.lines[m_end + 1:]
        self._reparse()
        return OpResult(0, True)

    def _op_replace_block(self, op: dict) -> OpResult:
        symbol_id = op.get("symbol_id", "")
        target = op.get("target", "")
        new_content = op.get("new_content", "")
        start, end = self._scope(symbol_id)
        bm = _BLOCK_START_RE.search(target)
        if bm:
            markers = _find_block_markers(self.lines, start, end, bm.group(1))
            if markers:
                b_start, b_end = markers
                new_lines = new_content.splitlines() if new_content else []
                self.lines = self.lines[:b_start] + new_lines + self.lines[b_end + 1:]
                self._reparse()
                return OpResult(0, True)
        match = _find_in_scope(self.lines, start, end, target,
                               allow_fuzzy=op.get("allow_fuzzy", False))
        if match is None:
            return OpResult(0, False, "FIND_NOT_MATCHED",
                            f"Target '{target[:60]}' not found.")
        m_start, m_end = match
        new_lines = new_content.splitlines() if new_content else []
        self.lines = self.lines[:m_start] + new_lines + self.lines[m_end + 1:]
        self._reparse()
        return OpResult(0, True)

    def _op_delete_block(self, op: dict) -> OpResult:
        return self._op_replace_block({**op, "new_content": ""})

    def _op_insert_block(self, op: dict) -> OpResult:
        symbol_id = op.get("symbol_id")
        after_anchor = op.get("after_anchor", "")
        new_content = op.get("new_content", "")
        start, end = self._scope(symbol_id)
        am = _ANCHOR_RE.search(after_anchor)
        anchor_name = am.group(1) if am else after_anchor.strip()
        pos = _find_anchor(self.lines, start, end, anchor_name)
        if pos is not None:
            new_lines = new_content.splitlines()
            self.lines = self.lines[:pos + 1] + new_lines + self.lines[pos + 1:]
            self._reparse()
            return OpResult(0, True)
        match = _find_in_scope(self.lines, start, end, after_anchor)
        if match is None:
            return OpResult(0, False, "ANCHOR_NOT_FOUND",
                            f"Anchor '{after_anchor[:60]}' not found.")
        new_lines = new_content.splitlines()
        self.lines = self.lines[:match[1] + 1] + new_lines + self.lines[match[1] + 1:]
        self._reparse()
        return OpResult(0, True)

    def _op_move_block(self, op: dict) -> OpResult:
        src_sym = op.get("source_symbol_id", "")
        src_tgt = op.get("source_target", "")
        dst_sym = op.get("target_symbol_id")
        after_anchor = op.get("after_anchor", "")
        s_start, s_end = self._scope(src_sym)
        bm = _BLOCK_START_RE.search(src_tgt)
        extracted: list[str] = []
        if bm:
            markers = _find_block_markers(self.lines, s_start, s_end, bm.group(1))
            if markers:
                b_start, b_end = markers
                extracted = self.lines[b_start:b_end + 1]
                self.lines = self.lines[:b_start] + self.lines[b_end + 1:]
                self._reparse()
            else:
                return OpResult(0, False, "BLOCK_NOT_FOUND",
                                f"Source block '{src_tgt[:60]}' not found.")
        else:
            match = _find_in_scope(self.lines, s_start, s_end, src_tgt)
            if match is None:
                return OpResult(0, False, "FIND_NOT_MATCHED",
                                f"Source '{src_tgt[:60]}' not found.")
            extracted = self.lines[match[0]:match[1] + 1]
            self.lines = self.lines[:match[0]] + self.lines[match[1] + 1:]
            self._reparse()
        t_start, t_end = self._scope(dst_sym)
        am = _ANCHOR_RE.search(after_anchor)
        anchor_name = am.group(1) if am else after_anchor.strip()
        pos = _find_anchor(self.lines, t_start, t_end, anchor_name)
        if pos is not None:
            self.lines = self.lines[:pos + 1] + extracted + self.lines[pos + 1:]
        else:
            match = _find_in_scope(self.lines, t_start, t_end, after_anchor)
            if match is None:
                return OpResult(0, False, "ANCHOR_NOT_FOUND",
                                f"Target anchor '{after_anchor[:60]}' not found.")
            self.lines = self.lines[:match[1] + 1] + extracted + self.lines[match[1] + 1:]
        self._reparse()
        return OpResult(0, True)

    def _op_copy_block(self, op: dict) -> OpResult:
        src_sym = op.get("source_symbol_id", "")
        src_tgt = op.get("source_target", "")
        dst_sym = op.get("target_symbol_id")
        after_anchor = op.get("after_anchor", "")
        s_start, s_end = self._scope(src_sym)
        bm = _BLOCK_START_RE.search(src_tgt)
        copied: list[str] = []
        if bm:
            markers = _find_block_markers(self.lines, s_start, s_end, bm.group(1))
            if markers:
                copied = list(self.lines[markers[0]:markers[1] + 1])
            else:
                return OpResult(0, False, "BLOCK_NOT_FOUND",
                                f"Source block '{src_tgt[:60]}' not found.")
        else:
            match = _find_in_scope(self.lines, s_start, s_end, src_tgt)
            if match is None:
                return OpResult(0, False, "FIND_NOT_MATCHED",
                                f"Source '{src_tgt[:60]}' not found.")
            copied = list(self.lines[match[0]:match[1] + 1])
        t_start, t_end = self._scope(dst_sym)
        am = _ANCHOR_RE.search(after_anchor)
        anchor_name = am.group(1) if am else after_anchor.strip()
        pos = _find_anchor(self.lines, t_start, t_end, anchor_name)
        if pos is not None:
            self.lines = self.lines[:pos + 1] + copied + self.lines[pos + 1:]
        else:
            match = _find_in_scope(self.lines, t_start, t_end, after_anchor)
            if match is None:
                return OpResult(0, False, "ANCHOR_NOT_FOUND",
                                f"Target anchor '{after_anchor[:60]}' not found.")
            self.lines = self.lines[:match[1] + 1] + copied + self.lines[match[1] + 1:]
        self._reparse()
        return OpResult(0, True)

    def _op_inject_markers(self, op: dict) -> OpResult:
        assert self.profile is not None
        symbol_id = op.get("symbol_id", "")
        markers = op.get("markers", [])
        sym = self._resolve(symbol_id) if symbol_id else None
        if symbol_id and sym is None:
            return OpResult(0, False, "SYMBOL_NOT_FOUND",
                            f"Symbol '{symbol_id}' not found.")
        start = sym.decl_line if sym else 0
        end = sym.body_end if sym else len(self.lines)
        offset = 0
        for marker in markers:
            mtype = marker.get("type")
            if mtype == "block":
                name = marker.get("name", "")
                wraps = marker.get("wraps", "")
                wraps_end = marker.get("wraps_end", "")
                w_match = _find_in_scope(self.lines, start + offset, end + offset, wraps)
                if w_match is None:
                    self.warnings.append(
                        f"inject_markers: '{wraps[:40]}' not found for block '{name}'")
                    continue
                open_line = self.profile.block_marker_open.format(name=name)
                self.lines.insert(w_match[0], open_line)
                offset += 1
                we_match = _find_in_scope(
                    self.lines, w_match[0] + 1, end + offset, wraps_end)
                if we_match is None:
                    self.warnings.append(
                        f"inject_markers: '{wraps_end[:40]}' not found for end of block '{name}'")
                    continue
                end_line = self.profile.block_end_marker.format(name=name)
                self.lines.insert(we_match[1] + 1, end_line)
                offset += 1
            elif mtype == "anchor":
                name = marker.get("name", "")
                after = marker.get("after", "")
                a_match = _find_in_scope(
                    self.lines, start + offset, end + offset, after)
                if a_match is None:
                    self.warnings.append(
                        f"inject_markers: '{after[:40]}' not found for anchor '{name}'")
                    continue
                anchor_line = self.profile.anchor_marker.format(name=name)
                self.lines.insert(a_match[1] + 1, anchor_line)
                offset += 1
        self._reparse()
        return OpResult(0, True)

    def _op_add_import(self, op: dict) -> OpResult:
        assert self.profile is not None
        statement = op.get("statement", "")
        if self.profile.is_import_duplicate(self.lines, statement):
            self.warnings.append(f"add_import: '{statement[:60]}' already present, skipped.")
            return OpResult(0, True)
        insert_at = self.profile.import_insert_point(self.lines)
        self.lines = self.lines[:insert_at] + [statement] + self.lines[insert_at:]
        self._reparse()
        return OpResult(0, True)

    def _op_remove_import(self, op: dict) -> OpResult:
        assert self.profile is not None
        statement = op.get("statement", "")
        norm = _normalize_ws(statement)
        imports = self.profile.find_imports(self.lines)
        for sym in imports:
            existing = " ".join(
                _normalize_ws(ln) for ln in self.lines[sym.decl_line:sym.body_end]
            )
            if _normalize_ws(existing) == norm or norm in _normalize_ws(existing):
                self.lines = (self.lines[:sym.decl_line]
                              + self.lines[sym.body_end:])
                self._reparse()
                return OpResult(0, True)
        return OpResult(0, False, "IMPORT_NOT_FOUND",
                        f"Import '{statement[:60]}' not found.")

    def _op_change_signature(self, op: dict) -> OpResult:
        symbol_id = op.get("symbol_id", "")
        new_signature = op.get("new_signature", "")
        sym = self._resolve(symbol_id)
        if sym is None:
            return OpResult(0, False, "SYMBOL_NOT_FOUND",
                            f"Symbol '{symbol_id}' not found.")
        new_sig_lines = new_signature.splitlines()
        self.lines = (self.lines[:sym.decl_line]
                      + new_sig_lines
                      + self.lines[sym.decl_end + 1:])
        self._reparse()
        return OpResult(0, True)

    def _op_add_decorator(self, op: dict) -> OpResult:
        symbol_id = op.get("symbol_id", "")
        decorator = op.get("decorator", "")
        sym = self._resolve(symbol_id)
        if sym is None:
            return OpResult(0, False, "SYMBOL_NOT_FOUND",
                            f"Symbol '{symbol_id}' not found.")
        self.lines = (self.lines[:sym.prefix_start]
                      + [decorator]
                      + self.lines[sym.prefix_start:])
        self._reparse()
        return OpResult(0, True)

    # ------------------------------------------------------------------
    # Dispatch
    # ------------------------------------------------------------------

    OP_HANDLERS: dict[str, str] = {
        "assert": "_op_assert",
        "rename_symbol": "_op_rename_symbol",
        "replace_symbol": "_op_replace_symbol",
        "delete_symbol": "_op_delete_symbol",
        "move_symbol": "_op_move_symbol",
        "swap_symbols": "_op_swap_symbols",
        "edit_text": "_op_edit_text",
        "replace_block": "_op_replace_block",
        "delete_block": "_op_delete_block",
        "insert_block": "_op_insert_block",
        "move_block": "_op_move_block",
        "copy_block": "_op_copy_block",
        "inject_markers": "_op_inject_markers",
        "add_import": "_op_add_import",
        "remove_import": "_op_remove_import",
        "change_signature": "_op_change_signature",
        "add_decorator": "_op_add_decorator",
    }

    def _apply_op(self, index: int, op: dict) -> OpResult:
        op_type = op.get("op", "")
        handler_name = self.OP_HANDLERS.get(op_type)
        if handler_name is None:
            return OpResult(index, False, "UNKNOWN_OP",
                            f"Unknown operation: '{op_type}'")
        result = getattr(self, handler_name)(op)
        result.index = index
        return result

    # ------------------------------------------------------------------
    # Main apply loop
    # ------------------------------------------------------------------

    def apply(self) -> tuple[str, dict, str]:
        """Apply all edits. Returns (STATUS, EXECUTION_REPORT_dict, LAST_STABLE)."""
        patch_id = self.patch.get("patch_id", "unknown")
        file_id = self.patch.get("file_id", "unknown")
        apply_mode = self.patch.get("apply_mode", "atomic")
        source_hash = "sha256:" + hashlib.sha256(
            self.source_text.encode()).hexdigest()
        language = self.patch.get("language", "")

        report = ExecutionReport(
            patch_id=patch_id, file_id=file_id,
            status="not_attempted", apply_mode=apply_mode,
            source_hash=source_hash,
        )

        # Validate language
        self.profile = get_profile(language)
        if self.profile is None:
            report.status = "envelope_error"
            report.errors = [{
                "error_level": "envelope",
                "error_type": "UNSUPPORTED_LANGUAGE",
                "detail": f"Language '{language}' is not supported.",
            }]
            return ("envelope_error", report.to_dict(), "B (unchanged)")

        # Validate base_hash
        base_hash = self.patch.get("base_hash")
        if base_hash and base_hash != source_hash:
            report.status = "envelope_error"
            report.errors = [{
                "error_level": "envelope",
                "error_type": "HASH_MISMATCH",
                "detail": f"Expected {base_hash}, got {source_hash}",
            }]
            return ("envelope_error", report.to_dict(), "B (unchanged)")

        patch_status = self.patch.get("status", "ready")
        if patch_status == "blocked":
            report.status = "not_attempted"
            return ("not_attempted", report.to_dict(), "B (unchanged)")

        edits = self.patch.get("edits", [])
        if not edits and patch_status in ("ready", "partial"):
            report.status = "envelope_error"
            report.errors = [{
                "error_level": "envelope",
                "error_type": "EMPTY_EDITS",
                "detail": "edits array is empty.",
            }]
            return ("envelope_error", report.to_dict(), "B (unchanged)")

        # Apply ops
        self._reparse()
        if self.verbose:
            print(f"[verbose] Language: {language}", file=sys.stderr)
            print(f"[verbose] Symbols ({len(self.symbols)}):", file=sys.stderr)
            for s in self.symbols:
                print(f"  {s.kind:12s} {s.qualified:30s}  "
                      f"decl={s.decl_line} body={s.body_start}-{s.body_end}"
                      f"  prefix={s.prefix_start}", file=sys.stderr)
            print(f"[verbose] Edits: {len(edits)} ops", file=sys.stderr)
        applied: list[int] = []
        skipped: list[dict] = []
        errors: list[dict] = []

        for i, op in enumerate(edits):
            if self.assertion_failed:
                skipped.append({
                    "index": i,
                    "error_type": "SKIPPED_AFTER_ASSERTION",
                    "detail": "Skipped due to prior assertion failure.",
                })
                continue

            result = self._apply_op(i, op)

            if self.verbose:
                sym_id = op.get('symbol_id', '')
                status_str = 'OK' if result.success else f'FAIL({result.error_type})'
                print(f"[verbose] op[{i}] {op.get('op','?'):20s} "
                      f"sym={sym_id or '(global)':30s} → {status_str}",
                      file=sys.stderr)
                if not result.success and result.closest_match:
                    print(f"          closest: {result.closest_match[:80]}",
                          file=sys.stderr)

            if result.success:
                applied.append(i)
            else:
                err: dict[str, Any] = {
                    "error_level": "op",
                    "failed_op_index": i,
                    "op": op.get("op", ""),
                    "error_type": result.error_type,
                    "detail": result.detail,
                }
                if result.closest_match:
                    err["closest_match"] = result.closest_match

                if result.error_type == "ASSERTION_FAILED":
                    if apply_mode == "atomic":
                        report.status = "blocked"
                        report.errors = [err]
                        return ("blocked", report.to_dict(), "B (unchanged)")
                    else:
                        self.assertion_failed = True
                        skipped.append({"index": i, "error_type": result.error_type,
                                        "detail": result.detail})
                        errors.append(err)
                        continue

                if apply_mode == "atomic":
                    report.status = "discarded"
                    report.errors = [err]
                    return ("discarded", report.to_dict(), "B (unchanged)")
                else:
                    skipped.append({"index": i, "error_type": result.error_type,
                                    "detail": result.detail})
                    errors.append(err)

        # Determine STATUS
        if not applied and skipped:
            status = "no_change"
        elif skipped:
            status = "partial_success"
        else:
            status = "full_success"

        # Verify original was not mutated
        if "\n".join(self.original_lines).rstrip("\n") != self.source_text.rstrip("\n"):
            self.warnings.append(
                "original_lines were modified during apply — this is a bug.")

        result_text = "\n".join(self.lines)
        result_hash = "sha256:" + hashlib.sha256(result_text.encode()).hexdigest()

        # Goals tracking
        applied_set = set(applied)
        goals_actual: list[dict] = []
        for gc in self.patch.get("goals_covered", []):
            indices = gc.get("edit_indices", [])
            applied_idx = [i for i in indices if i in applied_set]
            skipped_idx = [i for i in indices if i not in applied_set]
            if skipped_idx and not applied_idx:
                actual_status = "not_applied"
            elif skipped_idx:
                actual_status = "partial"
            else:
                actual_status = "done"
            goals_actual.append({
                "goal": gc.get("goal", ""),
                "planned_status": gc.get("status", ""),
                "actual_status": actual_status,
                "planned_indices": indices,
                "applied_indices": applied_idx,
                "skipped_indices": skipped_idx,
            })

        # Write working copy
        ext = Path(file_id).suffix or f".{language}"
        ulid = generate_ulid()
        wc_name = f"{Path(file_id).stem}.{ulid}{ext}"
        wc_path = os.path.join(self.output_dir, wc_name)

        report.status = status
        report.applied_ops = applied
        report.skipped_ops = skipped
        report.errors = errors
        report.goals_actual = goals_actual
        report.warnings = list(self.warnings)
        report.dry_run = self.dry_run

        if status in ("full_success", "partial_success"):
            report.result_hash = result_hash
            report.working_copy_path = wc_name
            Path(wc_path).write_text(result_text + "\n", encoding="utf-8")

        last_stable = "C (promoted)" if status == "full_success" else "B (unchanged)"
        if self.dry_run and status == "full_success":
            last_stable = "C (would be promoted — dry run)"

        return (status, report.to_dict(), last_stable)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="code-patch applier — apply a patch envelope to a source file.")
    parser.add_argument("source", help="Path to the source file.")
    parser.add_argument("patch", help="Path to the patch envelope JSON.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Compute results without writing working copy.")
    parser.add_argument("--output-dir", default=".",
                        help="Directory for the working copy (default: cwd).")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Print symbol table and per-op results to stderr.")
    args = parser.parse_args()

    source_text = Path(args.source).read_text(encoding="utf-8")
    patch = json.loads(Path(args.patch).read_text(encoding="utf-8"))

    applier = CodePatchApplier(source_text, patch,
                               output_dir=args.output_dir,
                               dry_run=args.dry_run,
                               verbose=args.verbose)
    status, report, last_stable = applier.apply()

    output = {
        "STATUS": status,
        "EXECUTION_REPORT": report,
        "LAST_STABLE": last_stable,
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
