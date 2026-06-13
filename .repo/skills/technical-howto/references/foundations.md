# Foundations Reference

---
disclaimer: >
  No information within this document should be taken for granted. Any
  statement or premise not backed by a real logical definition or verifiable
  reference may be invalid, erroneous, or a hallucination. Sources are cited
  where possible; verify independently.
---

This document provides the theoretical and empirical grounding for the
decisions made in the technical-howto skill. Read this when you need to
understand WHY a particular rule exists, or when a user challenges a
recommendation.

---

## 1. Diátaxis Documentation Framework

**Source:** Daniele Procida. Originally published as "The Documentation
System" at documentation.divio.com, later renamed Diátaxis and moved to
diataxis.fr.

### Core Claim

Documentation has four distinct functions — tutorials, how-to guides,
reference, and explanation — and each requires a different writing mode.
Mixing them degrades all of them.

### Why It Matters for This Skill

The single most common structural failure in technical how-to guides is
genre contamination: a how-to that also tries to teach (tutorial), also
tries to list every parameter (reference), and also tries to explain the
underlying theory (explanation). The result satisfies none of these needs
well.

### The Four Quadrants

| Quadrant    | Orientation       | Reader's Need               | Analogy         |
|-------------|-------------------|-----------------------------|-----------------|
| Tutorial    | Learning          | "Help me get started"       | A cooking lesson|
| How-To      | Goal completion   | "Help me solve this problem"| A recipe        |
| Reference   | Information       | "Give me the exact specs"   | An encyclopedia |
| Explanation | Understanding     | "Help me understand why"    | A journal article|

### Key Distinctions for How-To Guides

From the Diátaxis framework:

- A how-to guide addresses a specific question or problem.
- It assumes the reader has baseline competence.
- It contains ordered steps but does not need to start from zero.
- Practical usability outweighs completeness.
- The title should tell the reader exactly what the guide does.
- How-to guides should allow for slight variations — enough flexibility
  for the reader to adapt, but not so much that the guide becomes vague.

### Limitations

The Diátaxis framework is a structural taxonomy, not an empirical finding
from controlled studies. It is based on extensive practitioner experience
across open-source and commercial projects. It has been widely adopted
(Django, Kubernetes, Cloudflare, Gatsby, many others) but lacks formal
experimental validation comparing documentation organized this way vs.
alternative structures.

---

## 2. Cognitive Load Theory (CLT)

**Source:** John Sweller. "Cognitive Load During Problem Solving: Effects
on Learning." Cognitive Science 12(2), 1988, pp. 257-285. Extended in
numerous subsequent publications through 2023.

### Core Claim

Working memory has a limited capacity (~4 chunks for novel information,
per Cowan 2001). Learning is optimized by reducing extraneous cognitive
load (load caused by poor presentation) while preserving germane load
(load that builds useful mental schemas).

### Three Types of Cognitive Load

1. **Intrinsic load.** The inherent difficulty of the subject matter.
   Determined by element interactivity — how many elements must be
   processed simultaneously. Cannot be reduced without reducing the
   complexity of the material itself.

2. **Extraneous load.** Load caused by how the information is presented,
   not by the information itself. This is the load that instructional
   design can and should minimize. Examples: poor formatting, unnecessary
   jargon, tangential information, split-attention between text and
   diagrams.

3. **Germane load.** The cognitive effort devoted to building and
   automating schemas (mental models). This is the "useful" load —
   the one that produces actual learning or skill acquisition.

### Application to How-To Guides

In a how-to context, the reader's goal is task completion, not learning.
This shifts the CLT calculus:

- **Minimize intrinsic load** by decomposing complex operations into
  single-action steps (one action per step rule).

- **Eliminate extraneous load** by removing inline explanations, tangential
  tips, undefined jargon, and any content that doesn't directly serve
  task completion.

- **Germane load is not the primary concern** in a how-to. The reader is
  not trying to build new schemas — they're trying to finish a task. If
  germane load matters (the reader wants to understand, not just do),
  they need an explanation document, not a how-to.

### The ~4 Chunk Limit

Cowan (2001) revised Miller's famous "7 ± 2" estimate downward. The
current consensus is approximately 4 chunks of novel information in
working memory at a time. This directly constrains step design:

- A step that requires the reader to hold more than ~4 novel elements
  simultaneously is likely to fail. Split it.

- Prerequisites that are not in the reader's long-term memory (i.e., not
  yet "chunked") each consume a working memory slot. This is why
  audience calibration matters — a step that's trivial for an expert
  (who has pre-chunked the concepts) is impossible for a novice (who
  hasn't).

### References

- Sweller, J. (1988). "Cognitive Load During Problem Solving: Effects on
  Learning." Cognitive Science, 12(2), 257-285.
- Cowan, N. (2001). "The Magical Number 4 in Short-Term Memory: A
  Reconsideration of Mental Storage Capacity." Behavioral and Brain
  Sciences, 24(1), 87-114.
- Sweller, J., Ayres, P., & Kalyuga, S. (2011). Cognitive Load Theory.
  Springer.
- Paas, F., Renkl, A., & Sweller, J. (2003). "Cognitive Load Theory and
  Instructional Design: Recent Developments." Educational Psychologist,
  38(1), 1-4.

---

## 3. Google Developer Documentation Style Guide

**Source:** Google. "Google Developer Documentation Style Guide."
Published 2017 (internal use since ~2005). Available at
developers.google.com/style.

### Relevant Principles

- Use second person, present tense, active voice.
- Use imperative mood for instructions.
- Write for a global audience: avoid idioms, slang, culturally specific
  references.
- Write for accessibility: support screen readers, use descriptive link
  text.
- Define abbreviations and acronyms on first use.
- Maintain consistent formatting, tone, and terminology.
- Guidelines, not rules — depart when doing so improves the content.

### Why This Guide and Not Others

The Google guide is the most comprehensive publicly available style guide
specifically for developer-facing technical documentation. Microsoft's
Writing Style Guide is comparable. Both are actively maintained.

The Google guide was chosen as the default because:
- It is free and publicly accessible.
- It is used for documentation across projects like Kubernetes, Dart,
  Android, and Google Cloud — all of which have large, diverse audiences.
- It explicitly addresses the needs of non-native English speakers and
  global audiences.

Organizations may have their own style guides. If the user specifies one,
follow theirs. The Google guide serves as the fallback default.

---

## 4. The "Maintaining User State" Principle

**Source:** Gernot Heiser. "Guide to Technical Writing."
gernot-heiser.org/style-guide.html. (Gernot Heiser is a Scientia
Professor at UNSW Sydney and Fellow of the ACM and IEEE.)

### Core Claim

The writer must maintain awareness of the reader's mental state at every
point in the document. New terms, concepts, or dependencies must not
appear without having been introduced or referenced. The reader's "state"
— what they know, what they've seen, what they can currently hold in
working memory — is the writer's responsibility.

### Application

This principle operationalizes CLT for sequential documents. In a how-to
guide, it means:

- Never use a term in Step N that wasn't defined in the prerequisites
  or a prior step.
- Never reference a file, service, or configuration that the reader
  hasn't created or been told to obtain.
- If a step changes the system state, subsequent steps must account for
  that change.
- Forward references ("we'll configure this later in Step 8") are
  acceptable only if the current step doesn't depend on the forward
  reference to succeed.

---

## 5. The Versioning and Freshness Problem

No single canonical source, but widely acknowledged in the documentation
community (Write the Docs, Google's 2021 Accelerate State of DevOps
Report, and common practitioner experience).

### The Problem

Technical how-to guides decay. Tools update, APIs change, defaults shift,
dependencies deprecate. A guide that worked in January may be actively
harmful by June. The decay is silent — the guide looks the same, but the
commands fail.

### Mitigation Strategies

1. **Pin all versions.** Every tool, language, library, and API version
   referenced in the guide must be explicit.

2. **Include a `last_verified` date.** This tells the reader when someone
   last confirmed the steps work end-to-end.

3. **Include a final verification step.** An end-to-end check that the
   reader can run to confirm everything works in their environment.

4. **Don't link to "latest" anything.** Link to specific versions of
   documentation, downloads, and dependencies.

These don't prevent decay, but they make decay visible — which lets the
reader calibrate their trust and the maintainer know when to update.
