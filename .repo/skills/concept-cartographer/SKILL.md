---
name: concept-cartographer
description: >
  Analyze any concept and produce a structured multi-dimensional classification
  across decomposition status, substitutability, strategic posture, IP regime,
  epistemic accessibility, maturity, combinatorial profile, application
  landscape, and temporal dynamics. Frame-relative, correlation-aware, and
  honest about its own limitations.
---

# Concept Cartographer v0.2.0

Analyze any concept and produce a structured, multi-dimensional
classification that replaces naive binary labels with formally defined,
partially-independent axes grounded in explicit criteria.

## Before you begin

1. Read `references/dimension-definitions-v0.2.0.md` — it contains the
   formal definitions, enum values, decision criteria, known correlations,
   and admitted limitations for every classification axis. Do not guess
   values from memory; confirm against the reference.

---

## Why This Exists

Human concept classification tends toward false binaries: "is it primary
or secondary?", "is it internal or external?", "is it a feature or a trade
secret?" These framings are:

- **Logically defective**: they assume mutual exclusivity where none exists.
- **Ontologically flat**: they ignore dependency graphs, cyclic relations,
  and negative interactions between concepts.
- **Epistemically naive**: they collapse a multi-dimensional space of
  audiences into a single linear scale.
- **Strategically incomplete**: they miss maturity, defensibility,
  composability, temporal trajectory, and combinatorial leverage.
- **Statically biased**: they produce snapshots without trajectory,
  treating volatile classifications as if they were permanent.

This skill replaces those broken heuristics with a nine-sub-axis framework
where each axis captures variance not fully captured by the others, and
known correlations between axes are explicitly documented.

**What this framework is NOT**: It is not orthogonal (axes correlate), not
complete (more dimensions exist), not computable (the formal tests are
heuristic), and not culturally universal (it assumes an analytic,
Western-business-compatible epistemology). It is a structured thinking tool,
not a source of truth.

---

## Phase 0 — Validate the Input

Before classifying anything, verify the input is well-formed.

A **concept** is: a named, bounded abstraction that can be the subject of
a truth-apt proposition within a specified domain.

| Check | Question | If fails |
|---|---|---|
| Nameable | Does it have or can it receive a stable label? | Ask the user to name it. |
| Bounded | Can you state what is and is not part of it? | Decompose until boundaries are clear. |
| Propositionally productive | Can you assert non-trivial true/false claims about it? | Reject: not yet well-formed for classification. |

## Phase 1 — Establish the Frame

Every classification is frame-relative. Before analyzing anything:

| Property | Question |
|---|---|
| `domain` | What system, product, field, or organization? |
| `viewpoint` | From whose vantage? (engineer, strategist, end user, regulator, competitor, researcher, operator) |
| `purpose` | Why? (product positioning, IP strategy, communication planning, competitive analysis, knowledge management, investment decision) |

If the user doesn't specify, infer from context and state explicitly,
or ask.

## Phase 2 — Structural Role

Two independent sub-axes. Evaluate each separately.

### 2a. Decomposition Status

| Value | Definition | Test |
|---|---|---|
| `primitive` | Relative stopping point: decomposition within this domain's vocabulary yields only terms outside the domain. Not an intrinsic property. | All sub-components leave the domain. |
| `composite` | Fully derivable from other concepts in the domain. Knowledge of parts + composition rule is sufficient. | Parts exist in domain AND all properties of the whole are derivable from them. |
| `emergent` | Arises from other concepts but has at least one property not derivable from complete knowledge of parts and their composition rule, **given current theory**. Epistemic claim, not metaphysical. | Non-derivable property exists under current understanding. If future theory explains it, reclassify as `composite`. |

### 2b. Substitutability Class

| Value | Definition |
|---|---|
| `irreplaceable` | No known functional equivalent. Removal destroys capabilities. |
| `costly_to_replace` | Substitutes exist. Switching cost > 6 months or > 20% domain restructuring. |
| `substitutable` | Multiple equivalents. Low switching cost. |

**Output**: Decomposition status + justification, substitutability class +
known substitutes, frame-sensitivity note.

## Phase 3 — Strategic Posture

Assign **all applicable postures with weights** (0.0–1.0, summing to 1.0):

| Posture | Definition |
|---|---|
| `differentiator` | Unique competitive advantage. Hard to replicate. |
| `commodity` | Widely available. Table stakes. ≥3 equivalents exist. |
| `enabler` | Multiplier. Removal blocks ≥2 downstream capabilities. |
| `moat` | Compounds over time (network effects, data flywheels, switching costs). |
| `standard` | Value from adoption, not exclusivity. Competing with the standard is destructive. |
| `public_good` | Non-rivalrous, non-excludable. Goal is adoption, not protection. |

**Correlation check** (mandatory): Does the posture assignment align with
expected correlations from maturity and substitutability? If divergent,
explain — divergence is often where the strategic insight lives.

## Phase 4 — IP Regime

Every regime is a tuple: `(regime, jurisdiction, confidence)`.

| Regime | Definition |
|---|---|
| `public_domain` | Freely available. No protection needed or possible. |
| `trade_secret` | Value derives from secrecy. Disclosure destroys advantage. |
| `patentable` | Novel, non-obvious, useful. Structural assessment, not legal advice. |
| `open_but_attributed` | Shared freely, attribution builds brand or ecosystem. |
| `proprietary_feature` | Visible to users. Protected by product boundary, not secrecy. |

`jurisdiction` ∈ { named legal jurisdiction or `universal` }
`confidence` ∈ { `assessed`, `assumed`, `unknown` }

## Phase 5 — Epistemic Accessibility

**Do not use a linear 1–5 scale.** Instead, enumerate the actual relevant
audiences:

For each audience segment, produce:

| Field | Content |
|---|---|
| `audience` | Named group (e.g., "ML engineers", "procurement officers", "regulators"). |
| `perceives` | What value they see, in one sentence. |
| `action_enabled` | What this understanding lets them do. |
| `channel` | How you reach them (API docs, press release, patent filing, etc.). |

## Phase 6 — Maturity

| Stage | Evidence Required |
|---|---|
| `theoretical` | Papers, proposals, designs. No implementation. |
| `experimental` | POC exists. Data is preliminary. |
| `validated` | Reproducible results under controlled conditions. |
| `deployed` | In production. Real users depend on it. |
| `commoditized` | Multiple independent implementations. Off-the-shelf. |
| `deprecated` | Was deployed/commoditized, now being actively replaced. |

**Correlation check** (mandatory): Does maturity align with expected
posture and IP correlations?

## Phase 7 — Combinatorial Profile

### Dependencies (may include cycles)
Format: `A → B [type, condition?]`
Types: `required`, `catalytic`, `unlocking`

### Positive Interactions
| Type | Definition |
|---|---|
| `synergy` | 1 + 1 > 2 |
| `threshold` | Only works when all are present |
| `amplification` | Each addition multiplies effect |

### Negative Interactions
| Type | Definition |
|---|---|
| `inhibition` | Co-presence reduces effectiveness of one or both |
| `mutual_exclusion` | Cannot coherently coexist in the same system |
| `cannibalization` | One reduces the need for the other |

## Phase 8 — Application Landscape

| Category | Confidence | Evidence |
|---|---|---|
| `proven_measured` | High, quantified | Metrics, A/B tests, benchmarks. |
| `proven_observed` | High, qualitative | In production, not rigorously measured. |
| `plausible` | Medium | Theoretically sound, not tested here. |
| `speculative` | Low | Requires assumptions beyond current evidence. |
| `excluded` | High (negative) | Known to not work. State failure mode + source. |

## Phase 9 — Temporal Dynamics

| Field | Content |
|---|---|
| `velocity` | `stable`, `shifting`, `volatile` |
| `trajectory` | Per-axis: current value → projected value + basis for projection |
| `half_life` | Time until current differentiating properties are commoditized/obsoleted |
| `forcing_functions` | External forces driving change |

Mark as speculative. Speculative-and-stated > speculative-and-omitted.

---

## Mandatory Correlation Audit

Before finalizing, check and document:

| Axis Pair | Expected Correlation | Your Assignment | Aligned or Divergent? | Note |
|---|---|---|---|---|
| Maturity ↔ Posture | commoditized → commodity | ... | ... | ... |
| Substitutability ↔ Posture | substitutable → commodity | ... | ... | ... |
| IP Regime ↔ Posture | public_domain ↗ incompatible with moat | ... | ... | ... |
| Maturity ↔ IP Regime | theoretical → limits proprietary_feature | ... | ... | ... |

Divergences are not errors. Unexplained divergences are.

---

## Important Principles

- **Frame-relativity is not optional.** State the frame. Always.
- **Do not claim orthogonality.** Axes correlate. Document it.
- **Never hallucinate applications or leverage.** Mark uncertainty.
- **The dependency graph + negative interactions are the most valuable
  output.** Give them proportional attention.
- **Challenge the user's framing.** If they ask a binary question,
  explain why it's the wrong question.
- **State what the framework cannot do.** It is not computable, not
  complete, not culturally universal. Say so when relevant.
- **Emergent is an epistemic claim.** It means "we cannot currently
  derive this from parts," not "this is metaphysically irreducible."
  Be honest about the difference.
