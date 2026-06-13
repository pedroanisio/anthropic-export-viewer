# Analysis Heuristics Reference

## Table of contents

1. Gap taxonomy — detailed definitions and detection heuristics
2. Leverage scoring rubric — calibration examples
3. Cross-domain bridging patterns — catalog of structural bridges
4. Anti-patterns — common mistakes and how to detect them

---

## 1. Gap taxonomy — detailed definitions and detection heuristics

### 1.1 Abstraction gaps

**Definition:** The document operates at a specific level of abstraction but
never names or exploits the general pattern its specifics instantiate.

**Detection heuristics:**
- Look for repeated structures across sections that share a common form
  but are treated as unrelated.
- Ask: "If I replaced every domain-specific noun in claim X with a variable,
  would the resulting template match another claim in the document?" If yes,
  the shared template is an unnamed abstraction.
- Ask: "Is this document about a specific X, or is it really about a class
  of things that X belongs to?" If the latter, the class is the abstraction
  gap.

**Example:**
A marketing strategy document discusses customer acquisition, retention, and
reactivation as separate problems with separate solutions. The abstraction
gap: all three are instances of **state transition optimization** in a
customer lifecycle Markov chain. Naming this enables a unified framework.

### 1.2 Cross-domain gaps

**Definition:** A field or discipline outside the document's domain contains
concepts, results, or frameworks that directly illuminate the document's
claims — but the document never references them.

**Detection heuristics:**
- For each core claim, ask: "What field studies this phenomenon as its
  primary subject?" If the answer differs from the document's field, there
  may be a gap.
- Look for reinvented wheels: the document may be constructing from scratch
  something that already has a mature treatment elsewhere.
- Check for structural homomorphisms: does the document's problem have the
  same mathematical or logical shape as a well-studied problem in another
  domain?

**Catalog of frequently valuable cross-domain bridges:**

| Document domain | Often-missed source domain | Bridge type |
|----------------|---------------------------|-------------|
| Business strategy | Game theory, mechanism design | Strategic interaction formalization |
| Software architecture | Category theory, type theory | Compositional structure |
| Policy design | Mechanism design, social choice | Incentive alignment |
| Marketing / growth | Epidemiology, network science | Diffusion dynamics |
| Organizational design | Distributed systems, control theory | Coordination mechanisms |
| Product specs | Decision theory, utility theory | Preference formalization |
| Educational materials | Cognitive load theory, constructivism | Pedagogical structure |
| Legal / compliance | Deontic logic, formal verification | Obligation formalization |
| Financial analysis | Information theory, signal processing | Signal extraction |

This table is a heuristic, not a checklist. The right bridge depends on the
specific document. Do not force a connection that does not carry structural
load.

### 1.3 Formalization gaps

**Definition:** The document makes claims that are precise enough to
formalize but leaves them in natural language, losing precision, verifiability,
or generalization power.

**Detection heuristics:**
- Look for claims containing "always", "never", "if and only if",
  "necessary", "sufficient", "optimal", "maximizes", "for all", "there
  exists" — these are natural-language quantifiers begging for formalization.
- Look for definitions that are ambiguous: the same term is used in multiple
  sections with subtly different meanings.
- Ask: "If I gave this claim to two competent readers, would they extract
  identical truth conditions?" If not, formalization would resolve the
  ambiguity.

### 1.4 Mechanism gaps

**Definition:** The document asserts a relationship between cause and effect
(or input and output) without explaining the mechanism — the HOW.

**Detection heuristics:**
- Look for causal claims ("X leads to Y", "X enables Y", "X drives Y")
  where the intermediate steps are not spelled out.
- Ask: "If I removed the author's assertion and kept only the evidence,
  would the causal relationship be obvious?" If not, the mechanism is
  missing.
- Look for "black box" arguments: the document describes inputs and outputs
  of a process without describing the process itself.

### 1.5 Boundary gaps

**Definition:** The document's model, framework, or strategy has implicit
scope limits that are never examined. It works under certain conditions but
does not say which conditions.

**Detection heuristics:**
- Look for universally stated claims: "This approach works for..." without
  "...except when..."
- Ask: "Under what conditions would this claim become false?" If you can
  easily construct such conditions and the document does not address them,
  there is a boundary gap.
- Look for assumptions that are only true in the document's default context
  (e.g., assumes a growing market, assumes rational actors, assumes stable
  technology).

### 1.6 Asymmetry gaps

**Definition:** The document treats structurally similar cases differently
(or structurally different cases the same way) without justification.

**Detection heuristics:**
- Look for two sections or arguments that have the same logical form but
  reach different conclusions, without explaining the difference.
- Conversely, look for cases where the document applies the same treatment
  to cases that differ in a dimension it cares about elsewhere.
- Ask: "If I swapped entities A and B in this argument, would the conclusion
  still follow?" If not, the asymmetry needs justification.

### 1.7 Temporal gaps

**Definition:** The document describes a state of affairs but does not
account for how that state evolves, decays, or transforms over time.

**Detection heuristics:**
- Look for present-tense claims about things that are inherently dynamic
  (markets, technologies, organizations, relationships).
- Ask: "Is this still true in 6 months? In 5 years? What changes?"
- Look for strategies that assume a static environment or opponent.
- Check for reflexivity: does the document's own existence or adoption
  change the conditions it describes?

### 1.8 Falsifiability gaps

**Definition:** The document makes claims that are not, even in
principle, refutable by any observable outcome. No conceivable evidence
could count against them — either because they are vacuously true,
tautological, unfalsifiably vague, or defined in terms that absorb any
counter-evidence.

**Detection heuristics:**
- For each core claim, ask: "What observable state of affairs would the
  author accept as evidence that this claim is wrong?" If neither you
  nor a reasonable reader can construct such a scenario, the claim is
  unfalsifiable.
- Look for **immunizing strategies**: qualifiers like "in the right
  conditions", "when properly implemented", "for suitable values of X"
  that make the claim true by definition because any failure can be
  attributed to the conditions not being right, the implementation not
  being proper, or the values not being suitable.
- Look for **untethered abstractions**: claims stated at such a high
  level of generality that they are compatible with any concrete
  outcome. Example: "Our culture of excellence drives results." No
  failure could refute this because "excellence" and "results" are
  unoperationalized.
- Look for **circular definitions**: the success criterion for a claim
  is defined in terms of the claim itself. Example: "An effective leader
  produces effective outcomes" — "effective" is load-bearing in both
  the premise and the conclusion.
- Ask: "Does this claim generate a *specific* prediction that could
  fail?" Predictions must be specific enough to be wrong. "Revenue will
  grow if we execute well" generates no testable prediction. "Revenue
  will grow by ≥15% YoY if we ship feature X to segment Y by Q3" does.
- Check whether the document contains any **empirical anchors** — points
  where its claims touch ground in measurable, observable reality. A
  document with zero empirical anchors is either purely formal (fine, if
  internally consistent) or unfalsifiably vague (not fine).

**Example:**
A strategy document states: "By fostering cross-functional synergy, we
will unlock compounding returns across the organization." This is
unfalsifiable — "cross-functional synergy" is not operationalized, and
"compounding returns" has no measurable referent. A falsifiable
reformulation: "If teams A and B hold joint weekly reviews (starting Q2),
the average cycle time for features requiring both teams will decrease by
at least 20% within two quarters." Now the claim can fail.

---

## 2. Leverage scoring rubric — calibration examples

The scoring is intentionally subjective but should be calibrated. Here are
anchor points for each axis.

### Impact calibration

| Score | Meaning | Example |
|-------|---------|---------|
| 1 | Marginal | Adding a glossary to a well-written spec |
| 2 | Useful | Adding a worked example to an abstract framework |
| 3 | Meaningfully stronger | Providing a formal proof for a key claim that was previously argued by analogy |
| 4 | Major upgrade | Introducing a framework that unifies three previously separate sections into a coherent model |
| 5 | Transforms core value | Revealing that the document's central claim is an instance of a known theorem, enabling rigorous guarantees |

### Uniqueness calibration

| Score | Meaning | Example |
|-------|---------|---------|
| 1 | Anyone would suggest this | "Add a conclusion section" |
| 2 | Competent reviewer would catch it | "The cost analysis ignores opportunity cost" |
| 3 | Requires cross-domain knowledge | "This scheduling problem is a variant of the job-shop problem; known approximation algorithms apply" |
| 4 | Requires reframing | "Your employee retention strategy is actually a mechanism design problem; the issue is incentive compatibility, not culture" |
| 5 | Structurally invisible from inside | "Your document's seven design principles are the axioms of a matroid; the eighth principle is uniquely determined by the axiom of augmentation" |

### Realizability calibration

| Score | Meaning | Example |
|-------|---------|---------|
| 1 | Needs empirical data Claude lacks | "Run an A/B test to validate this claim" |
| 2 | Needs substantial domain expertise | "Audit this against current SEC regulations" |
| 3 | Can produce with flagged assumptions | "Build a formal model assuming these three parameters are independent" |
| 4 | Can produce with minor gaps | "Write the bridging argument; one cited result needs verification" |
| 5 | Can produce completely | "Formalize this decision matrix and prove its completeness" |

---

## 3. Cross-domain bridging patterns

A bridge is not a metaphor. A bridge is a structural mapping that preserves
relationships and enables transfer of results.

### Pattern 1: Isomorphism

The document's problem IS a known problem in another field, up to relabeling.

**Test:** Can you construct a bijection between the document's entities and
the other field's entities such that all relationships are preserved?

**Value:** If isomorphic, the entire toolkit of the other field applies
directly. This is the highest-value bridge.

### Pattern 2: Homomorphism

The document's problem maps to a simpler structure in another field.
The mapping preserves some relationships but not all.

**Test:** Can you construct a surjection that preserves the key operation
or relation?

**Value:** Results from the simpler structure give necessary (but not
sufficient) conditions for the document's problem.

### Pattern 3: Analogy with bounded transfer

The document's problem resembles a problem in another field in some
dimensions but not others.

**Test:** Specify exactly which properties transfer and which do not.
If you cannot do this precisely, the analogy is decorative, not structural.

**Value:** Hypotheses and frameworks transfer; proofs do not. Use the bridge
to generate candidates, then verify in the document's own domain.

### Pattern 4: Dual / complementary view

The document examines one side of a duality that has a well-studied
complementary side.

**Test:** Is there a known duality (e.g., time/frequency, primal/dual,
supply/demand, structure/behavior) that maps the document's perspective
to its complement?

**Value:** The dual view reveals constraints and invariants invisible from
the primal view.

---

## 4. Anti-patterns — detecting and avoiding common failures

### Anti-pattern: The Wikipedia bridge

The contribution says "this is related to [well-known concept]" without
showing how the relationship generates insight the document lacks.

**Test:** Does the bridge enable a specific conclusion, prediction, or
construction that the document cannot reach on its own? If not, it is a
Wikipedia bridge.

### Anti-pattern: Complexity theater

The contribution adds formalism that restates the document's claims in
symbols without increasing precision, enabling new derivations, or
revealing hidden structure.

**Test:** Does the formalization enable you to prove something, compute
something, or detect an inconsistency that was not apparent in natural
language? If not, it is complexity theater.

### Anti-pattern: Scope imperialism

The contribution argues that the document should expand to cover a much
larger territory, when the document's narrow scope may be intentional
and well-chosen.

**Test:** Does the author plausibly know about the broader scope and
chose to focus? If possibly yes, flag as [possibly intentional] and do
not build the contribution around scope expansion.

### Anti-pattern: Recency bias

The contribution introduces a concept or framework because it is currently
fashionable (e.g., "this is actually an AI alignment problem" or "you
should add a blockchain component") rather than because it is structurally
appropriate.

**Test:** Would this bridge have been equally valid 10 years ago? If the
connection only seems relevant because of a current trend, scrutinize it
more carefully.

### Anti-pattern: The unfalsifiable contribution

The contribution reads as insightful — it reframes the problem, it
introduces a bridging theory, it names a pattern — but nothing observable
follows from it. No experiment, measurement, case study, or formal check
could demonstrate that the contribution is wrong. It is compatible with
every possible outcome.

This anti-pattern is insidious because unfalsifiable contributions often
*feel* profound. The reframing creates an "aha" moment. But intellectual
pleasure is not epistemic value. A contribution has epistemic value only
if it partitions the space of possible observations into those that are
consistent with it and those that are not.

**Detection heuristics:**
- Strip the contribution to its core claim and ask: "What does this
  predict that the document without it does not predict?" If the answer
  is "nothing concrete," it is unfalsifiable.
- Check for immunizing qualifiers introduced by the contributor (not just
  in the source document). "This framework applies when the conditions
  are met" is a tautology.
- Check whether the contribution's formalism is load-bearing or
  decorative. A formal model that generates no testable consequence
  beyond what the informal argument already stated is complexity theater
  *and* unfalsifiable.
- Ask: "Could a skeptic construct a scenario that would make the
  contribution's author concede the contribution is wrong?" If no such
  scenario exists, the contribution is unfalsifiable.

**Common disguises:**
- **The framework that classifies everything.** If the taxonomy can
  absorb any new case without revision, it has no predictive power.
  A good taxonomy makes claims about what *cannot* coexist or what
  *must* follow from a classification — and those claims can be wrong.
- **The bridging metaphor.** "Your problem is isomorphic to X" — but
  no theorem or result from X is actually transferred, so no prediction
  from X can fail in the document's domain. The bridge carries no load.
- **The "deeper understanding" move.** The contribution claims to
  reveal "the real reason" behind the document's claims but offers no
  way to distinguish the real reason from the originally stated reason
  by any observable consequence.

**The fix:** Every contribution must include at least one explicit
**[Falsification criterion]** — a concrete, specific, observable
condition under which the contribution is refuted. If you cannot produce
one after genuine effort, the contribution is unfalsifiable. Select a
different candidate or reformulate until the criterion exists.
