---
name: pals-assessment
description: >
  Assess any software artifact — API, codebase, pipeline, system, component,
  or agentic workflow — for LLM output verification defects using PALS's Law
  (v1.5.4). Produces a structured audit report and actionable checklist.
  Applies the 9-class error taxonomy as assessment lens for code and API
  surfaces, and the 5 architectural corollaries for system-level evaluation.
  Trigger on "assess", "audit", "review", "evaluate", or "check" any software
  for LLM safety, verification coverage, or agentic readiness. Also trigger
  on "PALS assessment", "PALS audit", "PALS's Law", "verification boundary",
  "LLM output verification", "agentic safety", "hallucination risk",
  "AI-ready", "silent acceptance", "does this trust LLM output", or any
  request to evaluate a system's posture toward LLM output trust. Trigger
  even without the PALS name when the intent is checking whether a system
  handles LLM unreliability. NOT for evaluating models — for evaluating
  systems that consume LLM output.
---

# PALS Assessment Skill

## What this skill does

Given any software artifact that interacts with LLM output — either
producing it, consuming it, wrapping it, or being consumed by LLM-driven
agents — this skill conducts a systematic assessment of whether the
system treats LLM output as untrusted by default and maintains adequate
verification boundaries.

The assessment framework is PALS's Law v1.5.4, an engineering
formalization asserting that LLM output error is a statistical invariant
of the model class (not an exceptional bug), and that any system failing
to treat it as such contains an architectural defect. The framework
provides a 9-class error taxonomy, 5 architectural corollaries, and a
pipeline compounding model.

**Framework author**: Pedro Anisio de Luna e Silva
**Framework source**: PALS's Law v1.5.4 (April 2026)
**Framework reference**: Zenodo — https://zenodo.org/records/19401530

The output is always:
1. A **structured audit report** (markdown) with findings, severity
   ratings, and recommendations.
2. An **actionable checklist** (markdown) showing verification coverage
   per error class and corollary compliance.

## Before starting — read the reference files

Before producing any output, read both reference files:

1. `references/pals-law-reference.md` — the formal definitions, error
   taxonomy, and architectural corollaries extracted from the source.
2. `references/assessment-procedures.md` — the step-by-step assessment
   methodology, target-specific guidance, severity classification,
   and output templates.

**Both files are mandatory reading before producing any output.** The
reference files contain the taxonomy definitions, corollary statements,
assessment procedures, and templates that the assessment depends on.

## Assessment scope

The skill handles five target types. Determine which applies and follow
the corresponding section in `references/assessment-procedures.md`:

| Target type | When to use | Key focus |
|------------|------------|----------|
| **API / tool interface** | The target is an API that agents will call, or an API that internally uses LLMs | Schema completeness, error classification, idempotency, observable commit state, destructive action boundaries |
| **Codebase** | The target is source code that invokes LLM APIs or processes LLM output | Call site verification, generated code paths, prompt construction, decision-point dependency |
| **Agentic pipeline** | The target is a multi-step agent, tool-using assistant, or automated workflow | Step-level verification, tool-call validation, planning verification, state management, cascade/amplification patterns |
| **System / architecture** | The target is a system design, infrastructure, or component integration | LLM isolation, verification layer architecture, model upgrade path, failure mode analysis |
| **Mixed** | The target spans multiple types | Assess each component by its type; synthesize findings at the system level |

## The assessment sequence

This is the universal procedure. Follow it for every assessment:

### 1. Identify interaction surfaces

Map every point where LLM output enters or exits the system. Record
location, input, output, downstream consumer, and side effects. If the
target does not use LLMs directly but will be consumed by agents, assess
it as a tool surface.

### 2. Classify error exposure per surface

For each surface, determine which of the 9 error classes are relevant
using the decision rules in the procedures reference. Build the exposure
matrix.

### 3. Map existing verification

For each surface, identify what verification currently exists and map
it to the error classes it covers. Be honest about coverage: a JSON
Schema validator covers ERR_SCHEMA and nothing else.

### 4. Evaluate architectural corollaries

Check the system against all 5 corollaries. Each violation is a finding.

### 5. Analyze pipeline compounding (if applicable)

For multi-step pipelines: count LLM-dependent steps, identify inter-step
verification, and classify correlation patterns (cascade, masking,
amplification).

### 6. Produce findings and recommendations

Each finding gets an ID, affected surface(s), error class(es), violated
corollary (if applicable), description, severity, and actionable
recommendation. Use the severity classification in the procedures
reference.

### 7. Generate outputs

Produce both the **report** and the **checklist** using the templates
in `references/assessment-procedures.md` §7 and §8.

## Critical constraints

### Honesty about verification limits

The error predicate ε is not computable in general. Some error classes
(ERR_HALLUCINATION, ERR_SEMANTIC) cannot be fully automated. When the
assessment identifies these as exposed, recommend the best available
mitigation — not a nonexistent perfect solution. Distinguish between
"verification exists and covers this class" and "verification is
theoretically possible but not implemented" and "no known automated
verification method exists for this class in this context."

### Severity must be justified

Every severity rating must trace to a specific criterion in the
severity classification (§6 of procedures reference). Do not inflate
severity to be alarmist or deflate it to be diplomatic. The criteria
are:

- **Critical**: unverified LLM output reaches side-effect-producing
  systems (writes, sends, deletes, deploys, payments).
- **High**: verification exists but doesn't cover the relevant error
  classes, OR ≥ 3 unverified sequential LLM steps.
- **Medium**: primary classes covered but secondary gaps exist, OR
  trust accumulation detected, OR model upgrades skip verifier review.
- **Low**: verification exists but documentation or scoping is
  insufficient.

### Scale to the target

A single API endpoint gets a focused, proportionate assessment. A
large distributed system gets comprehensive treatment. Do not produce
a 30-page report for a 10-line function, and do not produce a
superficial checklist for a complex agentic platform.

### Attribution

Always credit the framework:
- **Framework**: PALS's Law v1.5.4
- **Author**: Pedro Anisio de Luna e Silva
- **Reference**: Zenodo — https://zenodo.org/records/19401530

### The disclaimer is mandatory

Per user preferences, every output document must include the standard
frontmatter disclaimer about unverified content.

## What this skill is NOT

- **Not a model evaluation tool.** This skill assesses systems that
  consume LLM output, not the models themselves. Benchmark scores,
  model comparisons, and capability evaluations are out of scope.
- **Not a security audit.** Prompt injection, adversarial attacks, and
  extrinsic threats are acknowledged in the taxonomy scope notes but
  are out of scope for the intrinsic error assessment. Note them if
  observed but do not claim coverage.
- **Not a compliance framework.** Policy violations (correct output
  that violates business rules) are extrinsic to semantic correctness.
  Note them if observed but assess them separately.

## Common pitfalls

- **Treating all error classes as equally detectable.** ERR_SCHEMA is
  trivially automatable. ERR_SEMANTIC requires domain expertise. The
  assessment must be honest about this asymmetry.
- **Confusing "we test it" with "we verify it."** Test-time inspection
  is Corollary 1. Runtime verification is the requirement.
- **Listing error classes without mapping them to surfaces.** The
  taxonomy is useful only when applied to specific interaction points.
  A global "we handle hallucinations" claim without surface-level
  mapping is a Corollary 3 violation.
- **Ignoring the tool-surface direction.** If the target is an API,
  assess it both as a consumer of LLM output (if applicable) AND as a
  surface that will be consumed by LLM agents (if applicable). These
  are different assessment directions.
- **Recommending "add human review" as a universal fix.** Human review
  is a valid verification layer for some error classes but does not
  scale, is subject to its own biases (especially for ERR_SYCOPHANCY
  and ERR_SEMANTIC), and is not a substitute for automated verification
  where automated verification is feasible.
