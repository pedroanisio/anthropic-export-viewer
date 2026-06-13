# Generalizability Methods Reference

## Table of contents

1. Dependency taxonomy — detailed definitions and edge cases
2. Mode B taxonomy — candidate preconditions and the π_def/π_par split
3. Parameterization protocol — step-by-step procedure
4. Counterexample search strategies — systematic methods
5. Invariant characterization — formal construction
6. Induced class discovery (Mode B) — from preconditions to a named class
7. Category-theoretic lens — when and how to apply
8. Domain-specific patterns — common generalizability shapes by field
9. Worked examples (Mode A and Mode B)

---

## 1. Dependency taxonomy

### 1.1 Structural dependencies (σ)

A dependency is structural if and only if it is entailed by the
definition of C. To verify: ask "If I removed this property, would the
resulting object still be a member of C?" If removing it expels the
object from C, the dependency is structural.

**Test:** ∀x ∈ C: σ(x) is true. If this holds by the definition of C,
it's structural.

**Subtlety:** Some properties are structural but non-obvious. A graph
being "finite" is structural for the class "finite graphs" but
accidental for "graphs." Always check the class definition carefully.

### 1.2 Accidental dependencies (α)

A dependency is accidental if there exists at least one member of C
for which it does not hold.

**Test:** ∃x ∈ C: ¬α(x). If you can construct such an x (even
hypothetically), the dependency is accidental.

**The critical question:** Does the solution use this property in a
load-bearing way? A solution might *mention* an accidental property
without depending on it (e.g., "let n = 7" where n could be anything).
The parameterization test (Phase 2) distinguishes decorative mentions
from genuine dependencies.

### 1.3 Derived dependencies (δ)

A derived dependency follows from one or more root dependencies. The
derivation must be explicit and verifiable.

**Trace rule:** Every δ must have a derivation chain ending at σ or α
roots. If a δ appears to have no root, either:
- There's an implicit dependency you haven't found (reclassify as ι), or
- The derivation is wrong (the property doesn't actually follow).

**Reduction rule:** For generalizability purposes, a δ inherits the
classification of its weakest root. If δ derives from one σ and one α,
δ is effectively accidental (it fails when the α-root fails).

### 1.4 Implicit dependencies (ι)

The most dangerous category. An implicit dependency is one that the
solution uses but never states. Common sources:

- **Convention dependencies**: "integers" meaning "positive integers,"
  "function" meaning "continuous function," "set" meaning "finite set."
- **Type dependencies**: operations that silently require specific types
  (division requiring a field, ordering requiring a total order).
- **Existence dependencies**: assuming a solution exists, a maximum is
  attained, a limit converges, an inverse exists.
- **Uniqueness dependencies**: assuming *the* solution (not *a*
  solution), where multiple could exist.
- **Computability dependencies**: assuming a step can be carried out
  effectively (decidable, terminating, polynomial-time).
- **Finiteness dependencies**: assuming a set is finite, a process
  terminates, a series converges.

**Detection heuristic:** For every step of S, ask: "Under what
conditions could this step fail to be well-defined?" Any such condition
that isn't explicitly stated is an implicit dependency.

---

## 2. Mode B taxonomy — candidate preconditions and the π_def/π_par split

When no problem class C is pre-specified (Mode B), the σ/α distinction
is unavailable — it requires a class to compare against. Instead, all
non-tautological dependencies are initially classified as candidate
preconditions (π).

### 2.1 Candidate preconditions (π)

A candidate precondition is any property of P that S uses and that is
not tautologically true. This is a deliberately broad category. The
analyst's job is to collect them all first, then partition them.

**Exhaustiveness principle:** In Mode B, the precondition list IS the
analysis. Miss a precondition and the induced class will be too broad
(it will include instances where S fails). Include a spurious
precondition and the induced class will be too narrow (it will exclude
instances where S would actually work). Both errors are caught by
Phases 2–3 (parameterization and counterexample search), but starting
with a complete list reduces iteration.

### 2.2 The π_def / π_par partition

After Phases 2–3 have filtered out inert and superficial preconditions,
the surviving ones are partitioned:

**Definitional preconditions (π_def)** define the *kind* of problem:

- **Type constraints**: "the input is a graph," "the function maps ℝ → ℝ"
- **Qualitative structural constraints**: "the graph is connected,"
  "the matrix is symmetric," "the function is continuous"
- **Closure test**: if an instance satisfies π_def and you perturb it
  slightly (in a domain-appropriate sense), does it still satisfy π_def?
  If yes, it's definitional. If a tiny change can violate it, it's
  parametric.

**Parametric preconditions (π_par)** constrain values within a kind:

- **Numeric bounds**: "n < 1000," "k ≥ 2," "ε > 0"
- **Specific structural values**: "the graph has exactly 3 components,"
  "the matrix has rank ≤ 5"
- **Fragility test**: can you construct a nearby instance that violates
  π_par but still satisfies all π_def? If yes, it's parametric.

### 2.3 Ambiguous cases

Some preconditions resist clean partition:

- "The graph is planar" — definitional or parametric? It defines a
  qualitative structural kind (definitional) but is also a constraint
  that can be violated by adding a single edge (parametric-like).
  **Resolution:** if the property has an established name and is closed
  under natural substructure operations (subgraphs of planar graphs
  are planar), classify as definitional.

- "The weights are positive" — qualitative (definitional) or a bound
  on a continuous parameter (parametric)? **Resolution:** if it
  partitions the space into two qualitatively different regimes
  (positive weights enable shortest-path algorithms; negative weights
  break them), classify as definitional.

When in doubt, classify as definitional and note the ambiguity. It's
better to induce a slightly narrower class than to induce one that
includes instances where S fails.

---

## 3. Parameterization protocol

### 2.1 Procedure

For each accidental dependency αᵢ identified in Phase 1:

```
1. Let v = concrete value used by S for αᵢ
2. Let V = domain of all values v could take within C
3. Replace v with v̂ ∈ V (free variable)
4. Re-execute S symbolically with v̂ in place of v
5. At each step, check: does the step's logic depend on v̂
   having a specific value, or does it work for arbitrary v̂ ∈ V?
6. If a step breaks:
   a. Identify the minimal property Q of v that the step needs
   b. Record: "αᵢ breaks at step X; requires Q(v̂)"
   c. Determine: {v̂ ∈ V : Q(v̂)} — what fraction of V satisfies Q?
7. If no step breaks: "αᵢ survives parameterization — superficial"
```

### 2.2 Symbolic vs. concrete execution

Prefer symbolic execution (working with v̂ as a formal variable) where
possible. Fall back to concrete sampling when:
- S involves iterative/recursive processes too complex for symbolic
  tracing.
- The dependency is high-dimensional (e.g., a matrix, a function, a
  graph structure).

For concrete sampling, test at minimum:
- The extreme values of V (min, max if ordered; empty, universal if
  set-valued).
- A generic/typical value.
- A value that maximally differs from the original v.

### 2.3 Sensitivity grading

After parameterization, grade each αᵢ:

| Grade | Meaning |
|-------|---------|
| **S0 (inert)** | S doesn't actually use αᵢ at all — a red herring |
| **S1 (superficial)** | S mentions αᵢ but works for any value in V |
| **S2 (mild)** | S needs Q(v̂) where {v̂ : Q(v̂)} covers most of V |
| **S3 (moderate)** | S needs Q(v̂) where {v̂ : Q(v̂)} is a significant proper subset |
| **S4 (severe)** | S needs Q(v̂) where {v̂ : Q(v̂)} is a small or trivial subset |
| **S5 (fatal)** | S needs Q(v̂) where Q(v̂) is satisfied essentially only by v itself |

S0–S1 dependencies don't block generalization. S2–S3 produce
conditional generalization. S4–S5 signal ad hoc solutions.

---

## 4. Counterexample search strategies

### 3.1 Boundary cases

For every parameter or structural element of C, identify its extremal
values. Construct instances of C at these extremes.

**For numeric parameters (n, k, dimension, size):** Test n = 0, n = 1,
n = 2 (first non-trivial), and n → ∞ (asymptotic behavior).

**For structural parameters (graph shape, function class):** Test the
simplest possible structure, the most complex, and the most degenerate
(e.g., complete graph, star graph, disconnected graph).

### 3.2 Degenerate cases

Identify which structural properties of P the solution S "leans on" and
construct instances where those properties vanish:

| S relies on | Degenerate instance to test |
|------------|---------------------------|
| Connectivity | Disconnected input |
| Non-singularity | Singular / rank-deficient input |
| Strict monotonicity | Constant or non-monotone input |
| Uniqueness of optimum | Input with multiple optima |
| Smoothness | Non-differentiable input |
| Full rank | Rank-deficient input |
| Finiteness | Infinite (or arbitrarily large) input |
| Non-emptiness | Empty input |
| Positive-definiteness | Semi-definite or indefinite input |

### 3.3 Symmetry breakers

If S exploits any symmetry — commutativity, associativity, isotropy,
exchangeability, time-reversibility — construct an instance where that
symmetry is absent.

**Detection:** Symmetry exploitation often hides behind phrases like "by
symmetry," "WLOG," "by the same argument," or steps that swap, permute,
or reverse without justification. Each such phrase is a candidate for
a symmetry-breaking counterexample.

### 3.4 Adversarial constructions

Use the preconditions Q identified in Phase 2 to construct instances
that violate exactly one precondition at a time (holding all others
fixed). This isolates which preconditions are genuinely necessary vs.
which are artifacts of conservative analysis.

**Method:**
1. Start from P (the original instance, where S works).
2. For each Qᵢ, modify P minimally to violate Qᵢ while keeping
   Q₁, …, Qᵢ₋₁, Qᵢ₊₁, …, Qₖ intact.
3. Run S on the modified instance.
4. If S still works: Qᵢ was not truly necessary — remove it from
   the precondition set.
5. If S fails: Qᵢ is confirmed necessary. Record the failure mode.

---

## 5. Invariant characterization

### 4.1 Formal construction

Given the confirmed necessary preconditions Q₁, …, Qₖ from Phases 2–3:

1. Express each Qᵢ as a predicate on the input space of C:
   Qᵢ: InputSpace(C) → {true, false}

2. Define the invariant set:
   I = {x ∈ C : Q₁(x) ∧ Q₂(x) ∧ … ∧ Qₖ(x)}

3. Determine the measure of I relative to C:
   - If C and I are finite: |I| / |C|
   - If C is a topological space: is I open, closed, dense, meager,
     full-measure, null-measure?
   - If C has no natural measure: characterize I structurally (a known
     subclass, a parametric family, etc.)

### 4.2 Naturality test

A subclass is **natural** if it satisfies at least one of:
- It has an established name in the literature.
- It is closed under the natural operations of C (if C has algebraic
  structure, is I a sub-algebra? if C is a category, is I a
  subcategory?).
- It arises from an independent motivation unrelated to S.
- It is defined by a property simpler than S itself.

A subclass is **artificial** if:
- Its only defining property is "the set of inputs where S works."
- Removing any single Qᵢ makes I non-closed under C's natural
  operations.
- It corresponds to no recognized concept in the field.

### 4.3 Gap analysis

For C \ I (the gap where S fails):

1. **Size**: What fraction of C does the gap represent?
2. **Importance**: Does the gap contain practically relevant instances?
   (A gap consisting only of pathological cases may be acceptable.)
3. **Structure**: Is the gap itself a natural subclass? If so, it
   may require a fundamentally different solution method.
4. **Boundary**: Is the boundary between I and C \ I sharp (a clear
   predicate) or fuzzy (gradual degradation of S's performance)?

---

## 6. Induced class discovery (Mode B)

### 6.1 From preconditions to a class

The definitional preconditions π_def₁, …, π_defⱼ collectively define:

  C* = {all problems satisfying π_def₁ ∧ … ∧ π_defⱼ}

This is the solution's **induced class** — the broadest natural class
over which S has a chance of working (parametric restrictions aside).

### 6.2 Naming the class

Check whether C* matches a known class:

1. **Exact match**: C* corresponds to a named class in the literature
   (e.g., "connected planar graphs," "convex optimization problems,"
   "linear time-invariant systems"). If so, state the name and cite
   the correspondence.
2. **Subset of a known class**: C* is a refinement of a known class
   with additional constraints. State both the parent class and the
   additional constraints (e.g., "symmetric positive-definite matrices
   with bounded condition number" — parent: SPD matrices; additional:
   bounded condition number).
3. **No known match**: C* doesn't correspond to anything standard. This
   is itself a finding. Either:
   - The solution has discovered a genuinely new problem class worth
     naming (rare but valuable).
   - The preconditions are ad hoc and don't carve a natural boundary
     (more common — signals a fragile solution).

### 6.3 Validation of the induced class

Even after naming C*, verify:

- **Forward check**: pick 3–5 members of C* that are NOT P and were not
  used in counterexample search. Run S on them (or trace S through them).
  Do they all work? If any fail, a precondition is missing.
- **Boundary check**: pick 3–5 instances just outside C* (violating
  exactly one π_def). Confirm S fails on them. If any succeed, a
  precondition is unnecessarily restrictive.
- **Independence check**: for each π_defᵢ, ask whether dropping it
  while keeping all others still yields a class where S works. If yes,
  π_defᵢ is redundant and C* can be expanded.

---

## 7. Category-theoretic lens

Use this perspective when the problem class C has morphisms (maps
between instances that preserve structure) — i.e., when C is naturally
a category, not just a set.

### 5.1 When to apply

Apply the category-theoretic lens when:
- C has a notion of "structure-preserving map" between instances
  (homomorphisms, isomorphisms, embeddings, etc.).
- S can be expressed as a function from instances to solutions:
  S: Ob(C) → Ob(D) for some target category D.
- The question is whether S "respects" the morphisms of C.

### 5.2 Natural transformation test

If S is a functor (or can be lifted to one), check whether the
solution assignment forms a natural transformation:

For every morphism f: P₁ → P₂ in C, does the diagram commute?

```
    S(P₁) ----S(f)---→ S(P₂)
      |                    |
    η_P₁               η_P₂
      |                    |
      ↓                    ↓
    T(P₁) ----T(f)---→ T(P₂)
```

If it commutes for all f: S is **natural** — it generalizes by
construction, because it doesn't depend on the specific identity of
objects, only on structural relationships.

If it fails to commute: identify the specific morphisms where
commutativity breaks. These are the "generalization obstructions."

### 5.3 When NOT to apply

Do not force category theory when:
- The problem class is a flat set with no natural morphisms.
- The solution is purely numeric/computational with no algebraic
  structure.
- The added abstraction would obscure rather than clarify.

State explicitly if you skip this lens and why.

---

## 8. Domain-specific patterns

### 6.1 Algorithms / Computer science

Common generalizability failures:
- **Hardcoded constants** that should be parameters.
- **Input size assumptions** (works for n < 1000 but not n = 10⁶).
- **Data type assumptions** (works for integers, fails for floats due
  to precision).
- **Structural assumptions** (works for trees, fails for general graphs;
  works for sorted input, fails for unsorted).

Typical invariant sets: sublinear inputs, sparse instances, bounded
treewidth, planar graphs, monotone functions.

### 6.2 Mathematics / Proofs

Common generalizability failures:
- **Dimension-specific** arguments (works in ℝ² but not ℝⁿ).
- **Field-specific** arguments (works over ℝ but not ℚ or finite
  fields).
- **Finiteness arguments** that don't extend to infinite cases.
- **Compactness arguments** that require specific topological properties.

Typical invariant sets: finite-dimensional spaces, compact manifolds,
separable spaces, Noetherian rings.

### 6.3 Engineering / Design solutions

Common generalizability failures:
- **Scale dependencies** (works for prototype, fails at production scale).
- **Environmental assumptions** (works under specific temperature,
  pressure, load conditions).
- **Material assumptions** (works for steel, fails for composites).
- **Interface assumptions** (works with specific API version, protocol,
  or data format).

Typical invariant sets: linear regime, small-signal regime, steady-state
conditions, specific material classes.

### 6.4 Business / Strategy

Common generalizability failures:
- **Market-specific** (works in US market, fails in EU due to
  regulation).
- **Scale-specific** (works for startups, fails for enterprises or
  vice versa).
- **Timing-specific** (worked in 2020 conditions, fails in 2025
  conditions).
- **Survivorship bias** (looks general because you only see the cases
  where it worked).

Typical invariant sets: specific market segments, regulatory regimes,
organizational sizes, maturity stages.

---

## 9. Worked examples

### 9.1 Mode A — Simple mathematical example

**Problem instance P:** Prove that x² + 6x + 9 ≥ 0 for all real x.

**Solution S:** Factor as (x + 3)², which is a perfect square, hence
non-negative.

**Problem class C:** Prove that ax² + bx + c ≥ 0 for all real x,
where a, b, c ∈ ℝ.

**Phase 1 — Dependencies:**
- σ₁: The expression is a quadratic in x (structural — defines C).
- α₁: a = 1 (accidental — C allows any real a).
- α₂: b = 6 (accidental).
- α₃: c = 9 (accidental).
- ι₁: The quadratic factors as a perfect square (implicit — S relies
  on this but doesn't state it as a general requirement).

**Phase 2 — Parameterization:**
- α₁ (a = 1): Parameterize to general a. If a < 0, the quadratic
  opens downward → unbounded below → cannot be ≥ 0 for all x. If a = 0,
  it's linear, not quadratic. **Breaks. Requires a > 0.**
- α₂, α₃ (b = 6, c = 9): Together with a = 1, these give
  discriminant b² − 4ac = 36 − 36 = 0. For general b, c with a > 0:
  need b² − 4ac ≤ 0 for the quadratic to be non-negative everywhere.
  **Breaks. Requires b² ≤ 4ac.**

**Phase 3 — Counterexamples:**
- x² + 6x + 1: discriminant = 32 > 0 → has real roots → goes negative.
  Confirms b² ≤ 4ac is necessary.
- −x² + 6x + 9: a < 0 → goes to −∞. Confirms a > 0 is necessary.

**Phase 4 — Invariant set:**
I = {(a, b, c) ∈ ℝ³ : a > 0 ∧ b² ≤ 4ac}

This is a natural subclass: it's exactly the positive semi-definite
quadratic forms, a well-studied object in linear algebra.

**Phase 5 — Verdict:** Conditional generalization. The factoring method
(or its generalization: completing the square) works for all positive
semi-definite quadratics, which is a natural and important subclass.

### 9.2 Mode A — Algorithmic example

**Problem instance P:** Sort the array [3, 1, 4, 1, 5] using the
observation that all elements are single digits.

**Solution S:** Use counting sort with a 10-element count array.

**Problem class C:** Sort an array of n integers.

**Phase 1 — Dependencies:**
- σ₁: Input is an array (structural).
- σ₂: Elements are integers (structural — by definition of C).
- α₁: Elements are in range [0, 9] (accidental).
- ι₁: The range of elements is small relative to n (implicit —
  counting sort's time complexity depends on this).

**Phase 2 — Parameterization:**
- α₁: Parameterize to range [0, k]. Counting sort works for any k,
  but time is O(n + k). If k = O(n), time is O(n) — fine. If k ≫ n
  (e.g., 64-bit integers), time and space become O(k) which is
  impractical. **Sensitivity: S3 (moderate).** Requires max(elements)
  to be manageable.

**Phase 3 — Counterexamples:**
- Array of 10 elements where values are 64-bit integers spanning
  [0, 2⁶³]. Counting sort requires 2⁶³ memory — infeasible. Hard
  failure.

**Phase 4 — Invariant set:**
I = {arrays of n integers with range k where k = O(n)}
This is a natural subclass (bounded-range integer sorting), and
counting sort is the textbook algorithm for exactly this class.

**Phase 5 — Verdict:** Conditional generalization over bounded-range
integer arrays. Easily extensible: radix sort extends the approach to
larger ranges by decomposing into digit-level counting sorts, expanding
I to all integer arrays (with O(n · w) time for w-bit integers).

### 9.3 Mode B — Solution-first example (discovering the class)

**Problem instance P:** A startup built a recommendation engine that
works by computing cosine similarity between user-item interaction
vectors and returning the top-k most similar items.

**Solution S:** Cosine-similarity-based k-nearest-neighbor retrieval
over sparse user-item matrices.

**Problem class C:** Unknown — the startup asks "what class of
recommendation problems does our engine actually solve?"

**Phase 0 (Mode B):**
- P: Recommend items to users based on historical interaction data
  (binary: viewed / not viewed).
- S: Cosine similarity on sparse binary vectors, top-k retrieval.
- C = ? (to be determined)

**Phase 1 — Candidate preconditions (π):**
- π₁: User-item interactions are representable as vectors (used by
  the inner product in cosine similarity).
- π₂: Interactions are binary (viewed / not viewed) — cosine similarity
  on binary vectors reduces to the Jaccard-like overlap measure.
- π₃: The interaction matrix is sparse (S uses sparse data structures;
  dense matrices would be handled differently).
- π₄: Similarity is a meaningful proxy for preference (the core
  assumption: users who interacted with similar items have similar
  tastes).
- π₅: The item catalog is static during retrieval (S doesn't handle
  real-time item additions).
- π₆: k is small relative to catalog size (top-k retrieval is efficient
  only when k ≪ |items|).
- ι₁: No cold-start handling (new users with no interactions get zero
  vectors — cosine similarity is undefined for the zero vector).
- ι₂: Interaction counts don't matter, only presence/absence (implicit
  in using binary vectors rather than count/rating vectors).

**Phase 2 — Parameterization:**
- π₂ (binary interactions): Replace with real-valued ratings (1–5
  scale). Cosine similarity still computes but now measures a different
  thing — angular similarity of rating profiles rather than interaction
  overlap. S still "runs" but the semantic interpretation changes.
  **Sensitivity: S2 (mild).** Works but with shifted semantics.
- π₃ (sparse matrix): Replace with dense matrix. S still works but
  performance degrades from O(nnz) to O(n·m). **Sensitivity: S2
  (mild).** Functional but impractical at scale.
- π₅ (static catalog): Allow real-time item additions. S requires
  recomputation of similarity for new items. **Sensitivity: S3
  (moderate).** Requires architectural modification for streaming.
- ι₁ (no cold start): Introduce users with 0 interactions. Cosine
  similarity fails (0/0). **Sensitivity: S5 (fatal)** for those users.

**Phase 3 — Counterexamples:**
- Cold-start user: new user, no interactions. S returns nothing or
  errors. Hard failure. Confirms ι₁.
- Implicit feedback with heavy-tail distribution: a few items have
  millions of interactions, most have single digits. Cosine similarity
  is dominated by popular items. S returns popular items for everyone
  — degenerates into a popularity-based recommender. Soft failure
  (technically "works" but loses personalization).
- Context-dependent preferences: user likes horror movies at night,
  comedies in the morning. Binary interaction vectors collapse this
  temporal structure. Soft failure.

**Phase 4 — Partition and induced class:**

Definitional preconditions (π_def):
- π₁: Interactions are vector-representable
- π₄: Interaction overlap is a meaningful similarity signal
- ι₂: Interaction is binary or binarizable (presence/absence)

Parametric preconditions (π_par):
- π₃: Matrix is sparse (performance constraint, not correctness)
- π₅: Catalog is static or slowly changing
- π₆: k ≪ |items|
- ι₁: No zero-interaction users (or they're handled separately)

Induced class C*: **Binary collaborative filtering on established users
with implicit feedback.** This is a recognized subfield of recommender
systems. It covers scenarios like "users who viewed these items also
viewed…" where the signal is binary engagement, the user base has
history, and the item catalog is relatively stable.

Naturality test: C* matches the standard definition of item-based
collaborative filtering with implicit feedback — a well-studied,
named class in the recommender systems literature. **Natural.**

**Phase 5 — Verdict: Natural scope.** The solution's induced class is
a recognized problem category. Limitations are clear: cold start,
context-dependence, and heavy-tail popularity bias fall outside C*.

**Extensibility:** The cold-start gap (ι₁) is addressable by hybrid
methods (content-based fallback for new users). The popularity bias
is addressable by TF-IDF-style reweighting of the interaction vectors.
Both are modifications to S within the same algorithmic family. The
context-dependence gap is structurally blocked — it requires a
fundamentally different representation (tensor factorization, sequence
models), not a tweak to cosine similarity.
