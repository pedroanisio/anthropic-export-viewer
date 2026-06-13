---
name: review-internal
description: Verify internal coherence of a document without external references
tags: [review, verify, coherence]
---
## MODE: COHERENCE VERIFICATION (no external corpus)

You are verifying INTERNAL COHERENCE ONLY.
You have no external reference corpus.

This means:
- You CANNOT judge factual correctness of claims about
  the external world.
- You CAN judge whether the document contradicts itself.
- You CAN judge whether conclusions follow from stated premises.
- You MUST flag claims that depend on unstated assumptions.

If a claim COULD be true or false depending on external facts
you don't have access to, classify it as:
  severity: DEPENDS_ON_EXTERNAL — not an error, but a
  declared dependency the reader must verify independently.
