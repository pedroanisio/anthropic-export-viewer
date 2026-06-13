---
name: problem-space-exploration
description: >
  Apply the Problem-Space Exploration Framework to transform solution-centric
  descriptions (app specs, product briefs, feature requests) into rigorous
  problem-centric analyses. Use this skill whenever the user explicitly
  requests a problem-space analysis, invokes the framework by name
  ("problem-space exploration", "PSE framework", "problem-space framework"),
  or asks to "run the problem-space exploration framework" on a given input.
  Also trigger when the user says "explore the problem space",
  "problem-centric analysis", "contamination guard", "problem class
  declaration", or references specific framework phases (Phase 0–7) by
  name. Do NOT trigger on general product critique, brainstorming, or
  spec review unless the user explicitly names this framework.
---

# Problem-Space Exploration Framework — Skill

## First Step: Load the Framework

Before doing anything else, read the full framework specification:

```
view /path/to/this/skill/references/framework.md
```

The framework document is the authoritative source for all phase
definitions, taxonomies, formats, and rules. Do not rely on memory
or summaries — load it fresh every time.

---

## Execution Modes

This skill supports two modes. **Ask the user which mode they want**
before proceeding, unless they have already indicated a preference.

### Mode A — Full Execution

Claude produces a complete problem-space analysis in a single pass.

**When to use:** The user provides a spec, brief, or description and
wants a finished analysis document. Typical prompt: "Run the PSE
framework on this spec."

**Process:**

1. Read the user's input (spec, brief, feature request, or description).
2. Declare the Problem Class (with justification and transition trigger).
3. Execute Phases 0 through 7 sequentially. Phase ordering is strict —
   see "Phase Ordering Rules" below.
4. Apply the Contamination Guard (Phase 0) at the end of every phase.
   Flag any solution-contaminated statements and reformulate or mark them.
5. Produce a single Markdown document as output (see "Output Format").

### Mode B — Guided Facilitation

Claude walks the user through each phase interactively, collecting
input and building the analysis collaboratively.

**When to use:** The user wants to think through the problem together,
or the input is too ambiguous for Claude to execute alone. Typical
prompt: "Let's explore the problem space for this idea."

**Process:**

1. Start by presenting the Problem Class taxonomy and asking the user
   to declare (or help them decide).
2. Walk through each phase in order. For each phase:
   - Explain what the phase does and why it matters (briefly).
   - Ask targeted questions drawn from the framework's required
     dimensions / structural questions.
   - Synthesize the user's answers into the phase output.
   - Run the Contamination Guard on the output; flag issues to the user.
   - Confirm the phase output before advancing.
3. After all phases are complete, compile into the final Markdown
   document (see "Output Format").

---

## Phase Ordering Rules

Phase ordering is **not optional**. The phases have dependency
relationships:

- **Phase 0** (Contamination Guard) is established first and applied
  continuously throughout all subsequent phases.
- **Phases 1–2** (Person in the Problem, Conditions and Triggers) must
  come before Phase 3 because vocabulary emerges from exploration.
- **Phase 3** (Vocabulary Consolidation) must precede Phase 5 because
  boundaries require stable terms.
- **Phase 5** (Problem Boundaries) and **Phase 5.1** (Constraint
  Relaxation Protocol) must precede Phase 6 because mandatory properties
  depend on bounded scope.
- **Phase 6** (Mandatory Properties) must precede Phase 7 because
  narratives test mandatory properties.
- **Phase 4** (Risks, Drawbacks, Failure Modes) feeds into Phase 5's
  constraints and Phase 7's catastrophic path.

Never skip or reorder phases. If the user asks to skip a phase,
explain the dependency and ask if they want to proceed with reduced
rigor (and note this in the output).

---

## Contamination Guard — Continuous Application

The Contamination Guard (Phase 0) is not a one-time check. At the
**end of every phase**, re-read the output and flag any statement
that:

1. Names a mechanism (solution, not problem).
2. Assumes a medium (presupposes a specific interface or artifact).
3. Specifies sequence where only outcome matters.
4. Uses implementation vocabulary (API, button, notification, module,
   endpoint, workflow engine) outside the context of analyzing an
   existing implementation.

Flagged statements must be either reformulated in problem-language
or explicitly marked as `[SOLUTION-ASSUMPTION: requires validation]`.

---

## Output Format

The final output is a **single Markdown document** with the following
structure:

```markdown
---
title: "Problem-Space Analysis: [Subject]"
framework_version: "1.1.0"
problem_class: "[Declared class]"
date: "[ISO date]"
disclaimer: >
  No information within this document should be taken for granted.
  Any statement or premise not backed by a real logical definition
  or verifiable reference may be invalid, erroneous, or a
  hallucination. This analysis is a reasoning instrument, not a
  truth claim.
---

# Problem-Space Analysis: [Subject]

## Problem Class Declaration
[Class, Justification, Transition Trigger]

## Phase 0 — Contamination Guard
[Detection criteria established for this analysis]

## Phase 1 — The Person in the Problem
[Required dimensions + Stakeholder topology]

## Phase 2 — Conditions and Triggers
[Structural questions + Counterfactual anchor]

## Phase 3 — Vocabulary Consolidation
[Term / Definition / Boundary / Source for each key term]

## Phase 4 — Risks, Drawbacks, and Failure Modes
[Failure taxonomy + per-risk analysis]

## Phase 5 — Problem Boundaries
[Problem statement, scope, constraints, validity conditions]

### Phase 5.1 — Constraint Relaxation Protocol
[Relaxation records, if any constraints are relaxed]

## Phase 6 — Mandatory Properties of Any Acceptable Resolution
[Property / Rationale / Violation test for each]

## Phase 7 — Narrative Execution Paths
### Path A — Coherent Resolution
[5-part narrative: initial state → trigger → decision points
→ resolution → residual risks]

### Path B — Catastrophic Execution
[6-part narrative: initial state → failure injection → cascade
→ detection failure → terminal state → retrospective signal]

## Contamination Audit Log
[Summary of all solution-contaminated statements found and
how they were handled across all phases]
```

### Output Rules

1. The disclaimer frontmatter is **mandatory**. Never omit it.
2. Every phase heading must appear even if the content is thin.
   An empty phase with a note ("Insufficient input to complete
   this phase — requires [X]") is better than a missing phase.
3. The Contamination Audit Log at the end collects all flags
   raised during the analysis. This is a quality signal for the
   user.
4. Use the vocabulary established in Phase 3 consistently from
   that point forward. If you catch yourself using a synonym not
   in the consolidated vocabulary, stop and either add it or use
   the established term.

---

## Iteration Guidance

The framework expects multiple passes:

- **First pass** reveals gaps.
- **Second pass** reveals contradictions.
- **Third pass** should stabilize.

If the third pass does not stabilize, the problem may be too
broadly scoped. Advise the user to return to Phase 5 and tighten
the boundaries.

If the Problem Class changes at any point (e.g., user realizes
the POC is actually going to production), treat it as a
**re-analysis event**: every constraint relaxation must be
re-evaluated, and the full framework should be re-run.

---

## What This Skill Does NOT Do

- It does not produce solution specifications. If the output reads
  like a product spec, the Contamination Guard was not applied
  rigorously enough.
- It does not replace domain expertise. The framework structures
  thinking; it does not supply domain knowledge.
- It does not guarantee completeness. The framework reduces the
  probability of unexamined assumptions; it does not eliminate it.
