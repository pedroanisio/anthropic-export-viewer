---
name: research-kb
description: >
  Build a source-grounded knowledge base on any subject BEFORE solving,
  building, or experimenting. Searches for formal information — papers,
  standards, RFCs, specs, datasets — evaluates source authority via a
  5-tier hierarchy, extracts claims with full provenance, identifies
  gaps and contradictions, and outputs a condensed .md KB. Trigger on:
  "research this first", "build a knowledge base", "what does the
  literature say", "gather formal sources", "find papers on", "state
  of the art", "ground this in evidence", "survey the field",
  "literature review", "prior art search", "what do we actually know
  about", "evidence base for", or any request to gather verified
  information before work begins. Also trigger when combining a problem
  with "research", "sources", "papers", or "formal". Should run BEFORE
  experiment-lab, multi-agent-deliberation, or implementation.
---

# Research Knowledge Base Builder

Systematically gather, evaluate, and organize formal knowledge on a
subject into a condensed, provenance-tracked knowledge base — before
any problem-solving begins.

## Why This Exists

Most AI-assisted work starts from vibes: the model generates plausible-
sounding content from training data, the user accepts it, and neither
party knows which claims are grounded and which are confabulation. This
skill inverts that pattern. It forces a research phase that produces an
explicit artifact — a knowledge base — where every claim traces to a
verifiable source, every gap is named, and every contradiction is surfaced.
The KB then becomes the foundation that other skills (experiment-lab,
multi-agent-deliberation, implementation) build on.

The goal is not comprehensiveness for its own sake. The goal is to know
what we know, know what we don't know, and never confuse the two.

---

## Source Authority Hierarchy

The skill evaluates sources in strict priority order. Higher-tier sources
override lower-tier sources when they conflict.

| Tier | Source Type | Trust Level | Examples |
|------|-----------|-------------|---------|
| T1 | Peer-reviewed papers, formal standards, RFCs | Highest | IEEE, ACM, IETF RFCs, ISO standards |
| T2 | Official documentation, specifications | High | Language specs, API docs, W3C recommendations |
| T3 | Verified datasets, reproducible benchmarks | High | Papers With Code leaderboards, official benchmarks |
| T4 | High-quality technical articles | Moderate | Authoritative blog posts by known experts, conference talks |
| T5 | Community knowledge | Low — corroboration only | Stack Overflow, forums, tutorials |

**Rules:**
- T5 sources never stand alone. They can corroborate T1–T4 claims only.
- When T1 and T4 conflict, T1 wins unless T1 is outdated and T4 cites
  newer evidence (flag the conflict explicitly).
- Undated sources are treated as T5 regardless of apparent quality.

See `references/source-evaluation.md` for detailed evaluation criteria.

---

## Core Workflow

```
SUBJECT/PROBLEM
      │
      ▼
┌─────────────┐
│  DECOMPOSE  │  Break subject into searchable facets
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   SEARCH    │  Multi-query systematic search, tier-aware
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  EVALUATE   │  Rank sources by authority, filter noise
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   EXTRACT   │  Fetch top sources, extract claims + evidence
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ SYNTHESIZE  │  Organize into structured KB with provenance
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  GAP AUDIT  │  What's missing, contradictory, or uncertain
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   OUTPUT    │  Produce .md KB + Google Drive backup
└─────────────┘
```

---

### Phase 1: DECOMPOSE — Break the Subject into Facets

Do NOT search yet. First, analyze the problem statement and decompose it
into orthogonal searchable facets.

**Produce a facet map:**

```
SUBJECT: "Optimizing transformer inference latency"

FACETS:
  ├── theoretical: attention complexity, KV-cache mechanics
  ├── algorithmic: quantization methods, pruning, distillation
  ├── systems: GPU memory hierarchy, batching strategies, kernel fusion
  ├── benchmarks: which models, which hardware, standard metrics
  └── frontier: speculative decoding, mixture-of-experts routing
```

Each facet becomes a search campaign. Facets should be:
- **Orthogonal**: minimal overlap so we don't waste searches
- **Concrete**: specific enough to yield precise search queries
- **Bounded**: each facet should map to 2–4 search queries max

Present the facet map to the user and ask: "Does this cover the right
ground? Any facets to add or remove?" Adjust before proceeding.

---

### Phase 2: SEARCH — Systematic Multi-Query Search

For each facet, construct 2–4 search queries optimized for the source
hierarchy:

**Query construction rules:**
- Lead with formal terms: "survey", "benchmark", "RFC", "specification",
  "standard", paper titles, author names
- Include year constraints for fast-moving fields (append current year
  or "2024 2025 2026" as appropriate)
- Avoid meta-words: don't search "best practices" or "how to" — these
  pull T5 content
- Use domain-specific vocabulary, not colloquial descriptions

**Search budget:** Scale to complexity.
- Narrow, well-defined subject: 6–10 searches total
- Broad or interdisciplinary subject: 15–25 searches total
- Deep research request: up to 40 searches, but warn the user it will
  take time

**For each search result, record immediately:**
- URL
- Title
- Source tier (T1–T5)
- Date (if identifiable)
- One-line relevance note

Discard T5-only results unless nothing better exists for that facet.
If a facet yields only T5 results, flag it as an **evidence gap**.

---

### Phase 3: EVALUATE — Source Authority Assessment

After the search sweep, rank all collected sources:

1. **De-duplicate**: same content at multiple URLs → keep highest-tier
2. **Date-check**: discard sources older than 5 years for fast-moving
   fields (unless they are foundational/canonical)
3. **Authority-check**: for T4 sources, verify the author has verifiable
   credentials in the domain
4. **Conflict-detect**: flag any two sources that make contradictory
   claims — these will be surfaced in the gap audit

Select the **top 8–15 sources** for full extraction. Prefer breadth
across facets over depth in one facet.

---

### Phase 4: EXTRACT — Fetch and Extract Claims

For each selected source, use `web_fetch` to retrieve full content.

**Extract into a structured format:**

```
SOURCE: [title]
URL: [url]
TIER: T[n]
DATE: [date]
DOMAIN FACET: [which facet this serves]

KEY CLAIMS:
  1. [claim in your own words] — [specific evidence from source]
  2. [claim] — [evidence]

DEFINITIONS:
  - [term]: [definition as given by this source]

DATA POINTS:
  - [metric/measurement]: [value] — [conditions/context]

LIMITATIONS NOTED BY SOURCE:
  - [what the source itself says it doesn't cover]
```

**Critical rules during extraction:**
- Paraphrase everything. Never copy verbatim from sources.
- Every claim must be attributable — no orphan statements.
- If a source makes a claim without evidence, mark it as
  `[UNSUPPORTED CLAIM]` and still record it (it may be corroborated
  elsewhere).
- If you cannot access a source (paywall, 403, etc.), record its
  metadata and mark it `[NOT FETCHED — reason]`.

---

### Phase 5: SYNTHESIZE — Build the Knowledge Base

Organize extracted knowledge into the KB template structure.
Read `references/kb-template.md` for the exact output format.

**Synthesis rules:**
- Group by concept, not by source. The KB is organized around what we
  know, not who said it.
- Every statement in the KB must have inline provenance: `[Source: title, tier]`
- When multiple sources agree, cite the highest-tier one and note
  corroboration: `[Source: ...; corroborated by: ...]`
- When sources disagree, present both positions and the evidence for
  each — do not pick a winner silently.
- Definitions should come from T1/T2 sources. If only T4/T5 definitions
  exist, flag it.

---

### Phase 6: GAP AUDIT — What We Don't Know

This section is as important as the confirmed knowledge. Produce:

**6a. Evidence Gaps**
Facets or sub-questions where no T1–T3 source was found.
```
GAP: No peer-reviewed benchmarks found for [specific technique] on
     [specific hardware]. Only T4 blog posts with unverified numbers.
IMPACT: Cannot make grounded claims about performance in this context.
REMEDIATION: [suggest what would fill this gap — specific paper, test, etc.]
```

**6b. Contradictions**
Pairs of sources that make conflicting claims.
```
CONTRADICTION:
  Source A (T1, 2024): "Technique X reduces latency by 40%"
  Source B (T2, 2025): "Technique X shows no significant improvement"
  POSSIBLE EXPLANATION: Different hardware, different model sizes
  RESOLUTION STATUS: Unresolved — needs controlled benchmark
```

**6c. Staleness Risks**
Claims that depend on information older than 2 years in a fast-moving
field.
```
STALE RISK: Claim about [topic] relies on [source, 2022]. Field has
  evolved significantly. Current validity: uncertain.
```

**6d. Confidence Map**
For each major section of the KB, assign a confidence level:
- **HIGH**: Multiple T1–T2 sources agree, recent, no contradictions
- **MEDIUM**: Single T1–T2 source, or T3 with corroboration, minor gaps
- **LOW**: Only T4–T5 sources, or contradictions exist, or stale data
- **SPECULATIVE**: No formal sources — included because relevant, but
  every claim is flagged

---

### Phase 7: OUTPUT — Produce and Persist

1. **Generate the KB** as a markdown file following `references/kb-template.md`
2. **Save locally** to `/mnt/user-data/outputs/kb-[subject-slug].md`
3. **Back up to Google Drive** using the gdrive-storage skill pattern
4. **Present to user** via `present_files`

After output, present a brief summary:
- Total sources consulted vs. sources used
- Tier distribution (how many T1, T2, etc.)
- Number of evidence gaps
- Number of contradictions
- Overall confidence assessment
- Suggested next steps (which gaps to fill, which skills to run next)

---

## Integration with Other Skills

The KB is designed to be consumed by downstream skills:

| Downstream Skill | How KB Integrates |
|-----------------|------------------|
| **experiment-lab** | KB → Phase 0 "Reference Material". Hypotheses should address KB gaps. |
| **multi-agent-deliberation** | KB → Problem context for all four agents. Critic should check claims against KB provenance. |
| **formal-completeness-checker** | KB claims → Propositions to formalize and verify. |
| **any implementation work** | KB → Design constraints and verified assumptions. |

When handing off to a downstream skill, explicitly state:
"The following knowledge base was built from [N] sources (T1: X, T2: Y, ...).
Gaps identified: [list]. Treat claims marked LOW or SPECULATIVE as hypotheses,
not facts."

---

## Anti-Patterns — What This Skill Must NOT Do

- **Never present training-data knowledge as researched knowledge.**
  If it didn't come from a search result with a URL, it doesn't go in
  the KB. Claude's "general knowledge" belongs in conversation, not in
  a provenance-tracked document.

- **Never silently resolve contradictions.** If sources disagree, the
  disagreement goes in the KB. The user or a downstream skill decides.

- **Never pad the KB with T5 sources to look comprehensive.** A short KB
  with high-confidence claims is more valuable than a long one full of
  forum posts.

- **Never skip the gap audit.** Even if the search went well, gaps exist.
  Find them.

- **Never hallucinate provenance.** If you can't trace a claim to a
  specific URL you fetched, do not invent a citation. Mark it
  `[PROVENANCE UNKNOWN — may be training data]`.
