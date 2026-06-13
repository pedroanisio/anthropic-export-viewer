---
title: "Solution-Space Convergence Framework"
version: "1.0.0"
type: "Methodological Specification"
disclaimer: >
  No information within this document should be taken for granted.
  Any statement or premise not backed by a real logical definition
  or verifiable reference may be invalid, erroneous, or a
  hallucination. The framework itself is a reasoning instrument,
  not a truth claim. Its value depends entirely on the rigor of
  the person applying it and on the correctness of the input
  problem-space analysis.
references:
  - "Pugh, S. (1991). Total Design: Integrated Methods for Successful Product Engineering. Addison-Wesley. ISBN 0201416395. [Concept selection / Pugh matrix]"
  - "Pugh, S. (1981). Concept Selection — A Method That Works. Proceedings of ICED'81, Heurista, Zürich, pp. 497–506. [Original publication]"
  - "NASA (2016). NASA Systems Engineering Handbook, Rev. 2, NASA/SP-2016-6105. Section on Decision Analysis Process and trade studies. [Trade study methodology]"
  - "Kazman, R., Klein, M., Barbacci, M., Longstaff, T., Lipson, H. & Carriere, S. (1998). The Architecture Tradeoff Analysis Method. CMU/SEI-98-TR-008, Software Engineering Institute, Carnegie Mellon University. [ATAM]"
  - "Kazman, R., Klein, M. & Clements, P. (2000). ATAM: Method for Architecture Evaluation. CMU/SEI-2000-TR-004, Software Engineering Institute, Carnegie Mellon University. [ATAM nine-step process]"
  - "Ward, A., Liker, J., Cristiano, J. & Sobek, D. (1995). The Second Toyota Paradox: How Delaying Decisions Can Make Better Cars Faster. Sloan Management Review 36(3), 43–61. [Set-based concurrent engineering]"
  - "Sobek, D., Ward, A. & Liker, J. (1999). Toyota's Principles of Set-Based Concurrent Engineering. Sloan Management Review 40(2), 67–83. [SBCE principles]"
  - "MacLean, A., Young, R., Bellotti, V. & Moran, T. (1991). Questions, Options, and Criteria: Elements of Design Space Analysis. Human–Computer Interaction 6(3–4), 201–250. [QOC notation / design rationale]"
  - "Design Council UK (2005). Eleven Lessons: Managing Design in Eleven Global Brands. [Double Diamond model]"
  - "Dorst, K. & Cross, N. (2001). Creativity in the design process: co-evolution of problem–solution spaces. Design Studies 22(5), 425–437. [Problem–solution co-evolution]"
---

# Solution-Space Convergence Framework

## Purpose

This framework transforms a completed problem-space analysis into a
**justified, auditable solution specification**. The output is not an
implementation, but a specification of *which candidate solution was
selected, why it was selected over alternatives, how it satisfies the
mandatory properties of the problem, and what would falsify the
choice*.

The framework is designed as a companion to the Problem-Space
Exploration (PSE) framework. Where PSE guards against
solution-contamination *of the problem*, this framework guards against
the opposite failure: **solution decisions that silently redefine the
problem to make a preferred solution look acceptable**.

### Why This Matters

Most solution-definition failures happen not because engineers choose
badly among options, but because:

1. Only one option was seriously considered (premature convergence).
2. Options were eliminated by hidden criteria rather than explicit
   violation tests.
3. The criteria used to compare options silently contradicted the
   mandatory properties from the problem analysis.
4. The rationale for the selected option was never recorded, so when
   conditions changed the team could not distinguish decisions that
   were load-bearing from decisions that were incidental.

This framework addresses each of those failure modes with a dedicated
phase.

---

## Intellectual Lineage

The framework synthesizes four research traditions. Each is cited where
it contributes, rather than presented as novel:

- **Concept selection (Pugh, 1981, 1991).** The decision-matrix method
  for screening and comparing design candidates against criteria.
  Contributes the core screening/trade-off mechanism in Phases C3 and C4.
- **Systems-engineering trade studies (NASA, 2016).** Structured
  decision analysis with quantitative evaluation criteria and
  explicit uncertainty handling. Contributes the discipline of
  verification planning in Phase C7.
- **Architecture Tradeoff Analysis Method (Kazman et al., 1998, 2000).**
  Scenario-based evaluation of architectures against quality attributes,
  with explicit identification of risks, non-risks, sensitivity points,
  and trade-off points. Contributes the stress-test structure in Phase
  C5.
- **Set-based concurrent engineering (Ward et al., 1995; Sobek et al.,
  1999).** Parallel exploration of multiple design sets, with gradual
  narrowing rather than early commitment. Contributes the divergence
  discipline in Phase C2.
- **Design rationale / QOC (MacLean et al., 1991).** Explicit capture
  of the design space as Questions, Options, and Criteria, with
  assessments linking options to criteria. Contributes the rationale
  format in Phase C6.

The divergence-then-convergence rhythm echoes the Double Diamond
model (Design Council UK, 2005; Dorst & Cross, 2001), with the first
diamond having been completed by the PSE framework and the second
diamond being the subject of this framework.

---

## Precondition: Input Problem-Space Analysis

This framework consumes a completed problem-space analysis. The input
must contain the following elements (or demonstrable equivalents):

| Required Input Element                         | From PSE Phase |
|------------------------------------------------|----------------|
| Problem class declaration                      | Preamble       |
| Primary actor and stakeholder topology         | Phase 1        |
| Trigger conditions and counterfactual anchor   | Phase 2        |
| Consolidated vocabulary                        | Phase 3        |
| Failure mode taxonomy                          | Phase 4        |
| Problem statement, scope, and hard constraints | Phase 5        |
| Mandatory properties with violation tests      | Phase 6        |
| Coherent resolution narrative (Path A)         | Phase 7        |
| Catastrophic execution narrative (Path B)      | Phase 7        |

If any of these are missing, Phase C1 will fail the Input Adequacy
Check and the convergence cannot proceed. Do not attempt to
reconstruct missing elements on the fly — this would be
reverse-contamination in its purest form.

---

## Phase C0 — Reverse-Contamination Guard

Before any analysis begins, establish the detection criteria for
**reverse-contamination**: moments where the solution analysis stops
respecting the problem boundary and starts editing the problem to suit
a preferred solution.

### Reverse-Contamination Signals

A statement is reverse-contaminated if any of the following hold:

1. **It relaxes a mandatory property** from PSE Phase 6 without an
   explicit re-analysis event. Example: "We'll treat the audit-log
   requirement as best-effort because none of our candidates can
   satisfy it fully."
2. **It reinterprets a hard constraint** from PSE Phase 5 as a soft
   preference. Example: "The 'must work offline' constraint is really
   about poor connectivity, so intermittent connectivity is close
   enough."
3. **It redefines the primary actor, trigger, or success condition**
   from PSE Phases 1–2. Example: "The user in our mental model is
   more technical than the actor described in the analysis."
4. **It substitutes the narrative path** from PSE Phase 7. Example:
   "The coherent-resolution path assumes the user notices the
   problem, but in our solution the system notices first, so we can
   skip that step."
5. **It invents new mandatory properties** not present in the problem
   analysis, to justify a preferred candidate's unique strength.

### Response to Contamination Flags

When a reverse-contamination flag is raised:

- **Default response:** The solution must adapt to the problem. The
  candidate is eliminated or revised, not the problem.
- **Escalation response:** If the team genuinely believes the problem
  analysis is wrong in the flagged respect, stop the convergence and
  trigger a **re-analysis event**: return to the PSE framework, revise
  the problem analysis explicitly, and restart convergence from C1.
  Do not edit the problem document silently.

The Contamination Guard runs at the end of every subsequent phase, not
only at the start.

---

## Phase C1 — Input Adequacy Check

Before generating any candidates, verify that the problem-space
analysis provides the minimum information needed to evaluate
candidates.

### Check Procedure

For each required input element (see Precondition table), rate the
input as **Present**, **Partial**, or **Absent**.

- **All Present:** Proceed to C2.
- **Any Partial:** Note the gaps and proceed to C2 with explicit
  marking that any downstream phase depending on the partial element
  will be weakened.
- **Any Absent:** Stop the convergence. Return the gap list to the
  user and direct them to PSE to complete the missing phase(s).

### Special Check: Mandatory Properties Must Be Testable

A mandatory property from PSE Phase 6 is only usable if it has a
**violation test**: a procedure by which a candidate can be declared
to fail the property. Properties without violation tests are aspirations,
not constraints, and must be either:

- Refined into testable form (return to PSE Phase 6), or
- Moved to the soft-criteria list for Phase C4.

### Output Format

```
Input Adequacy Check
  Problem class:                 [Present | Partial | Absent]
  Primary actor & topology:      [Present | Partial | Absent]
  Triggers & counterfactual:     [Present | Partial | Absent]
  Consolidated vocabulary:       [Present | Partial | Absent]
  Failure mode taxonomy:         [Present | Partial | Absent]
  Problem statement & scope:     [Present | Partial | Absent]
  Hard constraints:              [Present | Partial | Absent]
  Mandatory properties:          [Present | Partial | Absent]
    Each has violation test:     [Yes | No | List which do not]
  Path A (coherent resolution):  [Present | Partial | Absent]
  Path B (catastrophic):         [Present | Partial | Absent]
Overall:                         [PROCEED | PROCEED WITH GAPS | STOP]
```

---

## Phase C2 — Divergent Candidate Generation

Generate a set of **structurally distinct** candidate solutions. The
goal of this phase is deliberate divergence, not efficiency.

### Rationale

Ward et al. (1995) and Sobek et al. (1999) documented that Toyota's
product development process outperforms point-based approaches by
carrying multiple candidate solutions in parallel and narrowing the
set gradually as evidence accumulates. Premature convergence on a
single candidate — common in Western engineering practice — forecloses
the discovery of superior options and makes late failures expensive
because no alternatives remain.

This phase operationalizes that discipline.

### Minimum Requirements

1. **At least three candidates.** Two candidates produce a false
   binary; one candidate is premature convergence. Three is the floor.
2. **Structural distinction.** Candidates must differ in their
   fundamental mechanism or architecture, not merely in surface
   parameters. "Option A with feature flag on" and "Option A with
   feature flag off" are one candidate, not two.
3. **Problem-class appropriate diversity.** For a POC, candidates may
   be thin sketches. For an Enterprise or Infrastructure problem,
   candidates should span meaningfully different architectural
   families (e.g., centralized vs. distributed, synchronous vs.
   asynchronous, build vs. buy).
4. **No pre-evaluation.** During generation, do not screen candidates
   against the mandatory properties. That happens in C3. Mixing
   generation and evaluation is the divergence/convergence collapse
   that both the Double Diamond (Design Council UK, 2005) and QOC
   (MacLean et al., 1991) are designed to prevent.

### Per-Candidate Format

For each candidate, document:

| Field                    | Description                                                      |
|--------------------------|------------------------------------------------------------------|
| **Candidate ID**         | Short identifier (e.g., C-A, C-B, C-C).                          |
| **Architectural sketch** | 2–5 sentences describing the structure in problem-space terms.   |
| **Primary mechanism**    | The specific mechanism by which the candidate resolves the trigger from PSE Phase 2. |
| **Assumed regime**       | Operating conditions the candidate assumes (scale, load, failure modes it assumes are rare). |
| **Known open questions** | Things that would need to be verified if this candidate were pursued. |

### Contamination Check

At the end of C2, re-read each candidate description and confirm:

- No candidate description contradicts the PSE vocabulary.
- No candidate requires relaxing a hard constraint to be describable.
- No candidate is phrased in a way that redefines the primary actor.

Flag any issue and either revise the candidate or eliminate it.

---

## Phase C3 — Hard-Constraint Screening

Screen each candidate against the mandatory properties from PSE Phase
6. The mechanism is the Pugh concept-screening step (Pugh, 1981),
adapted so that each cell contains a **violation-test result**, not
a preference score.

### Rationale

Pugh's decision-matrix method separates two kinds of evaluation:
binary screening against must-have criteria (done here in C3) and
preference-weighted trade-off among survivors (done in C4). The
two must not be collapsed; the 1991 Wikipedia-documented critique of
weighted decision matrices is that scoring with weights can allow a
candidate to "win" overall while missing a must-have requirement. This
framework avoids that failure mode by making C3 binary and
non-negotiable.

### Procedure

Build a matrix with mandatory properties as rows and candidates as
columns. For each cell, record one of:

- **Pass:** The candidate satisfies the violation test.
- **Fail:** The candidate fails the violation test. Record which
  test and how it fails.
- **Uncertain:** The violation test cannot be run without building
  the candidate, or the test itself is ambiguous.

### Decision Rules

- A candidate with **any Fail** is eliminated. Do not advance failed
  candidates to C4. Do not negotiate ("we could relax that property")
  — any such negotiation is reverse-contamination and must be handled
  via Phase C0.
- A candidate with **all Pass** advances to C4.
- A candidate with **some Uncertain and no Fail** advances to C4 with
  a marker, and Phase C7 will require a verification step for each
  Uncertain cell before implementation commits.

### If Fewer Than Two Candidates Survive

If zero or one candidate survives C3:

- **Zero survivors:** The problem as specified may be infeasible under
  the current mandatory properties. Return to PSE with this finding —
  it is a legitimate outcome of the framework, not a framework failure.
- **One survivor:** Do not proceed to C4 with a single candidate.
  Either return to C2 and generate additional structurally distinct
  candidates, or accept that there is effectively no choice and
  proceed directly to C5 with documentation that C4 was skipped.

### Output Format

A matrix in Markdown table form, followed by a list of eliminated
candidates with their failure reasons.

---

## Phase C4 — Trade-Off Analysis (Soft Criteria)

Compare the C3 survivors on **soft criteria** — criteria that
differentiate acceptable candidates from each other but are not
mandatory in the problem-analysis sense.

### Rationale

Soft criteria include cost, development time, operational load,
reversibility, time-to-signal, organizational fit, and dependency
risk. These matter, but they are not "must-haves" and confusing them
with mandatory properties is the failure mode Pugh (1991) and the
concept-selection literature repeatedly warn against.

The trade-off discipline here follows Pugh's concept-selection
method. For large candidate sets or high-stakes decisions, a weighted
version may be used, with the caveat that weighting is
itself a judgment that must be made explicit and open to revision.

### Procedure

1. **Derive soft criteria from the problem class and stakeholder
   topology.** A POC weighs speed and reversibility. An Enterprise
   problem weighs operational load, failure isolation, and audit
   coverage. An Infrastructure problem weighs API stability, backward
   compatibility, and dependency burden. Do not invent criteria that
   are not traceable to the problem analysis.
2. **Assign weights explicitly** if using a weighted matrix. Weights
   must be agreed before scoring, not after.
3. **Select a datum** — typically the status-quo candidate (or
   "do nothing") if one exists, otherwise the simplest surviving
   candidate (Pugh, 1991; the Pugh method uses a datum rather than
   absolute scoring).
4. **Score each non-datum candidate relative to the datum** on each
   criterion: better (+), same (S), or worse (−). For weighted
   matrices, use numeric scales (e.g., −2..+2) and multiply by
   weight.
5. **Sum the scores** per candidate but **do not treat the sum as
   the decision**. The sum is a signal for further examination, not
   a selector. If the highest-scoring candidate has more criteria
   marked worse than another candidate, that is a trade-off worth
   discussing, not a result to overrule.

### Anti-Patterns (to flag and revise)

- **Criterion stacking:** Multiple criteria that measure the same
  underlying property inflate its apparent importance.
- **Weight engineering:** Adjusting weights after scoring to produce
  a desired winner. Weights must be locked before scoring.
- **Missing datum:** Scoring candidates without a reference point
  produces subjective ratings that are hard to compare.
- **False precision:** Using numeric weights that imply accuracy the
  team does not actually have (see the Wikipedia decision-matrix
  caveat: "the entire decision matrix can create the impression of
  being scientific, even though it requires no quantitative
  measurements of anything at all").

### Output Format

A Pugh or weighted matrix in Markdown table form, followed by a
list of identified trade-offs (sensitivity points) to carry into C5.

---

## Phase C5 — Catastrophic-Path Stress Test

Test each remaining candidate against the catastrophic-execution
narrative (Path B) from PSE Phase 7.

### Rationale

The ATAM (Kazman et al., 1998, 2000) evaluates architectures by
running scenarios — specifically, quality-attribute scenarios — against
each architectural approach and recording **risks, non-risks,
sensitivity points, and trade-off points**. The insight is that an
architecture's quality cannot be read from its diagram; it is
revealed by asking how the architecture responds to specific,
operationally meaningful stimuli.

This phase adapts that discipline. Path B from the PSE framework is
exactly such a scenario: it describes how the problem would unfold
catastrophically. A solution candidate that makes Path B *more*
likely, or that accelerates the cascade once Path B begins, is
worse than a candidate that dampens or interrupts Path B — even
if C4 scored the former higher on soft criteria.

### Procedure

For each candidate surviving C4:

1. **Walk the candidate through Path B step by step.** At each step,
   ask: would this candidate change the probability or severity of
   the next step?
2. **Classify the candidate's effect** on each step as:
   - **Dampens:** The candidate reduces the probability or severity
     of this step, interrupting the cascade.
   - **Neutral:** The candidate does not affect this step.
   - **Amplifies:** The candidate increases the probability or
     severity of this step, accelerating the cascade.
3. **Identify new failure modes** the candidate introduces that are
   not in Path B. These extend the failure taxonomy from PSE Phase 4
   and must be recorded.
4. **Record ATAM-style findings** for each candidate:
   - **Risks:** Candidate-specific decisions that threaten a mandatory
     property or amplify Path B.
   - **Non-risks:** Candidate-specific decisions that are
     demonstrably sound under the scenario.
   - **Sensitivity points:** Candidate decisions to which quality
     outcomes are especially sensitive.
   - **Trade-off points:** Candidate decisions that improve one
     property at the cost of another.

### Decision Signals

- A candidate that **amplifies any Path B step** is a
  finalist-of-last-resort: it may still be chosen, but only if the
  amplification can be mitigated by an explicit control, and the
  control itself must be verifiable (Phase C7).
- A candidate that **introduces failure modes not in PSE Phase 4**
  requires updating the problem analysis (re-analysis event) or
  demonstrating that the new modes are dominated by mitigations
  already present in the problem analysis.

### Output Format

For each candidate, a Markdown section with:

- Path B step-by-step effect classification
- New failure modes introduced
- ATAM findings (risks, non-risks, sensitivity points, trade-off
  points)

---

## Phase C6 — Selection and Rationale Capture (QOC)

Make the final selection and capture the rationale in a form that
survives the passage of time and personnel changes.

### Rationale

MacLean et al. (1991) argued that design decisions made without
explicit rationale capture are effectively unmaintainable: when
conditions change, maintainers cannot distinguish decisions that
were load-bearing from decisions that were incidental, and so they
treat all decisions as sacred (paralyzing change) or all decisions
as revisable (breaking invariants). The **QOC notation** — Questions,
Options, Criteria, with positive/negative assessments linking
options to criteria — was designed to solve this.

This phase uses QOC as the rationale format.

### Procedure

1. **Frame the selection as one or more Questions.** The top-level
   question is typically "Which candidate satisfies the mandatory
   properties while best serving the soft criteria?" Sub-questions
   emerge from trade-off points identified in C5.
2. **List the Options** for each question. For the top-level question,
   these are the C5 survivors.
3. **List the Criteria** against which options are compared. Criteria
   are drawn from the PSE mandatory properties (already binary, so
   uniformly positive) and the C4 soft criteria.
4. **Record assessments** linking each Option to each Criterion as
   **positive** (the option supports the criterion) or **negative**
   (the option works against the criterion).
5. **Select the Option** that emerges from the assessments. If no
   single option dominates, record the trade-off explicitly and
   justify the selection on specified grounds — typically by which
   criteria are more tightly bound to the problem class.

### Format (following MacLean et al., 1991)

```
Q: [Question text]
  O: [Option 1]
    + [Criterion the option supports]
    − [Criterion the option works against]
  O: [Option 2]
    + [...]
    − [...]
  O: [Option 3]
    + [...]
    − [...]
Selected: [Option N]
Rationale: [Which criteria were decisive and why, referencing the
            problem class and the C5 catastrophic-path findings.]
```

Nest sub-questions as MacLean et al. (1991) describe: an option in
one diagram may spawn a new question in a child diagram for any
decision the option defers.

### Contamination Check

At the end of C6, re-read the selection rationale and confirm:

- No criterion cited in the rationale silently relaxes a PSE Phase 6
  mandatory property.
- No criterion cited in the rationale is specific to the winning
  candidate in a way that presupposes the selection.
- The decisive criteria are traceable to the problem class and
  stakeholder topology from the PSE input.

---

## Phase C7 — Verification Plan and Handoff

Produce the specification the implementation team will consume.

### Rationale

NASA's systems engineering practice (NASA, 2016) frames the link
between design and implementation as a verification problem: for
every requirement, there must be a specified test by which the
implementation can be shown to meet it. Without this link,
implementation drift is invisible until it fails operationally.

This phase produces that link.

### Procedure

1. **Map each mandatory property from PSE Phase 6 to the mechanism
   in the selected candidate that satisfies it.** If any property
   has no corresponding mechanism, the selection is incomplete —
   return to C6.
2. **Specify a verification test for each mapping.** The test must
   be concrete enough that a third party can run it and produce a
   binary pass/fail result.
3. **Record residual risks.** These include:
   - Uncertain cells from C3 that were advanced pending verification.
   - Path B amplifications from C5 that were accepted with
     mitigations.
   - Sensitivity points from C5 that affect verification
     interpretation.
4. **Produce the handoff checklist.** The implementation team needs
   to know: what must be true at implementation start, what must be
   verified before deploy, and what conditions would trigger
   re-running the convergence.

### Output Format

| Mandatory Property (from PSE Phase 6) | Mechanism in Selected Candidate | Verification Test | Owner |
|---------------------------------------|---------------------------------|-------------------|-------|
| [property 1]                          | [mechanism]                     | [test]            | [who] |
| ...                                   | ...                             | ...               | ...   |

Followed by:

- **Residual risks:** [list, with mitigations]
- **Handoff checklist:** [what must be true at start, before deploy,
  and triggers for re-analysis]

---

## Phase Ordering — Why It Cannot Be Shuffled

| Phase | Depends on                                     | Why                                                                          |
|-------|------------------------------------------------|------------------------------------------------------------------------------|
| C0    | (none — established first)                     | Contamination can appear in any phase; the guard must be active throughout. |
| C1    | PSE input                                      | Cannot evaluate what has not been specified.                                 |
| C2    | C1                                             | Generating candidates from an inadequate problem produces false precision.  |
| C3    | C2                                             | Cannot screen candidates that do not exist.                                  |
| C4    | C3                                             | Trade-off analysis among non-viable candidates is wasted effort.            |
| C5    | C4                                             | Stress testing is expensive; run only on trade-off survivors.                |
| C6    | C5                                             | Selection without stress-test evidence is premature convergence.             |
| C7    | C6                                             | Verification plan requires a selected mechanism.                             |

---

## Iteration — What to Do When the Framework Does Not Stabilize

The framework expects multiple passes. A common trajectory:

- **First pass** reveals that C2 produced too few or
  insufficiently-distinct candidates. Expand and retry.
- **Second pass** reveals that C4 weights are tuned such that a
  preferred candidate wins by construction. Relock weights before
  scoring and retry.
- **Third pass** should stabilize.

If the third pass does not stabilize, one of these is true:

1. **The problem analysis is under-specified.** Properties from PSE
   Phase 6 that looked binary are actually fuzzy, and every
   candidate lands in "Uncertain" for the same cells. Return to PSE
   Phase 6 and tighten the violation tests.
2. **The candidate set is missing a fundamentally different
   architecture.** Return to C2 with a deliberately different
   starting premise (e.g., "assume we cannot build this and must
   buy it" or the inverse).
3. **The problem class is wrong.** The weights that feel correct in
   C4 do not match the weights implied by the declared problem class.
   Return to the PSE Problem Class Declaration.

### Re-Analysis Events

The framework is paused, not edited, when any of the following occur:

- The problem class changes (e.g., POC becomes Enterprise).
- A mandatory property is discovered to be incorrect.
- A new stakeholder is identified whose constraints were not in the
  original analysis.
- External conditions (regulatory, market, technical) invalidate an
  assumption that a candidate depended on.

In each case, return to the PSE framework, revise the problem
analysis explicitly, and restart this framework from C1. Do not
patch the convergence document to accommodate the change.

---

## This Framework Is Not an Implementation

If the output of this framework reads like code, a data model, or an
API contract, Phase C7 has over-reached. The output is a
specification with verification criteria. Implementation is a
downstream activity, governed by whatever engineering practices the
team uses, and falls outside the scope of problem-to-solution
reasoning.

If the output of this framework reads like a product spec that makes
no reference to the problem analysis, Phase C0 was not applied
rigorously enough. Return to C0 and audit each phase against the
reverse-contamination signals.
