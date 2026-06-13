---
name: tsdoc-voice
version: "1.0.0"
description: >
  Enforce the project's TSDoc Voice Guide when writing, reviewing, or refactoring
  TypeScript documentation comments. Use this skill whenever you are writing TSDoc
  comments, documenting schemas (Zod or otherwise), adding JSDoc/TSDoc to functions
  or types, reviewing PR documentation quality, or when the user mentions TSDoc,
  documentation style, doc comments, or code documentation standards. Also trigger
  when writing file headers, section dividers, `@example`, `@deprecated`,
  `@defaultValue`, or `ai()` metadata alongside TSDoc.
allowed-tools: Read Glob Grep Edit
metadata:
  ulid: 01KM17JDVNJ333TN3R5BGZB5QS
---

# TSDoc Voice Guide — Skill

Apply the project's TSDoc documentation standards consistently across all TypeScript
files. The full specification lives in `references/tsdoc-spec.md` — read it when you
need exact rules or examples for a specific section. This skill distills the
decision-making workflow and the rules you need in working memory.

## When This Skill Applies

- Writing new TypeScript files with exports (schemas, functions, types)
- Adding or editing doc comments on existing code
- Reviewing documentation quality in PRs or diffs
- Refactoring doc comments for voice/style compliance
- Any task where the user asks about TSDoc standards or documentation conventions

## Core Philosophy

TSDoc serves two audiences: **humans reading source** and **IDE hover/tooling**.
Every comment must be self-sufficient — a reader with no access to external documents
must understand what the symbol does. Formal references supplement but never replace
explanations. Voice is imperative, not conversational. Constraints are preserved;
audience coaching is deleted.

## Quick Rules (Keep in Working Memory)

### File Headers
- Use plain `//` comments — never `/** */` for file headers
- No `@module`, `@version`, `@license`, `@author` tags in source
- Max 15 lines (excluding copyright)
- Structure: copyright line, divider, module name, 1-3 sentence purpose
- If this module implements a spec, name and link it once here
- No workflow diagrams, mapping tables, or agent protocols in headers

### Section Dividers
- One-liner with `§ N` and a purpose clause after the em dash
- Design rationale belongs in the TSDoc of the schema constant that follows, not in the divider
- Example: `// -- S 5  Entity Inventory -- domain entities the plan references --`

### Exported Schemas (Zod Objects)
- Every exported schema gets a `/** */` block
- Line 1: one-sentence summary of what it validates (imperative mood)
- `@remarks` only when needed: cross-field refinements, invariants, forward-compat notes
- Internal (non-exported) schemas: summary line only

### Inline Field Comments
- Self-explanatory fields: no comment needed
- Fields with constraints/enums/non-obvious semantics: short `/** */`
- Enum values: use compact block format with backtick-quoted values and em dashes
- Reusable enums: document at definition site, reference with `{@link}` at usage sites

### Exported Functions
- Summary: verb-first, imperative mood ("Parse and validate..." not "This function...")
- `@param` for each parameter with `-` separator
- `@returns` describing what comes back
- `@throws` for each exception type (use `{@link}` for the type)
- `@remarks` only for: detection heuristics, error wrapping, non-obvious perf characteristics
- Internal functions: summary only

### Types (z.infer)
- One-line `/** */` with a **role-oriented label**
- Link to the source schema with `{@link}`
- Do not restate the schema's summary — describe the type's role in the system

### Formal-Model Cross-References
- Self-sufficient explanation first, reference in brackets at the end
- Never write a comment that is only a formal ref

### `@example` Blocks
- Write when: signature is ambiguous, format isn't obvious from type, or common mistakes exist
- For schemas: write when `.refine()`, `.superRefine()`, or `.transform()` is used
- Show a valid object literal that passes parsing
- Max 10 lines, at least one valid input, no prose inside — use `// => result` comments
- One example block per symbol

### `@deprecated`
- Always name the replacement with `{@link}`
- Include the version when deprecation was introduced
- Keep existing TSDoc intact — don't delete it
- For deprecated enum members: notice in `@remarks` + trailing `// deprecated` inline

### `@defaultValue`
- Skip when `.default()` contains a literal value (the code is the documentation)
- Use when: default is computed, imported from a constant, or set in `.transform()`
- For `.transform()` implicit defaults, add parenthetical `(applied inside .transform())`

### `ai()` Layer Interaction
- TSDoc is source of truth for what a symbol *is*
- `ai()` metadata is source of truth for how an LLM should *produce/consume* values
- `ai().instruct()` may repeat TSDoc summary (intentional duplication for different audience)
- Semantic content must not contradict between TSDoc and `ai()`
- Place `ai()` calls in the same file, directly after the schema constant they annotate

## Review Checklist

When reviewing or writing TSDoc, verify each file passes these checks:

1. File header is `//` comment, max 15 lines
2. No `@module`, `@version`, `@license`, `@author` in source
3. Every exported schema/function/type has a `/** */` block
4. Every `/** */` summary is one sentence, imperative mood
5. `@remarks` present only for cross-field refinements, invariants, or heuristics
6. `@param` / `@returns` / `@throws` on every exported function
7. Formal-model refs supplement, never replace, explanations
8. No audience coaching ("the human should...", "lets the human see...")
9. Domain constraints preserved (rewritten in imperative voice, not deleted)
10. No design documents embedded in file headers
11. Internal schemas have at most a summary line
12. Reusable enums documented at definition site, not duplicated at each usage
13. Section dividers include purpose clause after em dash
14. `@deprecated` present on any symbol scheduled for removal, with `{@link}` to replacement
15. `@example` blocks are max 10 lines with at least one valid input case
16. TSDoc and `ai()` metadata do not contradict each other

## Voice Transformation Patterns

These patterns capture the most common rewrites. Internalize them rather than
looking them up each time.

**Soft coaching -> imperative constraint:**
- Before: "Should be concrete enough to verify"
- After: "Must name a countable artifact or measurable outcome"

**Opaque formal ref -> self-sufficient + ref:**
- Before: `/** [Def 3.2.1] Must be >= authority of requestedBy. */`
- After: `/** Actor who authorized this version transition. Must have authority >= requestedBy. Self-authorization is forbidden [Def 3.2, Ax 2.4]. */`

**Schema summary copy -> role label:**
- Before: `/** An ADR record with lifecycle and supersession tracking. */`
- After: `/** Validated ADR record, inferred from {@link ADRRecordSchema}. */`

**Missing failure mode -> explicit @throws:**
- Before: `@returns The validated mental model.`
- After: `@returns A validated {@link MentalModel}. @throws {@link ZodError} If input fails schema validation.`

## Full Specification Reference

For exact formatting rules, before/after examples, or edge cases not covered above,
read `.repo/references/01KM17JDVNJ333TN3R5BGZB5QS-tsdoc-spec.md`. Key sections:

| Section | Topic |
|---------|-------|
| S 1 | File headers |
| S 2 | Section dividers |
| S 3 | Schema constants |
| S 4 | Inline field comments |
| S 5 | Functions |
| S 6 | Types |
| S 7 | Formal-model cross-references |
| S 8 | What does NOT belong in TSDoc |
| S 9 | Checklist |
| S 10 | `@example` blocks |
| S 11 | `@deprecated` |
| S 12 | `@defaultValue` |
| S 13 | `ai()` layer interaction |
