# Mental Model Schema Overview

Quick reference for the mental model JSON structure. The authoritative schema is `_specs/schemas/mental-model-schema.ts`.

## Root Object

```
{
  schemaVersion: "0.1.0",
  identity: ModelIdentity,
  baseline: BaselineState,
  targetState: TargetState,
  delta: Delta,
  entities: EntityInventory,
  assumptions: Assumption[],
  openQuestions: OpenQuestion[],
  openDecisions: OpenDecision[],
  constraints: Constraint[],
  proposedPhases?: ProposedPhase[],
  overallConfidence: "high" | "medium" | "low",
  reviewNotes?: string
}
```

## Identity

| Field | Type | Description |
|---|---|---|
| modelId | string | Unique identifier |
| createdAt | ISO 8601 datetime | When this model was created |
| authorId | string | Who/what created it |
| taskDescription | string | The original request |
| sourcesConsulted | array | Documents inspected, each with `path`, `description`, `trustLevel` ("codebase" / "reference" / "user-provided") |

## Baseline State

| Field | Type | Description |
|---|---|---|
| snapshot | string | Git SHA (7-40 hex chars) |
| metrics | array | Each: `name`, `value` (number), `unit`, `measuredBy` |
| summary | string | Prose summary of what exists |
| existingCapabilities | string[] | Working capabilities (min 1) |
| knownIssues | string[] | Current problems |

## Target State

| Field | Type | Description |
|---|---|---|
| definition | string | One-sentence end state |
| successCriteria | string[] | Measurable "done" criteria (min 1) |
| derivation | enum | "user-explicit" / "inferred-from-reference" / "inferred-from-codebase" / "composite" |
| derivationRationale | string? | Required when derivation is not "user-explicit" |

## Delta

| Field | Type | Description |
|---|---|---|
| summary | string | High-level gap description |
| workStreams | WorkStream[] | Units of work (min 1) |
| excludedFromScope | array | Items excluded with `item` and `reason` |

### WorkStream

| Field | Type | Description |
|---|---|---|
| id | string | Unique identifier |
| title | string | Work stream name |
| deliverable | string | Concrete output |
| estimatedSize | enum | "XS" / "S" / "M" / "L" / "XL" |
| dependsOn | string[] | IDs of prerequisite work streams |
| touchesAreas | string[] | Files/modules affected |
| rationale | string? | Why this is needed |

## Entity Inventory

### verified
Each: `name`, `kind` (adapter/service/file/etc.), `verifiedFrom` (file path or command)

### unverified
Each: `name`, `kind`, `source` (where learned about it), `impactIfMissing`

### confirmedAbsent
Each: `name`, `kind`, `expectedLocation`, `checkedVia` (command or path)

## Assumption

| Field | Type | Description |
|---|---|---|
| id | string | Unique identifier |
| statement | string | What you believe |
| ifWrong | string | What goes wrong |
| confidence | enum | "high" / "medium" / "low" |
| verificationHint | string? | How to verify |

## Open Question

| Field | Type | Description |
|---|---|---|
| id | string | Unique identifier |
| question | string | What you need to know |
| context | string | Why you can't answer it |
| options | array | Min 2 options, each with `answer` and `implication` |
| blocksWorkStreams | string[] | Which work streams are blocked |
| agentRecommendation | string? | Your recommended answer |

## Open Decision

| Field | Type | Description |
|---|---|---|
| id | string | Unique identifier |
| title | string | Decision title |
| reason | enum | "external-vendor-cost" / "irreversible-architecture" / "infrastructure-commitment" / "scope-expansion" / "security-implications" / "other" |
| options | array | Min 2 options, each with `option` and `tradeoff` |
| affectsWorkStreams | string[] | Which work streams are affected |
| agentRecommendation | string? | Your recommendation |

## Constraint

| Field | Type | Description |
|---|---|---|
| id | string | Unique identifier |
| description | string | What must hold |
| verificationCommand | string? | How to check it |
| kind | enum | "invariant" (every step) / "milestone" (specific point) |

## Proposed Phase

| Field | Type | Description |
|---|---|---|
| phaseId | string | Unique identifier |
| title | string | Phase name |
| description | string | What this phase covers |
| workStreamIds | string[] | Which work streams belong here (min 1) |
| dependsOnPhases | string[] | Prerequisite phase IDs |
| estimatedPlanLines | number? | Size estimate |

## Validation Rules

A mental model is `"ready-for-plan"` only when:
- No structural errors (work stream DAG is acyclic, all references resolve)
- No open questions
- No open decisions
- No unverified entities
- Overall confidence is "high"

Otherwise it is `"needs-human-input"` or `"needs-investigation"`.
