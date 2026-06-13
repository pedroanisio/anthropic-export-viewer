---
title: "Problem-Space Exploration Framework"
version: "1.1.0"
type: "Methodological Specification"
disclaimer: >
  No information within this document should be taken for granted.
  Any statement or premise not backed by a real logical definition
  or verifiable reference may be invalid, erroneous, or a
  hallucination. The framework itself is a reasoning instrument,
  not a truth claim. Its value depends entirely on the rigor of
  the person applying it.
references:
  - "Christensen, C. (2016). Competing Against Luck. Harper Business. [Jobs-to-be-Done theory]"
  - "Klein, G. (2007). Performing a Project Premortem. Harvard Business Review. [Pre-mortem analysis]"
  - "Evans, E. (2003). Domain-Driven Design. Addison-Wesley. [Bounded Context]"
  - "Snowden, D. & Boone, M. (2007). A Leader's Framework for Decision Making. Harvard Business Review. [Cynefin]"
  - "IEC 60812:2018. Failure modes and effects analysis (FMEA and FMECA). [Failure mode taxonomy]"
  - "Cunningham, W. (1992). The WyCash Portfolio Management System. OOPSLA Experience Report. [Technical debt as deliberate trade-off]"
  - "Kruchten, P., Nord, R. & Ozkaya, I. (2012). Technical Debt: From Metaphor to Theory and Practice. IEEE Software 29(6). [Debt quadrant: deliberate/inadvertent × reckless/prudent]"
---

# Problem-Space Exploration Framework

## Purpose

This framework transforms a solution-centric description (an application
spec, a product brief, a feature request) into a problem-centric analysis.
The output is not a specification for *what to build*, but a rigorous
characterization of *what is wrong, for whom, under what conditions, and
what would constitute an acceptable resolution*.

The transformation matters because solution-centric descriptions embed
assumptions about implementation that foreclose alternatives, obscure risks,
and conflate the author's mental model with the user's actual situation.

---

## Problem Class Declaration

Before entering any phase, declare the **problem class**. The class
determines which failure modes are dominant, which constraints are
load-bearing, and which can be deliberately relaxed.

### Taxonomy

| Class              | Primary Risk              | Optimization Axis        | Constraint Profile                          |
|--------------------|---------------------------|--------------------------|---------------------------------------------|
| **Proof of Concept** | Over-engineering; never validating the core assumption | Speed to learning | Minimal. Most constraints are deferrable. The only non-negotiable is that the POC must *actually test the hypothesis it claims to test*. |
| **Prototype**        | Confusing the prototype with the product; stakeholders treating disposable work as commitments | Speed to feedback | Light. Structural shortcuts are acceptable if the interaction surface is representative. |
| **Enterprise**       | Under-engineering; shipping fast and paying compound interest for years | Durability under change | Heavy. Auth, audit, compliance, multi-tenancy, data governance, and operational observability are typically non-negotiable. |
| **Consumer**         | Misreading the person; solving the wrong problem elegantly | Fit to real behavior | Medium. Performance, accessibility, and privacy are non-negotiable. Architecture can be iterative if the interaction layer is right. |
| **Infrastructure**   | Abstraction leakage; building something that works until someone depends on it | Correctness under composition | Heavy. API contracts, failure semantics, backward compatibility, and operational transparency are non-negotiable. |

### Why This Matters

The same problem — say, "users lose work when context switches" — produces
radically different analyses depending on class:

- **POC**: Build the cheapest thing that tests whether auto-save reduces
  reported data loss. Skip auth. Skip multi-user. Ship in days.
- **Enterprise**: Auto-save must integrate with audit trails, conflict
  resolution, permission models, and data retention policies. Ship in
  months.
- **Consumer**: Auto-save must be invisible, instant, and never produce
  a confusing state. The technical mechanism matters less than the
  perceived experience. Ship when it feels right.

The framework phases remain the same across all classes. What changes is
the **weight** assigned to each phase's outputs and the **threshold**
for accepting constraint relaxation.

### Declaration Format

```
Problem Class: [POC | Prototype | Enterprise | Consumer | Infrastructure]
Justification: [Why this class, not another. One to three sentences.]
Transition Trigger: [What event or condition would force reclassification.
                     E.g., "If the POC gets deployed to production users,
                     it becomes Enterprise and must be re-analyzed."]
```

---

## Phase 0 — Contamination Guard

Before any analysis begins, establish the detection criteria for
**solution-contamination**: moments where the analysis stops describing
the problem and starts prescribing an implementation.

### Contamination Signals

A statement is solution-contaminated if any of the following hold:

1. **It names a mechanism.** "The system should sync data" is a solution.
   "Data becomes stale across contexts" is a problem.
2. **It assumes a medium.** "The user opens the dashboard" presupposes a
   dashboard exists. "The user needs visibility into X" does not.
3. **It specifies sequence where only outcome matters.** "First the user
   logs in, then selects a project" is solution-thinking. "The user must
   be able to act on a specific project with confidence in their
   authorization" is problem-thinking.
4. **It uses implementation vocabulary.** Words like *API*, *button*,
   *notification*, *module*, *endpoint*, *workflow engine* belong in a
   solution spec, not a problem analysis. The exception is when the
   problem IS about an existing implementation (e.g., "the current API
   fails under load").

### Application Rule

At the end of every subsequent phase, re-read the output and flag any
sentence that triggers one of these signals. Either reformulate it in
problem-language or explicitly mark it as a *solution-assumption* that
must be validated later.

---

## Phase 1 — The Person in the Problem

Describe the cognitive and emotional state of the person who encounters
this problem. This is not a persona exercise. It is an attempt to model
the *decision-making context* — what the person knows, what they don't
know, what they fear, and what they're optimizing for.

### Required Dimensions

| Dimension          | Question to Answer                                                                 |
|--------------------|------------------------------------------------------------------------------------|
| **Motivation**     | What is the person trying to accomplish *before* the problem appears?               |
| **Pressure**       | What external forces constrain their time, attention, or options?                   |
| **Uncertainty**    | What do they not know, and what is the cost of that ignorance?                     |
| **Expectation**    | What does "good enough" look like to them? What does "perfect" look like?          |
| **Frustration**    | What have they already tried, and why did it fail or feel insufficient?             |
| **Stakes**         | What do they lose if the problem persists? What do they risk by trying to solve it? |

### Stakeholder Topology

The person experiencing the problem is rarely the only actor. Map the
ecosystem:

- **Primary actor**: The person in the problem.
- **Affected parties**: Others who bear consequences of the problem or
  its resolution (team members, customers, dependents).
- **Veto holders**: Anyone who can block, reverse, or undermine a
  solution (managers, compliance, platform owners).
- **Beneficiaries of the status quo**: Anyone whose interests are served
  by the problem *remaining unsolved*. This category is frequently
  ignored and frequently decisive.

---

## Phase 2 — Conditions and Triggers

Explore the circumstances that make this problem *manifest*. A problem
that exists in theory but never triggers in practice is not a problem —
it is an anxiety.

### Structural Questions

1. **Under what conditions does the problem appear?**
   Enumerate specific scenarios. Be concrete: "when the team exceeds
   5 people" is better than "at scale."

2. **What triggers the transition from latent to acute?**
   Identify the event, threshold, or change that converts background
   friction into active pain.

3. **Is the problem continuous, periodic, or episodic?**
   Continuous problems justify permanent solutions. Episodic problems
   may be better served by coping strategies.

4. **Is the problem worsening, stable, or self-resolving?**
   If self-resolving, the cost of intervention must be justified against
   the cost of waiting.

5. **What adjacent problems does this problem create or intensify?**
   Problems rarely exist in isolation. Map the causal neighborhood.

### Counterfactual Anchor

**What happens if the problem is never solved?**

This question is mandatory. It establishes the baseline against which
any proposed solution must justify itself. If the answer is "nothing
significant changes," the problem may not warrant a dedicated solution.
If the answer is "cascading failures across X, Y, Z," the scope and
urgency are established.

---

## Phase 3 — Vocabulary Consolidation

Before proceeding to boundaries or requirements, consolidate the
terminology that has emerged from Phases 1 and 2.

### Why Here, Not Later

Precise boundaries require precise words. If "user," "project,"
"context," or "state" mean different things in different paragraphs,
the boundary definitions will be ambiguous and the requirements will
contradict each other. Vocabulary must be stabilized before it is
used structurally.

### Format

For each key term:

- **Term**: The word or phrase.
- **Definition**: What it means *in this problem space*. Not a
  dictionary definition — a contextual one.
- **Boundary**: What the term does NOT include. Negative definitions
  are often more clarifying than positive ones.
- **Source**: Where the term emerged in the analysis (Phase 1 dimension,
  Phase 2 scenario, etc.). Terms without traceable origin are suspect.

---

## Phase 4 — Risks, Drawbacks, and Failure Modes

Analyze what can go wrong — not with the problem, but with *attempting
to address it*.

### Taxonomy of Failure

Adapted from FMEA (IEC 60812) structure, applied to problem-solving
rather than hardware:

| Failure Mode               | Description                                                                                  |
|----------------------------|----------------------------------------------------------------------------------------------|
| **Misdiagnosis**           | The stated problem is a symptom; the root cause is elsewhere.                                |
| **Scope creep**            | Addressing the problem pulls in adjacent concerns until the effort becomes unmanageable.      |
| **Displacement**           | Solving the problem here creates an equivalent or worse problem elsewhere.                   |
| **Dependency lock**        | The solution creates a dependency that is harder to remove than the original problem.         |
| **Expectation mismatch**   | The solution addresses the problem as analyzed but not as experienced by the primary actor.   |
| **Stakeholder conflict**   | Resolution benefits some actors at the expense of others, triggering resistance.              |
| **Premature convergence**  | The first plausible solution is adopted without exploring the space, foreclosing better options.|

### For Each Identified Risk

- **Likelihood**: How probable is this failure mode given what is known?
- **Impact**: If it occurs, what is the damage and to whom?
- **Detection**: How would you know this failure mode has occurred?
  (If the answer is "you wouldn't, until it's too late," this is the
  highest-priority risk.)
- **Mitigation**: What would prevent, reduce, or contain the damage?

---

## Phase 5 — Problem Boundaries

Restate the problem with explicit scope. This is the synthesis of
everything above — the person, the conditions, the vocabulary, and the
risks — compressed into a bounded definition.

### Structure

**The problem is:**
_(One to three sentences. No solution language. Uses consolidated
vocabulary.)_

**Inside scope:**
_(What this problem analysis covers. Concrete, enumerable.)_

**Outside scope:**
_(What this analysis explicitly excludes. Name the adjacent problems
that are tempting to absorb and explain why they are excluded.)_

**Constraints:**
_(Non-negotiable conditions that any resolution must respect.
Distinguish between constraints imposed by reality — physics, law,
existing commitments — and constraints imposed by choice — values,
priorities, strategy.)_

**Validity conditions:**
_(Under what circumstances does this problem statement become invalid?
What evidence would force a restatement? If no such evidence is
conceivable, the statement is unfalsifiable and therefore suspect.)_

---

## Phase 5.1 — Constraint Relaxation Protocol

Any constraint from Phase 5 or mandatory property from Phase 6 may be
**deliberately relaxed** — but never silently dropped. Silent removal
is how technical debt becomes invisible until it compounds into crisis.

This protocol is adapted from Cunningham's original technical debt
metaphor (1992) and Kruchten, Nord & Ozkaya's debt quadrant (2012).
The framework only permits **deliberate-prudent** debt: you know what
you're deferring, you know why, and you know what triggers repayment.

### Relaxation Record Format

For each constraint being relaxed:

```
Constraint:        [Name of the constraint being relaxed]
Problem Class:     [Current declared class from Problem Class Declaration]
Relaxation Type:   [Deferred | Degraded | Removed]
  - Deferred:  Will be enforced later. A specific trigger restores it.
  - Degraded:  A weaker version is accepted. Define the weaker version.
  - Removed:   Permanently excluded. Requires explicit justification.

Justification:     [Why this relaxation is acceptable given the current
                    problem class. Must reference the class's optimization
                    axis — e.g., "POC optimizes for speed to learning;
                    auth does not gate the hypothesis being tested."]

Blast Radius:      [What breaks, degrades, or becomes impossible when
                    this constraint is absent. Be concrete:
                    - "Multi-user scenarios cannot be tested."
                    - "Data integrity depends on a single-writer assumption."
                    - "Compliance audit would fail on section X."]

Restoration Trigger: [The event, threshold, or class transition that
                      forces this constraint back into scope. E.g.:
                      - "If the POC is shown to external users."
                      - "If more than one person writes to the same data."
                      - "If the problem class transitions to Enterprise."]

Restoration Cost:  [Estimated effort to restore the constraint later,
                    expressed qualitatively:
                    - Trivial:  Configuration change, feature flag.
                    - Moderate: Refactor required but no redesign.
                    - Severe:   Architectural change; may require rewrite
                                of dependent components.
                    - Unknown:  Cannot estimate. This is a warning flag.]
```

### Rules

1. **Every relaxation must be recorded.** An unrecorded relaxation is
   not a trade-off — it is a mistake waiting to be discovered.

2. **The restoration trigger is mandatory.** "We'll add it later" is
   not a trigger. "When X happens" is. If no trigger can be defined,
   the relaxation type must be `Removed`, which requires stronger
   justification.

3. **Restoration cost of `Unknown` is a risk.** It must appear in
   Phase 4's risk analysis. Deferring a constraint whose restoration
   cost is unknown is a bet, and it should be evaluated as one.

4. **Class transitions invalidate relaxations.** If the Problem Class
   changes (e.g., POC → Enterprise), every relaxation record must be
   re-evaluated. Relaxations justified by the old class do not
   automatically carry over.

5. **Relaxation does not reduce analysis rigor.** Deciding to skip
   auth in a POC still requires understanding *why* auth exists in
   the problem space, *what* it protects, and *what scenarios* become
   invalid without it. The relaxation is applied in Phase 6 (mandatory
   properties), not in Phases 1–5 (understanding).

### Common Relaxation Patterns by Problem Class

| Constraint Domain    | POC                    | Prototype              | Enterprise           | Consumer               |
|----------------------|------------------------|------------------------|----------------------|------------------------|
| Authentication       | Typically deferrable   | Deferrable if single-user | Non-negotiable     | Non-negotiable         |
| Authorization/RBAC   | Typically removable    | Deferrable             | Non-negotiable       | Deferrable early       |
| Data persistence     | Degradable (in-memory) | Degradable             | Non-negotiable       | Non-negotiable         |
| Error handling       | Degradable             | Degradable             | Non-negotiable       | Non-negotiable         |
| Scalability          | Removable              | Removable              | Deferrable           | Deferrable early       |
| Observability        | Deferrable             | Deferrable             | Non-negotiable       | Deferrable             |
| Accessibility        | Deferrable             | Degradable             | Non-negotiable       | Non-negotiable         |
| Test coverage        | Degradable             | Degradable             | Non-negotiable       | Deferrable early       |

This table is a starting heuristic, not a rulebook. The actual
relaxation decision depends on the specific problem, the specific
constraint, and the specific blast radius.

---

## Phase 6 — Mandatory Properties of Any Acceptable Resolution

These are not features. They are properties that must hold regardless
of implementation form.

### Format

For each mandatory property:

- **Property**: What must be true.
- **Rationale**: Why it must be true, traced to a specific finding in
  Phases 1–5.
- **Violation test**: A concrete scenario in which this property is
  absent. If the outcome of that scenario is acceptable, the property
  is not actually mandatory — demote it to "desirable."

---

## Phase 7 — Narrative Execution Paths

Two structured narratives that test the problem analysis against
temporal reality.

### Path A — Coherent Resolution (Reversal Happy Path)

A narrative showing what clean execution looks like from first
recognition of the problem through stable resolution.

**Required structure:**

1. **Initial state**: The person in the problem, before any action.
   Use Phase 1 dimensions.
2. **Trigger**: The event or realization that initiates action. Use
   Phase 2 conditions.
3. **Decision points**: At least three moments where the person or
   a stakeholder must choose between alternatives. At each point:
   - What information is available?
   - What is chosen and why?
   - What is foreclosed by that choice?
4. **Resolution state**: The problem is resolved. Describe what
   "resolved" looks like in concrete, observable terms — not
   feelings, not abstractions.
5. **Residual risks**: What risks from Phase 4 remain even in the
   happy path? (If the answer is "none," the analysis is
   insufficiently honest.)

### Path B — Catastrophic Execution (Disastrous Path)

A narrative showing what systemic failure looks like.

**Required structure:**

1. **Same initial state** as Path A. The divergence must come from
   decisions and conditions, not from a different starting point.
2. **Failure injection**: Identify the earliest point where a
   plausible mistake, misunderstanding, or bad-luck event changes
   the trajectory.
3. **Cascade mechanism**: Show how the initial failure propagates.
   Use the failure modes from Phase 4 — at least two must appear
   in the narrative.
4. **Detection failure**: Show the point at which the actors could
   have recognized the failure and didn't. Explain why.
5. **Terminal state**: The problem is now worse than before the
   attempt. Describe the damage concretely.
6. **Retrospective signal**: Identify the earliest observable
   indicator that, in hindsight, predicted the failure. This
   becomes a monitoring criterion for any future attempt.

---

## Usage Notes

### Ordering Is Not Optional

The phases are ordered by dependency. Phase 3 (Vocabulary) cannot
precede Phases 1–2 because vocabulary emerges from exploration.
Phase 5 (Boundaries) cannot precede Phase 3 because boundaries
require stable terms. Phase 7 (Narratives) cannot precede Phase 6
because narratives test mandatory properties.

Skipping phases or reordering them will produce outputs that
*look* structured but contain unresolved ambiguities.

### Iteration Is Expected

The first pass through this framework will reveal gaps. The second
pass will reveal contradictions. The third pass should stabilize.
If it does not, the problem may be too broadly scoped — return to
Phase 5 and tighten the boundaries.

### Class Transitions Are Re-Analysis Events

When a POC becomes a product, or a prototype gets deployed, the
Problem Class changes. This is not an incremental update — it
invalidates the constraint relaxations, shifts the dominant failure
modes, and may invalidate the problem boundaries themselves. Treat
class transitions as triggers for a fresh pass through the framework,
not as occasions to bolt new requirements onto the old analysis.

### This Framework Is Not a Solution

If the output of this framework reads like a product specification,
the contamination guard (Phase 0) was not applied rigorously enough.
Return to Phase 0 and re-audit.
