---
name: step-change-contributor
description: >
  Analyze any document or business asset and produce a single, fully realized,
  high-leverage contribution via cross-domain synthesis. Trigger when the user
  asks "what's the most original contribution you can make?", "what would
  produce a step-change?", "what's your novel contribution?", "highest leverage
  addition?", "what single thing would make this dramatically better?", "add
  the most value you can", "surprise me with something original", "what am I
  missing?", "what insight would transform this?", "find the gap only you could
  fill", or provides a document with "make this significantly better" without
  specifying how. Covers docs, specs, papers, strategies, plans, proposals,
  memos. Do NOT trigger for editing, proofreading, summarization, or when the
  user specifies exactly what to add.
---

# Step-Change Contributor

## What this skill does

Given a document or business asset, this skill runs a four-phase pipeline:

1. **Gap Analysis** — map the document's structure, claims, and reasoning,
   then identify what is absent, weak, implicit, or domain-blind.
2. **Leverage Ranking** — generate candidate contributions and rank them by
   a formal impact/feasibility metric, selecting the single highest-leverage
   move.
3. **Contribution** — produce the contribution itself as a fully realized
   artifact: a new section, a formalized model, a proof sketch, a framework,
   a bridging theory, or whatever form best delivers the value.
4. **Justification** — explain why this contribution produces a step-change,
   what it unlocks, and why it is non-obvious from within the document's
   existing frame.

The output is always a single Markdown document containing ALL four phases.

## Why this pipeline matters

Documents and plans develop blind spots proportional to their internal
coherence. The more internally consistent an asset is, the harder it is for
its authors to see what is missing — because the missing thing typically
lives in a different domain, at a different level of abstraction, or under a
framing the authors have no reason to consider. Claude's comparative
advantage is precisely here: rapid cross-domain retrieval, multi-level
abstraction, and the ability to reframe without political or institutional
bias. This skill channels that advantage into a disciplined process instead
of a vague "here are some suggestions."

## Mandatory pre-reading

Before beginning analysis, read `references/analysis-heuristics.md`. It
contains the gap taxonomy, the leverage scoring rubric, and the
cross-domain bridging patterns that prevent shallow or generic output.

**This file is mandatory reading before producing any output.**

## The pipeline in detail

### Phase 1 — Gap Analysis

Read the entire input document. Produce a **gap inventory**: a structured
map of what the document does and does not contain.

#### 1.1 — Structural map

Produce a concise outline of the document's architecture:
- What are its major sections, arguments, or components?
- What is the implicit hierarchy of claims (which claims support which)?
- What is the document's apparent purpose and intended audience?

#### 1.2 — Strength inventory

Before looking for gaps, explicitly acknowledge what the document does well.
This prevents the pathology of treating everything as deficient. Record:
- **Core strengths**: what the document handles with depth and rigor
- **Implicit competencies**: what the authors clearly understand even if not
  fully articulated
- **Structural virtues**: organizational choices that serve the purpose well

#### 1.3 — Gap taxonomy

Systematically probe for gaps across eight dimensions. For each dimension,
record either a specific gap or "no significant gap found." Do not
manufacture gaps that do not exist.

| Dimension | What to look for |
|-----------|-----------------|
| **Abstraction gaps** | Is there a higher-level pattern the document's specifics are instances of, but the document never names or exploits? |
| **Cross-domain gaps** | Is there a field, discipline, or practice area whose concepts would illuminate, validate, or challenge the document's claims — but which is never referenced? |
| **Formalization gaps** | Are there claims that would become significantly more powerful (or be revealed as flawed) if translated into formal language (logic, math, type systems, decision theory)? |
| **Mechanism gaps** | Does the document assert outcomes without explaining the causal mechanism that produces them? |
| **Boundary gaps** | Where does the document's model break down? What edge cases, failure modes, or scope limits are unexamined? |
| **Asymmetry gaps** | Does the document treat symmetric situations asymmetrically, or vice versa, without justification? |
| **Temporal gaps** | Does the document account for how its claims, strategies, or structures evolve over time, or is it implicitly static? |
| **Falsifiability gaps** | Does the document make claims that cannot, even in principle, be shown false by any observable outcome? Are there assertions with no conceivable counter-evidence? |

Each identified gap must include:
- **G-ID**: sequential identifier (G1, G2, …)
- **Dimension**: which of the seven
- **Description**: what is missing, in one sentence
- **Severity**: how much the document's value is diminished by this absence
  (minor / moderate / critical)
- **Evidence**: the specific passage or structural feature that reveals
  the gap

#### 1.4 — Honesty check

After producing the gap inventory, apply a self-audit:
- Are any of these "gaps" actually deliberate scope decisions by the author?
  If possibly so, flag them as **[possibly intentional]**.
- Are any of these gaps things Claude genuinely cannot fill (requires
  empirical data Claude does not have, domain expertise beyond Claude's
  training, or access to information not in the document)? If so, flag them
  as **[not addressable by Claude]**.

### Phase 2 — Leverage Ranking

#### 2.1 — Candidate generation

From the gap inventory, generate 3–7 **candidate contributions**: concrete,
specific things Claude could produce that would address one or more gaps.
Each candidate must be a deliverable, not a suggestion. Not "you should add a
section on X" but "a formal decision framework that maps X to Y using Z."

For each candidate, record:
- **C-ID**: sequential identifier (C1, C2, …)
- **Addresses gaps**: which G-IDs this candidate closes or reduces
- **Form**: what the contribution physically is (section, model, framework,
  proof, diagram, taxonomy, reframing, bridging argument, etc.)
- **Cross-domain source**: which field or discipline the contribution draws
  from (if any)
- **Novelty claim**: why this contribution is non-obvious from within the
  document's existing frame

#### 2.2 — Falsifiability gate

Before scoring, test each candidate for falsifiability. For each
candidate, attempt to state one concrete, observable outcome that would
refute the contribution if found to hold. Record the result:

- **[Falsifiable]** — a specific refuting observation was identified.
  State it. The candidate advances to scoring.
- **[Reformulable]** — the candidate as stated is unfalsifiable, but a
  more precise version of the same idea would be falsifiable. State the
  reformulation and the refuting observation. The reformulated version
  advances to scoring.
- **[Unfalsifiable]** — no refuting observation could be identified even
  after reformulation attempts. The candidate is eliminated. It does not
  advance to scoring regardless of how high it might score on Impact,
  Uniqueness, or Realizability.

If all candidates are eliminated, return to Phase 1 and generate new
candidates from a different subset of gaps, or conclude that no
falsifiable step-change contribution exists (a valid output).

#### 2.3 — Leverage scoring

Score each candidate on three axes using a 1–5 scale:

1. **Impact** — If this contribution were added, how much would the
   document's power, reach, or correctness increase?
   - 1: marginal improvement
   - 3: meaningfully stronger in one dimension
   - 5: transforms the document's core value proposition

2. **Uniqueness** — How likely is it that the document's authors (or a
   standard reviewer) would arrive at this contribution on their own?
   - 1: obvious next step anyone would suggest
   - 3: requires cross-domain knowledge the authors may lack
   - 5: requires a framing shift that is structurally invisible from
     the document's current perspective

3. **Realizability** — How fully can Claude produce this contribution right
   now, with only the document as input?
   - 1: would require significant external data or empirical work
   - 3: can be substantially produced but with some assumptions flagged
   - 5: can be produced completely and rigorously from available information

**Leverage score** = Impact × Uniqueness × Realizability (range: 1–125)

Select the candidate with the highest leverage score. If two candidates are
within 10% of each other, prefer the one with higher Uniqueness — the skill's
purpose is to deliver what others cannot.

In case of a tie after this tiebreaker, briefly note both candidates and
explain the choice.

### Phase 3 — Contribution

Produce the selected contribution in full. This is not a summary, a
suggestion, or an outline — it is the realized artifact itself.

**Form requirements by type:**

- **New section / argument**: Write it as publication-ready prose with
  the same voice and depth as the strongest section of the source document.
  Include citations to real, verifiable sources where claims rest on
  external knowledge.

- **Formal model**: Define all terms, state all assumptions explicitly,
  derive the result step by step. Use proper mathematical or logical notation.
  If the model introduces variables or parameters, define their domains.

- **Framework / taxonomy**: Define the dimensions, explain the partitioning
  logic, populate with examples drawn from the source document, and
  demonstrate how the framework generates insight the document currently
  lacks.

- **Bridging argument**: Identify the two domains being bridged, establish
  the structural homomorphism or analogy explicitly, note where the analogy
  holds and where it breaks down.

- **Proof sketch / formal analysis**: Follow the standards of the
  formal-completeness-checker skill. State the proposition, define the
  formal system, and carry the proof as far as the available information
  allows. Flag any steps that require assumptions.

**Critical constraints for the contribution:**

1. **Do not hallucinate references.** If you cite a paper, book, or
   result, it must be real and verifiable. If you are uncertain, say
   "this draws on a result attributed to [X]; verify the citation."

2. **Do not flatten the source.** The contribution must respect the
   source document's level of sophistication. Do not simplify a technical
   document or overcomplicate a strategic one.

3. **Do not replicate what exists.** If the document already covers a
   topic, the contribution must extend, reframe, or formalize it — not
   restate it.

4. **Label all assumptions.** Every assumption the contribution
   introduces that is not present in the source document must be
   explicitly labeled **[Assumption introduced by contributor]**.

5. **Make it falsifiable.** The contribution must entail at least one
   concrete, observable prediction — a state of affairs that, if found
   not to hold, would refute or materially weaken the contribution. This
   is not optional decoration; it is the difference between an
   epistemically useful contribution and rhetoric. State the prediction
   explicitly in the form: **[Falsification criterion]: If ___ is
   observed / measured / found to be the case, then this contribution is
   refuted or must be revised.** If the contribution is a formal model,
   the criterion should follow from the model's axioms. If the
   contribution is a framework or taxonomy, the criterion should identify
   an empirical case that the framework predicts it can classify but which
   would break the partitioning if found. If you cannot state any
   falsification criterion, the contribution is unfalsifiable — rework it
   or choose a different candidate.

### Phase 4 — Justification

After the contribution, write a structured justification:

#### 4.1 — Step-change argument

Explain in 2–4 paragraphs:
- What specific capability, reach, or rigor the document gains from this
  contribution that it did not have before.
- Why this improvement is non-linear (a step-change rather than an
  incremental addition).
- What new possibilities, arguments, or applications become available
  once this contribution is integrated.

#### 4.2 — Leverage audit

Revisit the leverage score and assess honestly:
- Did the realized contribution deliver on the Impact / Uniqueness /
  Realizability scores assigned in Phase 2?
- If the contribution fell short on any axis, say so and explain why.

#### 4.3 — Falsifiability audit

State explicitly:
- **The falsification criterion** (restated from the contribution for
  visibility): what observable outcome would refute this contribution?
- **Test sketch**: what concrete procedure — experiment, data query,
  case study, formal check — could in principle produce the refuting
  observation? This does not need to be immediately executable, but it
  must be specific enough that a competent practitioner could carry it
  out. "Further research is needed" is not a test sketch.
- **Strength of test**: classify the criterion as one of:
  - **Strong** — a single counter-observation would refute the core
    claim outright.
  - **Moderate** — a counter-observation would weaken the core claim
    and require revision of a key parameter or boundary condition.
  - **Weak** — a counter-observation would refute a secondary
    prediction but leave the core claim standing with reduced scope.
  If you can only produce a Weak criterion, consider whether the
  contribution is substantive enough to qualify as a step-change.

#### 4.4 — Limitations and caveats

Enumerate:
- What the contribution does NOT do
- What assumptions it depends on that might not hold
- What further work would be needed to fully integrate it into the
  source document
- Any domains or perspectives the contribution itself is blind to

## Output document structure

Produce a single Markdown document:

```
---
disclaimer: >
  No information within this document should be taken for granted.
  Any statement or premise not backed by a real logical definition or
  verifiable reference may be invalid, erroneous, or a hallucination.
  This analysis represents one model's assessment of leverage and
  novelty — it may be wrong. Verify independently.
title: "Step-Change Contribution: [Document Title]"
date: [current date]
method: step-change-contributor/v1
source_document: "[filename or title of input]"
---

# Step-Change Contribution: [Document Title]

## 1. Gap Analysis

### 1.1 Structural map
[Outline of the document's architecture]

### 1.2 Strengths
[What the document does well — be specific and genuine]

### 1.3 Gap inventory
[Table or list of all identified gaps with G-IDs, dimensions,
severity, and evidence]

### 1.4 Honesty check
[Flags for possibly intentional gaps and non-addressable gaps]

## 2. Leverage Ranking

### 2.1 Candidate contributions
[3–7 candidates with C-IDs, forms, gap coverage, cross-domain
sources, and novelty claims]

### 2.2 Falsifiability gate
[Each candidate's falsifiability status: Falsifiable, Reformulable
(with reformulation), or Unfalsifiable (eliminated)]

### 2.3 Scoring and selection
[Score table and explanation of the selected candidate — only
candidates that passed the falsifiability gate]

## 3. The Contribution

### [Title of the contribution]
[The fully realized contribution itself — this is the core deliverable]

## 4. Justification

### 4.1 Step-change argument
[Why this is non-linear improvement]

### 4.2 Leverage audit
[Honest reassessment of the scores]

### 4.3 Falsifiability audit
[Falsification criterion, test sketch, and strength classification]

### 4.4 Limitations and caveats
[What this does not do and what it depends on]
```

## Scaling behavior

- **Short documents (< 2 pages)**: Gap analysis can be brief. Focus
  energy on the contribution itself. Full output: 3–6 pages.
- **Medium documents (2–20 pages)**: Full pipeline as described.
  Output: 6–15 pages.
- **Long documents (> 20 pages)**: Gap analysis should be thorough
  but the contribution should still be ONE thing. Resist the temptation
  to produce multiple contributions for a long document — the skill's
  power is focus. Output: 10–20 pages.

## Common failure modes to avoid

1. **The "obvious improvement" trap.** If your best candidate is
   something the authors clearly know about but chose not to include
   (e.g., "add a literature review" to a practitioner document), your
   gap analysis missed a [possibly intentional] flag. Revisit.

2. **The "impressive but irrelevant" trap.** Cross-domain synthesis
   is only valuable if the bridge carries load. If the connection to
   another field is merely aesthetic ("this is like X in quantum
   mechanics!") rather than structural, it is not a contribution.

3. **The "meta-commentary" trap.** The contribution must be object-level
   content, not commentary about the document. "Your document would
   benefit from more formalization" is not a contribution; a formalized
   model of the document's core argument IS a contribution.

4. **The "scope explosion" trap.** One contribution. Fully realized.
   Not five sketches. The skill's name is singular for a reason.

5. **The "sycophancy" trap.** If the document is genuinely excellent
   and no high-leverage contribution exists, say so. "After analysis,
   I find no single addition that would produce a step-change" is a
   valid output. It is better than a forced, low-leverage contribution.

6. **The "unfalsifiable insight" trap.** The contribution sounds
   profound — it reframes, it bridges, it synthesizes — but there is
   no conceivable observation that could show it to be wrong. If you
   cannot state a falsification criterion for the contribution, it has
   no empirical or logical teeth. This is especially common with
   bridging arguments and framework contributions where the language
   of another field is imported decoratively. The test: strip away the
   prose and ask what the contribution *predicts* that the document
   without it does not predict. If the answer is nothing, rework the
   contribution until it does predict something testable, or select a
   different candidate.
