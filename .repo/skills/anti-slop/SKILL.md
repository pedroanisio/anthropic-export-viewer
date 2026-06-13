---
name: anti-slop
description: >
  Review prose for low-substance writing ("slop") using a two-tier diagnostic.
  Tier 1: surface cues (vocabulary, sentence patterns, structure, decorative
  performance). Tier 2: substance failures (abstraction without specifics,
  invocation without application, intellectual dishonesty, unfalsifiability).
  Tier 2 dominates Tier 1. Trigger whenever the user asks to "check for slop",
  "review writing quality", "detect AI writing", "run anti-slop", "check my
  writing", "audit this text", "is this filler", "does this say anything",
  "this reads like AI", "too fluffy", "strip the slop", "make this real",
  or any variation of assessing whether writing does intellectual work versus
  performing the shape of thought. Also trigger for self-editing or reviewing
  Claude's own output for substance. If text is uploaded and the user asks
  whether it is substantive or worth reading, use this skill.
---

# Anti-Slop Checklist — Review Protocol

A structured protocol for identifying low-substance prose. Run sequentially,
but the verdict is determined by the **priority rule**: Tier 2 dominates Tier 1.

## What This Skill Is & Is Not

**IS:** A rubric for detecting low-substance prose (slop) regardless of
authorship. A self-editing and peer-review tool. A framework for thinking
systematically about writing quality.

**IS NOT:** A reliable AI-authorship detector (stylometric detection has high
false-positive rates, especially for non-native English speakers). Not a
substitute for human judgment. Not a formal detection method — it is a
heuristic. No single checklist item triggers an automatic verdict.

---

## Priority Rule

The checklist has two tiers. **Tier 2 dominates Tier 1.**

- **Tier 1 (Sections 1–4):** Surface diagnostics — vocabulary, sentence
  patterns, structural templates, decorative performance. Diagnostic only
  when Tier 2 also fails. A document passing Tier 2 with Tier 1 blemishes
  has stylistic imperfections, not slop.

- **Tier 2 (Sections 5–8):** Substance diagnostics — content checks,
  invocation-vs-application, intellectual honesty, acid tests. These catch
  the absence of real intellectual work. A document failing Tier 2 is slop
  regardless of surface cleanliness.

**Decision rule:**
1. Passes Tier 2 → Tier 1 flags are cosmetic notes.
2. Fails Tier 2 → Tier 1 flags become confirming evidence.
3. Fails Tier 2 with clean Tier 1 → **high-quality slop** (the most
   dangerous kind — passes casual inspection while communicating nothing
   falsifiable).

---

## Execution Protocol

When this skill triggers, run all eight sections in order, then produce
the verdict. Do not skip sections. Do not stop at Tier 1.

### Tier 1 — Surface Diagnostics

#### Section 1 — Vocabulary Red Flags

Search the text for slop-lexicon items. See `references/lexicon.md` for
the full list. In isolation these are blemishes; in concentration they are
symptoms.

**Severity calibration:** Count density, not just presence. A handful of
tics in an otherwise rigorous document is a stylistic note. The same tics
every other paragraph in a document making no falsifiable claims is
confirming evidence.

**Non-native speaker caveat:** Vocabulary heuristics show documented high
false-positive rates (61.3% misclassification per Liang et al., Patterns
2023) when applied to non-native English speakers. Do not use Section 1
alone to assess such writing — verify with Tier 2 before drawing
conclusions.

**Test:** Delete every flagged word. If the sentence still works, the word
was filler.

#### Section 2 — Sentence-Level Patterns

These correlate with formulaic or evasive prose but are NOT validated as
AI-specific markers. Treat them as quality signals, not detection markers.

Check for:
- **Length variance.** Sample 10 consecutive sentences. If most cluster
  15–25 words with low variance, the rhythm may be synthetic. Real prose
  mixes short (<12 words) with long (35+ words).
- **Connector chains.** Three or more sentences starting with "Additionally
  ... Moreover... Furthermore..." is padding.
- **Hedging pileup.** "It could potentially be argued that one might
  consider..." — state the uncertainty once, then commit.
- **Em-dash overuse.** 0–3 per page is normal. Heavy clustering warrants
  attention (model-dependent: GPT-4o uses ~10× more than GPT-3.5; Claude
  uses fewer).
- **Passive agglutination.** Long stretches with no identifiable agent.

**Test:** Read five consecutive sentences. If they could be reordered
without the reader noticing, they lack logical progression.

#### Section 3 — Structural Tells

Check for:
- **Symmetric structure.** Every section follows the same template. Real
  ideas have irregular shapes.
- **Rule-of-three clustering.** Multiple sections in exactly three parts,
  or multiple lists with exactly 3 or 5 items. Real lists vary: 2, 4, 7,
  11 — whatever the content demands.
- **Restating the question.** Opening paragraph rephrases what was asked.
  Cut it.
- **"In today's [adjective] [noun]..."** As an opener, diagnostic on its
  own.
- **Conclusion that concludes nothing.** Final paragraph restating what
  was said, or ending with "only time will tell."

**Test:** Remove the first and last paragraph. Does the document lose
anything substantive? If not, they were scaffolding. (Some framing
paragraphs earn their place — this identifies candidates, not automatic
deletions.)

#### Section 4 — Decorative Performance

Stylistic moves that simulate depth without producing it:
- **Analogies that don't do work.** Metaphor swappable for any other
  without changing the argument.
- **Performative profundity.** Rephrase plainly; if the plain version is
  "this is an open question," the original was performing.
- **Binary-opposition patterns.** Heavy "not X, but Y" clustering.
- **Synonym cycling.** Repeating the same concept with different vocabulary
  without advancing it.
- **Heavy signposting.** "This is important," "Notably," "Significantly,"
  punctuating every paragraph.
- **Rigor theater.** Self-referential praise for the document's own
  methodology. The derivation works or it doesn't — narrating one's own
  rigor is performative.

**Test:** Strip all aesthetic ornamentation. Does the remaining text still
have a thesis?

---

### Tier 2 — Substance Diagnostics

#### Section 5 — Content-Level Checks

These determine whether the document does intellectual work. A document
passing this section is not slop, regardless of surface tells.

- **Abstraction without specifics.** Does every claim stay conceptual, or
  are there names, numbers, dates, mechanisms, counterexamples? Slop
  floats above specifics because specifics are falsifiable.
- **Permanent balance without position.** "On one hand... on the other
  hand..." on every point, never resolving. Real analysis takes a position.
- **Information delta.** After reading, does the reader know anything new?
  If the text is predictable from the title alone, it communicated nothing.
- **Falsifiability.** Has any claim been stated precisely enough to be
  wrong? If every statement is hedged to unfalsifiability, no intellectual
  commitment was made. Conversely, self-correction is strong evidence of
  real work — slop was never precise enough to be wrong.
- **Semantic looping.** The text restates the same idea with synonymous
  vocabulary instead of advancing it.

**Test:** Identify the single strongest claim. Can you imagine specific
evidence that would refute it? If not, the claim is not precise enough to
be meaningful.

#### Section 6 — Invocation Without Application

Naming a concept is not the same as using it.

- **Concept name-dropping.** Technical concept mentioned but not used as a
  premise, not derived from, not applied to the problem. Listing impressive
  concepts signals competence without demonstrating it.
- **Numbers without provenance.** A precise figure appears with no
  derivation, no citation, no source. Precise numbers require either a
  calculation or a reference.
- **Fabricated or unverifiable citations.** Specific claim presented as
  fact with no URL, no author, or a fabricated URL. This is a critical slop
  marker. Exception: text that explicitly flags its estimate as unsourced
  demonstrates intellectual honesty.
- **Formalism gap.** Document claims to operate in a formal domain but
  contains zero equations, zero formal definitions, zero derivations.
- **Completionism.** Computing a result no one asked for to close a logical
  space. Flag as debatable — can be rigorous overkill or genuine
  thoroughness.

**Test:** For each technical concept, ask: is it doing argumentative work
(premise, derivation, constraint) or is it decoration? If removable
without weakening any argument, it is decoration.

#### Section 7 — Intellectual Honesty Patterns

These distinguish real analytical work from its simulation.

- **Uncredited restatement.** Presenting a well-known problem as a novel
  observation. Real scholarship acknowledges intellectual lineage.
- **Raise and abandon.** Introducing the strongest counterargument then
  dropping it without engagement. Measure: if the strongest objection gets
  fewer than three sentences of direct engagement, it was raised for show.
- **Fake epistemic humility.** Stacked "whether this is X... or Y... or
  Z..." that simulate careful thinking without commitment. Genuine
  uncertainty is stated once, directly.
- **Error correction and self-undermining (POSITIVE signal).** Version
  history with real corrections, admitted fabricated sources, active
  self-correction — these indicate genuine intellectual process.

**Test:** Find the point of strongest objection engagement. How many
sentences before the text moves on? If fewer than three, the objection was
for show. Does the document anywhere admit a specific error?
Self-correction is among the strongest anti-slop signals.

#### Section 8 — Acid Tests (Run Last)

Holistic checks. Run after everything else. These produce the final
verdict.

1. **Voice test.** Read aloud. Does it sound like a specific person with
   specific views, or a press release from nowhere?
2. **Swap test.** Could this be replaced with any other response on the
   same topic without anyone noticing? If yes, no distinctive analytical
   content.
3. **Deletion test.** Remove first and last paragraph. Anything
   substantive lost?
4. **Prediction test.** Before reading each paragraph, predict what it
   says from the heading. If always predictable, the text is formulaic.
5. **So-what test.** After reading, state: "What specific, non-obvious,
   falsifiable claim does this document make?" If you cannot state one,
   the document performed the activity of saying something without saying
   anything. That is slop.

---

## Output Format

After running all eight sections, produce a structured verdict. Use this
template:

```
## Anti-Slop Assessment

### Tier 1 — Surface Diagnostics
- **Section 1 (Vocabulary):** [CLEAN | FLAGS | HEAVY] — [brief note]
- **Section 2 (Sentence patterns):** [CLEAN | FLAGS | HEAVY] — [brief note]
- **Section 3 (Structural tells):** [CLEAN | FLAGS | HEAVY] — [brief note]
- **Section 4 (Decorative performance):** [CLEAN | FLAGS | HEAVY] — [brief note]

### Tier 2 — Substance Diagnostics
- **Section 5 (Content-level):** [PASS | WEAK | FAIL] — [brief note]
- **Section 6 (Invocation vs application):** [PASS | WEAK | FAIL] — [brief note]
- **Section 7 (Intellectual honesty):** [PASS | WEAK | FAIL] — [brief note]
- **Section 8 (Acid tests):** [PASS | WEAK | FAIL] — [brief note]

### Verdict
[One of:]
- **NOT SLOP** — Tier 2 passes. Tier 1 flags (if any) are cosmetic notes.
- **SLOP** — Tier 2 fails. [State which substance checks failed and why.]
- **HIGH-QUALITY SLOP** — Tier 2 fails but Tier 1 is clean. [Explain what
  is missing despite the polish.]

### Strongest Claim Identified
[State it, or state that none was found.]

### Recommendations
[Specific, actionable items — not generic advice.]
```

Adapt the format to context. For casual requests ("is this any good?"),
the verdict and recommendations may be conversational rather than
templated. For formal reviews, use the full template. The protocol is
the same either way — run all sections, apply the priority rule, produce
the verdict.

---

## Self-Review Mode

When asked to review your own output, or when self-editing before
delivering a response:

1. Run the full protocol on your own text.
2. Be adversarial — do not grade yourself leniently.
3. If your own output fails Tier 2, rewrite before delivering.
4. If your own output has Tier 1 flags, note them and clean up where
   possible without over-sterilizing the prose.

The goal is not to produce text that "passes the checklist" by being
maximally bland. The goal is to produce text that does intellectual work.
A document with personality, voice, and occasional stylistic tics that
also makes falsifiable claims and engages objections is better than a
document that is stylistically sterile and says nothing.

---

## References

- `references/lexicon.md` — Full slop lexicon, padding connectors,
  sycophantic openers, empty intensifiers, AI verbal tics. Read when
  running Section 1 and you need the complete word lists.
- `references/research-notes.md` — Citations and methodological notes
  from Kobak et al. 2025, Liang et al. 2025, Juzek & Ward 2025 on
  vocabulary evolution and false-positive rates. Read when assessing
  non-native speakers or when the temporal validity of vocabulary
  markers is in question.
