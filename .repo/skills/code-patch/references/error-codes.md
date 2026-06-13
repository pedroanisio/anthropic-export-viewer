---
title: Error Codes — code-patch
---

# Error Codes

All errors appear in `EXECUTION_REPORT.errors[]` with `error_type` and
`detail` fields.

---

## Envelope-level errors

These stop the executor before any op runs. `STATUS` is `envelope_error`.

| Error type | Cause | Fix |
|---|---|---|
| `UNSUPPORTED_LANGUAGE` | `language` field is not one of the six supported values | Use: `python`, `javascript`, `typescript`, `rust`, `html`, `css` |
| `HASH_MISMATCH` | `base_hash` does not match the source file's SHA-256 | Re-read the source file; recompute hash; update `base_hash` |
| `EMPTY_EDITS` | `edits` array is empty and `status` is `ready` or `partial` | Add at least one edit, or set `status: "blocked"` to mark as not-ready |

---

## Op-level errors

These appear in `errors[]` per operation. In `atomic` mode, the first
op-level error stops all remaining ops and returns the named STATUS.

### `SYMBOL_NOT_FOUND`

**STATUS in atomic:** `discarded`

The `symbol_id` did not resolve to any symbol in the file.

**Common causes:**
- Symbol was deleted or renamed in a previous op in this patch.
- Type-qualified ID has wrong kind: check `function:` vs `class:` etc.
- Qualified name format wrong: use `ClassName.method_name` (dot, not `::` or `/`).
- Bare name is ambiguous: use type-qualified ID.

**Fix:** Read the source file, verify the symbol name and kind, update
the `symbol_id`.

---

### `FIND_NOT_MATCHED`

**STATUS in atomic:** `discarded`

The `find` text (or `target` / `source_target`) was not found in scope.

The report may include `closest_match` — the line with the best word
overlap — to help identify the issue.

**Common causes:**
- Extra whitespace in `find` text (tier 2 whitespace-normalized matching
  handles most cases, but multiline patterns may still fail).
- The text was already changed by a previous op in this patch.
- Wrong `symbol_id` scope — the text exists, but not inside that symbol.
- Text contains special characters that were altered by the editor.

**Fix:** Copy the exact text from the source file. Remove leading/trailing
whitespace that isn't in the actual file. Widen scope by removing
`symbol_id`.

---

### `ANCHOR_NOT_FOUND`

**STATUS in atomic:** `discarded`

The `after_anchor` anchor name or text was not found in scope.

**Fix:** Check the anchor name matches exactly (case-sensitive). Verify
the anchor comment was injected first via `inject_markers`. Remove
`symbol_id` scope to widen the search.

---

### `BLOCK_NOT_FOUND`

**STATUS in atomic:** `discarded`

A named `BLOCK:name` marker was specified but not found in scope.

**Fix:** Verify the block markers exist with `assert` first. Inject them
with `inject_markers` if they don't exist yet.

---

### `IMPORT_NOT_FOUND`

**STATUS in atomic:** `discarded`

`remove_import` could not find a matching import statement.

**Fix:** Copy the exact import statement from the source file. Whitespace
normalization is applied, so minor spacing differences are handled.

---

### `ASSERTION_FAILED`

**STATUS in atomic:** `blocked`

An `assert` op's `contains` text was not found in the specified scope.

**Status note:** Unlike other op errors, assertion failures in `atomic`
mode return `STATUS: blocked` (not `discarded`) to distinguish a failed
pre-condition check from an execution error.

**Fix:** Read the source file to confirm the expected text exists. If the
assertion is guarding against a specific version, update it. If the text
genuinely doesn't exist, the patch should not be applied.

---

### `UNKNOWN_OP`

**STATUS in atomic:** `discarded`

The `op` field value is not a known operation.

**Fix:** Check the operation name against `op-reference.md`. Operation
names are case-sensitive and use underscores (`rename_symbol`, not
`renameSymbol`).

---

### `SKIPPED_AFTER_ASSERTION`

Not an error — a skip record indicating that `best_effort` mode skipped
this op because a prior `assert` op failed.

---

## STATUS → next action

| STATUS | Working copy written? | Next action |
|---|---|---|
| `full_success` | Yes | Promote working copy to source file |
| `partial_success` | Yes | Review `skipped_ops`; confirm with user; promote or abort |
| `no_change` | No | All ops failed; fix envelope; retry |
| `discarded` | No | Fix `errors[0]`; retry |
| `blocked` | No | Fix assertion; retry |
| `envelope_error` | No | Fix envelope schema; retry |
| `not_attempted` | No | Patch status was "blocked"; update to "ready" |
