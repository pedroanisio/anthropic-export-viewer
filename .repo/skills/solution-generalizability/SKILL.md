---
name: solution-generalizability
description: >
  Analyze whether a solution generalizes across a problem class or is ad hoc.
  Produces a verdict (full / conditional / fragile / ad-hoc) via dependency
  extraction, parameterization testing, counterexample search, and invariant
  characterization. Trigger on "does this generalize?", "is this a general
  solution?", "will this work for all cases?", "is this ad hoc?", "can we
  extend this?", "is this a one-off?", "what class of problems does this
  solve?", "when does this break?", "what assumptions does this depend on?",
  "is this robust?", "does this always work?", "can I reuse this approach?",
  or any request to assess whether a solution extends beyond its original
  instance. If the user has a solution and wants to know its scope, use this
  skill.
---

# Solution Generalizability Analyzer

## What this skill does

Given a solution S to a problem instance P, this skill determines:

1. **Whether S generalizes** to an entire problem class C that P belongs to.
2. **If not, exactly why** — which dependencies on accidental properties
   prevent generalization.
3. **The maximal subclass** I ⊆ C over which S does generalize.
4. **What modifications** (if any) would extend S to cover all of C.

The output is a Markdown document with a formal generalizability verdict,
dependency map, counterexample inventory, and scope diagram.

## The constitutive principle

A solution does not "become general" on its own. Generalization is always
a relation between a solution and a problem class:

  S generalizes ⟺ ∃C (problem class) such that ∀P ∈ C: S(P) is correct

The pair (S, C) is the unit of analysis. This means the question "does S
generalize?" is incomplete — it must be "does S generalize *over C*?"

This has a non-obvious consequence: the analysis can run in two
directions, and they produce different results.

## Two modes of analysis

### Mode A — Problem-first ("does S cover C?")

The user has both a solution S and a target problem class C (or can
state one). The question is whether S reaches all of C.

Direction: C is given → extract S's dependencies → check if they're
structural (guaranteed by C) or accidental (not guaranteed).

Use this mode when:
- The user explicitly names a class ("does this work for all graphs?").
- There is an obvious, natural class that P belongs to.
- The user's intent is to validate S against a known scope.

### Mode B — Solution-first ("what class does S define?")

The user has a solution S but no specific target class. The question is:
what is the largest natural class over which S works?

Direction: extract S's dependencies → the invariant set I *becomes* the
class definition → check if I is natural or artificial.

Use this mode when:
- The user asks "what does this work for?" without naming a target.
- The user asks "what class of problems does this solve?"
- There is no obvious target class, or the user is exploring.
- The user has a technique and wants to discover its natural scope.

### Mode detection

If the user supplies or implies a target class → Mode A.
If the user asks about scope without a target → Mode B.
If ambiguous, default to Mode A with the most natural class and note
that Mode B is available. In Mode B, Phase 0 is abbreviated: only P
and S are stated; C is left as "to be determined by analysis."

## Theoretical grounding — read this first

Before beginning any analysis, read `references/generalizability-methods.md`.
It contains the dependency taxonomy, parameterization protocol, counterexample
search strategies, and the invariant characterization method. These prevent
the most common analytical errors (confusing structural with accidental
properties, missing implicit dependencies, premature generalization claims).

**This file is mandatory reading before producing any output.**

## The pipeline

### Phase 0 — Problem class identification

**Mode A (problem-first):**

1. **State the specific problem instance** P that the solution addresses.
   Be precise — include all given data, constraints, and the goal.
2. **State the problem class** C — the set of all problems "of the same
   kind." This requires a judgment call: define C by listing the
   structural signature (input types, constraint shapes, objective form)
   that any member must satisfy.
3. **State the solution** S — the method, algorithm, construction, proof
   technique, or strategy being analyzed.

If the user's description of C is vague, make the class explicit and flag
the choice. If there are multiple reasonable definitions of "the problem
class," analyze under the most natural one but note the alternatives.

**Mode B (solution-first):**

1. **State P** — same as Mode A.
2. **State S** — same as Mode A.
3. **State C = ?** — explicitly mark the problem class as unknown. Write:
   "The problem class is not pre-specified. The analysis will derive it
   from the solution's dependency structure."

In Mode B, Phases 1–3 proceed without a reference class. The dependency
taxonomy shifts: instead of "structural vs. accidental" (which requires
knowing C), all non-trivial dependencies are initially classified as
**candidate preconditions** (π). Phase 4 then partitions the π set into
those that define a natural class vs. those that are artificial, and the
natural ones collectively define C* — the solution's induced class.

### Phase 1 — Dependency extraction

Decompose S into the atomic facts about P that it consumes. For each
fact, classify it.

**Mode A classification** (C is known):

| Symbol | Category | Definition | Example |
|--------|----------|-----------|---------|
| **σ** | **Structural** | True of every member of C by definition of C | "The input is a graph" |
| **α** | **Accidental** | True of P but not guaranteed across C | "The graph has exactly 7 nodes" |
| **δ** | **Derived** | Follows logically from other dependencies | "The graph has an odd number of nodes" (follows from α) |
| **ι** | **Implicit** | Used by S but never stated; an unstated assumption | "The edge weights are positive" |

**Mode B classification** (C is unknown):

| Symbol | Category | Definition | Example |
|--------|----------|-----------|---------|
| **τ** | **Tautological** | True by definition of the terms involved (logic, not domain) | "A set either contains x or it doesn't" |
| **π** | **Candidate precondition** | Any non-tautological fact S uses | "The graph is connected," "n = 7," "weights are positive" |
| **δ** | **Derived** | Same as Mode A | Same as Mode A |
| **ι** | **Implicit** | Same as Mode A | Same as Mode A |

In Mode B, the σ/α distinction is deferred to Phase 4. Every
non-tautological dependency starts as π. The point: without a class
to compare against, you cannot yet say what is "structural." You can
only list what S needs.

**Rules for honest dependency extraction:**

- Every step of S must be traced to the facts it requires. If a step
  "just works" without justification, there is an implicit dependency.
  Find it.
- Derived dependencies must be traced to their roots (structural or
  accidental). The root classification is what matters.
- If a dependency is ambiguous (could be structural or accidental
  depending on how C is defined), flag the ambiguity — do not silently
  resolve it.

Produce a **dependency table**: one row per dependency, columns for ID,
statement, category (σ/α/δ/ι), used-by (which steps of S), and root
(for δ dependencies).

### Phase 2 — Parameterization test

For every accidental dependency α found in Phase 1:

1. **Replace** the concrete value with a free variable ranging over all
   values possible within C.
2. **Trace the solution** S with this free variable and identify the
   first step that breaks — the step where the argument, construction,
   or computation no longer follows.
3. **Record** the breaking point and what property of the concrete value
   the step actually needed.

This produces a **parameterization report**: for each α, either "S
survives parameterization" (the dependency was superficial — S works
for any value) or "S breaks at step X because it requires property Q
of the concrete value."

If ALL accidental dependencies survive parameterization, S is a strong
generalization candidate. If ANY break, identify the required property
Q — this becomes a precondition.

### Phase 3 — Counterexample search

Actively construct members of C where S fails. Strategies (apply in
order, escalating in adversarial intensity):

1. **Boundary cases** — members of C at the extremes of any continuous
   parameter (n=0, n=1, n→∞, empty inputs, maximal inputs).
2. **Degenerate cases** — members where some structure that S relies on
   collapses (disconnected graph, zero-measure set, singular matrix,
   constant function).
3. **Symmetry breakers** — members where an implicit symmetry that S
   exploits does not hold (asymmetric inputs, non-commutative
   operations, non-uniform distributions).
4. **Adversarial constructions** — members specifically designed to
   violate the preconditions identified in Phase 2.

For each counterexample found:
- State the instance explicitly.
- Identify exactly which step of S fails and why.
- Classify the failure as **hard** (S produces a wrong answer or no
  answer) or **soft** (S still works but suboptimally or with degraded
  guarantees).

If no counterexample is found after a thorough search, say so honestly
— and state that absence of counterexamples is evidence for but not
proof of generalizability.

### Phase 4 — Invariant characterization

Synthesize Phases 1–3 into a formal precondition set.

#### Mode A (problem-first)

1. Collect all properties Q₁, Q₂, …, Qₖ that Phase 2 identified as
   necessary and Phase 3 confirmed as meaningful (i.e., violating them
   produces counterexamples).
2. State each Qᵢ as a formal predicate over the input space of C.
3. Define the **invariant set** I = {x ∈ C : Q₁(x) ∧ Q₂(x) ∧ … ∧ Qₖ(x)}.
4. Determine the relationship between I and C:
   - **I = C** → S generalizes fully. The Qᵢ are structural properties
     already guaranteed by membership in C.
   - **I ⊂ C, I non-trivial** → S generalizes over a proper subclass.
     Characterize C \ I (the gap) and assess whether it's negligible,
     significant, or dominant.
   - **I is a singleton or near-singleton** → S is essentially ad hoc.
     It works only for P (or instances nearly identical to P).

5. For the case I ⊂ C: determine whether the Qᵢ define a
   **natural subclass** (a recognized, named, or independently motivated
   subset of C) or an **artificial subclass** (a set defined only by
   "the things that make S work," with no independent motivation). The
   former is a meaningful partial generalization; the latter is a sign
   that S is unprincipled.

#### Mode B (solution-first)

In Mode B, there is no pre-given C to compare against. Instead:

1. Collect ALL candidate preconditions π₁, …, πₘ from Phase 1, filtered
   by the parameterization and counterexample results from Phases 2–3
   (drop any πᵢ that proved inert or superficial).
2. Partition the surviving preconditions into two groups:

   **Definitional preconditions (π_def):** Properties that could
   reasonably define a problem class — they describe the *kind* of
   problem, not a specific instance. Indicators:
   - They constrain the type or shape of the input (e.g., "the input
     is a connected graph," "the function is differentiable").
   - They are qualitative, not quantitative.
   - They are closed under reasonable perturbation (slightly modifying
     an instance that satisfies πᵢ still satisfies πᵢ).

   **Parametric preconditions (π_par):** Properties that constrain
   specific values within a problem kind — they distinguish instances
   within a class. Indicators:
   - They fix or bound a numeric parameter (e.g., "n < 100," "k = 3").
   - They are fragile under perturbation.
   - They are quantitative, not qualitative.

3. Define the **induced class**:
   C* = {all problems satisfying π_def₁ ∧ … ∧ π_defⱼ}

   This is the class that S "wants to solve." The parametric
   preconditions then define the invariant set within C*:
   I = {x ∈ C* : π_par₁(x) ∧ … ∧ π_parₖ(x)}

4. Apply the naturality test to C*:
   - Is C* a recognized problem class? Does it have a name?
   - Is C* independently motivated (someone would study it even
     without knowing S)?
   - Is C* closed under the natural operations of the domain?

   If C* is natural → S has discovered its own scope, and that scope
   is meaningful.
   If C* is artificial → S's preconditions don't carve nature at its
   joints. The solution may be fundamentally ad hoc even though it
   "works" on a set of instances.

5. If I ⊊ C* (the parametric preconditions further restrict scope),
   assess whether the parametric restrictions are essential or could
   be relaxed with modifications to S.

### Phase 5 — Generalizability verdict

Produce the final classification.

**Mode A verdicts** (S tested against a given C):

| Verdict | Criterion |
|---------|-----------|
| **Full generalization** | I = C. S works for every member of C with no additional preconditions. |
| **Conditional generalization** | I ⊊ C, I is a natural subclass. S works for a well-motivated subset. |
| **Fragile generalization** | I ⊊ C, I is artificial. S works only under conditions that exist to serve S itself. |
| **Ad hoc (non-generalizable)** | I ≈ {P}. S is instance-specific. |

**Mode B verdicts** (S defines its own class):

| Verdict | Criterion |
|---------|-----------|
| **Natural scope** | C* is a recognized, independently motivated class. S has found its home. |
| **Useful scope** | C* is not a standard class but is coherent and practically useful. |
| **Narrow scope** | C* is coherent but covers only a small or marginal set of instances. |
| **Degenerate scope** | C* ≈ {P}. The preconditions are so specific that the "class" is effectively one instance. |

Additionally, for both modes, assess **extensibility**:
- **Easily extensible**: small, identifiable modifications to S would
  expand I toward C (Mode A) or expand C* (Mode B).
- **Structurally blocked**: the core mechanism of S is incompatible
  with the gap; a fundamentally different approach is needed.

**Cross-mode insight.** When both modes are run (or when one suggests
the other), report the relationship between the user's intended class C
and the solution's induced class C*. Three cases:
- **C ⊆ C***: the solution covers more than the user needed. S is
  "overqualified" — it generalizes beyond the target.
- **C* ⊆ C**: the solution covers less than the user needed. The gap
  C \ C* is the precise scope of the problem.
- **C and C* partially overlap**: the solution covers some things the
  user doesn't need and misses some things they do. This is the most
  interesting case — it often reveals that the user's problem class
  and the solution's natural class are different problems.

### Phase 6 — Scope map

Produce a visual/textual diagram showing the solution's reach.

**Mode A scope map:**

```
C (target problem class — user-defined)
├── I (invariant set — S works here)
│   ├── Structural properties (guaranteed by C)
│   └── Required preconditions Q₁, …, Qₖ
└── C \ I (gap — S fails here)
    ├── Hard failures (wrong answer / no answer)
    └── Soft failures (suboptimal / degraded)
```

**Mode B scope map:**

```
Universe of all problems
├── C* (induced class — defined by S's definitional preconditions)
│   ├── I (invariant set — S works here)
│   │   └── Parametric preconditions π_par₁, …, π_parₖ
│   └── C* \ I (internal gap — S's own class, but parametrically blocked)
└── Outside C* (S's preconditions not met — different problem kind)
```

**Cross-mode scope map** (when both C and C* are known):

```
C ∪ C*
├── C ∩ C* (overlap — S covers what the user needs here)
│   ├── I ∩ C (works and wanted)
│   └── (C ∩ C*) \ I (wanted, in scope, but parametrically blocked)
├── C \ C* (wanted but outside S's natural scope)
└── C* \ C (S covers this, but user doesn't need it)
```

Include concrete representatives of each region.

## Output document

Produce a Markdown document with this structure:

```
---
disclaimer: >
  No information within this document should be taken for granted.
  Any statement or premise not backed by a real logical definition or
  verifiable reference may be invalid, erroneous, or a hallucination.
  All formal claims herein are the author's analysis and may contain
  errors. Verify independently before relying on any conclusion.
title: "Generalizability Analysis: [Solution Name]"
date: [current date]
method: solution-generalizability/v2
mode: [A (problem-first) | B (solution-first)]
verdict: [full | conditional | fragile | ad-hoc | natural-scope | useful-scope | narrow-scope | degenerate-scope]
---

# Generalizability Analysis: [Solution Name]

## 1. Problem class definition
[P, C (or C = ?), and S as defined in Phase 0. State mode used.]

## 2. Dependency map
[The dependency table from Phase 1. σ/α/δ/ι for Mode A; τ/π/δ/ι for Mode B.]

## 3. Parameterization results
[Per-dependency parameterization report from Phase 2.]

## 4. Counterexamples
[All counterexamples found (or honest "none found" statement) from Phase 3.]

## 5. Invariant characterization
[Mode A: The formal precondition set and I vs C analysis from Phase 4.]
[Mode B: The π_def/π_par partition, induced class C*, naturality assessment.]

## 6. Verdict
[Classification and extensibility assessment from Phase 5.]
[If cross-mode: relationship between C and C*.]

## 7. Scope map
[The visual diagram from Phase 6, using the appropriate mode template.]

## 8. Recommendations
[How to close the gap, if applicable. What to try next if S is ad hoc.
 For Mode B: whether C* is worth naming and studying as a class.]
```

## Critical constraints

1. **Never claim generality you cannot demonstrate.** If the analysis
   is incomplete (large C, complex S), state what was checked and what
   was not. "Appears general based on the cases examined" is honest.
   "Generalizes fully" requires either an exhaustive check or a proof.

2. **Never confuse "no counterexample found" with "no counterexample
   exists."** These are different epistemic states. Report them
   differently.

3. **The dependency extraction must be exhaustive.** Every step of S
   must account for its preconditions. If you find yourself writing
   "this step obviously works," stop — that's where the implicit
   dependency lives.

4. **Accidental vs. structural is relative to C.** The same property
   can be structural for one class definition and accidental for another.
   If C is ambiguous, the analysis must say so.

5. **Scale to the solution.** A one-line formula gets a one-page
   analysis. A 200-line algorithm gets proportional treatment. Do not
   produce a 30-page report for "multiply both sides by 2."

6. **The disclaimer frontmatter is mandatory.** Per user preferences,
   every output document must warn that unverified content may be
   invalid.

## Common pitfalls

- **Conflating the two modes.** Mode A asks "does S cover C?" Mode B
  asks "what does S cover?" These have different outputs and different
  verdicts. Do not mix them. If the user supplies a class, use Mode A.
  If they don't, use Mode B. If both are informative, run both
  explicitly and report the cross-mode comparison.
- **Survivorship bias in counterexample search.** Searching only where
  you expect to find counterexamples misses the surprising ones. Apply
  all four strategies from Phase 3 systematically.
- **Confusing the solution with its implementation.** An algorithm may
  fail to generalize, but the underlying *idea* might generalize with
  modifications. Phase 5's extensibility assessment addresses this.
- **Implicit type coercion.** The solution might work because the
  programming language, mathematical convention, or domain silently
  converts types (e.g., integers to reals). This is an implicit
  dependency.
- **Overfitting the problem class (Mode A).** If you define C so
  narrowly that S trivially generalizes, the analysis is vacuous. C
  should be the *natural* class that a practitioner would recognize,
  not one gerrymandered to make S look good.
- **Undergeneralizing the induced class (Mode B).** Conversely, in
  Mode B, don't stop at the first coherent class you find. Check
  whether any of the definitional preconditions are actually droppable
  — the induced class might be larger than the initial precondition
  set suggests.
- **Confusing generalization with correctness.** A solution can be
  correct for P but non-generalizable. It can also be generalizable
  but incorrect. This skill analyzes generalizability, not correctness.
  If correctness is in doubt, flag it but don't conflate the two.
