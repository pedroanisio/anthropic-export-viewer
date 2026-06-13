---
name: formal-completeness-checker
description: >
  Formalize any natural-language proposition, argument, policy document, spec,
  or contract into mathematical logic and then verify whether it covers all
  computable cases in its state space. Use this skill whenever the user asks to
  "formalize", "prove completeness of", "check all cases", "verify
  exhaustiveness", "find logical gaps", "model-check", or "turn into math" any
  document or proposition. Also trigger on phrases like "does this cover
  everything?", "are there edge cases?", "is this logically complete?", "formal
  verification", "case analysis", "decision matrix", or any request to convert
  prose into formal definitions and check whether the definitions leave
  unhandled scenarios. If the user uploads a document and asks whether it is
  "sound", "airtight", "exhaustive", or "covers all possibilities", use this
  skill. Even partial requests like "formalize section 3" or "what cases does
  this policy miss?" should trigger it.
---

# Formal Completeness Checker

## What this skill does

Given any natural-language document or proposition, this skill guides a
systematic pipeline:

1. **Extraction** — decompose the text into atomic propositions and compound
   claims.
2. **Formalization** — translate each claim into a well-formed formula in an
   appropriate logic (propositional, first-order, or typed).
3. **Domain classification** — determine whether the resulting state space is
   finite (decidable by enumeration), structured-infinite (decidable by
   structural induction or partitioning), or genuinely undecidable.
4. **Completeness analysis** — for the decidable fragment, enumerate or
   partition the full case space and check whether the formalized claims
   collectively assign a verdict to every point.
5. **Gap report** — produce a formal document listing uncovered cases,
   contradictions, redundancies, and the decidability boundary.

The output is always a Markdown document with a frontmatter disclaimer (per
user preferences) and full formal definitions.

## Theoretical grounding — read this first

Before beginning any formalization, read `references/formalization-guide.md`.
It contains the logic taxonomy, translation heuristics, and worked examples
that prevent the most common formalization errors.

Before beginning completeness analysis, read
`references/completeness-methods.md`. It contains the case-matrix
construction, partition methods, and the decidability boundary rules.

**Both files are mandatory reading before producing any output.**

## The pipeline in detail

### Phase 1 — Extraction

Read the entire input document. Produce a **claim inventory**: a numbered,
flat list of every distinct claim the document makes. A "claim" is any
statement that asserts something is true, required, forbidden, conditional,
or universally/existentially quantified.

For each claim, record:
- **ID**: sequential number (C1, C2, …)
- **Source text**: the verbatim sentence or clause
- **Claim type**: assertion, conditional, universal, existential, prohibition,
  obligation, definition, or assumption
- **Dependencies**: which other claims it references or presupposes

Do not skip implicit claims. If the document says "Employees must submit
timesheets weekly," the implicit claims include: employees exist, timesheets
exist, a week is a defined period, submission is a defined action. Extract
these as assumptions and flag them.

### Phase 2 — Formalization

For each claim in the inventory, produce a well-formed formula (WFF). Follow
the logic selection rules in `references/formalization-guide.md`:

1. **Propositional logic** — if the claim involves only Boolean combinations
   of atomic facts with no quantification over a domain.
2. **First-order logic (FOL)** — if the claim quantifies over elements of a
   domain (∀x, ∃x) but the domain is explicit and finite or enumerable.
3. **Typed/sorted FOL** — if multiple domains interact (people, documents,
   dates, amounts).
4. **Temporal logic (LTL/CTL)** — if the claim involves sequences of states,
   "always", "eventually", "until", or process ordering.
5. **Deontic logic** — if the claim involves obligations (O), permissions (P),
   or prohibitions (F) that are not reducible to plain truth values.

**Rules for honest formalization:**
- Every free variable must be explicitly typed with its domain.
- Every domain must be declared finite or infinite with justification.
- Every logical connective must map to a specific natural-language construct
  in the source text. If there is no source text, the formula is an
  *assumption you are introducing* — label it as such.
- If a natural-language claim is genuinely ambiguous between two
  formalizations, produce BOTH and flag the ambiguity. Do not silently
  pick one.

Collect all formulas into a formal system Φ = {φ₁, …, φₙ}.

### Phase 3 — Domain classification

Compute the **state space** S of the formal system:
- Identify all variables {v₁, …, vₘ} and their domains {D₁, …, Dₘ}.
- The raw state space is S = D₁ × D₂ × … × Dₘ.
- If all domains are finite, |S| is finite and computable. State its
  cardinality explicitly.
- If any domain is infinite, classify the system's decidability:
  - **Monadic FOL over finite domains**: decidable.
  - **Propositional**: decidable (2^k states for k variables).
  - **FOL with equality over infinite domains**: semi-decidable
    (complete by Gödel's completeness theorem, but validity is undecidable
    in general by Church-Turing).
  - **Arithmetic (Peano or stronger)**: incomplete by Gödel's first
    incompleteness theorem. Flag this explicitly.

**Be honest about the boundary.** If the system crosses into undecidable
territory, say so. Do not fake a completeness proof. Instead, identify the
maximal decidable fragment and analyze that.

### Phase 4 — Completeness analysis

This phase differs by domain class.

#### 4a — Finite state space (decidable by enumeration)

1. Construct the **full case matrix**: every element of S as a row.
2. For each row, evaluate which formulas in Φ apply (their truth value
   under that assignment).
3. Classify each row:
   - **Covered**: at least one formula in Φ determines a verdict
     (true/false, permitted/forbidden, handled/etc.)
   - **Uncovered (gap)**: no formula in Φ says anything about this case.
   - **Contradicted**: two or more formulas assign conflicting verdicts.
   - **Redundantly covered**: multiple formulas agree on the verdict
     (not a defect, but worth noting for simplification).

4. If |S| > 2¹⁶ (65,536 rows), do NOT attempt to print the full matrix.
   Instead:
   - Use **BDD-style symbolic analysis**: express Φ as a single Boolean
     function and find its satisfying/falsifying assignments symbolically.
   - Or use **partition refinement**: group rows by their formula-coverage
     signature and report by partition class.

5. Report:
   - Total |S|
   - Number and percentage of covered, uncovered, contradicted,
     redundant rows
   - Explicit listing of ALL uncovered cases (if ≤ 50; otherwise
     characterize them as a formula or partition description)
   - Explicit listing of ALL contradictions

#### 4b — Structured-infinite state space (decidable by partition)

If the infinite domain has exploitable structure (e.g., integers partitioned
into negative/zero/positive, or strings partitioned by regex classes):

1. Define a **finite partition** P of S such that all formulas in Φ are
   uniform within each partition class (i.e., if two states are in the
   same class, every formula gives them the same verdict).
2. Verify that P is indeed a valid partition (classes are disjoint and
   exhaustive).
3. Run the finite case matrix analysis from 4a on the partition classes
   instead of individual states.
4. Report the partition scheme and results.

If no finite partition exists that makes Φ uniform, this case is not
decidable by partition. Fall through to 4c.

#### 4c — Undecidable fragment

1. State clearly: "The following portion of the formal system falls
   outside the decidable fragment. Completeness cannot be
   mechanically verified."
2. Identify the specific source of undecidability (quantification over
   an infinite unstructured domain, self-reference, arithmetic, etc.).
3. Identify the **maximal decidable sub-system** — the largest subset
   of Φ that remains decidable — and run 4a or 4b on that subset.
4. For the undecidable remainder, provide:
   - A **best-effort structural argument** for coverage (not a proof,
     clearly labeled as such).
   - Known **necessary conditions** for gaps (if gaps exist, they must
     satisfy these conditions).
   - **Concrete counterexample search**: attempt to find specific
     uncovered cases by sampling or heuristic search. Report findings
     honestly — "no counterexample found" ≠ "no counterexample exists."

### Phase 5 — Output document

Produce a Markdown document with the following structure:

```
---
disclaimer: >
  No information within this document should be taken for granted.
  Any statement or premise not backed by a real logical definition or
  verifiable reference may be invalid, erroneous, or a hallucination.
  All formal definitions herein are the author's translation of the
  source text and may not capture the original intent. Verify
  independently before relying on any conclusion.
title: "Formal Completeness Analysis: [Document Title]"
date: [current date]
method: formal-completeness-checker/v1
---

# Formal Completeness Analysis: [Document Title]

## 1. Source summary
[Brief description of the input document and its apparent purpose.]

## 2. Claim inventory
[Numbered list of all extracted claims with types and dependencies.]

## 3. Formal system
### 3.1 Domains
[Declaration of all domains with cardinality / decidability status.]

### 3.2 Variables
[All variables with their types.]

### 3.3 Formulas
[Each formula φᵢ with its source claim ID, formal expression, and
any ambiguity notes.]

## 4. State space
[Cardinality, classification (finite / structured-infinite /
undecidable), justification.]

## 5. Completeness results

### 5.1 Coverage summary
[Table: total cases, covered, uncovered, contradicted, redundant.]

### 5.2 Uncovered cases (gaps)
[Explicit listing or characterization.]

### 5.3 Contradictions
[Explicit listing with the conflicting formulas.]

### 5.4 Decidability boundary
[What was provably checked vs. what remains unverifiable.]

## 6. Recommendations
[Suggested additions or modifications to close gaps, resolve
contradictions, or clarify ambiguities.]

## Appendix A: Full case matrix
[If |S| ≤ 256, include the full matrix. Otherwise, include the
partition-class matrix or a representative sample.]

## Appendix B: Proof sketches
[For any structural arguments in 4c, include the reasoning.]
```

## Critical constraints

1. **Never claim completeness you cannot demonstrate.** If the domain
   is undecidable, say so. If the formalization is ambiguous, say so.
   Epistemic honesty is non-negotiable.

2. **Never hallucinate formal definitions.** Every formula must trace
   back to source text or be explicitly labeled as an introduced
   assumption.

3. **The disclaimer frontmatter is mandatory.** Per user preferences,
   every output document must warn that unverified content may be
   invalid.

4. **Ambiguity is a finding, not a failure.** If the source text is
   ambiguous, reporting that ambiguity IS the valuable output. Do not
   resolve ambiguity by silent choice.

5. **Scale to the document.** A one-sentence proposition gets a
   one-page analysis. A 50-page policy document gets a proportional
   treatment. Do not produce a 30-page report for "if it rains, bring
   an umbrella."

## Common pitfalls

- **Confusing completeness and consistency.** Completeness = every case
  has a verdict. Consistency = no case has contradictory verdicts. Check
  both but report them separately.
- **Ignoring implicit negation.** If a policy says "employees in
  department A get benefit X," does the absence of a rule for department
  B mean they do NOT get benefit X (closed-world assumption) or that the
  policy is silent (open-world)? Always ask. If you cannot ask, analyze
  under BOTH assumptions and report the difference.
- **Over-formalizing.** Not every English sentence needs its own formula.
  Definitions and assumptions can be folded into domain declarations.
  Only claims that assert something about the state space need formulas.
- **Under-formalizing.** Conversely, do not skip claims because they
  seem "obvious." Obvious claims are the ones most likely to harbor
  unstated exceptions.
