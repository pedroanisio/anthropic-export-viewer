---
name: code-patch
description: >
  Apply a structured JSON patch envelope to source code files. Supports
  Python, JavaScript, TypeScript, Rust, HTML, and CSS. Operations: rename,
  replace, delete, move symbols; add/remove imports; find/replace within
  scope; BLOCK/ANCHOR markers; decorator injection. Produces a deterministic
  EXECUTION_REPORT with per-op status, content hash, and a ULID-named
  working copy. Use when the user says: "apply code patch", "structured
  edit", "patch envelope", "rename function", "rename class", "move symbol",
  "delete function", "add import", "remove import", "replace the body of",
  "refactor this function", "reorganize imports", "restructure the code",
  "batch edit", "surgical code change", "swap these functions", "change
  the signature", "inject a decorator", "find and replace in this function",
  or provides a JSON object with "op" fields targeting source code. Also
  trigger for batch mutations with an audit trail, or any targeted,
  auditable source code changes without rewriting the whole file.
---

# Code-Patch

Apply a JSON patch envelope to a source file. The executor
(`apply_code_patch.py`) is the source of truth — read `--help` before
anything else.

---

## Quick start

```bash
# Resolve the skill's install path (varies by environment)
SCRIPT="$(dirname "$(readlink -f "$0")")/scripts/apply_code_patch.py"
# Or use the absolute path directly:
python /mnt/skills/user/code-patch/scripts/apply_code_patch.py --help
python /mnt/skills/user/code-patch/scripts/apply_code_patch.py <source_file> <patch.json> [--dry-run] [--verbose]
```

`--verbose` (`-v`) prints the parsed symbol table and per-op results
to stderr — invaluable when debugging `SYMBOL_NOT_FOUND` or
`FIND_NOT_MATCHED` errors. Stdout remains pure JSON regardless.

Stdout is always a JSON object:
```json
{
  "STATUS": "full_success | partial_success | no_change | discarded | blocked | envelope_error | not_attempted",
  "EXECUTION_REPORT": { ... },
  "LAST_STABLE": "C (promoted) | B (unchanged) | C (would be promoted — dry run)"
}
```

---

## Workflow

### Phase 0 — Orient

Read the target file to understand its structure:
- What language? (python / javascript / typescript / rust / html / css)
- What symbols exist? (functions, classes, imports, rules …)
- Read `references/language-profiles.md` for the target language's symbol ID format.

### Phase 1 — Build the patch envelope

Read `references/envelope-schema.md` for the full JSON schema.

Minimum required fields:
```json
{
  "patch_id": "<ULID>",
  "file_id": "path/to/file.py",
  "language": "python",
  "apply_mode": "atomic",
  "edits": [ ... ]
}
```

Read `references/op-reference.md` for all available operations and their
required fields.

**Before generating symbol IDs:**
- Verify symbol names by reading the source file — never invent names.
- Use type-qualified IDs (`"function:foo"`, `"class:Bar"`) to avoid
  ambiguity when a file has both a class and a function with the same name.

### Phase 2 — Dry run

Always run with `--dry-run` first:

```bash
python /mnt/skills/user/code-patch/scripts/apply_code_patch.py <file> patch.json --dry-run
```

Check `STATUS` from stdout:
- `full_success` → all ops applied; inspect working copy before promoting.
- `partial_success` → some ops skipped; review `skipped_ops` in the report.
- `discarded` / `blocked` → error; read `errors[0]` and fix the envelope.
- `envelope_error` → invalid envelope; fix schema issues.

### Phase 3 — Handle result

| STATUS | Action |
|---|---|
| `full_success` | Promote: `cp <working_copy_path> <file_id>` |
| `partial_success` | Show user `skipped_ops`; ask to promote or abort |
| `discarded` | Show `errors[0].detail`; fix envelope; retry |
| `blocked` | Assertion failed; show which op blocked; do NOT promote |
| `envelope_error` | Fix envelope schema; retry |
| `not_attempted` | Patch has `status: "blocked"`; nothing was applied |

**Never promote a working copy on `partial_success` without user confirmation.**

### Phase 4 — Promote (non-dry-run run)

If the user approves:
```bash
python /mnt/skills/user/code-patch/scripts/apply_code_patch.py <file> patch.json --output-dir <dir>
```

Then promote the working copy:
```bash
cp <output_dir>/<working_copy_path> <file_id>
```

### Phase 5 — Report

Present to the user:
1. Final `STATUS`
2. `goals_actual` summary (which goals were `done` / `partial` / `not_applied`)
3. `result_hash` for audit trail
4. Any `warnings` from the report

---

## Error recovery

Read `references/error-codes.md` for all error types and recovery steps.

Common fixes:

| Error | Fix |
|---|---|
| `SYMBOL_NOT_FOUND` | Check symbol exists in file; use type-qualified ID |
| `FIND_NOT_MATCHED` | Verify exact text; check for whitespace differences |
| `HASH_MISMATCH` | Re-read source file to get current hash; update `base_hash` |
| `UNSUPPORTED_LANGUAGE` | Use one of: python, javascript, typescript, rust, html, css |
| `IMPORT_NOT_FOUND` | Check exact import statement spelling |

---

## Key principles

**Never invent symbol names.** Read the source file first. If a symbol ID
fails to resolve, `SYMBOL_NOT_FOUND` will stop the patch — check the
actual file contents before retrying.

**Dry run first, always.** The working copy is cheap. Promoting the wrong
content is not.

**Atomic by default.** `apply_mode: "atomic"` means one failure stops
everything. Use `"best_effort"` only when partial application is
explicitly acceptable.

**`base_hash` is optional but recommended.** Including the source hash
prevents applying a patch to the wrong version of a file.

---

## Known limitations

**Nested scopes:** Python/JS nested functions (closures) are detected
but cannot be individually addressed with qualified names like
`"outer_fn.inner_fn"`. Only class methods get qualified names.
Use `edit_text` scoped to the outer function as a workaround.

**CSS `rename_symbol`:** Renames only the declaration selector, not
occurrences in other rules (e.g. inside `@media` blocks). Use
`edit_text` for global selector renames.

**CRLF line endings:** Input files with `\r\n` are read and output
with `\n` (LF only). This is intentional but may produce noisy diffs
in Windows-centric codebases.
