# PALS's Law Reference — Extracted Definitions

Source: PALS's Law v1.5.4 (Pedro Anisio de Luna e Silva, April 2026)
Status: Draft — peer review pending
Zenodo: https://zenodo.org/records/19401530

This reference file contains the definitions, taxonomy, and corollaries
needed for assessment. It is extracted from the source document for
efficient context loading. Consult the full source for proofs, empirical
support, and limitations.

---

## 1. Core Definitions

- **M**: the class of autoregressive transformer language models.
- **M ∈ M**: any concrete model with parameter set θ.
- **X**: the space of all valid input prompts.
- **Y**: the space of all possible output sequences.
- **Σ**: a ground-truth semantic specification (partial function mapping
  prompts to correct outputs).
- **ε(y, x) ∈ {0, 1}**: Boolean error predicate — 1 iff output y
  deviates from Σ(x) in any dimension enumerated in the taxonomy.

## 2. The Law — Operative Form

For every model M in M and every realistic distribution D over X:

    E[ε(M(x), x)] ≥ δ > 0

where δ is non-negligible — measurably above zero for any extant model
on any realistic task distribution. The expectation is restricted to
x ∈ dom(Σ) — inputs for which ground truth exists.

**Implication**: LLM error is not an exceptional bug but a statistical
invariant of the model class. Any system consuming LLM output without a
declared verification boundary contains an architectural defect.

## 3. The Pipeline Corollary

For a pipeline P = (M₁, M₂, …, Mₙ):

    P(at least one error) = 1 − ∏(1 − pᵢ) → 1 as n → ∞

where pᵢ ≥ δ > 0 for each step.

**Independence caveat**: Real pipelines share context. The product
formula can be wrong in both directions. It motivates the architectural
consequence but is not a deployable risk model without a correlation
model.

## 4. Error Taxonomy — 9 Classes

Each class requires a distinct detection strategy. No single verifier
can cover all classes. This is the foundational motivation for treating
verification as architectural.

| ID | Class | Definition | Detection strategy hint |
|----|-------|-----------|----------------------|
| ERR_HALLUCINATION | Hallucination | Asserting a false factual claim with apparent confidence — fabricated references, non-existent APIs, incorrect statistics. | External ground-truth lookup; cross-reference validation; source retrieval. |
| ERR_OMISSION | Omission | Silently dropping required content — instructions followed partially, constraints missed, fields absent. | Completeness checklist against specification; diff against requirements. |
| ERR_SCHEMA | Schema violation | Output structurally non-conformant with declared format — JSON parse failure, missing keys, wrong types. | Automated schema validation (JSON Schema, Zod, protobuf, OpenAPI). |
| ERR_TRUNCATION | Partial completion | Output cut short due to token budget, stopping heuristics, or streaming interruption. | Length/completeness checks; sentinel markers; section-count validation. |
| ERR_SYCOPHANCY | Sycophantic drift | Output shaped by perceived user preference rather than truth; agreement substituting for accuracy. | Adversarial rephrasing; consistency checks across varied framings. |
| ERR_INSTRUCTION | Instruction failure | Violation of explicit constraints stated in the prompt — language, length, format, prohibited content. | Constraint extraction + automated verification against each constraint. |
| ERR_CALIBRATION | Calibration failure | Expressed confidence misaligned with actual reliability — under- or over-hedging. | Confidence extraction + empirical accuracy measurement; calibration curves. |
| ERR_REASONING | Reasoning failure | Correct facts, invalid composition — multi-step inference breakdowns, reversal failures, logical contradictions. | Logical consistency checks; intermediate-step verification; formal reasoning tools. |
| ERR_SEMANTIC | Semantic drift | Correct surface form, wrong meaning — paraphrase that inverts, weakens, or subtly misrepresents the intended claim. | Semantic equivalence testing; back-translation; domain-expert review. |

**Scope notes from source**:
- Adversarial contexts (prompt injection) are extrinsic and out of
  scope for this intrinsic error taxonomy — but require separate threat
  modeling in agentic deployments.
- Policy/compliance violations (correct output that violates business
  rules) are extrinsic to semantic correctness.
- Multimodal and tool-use errors (ERR_TOOL_USE) are acknowledged as
  future extensions.

## 5. Architectural Corollaries

These are logical consequences of the operative form, not
recommendations.

### Corollary 1 — Appearance of correctness is not correctness
A system that validates LLM output by inspection on a finite test set
has demonstrated error-absence on the tested inputs, not error-freedom.
Manual review during development does not substitute for runtime
verification in production.

### Corollary 2 — Trust accumulation is prohibited
Observing correct outputs on x₁, …, xₖ provides no guarantee about
P(ε = 1) on xₖ₊₁. A system must not relax its verification layer
after a run of correct outputs.

### Corollary 3 — Verification scope must match error taxonomy
A verifier that checks only ERR_SCHEMA does not cover ERR_HALLUCINATION
or ERR_SYCOPHANCY. Partial verification is better than none but must be
scoped honestly. Verification claims must be documented, not asserted
globally.

### Corollary 4 — Silent acceptance is an architectural defect
Any production system that passes LLM output directly to downstream
consumers without a declared verification boundary has an architectural
omission — regardless of observed output quality or model capability.

### Corollary 5 — Capability growth shifts the verification problem
As model capability increases:
- Low-stakes error classes (ERR_OMISSION, ERR_SCHEMA, ERR_TRUNCATION,
  ERR_INSTRUCTION) become less frequent and easier to detect.
- High-stakes error classes (ERR_HALLUCINATION, ERR_SYCOPHANCY,
  ERR_SEMANTIC, ERR_CALIBRATION, ERR_REASONING) become harder to detect
  because more capable models produce more plausible errors.

Verification system upgrades are a precondition for deploying a more
capable model. Treating the verifier as stable while upgrading the model
is an architectural regression.

## 6. Contract Block Template

For any function, endpoint, pipeline, or workflow that consumes LLM
output, the following checklist scopes which error classes the system's
verifier covers:

```
ARCHITECTURAL CONTRACT — PALS's LAW

MODEL_VERSION: <model identifier and version>
PALS_LAW_VERSION: 1.5.4

INVARIANT (operative form):
  E[ε(M(x), x)] ≥ δ > 0

ERROR CLASSES COVERED BY THIS SYSTEM'S VERIFIER:
[ ] ERR_HALLUCINATION
[ ] ERR_OMISSION
[ ] ERR_SCHEMA
[ ] ERR_TRUNCATION
[ ] ERR_SYCOPHANCY
[ ] ERR_INSTRUCTION
[ ] ERR_CALIBRATION
[ ] ERR_SEMANTIC
[ ] ERR_REASONING

Unchecked boxes are known, accepted risks.
Leaving all boxes unchecked with no mitigation note is a blocking defect.
```

## 7. Key Limitations (from source §7)

1. The error predicate ε is not computable in general — the law asserts
   errors exist, not a general algorithm for finding them.
2. δ is task-, model-, and distribution-dependent — calibrating it
   requires empirical measurement on the target deployment.
3. Independence in pipeline compounding is approximate — errors
   correlate through shared context.
4. Verification coverage vs. depth is unresolved — the contract
   checklist identifies which classes a verifier covers but not
   detection power within each class.
5. The Boolean error predicate is a deliberate simplification — a
   graded predicate ε ∈ [0,1] is the appropriate extension for
   severity-weighted verification.
6. Computability-theoretic impossibility vs. practical non-negligibility
   operate at different levels — the operative form is empirical, the
   existential form is formal.
