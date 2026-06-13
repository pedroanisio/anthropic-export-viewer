# Plan Schema Field Reference

Quick reference for PlanSchema v0.3.0 JSON structure. The authoritative schema is `.repo/schemas/01KM18ZD23GC3TDVN7W0GX2000-plan-schema.ts`.

## Root Object

```
{
  schemaVersion: "0.3.0",
  metadata: PlanMetadata,
  problem: ProblemDefinition,
  baseline: BaselineState,
  resources: Resource[],
  scope: ScopeDefinition,
  actors: ActorRegistration[],
  concurrency: ConcurrencyModel,
  verificationEconomics?: VerificationEconomics,
  steps: PlanStep[],
  executionOrder: ExecutionOrder,
  risks: Risk[],
  decisions: Decision[],
  dataSyncRules: DataSyncRules,
  acceptanceCriteria: AcceptanceCriterion[],
  mergeStrategy: MergeStrategy,
  futureWork: FutureWorkItem[]
}
```

## PlanMetadata

| Field | Type | Required | Notes |
|---|---|---|---|
| planId | string | yes | Unique identifier |
| version | SemVer | yes | e.g. "1.0.0" |
| createdAt | ISO 8601 | yes | |
| updatedAt | ISO 8601 | yes | |
| authorId | ActorId | yes | |
| snapshotRef | GitSha | yes | Must match baseline.snapshotRef |
| branch | string | yes | |
| supersedes | PlanSupersedes[] | no | For plan replacement (NOT phases) |
| selfPath | string | yes | Path to this plan file |
| versionHistory | PlanVersionTransition[] | no | |

## ProblemDefinition

| Field | Type | Required |
|---|---|---|
| problemStatement | string | yes |
| affectedActors | string[] | yes (min 1) |
| successOutcome | string | yes |
| costOfInaction | string | no |

## BaselineState

| Field | Type | Required | Notes |
|---|---|---|---|
| snapshotRef | GitSha | yes | Must match metadata.snapshotRef |
| metrics | MetricThreshold[] | yes (min 1) | Each: name, baseline, floor, target?, unit |
| knownIssues | string[] | no | |
| invariants | string[] | no | |
| healthCommands | ShellCommand[] | yes (min 1) | |

## Resource

| Field | Type | Required |
|---|---|---|
| id | ResourceId | yes |
| path | string | yes |
| estimatedTokens | number | yes |
| kind | enum | yes |

Kinds: `source-file`, `config-file`, `sql-migration`, `test-file`, `documentation`, `infrastructure`, `external-service`

## ScopeDefinition

| Field | Type | Required |
|---|---|---|
| inScope | ScopeZone[] | yes (min 1) |
| nonScope | ScopeZone[] | no |
| nonScopeRationale | string | no |
| sharedSurfaces | array | no |

ScopeZone: `id`, `label`, `includes` (glob[]), `excludes` (glob[])

## ActorRegistration

| Field | Type | Required | Notes |
|---|---|---|---|
| id | ActorId | yes | |
| kind | enum | yes | `human`, `agent`, `sub-agent` |
| trustLevel | enum | yes | `operator`, `orchestrator`, `worker` |
| label | string | yes | |
| gitAuthor | string | yes | |
| authorizedZones | ScopeZoneId[] | yes (min 1) | Must cover all zones used by assigned steps |
| contextCapacity | number | no | Tokens |
| lifespan | discriminated union | no | `unbounded`, `session-bounded`, `task-bounded` |
| outputDivergence | 0-1 | no | |
| reproducibility | object | no | For AI actors |
| tacitKnowledge | string[] | no | |

## ConcurrencyModel

```
{
  mode: { mode: "sequential", executorId: ActorId }
       | { mode: "parallel", syncInterval, lockProtocol, conflictResolution },
  channels: CommunicationChannel[]
}
```

## VerificationEconomics

| Field | Type | Default |
|---|---|---|
| unit | enum | "checks-per-hour" |
| bwVerify | number | 10 |
| bwDecl | number | 3 |
| bwReview | number | 7 |
| bwEmitResidual | number | 5 |
| intentProjection | IntentConstraint[] | [] |

IntentConstraint: `id`, `name`, `temporalScope`, `modality`, `gradingKind`, `predicateRef`, `declarationCost`, `estimatedYield?`, `notes?`

TemporalScope variants: `all-steps`, `single-step` (stepId), `step-set` (stepIds[]), `phase` (fromStep, toStep), `recurring` (everyN)

## PlanStep

| Field | Type | Required | Notes |
|---|---|---|---|
| id | StepId | yes | |
| title | string | yes | |
| description | string | yes | |
| size | enum | yes | XS, S, M, L, XL |
| assignedTo | ActorId | yes | Must be registered |
| dependsOn | StepId[] | no | Must exist, no cycles |
| scopeZones | ScopeZoneId[] | yes (min 1) | Must be in actor's authorizedZones |
| fileChanges | FileChange[] | yes (min 1) | path, action, description |
| blastRadius | BlastRadiusEntry[] | no | path, impactDescription, dependencyKind |
| verification | VerificationCheck[] | yes (min 1) | name, command, passCriteria, blocking, verifiedBy |
| reversibility | discriminated union | yes | `reversible`, `irreversible`, `partially-reversible` |
| stopConditions | StopCondition[] | no | Required for M+ by protocol |
| handoffTemplate | HandoffState | no | Required at phase boundaries |
| resourceRequirements | object | no | Required for M+ by protocol |
| commitTemplate | string | no | |
| notes | string | no | |
| validationBudget | object | no | |

### Reversibility Variants

**reversible:** `rollbackProcedure`
**irreversible:** `reason`, `mitigation`, `requiredApprover` (must be operator, not self)
**partially-reversible:** `reversiblePart`, `irreversiblePart`, `rollbackProcedure`, `mitigation`, `requiredApprover`

### StopCondition

| Field | Type | Notes |
|---|---|---|
| trigger | string | What triggers the stop |
| action | enum | halt-and-escalate, retry-once, retry-with-backoff, skip-and-document, rollback-step, rollback-all |
| escalateTo | ActorId | optional |
| maxRetries | number | default 0 |
| blindSpotRisk | string | default "unknown" |
| redundantMonitors | ActorId[] | |

## Risk

| Field | Type | Required |
|---|---|---|
| id | RiskId | yes |
| description | string | yes |
| severity | enum | yes |
| likelihood | enum | yes |
| affectedSteps | StepId[] | yes (min 1) |
| mitigation | string | yes |
| fallback | string | no |
| ownerId | ActorId | yes |
| relatedConstraint | enum | no |

## Decision

| Field | Type | Required |
|---|---|---|
| id | DecisionId | yes |
| timestamp | ISO 8601 | yes |
| decidedBy | ActorId | yes |
| title | string | yes |
| chosen | string | yes |
| alternatives | array | no |
| reversible | boolean | yes |
| affectedSteps | StepId[] | no |

## ExecutionOrder

| Field | Type | Required |
|---|---|---|
| sequence | StepId[] | yes (min 1) |
| parallelizableGroups | StepId[][] | no (each min 2) |

## Other Sections

**DataSyncRules:** `syncRules` (sourceOfTruth, derivedArtifacts, regenerateCommand, trigger) + optional `migrationPolicy`

**AcceptanceCriterion:** `description`, `verificationCommand?`, `passCriteria`

**MergeStrategy:** `targetBranch`, `method` (merge-commit/squash/rebase/fast-forward), `requiredGates`, `approvers`

**FutureWorkItem:** `title`, `description`, `dependsOnDecisions`, `targetPhase?`

## Well-Formedness Checks (13 total)

1. Referential integrity (actors, steps, zones, risks, decisions, merge approvers, snapshotRef)
2. Scope containment — actor authorizedZones cover assigned step zones
3. DAG acyclicity — no cycles in step dependencies
4. Execution order completeness — all steps in sequence
5. Capacity feasibility — simultaneous resources fit actor context
6. Irreversibility gating — operator approval, no self-approval
7. Detection adequacy — not all self-verification
8. Intent projection adequacy — verificationEconomics present and valid
9. Version transition authorization — no self-authorize
10. Constraint debt — validation budget tracking
11. Handoff compression loss — cumulative loss warning >50%
12. Verification gap — emit >> verify on critical channels
13. Blast radius bounds — static lower bounds present
