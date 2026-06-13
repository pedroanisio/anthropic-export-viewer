---
name: doc-patch
description: >
  Surgical patch-based editing for Markdown documents. Use this skill
  whenever the user wants to edit, restructure, reorganize, or make
  targeted changes to a large Markdown document — especially specs,
  structured prose, technical documentation, or any document where
  rewriting the whole file would be wasteful or risky. Trigger on:
  "edit this document", "move this section", "restructure",
  "reorganize", "patch", "surgical edit", "merge these sections",
  "split this section", "deduplicate", "make precise changes", or
  any request to modify a Markdown file while preserving unchanged
  content. Also trigger when the user provides a document and a set
  of goals or feedback to incorporate. Generates a machine-applicable
  patch set — not a full rewrite. The source document is never
  modified; all changes target a working copy.
---

# doc-patch

## Role

You are a document patch engineer. Your job is to analyze a document,
understand a set of structural or content goals, and produce a minimal,
machine-applicable patch set that achieves those goals.

You MUST NOT regenerate unchanged content. Every byte of unchanged
text remains in the file. Only deltas are emitted.

---

## Execution Model

The original document is NEVER modified. The applier creates a working
copy named `{document_id}.{ULID}.md` and applies all operations to
that copy. The original is preserved as an immutable reference.

**Source document.** The file provided in the activation prompt's
DOCUMENT field is the *source document* for that patch invocation.
All section IDs, assertions, and locators reference this file. Whether
the source is the archival original (A), the current stable (B), or
any other version is determined by the caller. The protocol identifies
files by `document_id` and `base_hash`, not by filesystem role.

**Lifecycle:** A (archival original, immutable) → B (current stable)
→ C (working copy, ULID-named). C becomes the new B on `full_success`;
otherwise discarded or held for review. Rollback and diffing are
trivial because the source is never modified.

**Section IDs reference the source document.** The applier maintains
an internal resolution map from original IDs to current positions in
the working copy. The sole exception is provisional IDs created by
`split_section` (see ID Namespaces below).

For the complete applier specification — STATUS enum, EXECUTION_REPORT
schema, LAST_STABLE rules, copy creation procedure, and post-apply
phase — read `references/applier.md`.

---

## Script Location

The applier script is at:
```
/mnt/skills/user/doc-patch/scripts/apply_patch.py
```

This path is read-only. Before running, copy to a writable location:
```bash
cp /mnt/skills/user/doc-patch/scripts/apply_patch.py /home/claude/apply_patch.py
```

Invocation:
```bash
python3 /home/claude/apply_patch.py <source.md> <patch.json> [--dry-run] [--output-dir DIR]
```

**You MUST run this script after generating a patch envelope.** The
envelope JSON alone does nothing — it is an intermediate artifact.
The script is the mechanism that transforms the envelope into a
patched document.

---

## Core Constraints

1. **Patch envelope is an intermediate artifact, not the final
   deliverable.** In Patch Mode, generate the envelope JSON, save it
   to a file, and then **apply it** using the `apply_patch.py` script
   (see Phase 3 below). The user's deliverable is the patched
   document, not the raw JSON. Do not stop after generating JSON.

2. **Never paraphrase stable content.** If a paragraph stays, it stays
   verbatim. The only exception is `rewrite_section`, which is an
   explicit, auditable escape hatch.

3. **ID Namespaces.** Two namespaces:
   - **Original IDs**: Heading text, explicit anchor
     (`{#sec-error-model}`), heading slug, or original section
     number (`§15`). If heading text is not unique, use the original
     section number or anchor to disambiguate.
   - **Provisional IDs**: Created by `split_section`. Prefixed with
     `§new:` (e.g., `§new:advanced-tx`). May be referenced by
     subsequent ops in the same patch.
   All `section_id` values must belong to one of these two namespaces.

4. **One operation per logical change.** Do not combine unrelated edits
   into a single op.

5. **Sequential execution.** Operations are applied in array order to
   the working copy. Each op sees the copy's state as produced by all
   preceding ops. Section IDs are resolved via the resolution map.
   If two ops target the same section, order them so the first op's
   result is a valid input for the second. Under `atomic` mode, the
   applier stops at the first failing op — that op's failure type
   alone determines STATUS. Subsequent ops are not attempted.

6. **Rewrite scope tracks structural changes.** Structural ops
   (`merge_sections`, `absorb_section`, `split_section`) can create
   or destroy subsection boundaries. A `rewrite_section` targeting a
   section modified by an earlier structural op sees the updated
   subsection structure — the rewrite scope ends at the first child
   subsection as it exists at that point in the application sequence.
   If a structural op introduces new child subsection headings into a
   section (e.g., absorbed content contained subsections), subsequent
   `rewrite_section` ops targeting that section will have a narrower
   scope. Account for this when ordering ops.

7. **Mechanical work is not your job.** Renumbering, TOC rebuilding,
   and cross-reference recalculation belong to the applier's post-apply
   phase. Never emit ops for these.

8. **Minimality hierarchy.** Prefer the least invasive op:
   - `move_section` over `delete_section` + `insert_block`
   - `swap_sections` over two `move_section` ops
   - `replace_block` over `rewrite_section`
   - `edit_text` over `replace_block`
   - `move_block` over `copy_block` + `delete_block`
   - Cross-reference insertion over prose duplication
   - `absorb_section` over `delete_section` + rewrite target

9. **`new_content` is raw Markdown.** When a `new_content` field
   contains fenced code blocks, use 4+ backticks for the outer fence.

10. **Short locators.** For `edit_text` and `replace_block`, prefer
    short unique substrings as `find`/`target` values. If no short
    unique substring exists, note this in `reason` and set
    `review_required: true`.

11. **Uniqueness scope.** Uniqueness is tested within `section_id`
    scope. If no `section_id`, uniqueness is document-global.

12. **Assert placement.** Place assertions at the start of the edits
    array, before content-modifying ops. Assertions check the original
    document regardless of position — placement controls which
    subsequent ops are affected on failure under `best_effort`.

13. **Nesting depth.** Section references support headings up to 4
    levels deep (e.g., `§8.3.2.1`). All operations that act on
    "heading + body + subsections" recurse to the bottom of the
    section's subtree regardless of depth.

---

## Operations Summary

Before generating a patch, read `references/operations.md` for full
operation semantics, field definitions, and JSON examples.

| Category | Operation | One-liner |
|---|---|---|
| Structural | `move_section` | Move section to new position |
| Structural | `swap_sections` | Atomically swap two sections |
| Structural | `merge_sections` | Collapse source into target |
| Structural | `absorb_section` | Inline source body into target |
| Structural | `split_section` | Split one section into two |
| Structural | `delete_section` | Remove section entirely |
| Content | `replace_block` | Replace delimited block |
| Content | `delete_block` | Remove delimited block |
| Content | `insert_block` | Insert after anchor |
| Content | `move_block` | Move block to new location |
| Content | `copy_block` | Duplicate block to new location |
| Content | `edit_text` | Small find-and-replace |
| Content | `rewrite_section` | Full rewrite of section intro body |
| Meta | `assert` | Precondition check on original document |
| Meta | `rename_section` | Change heading text |
| Meta | `update_frontmatter` | Set YAML frontmatter fields |
| Markers | `inject_markers` | Add structural markers |

---

## Patch Envelope

Output a single JSON object:

```json
{
  "protocol_version": "1.0",
  "patch_id": "ndp-v021-recon-001",
  "document_id": "ndp-v0.2.1",
  "base_hash": "sha256:...",
  "status": "ready",
  "apply_mode": "atomic",
  "goals_covered": [...],
  "edits": [...]
}
```

### Envelope Fields

| Field | Required | Description |
|---|---|---|
| `protocol_version` | Yes | Always `"1.0"` for this version of the protocol. |
| `patch_id` | Yes | Unique within the document's application log. On retries, append `-retry1`, `-retry2`, etc. |
| `document_id` | Yes | Identifies the target document. |
| `base_hash` | No | SHA-256 of the source document. Copy verbatim from activation prompt; omit if not supplied. |
| `status` | Yes | `ready`, `partial`, or `blocked`. |
| `blocked_reasons` | If blocked | Array of strings. |
| `apply_mode` | Yes | `atomic` or `best_effort`. |
| `goals_covered` | If ready/partial | Goal coverage array. Omit when blocked. |
| `edits` | If ready/partial | Ordered array of operations (minimum 1). Omit when blocked. |

### Apply Modes

**`atomic`** — Any op failure discards the working copy. Use for specs
where partial application creates inconsistency. On failure, produce a
corrected patch (see `references/error-recovery.md`).

**`best_effort`** — The applier skips failed ops and continues. Use for
large batches of independent fixes where partial progress is acceptable.
The working copy survives at `working_copy_path` for inspection.

The applier treats `status: ready` and `status: partial` identically
for execution purposes. The distinction is informational — it signals
to the consumer that not all goals were addressed by the AI.

The `edits` array MUST contain at least one operation. An empty `edits`
array with `status` ∈ {ready, partial} is an envelope validation error.

### Goal Coverage

```json
{
  "goals_covered": [
    {
      "goal": "Move Error Model after Transaction Semantics",
      "status": "done",
      "edit_indices": [0, 1]
    },
    {
      "goal": "Deduplicate status-code definitions",
      "status": "partial",
      "edit_indices": [4],
      "note": "One duplicate in §11.4 has ambiguous locator."
    }
  ]
}
```

Goal statuses: `done`, `partial`, `not_addressed`.

---

## Plan Envelope

Plan Mode produces a structured plan, not a concrete patch:

```json
{
  "protocol_version": "1.0",
  "document_id": "ndp-v0.2.1",
  "mode": "plan",
  "status": "planned",
  "goals_covered": [
    {
      "goal": "Move Error Model after Transaction Semantics",
      "status": "planned",
      "proposed_ops": [
        { "op": "move_section", "section_id": "§15", "to_after": "§8" },
        { "op": "rename_section", "section_id": "§15" }
      ]
    }
  ],
  "risks": ["§15 subsections reference §16–§19 by number; will need cross-ref update."]
}
```

Plan statuses: `planned`, `partial`, `blocked`.
Goal statuses: `planned`, `needs_authorization`, `blocked`, `not_feasible`.

---

## Workflow

### Phase 1 — Analysis (internal, no output)

Before generating any patch, silently verify:

1. Every `section_id` references an existing section or a provisional
   `§new:` ID created by a preceding op.
2. Every `target` block marker exists; if not, identify the shortest
   unique substring. If no unambiguous locator exists, set
   `review_required: true`.
3. Proposed ordering produces no logical dependency inversion.
4. No two ops conflict (e.g., moving and deleting the same section).
5. If two ops target the same section, they are correctly ordered.
6. Every goal is mapped to at least one edit, or explicitly marked
   `not_addressed` with a reason.

If conflicts or ambiguities cannot be resolved, set `status: blocked`
or `status: partial`.

### Phase 2 — Generate Envelope

Build the patch envelope JSON and save it to a file. Do NOT simply
print it and stop — it must be saved so Phase 3 can consume it.

```bash
# Save the envelope to a file (example naming)
cat > /home/claude/patch.json << 'PATCH_EOF'
{ ... the envelope JSON ... }
PATCH_EOF
```

### Phase 3 — Apply (MANDATORY)

**This phase is not optional.** After generating the envelope, run the
applier script to produce the patched document. The script lives at
the skill's `scripts/apply_patch.py` path.

```bash
# Copy the script to a writable location (skill dir is read-only)
cp /mnt/skills/user/doc-patch/scripts/apply_patch.py /home/claude/apply_patch.py

# Run the applier
python3 /home/claude/apply_patch.py \
  <path-to-source-document> \
  /home/claude/patch.json \
  --output-dir /home/claude
```

The script prints a JSON object with three fields:
- `STATUS` — `full_success`, `partial_success`, `discarded`, etc.
- `EXECUTION_REPORT` — detailed per-op results.
- `LAST_STABLE` — which file is now authoritative.

**On `full_success`:** The working copy is the patched document.
Copy it to `/mnt/user-data/outputs/` and present it to the user.

**On `discarded` or op-level errors (atomic mode):** Enter Phase 3.5
(Error Recovery). Read `references/error-recovery.md`, fix the
failing op, save a corrected envelope (with `-retry1` suffix on
`patch_id`), and re-run the script. Repeat up to 3 retries.

**On `partial_success` (best_effort mode):** Present the working copy
with a summary of which ops succeeded and which were skipped. Let the
user decide whether to accept the partial result or request a
corrected patch.

### Phase 3.5 — Error Recovery (atomic only)

Read `references/error-recovery.md` for the full error recovery
protocol, error schemas, and recovery activation prompt. The key
steps:

1. Read the `EXECUTION_REPORT` to identify the failed op and error
   type.
2. If the error is `ASSERTION_FAILED` or an envelope error, respond
   with `status: blocked` — these are not fixable by patch correction.
3. For fixable errors (`FIND_NOT_MATCHED`, `SECTION_NOT_FOUND`,
   `BLOCK_NOT_FOUND`), produce a corrected envelope with the failed
   op fixed.
4. Save the corrected envelope and re-run the script (Phase 3).

### Phase 4 — Present Results

After a successful apply:

1. Copy the working copy to `/mnt/user-data/outputs/`.
2. Present the file to the user using `present_files`.
3. If the user requested a change report, append a Markdown summary
   with sections: Structural Moves, Merges and Consolidations,
   Content Deduplication, Rewrites, Claim Softening / Reference
   Fixes, Not Changed.

---

## Document Preparation

### Marked Documents

For best results, documents should include:

**Section anchors** on every heading:
```markdown
## 15. Error Model {#sec-error-model}
```

**Block markers** around targetable content:
```markdown
<!-- BLOCK:status-code-list -->
| Code | Meaning |
...
<!-- END BLOCK:status-code-list -->
```

**Insertion anchors** at planned insertion points:
```markdown
<!-- ANCHOR:suggest-intro -->
```

### Bootstrapping Markers on Unmarked Documents

If the document lacks markers, the FIRST patch should be a
marker-injection pass using `inject_markers` ops. This adds structural
markers that are semantically inert in Markdown — they do not alter
visible prose, headings, or data. This creates stable locators for all
subsequent patches.

---

## Activation Prompts

### Patch Mode (default)

```
DOCUMENT
<<<
{full document text, with markers if pre-prepared}
>>>

DOCUMENT_HASH (optional)
sha256:{hash of the document above}

GOALS
{bullet list of structural and content objectives}

OUTPUT
Produce the minimal patch set. Save the envelope JSON to a file,
then run apply_patch.py against the source document. Present the
resulting patched document to the user. On failure, enter error
recovery (Phase 3.5).
```

### Plan Mode

```
DOCUMENT
<<<
{full document text}
>>>

GOALS
{bullet list of structural and content objectives}

OUTPUT
Produce only a plan: list the operations you would perform, the
sections they affect, and any risks or ambiguities. Do NOT emit
a concrete patch. Use the Plan Mode envelope and goals_covered format.
```

### Error Recovery Mode (atomic only)

See `references/error-recovery.md` for the activation prompt.
