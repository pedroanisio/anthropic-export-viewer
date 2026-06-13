# CFS Mapping Guide — Decision Tables & Examples

This reference covers content-type-specific strategies and a worked
example for each major `source_kind`.

---

## Table of Contents

1. [Classification Quick-Reference](#1-classification-quick-reference)
2. [Journalism Mapping](#2-journalism)
3. [Academic Paper Mapping](#3-academic-paper)
4. [Fiction Mapping](#4-fiction)
5. [Scripture Mapping](#5-scripture)
6. [Technical Documentation Mapping](#6-technical-documentation)
7. [Legal Filing Mapping](#7-legal-filing)
8. [Policy Paper Mapping](#8-policy-paper)
9. [Transcript Mapping](#9-transcript)
10. [Common Pitfalls](#10-common-pitfalls)

---

## 1. Classification Quick-Reference

| Content | source_kind | truth_regime | narrative_frame? | Typical speech_acts |
|---------|-------------|-------------|------------------|---------------------|
| News article | journalism | realist | No | assertion, editorial |
| Opinion/editorial | journalism | realist | No | editorial, prediction, recommendation |
| Peer-reviewed paper | academic_paper | realist | No | assertion, definition, prediction |
| Novel / short story | fiction | diegetic | **Yes** | narration, characterization, figuration |
| Historical fiction | fiction | mixed | **Yes** | narration, assertion (for real facts), characterization |
| Bible / Quran / Gita | scripture | scriptural | **Yes** | revelation, directive, narration, figuration |
| Exegesis / commentary | other or academic_paper | mixed | **Yes** (if quoting scripture) | assertion, editorial, definition |
| API docs / man pages | technical_documentation | realist | No | definition, directive, assertion |
| Court filing / statute | legal_filing | realist | No | assertion, directive, definition |
| Policy white paper | policy_paper | realist | No | assertion, recommendation, prediction |
| Interview / hearing | transcript | realist | No | assertion, directive, editorial |

---

## 2. Journalism

### Entity Strategy
- **Reporter** → `Person`, role: `["journalist"]`
- **Publication** → `Organization` or `Editorial_Voice`
- **Sources quoted** → `Person` / `Organization` with appropriate roles
- **Institutions mentioned** → `Organization`, `Government_Agency`, etc.

### Proposition Strategy
- **Direct quotes**: `fidelity: "verbatim_quote"`, speaker is the person quoted
- **Paraphrased claims**: `fidelity: "close_paraphrase"` or `"loose_paraphrase"`, speaker is the person paraphrased
- **Reporter's synthesis**: `speech_act: "editorial"`, `fidelity: "editorial_synthesis"`, speaker is the reporter or Editorial_Voice
- **Statistics / data points**: `verifiability: "machine_verifiable"` if checkable, `"empirically_testable"` otherwise
- **Expert opinions**: `verifiability: "expert_judgment"`

### Provenance
When a journalist reports what a source said, use provenance:
```json
{
  "id": "P3",
  "speaker": "SMITH",
  "claim": "The merger will close by Q3.",
  "speech_act": "prediction",
  "verifiability": "expert_judgment",
  "fidelity": "close_paraphrase",
  "provenance": [
    { "speaker": "SMITH", "medium": "interview" },
    { "speaker": "REUTERS", "medium": "wire report" }
  ]
}
```
Here the outer hop is Smith (the original speaker), the inner hop is Reuters (the relay).

### Silences to Look For
- Absent counter-sources
- Missing context (e.g., prior history, competing data)
- Unasked follow-up questions

### Worked Micro-Example — News Article

**Source**: "Reuters reports that CEO Jane Smith announced a 15% revenue increase. Analysts at Goldman Sachs called the figures 'surprisingly strong'."

```json
{
  "schema_version": "0.5.0",
  "meta": {
    "source": "Reuters",
    "author": ["Reuters Staff"],
    "published": "2024-11-20",
    "title": "Acme Corp Reports 15% Revenue Increase",
    "source_kind": "journalism",
    "truth_regime": "realist"
  },
  "entities": [
    { "id": "REUTERS", "type": "Organization", "roles": ["news_agency"] },
    { "id": "JANE_SMITH", "type": "Person", "roles": ["CEO"], "affiliations": ["ACME_CORP"] },
    { "id": "ACME_CORP", "type": "Organization", "roles": ["public_company"] },
    { "id": "GOLDMAN_SACHS", "type": "Organization", "roles": ["financial_analyst"] }
  ],
  "propositions": [
    {
      "id": "P1",
      "speaker": "JANE_SMITH",
      "claim": "Acme Corp's revenue increased by 15%.",
      "speech_act": "assertion",
      "verifiability": "machine_verifiable",
      "fidelity": "close_paraphrase",
      "provenance": [
        { "speaker": "JANE_SMITH", "medium": "corporate announcement" },
        { "speaker": "REUTERS", "medium": "wire report" }
      ]
    },
    {
      "id": "P2",
      "speaker": "GOLDMAN_SACHS",
      "claim": "The revenue figures were surprisingly strong.",
      "speech_act": "assertion",
      "verifiability": "expert_judgment",
      "fidelity": "close_paraphrase",
      "provenance": [
        { "speaker": "GOLDMAN_SACHS", "medium": "analyst commentary" },
        { "speaker": "REUTERS", "medium": "wire report" }
      ]
    }
  ],
  "axioms": [
    {
      "id": "A1",
      "name": "Revenue self-reporting reliability",
      "definition": "Corporate revenue announcements by public companies are presumed accurate pending audit.",
      "domain": "corporate finance",
      "controversial": false
    }
  ],
  "rules": [
    {
      "id": "R1",
      "name": "Analyst assessment relies on reported figures",
      "relation_type": "presupposes",
      "antecedent_ids": ["P2"],
      "consequent_ids": ["P1"],
      "form": "P2 ⊲ P1",
      "plain": "The analyst assessment of 'surprisingly strong' presupposes the accuracy of the reported 15% increase."
    }
  ],
  "open_questions": [
    {
      "id": "Q1",
      "question": "What is the year-over-year comparison baseline for the 15% figure?",
      "kind": "factual",
      "related": ["P1"]
    }
  ],
  "silences": [
    {
      "id": "S1",
      "kind": "absent_perspective",
      "description": "No competing analyst viewpoints or bearish assessments are presented.",
      "affected_entities": ["GOLDMAN_SACHS"],
      "related_propositions": ["P2"]
    }
  ]
}
```

---

## 3. Academic Paper

### Entity Strategy
- Each **author** → `Person`, role: `["researcher"]`
- **Institution** → `Organization`
- **Cited prior work** → `Document` or `Person` (the cited author)

### Proposition Strategy
- **Hypotheses** → `speech_act: "assertion"` or `"prediction"`
- **Definitions** → `speech_act: "definition"`, `verifiability: "unfalsifiable"` (definitions are stipulative)
- **Empirical results** → `"assertion"`, `verifiability: "empirically_testable"` or `"machine_verifiable"`
- **Claims about prior work** → use provenance to track citation chains

### Axiom Strategy
- Methodological assumptions (e.g., "random sampling produces representative data")
- Theoretical framework premises (e.g., "markets are efficient")

### Rules
- Hypothesis → evidence support: `strengthens`
- Conflicting prior results: `contradicts` or `weakens`
- Framework → prediction: `entails`

---

## 4. Fiction

### Narrative Frame — Required
Every fiction mapping must have a `narrative_frame`. Build layers from
outermost narrator inward:

**Simple first-person novel:**
```json
{
  "layers": [
    { "narrator": "NICK_CARRAWAY", "reliability": "unreliable" }
  ]
}
```

**Frame narrative (e.g., *Wuthering Heights*):**
```json
{
  "layers": [
    { "narrator": "LOCKWOOD", "reliability": "reliable", "note": "Outer frame" },
    { "narrator": "NELLY_DEAN", "reliability": "indeterminate", "note": "Inner narrator" }
  ]
}
```

### Entity Strategy
- All characters → `Person`, `ontological_status: "fictional"`
- Fictional places → `Place`, `ontological_status: "fictional"`
- The author (if needed) → `Person`, `ontological_status: "real"`

### Proposition Strategy
- **Plot events** → `speech_act: "narration"`, `verifiability: "diegetic_fact"`
- **Character dialogue making claims** → `speech_act: "assertion"`, `verifiability: "diegetic_testimony"`
- **Character descriptions** → `speech_act: "characterization"`
- **Metaphors / symbolism** → `speech_act: "figuration"`, `literal: false`
- **Narrator's framing** → examine reliability; unreliable narrators get `verifiability: "diegetic_testimony"`

### Rules
- `mirrors` — useful for thematic parallels
- `motivates` — character motivation chains
- `contradicts` — conflicting accounts (unreliable narrator, multiple perspectives)

### Silences
Fiction silences are especially rich:
- Whose perspective is never shown?
- What events happen offstage?
- What social context goes unexamined?

---

## 5. Scripture

### Narrative Frame — Required
Scripture always requires `narrative_frame` (V17).

**Single divine narrator (e.g., Quran):**
```json
{
  "layers": [
    { "narrator": "GOD", "reliability": "divinely_authorized" }
  ]
}
```

**Prophetic relay (e.g., Hadith):**
```json
{
  "layers": [
    { "narrator": "GOD", "reliability": "divinely_authorized" },
    { "narrator": "MUHAMMAD", "audience": "COMPANIONS", "reliability": "divinely_authorized" },
    { "narrator": "COMPILER", "reliability": "reliable", "note": "Hadith collector" }
  ]
}
```

**Gospel narrative:**
```json
{
  "layers": [
    { "narrator": "GOSPEL_AUTHOR", "reliability": "reliable",
      "note": "Traditional attribution; historicity debated" }
  ]
}
```

### Entity Strategy
- Divine figures → `Person` or `Manifestation`, `ontological_status: "traditional"`, roles: `["god"]`, `["prophet"]`, etc.
- Historical/traditional figures → `ontological_status: "traditional"`
- Places → `Place`, `ontological_status: "traditional"` or `"real"` (Jerusalem is real; Eden is traditional)
- **Crucially**: assign authority roles (`god`, `prophet`, `angel`, `sage`, `priest`, etc.) — lint L7 checks for these on `revelation` speech acts.

### Proposition Strategy
- **Divine commands** → `speech_act: "directive"`, `verifiability: "traditional_doctrine"`
- **Theological claims** → `speech_act: "revelation"`, `verifiability: "traditional_doctrine"` — speaker **must** have authority role (L7)
- **Narrative events** → `speech_act: "narration"`, `verifiability: "diegetic_fact"` or `"traditional_doctrine"`
- **Parables / figurative language** → `speech_act: "figuration"`, `literal: false`
- **Avoid** `machine_verifiable` under `scriptural` regime (lint L1)

### Axiom Strategy
- "The text is divinely inspired" — almost always an implicit axiom, often `controversial: true`
- Theological premises (monotheism, covenant, karma, dharma, etc.)

### Rules
- `presupposes` — theological claims presuppose doctrinal axioms
- `entails` — careful with L3 (entails from unfalsifiable)
- `mirrors` — good for typological parallels (OT → NT prefiguration, Quran ↔ Torah echoes)

---

## 6. Technical Documentation

### Entity Strategy
- **Software / systems** → `Software_System` or `Software_Module`
- **APIs / tools** → `Software_System`
- **Organizations** → `Organization` (the vendor)

### Proposition Strategy
- **Feature descriptions** → `assertion`, `machine_verifiable`
- **"You should…" guidance** → `recommendation` or `directive`
- **Definitions** → `definition`
- **Compatibility claims** → `assertion`, `machine_verifiable`

### Axioms
- "The reader has version X installed"
- "The system meets minimum requirements"

---

## 7. Legal Filing

### Entity Strategy
- Parties → `Person` / `Organization`
- Court → `Organization` or `Government_Agency`
- Statutes → `Document`

### Proposition Strategy
- **Factual allegations** → `assertion`, `empirically_testable`
- **Legal conclusions** → `assertion`, `expert_judgment`
- **Statutory definitions** → `definition`
- **Judicial orders** → `directive`

---

## 8. Policy Paper

### Entity Strategy
- Authors / think tanks → `Person` / `Organization`
- Government bodies → `Government_Agency`

### Proposition Strategy
- **Empirical claims** → `assertion`, `empirically_testable`
- **Policy recommendations** → `recommendation`
- **Projections** → `prediction`
- **Framing / values** → `editorial`

---

## 9. Transcript

### Entity Strategy
- Each speaker → `Person`
- The venue / body → `Organization` or `Event`

### Proposition Strategy
- Direct statements are typically `verbatim_quote` fidelity
- Assign `speech_act` based on what the speaker is doing (asserting, directing, recommending, etc.)
- Crosstalk, interruptions → note in `note` field

---

## 10. Common Pitfalls

1. **Forgetting `narrative_frame`** for fiction/scripture → Parse failure (V17).
2. **Entity ID collision with reserved prefixes** → `P1` as an entity ID will fail validation.
3. **Provenance too short** → If present, must have ≥ 2 hops (V20).
4. **Provenance[0].speaker mismatch** → Must equal the proposition's speaker (V19).
5. **Missing entity declarations** → Every EntityID referenced anywhere must appear in `entities[]` (V8).
6. **Figuration without `literal: false`** → Hard validation failure (V18).
7. **QuestionID in Question.related** → Questions cannot reference other questions.
8. **Rule operands not P<n> or A<n>** → Entity IDs are not valid rule operands.
9. **`revelation` without authority role** → Lint L7 fires. Ensure speaker has a role matching the authority regex.
10. **Cross-regime entailment under `mixed`** → Lint L10. If diegetic antecedents entail realist consequents, reconsider the rule's `relation_type` — `motivates` or `is_consistent_with` may be more honest than `entails`.
