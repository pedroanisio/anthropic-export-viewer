# Assessment Procedures Reference

This file contains the detailed methodology for conducting a PALS
assessment against different target types. Read the target-specific
section that matches the artifact under review.

---

## Table of Contents

1. Universal procedure (all targets)
2. API and tool interface assessment
3. Codebase assessment
4. Agentic pipeline and workflow assessment
5. System / component architecture assessment
6. Severity classification
7. Report template
8. Checklist template

---

## 1. Universal Procedure (All Targets)

Every PALS assessment follows this sequence regardless of target type:

### Step 1 — Identify LLM interaction surfaces

Map every point where LLM output enters the system. An "interaction
surface" is any location where model-generated content is consumed —
as code, data, configuration, API call, parameter, decision, natural
language, or structured output.

For each surface, record:
- **Surface ID** (S1, S2, …)
- **Location** (file, function, endpoint, pipeline step)
- **Input to model** (what prompt or context is provided)
- **Output from model** (what the model produces)
- **Downstream consumer** (what system, function, or user receives it)
- **Side effects** (writes, mutations, external calls, state changes)

If the target does not interact with LLMs at all, the PALS assessment
still applies to any point where the system *could* be consumed by an
LLM agent — i.e., assess the target as a tool surface.

### Step 2 — Classify each surface by error exposure

For each interaction surface, determine which of the 9 error classes
are relevant. Not every class applies to every surface.

Decision rules:
- Surface produces factual claims → ERR_HALLUCINATION is relevant.
- Surface must follow a specification → ERR_OMISSION, ERR_INSTRUCTION.
- Surface produces structured output → ERR_SCHEMA.
- Surface involves multi-step reasoning → ERR_REASONING.
- Surface has token budget constraints → ERR_TRUNCATION.
- Surface interacts with user preferences → ERR_SYCOPHANCY.
- Surface expresses confidence levels → ERR_CALIBRATION.
- Surface paraphrases or summarizes → ERR_SEMANTIC.

Record the relevant error classes per surface in a coverage matrix.

### Step 3 — Map existing verification boundaries

For each surface, identify what verification currently exists:
- Schema validation (JSON Schema, Zod, protobuf, type checks)?
- Output length / completeness checks?
- Factual grounding (RAG retrieval, source comparison)?
- Constraint enforcement (instruction compliance checking)?
- Consistency checks (adversarial rephrasing, cross-validation)?
- Human review gates?
- Retry / fallback logic?
- Logging / audit trail?

Map each existing verifier to the error classes it covers. Be honest:
a JSON Schema validator covers ERR_SCHEMA and nothing else. A human
review gate may partially cover several classes but at unknown depth.

### Step 4 — Apply architectural corollaries

Evaluate the system against each of the 5 corollaries:

**Corollary 1 (Appearance ≠ correctness):**
Does the system rely on test-time inspection as proof of correctness?
Are there production verification layers distinct from development
testing?

**Corollary 2 (Trust accumulation):**
Does the system relax verification after observing good outputs? Are
there adaptive trust mechanisms that reduce checking over time? These
are defects.

**Corollary 3 (Scope must match taxonomy):**
Do the verification claims match the actual coverage? Is verification
scoped and documented, or globally asserted without evidence?

**Corollary 4 (Silent acceptance):**
Are there paths where LLM output reaches downstream consumers with no
declared verification boundary? Every such path is an architectural
defect regardless of observed quality.

**Corollary 5 (Capability-detection asymmetry):**
If the system upgrades to a more capable model, do the verification
layers also upgrade? Is the verifier treated as a stable component
while the model is treated as a variable one?

### Step 5 — Pipeline compounding analysis

If the system chains multiple LLM calls, analyze the pipeline:
- How many sequential LLM-dependent steps exist?
- What verification exists between steps?
- Can an error in step i corrupt the context for step i+1 (cascade)?
- Can a downstream verifier catch errors introduced upstream (masking)?
- Can errors amplify through the pipeline (amplification)?

The product formula (P(error-free) = ∏(1 − pᵢ)) is a lower-bound
motivator, not a deployable model. But the directional claim holds:
longer pipelines without per-step verification have failure probability
approaching 1.

### Step 6 — Produce findings

Each finding has:
- **Finding ID** (F1, F2, …)
- **Surface(s) affected** (S1, S3, …)
- **Error class(es)** (ERR_HALLUCINATION, ERR_SCHEMA, …)
- **Corollary violated** (if applicable)
- **Description** (what the defect is)
- **Severity** (critical / high / medium / low — see §6)
- **Recommendation** (specific, actionable mitigation)

---

## 2. API and Tool Interface Assessment

When the target is an API that will be consumed by LLM agents or that
itself consumes LLM output, assess these additional dimensions:

### As a tool surface (API consumed by agents)

- **Schema completeness**: Can every request and response be validated
  mechanically against an explicit schema? Prose-only documentation is
  insufficient for agent consumers.
- **Error classification**: Does the API distinguish validation, auth,
  conflict, transient, and internal failures in machine-readable form?
  Or must the consumer interpret prose error messages?
- **Idempotency**: Are mutating operations replay-safe? Do they support
  idempotency keys or equivalent mechanisms?
- **Observable commit state**: Can the caller determine whether a write
  was proposed, accepted, committed, rejected, or partially applied?
- **Destructive action boundaries**: Are high-impact operations bounded
  by confirmation, narrow scope, or reversible workflow design?
- **Stable identifiers and pagination**: Does the API expose stable IDs
  and deterministic pagination sufficient for post-call verification?

### As an LLM-consuming service (API that uses LLM internally)

- Map every internal LLM call as an interaction surface (Step 1).
- Assess whether LLM-generated content leaks into API responses without
  verification.
- Check whether error responses generated by LLMs are passed through
  without structural validation.

---

## 3. Codebase Assessment

When the target is a codebase that interacts with LLMs:

### LLM call sites

- Identify every function, method, or module that invokes an LLM API
  (direct HTTP calls, SDK usage, framework abstractions).
- For each call site, trace the output path: where does the response
  go? Is it validated before use?
- Check for the contract block pattern: does the call site declare
  which error classes its verifier covers?

### Generated code paths

- If the system uses LLM-generated code (Copilot suggestions, code
  generation pipelines), assess:
  - Is generated code reviewed before execution?
  - Is generated code tested against specifications?
  - Are there sandbox / isolation boundaries?
  - Is the generation → acceptance path logged?

### Prompt construction

- Are prompts constructed from user input without sanitization?
  (prompt injection surface — extrinsic, but note it)
- Are prompts version-controlled and reviewed?
- Do prompts include explicit output format specifications that
  enable downstream schema validation?

### Dependency on LLM correctness

- Identify decision points where LLM output determines control flow
  (if/else branches, routing decisions, tool selection).
- Each such point is a high-severity interaction surface because
  errors affect not just data but system behavior.

---

## 4. Agentic Pipeline and Workflow Assessment

When the target is a multi-step agent, tool-using assistant, or
automated workflow:

### Step-level analysis

For each step in the pipeline:
- What is the LLM asked to do? (plan, execute, evaluate, summarize)
- What verification exists before the next step consumes this output?
- Can this step's errors cascade into subsequent steps?
- Is this step's output logged for post-hoc audit?

### Tool-call verification

- When the agent selects and invokes tools, is the selection verified?
- Are tool call parameters validated against the tool's schema before
  execution?
- Are tool results verified before being fed back to the model?
- For destructive tools (write, delete, send), is confirmation required?

### Planning and decomposition

- If the agent decomposes tasks into sub-tasks, is the decomposition
  verified against the original task specification?
- Can the agent create sub-tasks that exceed its authorization scope?
- Is there a mechanism to detect when the agent is pursuing a goal
  that diverges from the user's intent?

### State management

- Does the pipeline maintain observable state between steps?
- Can an external system inspect the pipeline's current state,
  determine which steps have completed, and identify where failures
  occurred?
- Is there a mechanism to resume from a known-good state after failure?

### Correlation patterns

Identify which of these patterns apply:
- **Cascade**: error in step i corrupts context for step i+1 (most
  common — fabricated IDs, wrong tool selection, hallucinated state).
- **Masking**: downstream verifier catches upstream error (desirable
  but must be explicitly designed).
- **Amplification**: error in step i causes step i+1 to produce a
  larger or more consequential error (e.g., wrong analysis → wrong
  decision → wrong action).

---

## 5. System / Component Architecture Assessment

When the target is a system architecture, infrastructure design, or
component integration:

### LLM integration architecture

- Where in the system architecture do LLMs sit?
- Are LLM services isolated behind service boundaries with explicit
  contracts?
- Do downstream services treat LLM service responses as trusted or
  untrusted?

### Verification layer architecture

- Is verification implemented as a cross-cutting concern or ad-hoc
  per-call-site?
- Is the verification layer independently deployable and upgradeable?
- Does the verification layer have its own observability (metrics,
  logging, alerting)?

### Model upgrade path

- When the LLM is upgraded, what changes in the verification layer?
- Is there a process for re-validating verification coverage against
  new model capabilities?
- Are there canary or shadow deployments that compare old-model and
  new-model outputs before full rollover?

### Failure mode analysis

- What happens when the LLM service is unavailable? (fallback behavior)
- What happens when the LLM produces output that fails verification?
  (retry, escalate, degrade gracefully, hard-fail)
- What happens when verification itself fails or times out?

---

## 6. Severity Classification

| Severity | Criteria |
|----------|---------|
| **Critical** | LLM output reaches a side-effect-producing system (write, send, delete, pay, deploy) with no verification boundary. Corollary 4 violation on a destructive path. |
| **High** | Verification exists but does not cover the relevant error classes for the surface. Corollary 3 violation. Or: pipeline has ≥ 3 unverified sequential LLM steps. |
| **Medium** | Verification covers the primary error classes but has known gaps in secondary classes. Or: trust accumulation pattern detected (Corollary 2). Or: model upgrade path does not include verifier upgrade (Corollary 5). |
| **Low** | Verification is present and scoped but could be made more precise or better documented. Or: contract block / verification scope documentation is missing but actual verification code exists. |

---

## 7. Report Template

```markdown
---
disclaimer: >
  No information within this document should be taken for granted.
  Any statement or premise not backed by a real logical definition or
  verifiable reference may be invalid, erroneous, or a hallucination.
title: "PALS Assessment: [Target Name]"
date: [current date]
method: pals-assessment/v1
framework: PALS's Law v1.5.4
framework_author: Pedro Anisio de Luna e Silva
---

# PALS Assessment: [Target Name]

## 1. Executive Summary
[2–4 sentences: what was assessed, critical finding count, overall
 verification posture.]

## 2. Target Description
[What the target is, its purpose, its LLM interaction model.]

## 3. LLM Interaction Surface Map
[Table: Surface ID | Location | Input | Output | Consumer | Side Effects]

## 4. Error Class Exposure Matrix
[Table: Surface ID | Each error class column | Verification status]
Use ✓ (covered), ✗ (exposed, not covered), — (not applicable).

## 5. Architectural Corollary Assessment
### 5.1 Corollary 1 — Appearance ≠ correctness
### 5.2 Corollary 2 — Trust accumulation
### 5.3 Corollary 3 — Verification scope
### 5.4 Corollary 4 — Silent acceptance
### 5.5 Corollary 5 — Capability-detection asymmetry

## 6. Pipeline Analysis
[If applicable: step count, inter-step verification, correlation
 patterns, compounding risk.]

## 7. Findings
[Each finding: ID, surface, error class, corollary, description,
 severity, recommendation.]

## 8. Verification Coverage Summary
[Contract block showing which error classes the system's current
 verification covers, with honest scoping.]

## 9. Recommendations
[Prioritized list of mitigations, ordered by severity.]
```

## 8. Checklist Template

```markdown
# PALS Assessment Checklist: [Target Name]

## Verification Boundary Existence
- [ ] Every LLM interaction surface has a declared verification boundary
- [ ] No path exists where LLM output reaches side-effect-producing
      systems without verification
- [ ] Verification boundaries are documented and scoped to specific
      error classes

## Error Class Coverage
- [ ] ERR_HALLUCINATION — factual claims are verified against ground truth
- [ ] ERR_OMISSION — output completeness is checked against requirements
- [ ] ERR_SCHEMA — structured output is validated against declared schemas
- [ ] ERR_TRUNCATION — output completeness / length is verified
- [ ] ERR_SYCOPHANCY — output consistency is checked across framings
- [ ] ERR_INSTRUCTION — constraint compliance is mechanically verified
- [ ] ERR_CALIBRATION — confidence expressions are calibrated or hedged
- [ ] ERR_REASONING — multi-step inferences are independently verified
- [ ] ERR_SEMANTIC — meaning preservation is verified (not just form)

## Architectural Corollaries
- [ ] Test-time correctness is not treated as proof of production safety
      (Corollary 1)
- [ ] Verification is not relaxed after observing good outputs
      (Corollary 2)
- [ ] Verification claims are scoped and documented per error class
      (Corollary 3)
- [ ] No silent acceptance paths exist in production
      (Corollary 4)
- [ ] Model upgrades trigger verification layer review
      (Corollary 5)

## Pipeline Safety (if applicable)
- [ ] Each LLM-dependent step has verification before output is consumed
      by next step
- [ ] Error cascade paths are identified and mitigated
- [ ] Pipeline state is observable and resumable after failure
- [ ] Destructive tool calls require confirmation or are bounded

## Tool Surface Safety (if target is an API consumed by agents)
- [ ] Every request/response is validatable against an explicit schema
- [ ] Error classes are machine-readable (not prose-only)
- [ ] Mutating operations are replay-safe (idempotency)
- [ ] Write commit state is observable by the caller
- [ ] Destructive operations are bounded or confirmation-gated
- [ ] Stable identifiers and deterministic pagination are provided
```
