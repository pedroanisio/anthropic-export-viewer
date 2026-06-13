---
name: mental-model
version: "1.0.0"
description: Build a structured mental model that captures baseline state, target state, gaps, assumptions, and open questions before generating a formal execution plan. Use this skill whenever the user asks to create, update, or regenerate a mental model, or when starting L/XL tasks, encountering scope-ambiguous language ("completion," "finish," "everything"), referencing existing plans, or working with codebases that have more than 20 files in affected scope zones. Also trigger when the user says "mental model", "pre-plan checkpoint", "scope analysis", or "understand the codebase before planning".
allowed-tools: Bash Read Write Glob Grep
effort: high
metadata:
  ulid: 01KM188YV2CJ26QH6KNH2NWG1Z
---

# Mental Model

Build a reviewable mental model before committing to a formal plan. The mental model makes your understanding of scope, entities, and assumptions explicit so the human can verify it at 1/10th the cost of reviewing a full plan.

The mental model is a verification checkpoint, not a plan. It creates shared state between you and the human. Do NOT generate a plan alongside it.

## When to Produce

**MANDATORY** when ANY of these hold:
- Task complexity is L or XL
- The request references an existing plan or architecture document
- The request uses scope-ambiguous language ("completion," "finish," "everything," "move forward")
- The codebase has more than 20 files in the affected scope zones
- The estimated plan would exceed 400 lines

**SKIP** when:
- Task complexity is XS or S with unambiguous scope
- The user provided a confirmed, itemized scope
- Single-step change (bug fix, config update)

When in doubt, produce the model. It costs 80-200 lines. A wrong plan costs 800-1500 lines.

## Workflow

### Step 1: Inspect the Codebase

Before reading any reference documents, inventory the codebase. The codebase is the source of truth; reference documents are consulted second.

```bash
# What exists?
.repo/scripts/treemeta.sh -g -l -e ts,tsx --limit 100 ./src

# How big is it?
.repo/scripts/treemeta.sh -g --count ./src

# Test state
npm test -- --coverage 2>&1 | tail -10
# or: cargo test 2>&1 | tail -20

# Git state
git rev-parse --short HEAD
```

This builds the `baseline` section.

### Step 2: Read Reference Documents

If the user pointed to reference documents (old plans, architecture docs, appendices), read them now. For each entity or claim:

- **Exists in codebase** -> `entities.verified` (include file path or command)
- **Not in codebase, but the plan will create it** -> `entities.confirmedAbsent` (it's a deliverable)
- **Not in codebase, status unclear** -> `entities.unverified` (hallucination risk zone)

Reference documents always have `trustLevel: "reference"`, never `"codebase"`. A previous plan is a previous agent's output. An architecture doc is a human's intent. Neither is current reality.

### Step 3: Formulate the Target State

Write the target state as one sentence. Then classify its derivation:

| Source | derivation value | Action |
|---|---|---|
| User stated it directly | `"user-explicit"` | None |
| Inferred from reference doc | `"inferred-from-reference"` | Write `derivationRationale` |
| Inferred from codebase gaps | `"inferred-from-codebase"` | Write `derivationRationale` |
| Multiple sources | `"composite"` | Write `derivationRationale` |

If the derivation is not user-explicit, this is the #1 thing the human needs to verify. Make `derivationRationale` clear and specific.

### Step 4: Identify the Delta

Delta = target state - baseline state. Organize into work streams where each is a coherent unit delivering a specific capability.

**Work stream sizing guide:**

| Size | Expected plan steps | Lines per step |
|---|---|---|
| XS | 1 | ~30 |
| S | 1-2 | ~40 |
| M | 2-4 | ~60 |
| L | 4-8 | ~60 |
| XL | 8-16 | ~60 |

### Step 5: Partition Entities

For every domain entity the plan will reference:

1. **Confirmed from codebase?** -> `verified` (include file path or command)
2. **In reference doc but not found in codebase?** -> `unverified`
3. **Looked for it, confirmed NOT there?** -> `confirmedAbsent`

The `unverified` list is the human review hotspot. Every item is either confirmed (-> verified), denied (-> removed), or identified as a deliverable (-> confirmedAbsent).

### Step 6: Surface Assumptions and Questions

Be explicit about uncertainty:

- **Assumption:** "I believe X because Y" -> add to `assumptions` with confidence level
- **Question:** "I can't determine X, and the answer changes the plan" -> add to `openQuestions` with options
- **Decision:** "X requires human authority (vendor cost, irreversible architecture)" -> add to `openDecisions`

The mental model is allowed to be incomplete. Open questions and unverified entities are features, not bugs.

### Step 7: Propose Phases (if needed)

Estimate total plan size: `sum(work_stream_steps * 60) + 200`.

If > 800 lines, propose phases. Each phase should be:
- A complete PlanSchema instance (not partial)
- Independently executable (given dependencies)
- Small enough for a single plan generation pass

## Output

Generate valid JSON conforming to `_specs/schemas/mental-model-schema.ts`. Read `references/schema-overview.md` for the field reference.

Key fields: `schemaVersion: "0.1.0"`, `identity`, `baseline`, `targetState`, `delta`, `entities`, `assumptions`, `openQuestions`, `openDecisions`, `constraints`, `proposedPhases` (optional), `overallConfidence`, `reviewNotes` (optional).

### Storage

```bash
TIMESTAMP=$(date -Ins)
SKILLID="01KM188YV2CJ26QH6KNH2NWG1Z"
FILEPATH=".repo/storage/${SKILLID}/mental-model.${TIMESTAMP}.json"
mkdir -p .repo/storage/${SKILLID}
# Write JSON to $FILEPATH (no code fences, valid JSON only)
ln -sf "mental-model.${TIMESTAMP}.json" .repo/storage/${SKILLID}/mental-model.latest.json
```

The symlink `mental-model.latest.json` always points to the most recent model and is consumed by downstream prompts (e.g., plan generation).

## Present for Review

The human needs to review this in under 5 minutes. The JSON is the authoritative artifact, but add a brief prose summary highlighting:

1. **Target state** - is this what you want?
2. **Unverified entities** - do these exist?
3. **Open questions** - I need answers to proceed
4. **Open decisions** - these need your authority
5. **Proposed phases** - does this splitting make sense?

Do NOT generate a plan yet. Wait for human confirmation.

## Incorporate Feedback

| Human response | Action |
|---|---|
| "Looks good, proceed" | All open items implicitly resolved; proceed to plan generation |
| Specific corrections | Update model, re-validate, surface new questions if any |
| "Wrong scope" / redirect | Rebuild the model with corrected scope |
| Partial confirmation | Generate plan for confirmed phase(s) only |

## Readiness Gate

A mental model reaches `"ready-for-plan"` only when:
- No open questions remain
- No open decisions remain
- No unverified entities exist
- Overall confidence is `"high"`

This is intentionally strict. Resolution happens BEFORE plan generation, not during.

## Mapping to Plan Generation

Once confirmed, map the mental model to PlanSchema:

| Mental model field | PlanSchema field |
|---|---|
| `baseline.snapshot` | `metadata.snapshotRef`, `baseline.snapshotRef` |
| `baseline.metrics` | `baseline.metrics` |
| `baseline.knownIssues` | `baseline.knownIssues` |
| `targetState.successCriteria` | `acceptanceCriteria` |
| `targetState.definition` | `problem.successOutcome` |
| `delta.workStreams` | `steps` (expand each into concrete steps) |
| `entities.verified` | `resources` |
| `assumptions` (confirmed) | `decisions` |
| `constraints` | `verificationEconomics.intentProjection` |
| `proposedPhases` | Separate PlanSchema instances |

Then follow `_specs/ai-agents/plan-generation.md` sections 2-3 for actual generation.

## Anti-Patterns

| Anti-pattern | Correct approach |
|---|---|
| Skipping for L/XL tasks | Always produce for L/XL |
| Generating plan alongside model | Present model, wait, then generate |
| Listing entities as "verified" without evidence | Include treemeta/grep command or file path |
| Empty openQuestions when scope is ambiguous | Surface every uncertainty with options |
| Treating reference docs as trustLevel "codebase" | Reference docs are always "reference" |
| Model exceeding 300 lines | Compress; large scope needs phasing |

## Full Specification Reference

For exact formatting rules, before/after examples, or edge cases not covered above,
read `.repo/references/01KM17JDVNJ333TN3R5BGZB5QS-tsdoc-spec.md`. Key sections: