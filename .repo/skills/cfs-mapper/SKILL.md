---
name: cfs-mapper
description: >
  Map any content — articles, news, books (fiction and non-fiction), scriptures,
  legal filings, transcripts, technical documentation, academic papers — into a
  valid Claim Formalization Schema (CFS) v0.5.0 JSON instance. Use this skill
  whenever the user asks to "formalize", "extract claims from", "map to CFS",
  "analyze the argument structure of", "decompose the logic of", or otherwise
  convert textual content into structured claim graphs. Also trigger when the
  user uploads or pastes content and asks for "propositions", "claim extraction",
  "argument mapping", "logical decomposition", "epistemic analysis", or
  "narrative formalization". This skill handles all source kinds: journalism,
  technical_documentation, legal_filing, policy_paper, transcript, academic_paper,
  fiction, scripture, and other. Even if the user does not mention CFS by name,
  trigger this skill whenever structured claim extraction from text is requested.
---

# CFS Mapper

Map any textual content into a valid **Claim Formalization Schema (CFS) v0.5.0**
JSON instance that passes both Zod structural parsing and programmatic
referential-integrity validation.

## Before you begin

1. Read `references/cfs-schema-reference.md` — it contains the full type
   inventory, enum values, and validation rules (V1–V21, L1–L10) you must
   satisfy.
2. Read `references/mapping-guide.md` — it contains decision tables and
   worked examples for each content type.

These two files are your ground truth. Do not guess enum values or field
constraints from memory; confirm against the reference.

---

## Core Workflow

### Phase 1 — Classify the Source

Determine these three properties before extracting anything:

| Property | How to decide |
|---|---|
| `source_kind` | Match the genre to one of: `journalism`, `technical_documentation`, `legal_filing`, `policy_paper`, `transcript`, `academic_paper`, `fiction`, `scripture`, `other`. |
| `truth_regime` | `realist` for empirical claims about the real world. `diegetic` for fiction (claims true *within the story*). `scriptural` for sacred texts with doctrinal authority. `mixed` when the text blends regimes (e.g., historical fiction, exegesis). |
| `narrative_frame` | **Required** when `source_kind ∈ {fiction, scripture}` or `truth_regime ∈ {diegetic, scriptural}`. Build the `layers` array from outermost narrator inward. |

If `source_kind` is fiction or scripture, or `truth_regime` is diegetic or
scriptural, you **must** populate `narrative_frame` — the schema enforces this
(V17). Failure to do so is a parse error.

### Phase 2 — Entity Extraction

Scan the content and register every agent, organization, place, or notable
object as an `Entity`.

**Rules**:
- IDs are `UPPER_SNAKE_CASE` (`/^[A-Z][A-Z0-9_]*$/`).
- IDs must **not** collide with reserved prefixes `P`, `R`, `Q`, `S`, `A`
  followed by digits (e.g., `P1` is invalid as an entity ID).
- Choose `ontological_status` carefully: `real` for real-world, `fictional`
  for in-story, `disputed` for contested existence, `traditional` for
  figures whose historicity is a matter of tradition rather than evidence.
- Assign `roles` generously — they feed lint rule L7 (revelation without
  authority role).
- Use `affiliations`, `developer`, `parent`, `founder`, `associated_with`,
  `location` to link entities. Every ID referenced here must be declared.
- For fiction/scripture: include the narrator(s) and audience(s) referenced
  in `narrative_frame` as entities.
- For journalism: include an `Editorial_Voice` entity for the publication
  whenever editorial synthesis or unsigned editorial claims appear.

### Phase 3 — Proposition Extraction

This is the core analytical step. For each substantive claim in the text,
create a `Proposition`.

**Decision checklist per proposition**:

1. **`speaker`**: Who is making this claim? Must be a declared EntityID.
2. **`claim`**: State the claim in your own words as a clear, atomic
   declarative sentence. One claim per proposition — do not bundle.
3. **`speech_act`**: Choose from `assertion`, `directive`, `recommendation`,
   `definition`, `editorial`, `prediction`, `narration`, `characterization`,
   `figuration`, `revelation`. See the mapping guide for content-type-specific
   heuristics.
4. **`verifiability`**: Choose from `machine_verifiable`,
   `empirically_testable`, `expert_judgment`, `unfalsifiable`,
   `diegetic_fact`, `diegetic_testimony`, `traditional_doctrine`.
   - Under `scriptural` regime: avoid `machine_verifiable` (lint L1).
   - Under `diegetic` regime: avoid `machine_verifiable` (lint L2).
5. **`fidelity`**: How faithfully does the source render this claim?
   `verbatim_quote`, `close_paraphrase`, `loose_paraphrase`,
   `editorial_synthesis`, `authorial_construction`.
6. **`literal`**: Default `true`. Set to `false` for metaphors, irony,
   hyperbole. If `speech_act` is `figuration`, `literal` **must** be `false`
   (V18).
7. **`provenance`**: Use when the claim passed through intermediaries.
   Min 2 hops. `provenance[0].speaker` must equal the proposition's
   `speaker` (V19). Chain runs outer→inner.
8. **`anchor`**: Optional locator within the source (page, paragraph,
   chapter, verse, timestamp).

**Quantity guidance**: Extract *substantive* claims — aim for thorough coverage
of the text's argumentative or narrative structure, but do not pad with trivial
restatements. A short article might yield 5–15 propositions; a book chapter
20–50; a scripture passage 10–30.

### Phase 4 — Axiom Identification

Axioms are unstated foundational assumptions the text relies upon but does
not argue for. They are background premises.

- Mark `controversial: true` when the axiom is debatable (feeds lint L8).
- Assign a `domain` when the axiom belongs to a specific field.
- Axioms are optional (the array can be empty), but look for them — they
  are epistemically important.

### Phase 5 — Rule Construction

Rules express logical or argumentative relations between propositions and/or
axioms.

- `antecedent_ids` and `consequent_ids` accept only `P<n>` or `A<n>` IDs.
- `relation_type` must match the `form` arrow (lint L5):
  `entails` → `→`, `motivates` → `⇝`, `contradicts` → `⇄`,
  `weakens` → `↓`, `strengthens` → `↑`, `is_consistent_with` → `∥`,
  `presupposes` → `⊲`, `refines` → `≻`, `mirrors` → `⇔`.
- `plain` is a human-readable restatement of the rule.
- Watch for lint L3 (entails from unfalsifiable), L8 (controversial axiom
  in rule), L10 (cross-regime entailment under mixed).

### Phase 6 — Open Questions

Identify at least one genuine question the text raises, leaves unanswered,
or that a critical reader would ask.

- `kind`: `factual`, `conceptual`, `methodological`, `ethical`.
- `related`: At least one ID. Can reference `P`, `R`, `A`, `S`, or
  Entity IDs — but **not** other `Q` IDs.

### Phase 7 — Silences

Silences capture what the text *doesn't* say. These are critical for
intellectual honesty.

- `kind`: `absent_perspective`, `unasked_question`, `suppressed_counter`,
  `missing_context`.
- `related_propositions`: At least one `P<n>` ID.
- `affected_entities`: Optional list of EntityIDs impacted by the silence.
- Silences are optional at the schema level, but the skill should always
  attempt to identify at least one unless the text is genuinely exhaustive
  (rare).

### Phase 8 — Assembly & Self-Validation

Before emitting the final JSON:

1. **ID uniqueness (V4)**: Every ID in each namespace must be unique.
2. **Referential integrity (V8–V12)**: Every EntityID, PropositionID,
   AxiomID, RuleID, SilenceID referenced anywhere must be declared.
3. **V17**: `narrative_frame` present when required.
4. **V18**: `figuration` ⟹ `literal: false`.
5. **V19**: `provenance[0].speaker == proposition.speaker`.
6. **V20**: Provenance chain length ≥ 2 when present.
7. **Lint scan**: Check L1–L10 and resolve or annotate.
8. **`schema_version`**: Always `"0.5.0"`.

Walk through these checks mentally before outputting. If you find a
violation, fix it — do not emit invalid JSON.

---

## Output Format

Emit a single JSON code block (` ```json ... ``` `) containing the full
`CfsInstance`. The JSON must:

- Be valid JSON (no trailing commas, no comments).
- Parse successfully against the CFS v0.5.0 Zod schema.
- Pass the `validate()` referential integrity checks with zero errors.
- Minimize lint warnings (zero is ideal, but some are acceptable if
  annotated in `note` fields).

If the content is very long (full book, lengthy scripture), offer to
formalize it chapter-by-chapter or section-by-section, each as a
separate CFS instance. Ask the user how they want to scope it.

---

## Important Reminders

- **Never invent claims not present in the source.** Every proposition must
  trace back to something the text actually says or clearly implies.
- **Distinguish speaker from author.** In journalism, the journalist reports
  what sources say — track provenance. In fiction, the narrator speaks, not
  the author.
- **Axioms are unstated.** If the text argues for it, it's a proposition,
  not an axiom.
- **Be honest about verifiability.** Don't upgrade `expert_judgment` to
  `machine_verifiable` or downgrade `unfalsifiable` to `empirically_testable`.
- **Silences matter.** The absence of counterargument, alternative
  perspective, or context is itself a finding.
- **When in doubt, add a `note`.** The `note` field exists on most objects.
  Use it to flag uncertainty, editorial judgment calls, or caveats.
