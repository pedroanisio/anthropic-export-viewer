#!/usr/bin/env python3
"""
doc-patch applier — deterministic executor for doc-patch envelopes.

Usage:
    python apply_patch.py <source_document> <patch_json> [--dry-run] [--output-dir DIR]

Reads a Markdown source document and a patch envelope JSON, creates a
ULID-named working copy, applies all operations sequentially, runs the
post-apply phase, and outputs STATUS, EXECUTION_REPORT, and LAST_STABLE.

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
# ULID-like ID generator (timestamp + random, monotonic, no dependency)
# ---------------------------------------------------------------------------

def generate_ulid() -> str:
    """Generate a ULID-like identifier (26 chars, Crockford base32)."""
    ENCODING = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
    t = int(time.time() * 1000)
    # 10 chars for timestamp
    ts_part = ""
    for _ in range(10):
        ts_part = ENCODING[t & 0x1F] + ts_part
        t >>= 5
    # 16 chars for randomness (10 bytes = 80 bits, 16 * 5 = 80)
    rand_bytes = os.urandom(10)
    rand_int = int.from_bytes(rand_bytes, "big")
    rand_part = ""
    for _ in range(16):
        rand_part = ENCODING[rand_int & 0x1F] + rand_part
        rand_int >>= 5
    return ts_part + rand_part


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class Section:
    """A parsed section from the Markdown document."""
    heading_line: int          # 0-based line index of the heading
    heading_text: str          # Raw heading text (without # prefix)
    heading_level: int         # Number of # symbols
    anchor: Optional[str]      # {#anchor-id} if present
    body_start: int            # First line after heading
    body_end: int              # Exclusive — first line of next sibling/parent section
    number: Optional[str]      # Extracted section number (e.g., "15", "11.4")
    slug: str                  # Heading slug for ID resolution
    children: list[Section] = field(default_factory=list)


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
    document_id: str
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
            "document_id": self.document_id,
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
# Document parser
# ---------------------------------------------------------------------------

HEADING_RE = re.compile(r'^(#{1,6})\s+(.*)')
# Two alternations:
#   group 1 — subsection (N.M[.P…]) with optional trailing dot: "5.2 Title" or "5.2. Title"
#   group 2 — top-level (N.) with required trailing dot: "5. Title"
# Bare integers ("5 Things") are not matched, preventing false positives.
SECTION_NUM_RE = re.compile(
    r'^(\d+(?:\.\d+)+)\.?\s+'
    r'|^(\d+)\.\s+'
)
ANCHOR_RE = re.compile(r'\{#([^}]+)\}\s*$')
BLOCK_START_RE = re.compile(r'<!--\s*BLOCK:(\S+)\s*-->')
BLOCK_END_RE = re.compile(r'<!--\s*END\s+BLOCK:(\S+)\s*-->')
ANCHOR_MARKER_RE = re.compile(r'<!--\s*ANCHOR:(\S+)\s*-->')
FRONTMATTER_RE = re.compile(r'^---\s*$')


def slugify(text: str) -> str:
    """Create a heading slug from text."""
    text = ANCHOR_RE.sub('', text).strip()
    text = SECTION_NUM_RE.sub('', text).strip()
    text = re.sub(r'[^\w\s-]', '', text.lower())
    text = re.sub(r'[\s_]+', '-', text).strip('-')
    return text


def parse_sections(lines: list[str]) -> list[Section]:
    """Parse all sections from document lines into a flat list."""
    sections: list[Section] = []
    for i, line in enumerate(lines):
        m = HEADING_RE.match(line)
        if m:
            level = len(m.group(1))
            raw_text = m.group(2).strip()
            # Extract anchor
            anchor_m = ANCHOR_RE.search(raw_text)
            anchor = anchor_m.group(1) if anchor_m else None
            clean_text = ANCHOR_RE.sub('', raw_text).strip()
            # Extract section number
            num_m = SECTION_NUM_RE.match(clean_text)
            number = (num_m.group(1) or num_m.group(2)) if num_m else None
            sections.append(Section(
                heading_line=i,
                heading_text=raw_text,
                heading_level=level,
                anchor=anchor,
                body_start=i + 1,
                body_end=len(lines),  # Will be fixed below
                number=number,
                slug=slugify(raw_text),
            ))
    # Fix body_end: each section ends where the next section at same or
    # higher level begins
    for idx, sec in enumerate(sections):
        for later in sections[idx + 1:]:
            if later.heading_level <= sec.heading_level:
                sec.body_end = later.heading_line
                break
    return sections


def build_section_tree(flat: list[Section]) -> list[Section]:
    """Build a tree from flat section list (for subsection resolution)."""
    root: list[Section] = []
    stack: list[Section] = []
    for sec in flat:
        sec.children = []
        while stack and stack[-1].heading_level >= sec.heading_level:
            stack.pop()
        if stack:
            stack[-1].children.append(sec)
        else:
            root.append(sec)
        stack.append(sec)
    return root


# ---------------------------------------------------------------------------
# ID resolution map
# ---------------------------------------------------------------------------

class IDResolver:
    """Maps section identifiers to Section objects."""

    def __init__(self, sections: list[Section]):
        self._by_number: dict[str, Section] = {}
        self._by_anchor: dict[str, Section] = {}
        self._by_slug: dict[str, Section] = {}
        self._by_heading: dict[str, list[Section]] = {}
        self._provisionals: dict[str, Section] = {}
        for sec in sections:
            if sec.number:
                self._by_number[sec.number] = sec
            if sec.anchor:
                self._by_anchor[sec.anchor] = sec
            if sec.slug:
                self._by_slug[sec.slug] = sec
            self._by_heading.setdefault(sec.heading_text, []).append(sec)

    def resolve(self, section_id: str) -> Optional[Section]:
        """Resolve a section_id string to a Section object."""
        if not section_id:
            return None
        # Provisional namespace
        if section_id.startswith("§new:"):
            key = section_id[5:]  # Strip §new:
            return self._provisionals.get(key)
        # Strip § prefix
        sid = section_id.lstrip("§").strip()
        # Try number
        if sid in self._by_number:
            return self._by_number[sid]
        # Try anchor
        if sid in self._by_anchor:
            return self._by_anchor[sid]
        # Try slug
        if sid in self._by_slug:
            return self._by_slug[sid]
        # Try heading text (only if unambiguous)
        if sid in self._by_heading and len(self._by_heading[sid]) == 1:
            return self._by_heading[sid][0]
        return None

    def register_provisional(self, key: str, section: Section) -> None:
        self._provisionals[key] = section

    def remove(self, section: Section) -> None:
        """Remove a section from all indices."""
        if section.number and self._by_number.get(section.number) is section:
            del self._by_number[section.number]
        if section.anchor and self._by_anchor.get(section.anchor) is section:
            del self._by_anchor[section.anchor]
        if section.slug and self._by_slug.get(section.slug) is section:
            del self._by_slug[section.slug]

    def reindex(self, sections: list[Section]) -> None:
        """Full reindex after structural changes."""
        self._by_number.clear()
        self._by_anchor.clear()
        self._by_slug.clear()
        self._by_heading.clear()
        for sec in sections:
            if sec.number:
                self._by_number[sec.number] = sec
            if sec.anchor:
                self._by_anchor[sec.anchor] = sec
            if sec.slug:
                self._by_slug[sec.slug] = sec
            self._by_heading.setdefault(sec.heading_text, []).append(sec)


# ---------------------------------------------------------------------------
# String matching (3-tier: exact, whitespace-normalized, fuzzy)
# ---------------------------------------------------------------------------

def normalize_ws(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip()


def find_in_scope(lines: list[str], start: int, end: int,
                  target: str,
                  allow_fuzzy: bool = False) -> Optional[tuple[int, int]]:
    """
    Find `target` in lines[start:end].
    Returns (line_start, line_end) inclusive, or None.
    Tries exact match, then whitespace-normalized.
    Tier 3 (fuzzy) only runs if allow_fuzzy is True.
    """
    scope_text = "\n".join(lines[start:end])

    # Tier 1: exact
    idx = scope_text.find(target)
    if idx != -1:
        return _char_to_lines(lines, start, scope_text, idx, len(target))

    # Tier 2: whitespace-normalized
    norm_target = normalize_ws(target)
    if not norm_target:
        return None
    norm_scope = normalize_ws(scope_text)
    if norm_target in norm_scope:
        # Map back to original lines: for each possible starting line,
        # accumulate normalized text forward until the target is found.
        for i in range(start, end):
            accum = ""
            for j in range(i, end):
                if accum:
                    accum += " "
                accum += normalize_ws(lines[j])
                if norm_target in accum:
                    # Verify line i actually contributes: if removing it
                    # still contains the target, then i is not the real
                    # start line — break inner loop and try i+1.
                    if j > i:
                        without_i = normalize_ws(
                            " ".join(normalize_ws(lines[k])
                                     for k in range(i + 1, j + 1)))
                        if norm_target in without_i:
                            break  # i is not needed, try next i
                    return (i, j)
                # Stop extending if accumulator is already much longer
                # than the target (the target can't start on line i)
                if len(accum) > len(norm_target) + 200:
                    break
        # Confirmed present in normalized scope but couldn't map to lines;
        # don't return None — fall through to tier 3 if allowed.
        pass

    # Tier 3: fuzzy — only if explicitly opted in
    if not allow_fuzzy:
        return None

    best_ratio = 0.0
    best_pos = None
    target_words = norm_target.split()
    if not target_words:
        return None
    for i in range(start, end):
        line_norm = normalize_ws(lines[i])
        # Simple word overlap ratio
        line_words = line_norm.split()
        if not line_words:
            continue
        common = len(set(target_words) & set(line_words))
        ratio = common / max(len(target_words), len(line_words))
        if ratio > best_ratio and ratio > 0.85:
            best_ratio = ratio
            best_pos = i
    if best_pos is not None:
        return (best_pos, best_pos)

    return None


def _char_to_lines(lines: list[str], offset: int, scope_text: str,
                   char_idx: int, char_len: int) -> tuple[int, int]:
    """Convert character position in scope_text back to line numbers."""
    if char_len <= 0:
        # Zero-length target: both start and end are the line containing char_idx
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
        line_end = pos + len(line) + 1  # +1 for newline
        if not found_start and pos <= char_idx < line_end:
            start_line = i
            found_start = True
        if pos <= char_idx + char_len - 1 < line_end:
            end_line = i
            break
        pos = line_end
    return (start_line, end_line)


def find_block_markers(lines: list[str], start: int, end: int,
                       name: str) -> Optional[tuple[int, int]]:
    """Find <!-- BLOCK:name --> ... <!-- END BLOCK:name --> in scope."""
    block_start = None
    for i in range(start, end):
        if BLOCK_START_RE.search(lines[i]) and name in lines[i]:
            m = BLOCK_START_RE.search(lines[i])
            if m and m.group(1) == name:
                block_start = i
        if block_start is not None and BLOCK_END_RE.search(lines[i]):
            m = BLOCK_END_RE.search(lines[i])
            if m and m.group(1) == name:
                return (block_start, i)
    return None


def find_anchor(lines: list[str], start: int, end: int,
                name: str) -> Optional[int]:
    """Find <!-- ANCHOR:name --> in scope."""
    for i in range(start, end):
        m = ANCHOR_MARKER_RE.search(lines[i])
        if m and m.group(1) == name:
            return i
    return None


# ---------------------------------------------------------------------------
# Section extraction helpers
# ---------------------------------------------------------------------------

def section_extent(sec: Section) -> tuple[int, int]:
    """Return (start, end) covering heading through body_end."""
    return (sec.heading_line, sec.body_end)


def extract_section_lines(lines: list[str], sec: Section) -> list[str]:
    """Extract all lines belonging to a section (heading + body + subs)."""
    start, end = section_extent(sec)
    return lines[start:end]


def remove_section_lines(lines: list[str], sec: Section) -> list[str]:
    """Return lines with the section removed."""
    start, end = section_extent(sec)
    return lines[:start] + lines[end:]


def find_section_insert_point(lines: list[str], sections: list[Section],
                              after_id: str, resolver: IDResolver) -> Optional[int]:
    """Find the line index to insert after a given section."""
    target = resolver.resolve(after_id)
    if target is None:
        return None
    _, end = section_extent(target)
    return end


def get_intro_body(lines: list[str], sec: Section,
                   all_sections: list[Section]) -> tuple[int, int]:
    """
    Get the intro body range (heading+1 to first child subsection).
    Returns (start, end) exclusive.
    """
    start = sec.body_start
    # Find first child subsection
    for other in all_sections:
        if (other.heading_line > sec.heading_line and
                other.heading_line < sec.body_end and
                other.heading_level > sec.heading_level):
            return (start, other.heading_line)
    return (start, sec.body_end)


# ---------------------------------------------------------------------------
# Frontmatter handling
# ---------------------------------------------------------------------------

def parse_frontmatter(lines: list[str]) -> tuple[Optional[dict], int, int]:
    """
    Parse YAML frontmatter if present.
    Returns (parsed_dict_or_None, start_line, end_line_exclusive).
    """
    if not lines or not FRONTMATTER_RE.match(lines[0]):
        return (None, 0, 0)
    for i in range(1, len(lines)):
        if FRONTMATTER_RE.match(lines[i]):
            # Simple YAML key: value parsing (no nested structures)
            fm: dict[str, str] = {}
            for line in lines[1:i]:
                if ':' in line:
                    key, _, val = line.partition(':')
                    fm[key.strip()] = val.strip()
            return (fm, 0, i + 1)
    return (None, 0, 0)


def serialize_frontmatter(fm: dict) -> list[str]:
    """Serialize a frontmatter dict back to lines."""
    result = ["---"]
    for k, v in fm.items():
        result.append(f"{k}: {v}")
    result.append("---")
    return result


# ---------------------------------------------------------------------------
# Operation implementations
# ---------------------------------------------------------------------------

class PatchApplier:
    """Applies a doc-patch envelope to a document."""

    def __init__(self, source_text: str, patch: dict, output_dir: str = ".",
                 dry_run: bool = False):
        self.source_text = source_text
        self.patch = patch
        self.output_dir = output_dir
        self.dry_run = dry_run
        self.lines: list[str] = source_text.splitlines()
        self.original_lines: list[str] = list(self.lines)
        self.sections: list[Section] = []
        self.resolver: Optional[IDResolver] = None
        self.warnings: list[str] = []
        self.op_results: list[OpResult] = []
        self.assertion_failed = False

    def _reparse(self) -> None:
        """Re-parse sections from current lines and rebuild resolver."""
        self.sections = parse_sections(self.lines)
        if self.resolver:
            self.resolver.reindex(self.sections)
        else:
            self.resolver = IDResolver(self.sections)

    def _resolve(self, section_id: str) -> Optional[Section]:
        assert self.resolver is not None
        return self.resolver.resolve(section_id)

    def _scope(self, section_id: Optional[str]) -> tuple[int, int]:
        """Return (start, end) scope for an operation."""
        if section_id:
            sec = self._resolve(section_id)
            if sec:
                return section_extent(sec)
        return (0, len(self.lines))

    # --- Individual op handlers ---

    def _op_assert(self, op: dict) -> OpResult:
        """Check assertion against ORIGINAL document."""
        section_id = op.get("section_id")
        contains = op.get("contains", "")
        # Assertions check the original, not the working copy
        orig_sections = parse_sections(self.original_lines)
        orig_resolver = IDResolver(orig_sections)
        if section_id:
            sec = orig_resolver.resolve(section_id)
            if sec is None:
                return OpResult(0, False, "SECTION_NOT_FOUND",
                                f"Section '{section_id}' not found in original.")
            start, end = section_extent(sec)
            scope_text = "\n".join(self.original_lines[start:end])
        else:
            scope_text = "\n".join(self.original_lines)
        if contains not in scope_text:
            norm_contains = normalize_ws(contains)
            norm_scope = normalize_ws(scope_text)
            if norm_contains not in norm_scope:
                return OpResult(0, False, "ASSERTION_FAILED",
                                f"'{contains}' not found in scope.")
        return OpResult(0, True)

    def _op_move_section(self, op: dict) -> OpResult:
        section_id = op.get("section_id", "")
        to_after = op.get("to_after", "")
        sec = self._resolve(section_id)
        if sec is None:
            return OpResult(0, False, "SECTION_NOT_FOUND",
                            f"Section '{section_id}' not found.")
        target_sec = self._resolve(to_after)
        if target_sec is None:
            return OpResult(0, False, "SECTION_NOT_FOUND",
                            f"Target section '{to_after}' not found.")
        extracted = extract_section_lines(self.lines, sec)
        self.lines = remove_section_lines(self.lines, sec)
        self._reparse()
        insert_at = find_section_insert_point(
            self.lines, self.sections, to_after, self.resolver)
        if insert_at is None:
            return OpResult(0, False, "SECTION_NOT_FOUND",
                            f"Could not find insert point after '{to_after}'.")
        self.lines = self.lines[:insert_at] + extracted + self.lines[insert_at:]
        self._reparse()
        return OpResult(0, True)

    def _op_swap_sections(self, op: dict) -> OpResult:
        sid_a = op.get("section_a", "")
        sid_b = op.get("section_b", "")
        sec_a = self._resolve(sid_a)
        sec_b = self._resolve(sid_b)
        if sec_a is None:
            return OpResult(0, False, "SECTION_NOT_FOUND",
                            f"Section '{sid_a}' not found.")
        if sec_b is None:
            return OpResult(0, False, "SECTION_NOT_FOUND",
                            f"Section '{sid_b}' not found.")
        # Ensure a comes before b
        if sec_a.heading_line > sec_b.heading_line:
            sec_a, sec_b = sec_b, sec_a
        lines_a = extract_section_lines(self.lines, sec_a)
        lines_b = extract_section_lines(self.lines, sec_b)
        a_start, a_end = section_extent(sec_a)
        b_start, b_end = section_extent(sec_b)
        # Replace b first (higher index), then a
        self.lines = (self.lines[:a_start] + lines_b +
                      self.lines[a_end:b_start] + lines_a +
                      self.lines[b_end:])
        self._reparse()
        return OpResult(0, True)

    def _op_merge_sections(self, op: dict) -> OpResult:
        source_id = op.get("source_id", "")
        target_id = op.get("target_id", "")
        strategy = op.get("strategy", "append_as_subsections")
        source = self._resolve(source_id)
        target = self._resolve(target_id)
        if source is None:
            return OpResult(0, False, "SECTION_NOT_FOUND",
                            f"Source '{source_id}' not found.")
        if target is None:
            return OpResult(0, False, "SECTION_NOT_FOUND",
                            f"Target '{target_id}' not found.")
        source_lines = extract_section_lines(self.lines, source)
        # Remove source heading, keep body
        source_body = source_lines[1:]  # Skip heading
        _, t_end = section_extent(target)
        if strategy == "prepend_as_subsections":
            insert_at = target.body_start
        else:  # append_as_subsections
            insert_at = t_end
        # Remove source first
        self.lines = remove_section_lines(self.lines, source)
        self._reparse()
        # Recalculate insert point
        target = self._resolve(target_id)
        if target is None:
            return OpResult(0, False, "SECTION_NOT_FOUND",
                            f"Target '{target_id}' lost after source removal.")
        _, t_end = section_extent(target)
        if strategy == "prepend_as_subsections":
            insert_at = target.body_start
        else:
            insert_at = t_end
        self.lines = self.lines[:insert_at] + source_body + self.lines[insert_at:]
        self._reparse()
        return OpResult(0, True)

    def _op_absorb_section(self, op: dict) -> OpResult:
        source_id = op.get("source_id", "")
        target_id = op.get("target_id", "")
        placement = op.get("placement", "append_as_outro")
        source = self._resolve(source_id)
        target = self._resolve(target_id)
        if source is None:
            return OpResult(0, False, "SECTION_NOT_FOUND",
                            f"Source '{source_id}' not found.")
        if target is None:
            return OpResult(0, False, "SECTION_NOT_FOUND",
                            f"Target '{target_id}' not found.")
        # Extract source body only (no heading)
        source_all = extract_section_lines(self.lines, source)
        source_body = source_all[1:]
        # Remove source
        self.lines = remove_section_lines(self.lines, source)
        self._reparse()
        target = self._resolve(target_id)
        if target is None:
            return OpResult(0, False, "SECTION_NOT_FOUND",
                            f"Target '{target_id}' lost after source removal.")
        intro_start, intro_end = get_intro_body(
            self.lines, target, self.sections)
        if placement == "prepend_as_intro":
            insert_at = intro_start
        else:  # append_as_outro
            insert_at = intro_end
        self.lines = self.lines[:insert_at] + source_body + self.lines[insert_at:]
        self._reparse()
        return OpResult(0, True)

    def _op_split_section(self, op: dict) -> OpResult:
        section_id = op.get("section_id", "")
        split_after = op.get("split_after", "")
        new_heading = op.get("new_section_heading", "New Section")
        new_id = op.get("new_section_id", "")
        sec = self._resolve(section_id)
        if sec is None:
            return OpResult(0, False, "SECTION_NOT_FOUND",
                            f"Section '{section_id}' not found.")
        start, end = section_extent(sec)
        match = find_in_scope(self.lines, start, end, split_after,
                              allow_fuzzy=op.get("allow_fuzzy", False))
        if match is None:
            return OpResult(0, False, "FIND_NOT_MATCHED",
                            f"Split boundary '{split_after}' not found.")
        split_line = match[1] + 1  # After the matched content
        # Everything from split_line to end becomes new section
        new_heading_line = f"{'#' * sec.heading_level} {new_heading}"
        new_sec_lines = [new_heading_line] + self.lines[split_line:end]
        # The new heading will be inserted at index split_line
        new_heading_idx = split_line
        # Truncate original section
        self.lines = self.lines[:split_line] + new_sec_lines + self.lines[end:]
        self._reparse()
        # Register provisional ID
        if new_id and new_id.startswith("§new:"):
            key = new_id[5:]
            # Find the section whose heading is at the known insertion line
            for s in self.sections:
                if s.heading_line == new_heading_idx:
                    self.resolver.register_provisional(key, s)
                    break
        return OpResult(0, True)

    def _op_delete_section(self, op: dict) -> OpResult:
        section_id = op.get("section_id", "")
        sec = self._resolve(section_id)
        if sec is None:
            return OpResult(0, False, "SECTION_NOT_FOUND",
                            f"Section '{section_id}' not found.")
        self.lines = remove_section_lines(self.lines, sec)
        self._reparse()
        return OpResult(0, True)

    def _op_replace_block(self, op: dict) -> OpResult:
        section_id = op.get("section_id", "")
        target = op.get("target", "")
        new_content = op.get("new_content", "")
        start, end = self._scope(section_id)
        # Try block markers first
        block_name = None
        bm = BLOCK_START_RE.search(target)
        if bm:
            block_name = bm.group(1)
        if block_name:
            markers = find_block_markers(self.lines, start, end, block_name)
            if markers:
                b_start, b_end = markers
                new_lines = new_content.splitlines() if new_content else []
                self.lines = self.lines[:b_start] + new_lines + self.lines[b_end + 1:]
                self._reparse()
                return OpResult(0, True)
        # Fallback: string match
        match = find_in_scope(self.lines, start, end, target,
                              allow_fuzzy=op.get("allow_fuzzy", False))
        if match is None:
            return OpResult(0, False, "FIND_NOT_MATCHED",
                            f"Target '{target[:60]}' not found in scope.")
        m_start, m_end = match
        new_lines = new_content.splitlines() if new_content else []
        self.lines = self.lines[:m_start] + new_lines + self.lines[m_end + 1:]
        self._reparse()
        return OpResult(0, True)

    def _op_delete_block(self, op: dict) -> OpResult:
        op_copy = dict(op)
        op_copy["new_content"] = ""
        return self._op_replace_block(op_copy)

    def _op_insert_block(self, op: dict) -> OpResult:
        section_id = op.get("section_id")
        after_anchor = op.get("after_anchor", "")
        new_content = op.get("new_content", "")
        start, end = self._scope(section_id)
        # Try anchor marker
        anchor_name = None
        am = ANCHOR_MARKER_RE.search(after_anchor)
        if am:
            anchor_name = am.group(1)
        elif after_anchor.startswith("<!-- ANCHOR:"):
            anchor_name = after_anchor.replace("<!-- ANCHOR:", "").replace("-->", "").strip()
        if anchor_name:
            pos = find_anchor(self.lines, start, end, anchor_name)
            if pos is not None:
                new_lines = new_content.splitlines()
                self.lines = self.lines[:pos + 1] + new_lines + self.lines[pos + 1:]
                self._reparse()
                return OpResult(0, True)
        # Fallback: string match for anchor
        match = find_in_scope(self.lines, start, end, after_anchor)
        if match is None:
            return OpResult(0, False, "BLOCK_NOT_FOUND",
                            f"Anchor '{after_anchor[:60]}' not found.")
        new_lines = new_content.splitlines()
        insert_at = match[1] + 1
        self.lines = self.lines[:insert_at] + new_lines + self.lines[insert_at:]
        self._reparse()
        return OpResult(0, True)

    def _op_move_block(self, op: dict) -> OpResult:
        source_section = op.get("source_section_id", "")
        source_target = op.get("source_target", "")
        target_section = op.get("target_section_id")
        after_anchor = op.get("after_anchor", "")
        # Find and extract source block
        s_start, s_end = self._scope(source_section)
        block_name = None
        bm = BLOCK_START_RE.search(source_target)
        if bm:
            block_name = bm.group(1)
        extracted_lines: list[str] = []
        if block_name:
            markers = find_block_markers(self.lines, s_start, s_end, block_name)
            if markers:
                b_start, b_end = markers
                extracted_lines = self.lines[b_start:b_end + 1]
                self.lines = self.lines[:b_start] + self.lines[b_end + 1:]
                self._reparse()
            else:
                return OpResult(0, False, "BLOCK_NOT_FOUND",
                                f"Source block '{source_target[:60]}' not found.")
        else:
            match = find_in_scope(self.lines, s_start, s_end, source_target)
            if match is None:
                return OpResult(0, False, "FIND_NOT_MATCHED",
                                f"Source '{source_target[:60]}' not found.")
            m_start, m_end = match
            extracted_lines = self.lines[m_start:m_end + 1]
            self.lines = self.lines[:m_start] + self.lines[m_end + 1:]
            self._reparse()
        # Insert at target
        t_start, t_end = self._scope(target_section)
        anchor_name = after_anchor.replace("<!-- ANCHOR:", "").replace("-->", "").strip()
        pos = find_anchor(self.lines, t_start, t_end, anchor_name)
        if pos is not None:
            self.lines = self.lines[:pos + 1] + extracted_lines + self.lines[pos + 1:]
        else:
            match = find_in_scope(self.lines, t_start, t_end, after_anchor)
            if match is None:
                return OpResult(0, False, "BLOCK_NOT_FOUND",
                                f"Target anchor '{after_anchor[:60]}' not found.")
            insert_at = match[1] + 1
            self.lines = self.lines[:insert_at] + extracted_lines + self.lines[insert_at:]
        self._reparse()
        return OpResult(0, True)

    def _op_copy_block(self, op: dict) -> OpResult:
        source_section = op.get("source_section_id", "")
        source_target = op.get("source_target", "")
        target_section = op.get("target_section_id")
        after_anchor = op.get("after_anchor", "")
        s_start, s_end = self._scope(source_section)
        # Find source
        block_name = None
        bm = BLOCK_START_RE.search(source_target)
        if bm:
            block_name = bm.group(1)
        copied_lines: list[str] = []
        if block_name:
            markers = find_block_markers(self.lines, s_start, s_end, block_name)
            if markers:
                b_start, b_end = markers
                copied_lines = list(self.lines[b_start:b_end + 1])
            else:
                return OpResult(0, False, "BLOCK_NOT_FOUND",
                                f"Source block '{source_target[:60]}' not found.")
        else:
            match = find_in_scope(self.lines, s_start, s_end, source_target)
            if match is None:
                return OpResult(0, False, "FIND_NOT_MATCHED",
                                f"Source '{source_target[:60]}' not found.")
            m_start, m_end = match
            copied_lines = list(self.lines[m_start:m_end + 1])
        # Insert at target
        t_start, t_end = self._scope(target_section)
        anchor_name = after_anchor.replace("<!-- ANCHOR:", "").replace("-->", "").strip()
        pos = find_anchor(self.lines, t_start, t_end, anchor_name)
        if pos is not None:
            self.lines = self.lines[:pos + 1] + copied_lines + self.lines[pos + 1:]
        else:
            match = find_in_scope(self.lines, t_start, t_end, after_anchor)
            if match is None:
                return OpResult(0, False, "BLOCK_NOT_FOUND",
                                f"Target anchor '{after_anchor[:60]}' not found.")
            insert_at = match[1] + 1
            self.lines = self.lines[:insert_at] + copied_lines + self.lines[insert_at:]
        self._reparse()
        return OpResult(0, True)

    def _op_edit_text(self, op: dict) -> OpResult:
        section_id = op.get("section_id", "")
        find_str = op.get("find", "")
        replace_str = op.get("replace", "")
        allow_fuzzy = op.get("allow_fuzzy", False)
        start, end = self._scope(section_id)
        match = find_in_scope(self.lines, start, end, find_str,
                              allow_fuzzy=allow_fuzzy)
        if match is None:
            # Find closest match for error reporting
            closest = None
            best_overlap = 0
            find_words = set(normalize_ws(find_str).lower().split())
            for i in range(start, end):
                line_words = set(normalize_ws(self.lines[i]).lower().split())
                overlap = len(find_words & line_words)
                if overlap > best_overlap:
                    best_overlap = overlap
                    closest = self.lines[i].strip()
            return OpResult(0, False, "FIND_NOT_MATCHED",
                            f"No match for '{find_str[:60]}'.",
                            closest)
        m_start, m_end = match
        scope_text = "\n".join(self.lines[m_start:m_end + 1])
        new_text = scope_text.replace(find_str, replace_str, 1)
        # If exact replace didn't work, try whitespace-normalized replace
        if new_text == scope_text:
            # The match was found via tier 2 (normalized) or tier 3 (fuzzy).
            # Do a character-level normalized replacement that preserves
            # surrounding content on the matched lines.
            norm_find = normalize_ws(find_str)
            # Build a char-level map: for each char in the normalized
            # scope_text, record its index in the original scope_text.
            norm_chars: list[int] = []  # norm_chars[i] = original index
            in_ws = False
            for ci, ch in enumerate(scope_text):
                is_ws = ch in ' \t\n\r'
                if is_ws:
                    if not in_ws:
                        in_ws = True
                        norm_chars.append(ci)  # collapsed space
                else:
                    in_ws = False
                    norm_chars.append(ci)
            # Build the normalized string from the map to stay in sync
            norm_from_map = ""
            for idx in norm_chars:
                ch = scope_text[idx]
                norm_from_map += ' ' if ch in ' \t\n\r' else ch
            norm_from_map = norm_from_map.strip()
            # Strip leading whitespace entries from norm_chars
            strip_count = 0
            for idx in norm_chars:
                if scope_text[idx] in ' \t\n\r':
                    strip_count += 1
                else:
                    break
            trimmed = norm_chars[strip_count:]
            # Find norm_find in the stripped normalized text
            nf_idx = norm_from_map.find(norm_find)
            if nf_idx != -1 and nf_idx + len(norm_find) <= len(trimmed):
                orig_start = trimmed[nf_idx]
                orig_end = trimmed[nf_idx + len(norm_find) - 1] + 1
                new_text = scope_text[:orig_start] + replace_str + scope_text[orig_end:]
            else:
                # Fallback: replace entire matched region
                new_text = replace_str
        new_lines = new_text.splitlines() if new_text else []
        self.lines = self.lines[:m_start] + new_lines + self.lines[m_end + 1:]
        self._reparse()
        return OpResult(0, True)

    def _op_rename_section(self, op: dict) -> OpResult:
        section_id = op.get("section_id", "")
        new_heading = op.get("new_heading", "")
        sec = self._resolve(section_id)
        if sec is None:
            return OpResult(0, False, "SECTION_NOT_FOUND",
                            f"Section '{section_id}' not found.")
        prefix = "#" * sec.heading_level + " "
        # Preserve anchor if present
        anchor_part = ""
        if sec.anchor:
            anchor_part = f" {{#{sec.anchor}}}"
        self.lines[sec.heading_line] = f"{prefix}{new_heading}{anchor_part}"
        self._reparse()
        return OpResult(0, True)

    def _op_rewrite_section(self, op: dict) -> OpResult:
        section_id = op.get("section_id", "")
        new_content = op.get("new_content", "")
        sec = self._resolve(section_id)
        if sec is None:
            return OpResult(0, False, "SECTION_NOT_FOUND",
                            f"Section '{section_id}' not found.")
        intro_start, intro_end = get_intro_body(
            self.lines, sec, self.sections)
        new_lines = new_content.splitlines()
        self.lines = self.lines[:intro_start] + new_lines + self.lines[intro_end:]
        self._reparse()
        return OpResult(0, True)

    def _op_update_frontmatter(self, op: dict) -> OpResult:
        set_fields = op.get("set", {})
        _, _fm_start, fm_end = parse_frontmatter(self.lines)
        if fm_end == 0:
            # No frontmatter — prepend a minimal new block
            new_lines = (["---"] +
                         [f"{k}: {v}" for k, v in set_fields.items()] +
                         ["---"])
            self.lines = new_lines + self.lines
            self._reparse()
            return OpResult(0, True)
        # Frontmatter exists — surgically replace matching top-level keys in the
        # raw lines and append any keys that are absent, preserving all complex
        # YAML (block scalars, sequences, nested objects) verbatim.
        body = list(self.lines[1:fm_end - 1])
        remaining = dict(set_fields)
        for idx, line in enumerate(body):
            if not line.startswith((' ', '\t', '-')) and ':' in line:
                key, _, _ = line.partition(':')
                key = key.strip()
                if key in remaining:
                    body[idx] = f"{key}: {remaining.pop(key)}"
        for key, val in remaining.items():
            body.append(f"{key}: {val}")
        self.lines = ["---"] + body + ["---"] + self.lines[fm_end:]
        self._reparse()
        return OpResult(0, True)

    def _op_inject_markers(self, op: dict) -> OpResult:
        section_id = op.get("section_id", "")
        markers = op.get("markers", [])
        sec = self._resolve(section_id) if section_id else None
        if section_id and sec is None:
            return OpResult(0, False, "SECTION_NOT_FOUND",
                            f"Section '{section_id}' not found.")
        start = sec.heading_line if sec else 0
        end = sec.body_end if sec else len(self.lines)
        offset = 0  # Track insertions
        for marker in markers:
            mtype = marker.get("type")
            if mtype == "block":
                name = marker.get("name", "")
                wraps = marker.get("wraps", "")
                wraps_end = marker.get("wraps_end", "")
                # Find wraps line
                w_match = find_in_scope(
                    self.lines, start + offset, end + offset, wraps)
                if w_match is None:
                    self.warnings.append(
                        f"inject_markers: could not find '{wraps[:40]}' for block '{name}'")
                    continue
                # Insert BLOCK start before wraps
                self.lines.insert(w_match[0], f"<!-- BLOCK:{name} -->")
                offset += 1
                # Find wraps_end
                we_match = find_in_scope(
                    self.lines, w_match[0] + 1, end + offset, wraps_end)
                if we_match is None:
                    self.warnings.append(
                        f"inject_markers: could not find '{wraps_end[:40]}' for block end '{name}'")
                    continue
                self.lines.insert(we_match[1] + 1, f"<!-- END BLOCK:{name} -->")
                offset += 1
            elif mtype == "anchor":
                name = marker.get("name", "")
                after = marker.get("after", "")
                a_match = find_in_scope(
                    self.lines, start + offset, end + offset, after)
                if a_match is None:
                    self.warnings.append(
                        f"inject_markers: could not find '{after[:40]}' for anchor '{name}'")
                    continue
                self.lines.insert(a_match[1] + 1, f"<!-- ANCHOR:{name} -->")
                offset += 1
            elif mtype == "section_anchor":
                anchor_id = marker.get("anchor_id", "")
                if sec:
                    # Re-locate the heading line in the current (possibly shifted)
                    # state by scanning for the original heading text.
                    h_idx = None
                    heading_prefix = "#" * sec.heading_level + " "
                    for scan_i in range(start, min(start + offset + 2, len(self.lines))):
                        if self.lines[scan_i].startswith(heading_prefix):
                            candidate = self.lines[scan_i][len(heading_prefix):]
                            # Match by slug or original heading text
                            if (slugify(candidate) == sec.slug or
                                    ANCHOR_RE.sub('', candidate).strip() ==
                                    ANCHOR_RE.sub('', sec.heading_text).strip()):
                                h_idx = scan_i
                                break
                    if h_idx is None:
                        # Fallback: use offset arithmetic
                        h_idx = sec.heading_line + offset
                        if h_idx >= len(self.lines):
                            self.warnings.append(
                                f"inject_markers: could not relocate heading "
                                f"for section_anchor '{anchor_id}'")
                            continue
                    heading = self.lines[h_idx]
                    desired = f"{{#{anchor_id}}}"
                    existing_anchor = ANCHOR_RE.search(heading)
                    if existing_anchor:
                        existing_id = existing_anchor.group(1)
                        if existing_id == anchor_id:
                            # Already has matching anchor — no-op
                            pass
                        else:
                            # Different anchor exists — replace it
                            self.lines[h_idx] = ANCHOR_RE.sub(
                                desired, heading)
                            self.warnings.append(
                                f"inject_markers: replaced existing anchor "
                                f"{{#{existing_id}}} with {desired} on "
                                f"section '{sec.heading_text}'")
                    else:
                        # No anchor — append
                        self.lines[h_idx] = heading.rstrip() + f" {desired}"
        self._reparse()
        return OpResult(0, True)

    # --- Dispatch ---

    OP_HANDLERS = {
        "assert": "_op_assert",
        "move_section": "_op_move_section",
        "swap_sections": "_op_swap_sections",
        "merge_sections": "_op_merge_sections",
        "absorb_section": "_op_absorb_section",
        "split_section": "_op_split_section",
        "delete_section": "_op_delete_section",
        "replace_block": "_op_replace_block",
        "delete_block": "_op_delete_block",
        "insert_block": "_op_insert_block",
        "move_block": "_op_move_block",
        "copy_block": "_op_copy_block",
        "edit_text": "_op_edit_text",
        "rename_section": "_op_rename_section",
        "rewrite_section": "_op_rewrite_section",
        "update_frontmatter": "_op_update_frontmatter",
        "inject_markers": "_op_inject_markers",
    }

    def _apply_op(self, index: int, op: dict) -> OpResult:
        op_type = op.get("op", "")
        handler_name = self.OP_HANDLERS.get(op_type)
        if handler_name is None:
            return OpResult(index, False, "UNKNOWN_OP",
                            f"Unknown operation type: '{op_type}'")
        handler = getattr(self, handler_name)
        result = handler(op)
        result.index = index
        return result

    # --- Main apply logic ---

    def apply(self) -> tuple[str, dict, str]:
        """
        Apply the patch.
        Returns (STATUS, EXECUTION_REPORT_dict, LAST_STABLE_description).
        """
        patch_id = self.patch.get("patch_id", "unknown")
        document_id = self.patch.get("document_id", "unknown")
        apply_mode = self.patch.get("apply_mode", "atomic")
        source_hash = "sha256:" + hashlib.sha256(
            self.source_text.encode()).hexdigest()

        report = ExecutionReport(
            patch_id=patch_id,
            document_id=document_id,
            status="not_attempted",
            apply_mode=apply_mode,
            source_hash=source_hash,
        )

        # --- Envelope validation ---
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
                "detail": "edits array is empty with patch status "
                          f"'{patch_status}'. Minimum 1 edit required.",
            }]
            return ("envelope_error", report.to_dict(), "B (unchanged)")

        # --- Apply ops ---
        self._reparse()
        applied: list[int] = []
        skipped: list[dict] = []
        errors: list[dict] = []

        for i, op in enumerate(edits):
            if self.assertion_failed:
                # Under best_effort, skip remaining after assertion failure
                skipped.append({
                    "index": i,
                    "error_type": "SKIPPED_AFTER_ASSERTION",
                    "detail": "Skipped due to prior assertion failure.",
                })
                continue

            result = self._apply_op(i, op)

            if result.success:
                applied.append(i)
            else:
                err = {
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
                        skipped.append({
                            "index": i,
                            "error_type": result.error_type,
                            "detail": result.detail,
                        })
                        errors.append(err)
                        continue

                if apply_mode == "atomic":
                    report.status = "discarded"
                    report.errors = [err]
                    return ("discarded", report.to_dict(), "B (unchanged)")
                else:
                    skipped.append({
                        "index": i,
                        "error_type": result.error_type,
                        "detail": result.detail,
                    })
                    errors.append(err)

        # --- Determine STATUS ---
        if not applied and skipped:
            status = "no_change"
        elif skipped:
            status = "partial_success"
        else:
            status = "full_success"

        # --- Post-apply: verify source unmodified (spec step 6) ---
        # Rejoin original_lines and compare against the stored source_text.
        # Use the same representation to avoid false positives from
        # splitlines/join asymmetry (trailing newlines, etc.).
        reconstructed = "\n".join(self.original_lines)
        original_repr = self.source_text.rstrip("\n")
        if reconstructed.rstrip("\n") != original_repr:
            self.warnings.append(
                "Source document original_lines were modified during patch "
                "application! This indicates a bug in the applier.")

        # --- Post-apply: compute hashes ---
        result_text = "\n".join(self.lines)
        result_hash = "sha256:" + hashlib.sha256(
            result_text.encode()).hexdigest()

        # --- Build goals_actual ---
        applied_set = set(applied)  # O(1) lookups
        goals_covered = self.patch.get("goals_covered", [])
        goals_actual = []
        for gc in goals_covered:
            indices = gc.get("edit_indices", [])
            applied_indices = [i for i in indices if i in applied_set]
            skipped_indices = [i for i in indices if i not in applied_set]
            if skipped_indices and not applied_indices:
                actual_status = "not_applied"
            elif skipped_indices:
                actual_status = "partial"
            else:
                actual_status = "done"
            goals_actual.append({
                "goal": gc.get("goal", ""),
                "planned_status": gc.get("status", ""),
                "actual_status": actual_status,
                "planned_indices": indices,
                "applied_indices": applied_indices,
                "skipped_indices": skipped_indices,
            })

        # --- Write working copy ---
        ulid = generate_ulid()
        working_copy_name = f"{document_id}.{ulid}.md"
        working_copy_path = os.path.join(self.output_dir, working_copy_name)

        report.status = status
        report.applied_ops = applied
        report.skipped_ops = skipped
        report.errors = errors
        report.goals_actual = goals_actual
        report.warnings = list(self.warnings)
        report.dry_run = self.dry_run

        if status in ("full_success", "partial_success"):
            report.result_hash = result_hash
            report.working_copy_path = working_copy_name
            # Always write the working copy (for inspection in dry-run,
            # for promotion in real runs)
            Path(working_copy_path).write_text(result_text + "\n",
                                               encoding="utf-8")

        # LAST_STABLE: in dry-run, report hypothetical outcome
        last_stable = "C (promoted)" if status == "full_success" else "B (unchanged)"
        if self.dry_run and status == "full_success":
            last_stable = "C (would be promoted — dry run)"

        return (status, report.to_dict(), last_stable)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="doc-patch applier — apply a patch envelope to a Markdown document.")
    parser.add_argument("source", help="Path to the source Markdown document.")
    parser.add_argument("patch", help="Path to the patch envelope JSON file.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Compute results without writing working copy.")
    parser.add_argument("--output-dir", default=".",
                        help="Directory for the working copy (default: cwd).")
    args = parser.parse_args()

    source_text = Path(args.source).read_text(encoding="utf-8")
    patch = json.loads(Path(args.patch).read_text(encoding="utf-8"))

    applier = PatchApplier(source_text, patch,
                           output_dir=args.output_dir,
                           dry_run=args.dry_run)
    status, report, last_stable = applier.apply()

    output = {
        "STATUS": status,
        "EXECUTION_REPORT": report,
        "LAST_STABLE": last_stable,
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()