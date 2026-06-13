# Operations Reference

All `section_id` values use the ID Namespaces defined in Core
Constraint 3 of the main SKILL.md.

## Table of Contents

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
| Meta | `assert` | Precondition check |
| Meta | `rename_section` | Change heading text |
| Meta | `update_frontmatter` | Set YAML frontmatter fields |
| Markers | `inject_markers` | Add structural markers |

---

## Structural Operations

### `move_section`

Move an entire section (heading + body + subsections) to a new
position.

```json
{
  "op": "move_section",
  "section_id": "§15",
  "to_after": "§8",
  "reason": "Error model must be defined before wire formats."
}
```

### `swap_sections`

Atomically swap the positions of two sections. Eliminates the
fragile two-`move_section` pattern where intermediate state is
invalid.

```json
{
  "op": "swap_sections",
  "section_a": "§8",
  "section_b": "§15",
  "reason": "Transaction semantics should precede error model."
}
```

The applier extracts both sections, then reinserts each at the
other's original position. The resolution map is updated once
after both reinsertions.

### `merge_sections`

Collapse one section into another.

```json
{
  "op": "merge_sections",
  "source_id": "§20",
  "target_id": "§15",
  "strategy": "append_as_subsections",
  "reason": "Hallucination tolerance is a protocol-level error concern."
}
```

`strategy` values:
- `append_as_subsections` — source content becomes subsections at the
  end of the target.
- `prepend_as_subsections` — source content becomes subsections at the
  start of the target.

### `absorb_section`

Absorb the *body* of one section into another as inline content (not
as subsections), then delete the source section shell.

```json
{
  "op": "absorb_section",
  "source_id": "§10",
  "target_id": "§11",
  "placement": "prepend_as_intro",
  "reason": "Wire Formats overview is a thin connector; absorb into Text Mode."
}
```

`placement` values: `prepend_as_intro`, `append_as_outro`.

### `split_section`

Split a section into two at a specified boundary.

```json
{
  "op": "split_section",
  "section_id": "§8",
  "split_after": "<!-- BLOCK:transaction-basics -->",
  "new_section_heading": "Advanced Transaction Semantics",
  "new_section_id": "§new:advanced-tx",
  "reason": "§8 covers both basic and advanced semantics; split for clarity."
}
```

The original section retains everything up to and including the split
boundary. The new section gets everything after it, inserted
immediately following the original.

`split_after` follows the same locator resolution rules as
`replace_block` targets: block marker, anchor, or shortest unique
substring within section scope.

`new_section_id` is a provisional identifier in the `§new:` namespace.
Subsequent ops in the same patch may reference it. The applier
registers it in the resolution map when this op executes and assigns a
real section number during post-apply renumbering.

**Cascade under `best_effort`.** If a `split_section` op is skipped,
its provisional ID is never registered. Any subsequent op referencing
that provisional ID will fail with `SECTION_NOT_FOUND` and also be
skipped. The applier includes a warning identifying the cascade root.

### `delete_section`

Delete an entire section (heading + body + subsections).

```json
{
  "op": "delete_section",
  "section_id": "§22",
  "reason": "Section is entirely superseded by §15 after merge."
}
```

Use sparingly. Prefer `absorb_section` or `merge_sections` when
content should be preserved elsewhere.

---

## Content Operations

### `replace_block`

Replace a specific delimited block inside a section. The applier scopes
its search to `section_id`.

```json
{
  "op": "replace_block",
  "section_id": "§11.4",
  "target": "<!-- BLOCK:status-code-list -->",
  "new_content": "See §15 for the canonical status code table.",
  "reason": "Deduplicate status code definitions."
}
```

### `delete_block`

Remove a delimited block entirely. Scoped to `section_id`.

```json
{
  "op": "delete_block",
  "section_id": "§6.5",
  "target": "<!-- BLOCK:and-or-constraint-restatement -->",
  "reason": "Duplicate of grammar section constraint."
}
```

### `insert_block`

Insert new content after a named anchor.

```json
{
  "op": "insert_block",
  "section_id": "§9",
  "after_anchor": "<!-- ANCHOR:suggest-intro -->",
  "new_content": "For the full SUGGEST recovery protocol, see §15.3.",
  "reason": "Add forward reference to canonical SUGGEST definition."
}
```

`section_id` is optional. If provided, the applier scopes the anchor
search to that section. If omitted, the anchor must be globally unique.

### `move_block`

Move a delimited block from one location to another. The source block
is removed. This is atomic — use instead of `copy_block` + `delete_block`.

```json
{
  "op": "move_block",
  "source_section_id": "§11.4",
  "source_target": "<!-- BLOCK:status-code-list -->",
  "target_section_id": "§15",
  "after_anchor": "<!-- ANCHOR:canonical-status-codes -->",
  "reason": "Move status code table to canonical location."
}
```

`target_section_id` is optional. If omitted, `after_anchor` must be
globally unique.

### `copy_block`

Copy a block from one location to another. The source block is read
from the working copy's current state (not the original document).
The source block's content in the working copy is not modified by
this op. Prefer cross-references over duplication — use only when the
target context genuinely requires inline content.

```json
{
  "op": "copy_block",
  "source_section_id": "§15.2",
  "source_target": "<!-- BLOCK:canonical-status-codes -->",
  "target_section_id": "§A",
  "after_anchor": "<!-- ANCHOR:appendix-status-codes -->",
  "reason": "Appendix requires inline status code table for standalone reading."
}
```

`target_section_id` is optional. If provided, the applier scopes the
`after_anchor` search to that section. If omitted, the anchor must be
globally unique.

### `edit_text`

Replace a short specific string within a section. Use ONLY for small
targeted changes (< 3 lines).

```json
{
  "op": "edit_text",
  "section_id": "§2.3",
  "find": "5x or greater reduction",
  "replace": "5x–25x reduction (see §11.5 for empirical data)",
  "reason": "Soften standalone claim with reference to analysis."
}
```

### `rewrite_section`

Full rewrite of a section's **intro body only** — the content between
the section's heading and the first child subsection heading. Subsections
are NOT included; to rewrite subsections, emit separate ops for each.

This is the ONE op where the AI emits new prose at scale. Use only for
voice normalization, structural incoherence that cannot be fixed by
smaller ops, or sections damaged beyond surgical repair. The `reason`
MUST justify why smaller ops are insufficient.

```json
{
  "op": "rewrite_section",
  "section_id": "§2.3",
  "instruction": "Normalize to passive technical voice.",
  "new_content": "...",
  "reason": "Section mixes three voice registers. edit_text would require 14 ops."
}
```

**Scope after structural ops.** Structural ops (`merge_sections`,
`absorb_section`) can create or destroy subsection boundaries. A
`rewrite_section` targeting a section modified by an earlier structural
op sees the updated subsection structure — the rewrite scope ends at
the first child subsection as it exists at that point in the
application sequence.

---

## Meta Operations

### `assert`

Precondition check. Verifies the ORIGINAL document (not the working
copy) contains the expected content.

```json
{
  "op": "assert",
  "section_id": "§15",
  "contains": "Status Codes",
  "reason": "Verify error model section exists before merging §20 into it."
}
```

Failure behavior:
- **`atomic`**: The applier discards the working copy and reports
  `ASSERTION_FAILED`. The AI MUST NOT attempt to fix assertions — they
  are facts about the document. Respond with `status: blocked`.
- **`best_effort`**: This op and all subsequent ops are skipped. The
  partial copy survives.

### `rename_section`

Change a section heading only.

```json
{
  "op": "rename_section",
  "section_id": "§15",
  "new_heading": "Error Model and Hallucination Recovery",
  "reason": "Reflects merged content from §20."
}
```

### `update_frontmatter`

Set specific frontmatter fields.

```json
{
  "op": "update_frontmatter",
  "set": { "version": "0.2.1-draft", "date": "2026-03-19" },
  "reason": "Bump version after structural reconciliation."
}
```

---

## Marker Operations

### `inject_markers`

Add structural markers to the document without altering semantic prose
or data. HTML comments and Pandoc-style anchors are semantically inert
in Markdown — they do not render as visible content.

Use as the first patch on unmarked documents to create stable locators
for subsequent patches.

```json
{
  "op": "inject_markers",
  "section_id": "§11.4",
  "markers": [
    {
      "type": "block",
      "name": "status-code-list",
      "wraps": "| Code | Meaning |",
      "wraps_end": "| 599  | Custom  |"
    },
    {
      "type": "anchor",
      "name": "suggest-intro",
      "after": "The SUGGEST mechanism provides"
    },
    {
      "type": "section_anchor",
      "anchor_id": "sec-wire-text-mode"
    }
  ],
  "reason": "Bootstrap stable locators for subsequent patches."
}
```

Marker types:
- `block` — wraps a content span. `wraps` identifies the start line;
  `wraps_end` identifies the end line. The applier places
  `<!-- BLOCK:name -->` before the `wraps` line and
  `<!-- END BLOCK:name -->` after the `wraps_end` line.
- `anchor` — inserts `<!-- ANCHOR:name -->` on the line after a unique
  substring identified by `after`.
- `section_anchor` — appends `{#anchor_id}` to the section's heading.
  If the heading already has an anchor matching the requested one,
  this is a no-op. If the heading has a different anchor, the applier
  replaces it with the new one and emits a warning.

---

## Per-Op Flags

Any operation MAY include:

```json
{
  "review_required": true,
  "allow_fuzzy": true,
  "reason": "Locator matched via substring, not block marker."
}
```

`review_required` signals the AI is not fully confident. The applier
may present flagged ops for human review before applying.

`allow_fuzzy` enables tier-3 fuzzy string matching for this op's
locators. When absent or false, the applier stops at tier 2
(whitespace-normalized). Set this only when the locator is close but
may differ in minor wording, punctuation, or formatting. Short, highly
specific locators should NOT use fuzzy matching.
