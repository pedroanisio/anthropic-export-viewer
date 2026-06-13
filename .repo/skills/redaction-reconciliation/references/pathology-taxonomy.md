# Pathology Taxonomy and Detection Heuristics

Reference material for the redaction-reconciliation skill. Consult this when
running Phase 2 diagnostics.

## Table of contents

1. Architectural accretion — definition, signals, heuristics, remediation
2. Resolution inconsistency — definition, signals, heuristics, remediation
3. Compound pathology — when both co-occur
4. Differential diagnosis — distinguishing pathological layering from
   intentional progressive disclosure
5. Worked examples

---

## 1. Architectural accretion

### Definition

The document's structure — section ordering, hierarchy, navigational logic —
encodes drafting history rather than reader dependency. Sections exist where
they do because that's where someone inserted them during round N, not because
that's where a reader needs them.

### Detection signals

**The adjacency test.** For each pair of consecutive sections (N, N+1), ask:
"What conceptual relationship justifies this ordering?" Valid answers:

- N+1 depends on concepts introduced in N (logical prerequisite)
- N and N+1 are parallel treatments of related topics (coordinate structure)
- N+1 is a specialization or application of N (hierarchical refinement)

Invalid answers (indicating accretion):

- "N+1 was added after N in draft round 3"
- "N+1 was requested by reviewer X and this is where there was space"
- No discernible relationship; the sections happen to be neighbors

**The heading-type test.** Scan all section headings. Classify each as:

- **Topical**: names a subject ("Authentication Model", "Market Analysis")
- **Processual**: names a drafting event ("Updates from Review", "Additions
  per Feedback Round 2", "New Requirements")
- **Catch-all**: names an absence of category ("Miscellaneous",
  "Additional Notes", "Other Considerations", "Appendix B")

Processual and catch-all headings are strong signals of accretion.

**The orphan-dependency test.** For each section, list the concepts it assumes
the reader already understands. Check whether those concepts were introduced
in a *preceding* section. If a section depends on material that comes *after*
it, the structure has inverted dependencies — a hallmark of insertion-order
organization.

**The size-distribution test.** Plot the length of each section. Accretion
often produces a few large "original" sections interspersed with small
"inserted" sections. If the document has a lumpy, irregular size distribution
and the small sections don't have a structural reason to be short (they're not
summaries, transitions, or definitions), suspect accretion.

### Remediation

1. Extract all content into a flat inventory (claims, concepts, definitions,
   examples, arguments — each as an independent unit).
2. Build the reader's dependency graph: for each unit, list what the reader
   must already know to understand it.
3. Topological-sort the units by dependency. Groups of mutually independent
   units become coordinate sections at the same level.
4. Assign hierarchical structure: units with shared prerequisites become
   siblings under a parent section named for the prerequisite.
5. Write transitions between sections. These didn't exist before because the
   sections were never meant to be adjacent — they need connective tissue now.

---

## 2. Resolution inconsistency

### Definition

The same concept appears in multiple locations at different levels of detail,
with no signal marking which formulation is preliminary, which is
authoritative, and which is superseded. The reader encounters the document
*disagreeing with itself across time*.

### Detection signals

**The concept-frequency test.** Scan the content inventory for any concept,
term, or definition that appears more than once. For each duplicate:

- Are the formulations identical? (Redundancy — minor issue, fix by
  deduplication.)
- Are they compatible but at different levels of detail? (Resolution
  inconsistency — the core pathology.)
- Are they contradictory? (Supersession — the most dangerous variant. One
  version was corrected but the old version was never removed.)

**The temporal-stratigraphy test.** Look for phrases that betray layering:

- "As mentioned above..." / "As noted earlier..." — followed by a formulation
  that doesn't match what was actually said earlier. The cross-reference was
  accurate when written but the target was later amended.
- "Actually, ..." / "More precisely, ..." / "To clarify, ..." — inline
  corrections that qualify an earlier statement without removing or amending
  it. These are *patches*, not *revisions*.
- Footnotes or parentheticals that effectively rewrite the sentence they're
  attached to.

**The version-shadow test.** For key definitions or claims, check whether an
earlier, simpler version exists elsewhere in the document. Common patterns:

- Executive summary contains version 1; body contains version 3; the
  summary was never updated.
- Introduction sketches a concept; a later section treats it fully; the
  sketch is now misleading because the full treatment refined it.
- An appendix contains a "corrected" version of something in the main body.

**The qualification-chain test.** Look for chains of qualifications: statement
A in section 2, qualified by B in section 4, further qualified by C in section
7. The reader must hold all three in mind and mentally compose them. This is
unreconciled: the final, fully qualified statement should exist in one place.

### Remediation

For each concept with multiple formulations:

1. **Determine the canonical formulation.** Usually the most complete and most
   correct version. Not always the latest — a revision might have introduced
   an error.
2. **Collapse the duplicates:**
   - If the simplified version serves no pedagogical purpose → delete it.
   - If progressive disclosure is intended → keep it, but add explicit
     cross-references ("simplified here; full treatment in §N") and ensure
     the simplified version is *consistent with* (not contradicted by) the
     full version.
   - If versions contradict → resolve the contradiction. Flag to the user if
     the correct version is ambiguous.
3. **Rebuild cross-references.** After deduplication, any "as mentioned above"
   references may now point to the wrong location or to deleted content.
   Audit all internal references.

---

## 3. Compound pathology

When both architectural accretion and resolution inconsistency co-occur, fix
them in this order:

1. **Content reconciliation first** (resolution inconsistency). Deduplicate and
   assign authority. This reduces the total volume of content.
2. **Structural reconciliation second** (architectural accretion). Rebuild the
   hierarchy around the now-deduplicated content.

Why this order: structural reconciliation is easier when there's less redundant
content to arrange. And deduplication sometimes *eliminates* sections entirely,
changing the structural problem.

---

## 4. Differential diagnosis: pathological vs. intentional layering

### Intentional progressive disclosure

Legitimate progressive disclosure has these properties:

- The simplified version is **explicitly marked** as simplified ("We introduce
  X here informally; the formal definition is in §N").
- The versions are **ordered simple → complex**, matching the reader's
  knowledge accumulation.
- The simplified version is **consistent with** the full version — it's a
  correct abstraction, not a contradicted first draft.
- There is a **pedagogical reason** for the layering — the reader genuinely
  benefits from encountering the simple version before the complex one.

### Pathological resolution inconsistency

Pathological inconsistency has these properties:

- No explicit marking — the reader doesn't know they're reading a preliminary
  version.
- Versions are ordered by **drafting chronology**, not by complexity.
- The simplified version **contradicts** or is **misleadingly incomplete**
  relative to the full version.
- The duplication exists because **the author forgot to kill the draft**, not
  because the reader needs scaffolding.

### Edge case: the evolved introduction

A very common case: the introduction was written first, the body evolved
significantly during review, and the introduction was never updated. The
introduction now promises a document that no longer exists. This is resolution
inconsistency (the introduction's claims about what the document covers don't
match the document) and often architectural accretion too (the introduction's
structure maps to an obsolete outline).

Fix: rewrite the introduction last, after all other reconciliation is done.
The introduction should describe the document as it *is*, not as it was
*planned*.

---

## 5. Worked examples

### Example A: Technical specification after 3 review rounds

**Symptom**: Section 4 ("Authentication") introduces OAuth2 flows. Section 7
("Updated Authentication Requirements") adds PKCE and deprecates one flow.
Section 4 was never amended.

**Diagnosis**: Resolution inconsistency (supersession variant). Section 7's
heading is processual ("Updated..."), suggesting accretion too.

**Fix**: Merge section 7 into section 4. The canonical formulation includes
PKCE and excludes the deprecated flow. Delete section 7. Rename section 4 if
needed. Check all references to the deprecated flow throughout the document.

### Example B: Research report with accumulated findings

**Symptom**: Sections are ordered chronologically by when findings became
available. Section 2 covers Q1 data. Section 5 covers Q2 data that
supersedes part of Q1. Section 8 is a late-added synthesis. The reader must
read the whole document to assemble the current picture.

**Diagnosis**: Architectural accretion (pure). The structure is a timeline of
the research, not an exposition of the findings.

**Fix**: Restructure around thematic axes (e.g., by metric or by business
unit), not by quarter. Integrate Q1 and Q2 data into unified sections.
The synthesis section becomes either the introduction or an executive summary,
not an afterthought at section 8.

### Example C: Policy document with amendments

**Symptom**: Section 3 states policy X. Section 9 is titled "Amendments to
Section 3" and modifies policy X with exceptions. A footnote in section 3
says "see section 9 for amendments."

**Diagnosis**: Resolution inconsistency (qualification-chain variant). The
reader must mentally compose sections 3 and 9 to know the actual policy.

**Fix**: Rewrite section 3 to state the policy *as amended*. Include the
exceptions inline. If the amendment history matters for audit purposes,
add a "Revision History" appendix — separate from the operative text.
