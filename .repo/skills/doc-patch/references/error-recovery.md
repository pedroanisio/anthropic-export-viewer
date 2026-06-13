# Error Recovery Reference

Error recovery (Phase 2.5) applies ONLY under `atomic` mode, triggered
when the applier returns a structured error after discarding the
working copy.

---

## Error Shapes

### Envelope-Level Error

Pre-op validation failure. The applier never attempted any ops.

```json
{
  "error_level": "envelope",
  "error_type": "HASH_MISMATCH",
  "detail": "Expected sha256:abc..., got sha256:def..."
}
```

Envelope error types:
- `HASH_MISMATCH` — `base_hash` does not match the original.
- `PATCH_ALREADY_APPLIED` — `patch_id` found in application log.
- `EMPTY_EDITS` — `edits` array is empty with patch status ∈ {ready, partial}.

For envelope errors, the AI cannot fix the patch. Respond with
`status: blocked`.

### Op-Level Error

Failure during application of a specific operation.

```json
{
  "error_level": "op",
  "failed_op_index": 2,
  "op": "edit_text",
  "error_type": "FIND_NOT_MATCHED",
  "section_id": "§2.3",
  "detail": "No match for find string.",
  "closest_match": "5× or greater reduction in token usage"
}
```

Op-level error types:
- `SECTION_NOT_FOUND` — section_id does not resolve.
- `FIND_NOT_MATCHED` — find/target has no match. May include
  `closest_match`.
- `BLOCK_NOT_FOUND` — block marker or anchor missing.
- `CONFLICT` — two ops target overlapping content.
- `ASSERTION_FAILED` — assert op returned false. **Non-fixable.**
  Respond with `status: blocked` explaining the unmet precondition.

---

## Recovery Procedure (Fixable Errors)

The working copy was discarded. The AI produces a COMPLETE corrected
patch — the full edits array with the failed op fixed. The applier
creates a fresh copy and applies the corrected patch from scratch.

On retries, append `-retry1`, `-retry2`, etc. to `patch_id`.

---

## Error Recovery Activation Prompt

```
ORIGINAL PATCH
<<<
{the patch JSON that failed}
>>>

ERROR
<<<
{the structured error returned by the applier}
>>>

DOCUMENT_HASH (optional)
sha256:{hash of the original document}

OUTPUT
Produce a complete corrected patch — all operations, with the failed
one fixed. The applier will apply this to a fresh copy.
For ASSERTION_FAILED or envelope errors, emit status: blocked.
```
