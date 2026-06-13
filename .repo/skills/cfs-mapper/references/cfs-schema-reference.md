# CFS v0.5.0 — Schema Reference

> This file is the authoritative reference for the CFS Mapper skill.
> Consult it whenever you need to confirm a type, enum value, or validation rule.

---

## Top-Level Structure (`CfsInstance`)

```
{
  schema_version: "0.5.0",          // REQUIRED — only "0.5.0"
  meta:           Meta,              // REQUIRED
  entities:       Entity[],          // REQUIRED — min 1
  propositions:   Proposition[],     // REQUIRED — min 1
  axioms:         Axiom[],           // REQUIRED — may be empty []
  rules:          Rule[],            // REQUIRED — min 1
  open_questions: Question[],        // REQUIRED — min 1
  silences:       Silence[]          // OPTIONAL
}
```

---

## ID Patterns

| Namespace   | Regex            | Examples         |
|-------------|------------------|------------------|
| Proposition | `/^P\d+$/`       | P1, P2, P42      |
| Rule        | `/^R\d+$/`       | R1, R2           |
| Question    | `/^Q\d+$/`       | Q1, Q2           |
| Silence     | `/^S\d+$/`       | S1, S2           |
| Axiom       | `/^A\d+$/`       | A1, A2           |
| Entity      | `/^[A-Z][A-Z0-9_]*$/` — must NOT match `[PRQSA]\d+` | NYT, JOHN_DOE, GOOGLE, NARRATOR |

---

## Enums — Complete Lists

### SourceKind
`journalism` · `technical_documentation` · `legal_filing` · `policy_paper` · `transcript` · `academic_paper` · `fiction` · `scripture` · `other`

### TruthRegime
`realist` · `diegetic` · `mixed` · `scriptural`

### NarratorReliability
`reliable` · `unreliable` · `indeterminate` · `divinely_authorized`

### EntityType
`Person` · `Organization` · `Government_Agency` · `Software_System` · `Software_Module` · `Hardware` · `Document` · `Event` · `Editorial_Voice` · `Place` · `Polity` · `Collective` · `Manifestation`

### OntologicalStatus
`real` · `fictional` · `semi_fictional` · `disputed` · `traditional`

### SpeechAct
`assertion` · `directive` · `recommendation` · `definition` · `editorial` · `prediction` · `narration` · `characterization` · `figuration` · `revelation`

### Verifiability
`machine_verifiable` · `empirically_testable` · `expert_judgment` · `unfalsifiable` · `diegetic_fact` · `diegetic_testimony` · `traditional_doctrine`

### Fidelity
`verbatim_quote` · `close_paraphrase` · `loose_paraphrase` · `editorial_synthesis` · `authorial_construction`

### RelationType
`entails` · `motivates` · `contradicts` · `weakens` · `strengthens` · `is_consistent_with` · `presupposes` · `refines` · `mirrors`

### QuestionKind
`factual` · `conceptual` · `methodological` · `ethical`

### SilenceKind
`absent_perspective` · `unasked_question` · `suppressed_counter` · `missing_context`

---

## Compound Types

### Meta

```
{
  source:          string,              // min 1 char — name of publication / book / etc.
  author:          string[],            // min 1 element — author name(s)
  published:       Published,           // see below
  title:           string,              // min 1 char
  source_kind:     SourceKind,
  truth_regime:    TruthRegime,
  locator:         string?,             // URL, DOI, ISBN, etc.
  narrative_frame: NarrativeFrame?,     // REQUIRED when source_kind ∈ {fiction, scripture}
                                        //   OR truth_regime ∈ {diegetic, scriptural}  (V17)
  note:            string?
}
```

**Published** — one of:
- `"undated"`
- `"YYYY"` (e.g., `"2024"`)
- `"YYYY-MM"` (e.g., `"2024-03"`)
- `"YYYY-MM-DD"` (e.g., `"2024-03-15"`)
- Full ISO 8601 datetime (e.g., `"2024-03-15T10:30:00Z"`)

### NarrativeFrame / NarrativeLayer

```
NarrativeFrame = { layers: NarrativeLayer[] }   // min 1 layer

NarrativeLayer = {
  narrator:    EntityId,              // must be declared in entities
  audience:    EntityId?,             // must be declared if present
  reliability: NarratorReliability,
  note:        string?
}
```

### ProvenanceHop / ProvenanceChain

```
ProvenanceHop = {
  speaker: EntityId,     // must be declared
  medium:  string?       // e.g., "interview", "press release", "oral tradition"
}

ProvenanceChain = ProvenanceHop[]    // min 2 elements (V20)
```

---

## Entity

```
{
  id:                EntityId,            // UPPER_SNAKE_CASE, no reserved collision
  type:              EntityType,
  ontological_status: OntologicalStatus,  // default: "real"
  roles:             string[],            // default: []
  affiliations:      EntityId[],          // default: [] — each must be declared
  domain:            string?,
  developer:         EntityId?,           // must be declared
  parent:            EntityId?,           // must be declared
  founder:           EntityId?,           // must be declared
  associated_with:   EntityId?,           // must be declared
  location:          EntityId?,           // must be declared
  note:              string?
}
```

---

## Proposition

```
{
  id:            PropositionId,     // P1, P2, ...
  speaker:       EntityId,          // must be declared (V8)
  medium:        string?,
  claim:         string,            // min 1 char — the substantive claim
  speech_act:    SpeechAct,
  verifiability: Verifiability?,
  fidelity:      Fidelity?,
  provenance:    ProvenanceChain?,  // min 2 hops if present (V20)
                                    // provenance[0].speaker == speaker (V19)
  literal:       boolean,           // default: true
                                    // MUST be false if speech_act == "figuration" (V18)
  anchor:        string?,           // locator within source
  note:          string?
}
```

---

## Axiom

```
{
  id:            AxiomId,       // A1, A2, ...
  name:          string,        // min 1 char
  definition:    string,        // min 1 char
  domain:        string?,
  controversial: boolean,       // default: false
  note:          string?
}
```

---

## Rule

```
{
  id:                 RuleId,          // R1, R2, ...
  name:               string,         // min 1 char
  relation_type:      RelationType,
  antecedent_ids:     (P<n>|A<n>)[],  // min 1
  consequent_ids:     (P<n>|A<n>)[],  // min 1
  form:               string?,        // symbolic expression — arrow must match relation_type (L5)
  plain:              string,         // min 1 char — human-readable restatement
  analytic_framework: string?,
  note:               string?
}
```

**Arrow ↔ RelationType (L5)**:
| relation_type      | Expected arrow |
|--------------------|---------------|
| entails            | →             |
| motivates          | ⇝             |
| contradicts        | ⇄             |
| weakens            | ↓             |
| strengthens        | ↑             |
| is_consistent_with | ∥             |
| presupposes        | ⊲             |
| refines            | ≻             |
| mirrors            | ⇔             |

---

## Question

```
{
  id:       QuestionId,     // Q1, Q2, ...
  question: string,         // min 1 char
  kind:     QuestionKind,
  related:  RelatedId[]     // min 1 — P, R, A, S, or Entity IDs. NO Q IDs.
}
```

---

## Silence

```
{
  id:                   SilenceId,        // S1, S2, ...
  kind:                 SilenceKind,
  description:          string,           // min 1 char
  affected_entities:    EntityId[],       // default: [] — each must be declared
  related_propositions: PropositionId[],  // min 1
  note:                 string?
}
```

---

## Validation Rules Summary

### Structural (Zod pass 1)

| Rule | Check |
|------|-------|
| V1–V7 | Type and shape checks on all fields (enforced by Zod types) |
| V13–V21 | Regex patterns, min lengths, array minimums, enum membership |
| V17 | `narrative_frame` required when `source_kind ∈ {fiction, scripture}` or `truth_regime ∈ {diegetic, scriptural}` |
| V18 | `speech_act == "figuration"` ⟹ `literal == false` |
| V19 | `provenance[0].speaker == proposition.speaker` |
| V20 | Provenance chain min length 2 |

### Referential Integrity (pass 2 — `validate()`)

| Rule | Check |
|------|-------|
| V4  | All IDs unique within their namespace |
| V8  | Every EntityID reference resolves to a declared entity |
| V9  | Every PropositionID reference resolves to a declared proposition |
| V10 | Every AxiomID reference resolves to a declared axiom |
| V11 | Every RuleID and SilenceID reference resolves |
| V12 | Question.related cannot contain QuestionIDs |

### Lint Warnings (pass 2)

| Rule | Condition |
|------|-----------|
| L1 | `machine_verifiable` under `scriptural` regime |
| L2 | `machine_verifiable` under `diegetic` regime |
| L3 | `entails` from `unfalsifiable` antecedent |
| L4 | Non-literal `assertion` or `definition` |
| L5 | Rule `form` arrow doesn't match `relation_type` |
| L6 | Provenance chain > 4 hops |
| L7 | `revelation` speech act but speaker lacks authority role |
| L8 | Controversial axiom used in a rule |
| L9 | `traditional_doctrine` under non-scriptural/non-mixed regime |
| L10 | Cross-regime entailment: diegetic/scriptural antecedents → realist consequents under `mixed` |
