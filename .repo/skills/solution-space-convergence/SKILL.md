---
name: solution-space-convergence
description: >
  Apply the Solution-Space Convergence Framework to transform a completed
  problem-space analysis (typically output from the Problem-Space
  Exploration skill) into a justified, auditable solution specification.
  Use this skill whenever the user explicitly requests a solution-space
  analysis, invokes the framework by name ("solution-space convergence",
  "SSC framework", "convergence framework"), or asks to "run SSC" on a
  given problem analysis. Also trigger when the user says "converge on
  a solution", "generate and select solution candidates", "run a trade
  study", "build a concept-selection matrix", "design rationale capture",
  or references specific framework phases (C0–C7) by name. Do NOT trigger
  on generic architecture discussion, coding tasks, or ad-hoc trade-off
  conversation unless the user explicitly names this framework. Requires
  a prior problem-space analysis as input; if none exists, redirect to
  the problem-space-exploration skill first.
---

# Solution-Space Convergence Framework — Skill

## First Step: Load the Framework

Before doing anything else, read the full framework specification:

```
view /path/to/this/skill/references/framework.md
```

The framework document is the authoritative source for all phase
definitions, notations, formats, and rules. Do not rely on memory or
summaries — load it fresh every time.

---

## Precondition: A Problem-Space Analysis Must Exist

This framework **does not generate its own problem analysis**. It
consumes one. If the user has not produced a problem-space analysis,
redirect them to the `problem-space-exploration` skill first and stop.

Acceptable inputs for this framework are:

1. A completed PSE analysis document (preferred).
2. A problem statement with explicit mandatory properties, constraints,
   and at least one narrative execution path, produced by any method
   that separates problem from solution with comparable rigor.

If neither is available, do not proceed — any "solution" produced from
an unstable problem is built on sand.

---

## Execution Modes

This skill supports two modes. **Ask the user which mode they want**
before proceeding, unless they have already indicated a preference.

### Mode A — Full Execution

Claude produces a complete solution-space convergence analysis in a
single pass.

**When to use:** The user provides a PSE analysis (or equivalent) and
wants a finished convergence document. Typical prompt: "Run SSC on this
problem analysis."

**Process:**

1. Read the problem-space analysis (input).
2. Verify the input meets the precondition (see "Input Adequacy Check"
   in the framework document). If not, stop and report the gap.
3. Execute Phases C0 through C7 sequentially. Phase ordering is strict —
   see "Phase Ordering Rules" below.
4. Apply the Reverse-Contamination Guard (Phase C0) at the end of every
   phase. Flag any solution decision that silently redefines the problem
   and either reject it or escalate it as a re-analysis event.
5. Produce a single Markdown document as output (see "Output Format").

### Mode B — Guided Facilitation

Claude walks the user through each phase interactively.

**When to use:** The user wants to reason through solution candidates
collaboratively, or the problem analysis has ambiguities that require
human judgment to resolve. Typical prompt: "Let's converge on a
solution for this problem."

**Process:**

1. Start by confirming the problem-space analysis is fixed for the
   duration of the convergence. Any mid-flight change to the problem
   is a re-analysis event, not an edit.
2. Walk through each phase in order. For each phase:
   - Explain what the phase does and why it matters (briefly).
   - Ask targeted questions drawn from the framework's required
     dimensions.
   - Synthesize the user's answers into the phase output.
   - Run the Reverse-Contamination Guard on the output.
   - Confirm the phase output before advancing.
3. After all phases are complete, compile into the final Markdown
   document (see "Output Format").

---

## Phase Ordering Rules

Phase ordering is **not optional**. The phases have dependency
relationships:

- **Phase C0** (Reverse-Contamination Guard) is established first and
  applied continuously throughout all subsequent phases.
- **Phase C1** (Input Adequacy Check) must pass before any candidate
  generation. Generating candidates from an inadequate problem
  specification produces false precision.
- **Phase C2** (Divergent Candidate Generation) must precede Phase C3
  because you cannot screen what has not been generated.
- **Phase C3** (Hard-Constraint Screening) must precede Phase C4
  because trade-off analysis among non-viable candidates is wasted
  effort.
- **Phase C4** (Trade-Off Analysis) must precede Phase C5 because
  catastrophic-path testing is expensive and should only run on
  survivors.
- **Phase C5** (Catastrophic-Path Stress Test) must precede Phase C6
  because selection without stress-test evidence is premature
  convergence.
- **Phase C6** (Selection and Rationale Capture) must precede Phase C7
  because verification plans depend on a chosen solution.
- **Phase C7** (Verification Plan and Handoff) is the final phase and
  produces the artifact the implementation team will consume.

Never skip or reorder phases. If the user asks to skip a phase,
explain the dependency and ask if they want to proceed with reduced
rigor (and note this in the output).

---

## Reverse-Contamination Guard — Continuous Application

Where the Problem-Space Exploration framework guards against
*solution-contamination of the problem*, this framework guards against
the opposite failure: **solution decisions that silently redefine the
problem to make the solution look better**.

At the **end of every phase**, re-read the output and flag any
statement that:

1. **Relaxes a mandatory property** from the problem analysis without
   going through an explicit re-analysis event.
2. **Reinterprets a hard constraint** as a soft preference to preserve
   a preferred candidate.
3. **Redefines the primary actor, trigger, or success condition** from
   Phases 1–2 of the problem analysis.
4. **Substitutes the narrative path** from Phase 7 with a more
   convenient one.

Flagged statements must be either reverted (the solution must adapt
to the problem, not the reverse) or escalated to the user as a
**re-analysis event**, which requires returning to the problem-space
framework.

---

## Output Format

The final output is a **single Markdown document** with the following
structure:

```markdown
---
title: "Solution-Space Convergence: [Subject]"
framework_version: "1.0.0"
problem_analysis_reference: "[Link or identifier of input PSE doc]"
problem_class: "[Class inherited from PSE]"
date: "[ISO date]"
disclaimer: >
  No information within this document should be taken for granted.
  Any statement or premise not backed by a real logical definition
  or verifiable reference may be invalid, erroneous, or a
  hallucination. This analysis is a reasoning instrument, not a
  truth claim. The solution selected here is conditional on the
  correctness of the input problem-space analysis.
---

# Solution-Space Convergence: [Subject]

## Input Reference
[Summary of the problem statement, mandatory properties, hard
constraints, and narrative paths inherited from the problem analysis.
This section is a restatement, not a revision.]

## Phase C0 — Reverse-Contamination Guard
[Detection criteria established for this convergence]

## Phase C1 — Input Adequacy Check
[Pass/Fail per required input element + gaps noted]

## Phase C2 — Divergent Candidate Generation
[≥3 structurally distinct candidates, each with architecture sketch,
mechanism summary, and assumed operating regime]

## Phase C3 — Hard-Constraint Screening
[Mandatory-property-by-candidate matrix: Pass / Fail / Uncertain,
with violation test result for each Fail]

## Phase C4 — Trade-Off Analysis (Soft Criteria)
[Pugh matrix or weighted decision matrix among C3 survivors,
with criteria traceable to the problem class and stakeholder
topology from the PSE input]

## Phase C5 — Catastrophic-Path Stress Test
[For each survivor, analysis against Phase 7 Path B from the PSE
input: dampens / neutral / amplifies the cascade]

## Phase C6 — Selection and Rationale Capture (QOC)
[Question / Options / Criteria notation for the primary selection
decision and any sub-decisions, with positive/negative assessments]

## Phase C7 — Verification Plan and Handoff
[Property → Mechanism → Test mapping, residual risks, and
implementation handoff checklist]

## Reverse-Contamination Audit Log
[Summary of all reverse-contamination flags raised during the
analysis and how they were handled]

## Re-Analysis Triggers
[Explicit list of conditions under which the convergence must be
re-run, inherited from the PSE transition triggers plus any
new ones surfaced during convergence]
```

### Output Rules

1. The disclaimer frontmatter is **mandatory**. Never omit it.
2. Every phase heading must appear even if the content is thin.
   An empty phase with a note ("Insufficient input to complete this
   phase — requires [X]") is better than a missing phase.
3. The Reverse-Contamination Audit Log at the end collects all flags
   raised during the analysis.
4. Use the vocabulary established in the PSE input's Phase 3
   consistently. Do not introduce new terms for concepts already
   named in the problem analysis; if a new term is needed, note it
   explicitly and justify why.

---

## Iteration Guidance

The framework expects multiple passes:

- **First pass** usually reveals that the candidate set is too narrow
  (fewer than 3 structurally distinct options) or that several
  candidates fail Phase C3 silently.
- **Second pass** usually reveals that soft criteria in Phase C4 are
  weighted in a way that pre-determines the winner. Reweight and retest.
- **Third pass** should stabilize.

If the third pass does not stabilize, one of the following is true:

- The problem analysis is under-specified (return to PSE).
- The candidate set is missing a fundamentally different architecture
  (return to C2 with a fresh perspective).
- The problem class is wrong (the weights that feel right do not match
  the declared class — return to PSE Problem Class Declaration).

---

## What This Skill Does NOT Do

- It does not replace the Problem-Space Exploration framework. It
  consumes PSE output.
- It does not produce implementation code. The output of Phase C7 is a
  specification with verification criteria, not an implementation.
- It does not make selection decisions for the user in Mode B. The
  framework structures the decision and makes rationale explicit; the
  user makes the call.
- It does not guarantee the chosen solution is correct. It guarantees
  that the reasoning from problem to solution is **auditable** —
  someone reading the output can reconstruct why this candidate was
  chosen and what would falsify the choice.
