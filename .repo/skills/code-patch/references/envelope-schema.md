---
title: Patch Envelope Schema — code-patch
---

# Patch Envelope Schema

The patch envelope is a JSON object passed to `apply_code_patch.py` as the
second argument.

---

## Top-level fields

| Field | Type | Required | Description |
|---|---|---|---|
| `patch_id` | string | yes | ULID or unique identifier for this patch |
| `file_id` | string | yes | Relative path to the target source file |
| `language` | string | yes | `python` \| `javascript` \| `typescript` \| `rust` \| `html` \| `css` |
| `apply_mode` | string | yes | `atomic` \| `best_effort` |
| `status` | string | no | `ready` (default) \| `partial` \| `blocked` |
| `base_hash` | string | no | `sha256:<hex>` — if set, must match source file hash |
| `edits` | array | yes | Ordered list of operations |
| `goals_covered` | array | no | Goal-to-edit-index mapping for reporting |

---

## `apply_mode`

- **`atomic`** (default): first failure stops and discards all changes.
- **`best_effort`**: failures are recorded as skipped; successful ops are kept.

---

## `goals_covered`

Optional. Maps human-readable goals to edit indices for reporting.

```json
"goals_covered": [
  {
    "goal": "Replace deprecated UTC call",
    "edit_indices": [1, 2],
    "status": "ready"
  }
]
```

`goals_actual` in the report will show `done`, `partial`, or `not_applied`
for each goal.

---

## Minimal example

```json
{
  "patch_id": "01JXYZ...",
  "file_id": "src/auth.py",
  "language": "python",
  "apply_mode": "atomic",
  "edits": [
    {
      "op": "edit_text",
      "find": "utcnow()",
      "replace": "now(tz=timezone.utc)"
    }
  ]
}
```

---

## Full example (Python)

```json
{
  "patch_id": "01JXYZ...",
  "file_id": "src/auth.py",
  "language": "python",
  "apply_mode": "atomic",
  "status": "ready",
  "base_hash": "sha256:a3f2...",
  "edits": [
    {
      "op": "assert",
      "contains": "def verify_token"
    },
    {
      "op": "rename_symbol",
      "symbol_id": "function:verify_token",
      "new_name": "validate_token"
    },
    {
      "op": "add_import",
      "statement": "from datetime import timezone"
    },
    {
      "op": "edit_text",
      "symbol_id": "function:validate_token",
      "find": "utcnow()",
      "replace": "now(tz=timezone.utc)"
    }
  ],
  "goals_covered": [
    {
      "goal": "Rename verify_token to validate_token",
      "edit_indices": [0, 1],
      "status": "ready"
    },
    {
      "goal": "Fix deprecated UTC usage",
      "edit_indices": [2, 3],
      "status": "ready"
    }
  ]
}
```

---

## EXECUTION_REPORT structure

```json
{
  "patch_id": "01JXYZ...",
  "file_id": "src/auth.py",
  "status": "full_success",
  "apply_mode": "atomic",
  "source_hash": "sha256:a3f2...",
  "result_hash": "sha256:b4e9...",
  "applied_ops": [0, 1, 2, 3],
  "skipped_ops": [],
  "errors": [],
  "goals_actual": [
    {
      "goal": "Rename verify_token to validate_token",
      "planned_status": "ready",
      "actual_status": "done",
      "planned_indices": [0, 1],
      "applied_indices": [0, 1],
      "skipped_indices": []
    }
  ],
  "warnings": [],
  "working_copy_path": "auth.01JXYZ.py"
}
```

---

## STATUS values

| STATUS | Meaning |
|---|---|
| `full_success` | All ops applied |
| `partial_success` | Some ops applied, some skipped (`best_effort` mode only) |
| `no_change` | All ops failed/skipped, no mutations (`best_effort` mode only) |
| `discarded` | Op failed in `atomic` mode — nothing was written |
| `blocked` | An `assert` op failed in `atomic` mode — nothing was written |
| `envelope_error` | Invalid envelope (bad hash, unsupported language, empty edits) |
| `not_attempted` | Patch `status` was `"blocked"` — executor did not run |
