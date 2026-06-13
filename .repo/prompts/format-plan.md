---
name: format-plan
description: Format documents or PlanSchema JSON into phased markdown plans with CLI-visible progress. Use this for informal/human-readable plans — use the adv-planning skill for formal JSON plans.
tags: [plan, format, refactor, markdown]
---
You are formatting a document into a **phased execution plan** optimized for
tracking via `repo docs plans`. Follow these rules strictly.

**Relationship to adv-planning skill:** This prompt produces informal markdown
plans for CLI tracking. The `adv-planning` skill produces formal PlanSchema
JSON. Use this prompt when:
- The task is XS/S and doesn't warrant formal planning
- You need a human-readable markdown view of an existing PlanSchema JSON
- The user explicitly asks for a markdown plan

Use the `adv-planning` skill instead when the task is M/L/XL and requires
schema-compliant JSON with verification economics, actors, and stop conditions.

## Input Modes

This prompt accepts two types of input:

1. **Prose/document** — restructure into phased markdown (default behavior)
2. **PlanSchema JSON** — convert a formal plan into CLI-trackable markdown
   (see [Converting from PlanSchema JSON](#converting-from-planschema-json))

---

## Structure

1. **YAML frontmatter** — every plan file MUST start with:

```yaml
---
title: "<concise plan title>"
status: proposal        # proposal → active → accepted → archived
date: YYYY-MM-DD
source: null             # or path to PlanSchema JSON if converted
---
```

2. **Context section** — a short paragraph explaining *why* this plan exists:
   what problem it solves, what prompted it, and the intended outcome.

3. **Phase headings** — use exactly this format:

```markdown
## Phase N — <Short Imperative Title>
```

The `## Phase` prefix is what the CLI parses. Number phases sequentially.
Use an em-dash (—) or hyphen (-) to separate the number from the title.

4. **Checkboxes for tasks** — every actionable item inside a phase MUST be
   a GitHub-flavored checkbox:

```markdown
- [ ] Pending task
- [x] Completed task
```

The CLI counts `- [ ]` and `- [x]` lines to compute per-phase and overall
progress. Sub-bullets without checkboxes (details, notes) are fine but are
not tracked.

5. **Dependencies** — after each phase's tasks, state its dependencies:

```markdown
**Depends on:** Phase 1, Phase 3
```

6. **Execution Order table** — after all phases, add a summary:

```markdown
## Execution Order

| Priority | Phase | Effort | Dependencies |
|---|---|---|---|
| 1 | Phase 1 (short name) | XS/S/M/L/XL | None |
| 2 | Phase 2 (short name) | M | Phase 1 |
```

Use the same T-shirt sizes as PlanSchema: **XS, S, M, L, XL**.

7. **Verification section** — at the end, describe how to test/verify the
   completed plan.

---

## Converting from PlanSchema JSON

When the input is a PlanSchema JSON (v0.3.0), apply this mapping:

| PlanSchema field | Markdown output |
|---|---|
| `metadata.description` / `problem.problemStatement` | Context section |
| `problem.successOutcome` | Verification section |
| `steps` (grouped by `executionOrder`) | Phases |
| `steps[].title` | Checkbox task text |
| `steps[].description` | Sub-bullet under task (no checkbox) |
| `steps[].size` | Effort column in Execution Order table |
| `steps[].dependsOn` | `**Depends on:**` line |
| `steps[].verification` | Sub-bullets listing verification commands |
| `executionOrder.parallelizableGroups` | Group into same phase |
| `acceptanceCriteria` | Verification section items |
| `risks` (severity high/critical) | Note under affected phase |
| `decisions` | Context section or phase notes |

### Grouping steps into phases

PlanSchema uses flat `steps` with a dependency graph. To convert:

1. Follow `executionOrder.sequence` as the canonical order
2. Group consecutive steps that share no cross-group dependencies into
   one phase — or use `parallelizableGroups` as phase boundaries
3. If the JSON has multi-phase files (`plan-phase-N.json`), each file
   becomes one phase
4. Name each phase from the common theme of its grouped steps

### Status mapping

| PlanSchema state | Markdown frontmatter `status` |
|---|---|
| Plan just generated | `proposal` |
| Execution started (any step in progress) | `active` |
| All acceptance criteria met | `accepted` |
| Superseded or completed and filed | `archived` |

### Preserving traceability

When converting from JSON, include:
- `source:` in frontmatter pointing to the JSON file path
- Step IDs as HTML comments after each checkbox: `- [ ] Task <!-- step-001 -->`
  (invisible in rendered markdown, useful for round-tripping)

---

## Style rules

- Keep phase titles short and imperative ("Add X", "Align Y", not
  "Adding X" or "X should be aligned").
- Use **bold** for key terms on first mention within a phase.
- Tables are preferred over prose for mappings and cross-references.
- Avoid nesting phases. If a phase is too large, split it.
- Mark phases complete by checking ALL their boxes. The CLI shows:
  - `done` (green) when all boxes are checked
  - `partial` (yellow) when some are checked
  - `pending` (dim) when none are checked

## What to avoid

- Do NOT use `## Phase` for non-actionable sections (Context, Execution
  Order, Verification). These are parsed as phases otherwise.
- Do NOT put checkboxes outside of phase sections — they won't be
  attributed to any phase.
- Do NOT use deeply nested checkbox lists (only top-level `- [ ]` inside
  a phase is tracked).
- Do NOT invent step details when converting from JSON — if a PlanSchema
  field is empty or absent, omit it rather than fabricating content.

## Example output

The CLI renders plans like this:

```
  FILE               TITLE                    STATUS  PROGRESS
  ─────────────────  ───────────────────────  ──────  ──────────────────────
  my-plan.md         Migrate auth system      active  2/5 phases  8/14 tasks

  Migrate auth system phases:
    [████████████████]  3/3  done     Phase 1 — Extract session store
    [████████████████]  2/2  done     Phase 2 — Add token rotation
    [██████░░░░░░░░░░]  2/4  partial  Phase 3 — Update middleware
    [░░░░░░░░░░░░░░░░]  0/3  pending  Phase 4 — Migration script
    [░░░░░░░░░░░░░░░░]  0/2  pending  Phase 5 — Cleanup legacy code
```

When reformatting an existing document, preserve all substantive content.
Restructure it into phases with checkboxes. Convert prose goals into
discrete, verifiable tasks. Add frontmatter if missing.
