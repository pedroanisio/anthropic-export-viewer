---
name: assess-corpus
description: Formal document assessment against a search-constructed reference corpus
tags: [review, assess, corpus]
---
You are performing a FORMAL DOCUMENT ASSESSMENT of document E
using search capabilities to construct a reference corpus.

## STRICT PHASE PROTOCOL — execute in order, do not interleave

### PHASE 0: DOMAIN TAXONOMY
Extract all non-trivial claims from E.
Map each to a recognized taxonomy (ACM CCS, MSC, MeSH, JEL, LoC).
Output the domain intersection profile D(E).
DO NOT SEARCH YET.

### PHASE 1: CORPUS CONSTRUCTION
For each domain in D(E): execute exactly 3 search queries.
Select exactly 3 seminal publications per domain.
Record: title, authors, year, venue, key claims, relevance to E.
For domain intersections: 1 bonus cross-domain query.
AFTER THIS PHASE: NO MORE SEARCHING. Corpus is FROZEN as T_O.

### PHASE 2: COHERENCE CHECK (T-free, over E alone)
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

### PHASE 3: NOVELTY CLASSIFICATION
For each claim in E: classify as KNOWN / RECOMBINATION /
NOVEL / CONTRADICTS with mandatory evidence.

### PHASE 4: COMPLETENESS CHECK
For each key claim in T_O: classify as ADDRESSED /
ACKNOWLEDGED / SCOPED_OUT / BLIND_SPOT / CONTRADICTED_SILENTLY.

### PHASE 5: UTILITY PROFILE
Assess: explanatory power, generative capacity,
unification value, practical delta.
Concrete evidence required for each — no vague praise.

### PHASE 6: DECISION
Apply gate logic. Output: GO / NO_GO / CONDITIONAL_GO
Attach all profiles.

## CONSTRAINTS
- Severity claims require proof or counterexample.
- Novelty claims require citation or gap identification.
- Utility claims require concrete examples.
- No search after Phase 1 completion.
- No improvement suggestions anywhere.
- If uncertain about classification: state uncertainty
  explicitly and choose the MORE CONSERVATIVE option.
