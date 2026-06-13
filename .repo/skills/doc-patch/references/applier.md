# Applier Reference

This document is the single canonical reference for the doc-patch
applier — the deterministic executor that applies patch envelopes to
documents. Everything in this file is applier-facing; the AI reads it
when it needs to understand what the applier will do, but the primary
audience is the applier implementation itself.

## Table of Contents

- Execution Model
- STATUS Enum
- EXECUTION_REPORT
- LAST_STABLE
- Copy Creation Procedure
- Operation Semantics
- String Matching
- Post-Apply Phase
- Verification Checklist

---

## Execution Model

The original document is NEVER modified. The applier creates a working
copy named `{document_id}.{ULID}.md` and applies all operations to
that copy.

Three-file lifecycle:

- **A** (archival original) — the first version. Never modified.
- **B** (current stable) — the latest successfully-patched version.
  Typically the source document for new patches.
- **C** (working copy) — the ULID-named copy created during patch
  application. Becomes the new B on `full_success`; otherwise
  discarded or held for manual review.

The protocol identifies files by `document_id` and `base_hash`, not
by filesystem role.

---

## STATUS Enum

| STATUS | Meaning | Working copy fate | Apply modes |
|---|---|---|---|
| `full_success` | All ops applied. Post-apply complete. | Exists, fully patched. Promoted to B. | atomic, best_effort |
| `partial_success` | Some ops applied, some skipped. | Exists, partially patched. Held for review. | best_effort only |
| `no_change` | No ops applied (all skipped or assertion at index 0). | Discarded (identical to source). | best_effort only |
| `discarded` | Op failure under atomic. | Deleted. | atomic only |
| `envelope_error` | Pre-op validation failed (hash mismatch, duplicate patch_id). | Deleted. | atomic, best_effort |
| `blocked` | Assertion failure under atomic. | Deleted. | atomic only |
| `not_attempted` | Patch status was `blocked`; no copy created. | Never existed. | atomic, best_effort |

`envelope_error` fires before any op executes and is independent of
`apply_mode`. An empty `edits` array with patch status ∈ {ready,
partial} is also an envelope error (`EMPTY_EDITS`).

---

## EXECUTION_REPORT

A structured object returned alongside STATUS. Always present (even
on `not_attempted`, where it is a stub).

```json
{
  "patch_id": "ndp-v021-recon-001",
  "document_id": "ndp-v0.2.1",
  "status": "full_success",
  "apply_mode": "atomic",
  "source_hash": "sha256:...",
  "result_hash": "sha256:...",
  "applied_ops": [0, 1, 2, 3, 4],
  "skipped_ops": [],
  "errors": [],
  "goals_actual": [
    {
      "goal": "Move Error Model after Transaction Semantics",
      "planned_status": "done",
      "actual_status": "done",
      "planned_indices": [0, 1],
      "applied_indices": [0, 1],
      "skipped_indices": []
    }
  ],
  "warnings": [],
  "working_copy_path": "ndp-v0.2.1.01J7KBQX9HXYZ.md"
}
```

### Field Reference

| Field | Present when | Description |
|---|---|---|
| `patch_id` | Always | Copied from envelope. |
| `document_id` | Always | Copied from envelope. |
| `status` | Always | The STATUS enum value. |
| `apply_mode` | Always | `atomic` or `best_effort`. |
| `source_hash` | Always | SHA-256 of the source document. |
| `result_hash` | full_success, partial_success | SHA-256 of working copy after all ops and post-apply. |
| `applied_ops` | Not on not_attempted, envelope_error | Array of indices of successfully applied ops. |
| `skipped_ops` | Not on not_attempted, envelope_error | Array of `{ "index": N, "error_type": "...", "detail": "..." }`. |
| `errors` | On failure | Structured errors (envelope or op level). |
| `goals_actual` | full_success, partial_success, no_change | Reconciled goal coverage. On `no_change`, all goals have `actual_status: "not_applied"`. |
| `warnings` | Always | Provisional ID cascades, fuzzy match fallbacks, etc. |
| `working_copy_path` | full_success, partial_success | Filesystem path of surviving working copy. |

### goals_actual Reconciliation

The applier produces `goals_actual` by cross-referencing the AI's
`goals_covered` with actual op outcomes:

- For each goal, partition its `edit_indices` into `applied_indices`
  and `skipped_indices` based on actual results.
- Derive `actual_status`:
  - `"done"` — all `edit_indices` in `applied_ops`.
  - `"partial"` — some applied, some skipped.
  - `"not_applied"` — all skipped.
- Copy `planned_status` from original `goals_covered.status`.

---

## LAST_STABLE

| STATUS | LAST_STABLE | C disposition |
|---|---|---|
| `full_success` | C (promoted) | Renamed/moved to replace B. |
| `partial_success` | B (unchanged) | C survives at `working_copy_path` for review. |
| `no_change` | B (unchanged) | C discarded. |
| `discarded` | B (unchanged) | C already deleted. |
| `envelope_error` | B (unchanged) | C already deleted. |
| `blocked` | B (unchanged) | C already deleted. |
| `not_attempted` | B (unchanged) | C never existed. |

Promotion (C → B) is automatic on `full_success` only.

Partial results are never auto-promoted. The user inspects
EXECUTION_REPORT, then either promotes C manually or discards it
and issues a corrected patch against unchanged B.

---

## Copy Creation Procedure

1. Read the source document and compute its SHA-256 (`source_hash`).
   This hash is stored regardless of whether `base_hash` is present
   in the envelope — it is used for post-apply source verification
   (step 6 of Post-Apply) and for the EXECUTION_REPORT.
2. If `base_hash` is present in the envelope, compare it against the
   computed `source_hash`. On mismatch → `envelope_error` with
   `HASH_MISMATCH`.
3. Check `patch_id` against the document's application log. If
   already present → `envelope_error` with `PATCH_ALREADY_APPLIED`.
4. If `edits` is empty and patch status ∈ {ready, partial} →
   `envelope_error` with `EMPTY_EDITS`.
5. Create working copy: `{document_id}.{ULID}.md`.
6. Build ID resolution map: for every section, map its identifiers
   (heading text, number, anchor) to position in working copy.
7. Apply ops sequentially, updating the resolution map after each
   structural op.

Envelope validation (steps 2–3) runs before any ops regardless of
`apply_mode`. On envelope error the applier deletes the working copy,
returns `envelope_error`, and sets LAST_STABLE = B.

---

## Operation Semantics

For ALL ops carrying `section_id`, the applier scopes its search
to that section's current extent in the working copy.

- `move_section`: Extract heading + body + subsections, reinsert at
  target. Update map.
- `swap_sections`: Extract both sections, reinsert each at the
  other's original position. Update map once after both moves.
- `merge_sections`: Move source into target per strategy; delete
  source shell. Update map.
- `absorb_section`: Extract source body (not heading), insert into
  target at placement; delete source. Update map.
- `split_section`: Find boundary, create new section. Register
  `new_section_id` in map.
- `delete_section`: Remove heading + body + subsections. Remove from
  map.
- `replace_block` / `delete_block`: Find markers within scope, splice.
- `insert_block`: Find anchor within scope (or global), insert on
  next line.
- `move_block`: Find source block in `source_section_id` scope,
  extract it, insert at `after_anchor` in `target_section_id` scope.
- `copy_block`: Read the source block from the working copy's current
  state (not the original document), duplicate at target. The source
  block's content in the working copy is not modified by this op.
- `edit_text`: Find-and-replace within `section_id` scope only.
- `rename_section`: Replace heading text only.
- `rewrite_section`: Replace intro body (heading to first child
  subsection). Subsections untouched.
- `assert`: Check original document (not working copy). On failure:
  under `atomic`, discard + report; under `best_effort`, skip this
  + subsequent ops.
- `update_frontmatter`: Set key-value pairs in YAML frontmatter.
- `inject_markers`: Insert markers per specs. For `section_anchor`:
  if the heading already has an anchor matching the requested one,
  no-op (no warning). If the heading has a different anchor, replace
  it with the new one and emit a warning.

---

## String Matching

For `edit_text`, `replace_block`, `inject_markers`, and `split_after`
locators, the applier attempts:

1. Exact string match within section scope.
2. Whitespace-normalized match (collapse runs, trim lines).
3. Fuzzy match — ONLY if the op includes `"allow_fuzzy": true`.
   Default threshold: Levenshtein ratio ≥ 0.85 (configurable).
   If `allow_fuzzy` is absent or false, the applier stops at tier 2.

If no match at the applicable level, return `FIND_NOT_MATCHED` with
the closest candidate (for diagnostic purposes, even when fuzzy is
disabled).

The AI sets `allow_fuzzy: true` when it is confident the locator is
close but may differ in whitespace, punctuation, or minor wording.
Short, highly specific locators should NOT use fuzzy matching.

---

## CONFLICT Detection

The applier MAY perform an optional pre-execution static analysis to
detect ops whose target ranges in the source document overlap. If
detected, report error type `CONFLICT`. This check is advisory — the
applier MAY instead rely on sequential execution and report
`FIND_NOT_MATCHED` if a prior op invalidated the target. Under
`atomic` mode, CONFLICT discards the working copy; under
`best_effort`, the conflicting op is skipped.

---

## Post-Apply Phase

After applying all ops (or all non-skipped ops under `best_effort`):

1. Recalculate section numbers sequentially.
2. Rebuild the table of contents.
3. Update ALL `§N` cross-references to new numbers. Deterministic AST
   pass — do NOT delegate to the LLM.
4. Resolve provisional `§new:` IDs to real section numbers.
5. Record `patch_id` in the document's application log.
6. Verify the source document is unmodified.
7. Compute `result_hash` (SHA-256 of working copy).
8. Build EXECUTION_REPORT.
9. Determine STATUS and LAST_STABLE.
10. If `full_success`: promote working copy (C → B).
11. If `partial_success`: retain at `working_copy_path`. Do NOT promote.
12. If `no_change`: discard working copy.

---

## Verification Checklist

After applying, verify:

- All `§N` cross-references resolve to correct sections
- No orphaned heading numbers remain
- Block markers remain balanced (open/close pairs)
- TOC matches actual heading structure
- No merged-section references point to deleted content
- Original file is unmodified

---

## Dry-Run Mode

The applier SHOULD support a `--dry-run` flag. In dry-run mode:

- All operations and post-apply steps execute normally on the working
  copy (including hash computation and EXECUTION_REPORT generation).
- STATUS is computed as usual.
- LAST_STABLE reports the **hypothetical** outcome — what WOULD happen
  if this were a real run. (E.g., `full_success` → LAST_STABLE = C,
  meaning C *would be* promoted.)
- No promotion or discard occurs. The working copy is retained at
  `working_copy_path` for inspection regardless of STATUS.
- The EXECUTION_REPORT includes `"dry_run": true` as an additional
  field to distinguish hypothetical from actual results.
