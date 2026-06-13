# Research Notes — Anti-Slop Checklist

Methodological notes and citations relevant to the checklist's empirical
claims. Read when assessing non-native speakers or when temporal validity
of vocabulary markers is in question.

## Key Citations

### Liang et al. (2023)
- **Source:** Liang, W., Yuksekgonul, M., Mao, Y., Wu, E., & Zou, J.
  "GPT Detectors Are Biased Against Non-Native English Writers."
  *Patterns*, 4(7), 2023.
- **Finding:** AI-text detectors misclassify non-native English writing
  as AI-generated at rates up to 61.3%. Vocabulary-based heuristics are
  the primary driver of these false positives.
- **Implication for Section 1:** Do not use vocabulary flags alone to
  assess writing by non-native speakers. Always verify with Tier 2.

### Kobak et al. (2025)
- **Relevance:** Documents vocabulary frequency shifts in academic and
  professional writing attributable to AI tool adoption. Specific words
  show measurable frequency increases in published text post-2023.
- **Implication:** The slop lexicon reflects a snapshot of 2024–2025
  patterns. These markers will shift as models retrain.

### Juzek & Ward (2025)
- **Relevance:** Examines stylometric markers and their reliability
  across writing genres and demographic groups.
- **Implication:** Genre and demographic variation introduce noise that
  makes surface-level markers unreliable for authorship determination.
  Substance checks (Tier 2) remain more robust.

## Methodological Constraints

1. **No single vocabulary item is diagnostic.** Density matters, not
   presence.
2. **Vocabulary markers decay over time.** Model retraining and cultural
   adaptation erode the signal. Tier 2 checks are more durable.
3. **False positives are systematic, not random.** Non-native speakers,
   technical writing, and formal registers all produce elevated
   false-positive rates on vocabulary heuristics.
4. **This checklist is a heuristic, not a formal detection method.**
   Apply judgment. No checklist item triggers an automatic verdict.

## Em-Dash Model Variation

Per the original checklist's model note:
- GPT-4o uses roughly 10× more em-dashes than GPT-3.5.
- Claude uses fewer still.
- Em-dash frequency is not a universal heuristic across models and should
  be weighted lightly when the originating model is unknown.
