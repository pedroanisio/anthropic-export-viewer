---
name: adv-planning
version: "1.0.0"
description: Generate formal, schema-compliant execution plans (JSON) from a confirmed mental model. Use this skill when the user asks to create a plan, generate an execution plan, turn a mental model into a plan, or produce a formal plan for M/L/XL tasks. Also trigger when the user says "create adv-plan", "generate adv-plan from mental model", "formal adv-plan", "adv-plan generation", "execution adv-plan". This skill produces structured PlanSchema JSON — not informal markdown plans. If you need an informal markdown plan, use the format-plan prompt instead.
allowed-tools: Bash Read Write Glob Grep
effort: max
metadata:
  ulid: 01KM18ZD23GC3TDVN7W0GX2000
---

# Advanced Plan Generation

Generate schema-compliant execution plans (PlanSchema v0.3.0 JSON) from a confirmed mental model. This skill implements the plan generation protocol — the bridge between a reviewed mental model and an actionable, machine-validated plan.

**Announce at start:** "I'm using the adv-planning skill to generate a formal execution plan."

## Prerequisites

Before generating a plan, verify:

1. **Mental model exists** — load from `.repo/storage/01KM188YV2CJ26QH6KNH2NWG1Z/mental-model.latest.json`
2. **Mental model is current** — check `identity.createdAt` and `baseline.snapshot` against current `git rev-parse --short HEAD`
3. **Mental model is confirmed** — readiness should be `"ready-for-plan"` (no open questions, no open decisions, no unverified entities, confidence is "high")

If the mental model is stale or missing, tell the user: "The mental model needs to be created/updated first. Should I run the mental-model skill?"

If readiness is `"needs-human-input"`, present the unresolved items and wait.

## Phase 1: Pre-Generation

### 1.0 Resolve Scope

If the request uses scope-ambiguous language ("completion," "finish," "everything"), STOP and present scope options to the user. Do not pick one silently.

For tasks referencing existing plans: the previous plan's scope is not automatically the new plan's scope. Ask: "Should this plan cover the same scope, a subset, or the remaining work?"

### 1.1 Load the Schema

Read `.repo/schemas/01KM18ZD23GC3TDVN7W0GX2000-plan-schema.ts` into context. At minimum, load:
- All field names and types for `PlanSchema`, `PlanStep`, `ActorRegistration`
- All discriminated unions (`TemporalScope`, `ActorLifespan`, `Reversibility`)
- The `validateWellFormedness()` function's 13 checks

Read `.repo/references/01KM18ZD23GC3TDVN7W0GX2000-plan-schema-fields.md` for a quick field reference.

### 1.2 Gather Domain Inputs

Use `treemeta.sh` to verify what exists:

```bash
# Full inventory
.repo/scripts/treemeta.sh -g -l -e ts,tsx --limit 100 ./src

# Count by extension
.repo/scripts/treemeta.sh -g --count -e ts,tsx ./src

# Recently modified
.repo/scripts/treemeta.sh -g -l --sort modified -o desc --limit 30 ./src
```

**Confidence gate (HARD RULE):** If the plan requires enumerating more than 5 domain-specific entities that you cannot verify from the codebase or context:
1. STOP plan generation
2. List what you know vs. what you're uncertain about
3. ASK the user to supply or confirm the list
4. RESUME only after receiving verified input

This gate applies continuously — not just at the start. If during step filling you reference unverified domain entities, STOP and verify.

### 1.3 Resolve Decisions

For each technology/vendor/architecture choice the plan depends on:

| Situation | Action |
|---|---|
| Prior ADR exists | Cite in `decisions` array |
| Codebase already uses it | Record as existing constraint |
| Neither | Decision is open — set `decidedBy` to human OR add `stopCondition` |

**Authority rule:** Decisions involving external vendors, recurring costs, infrastructure commitments, or irreversible architecture MUST have `decidedBy` set to a human actor.

### 1.4 Estimate Output Size

```
estimated_lines = (step_count × 60) + 200
```

| Estimated lines | Strategy |
|---|---|
| ≤ 400 | Single-pass generation |
| 401-800 | Single-pass with compression |
| > 800 | Multi-pass generation (skeleton first) |

## Phase 2: Generation

### 2.1 Skeleton First (HARD RULE for >400 lines)

**Pass 1 — Skeleton:** Generate everything except step details:
- `metadata` (complete) — `schemaVersion: "0.3.0"`
- `problem` (complete)
- `baseline` (complete) — map from mental model's `baseline`
- `resources` (complete) — map from mental model's `entities.verified`
- `scope` (complete)
- `actors` (complete)
- `concurrency` (complete)
- `verificationEconomics` (complete — see defaults below)
- `steps` — IDs, titles, sizes, dependsOn, scopeZones ONLY
- `executionOrder` (complete)
- `risks` (complete)
- `decisions` (complete)
- `acceptanceCriteria` (complete) — from mental model's `targetState.successCriteria`
- `mergeStrategy` (complete)
- `futureWork` (complete)

**Validate the skeleton** before proceeding.

**Pass 2 — Fill:** Step details in dependency order:
- `fileChanges`
- `verification`
- `blastRadius`
- `reversibility`
- `stopConditions` (required for M+ steps)
- `resourceRequirements` (required for M+ steps)
- `handoffTemplate` (at phase boundaries for session-bounded agents)
- `commitTemplate`
- `validationBudget`

### 2.2 Verification Economics Defaults

Use these unless the user provides project-specific values:

| Field | Default | Meaning |
|---|---|---|
| `unit` | `"checks-per-hour"` | — |
| `bwVerify` | 10 | Total verification actions/hr |
| `bwDecl` | 3 | Constraint declaration actions/hr |
| `bwReview` | 7 | Output review actions/hr |
| `bwEmitResidual` | 5 | Agent output needing human review/hr |

Constraints: `bwDecl + bwReview ≤ bwVerify` and `bwEmitResidual ≤ bwReview`.

For intent projections, populate:
- `temporalScope`: `all-steps` for invariants, `single-step` for milestones
- `modality`: choose from `mathematical | structural | visual | textual | hybrid`
- `gradingKind`: `boolean` for pass/fail, `graded` for thresholds
- `predicateRef`: an executable command or verifiable assertion
- `declarationCost`: nonzero estimate (default 1)

### 2.3 File Enumeration Policy for XL Steps

| Content type | Enumerate? |
|---|---|
| Source files (deliverables) | YES — list every one |
| Shared/modified files | YES — list every one |
| Test files | 2-3 examples + pattern note |
| Fixture/data files | 1-2 examples + pattern note |

### 2.4 Conditional Field Requirements

| Condition | Required field |
|---|---|
| Step size M+ | `stopConditions` (min 1) |
| Step size M+ | `resourceRequirements.simultaneousResources` |
| Session-bounded agents | `handoffTemplate` at phase boundaries |
| Step size L+ | At least 1 `verification` with `verifiedBy: "human"` |
| Irreversible mutations | `reversibility.kind: "irreversible"` with operator approval |

### 2.5 Mental Model to Plan Mapping

| Mental model field | PlanSchema field |
|---|---|
| `baseline.snapshot` | `metadata.snapshotRef`, `baseline.snapshotRef` |
| `baseline.metrics` | `baseline.metrics` (add `floor` values) |
| `baseline.knownIssues` | `baseline.knownIssues` |
| `baseline.existingCapabilities` | Inform `problem.problemStatement` context |
| `targetState.successCriteria` | `acceptanceCriteria` |
| `targetState.definition` | `problem.successOutcome` |
| `delta.workStreams` | `steps` (expand each into concrete steps) |
| `delta.excludedFromScope` | `scope.nonScope` + `scope.nonScopeRationale` |
| `entities.verified` | `resources` |
| `assumptions` (confirmed) | `decisions` |
| `constraints` | `verificationEconomics.intentProjection` |
| `proposedPhases` | Separate PlanSchema instances per phase |

## Phase 3: Validation

### 3.1 Structural Self-Check

Before outputting, verify:
- [ ] All step IDs in `executionOrder.sequence` exist in `steps`
- [ ] All `dependsOn` targets exist as step IDs
- [ ] All `assignedTo` values reference registered actors
- [ ] All `scopeZones` reference declared scope zones
- [ ] Actor authorized zones contain all zones referenced by their assigned steps
- [ ] `bwDecl + bwReview ≤ bwVerify`
- [ ] `bwEmitResidual ≤ bwReview`
- [ ] No cycles in dependency graph
- [ ] `metadata.snapshotRef == baseline.snapshotRef`
- [ ] Parallelizable groups contain no intra-group dependencies

### 3.2 Semantic Self-Check

- [ ] Step size matches fileChanges count (XS=1, S=2-3, M=4-8, L=10-20, XL=20+)
- [ ] Every L/XL step has at least one `verifiedBy: "human"` check
- [ ] No agent self-authorizing vendor/cost decisions without stopCondition
- [ ] No step references unverified domain entities
- [ ] M+ steps have stopConditions and resourceRequirements
- [ ] Session-bounded plans have handoffTemplates at phase boundaries

### 3.3 When Validation Fails

- **Structural failure:** Fix before emitting. These are blocking.
- **Semantic failure:** Fix, flag as risk, or stop and ask user.

NEVER emit a plan that fails structural self-check.

## Output

Generate valid JSON (no code fences) conforming to `.repo/schemas/01KM18ZD23GC3TDVN7W0GX2000-plan-schema.ts` with `schemaVersion: "0.3.0"`.

**Storage:** Save the plan JSON to a location the user specifies. If no location specified, use `.repo/storage/01KM18ZD23GC3TDVN7W0GX2000/`.

## Multi-Phase Plans

When the mental model has `proposedPhases`, generate each phase as a separate PlanSchema instance:
- Number sequentially: `plan-phase-1.json`, `plan-phase-2.json`
- Each phase's `metadata.description` states phase index and total count
- Earlier phase's final step includes `handoffTemplate` for next phase
- Do NOT use `metadata.supersedes` — phases depend on each other, they don't replace each other

## Anti-Patterns

| Anti-pattern | Correct approach |
|---|---|
| Full plan in one pass without estimation | Estimate size first, multi-pass if needed |
| >400-line plan without skeleton validation | Skeleton first, validate, then fill |
| Inventing domain entity names | Stop and ask when unverified |
| Agent self-authorizing vendor decisions | Set decidedBy to human or add stopCondition |
| 100% automated verification on all steps | Add human verification for L/XL steps |
| Empty stopConditions on M+ steps | Populate; `blindSpotRisk: "unknown"` is OK |
| No handoffTemplate for session-bounded agents | Add at phase boundaries |
| XL step with every test file listed | List source files; describe test pattern |
| Uncalibrated verification economics | Use default table or justify custom values |
