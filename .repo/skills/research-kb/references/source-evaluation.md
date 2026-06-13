# Source Evaluation Criteria

Detailed criteria for assessing whether a source qualifies for each tier
and how to handle edge cases.

---

## Tier 1: Peer-Reviewed Papers, Standards, RFCs

**Qualifies if:**
- Published in a peer-reviewed journal or conference proceedings
- Issued by a recognized standards body (IEEE, ISO, IETF, W3C, NIST, etc.)
- Is an RFC with "Standards Track" or "Informational" status
- Appears on a recognized preprint server (arXiv, SSRN) AND has been
  cited by T1 sources or accepted at a known venue

**Does NOT qualify if:**
- Preprint with zero citations and no venue acceptance
- Self-published "white paper" by a company (→ T2 or T4)
- Conference workshop paper without peer review (→ T4)

**Edge cases:**
- arXiv papers by well-known research labs (Google Brain, DeepMind, FAIR)
  with significant citations: treat as T1 with a note
- Retracted papers: exclude entirely, note the retraction
- Foundational papers older than 10 years: include if still canonical,
  flag age

---

## Tier 2: Official Documentation, Specifications

**Qualifies if:**
- Published by the maintainer/creator of the technology it describes
- Is a language specification, API reference, or protocol specification
- Is a W3C Recommendation, WHATWG Living Standard, or equivalent
- Is official documentation hosted on the project's primary domain

**Does NOT qualify if:**
- Third-party documentation or "unofficial guides" (→ T4)
- README files or changelogs (may contain useful data, but → T4)
- Marketing pages or product announcements (→ T4 at best)

**Edge cases:**
- GitHub issues/PRs by core maintainers discussing implementation
  details: T2 for the specific technical claim, T4 for opinions
- Official blog posts by the maintaining org: T2 if announcing specs
  or documenting behavior, T4 if opinion/strategy

---

## Tier 3: Verified Datasets, Reproducible Benchmarks

**Qualifies if:**
- Published benchmark with documented methodology and reproducible
  results
- Dataset with a clear data card or documentation of collection process
- Results independently reproduced or verified by multiple parties
- Hosted on recognized platforms (Papers With Code, Hugging Face with
  documented evaluation, MLCommons)

**Does NOT qualify if:**
- Self-reported benchmarks by the technology's creator with no
  independent verification (→ T4, note the bias risk)
- Benchmarks without disclosed methodology
- "Benchmarks" that are actually marketing comparisons

**Edge cases:**
- Company-published benchmarks on their own hardware: T3 if methodology
  is fully disclosed, T4 otherwise
- Crowdsourced benchmarks (e.g., LMSYS Chatbot Arena): T3 with a note
  about methodology limitations

---

## Tier 4: High-Quality Technical Articles

**Qualifies if:**
- Author has verifiable credentials in the domain (academic position,
  core contributor, recognized practitioner)
- Contains concrete technical detail, not just opinions
- Published on a recognized platform or personal site of a known expert
- Dated (undated → T5)

**Does NOT qualify if:**
- Author unknown or not verifiable
- Content is primarily opinion, speculation, or promotional
- Aggregator content that summarizes other sources without adding
  analysis
- SEO-optimized content farms

**Edge cases:**
- Well-known practitioners' blog posts (e.g., a systems researcher's
  detailed analysis): T4
- Company engineering blogs (Netflix Tech Blog, Uber Engineering):
  T4 — good technical content but inherent bias toward their own stack

---

## Tier 5: Community Knowledge (Corroboration Only)

Includes: Stack Overflow answers, Reddit threads, Hacker News discussions,
tutorials, YouTube transcripts, forum posts, undated articles, anonymous
authors.

**Usage rules:**
- NEVER cite T5 as the sole source for any KB claim
- T5 can corroborate a T1–T4 claim: "also discussed in [T5 source]"
- T5 can signal a gap: "community discussion suggests [X] but no
  formal source confirms it"
- Multiple T5 sources agreeing does NOT upgrade them to T4

---

## Cross-Tier Conflict Resolution

When sources from different tiers disagree:

1. **T1 vs T4**: T1 wins unless T4 cites newer empirical data that
   post-dates the T1 source. In that case, flag the conflict.

2. **T1 vs T1**: Present both. Note methodology differences. Do not
   pick a winner — downstream skills decide.

3. **T2 vs T2**: The more recent specification wins for "current
   behavior." Both are relevant for "historical behavior."

4. **Any tier vs T5**: The higher-tier source wins. T5 disagreement
   is noted only if it might signal that the higher-tier source is
   outdated.

5. **No source vs training data**: If Claude "knows" something but no
   search result confirms it, it does NOT go in the KB. It can go in
   a footnote marked `[TRAINING DATA — UNVERIFIED]` if the user is
   informed.
