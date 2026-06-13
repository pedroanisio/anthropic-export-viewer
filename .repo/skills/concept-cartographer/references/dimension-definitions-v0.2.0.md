# Dimension Definitions Reference — Concept Cartographer v0.2.0

---
**Disclaimer**: This document defines a classification framework. No
classification it produces should be taken as absolute truth. Any statement
or premise not backed by a real logical definition or verifiable reference
may be invalid, erroneous, or a hallucination. This framework is a
structured thinking tool, not a source of truth. The formal notation below
is heuristic — it makes intended semantics explicit but is not mechanically
verifiable.
---

## Meta-Properties

### Concept Identity (new in v0.2.0)

A **concept** is: a named, bounded abstraction that can be the subject of
a truth-apt proposition within a specified domain.

**Identity criterion**: Two concept-descriptions refer to the same concept
iff substituting one for the other preserves the truth value of all
propositions expressible in the domain.

**Granularity test**:
1. **Nameable**: Has or can receive a stable label.
2. **Bounded**: You can state what is and is not part of it.
3. **Propositionally productive**: Non-trivial true/false claims can be
   asserted about it within the domain.

If a candidate fails any test, decompose until sub-parts pass, or reject.

### Frame

A **frame** `F = (D, V, P)` where:
- `D` (domain) ∈ { any bounded system, product, field, or organization }
- `V` (viewpoint) ∈ { engineer, business_strategist, end_user, regulator,
  competitor, researcher, operator }
- `P` (purpose) ∈ { product_positioning, ip_strategy,
  communication_planning, competitive_analysis, knowledge_management,
  investment_decision, hiring_priority }

**Rule**: No classification is valid without an explicit frame.

**Frame sensitivity rule** (new in v0.2.0): For each axis, if the
classification would change under a plausible alternative frame, note this.

### Known Axis Correlations (new in v0.2.0)

These axes are **not orthogonal**. The following correlations are expected.
Divergence from expected correlations should be documented and explained —
it is often where strategic insight lives.

| Axis A | Axis B | Expected Correlation |
|---|---|---|
| Maturity (`commoditized`) | Strategic Posture | → `commodity` posture (near-deterministic) |
| Maturity (`theoretical`) | IP Regime | → limits `proprietary_feature` |
| Maturity (`commoditized`) | IP Regime | → limits `trade_secret` |
| Substitutability (`substitutable`) | Strategic Posture | → `commodity` or `enabler` |
| Substitutability (`irreplaceable`) | Strategic Posture | → `differentiator` or `moat` |
| IP Regime (`public_domain`) | Strategic Posture | → incompatible with `moat` in most frames |
| Epistemic Accessibility (audience set) | Application Landscape (audience) | Accessibility constrains reachable audiences |

---

## Axis 1: Structural Role

**What it measures**: The structural relationship between the concept and
the domain's conceptual fabric, along two independent sub-axes.

**What it does NOT measure**: Importance, value, difficulty, or strategic
worth.

### 1a. Decomposition Status

#### `primitive`
**Definition**: A relative stopping point within this domain. Decomposition
yields only terms outside the domain's vocabulary.

This is NOT an intrinsic property. It is a consequence of where the domain
boundary is drawn. "Gradient descent" is `primitive` in ML optimization
(decomposing it yields calculus, which is outside ML's domain) and
`composite` in mathematics (it decomposes into calculus + iterative methods
+ convergence theory, all within mathematics).

**Formal test**: `∀ c ∈ decompose(X, D): c ∉ vocabulary(D)`

#### `composite`
**Definition**: Fully derivable from other concepts in the domain.
Knowledge of the parts and their composition rule is sufficient to
reconstruct the whole and all its properties.

**Formal test**: `∃ {c₁...cₙ} ⊂ D, ∃ f : X = f(c₁...cₙ)` AND
`∀ P : P(X) ↔ derivable(P, {c₁...cₙ}, f)`

**Requirement**: When classifying as `composite`, enumerate the
constituent concepts.

#### `emergent`
**Definition**: Arises from the interaction of other concepts but exhibits
at least one property that is **not derivable** from complete knowledge of
the parts and their composition rule, given current theoretical
understanding.

**Formal test**: `∃ P : P(X) ∧ ¬derivable(P, {c₁...cₙ}, f)` under
current theory.

**Critical distinction from v0.1.0**: This is an **epistemic** claim ("we
currently cannot derive P from the parts"), not a **metaphysical** claim
("P is intrinsically irreducible"). If future theory explains P, the
concept should be reclassified as `composite`. Always note which property
P is and why it is not currently derivable.

**Why the v0.1.0 test was defective**: v0.1.0 tested for "a property the
whole has that no part has" (`∃ P : P(X) ∧ ¬P(cᵢ) ∀ i`). This is
trivially true for any combination of things — a molecule has "molecular
weight" which no individual atom has as "molecular weight." The revised
test requires non-derivability, not mere non-possession.

### 1b. Substitutability Class

**What it measures**: How replaceable this concept is within the domain.

This was `auxiliary` in v0.1.0, incorrectly encoded as a fourth value in
the Decomposition enum. It is independent of decomposition status: a
`primitive` can be `substitutable` (many foundational concepts have
alternatives); an `emergent` can be `irreplaceable`.

| Value | Definition | Heuristic threshold |
|---|---|---|
| `irreplaceable` | No known functional equivalent. Removal destroys capabilities with no recovery path. | Removal requires fundamental domain redesign. |
| `costly_to_replace` | Substitutes exist. Switching is expensive. | > 6 months or > 20% of domain restructuring. |
| `substitutable` | Multiple functional equivalents. Low switching cost. | < 6 months, < 5% restructuring. |

### Decision Procedure

```
Step 1 — Decomposition:
  Can X be decomposed within domain D?
  ├─ No → primitive
  └─ Yes → Are ALL properties of X derivable from parts + composition?
           ├─ Yes → composite
           └─ No → emergent (state the non-derivable property)

Step 2 — Substitutability (independent of Step 1):
  Does a functional equivalent to X exist?
  ├─ No → irreplaceable
  └─ Yes → What is the switching cost?
           ├─ High → costly_to_replace
           └─ Low → substitutable
```

All six combinations (primitive+irreplaceable, primitive+substitutable,
composite+irreplaceable, etc.) are valid.

---

## Axis 2: Strategic Posture

**What it measures**: How the concept should be positioned relative to
competitors, partners, regulators, and the market.

**Key property**: Non-exclusive. Assign weights (0.0–1.0) summing to 1.0.

### Enum Values

#### `differentiator`
Unique competitive advantage. Competitors cannot replicate within a
relevant time horizon.

**Test**: If a competitor had complete knowledge, how long to replicate?
If "meaningfully long" relative to market dynamics → differentiator.

#### `commodity`
Widely known and available. Table stakes.

**Test**: ≥3 competitors have functionally equivalent implementations, OR
taught in standard curricula, OR available open-source.

#### `enabler`
Not valuable alone but unlocks disproportionate value in combination.

**Test**: Removing it blocks ≥2 downstream capabilities.

#### `moat`
Defensible advantage that compounds over time.

**Test**: Exhibits network effects, data flywheels, switching costs, or
scale economies. Advantage grows with usage.

#### `standard` (new in v0.2.0)
Value derives from adoption, not exclusivity. Competing with the standard
is destructive.

**Test**: Industry standard, regulatory requirement, or protocol where
fragmentation reduces total value.

#### `public_good` (new in v0.2.0)
Non-rivalrous and non-excludable. Strategic goal is adoption and
ecosystem health, not protection.

**Test**: Value increases with unrestricted access. Restricting access
reduces total ecosystem value.

### Posture Weights

Instead of "primary" and "secondary" (a binary that v0.1.0 criticized in
others but replicated itself), assign continuous weights:

Example: `differentiator: 0.6, enabler: 0.3, moat: 0.1`

This means the concept's strategic profile is primarily differentiation,
substantially enabling, and slightly moat-like.

---

## Axis 3: IP Regime

**What it measures**: Appropriate intellectual property protection strategy.

**Key change in v0.2.0**: Every regime is now a tuple
`(regime, jurisdiction, confidence)` to address the fact that IP law varies
dramatically across legal systems.

### Enum Values

(Definitions unchanged from v0.1.0. See SKILL.md.)

### Jurisdiction and Confidence

- `jurisdiction`: A named legal jurisdiction (e.g., "US", "EU",
  "China", "Brazil") or `universal` (for regimes like `public_domain`
  that are jurisdiction-independent).
- `confidence`: How certain is this assessment?
  - `assessed`: Based on actual legal review or specific prior art
    analysis.
  - `assumed`: Based on general knowledge of the jurisdiction's IP
    framework. Structural assessment, not legal advice.
  - `unknown`: Insufficient information to assess.

---

## Axis 4: Epistemic Accessibility

**What it measures**: Who can perceive this concept's value, and what value
they perceive.

**Key change in v0.2.0**: The linear 1–5 scale is replaced by named
audience profiles.

**Why**: The v0.1.0 scale assumed a single ladder of expertise. But
understanding is domain-specific and multi-track. A marketing professional
and a DevOps engineer are both "Level 3 — domain-adjacent professional"
in v0.1.0, but they perceive entirely different value in an ML product.
The number obscured this difference.

### Audience Profile Format

For each relevant audience:

| Field | Content |
|---|---|
| `audience` | Named group (e.g., "ML engineers", "procurement officers"). NOT a numbered level. |
| `perceives` | What value they see, in one sentence. |
| `action_enabled` | What this understanding enables them to do. |
| `channel` | Where you reach them (press release, API docs, academic paper, etc.). |

### Migration from v0.1.0

If backward compatibility with the 1–5 scale is needed, map audience
groups to the nearest v0.1.0 level. But prefer the audience-profile
format in new analyses.

---

## Axis 5: Maturity

**What it measures**: Where the concept sits in its lifecycle, based on
evidence.

### Enum Values

| Stage | Evidence Required |
|---|---|
| `theoretical` | Published theory, design docs. No implementation. |
| `experimental` | POC or prototype. Preliminary data. Not relied upon. |
| `validated` | Reproducible results under controlled conditions. |
| `deployed` | Running in production. Real users depend on it. |
| `commoditized` | Multiple independent implementations. Off-the-shelf. |
| `deprecated` | (New) Was deployed/commoditized, now actively being replaced. Successor exists or is in progress. |

### Maturity × Posture Expected Correlations

| Maturity | Likely Postures | Notes |
|---|---|---|
| theoretical | differentiator (speculative) | High risk, high potential |
| experimental | differentiator, enabler | Validate or abandon |
| validated | differentiator, moat | Decision point: patent? open-source? |
| deployed | any | All postures possible |
| commoditized | commodity, enabler, standard, public_good | Rarely differentiator |
| deprecated | (posture is residual, not strategic) | Focus shifts to successor |

---

## Axis 6: Combinatorial Profile

**What it measures**: How the concept interacts with other concepts.

### 6a. Dependencies

**Topology**: Dependencies may be **cyclic** (A → B, B → A at different
abstraction levels) and **conditional** (A → B only if condition C holds).

Format: `A → B [type, condition?]`
Types: `required` (necessary input), `catalytic` (improves but not
required), `unlocking` (binary gate).

### 6b. Positive Interactions

| Type | Definition |
|---|---|
| `synergy` | 1 + 1 > 2. Combination exceeds sum. |
| `threshold` | Only works when all concepts in group are present. |
| `amplification` | Each addition multiplies the effect. |

### 6c. Negative Interactions (new in v0.2.0)

| Type | Definition | Example Pattern |
|---|---|---|
| `inhibition` | Co-presence reduces effectiveness of one or both. | "Move fast" culture + "rigorous QA" — each dilutes the other. |
| `mutual_exclusion` | Cannot coherently coexist in the same system. | "Full transparency" + "trade secret protection" on the same data. |
| `cannibalization` | Deploying one reduces the need for the other. | Self-service tool cannibalizes "personalized support." |

**Why this matters**: A framework that only models positive combinatorics
will systematically overestimate the value of "adding more concepts" and
miss real-world tradeoffs. Every concept added to a system potentially
inhibits or cannibalizes existing ones.

### 6d. Substitutability

**Removed in v0.2.0.** Moved to Axis 1b (Structural Role) to eliminate
redundancy with the old `auxiliary` classification.

---

## Axis 7: Application Landscape

**What it measures**: Where this concept can and cannot be applied, with
what confidence.

### Categories

| Category | Confidence | Evidence |
|---|---|---|
| `proven_measured` | High, quantified | Metrics, A/B tests, published benchmarks. |
| `proven_observed` | High, qualitative | In production, relied upon, but not rigorously measured. |
| `plausible` | Medium | Theoretically sound, supporting analogies. Not tested here. |
| `speculative` | Low | Requires assumptions beyond current evidence. |
| `excluded` | High (negative) | Known to not work. Must state failure mode and source. |

### Application Entry Format

For each application:
- Name / description
- Category
- Relevant audience (from Axis 4 profiles)
- Evidence or failure mode

---

## Axis 8: Temporal Dynamics (new in v0.2.0)

**What it measures**: The trajectory and rate of change of the concept's
classification across all other axes.

| Field | Content |
|---|---|
| `velocity` | `stable` (classification unchanged for >2 years), `shifting` (changed or likely to change within 1–2 years), `volatile` (changing or likely to change within months). |
| `trajectory` | For each axis that is changing: current value → projected value, and basis for projection. |
| `half_life` | Estimated time until the concept's current differentiating properties are commoditized or obsoleted. Optional; mark confidence. |
| `forcing_functions` | External forces driving the change: competitors, regulation, technological shifts, market dynamics, internal strategy. |

**This axis is inherently speculative.** Mark it as such. But
speculative-and-documented is strictly better than speculative-and-omitted,
which is what v0.1.0 does by producing a static snapshot and implying
stability.

---

## Validation Checklist (revised)

Before emitting a final analysis, verify:

1. **Input validated**: Concept passes granularity test (nameable, bounded,
   propositionally productive).
2. **Frame is explicit**: Domain, viewpoint, and purpose are stated.
3. **No axis is skipped**: All axes have values.
4. **Decomposition and substitutability are separate**: 1a and 1b are
   independently justified.
5. **Non-exclusivity respected**: Posture uses weights. IP allows
   multiple regimes.
6. **Correlation audit completed**: Each known correlation pair is
   checked. Divergences are explained.
7. **Frame sensitivity noted**: For any axis where a plausible alternative
   frame would change the classification, this is documented.
8. **Negative interactions considered**: Combinatorial profile includes
   inhibition, exclusion, or cannibalization where they exist, or
   explicitly notes their absence.
9. **Temporal dynamics populated**: Even if the answer is "stable across
   all axes," state it.
10. **Speculation is marked**: Anything without evidence is labeled
    accordingly.
11. **Emergent is epistemic**: If `emergent` is assigned, the specific
    non-derivable property is named and the epistemic (vs. metaphysical)
    nature of the claim is acknowledged.

---

## Known Limitations of v0.2.0

This framework:

1. **Is not orthogonal.** Axes correlate. The correlation matrix documents
   known dependencies but is not empirically calibrated.
2. **Is not complete.** Ethical valence, cognitive load, falsifiability,
   and other dimensions are excluded. Users should extend via the
   `extensions` field.
3. **Is not computable.** Formal tests are heuristic notation. They make
   semantics explicit but cannot be mechanically verified.
4. **Is not culturally universal.** It assumes discrete, classifiable
   concepts and a Western-analytic epistemology.
5. **Has an arbitrary axis count.** 8 axes (9 sub-axes) is a design
   choice, not a derivation. No completeness proof exists.
6. **Trades brevity for honesty.** The audience-profile replacement for
   the 1–5 scale is more accurate but more verbose. This tradeoff is
   intentional but costly for quick comparisons.
