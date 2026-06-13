---
name: schema-designer
description: >
  Design and produce high-quality, standards-compliant schemas for any domain.
  Trigger this skill whenever the user asks to "design a schema", "model a domain",
  "create a data model", "define types", "write interfaces", "build a contract",
  "create a JSON Schema", "write Zod schemas", "define Protobuf messages",
  "design a database schema", or any variation of defining the structural contract
  for entities, fields, types, relationships, and constraints. Also trigger when
  the user uploads an existing schema and asks for a review, audit, refactor,
  migration, or evolution plan. Trigger when the user describes a system, product,
  or feature and wants its data model formalized. Even if the user says something
  casual like "what should my data look like" or "help me think through the
  structure", this skill applies. If a schema or data model is being created,
  evaluated, or evolved — use this skill.
---

# Schema Designer

Design rigorous, standards-compliant schemas following the **Rules for Great
Schema Design** standard (31 rules across 6 parts). Every schema produced by
this skill is scored against the standard's review scorecard before delivery.

## Before you begin

1. **Read the reference** — `references/schema-design-rules.md` contains the
   full standard: all 31 rules with rationale, good/bad examples, violation
   signals, the compatibility matrix, and the schema language mapping table.
   Read it before designing anything. Do not guess rule details from memory.

2. **Read the scorecard** — `references/scorecard-quick-ref.md` contains the
   compact review scorecard. You will score every schema you produce against
   it before delivering to the user.

---

## Core Workflow

### Phase 1 — Understand the Domain

Before writing a single type definition, establish these facts through
conversation or by analyzing the user's input:

| Question | Why it matters |
|---|---|
| What **entities** exist? | Drives the top-level type inventory. |
| What **relationships** connect them? | Composition vs. aggregation vs. association (Rule 12). |
| What is the **lifecycle ownership** graph? | Who creates, owns, and deletes what (Rules 11–14). |
| What **enums** exist and are they closed? | Closed + versioned enums (Rule 3). |
| Are there **polymorphic** structures? | Discriminated unions required (Rule 8). |
| What **temporal** fields exist? | Precision, timezone, format (Rule 6). |
| What **numeric** fields carry domain meaning? | Units must be declared (Rule 7). |
| Is there **PII, PHI, or credentials**? | Sensitivity classification required (Rule 23). |
| Is this **multilingual**? | Localization strategy (Rule 25). |
| Is this **multi-actor** (multiple authors/systems)? | Provenance metadata (Rule 26). |
| What **schema language** does the user want? | Default to TypeScript/Zod. Alternatives: JSON Schema, Protobuf, SQL DDL, Avro. |
| What **version** is this? | Explicit semver from day one (Rule 19). |

If the user has not specified enough, ask — but prefer to infer reasonable
defaults and state your assumptions explicitly rather than blocking on
questions. Bias toward producing a concrete draft the user can react to.

### Phase 2 — Design the Schema

Apply the rules in order of structural dependency. This is not a checklist
to run after the fact — each rule shapes the design as you write it.

**Pass 1 — Type skeleton**
Define every entity with its fields. For each field:
- Assign a single, unambiguous type (Rule 1).
- Encode all constraints in the schema, not in comments (Rule 2).
- Distinguish nullable vs. optional vs. absent (Rule 4).
- Declare array item type, cardinality, and ordering semantics (Rule 5).
- Annotate temporal fields with format, timezone, precision (Rule 6).
- Declare units on meaningful numeric fields (Rule 7).
- Use discriminated unions for polymorphic structures (Rule 8).
- Declare defaults in the schema (Rule 9).
- Use closed, versioned enums (Rule 3).

**Pass 2 — Identity and relationships**
- Assign stable, opaque identifiers to every entity (Rule 10).
- Make every relationship navigable in at least one direction (Rule 11).
- Annotate composition / aggregation / association explicitly (Rule 12).
- Ensure all FKs point to declared targets (Rule 13).
- Declare topology constraints on any cyclic references (Rule 14).

**Pass 3 — Normalization and coherence**
- Ensure single source of truth per fact (Rule 15).
- Eliminate bag-of-arrays entities or justify them (Rule 16).
- Extract cross-cutting types into shared definitions (Rule 17).
- Distinguish computed vs. stored fields (Rule 18).

**Pass 4 — Evolution and compatibility**
- Assign explicit semver version (Rule 19).
- Resolve any duplicate-version entities (Rule 20).
- Classify any changes if evolving an existing schema (Rule 21).
- Annotate any deprecated fields (Rule 22).

**Pass 5 — Operational annotations**
- Classify sensitive fields (Rule 23).
- Mark identity/provenance fields as immutable (Rule 24).
- Declare localization strategy if multilingual (Rule 25).
- Add provenance metadata if multi-actor (Rule 26).

**Pass 6 — Documentation and generability**
- Enforce consistent naming conventions (Rule 27).
- Verify the schema can generate validators mechanically (Rule 28).
- Mark intentional extension points explicitly (Rule 29).
- Confirm access patterns inform but don't dictate structure (Rule 30).
- Ensure the schema is readable as a standalone artifact (Rule 31).

### Phase 3 — Self-Review (Scorecard)

Before presenting the schema to the user, score it against the review
scorecard in `references/scorecard-quick-ref.md`.

For each rule, assign:
- **Pass** — fully satisfied.
- **Warn** — documented deviation with rationale.
- **Fail** — unaddressed violation.

**Compliance threshold:**
- All MUST rules must Pass.
- All SHOULD rules must Pass or have documented rationale.

If any MUST rule Fails, fix it before delivering. If a SHOULD rule is
intentionally not met, add a `note` or `x-waiver` annotation in the schema
explaining why.

Include the completed scorecard as an appendix or trailing comment in the
delivered schema so the user can see the audit trail.

### Phase 4 — Deliver

Produce the schema in the user's requested language. Default to
**TypeScript with Zod** unless instructed otherwise. When delivering:

1. **One file per logical module** — if the schema has 3+ entities with
   distinct concerns, split into modules. Otherwise, a single file is fine.
2. **Include version metadata** — schema_version as a const.
3. **Include the scorecard** — either as trailing comments or a companion
   markdown file.
4. **State assumptions** — list any design decisions where you chose a
   default the user didn't specify (e.g., "I used UUIDs for identity;
   switch to ULIDs if you need lexicographic ordering").

---

## Output Format by Language

### TypeScript / Zod (default)

```typescript
import { z } from "zod";

// Schema version
export const SCHEMA_VERSION = "1.0.0" as const;

// Shared definitions
const AudienceTier = z.object({
  tier: z.enum(["beginner", "intermediate", "advanced"]),
  locale: z.string().regex(/^[a-z]{2}-[A-Z]{2}$/).optional(),
});

// Entity
const MyEntity = z.object({
  id: z.string().uuid().describe("Opaque unique identifier"),
  // ... fields with full constraints
});

export type MyEntity = z.infer<typeof MyEntity>;
```

### JSON Schema

Use draft 2020-12. Include `$schema`, `$id`, `definitions`, `required`,
constraint keywords, `description` on every non-obvious field, and
`x-` extensions for annotations the spec doesn't cover natively
(sensitivity, immutability, graph constraints, etc.).

### Protobuf

Use proto3. Add `option` annotations for metadata. Use `google.protobuf.Timestamp`
for temporal fields. Use `oneof` for discriminated unions.

### SQL DDL

Use `CREATE TABLE` with `CHECK` constraints, `NOT NULL`, `REFERENCES`,
`DEFAULT`, and comments for annotations. Prefer PostgreSQL dialect unless
specified otherwise.

---

## Evolving an Existing Schema

When the user provides an existing schema for review or evolution:

1. Run the scorecard against the current schema first.
2. Present the scorecard results to the user.
3. Propose changes grouped by severity:
   - **Fail (MUST)** — these must be fixed.
   - **Warn (SHOULD)** — recommend fixing; document if deferring.
   - **Enhancement** — improvements beyond the standard.
4. Classify every proposed change using the compatibility matrix
   (Appendix A of the reference): backward-compatible, forward-compatible,
   or breaking.
5. If breaking changes are needed, produce a migration plan with:
   - Deprecation annotations on the current version.
   - A new version with the changes applied.
   - A migration guide (what consumers must change).

---

## Common Pitfalls to Avoid

These are patterns that consistently violate the standard. Watch for them:

- **`type: any` or `type: unknown` on a required field** → Rule 1 violation.
- **Constraints in comments instead of schema keywords** → Rule 2 violation.
- **`string` fields that are enums in practice** → Rule 3 violation.
- **`?` conflating absent and null** → Rule 4 violation.
- **`array` with no item type or cardinality** → Rule 5 violation.
- **Date fields typed as `string` with no format** → Rule 6 violation.
- **Numeric fields with no unit** → Rule 7 violation.
- **Union types with no discriminator** → Rule 8 violation.
- **Business-meaningful primary keys** → Rule 10 violation.
- **Array of objects with no FK back** → Rule 11 violation.
- **Same field defined independently on 3+ entities** → Rules 15, 17 violation.
- **`schema_version` as an unresolved constant** → Rule 19 violation.
- **Field removed without prior deprecation** → Rule 22 violation.
- **PII field with no sensitivity annotation** → Rule 23 violation.
- **Mixed naming conventions** → Rule 27 violation.

---

## When the User Provides Only a Description

If the user describes a system in natural language without any existing
schema, your job is to extract the implicit data model:

1. Identify nouns → candidate entities.
2. Identify verbs / relationships between nouns → candidate relationships.
3. Identify adjectives / constraints → candidate field constraints.
4. Identify lifecycle language ("belongs to", "owned by", "shared across")
   → composition / aggregation / association.
5. Identify volatility ("changes frequently", "set once", "computed from")
   → mutability and derivation annotations.

Draft the schema, present it with your assumptions listed, and iterate.

---

## Reminder

The full rule set, with rationale, examples, violation signals, the
compatibility matrix, and the schema language mapping table are in
`references/schema-design-rules.md`. Consult it for any rule you are
uncertain about. Never guess a rule's details — verify against the
reference.
