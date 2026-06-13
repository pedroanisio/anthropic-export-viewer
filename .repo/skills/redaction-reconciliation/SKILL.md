---
name: redaction-reconciliation
description: >
  Prevent unreconciled redaction — structural and content decay from multiple
  revision rounds. Use whenever revising, editing, restructuring, or
  incorporating feedback into any document or article, especially multi-round
  feedback merges, adding sections, or any edit touching more than one section.
  Trigger on "incorporate this feedback", "merge these edits", "revise based on
  comments", "clean up this draft", "the structure is off", "something reads
  weird about the flow", or documents with changelogs like "incorporated
  feedback from rounds 1–N", visible style seams, or redundant treatments of
  the same concept. If the task substantively modifies an existing document's
  content or structure, use this skill. Skip for pure copy-editing (typos,
  grammar only).
---

# Redaction Reconciliation

## The problem this skill solves

When a document passes through multiple revision rounds, each round adds,
amends, or qualifies material. But no round takes ownership of the document as
a whole — no pass asks "given everything that's now here, what structure and
voice would I choose if writing from scratch?" The result is a text whose
organization reflects the **chronology of its drafting** rather than the
**logic of its subject matter**.

This is **redactional layering** — the same phenomenon textual criticism has
studied for centuries in composite texts. The document becomes a palimpsest
where earlier layers remain visible through the surface.

Two separable pathologies branch from this root, and they require different
diagnoses and different fixes. See `references/pathology-taxonomy.md` for the
full analytical framework.

## The reconciliation protocol

Every substantive revision MUST include a reconciliation pass. This is not
optional. It is the difference between editing and redacting.

### Phase 0 — Snapshot before touching anything

Before making any changes:

1. Read the entire document end-to-end. Do not skim. Every section, every
   transition, every repeated concept.
2. Build a **content inventory**: a flat list of every distinct claim, concept,
   definition, example, and argument in the document, tagged with its location.
   This is your ground truth for deduplication later.
3. Identify the document's **apparent structure** (what the ToC says) vs. its
   **actual dependency graph** (what the reader needs to know before they can
   understand each section).

Record these as internal working notes before proceeding.

### Phase 1 — Apply the requested changes

Make the edits the user asked for. Insert new material, revise existing
passages, incorporate feedback. Do this faithfully — the reconciliation pass
does not override the user's intent, it *completes* it.

### Phase 2 — Diagnose redactional damage

After applying changes, run two independent diagnostic checks. Consult
`references/pathology-taxonomy.md` for the detailed heuristics.

#### Check A: Architectural accretion

For every section boundary in the document, answer:

> "Why does section N+1 follow section N?"

If the only honest answer is "because it was added later" rather than "because
the reader needs N's content to understand N+1," flag this as architectural
accretion. The table of contents should read like a logical argument, not a
changelog.

Specific signals:
- A section's content logically depends on material that appears *after* it.
- Two adjacent sections have no conceptual relationship — they're neighbors by
  chronological accident.
- A section heading names a *process* ("Updates from Q3 Review") rather than a
  *topic* ("Resource Allocation Model").
- The document has a "Miscellaneous" or "Additional Notes" section that's grown
  to substantial size.

#### Check B: Resolution inconsistency

For every concept in the content inventory, check whether it appears more than
once. For each duplicate:

> "Which formulation is canonical? Does the reader know which to trust?"

Specific signals:
- The same concept is defined differently in two places.
- A simplified sketch exists in one section and a full treatment in another,
  with no cross-reference.
- An earlier formulation has been implicitly superseded by a later one, but
  the earlier one was never removed or marked.
- A correction or qualification in one section contradicts an unmodified
  statement elsewhere.

### Phase 3 — Reconcile

This is the critical phase. Do NOT skip it.

#### 3a: Structural reconciliation (fixes architectural accretion)

If Check A found accretion:

1. Take the full content inventory from Phase 0 (updated with Phase 1 changes).
2. Discard the existing section hierarchy entirely.
3. Rebuild the structure around the **reader's dependency graph**: each section
   should be comprehensible given only the sections that precede it. The
   ordering principle is *logical prerequisite*, not *drafting chronology*.
4. Verify: walk the new table of contents and confirm every adjacency has a
   reason beyond "this is when it was written."

Preserve the user's voice and terminology. Restructuring changes the
*container*, not the *contents*.

#### 3b: Content reconciliation (fixes resolution inconsistency)

If Check B found inconsistency:

For each concept with multiple formulations:

1. **Assign authority**: decide which formulation is canonical. This is usually
   the most complete, most correct, and most recent version — but not always.
   The user may have a reason for a particular phrasing.
2. **Deduplicate**: fold subordinate formulations into the canonical one.
   Delete, merge, or redirect.
3. **If progressive disclosure is genuinely intended**: make it explicit. Add
   a forward reference from the simplified version to the full treatment:
   "We introduce X here in simplified form; the full treatment is in §N." The
   reader must never wonder whether they're reading an outdated version of a
   concept.

#### 3c: Voice normalization

After structural and content reconciliation, read the document once more for
**register and tense discontinuities** — seams where different revision rounds
wrote in different voices. Smooth these without flattening intentional voice
shifts (e.g., a formal executive summary followed by a conversational
technical walkthrough is fine; the same section oscillating between registers
is not).

### Phase 4 — Report

After completing the reconciliation, provide a brief summary to the user:

1. What changes were applied (Phase 1).
2. What redactional damage was found (Phase 2), classified as architectural
   accretion, resolution inconsistency, or both.
3. What reconciliation was performed (Phase 3).
4. Any judgment calls where you chose between competing formulations or
   structural options — surface these so the user can override.

If no redactional damage was found, say so explicitly. Do not fabricate
problems.

## The intentional/unintentional axis

Not all layering is pathological. The diagnostic is whether the layering is
**legible and purposeful** to the reader.

- **Architectural accretion is almost always unintentional.** It is hard to
  imagine deliberately organizing a document by drafting chronology.
- **Resolution inconsistency can be intentional** — it's called progressive
  disclosure in information design and scaffolding in pedagogy (Bruner 1966,
  building on Vygotsky's zone of proximal development). The pathology isn't
  layered presentation per se — it's layered presentation where the reader
  doesn't know it's layered, or the layers aren't ordered simple→complex on
  purpose.

When you encounter what looks like intentional progressive disclosure, preserve
it and make it explicit. When you encounter what looks like someone wrote the
sketch, wrote the full version, and forgot to kill the sketch — kill the sketch.

## The changelog heuristic

A version entry that says "incorporated feedback from rounds 1–3" is a prior
that unreconciled redaction has occurred. It tells you the process was additive.
Whether the resulting damage is architectural, content-level, or both is a
second-order diagnosis you make by reading the text — but the changelog gives
you the starting suspicion.

When you see such changelogs, escalate your scrutiny. Run Phase 2 checks more
carefully.

## Scope and proportionality

Not every edit requires full structural reconciliation. The protocol scales to
the size of the change:

- **Single-section edit, no structural implications**: Run Check B only
  (resolution consistency for the concepts touched). Skip Check A unless
  something looks obviously misplaced.
- **Multi-section edit or feedback incorporation**: Full protocol, both checks.
- **Major rewrite or "clean up this draft"**: Full protocol with extra
  attention to Phase 3a. The user is likely already sensing the accretion.

Use judgment. The goal is zero unreconciled redaction, not zero efficiency.
