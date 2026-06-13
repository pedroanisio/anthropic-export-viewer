---
title: "Rules for Great Schema Design"
subtitle: "A Standard for Contract Clarity, Domain Modeling, and Machine-Interpretable Structure"
version: "2.0.0"
date: "2026-03-09"
status: "Draft for Review"
normative_language: "RFC 2119"
disclaimer: >
  No information within this document should be taken for granted.
  Any statement or premise not backed by a real logical definition
  or verifiable reference may be invalid, erroneous, or a hallucination.
  The reader is responsible for independent verification.
  See Appendix B for external grounding and references.
---

# Rules for Great Schema Design

---

## 0. Purpose, Scope, and Governance

### 0.1 What This Document Governs

This standard governs the **logical design** of schemas — the structural
contracts that define entities, fields, types, relationships, and constraints
for systems that produce, consume, or validate structured data.

It applies to any schema expressed as or translatable to: JSON Schema, OpenAPI
component definitions, TypeScript interfaces/types, Zod schemas, Protobuf
message definitions, Avro schemas, SQL DDL, or equivalent formalisms.

### 0.2 What This Document Does Not Govern

This standard does not prescribe:

- **Physical storage layout** — partitioning, sharding, indexing, column
  ordering for cache-line alignment. These are implementation concerns
  addressed at the storage layer.
- **Serialization wire format** — JSON, MessagePack, CBOR, Protobuf binary.
  The schema defines shape; the codec defines encoding.
- **CI/CD tooling** — linters, schema registry pipelines, compatibility
  checkers. These are implementations *of* the standard, not parts *of* it.
- **API design** — pagination envelopes, error response formats, read/write
  scope annotations (`readOnly`/`writeOnly`), HTTP method semantics. These
  are interface-layer concerns. A field's mutability in a specific endpoint
  is a property of that endpoint's contract, not of the data model.
- **Application-layer business logic** — validation rules that depend on
  runtime state, cross-entity invariants enforced in code, soft-delete
  patterns. The schema governs static structure; the application governs
  dynamic behavior.

### 0.3 Relationship to Other Layers

```
┌──────────────────────────────────────────────┐
│  Application Logic    (business rules, UX)   │
├──────────────────────────────────────────────┤
│  API / Interface      (endpoints, errors,    │
│                        pagination, auth)      │
├──────────────────────────────────────────────┤
│  ➤ THIS STANDARD      (logical schema:       │
│                        types, relationships,  │
│                        constraints, evolution)│
├──────────────────────────────────────────────┤
│  Physical Storage     (indexes, partitions,  │
│                        encoding, replication) │
└──────────────────────────────────────────────┘
```

Rules in this standard may *inform* decisions at adjacent layers, but they
govern only the logical schema layer.

### 0.4 Normative Language

This document uses RFC 2119 keywords to distinguish obligation levels:

- **MUST / MUST NOT** — Non-negotiable invariant. Violation constitutes a
  schema defect. No exceptions without a formal waiver (see §0.5).
- **SHOULD / SHOULD NOT** — Strong default. Deviation is permitted when a
  documented rationale exists and is recorded in the schema's own metadata
  (e.g., a `note` field or design-decision record).
- **MAY** — Discretionary. Useful practice that improves quality but is not
  required for compliance.

Each rule below is annotated with its normative tier.

### 0.5 Exception and Waiver Policy

When a rule marked MUST cannot be satisfied:

1. The deviation MUST be documented in the schema itself (not in external
   prose), using a `waiver` or `note` annotation on the affected entity or
   field.
2. The documentation MUST state: which rule is waived, why, what the expected
   remediation timeline is, and who approved the waiver.
3. Waivers MUST be reviewed at each schema version increment. A waiver that
   persists across three or more minor versions without remediation MUST be
   escalated to the schema owner.

For rules marked SHOULD, deviation requires only a recorded rationale — no
formal waiver process.

---

## Part I — Type Safety and Precision

### Rule 1. Every field MUST have a single, unambiguous type

A field typed `unknown`, `any`, or `object` is a hole in the contract. If a
field is required, its consumers must know its shape at design time. If the
shape genuinely varies, use a discriminated union with an explicit tag field
(see Rule 8).

**Bad:**
```yaml
# What is "audience"? A string? An array? An object?
audience:
  type: unknown
  required: true
```

**Good:**
```yaml
audience:
  type: array
  items:
    type: object
    properties:
      tier:
        type: string
        enum: [beginner, intermediate, advanced]
      locale:
        type: string
        pattern: "^[a-z]{2}-[A-Z]{2}$"
    required: [tier]
  minItems: 1
```

**Violation signal:** A required field whose type cannot be validated without
out-of-band documentation.

---

### Rule 2. Constraints MUST live in the schema, not in documentation

Min/max values, regex patterns, string length bounds, array cardinality
limits, numeric precision — all of these are part of the type. If a field is
`number` but only values 1–100 are valid, the schema must encode that
constraint. Prose-only constraints are invisible to validators, code
generators, and every downstream consumer.

**Bad:**
```yaml
# "duration_ms should be between 100 and 30000" — says the wiki page
duration_ms:
  type: integer
```

**Good:**
```yaml
duration_ms:
  type: integer
  minimum: 100
  maximum: 30000
  description: "Step duration in milliseconds"
```

**Violation signal:** A constraint that exists in documentation, code
comments, or tribal knowledge but not in the schema definition.

---

### Rule 3. Enums MUST be closed, versioned, and never overloaded

Each enum value SHOULD represent exactly one semantic meaning. If two values
would trigger identical behavior in every consumer, they should be merged.

Enums MUST NOT be extended without a schema version increment. If the enum is
expected to grow, the schema SHOULD declare an extension strategy: either an
explicit `other` value with a companion freetext field, or a documented
versioning policy.

**Bad:**
```yaml
method:
  type: string  # any string accepted — consumers must guess valid values
```

**Good:**
```yaml
method:
  type: string
  enum:
    - socratic_questioning
    - worked_example
    - scaffolding
    - spaced_repetition
    - interleaving
    - elaborative_interrogation
    - retrieval_practice
    - peer_instruction
```

**Violation signal:** An enum where two values are semantically
indistinguishable; a string field that is an enum in practice but not in
declaration.

---

### Rule 4. Nullable, optional, and absent MUST be distinguished

These three states carry different semantics:

- **Absent** — the field was never provided (the schema version that
  introduced it may be newer than the document).
- **Null** — the field was explicitly set to "no value."
- **Present** — the field carries data.

A schema MUST declare which of these states are legal per field. The common
shorthand `?` (optional) conflates absent and null — if they have different
meanings in the domain, the schema must distinguish them.

**Bad:**
```typescript
// Does undefined mean "not set" or "use default"? Does null mean "clear it"?
voice_override?: string;
```

**Good:**
```typescript
// Absent: use system default. Null: explicitly disable voice. Present: use this voice ID.
voice_override: string | null | undefined;
// With documentation:
// - undefined → inherit from parent config
// - null      → explicitly no voice
// - string    → voice ID to use
```

**Violation signal:** Consumer code that checks `if (field === null ||
field === undefined)` identically — the schema failed to express the
distinction the domain requires.

---

### Rule 5. Array fields MUST declare item type, cardinality, and ordering semantics

`steps: array` is incomplete. `steps: GuidedSolutionStep[]` with
`minItems: 1` and `ordered: true` is a contract.

Without item-type annotation, the array is a black box. Without cardinality
bounds, consumers can't allocate, paginate, or validate. Without ordering
declaration, consumers can't know whether insertion order is significant
(a sequence) or irrelevant (a set).

**Bad:**
```yaml
skills:
  type: array  # array of what? how many? does order matter?
```

**Good:**
```yaml
skills:
  type: array
  items:
    $ref: "#/definitions/Skill"
  minItems: 1
  maxItems: 200
  x-ordering: significant  # insertion order defines prerequisite chain
```

```yaml
tags:
  type: array
  items:
    type: string
  uniqueItems: true
  x-ordering: insignificant  # this is a set, not a list
```

**Violation signal:** An array field where consumers disagree about whether
reordering the elements would change semantics.

---

### Rule 6. Temporal fields MUST declare precision, timezone, and format

`created: string(min)` is not a date — it's a string with a minimum length
constraint that happens to hold a date. Temporal fields MUST use an explicit
format annotation (ISO 8601 is the conventional choice) and MUST declare
timezone handling (UTC-normalized, local-with-offset, or timezone-naive).

**Bad:**
```yaml
created:
  type: string
  minLength: 1  # this is a string constraint, not a date constraint
```

**Good:**
```yaml
created:
  type: string
  format: date-time       # ISO 8601: 2026-03-09T14:30:00Z
  x-timezone: UTC         # all values normalized to UTC
  x-precision: seconds    # no sub-second precision stored
```

**Violation signal:** A field named `*_at`, `*_date`, or `*_time` whose type
is `string` without a `format` annotation.

---

### Rule 7. Numeric fields with domain meaning MUST declare units

This is the numeric analog to Rule 6. A field `weight: number` without unit
declaration is exactly as ambiguous as `created: string` without format
declaration. Units are especially critical for monetary values, where amount,
currency, and decimal precision are inseparable.

**Bad:**
```yaml
price:
  type: number  # dollars? cents? reais? euros? integer cents or float dollars?

duration:
  type: integer  # seconds? milliseconds? minutes?
```

**Good:**
```yaml
price:
  type: object
  properties:
    amount:
      type: integer
      description: "Value in minor units (e.g., cents)"
    currency:
      type: string
      pattern: "^[A-Z]{3}$"  # ISO 4217
  required: [amount, currency]

duration_ms:
  type: integer
  minimum: 0
  x-unit: milliseconds
```

Self-documenting field names (`duration_ms`, `weight_kg`) are an acceptable
alternative to annotation when the convention is enforced project-wide. But
the unit MUST be recoverable from the schema alone — never from tribal
knowledge.

**Violation signal:** A numeric field where two consumers disagree about the
unit of measurement.

---

### Rule 8. Polymorphic structures MUST have an explicit discriminator

If a field can hold different shapes depending on context, there MUST be a
sibling field that unambiguously determines which shape applies. The mapping
from discriminator values to shapes MUST be exhaustive and documented in the
schema.

**Bad:**
```yaml
value:
  type: union  # union of what? how does the consumer know which branch?
```

**Good:**
```yaml
condition:
  type: object
  discriminator:
    propertyName: type
  oneOf:
    - $ref: "#/definitions/SkillMasteryCondition"     # type: "skill_mastery"
    - $ref: "#/definitions/TurnCountCondition"         # type: "turn_count"
    - $ref: "#/definitions/TimeElapsedCondition"       # type: "time_elapsed"
  required: [type]
```

**Violation signal:** Consumer code that uses `typeof` checks, property
probing, or try/catch parsing to determine which branch of a union a value
belongs to.

---

### Rule 9. Default values SHOULD be declared in the schema

If `interactive` defaults to `true` when absent, the schema should say so.
Hidden defaults create divergent behavior across implementations and make the
schema unreproducible from its definition alone.

This is a SHOULD rather than MUST because some schema languages (Protobuf,
Avro) handle defaults natively while others (JSON Schema) treat them as
advisory. The obligation is: if the schema language supports default
declarations, use them; if it doesn't, document defaults in the field's
`description`.

**Bad:**
```yaml
interactive:
  type: boolean  # defaults to... what? depends on who you ask
```

**Good:**
```yaml
interactive:
  type: boolean
  default: true
  description: "Whether the canvas accepts user input. Defaults to true."
```

**Violation signal:** Two independent implementations of the same schema that
produce different behavior for an absent field.

---

## Part II — Identity and Relationships

### Rule 10. Every entity MUST have a stable, opaque identity

Primary keys SHOULD be semantically meaningless (UUIDs, CUIDs, ULIDs — not
composite natural keys). Natural keys change; business rules change; opaque
identifiers don't. If a natural key is needed for lookups, model it as a
unique index, not the PK.

**Bad:**
```yaml
# PK is a business-meaningful composite that will break when naming conventions change
id:
  type: string
  pattern: "^[A-Z]{3}-[0-9]{4}-Q[1-4]$"  # e.g., "ENG-2026-Q1"
```

**Good:**
```yaml
id:
  type: string
  format: uuid
  readOnly: true
  description: "Opaque unique identifier"

# Natural key as a separate unique field
fiscal_quarter_code:
  type: string
  pattern: "^[A-Z]{3}-[0-9]{4}-Q[1-4]$"
  x-unique: true
```

**Exception:** Lookup tables with genuinely immutable codes (ISO 3166 country
codes, ISO 4217 currency codes).

**Violation signal:** A PK whose value encodes business meaning that could
change independently of the entity's identity.

---

### Rule 11. Every relationship MUST be explicitly navigable in at least one direction

If entity A contains an array of B, there must be either a composition edge
(A owns B's lifecycle) or a foreign key on B pointing to A. An array field
with no corresponding FK or composition annotation is an undeclared
relationship — it can't be enforced, indexed, or migrated.

**Bad:**
```yaml
# CtsInstance has "widgets: array" but WidgetSlot has no FK back to CtsInstance.
# Is the array the source of truth? Can a widget exist in two instances?
CtsInstance:
  properties:
    widgets:
      type: array
      items: { $ref: "#/definitions/WidgetSlot" }
```

**Good:**
```yaml
CtsInstance:
  properties:
    widget_ids:
      type: array
      items: { type: string, format: uuid }
      description: "Ordered references to WidgetSlot entities"

WidgetSlot:
  properties:
    instance_id:
      type: string
      format: uuid
      x-fk: CtsInstance.id
      description: "The CtsInstance this widget belongs to"
```

**Violation signal:** A consumer that must infer a relationship by matching
field names or array contents across entities rather than following declared
references.

---

### Rule 12. Composition, aggregation, and association MUST be explicit

- **Composition:** Parent owns child's lifecycle. Deleting the parent deletes
  the children. The child has no independent identity outside the parent.
- **Aggregation:** Parent references children, but children can outlive the
  parent.
- **Association:** Two independent entities are linked. Neither owns the other.

Crow's foot notation encodes cardinality, not lifecycle ownership. The schema
MUST annotate which relationship type applies.

**Bad:**
```yaml
# Is GuidedSolutionStep composed into GuidedSolution? Or can steps be shared?
# The 1:* cardinality alone doesn't answer this.
GuidedSolution:
  relationships:
    - target: GuidedSolutionStep
      cardinality: "1:*"
```

**Good:**
```yaml
GuidedSolution:
  relationships:
    - target: GuidedSolutionStep
      cardinality: "1:*"
      type: composition          # steps die with the solution
      cascade_delete: true

AdaptationRule:
  relationships:
    - target: PedagogicalStrategy
      cardinality: "*:1"
      type: aggregation          # strategy survives rule deletion
      cascade_delete: false
```

**Violation signal:** A developer asking "if I delete this parent, what
happens to the children?" and getting no answer from the schema.

---

### Rule 13. Foreign keys MUST point to declared targets

If a field is marked FK, the target entity and target field MUST be
identifiable from the schema alone. An FK to an entity not present in the
schema MUST be annotated as an external reference with enough metadata for
consumers to resolve it.

**Bad:**
```yaml
# VoiceConfig.voice_id is FK — to what? Not declared in this schema.
voice_id:
  type: string
  x-fk: true  # target unknown
```

**Good:**
```yaml
voice_id:
  type: string
  x-fk: "VoiceCatalog.id"
  x-fk-external: true
  x-fk-system: "voice-provider-registry"
  description: "References VoiceCatalog.id in the voice provider service"
```

**Violation signal:** An FK annotation with no target, or a target entity
that doesn't exist in the schema and has no external-reference metadata.

---

### Rule 14. Cyclic reference graphs MUST declare topology constraints

If entity A references B, B references C, and C references A, the schema
MUST declare whether this cycle is intentional. If cycles are prohibited
(the graph must be a DAG), the schema MUST state this. If cycles are
permitted, the schema MUST declare a maximum depth or cycle-tolerance
annotation.

This generalizes the v1 rule on self-referential recursion. Self-reference
(`Skill.prerequisites → Skill.id`) is a special case of the broader problem.

**Bad:**
```yaml
Skill:
  properties:
    prerequisites:
      type: array
      items: { type: string }
      description: "Skill IDs"
      # Can a skill be its own prerequisite? Can A→B→A exist?
```

**Good:**
```yaml
Skill:
  properties:
    prerequisites:
      type: array
      items: { type: string, x-fk: "Skill.id" }
      x-graph-constraint: DAG        # no cycles permitted
      x-max-depth: 5                 # max chain length
      description: "Prerequisite skill IDs. Must form a DAG (no cycles)."
```

**Violation signal:** A reference graph where a consumer performing a
recursive traversal can loop infinitely without the schema having warned them.

---

## Part III — Normalization and Coherence

### Rule 15. One source of truth per fact — MUST

A datum SHOULD live in exactly one place. If two entities both store a user's
name, one of them is a cache — and the schema MUST declare which is
authoritative and what the staleness contract is.

Denormalization is a performance decision at the physical layer; the logical
schema SHOULD be normalized to at least 3NF.

**Bad:**
```yaml
PromptTemplate:
  properties:
    audience: { type: unknown }  # same field, same shape...

AdaptationRule:
  properties:
    audience: { type: unknown }  # ...independently defined on 7 entities
```

**Good:**
```yaml
# Audience is defined once as a shared definition
definitions:
  AudienceTier:
    type: object
    properties:
      tier: { type: string, enum: [beginner, intermediate, advanced] }
      locale: { type: string, pattern: "^[a-z]{2}-[A-Z]{2}$" }
    required: [tier]

PromptTemplate:
  properties:
    audience:
      $ref: "#/definitions/AudienceTier"
```

**Violation signal:** Identical (or near-identical) field definitions
appearing independently on 3+ entities without a shared `$ref` or named type.

---

### Rule 16. No entity SHOULD exist solely as a bag of arrays

If an entity's only purpose is to group arrays, it's either an unnecessary
wrapper or it's missing the fields that would justify its existence. Either
inline the array into the parent, or add the fields that give the entity its
own semantics (timestamps, versioning, ownership, policies).

**Bad:**
```yaml
SkillMap:
  properties:
    global_mastery_threshold:
      type: number      # optional
    skills:
      type: array       # the only real content
  # This entity exists only to hold one array and one optional number.
```

**Good:**
```yaml
SkillMap:
  properties:
    id: { type: string, format: uuid }
    version: { type: string }
    global_mastery_threshold: { type: number, minimum: 0, maximum: 1 }
    created_at: { type: string, format: date-time }
    skills:
      type: array
      items: { $ref: "#/definitions/Skill" }
      minItems: 1
```

**Violation signal:** An entity where removing the array fields leaves zero
or one meaningful scalar.

---

### Rule 17. Cross-cutting concerns SHOULD be typed once and referenced everywhere

If `audience`, `note`, `created_at`, or `audit_metadata` appears on 7+
entities, define it as a named type (or mixin/trait/interface depending on the
schema language). Redefining the same structure independently on each entity
guarantees drift.

**Violation signal:** A field name that appears on 3+ entities with slightly
different type definitions across them.

---

### Rule 18. Computed vs. stored fields SHOULD be distinguished

If `mastery_threshold` can be derived from `p_init`, `p_learn`, and the
global threshold, the schema should annotate whether it is:

- **Source-of-truth** — this is the canonical value.
- **Derived-cached** — computable from other fields, stored for performance.
- **Override-if-present** — uses the derived value unless explicitly set.

**Bad:**
```yaml
mastery_threshold:
  type: number
  # Is this computed? Can I write to it? Does it override the global?
```

**Good:**
```yaml
mastery_threshold:
  type: number
  minimum: 0
  maximum: 1
  x-derivation: override-if-present
  x-derived-from: "SkillMap.global_mastery_threshold"
  description: "Per-skill override. Falls back to SkillMap.global_mastery_threshold if absent."
```

**Violation signal:** A consumer that writes to a derived field and discovers
their value is silently overwritten by a recomputation.

---

## Part IV — Schema Evolution and Compatibility

### Rule 19. Schema versions MUST be explicit, monotonic, and machine-parseable

Every serialized instance MUST carry its schema version. The version MUST
follow a deterministic ordering (semver is the conventional choice). The
schema itself MUST declare which versions are forward-compatible,
backward-compatible, or breaking.

**Bad:**
```yaml
schema_version:
  type: string
  const: CTS_SPEC_VERSION  # unresolved build-time constant — opaque in the schema
```

**Good:**
```yaml
schema_version:
  type: string
  const: "2.0.0"
  description: "Semver. See CHANGELOG.md for compatibility matrix."
```

**Violation signal:** A `schema_version` field whose value cannot be
determined by reading the schema definition alone.

---

### Rule 20. No two entities MUST model the same concept at different versions simultaneously

If `CtsInstance` and `CtsInstanceV2` coexist, the schema MUST declare:
(a) which is canonical, (b) whether v1 is deprecated (see Rule 22),
(c) whether children are shared or duplicated, and (d) what the migration
path is.

Two undifferentiated roots sharing the same children is a data ownership
ambiguity, not a versioning strategy.

**Bad:**
```yaml
# Two root entities, same children, no declared relationship between them
CtsInstance:
  properties:
    prompt_templates: { type: array }
CtsInstanceV2:
  properties:
    prompt_templates: { type: array }
# Which one owns PromptTemplate? Both? Neither?
```

**Good:**
```yaml
CtsInstance:
  x-deprecated: true
  x-deprecated-since: "1.5.0"
  x-replaced-by: CtsInstanceV2
  x-migration: "See migrations/v1-to-v2.md"
  # Children are NOT shared — v1 instances use v1-era children only

CtsInstanceV2:
  x-canonical: true
  # Sole owner of all child entities from schema version 2.0.0 onward
```

**Violation signal:** Two entities with near-identical field lists and no
declared deprecation, migration, or ownership annotation.

---

### Rule 21. Breaking changes MUST be detectable and classified

Adding a required field, removing a field, narrowing an enum, or changing a
type are breaking changes. The schema MUST be stored in a diffable format
(JSON Schema, TypeScript interfaces, Protobuf — not diagrams alone), and
the compatibility classification MUST be documented.

**Compatibility classification** (see Appendix A for full matrix):

- **Backward-compatible** (safe for consumers): adding an optional field,
  widening an enum, relaxing a constraint.
- **Forward-compatible** (safe for producers): removing an optional field,
  adding a new required field with a default.
- **Breaking** (requires major version): removing a required field, narrowing
  an enum, changing a type, renaming a field.

**Violation signal:** A schema diff that a tool cannot classify as breaking
or non-breaking without human interpretation.

---

### Rule 22. Field deprecation MUST be an explicit, annotated state

Before a field is removed (causing a breaking diff per Rule 21), it MUST
pass through a transitional deprecated state. The deprecation annotation
MUST include: (a) the version in which deprecation began, (b) a pointer to
the replacement field or pattern, and (c) a sunset version or date after
which removal is permitted.

**Bad:**
```yaml
# version 3.0.0: "output_format" silently removed. Consumers break.
```

**Good:**
```yaml
output_format:
  type: string
  enum: [json, markdown, html, latex, plain]
  x-deprecated: true
  x-deprecated-since: "2.3.0"
  x-replaced-by: "response_config.format"
  x-sunset: "4.0.0"
  description: "DEPRECATED — use response_config.format instead. Will be removed in 4.0.0."
```

**Violation signal:** A field that disappears between two schema versions
with no prior deprecation annotation.

---

## Part V — Operational Annotations

### Rule 23. Sensitive fields MUST declare data classification

If a schema may contain personally identifiable information (PII), protected
health information (PHI), financial data, or credentials, the affected fields
MUST be annotated with their sensitivity classification. This enables
downstream automation: log masking, access control scoping, retention policy
enforcement, and audit trail generation — all derived mechanically from the
schema, consistent with Rule 28's principle that schemas must generate
validators.

**Bad:**
```yaml
user_email:
  type: string
  format: email
  # No sensitivity annotation. Gets logged in plaintext, exported to analytics,
  # and retained forever.
```

**Good:**
```yaml
user_email:
  type: string
  format: email
  x-sensitivity: pii
  x-data-classification: personal
  x-retention: "365d"
  description: "User's email address. PII — must be masked in logs."
```

This rule is MUST for schemas that handle personal, financial, or health data.
For schemas in domains with no PII exposure (e.g., a game level schema with
no user data), it MAY be omitted.

**Violation signal:** A field containing PII/PHI/credentials with no
sensitivity annotation, discovered during a security audit rather than at
design time.

---

### Rule 24. Identity and provenance fields SHOULD declare immutability

Fields that form an entity's identity (`id`, `created_at`, `author`) or
provenance (`source_system`, `schema_version`) are typically write-once:
set at creation, never modified. The schema SHOULD annotate these fields
as immutable so that consumers, migration tools, and PATCH handlers know
not to accept updates.

**Bad:**
```yaml
id:
  type: string
  format: uuid
  # Nothing prevents a consumer from attempting to mutate this in a PATCH
```

**Good:**
```yaml
id:
  type: string
  format: uuid
  x-immutable: true
  description: "Set at creation. Never modified."

created_at:
  type: string
  format: date-time
  x-immutable: true
```

Note: this is narrower than a general "mutability contract for every field."
General field-level mutability (which fields are PATCHable, which status
transitions are legal) is an API-layer concern outside this standard's scope.
Immutability of identity/provenance fields, however, is a *structural*
property of the data model.

**Violation signal:** An identity field that is modified in production,
discovered via broken foreign key references or audit trail inconsistencies.

---

### Rule 25. Multilingual display fields SHOULD declare localization strategy

If a field is intended for human-facing display in multilingual contexts, the
schema SHOULD declare how localized content is modeled. Common strategies:

- **Single-locale field** with a companion `locale` field on the entity.
- **Localized map** (`{ "en-US": "Hello", "pt-BR": "Olá" }`).
- **Locale-per-entity** (separate rows/documents per locale).

The choice affects storage, querying, and rendering. The schema should not
leave consumers to guess which strategy applies.

**Bad:**
```yaml
name:
  type: string  # is this always English? locale-dependent? who decides?
```

**Good:**
```yaml
name:
  type: object
  additionalProperties:
    type: string
  x-localization: locale-map
  description: "Keyed by BCP 47 locale code. Fallback: en-US."
  example:
    en-US: "Quadratic Equations"
    pt-BR: "Equações Quadráticas"
```

This rule applies as SHOULD, not MUST, because many schemas are
single-locale by design. It becomes MUST when the schema explicitly
serves multilingual consumers.

**Violation signal:** A field displayed in a UI where the locale is
determined by application code rather than by a declaration in the schema.

---

### Rule 26. Multi-actor schemas SHOULD declare provenance metadata

For schemas that mediate data across multiple authors, systems, or
organizations (B2B contracts, multi-tenant platforms, collaborative
authoring tools), the schema SHOULD declare provenance fields: who created
or last modified the entity, from what system, and when.

**Bad:**
```yaml
AdaptationRule:
  properties:
    name: { type: string }
    conditions: { type: array }
    # Who created this rule? When? From which authoring tool? No record.
```

**Good:**
```yaml
AdaptationRule:
  properties:
    name: { type: string }
    conditions: { type: array }
    provenance:
      $ref: "#/definitions/ProvenanceMetadata"

definitions:
  ProvenanceMetadata:
    type: object
    properties:
      created_by: { type: string, description: "Actor ID or system name" }
      created_at: { type: string, format: date-time, x-timezone: UTC }
      modified_by: { type: string }
      modified_at: { type: string, format: date-time, x-timezone: UTC }
      source_system: { type: string }
    required: [created_by, created_at]
```

This is SHOULD, not MUST, because single-author, single-system schemas
(a local config file, a game save format) do not benefit from provenance
metadata. It becomes MUST in regulated domains or multi-actor systems
where audit is a compliance requirement.

**Violation signal:** An entity modified by an unknown actor at an unknown
time, discovered during an incident investigation.

---

## Part VI — Documentation and Generability

### Rule 27. Naming MUST be consistent, predictable, and greppable

Pick one convention and enforce it mechanically:

- `snake_case` vs. `camelCase` — one, not both.
- `_id` suffix for all foreign keys, or none.
- Boolean fields: `is_`/`has_` prefix, or bare adjectives — one, not both.
- Plural for arrays, singular for scalars.

A developer SHOULD be able to predict a field's name from its semantics
without consulting the schema.

**Bad:**
```yaml
# Mixed conventions in the same schema
provider_id: ...     # snake_case FK
slotId: ...          # camelCase FK
isEnabled: ...       # camelCase boolean with prefix
interactive: ...     # bare adjective boolean without prefix
targets: ...         # plural (good: it's an array)
focus: ...           # singular (bad: it's also an array)
```

**Good:**
```yaml
# Uniform snake_case, _id suffix for FKs, is_ prefix for booleans, plural arrays
provider_id: ...
slot_id: ...
is_enabled: ...
is_interactive: ...
targets: ...
focus_items: ...     # plural, matches array semantics
```

**Violation signal:** A developer misspelling a field name because the
convention was unpredictable.

---

### Rule 28. The schema MUST be self-describing enough to generate validators

A well-designed schema is mechanically transformable into: a JSON Schema
validator, a TypeScript type, a database DDL, and a validation function —
without human interpretation. Every `unknown` type, unresolved constant,
or prose-only constraint is a point where automated generation breaks.

This is the *generative test* for the entire standard: if a rule is followed,
the schema gets closer to full mechanical generability; if it's violated,
a human must intervene.

**Violation signal:** A code generator that requires manual overrides or
post-generation patches to produce correct output from the schema.

---

### Rule 29. Extension points MUST be intentional, not accidental

`config: Record<string, unknown>` is a deliberate escape hatch — it says
"this entity is extensible, and extensions are opaque to the core schema."
That's acceptable, if annotated:

**Good:**
```yaml
config:
  type: object
  additionalProperties: true
  x-extension-point: true
  description: "Provider-specific configuration. Schema varies by provider.kind."
```

A field typed `unknown` without the extension annotation is not an extension
point — it's an unfinished definition. The distinction MUST be explicit.

**Violation signal:** A field typed `unknown` or `any` that the original
author claims is "flexible" but that consumers treat as if it has a fixed
shape in practice.

---

### Rule 30. Access patterns SHOULD inform but not dictate structure

Denormalization, embedding, and indexing hints are legitimate at the physical
layer. But the logical schema SHOULD model the domain truthfully first. If
you find yourself flattening a relationship because "reads are faster," you're
conflating two layers.

Performance optimizations SHOULD be documented as annotations on the logical
schema (`x-denormalized-from`, `x-materialized-view`), not baked into the
logical structure itself.

**Violation signal:** A field that exists solely to avoid a JOIN, with no
annotation explaining that it's a denormalization of another entity's data.

---

### Rule 31. The schema MUST be readable as a standalone artifact

A reader SHOULD be able to understand the domain model from the schema alone,
without running the application, reading the source code, or asking the
original author. This means: entity names reflect domain language, field
names are self-documenting, relationships are labeled, and every non-obvious
design decision has a `note` or `description` that explains *why*, not just
*what*.

Every field with a non-trivial constraint, a custom format, or a
business-specific semantic SHOULD include a `description` and MAY include
an `example` value. Representative examples improve mock generation, contract
testing, and onboarding — but are advisory, not structural.

**Violation signal:** A new team member who reads the schema and must ask
the original author what a field means, what values are valid, or how two
entities relate.

---

## Review Scorecard

Use this scorecard to evaluate a schema against this standard. Each rule is
scored **Pass**, **Warn** (documented deviation), or **Fail** (unaddressed
violation). A schema is compliant if all MUST rules pass and all SHOULD rules
either pass or have documented rationale for deviation.

```
┌─────┬──────────────────────────────────────────┬──────────┬────────┐
│  #  │ Rule (short form)                        │ Tier     │ Score  │
├─────┼──────────────────────────────────────────┼──────────┼────────┤
│     │ PART I — TYPE SAFETY AND PRECISION       │          │        │
│  1  │ Unambiguous field types                  │ MUST     │ ______ │
│  2  │ Constraints in schema                    │ MUST     │ ______ │
│  3  │ Closed, versioned enums                  │ MUST     │ ______ │
│  4  │ Nullable ≠ optional ≠ absent             │ MUST     │ ______ │
│  5  │ Arrays: item type + cardinality + order  │ MUST     │ ______ │
│  6  │ Temporal precision and format            │ MUST     │ ______ │
│  7  │ Numeric units declared                   │ MUST     │ ______ │
│  8  │ Discriminated polymorphism               │ MUST     │ ______ │
│  9  │ Defaults declared in schema              │ SHOULD   │ ______ │
├─────┼──────────────────────────────────────────┼──────────┼────────┤
│     │ PART II — IDENTITY AND RELATIONSHIPS     │          │        │
│ 10  │ Stable, opaque identity                  │ MUST     │ ______ │
│ 11  │ Navigable relationships                  │ MUST     │ ______ │
│ 12  │ Explicit lifecycle ownership             │ MUST     │ ______ │
│ 13  │ FK targets declared                      │ MUST     │ ______ │
│ 14  │ Cyclic graph constraints                 │ MUST     │ ______ │
├─────┼──────────────────────────────────────────┼──────────┼────────┤
│     │ PART III — NORMALIZATION AND COHERENCE   │          │        │
│ 15  │ Single source of truth                   │ MUST     │ ______ │
│ 16  │ No bag-of-arrays entities                │ SHOULD   │ ______ │
│ 17  │ Cross-cutting types defined once         │ SHOULD   │ ______ │
│ 18  │ Computed vs. stored distinguished        │ SHOULD   │ ______ │
├─────┼──────────────────────────────────────────┼──────────┼────────┤
│     │ PART IV — EVOLUTION AND COMPATIBILITY    │          │        │
│ 19  │ Explicit, monotonic versioning           │ MUST     │ ______ │
│ 20  │ No duplicate-version entities            │ MUST     │ ______ │
│ 21  │ Breaking changes classified              │ MUST     │ ______ │
│ 22  │ Field deprecation annotated              │ MUST     │ ______ │
├─────┼──────────────────────────────────────────┼──────────┼────────┤
│     │ PART V — OPERATIONAL ANNOTATIONS         │          │        │
│ 23  │ Sensitive fields classified              │ MUST*    │ ______ │
│ 24  │ Identity/provenance immutability         │ SHOULD   │ ______ │
│ 25  │ Localization strategy declared           │ SHOULD   │ ______ │
│ 26  │ Multi-actor provenance metadata          │ SHOULD   │ ______ │
├─────┼──────────────────────────────────────────┼──────────┼────────┤
│     │ PART VI — DOCUMENTATION AND GENERABILITY │          │        │
│ 27  │ Consistent naming                        │ MUST     │ ______ │
│ 28  │ Mechanically generatable validators      │ MUST     │ ______ │
│ 29  │ Intentional extension points             │ MUST     │ ______ │
│ 30  │ Access patterns don't dictate structure  │ SHOULD   │ ______ │
│ 31  │ Readable as standalone artifact          │ MUST     │ ______ │
├─────┼──────────────────────────────────────────┼──────────┼────────┤
│     │ TOTALS                                   │          │        │
│     │ MUST Pass:  ___/20  (or ___/19 if no PII)│         │        │
│     │ SHOULD Pass or Documented: ___/11        │          │        │
└─────┴──────────────────────────────────────────┴──────────┴────────┘

* Rule 23 is MUST for PII-bearing schemas, MAY otherwise.
```

---

## Appendix A — Compatibility Classification Matrix

| Change Type                          | Backward | Forward | Breaking |
|--------------------------------------|----------|---------|----------|
| Add optional field                   | ✅       | ✅      |          |
| Add required field with default      | ✅       | ⚠️      |          |
| Add required field without default   |          |         | ❌       |
| Remove optional field                | ⚠️       | ✅      |          |
| Remove required field                |          |         | ❌       |
| Widen enum (add value)               | ✅       | ⚠️      |          |
| Narrow enum (remove value)           |          |         | ❌       |
| Relax constraint (widen range)       | ✅       | ⚠️      |          |
| Tighten constraint (narrow range)    |          |         | ❌       |
| Change field type                    |          |         | ❌       |
| Rename field                         |          |         | ❌       |
| Change default value                 | ⚠️       | ⚠️      |          |
| Add new entity                       | ✅       | ✅      |          |
| Remove entity                        |          |         | ❌       |
| Deprecate field (no removal)         | ✅       | ✅      |          |

**Legend:**
✅ = Safe. ⚠️ = Safe with caution (may affect some consumers). ❌ = Breaking.

**Policy:** Breaking changes MUST increment the major version. Non-breaking
changes SHOULD increment the minor version. Patch versions are reserved for
documentation, description, or annotation-only changes.

---

## Appendix B — External Grounding and References

This standard draws on established principles from the following sources.
Where a rule aligns with an external specification, the reference is noted
so the reader can verify independently.

| Rule(s) | Grounding Source | Reference |
|---------|-----------------|-----------|
| 1, 8, 28 | JSON Schema specification: type system, `oneOf`/`discriminator` | json-schema.org, draft 2020-12 §10.2 |
| 2, 5, 6 | JSON Schema validation keywords: `minimum`, `maximum`, `pattern`, `format`, `minItems` | json-schema.org, draft 2020-12 §6 |
| 3 | Protobuf style guide: enum design, reserved values | protobuf.dev/programming-guides/style |
| 4 | OpenAPI 3.1: `nullable` vs. `required` semantics | spec.openapis.org/oas/v3.1.0 §4.7.25 |
| 7 | ISO 4217 (currency codes), SI unit conventions | iso.org/iso-4217-currency-codes |
| 10 | UUID specification, ULID specification | RFC 4122, github.com/ulid/spec |
| 11–14 | Entity-relationship modeling: Chen notation, crow's foot | Chen, P. (1976). "The Entity-Relationship Model" |
| 15 | Database normalization: Codd's normal forms | Codd, E.F. (1970). "A Relational Model of Data for Large Shared Data Banks" |
| 19, 21 | Semantic versioning | semver.org/spec/v2.0.0 |
| 21 | Avro schema evolution / compatibility types | avro.apache.org/docs/current/spec.html §schema-resolution |
| 21 | Protobuf backward/forward compatibility rules | protobuf.dev/programming-guides/proto3 §updating |
| 23 | GDPR Article 25 (data protection by design), LGPD Art. 46 | gdpr-info.eu/art-25-gdpr |
| 25 | BCP 47 language tags | RFC 5646 |
| 27 | Google API design guide: naming conventions | cloud.google.com/apis/design/naming_convention |

**Note:** References are provided for verification, not as appeals to
authority. Each rule in this standard stands on its own rationale. If a
rule conflicts with a referenced source, the rule's stated rationale
governs within this standard's scope.

---

## Appendix C — Schema Language Mapping

This table maps key concepts from this standard to their expression in
common schema languages.

| Concept | JSON Schema | TypeScript/Zod | Protobuf | SQL DDL | Avro |
|---------|-------------|----------------|----------|---------|------|
| Unambiguous type (R1) | `type` keyword | Type literal | Message/scalar | Column type | Named type |
| Constraints (R2) | `minimum`, `pattern` | `.min()`, `.regex()` | Custom options | `CHECK` constraint | `logicalType` |
| Closed enum (R3) | `enum` keyword | `z.enum()` | `enum` | `ENUM` / `CHECK` | `enum` |
| Nullable (R4) | `type: [T, "null"]` | `T \| null` | `optional` + wrapper | `NULL` / `NOT NULL` | `["null", T]` |
| Array cardinality (R5) | `minItems`, `maxItems` | `.min()`, `.max()` | N/A (repeated) | N/A (app layer) | N/A |
| Temporal format (R6) | `format: "date-time"` | `z.string().datetime()` | `google.protobuf.Timestamp` | `TIMESTAMP WITH TIME ZONE` | `timestamp-millis` |
| Discriminator (R8) | `discriminator` + `oneOf` | `z.discriminatedUnion()` | `oneof` | Inheritance / type column | `union` |
| Default (R9) | `default` keyword | `.default()` | `default` value | `DEFAULT` clause | `default` |
| FK reference (R13) | `$ref` or `x-fk` | Custom branded type | N/A (app layer) | `REFERENCES` | N/A |
| Deprecation (R22) | `deprecated: true` | `.describe("DEPRECATED")` | `[deprecated = true]` | Comment convention | `@deprecated` |
| Sensitivity (R23) | `x-sensitivity` | Custom metadata | Custom options | Column comment | Custom `logicalType` |
| Immutability (R24) | `readOnly: true` | `readonly` modifier | N/A (app layer) | Trigger / policy | N/A |

---

*End of document.*
