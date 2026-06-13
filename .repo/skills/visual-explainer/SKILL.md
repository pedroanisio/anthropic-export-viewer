---
name: visual-explainer
description: >
  Transform any document (news, paper, math proof, physics, medical study,
  legal ruling) into a production-ready animation script — scenes, visuals,
  narration, style — that a renderer or video pipeline can execute into a
  complete explainer for young adults. Trigger on: "explain visually",
  "make an animation of", "video script for", "turn this into an
  explainer", "animate this", "visual breakdown", "storyboard this",
  "scene-by-scene", "animation script", "explainer video", "explain like
  I'm 18", "make this accessible", "visual summary", "animated summary".
  Also trigger when a user uploads any document and wants it turned into
  something a general audience can watch and understand. Even partial
  requests like "script the first 3 minutes" or "storyboard the key
  insight" should trigger it.
---

# Visual Explainer

## What this skill does

Given any source document, this skill produces a **production-ready
animation script** — a structured Markdown document that specifies
every scene, every visual element, every word of narration, and every
simplification trade-off, so that a downstream renderer can produce a
complete explainer animation without needing to consult the original
source or make creative guesses.

The output is designed for two consumers:
1. **An automated pipeline** (AI video gen, Manim, Remotion, etc.)
   that parses the structured scenes into frames.
2. **A human production team** (motion designers, voice artists,
   editors) that reads the script like a shooting script.

Both consumers must be able to work from the script alone.

## Before you begin — mandatory reading

Read these two reference files before producing any output:

1. `references/script-schema.md` — the exact output format, section by
   section, with the scene template and all required fields.
2. `references/pedagogy.md` — the simplification strategies, audience
   model, anti-patterns, and the cardinal rule ("simplify, never
   falsify").

Both files are short. Read them in full. They prevent the most common
failure modes: under-specified visuals, jargon-heavy narration, and
untracked simplifications.

## The pipeline

### Phase 0 — Ingest and comprehend

Read the source document end to end. If the document is technical, read
it twice: once for gist, once for structure. Identify:

- **Domain**: what field does this belong to?
- **Core thesis**: what is the single most important claim or result?
- **Prerequisite concepts**: what must the viewer already understand
  (or be taught) before the core thesis makes sense?
- **Scope decision**: can the entire document fit into one animation
  (target: 3–8 minutes), or should it be split into a series? If split,
  define episode boundaries and produce the script for episode 1, noting
  what the subsequent episodes will cover.

At the end of Phase 0, state your scope decision and the estimated
runtime before proceeding. If the user has specified a duration target,
respect it and trim scope accordingly.

### Phase 1 — Concept extraction

Produce the **Concept Map** (Section 2 of the output schema). This is
a dependency-ordered list of every concept the animation will teach.

Rules:
- Every concept must have a single, one-sentence definition that a
  16-year-old can parse.
- Dependencies must be acyclic (no circular references).
- Anchor every concept to a specific location in the source document
  so a fact-checker can verify it.
- If the source uses multiple terms for the same concept, pick one and
  note the aliases in parentheses.

The concept map is the structural skeleton of the entire script. Get it
right before writing a single scene.

### Phase 2 — Style selection

Choose a visual style from the Style Catalogue in `script-schema.md`,
or blend two styles if the material warrants it. Then write the full
**Style Directive** (Section 3 of the output schema): palette, typography,
visual idiom, motion language, and narrator presence.

Style selection criteria:
- Match the emotional register of the material. A math proof may suit
  `blueprint` or `whiteboard`. A news story about climate change may suit
  `cinematic` or `infographic`. A whimsical science fact may suit
  `paper-cutout` or `comic-panel`.
- If the source material has its own visual language (circuit diagrams,
  anatomical illustrations, geographic maps), incorporate it into the
  idiom rather than replacing it.
- When in doubt, default to `infographic` — it is the most versatile
  and the easiest for automated renderers to execute.

### Phase 3 — Scene writing

Write every scene following the template in `script-schema.md` and the
pedagogical strategies in `pedagogy.md`. This is the most labour-
intensive phase. Key directives:

**Narration craft:**
- Write for the ear, not the eye. Read every sentence aloud (mentally).
  If it sounds like a textbook, rewrite it.
- Target ~150 words per minute of narration. A 60-second scene should
  have ~150 words of narration, not 250.
- Use active voice. Use second person ("you") to address the viewer
  directly.
- Introduce no more than one new term per 45 seconds of runtime.
- Short sentences. Average 10–15 words. Maximum 25 words.

**Visual description craft:**
- Write in present tense, as if narrating what is currently on screen.
- Be spatially explicit: "A blue circle appears at screen centre.
  A red arrow extends from the circle to the upper-right corner."
- Specify size relationships: "The planet is roughly one-fifth the
  width of the frame. The star fills the left third."
- Specify timing within the scene: "At second 3, the label fades in.
  At second 7, the circle morphs into an ellipse."
- Never describe a visual as "complex" or "detailed" — describe what
  it actually looks like. The renderer cannot interpret adjectives of
  impression.

**Accuracy discipline:**
- Fill the `Accuracy notes` for every scene. This is non-negotiable.
- If you use an analogy, document exactly where it breaks down.
- If you omit a caveat present in the source, note the omission and
  justify why (usually: "would exceed the jargon budget for this scene
  and is not necessary for the core insight").

**Sequencing discipline:**
- Follow the five scene-sequencing rules in `script-schema.md`: hook
  first, progressive disclosure, analogy-then-precision, recap beats,
  closing scene.
- Cross-check: every concept in the Concept Map must appear in at least
  one scene's `Concepts covered` field. If a concept is orphaned, either
  add a scene or remove the concept from the map.
- Cross-check: no scene's narration references a concept that hasn't
  been introduced in a prior scene.

### Phase 4 — Fact-check ledger

Build the **Fact-Check Ledger** (Section 5 of the output schema). Go
through every scene's narration sentence by sentence and record the
source location for each factual claim.

Confidence tags:
- `verified` — directly stated in the source.
- `approximated` — a rounded or simplified version.
- `inferred` — a logical consequence you derived; flag for review.
- `analogical` — a metaphor with no direct source equivalent.

If you cannot find a source anchor for a claim, either remove the claim
from the narration or explicitly tag it as `inferred` and explain your
reasoning.

### Phase 5 — Self-review

Before delivering the script, run these checks:

1. **Duration consistency**: sum all scene durations. Does the total
   match the frontmatter's `target_duration_seconds` within ±10%?
2. **Word-count consistency**: sum narration word counts. At 150 wpm,
   does the total match the total duration within ±10%?
3. **Concept coverage**: is every concept in the map referenced by at
   least one scene?
4. **Dependency order**: does any scene reference a concept that was
   introduced in a later scene?
5. **Jargon budget**: count new terms introduced. Is the density ≤ 1
   per 45 seconds?
6. **Accuracy coverage**: does every scene have a non-empty `Accuracy
   notes` field? (Even scenes with no simplifications should say
   "No simplifications in this scene.")
7. **Ledger coverage**: does the Fact-Check Ledger have at least one
   row per scene?

If any check fails, fix the script before delivering.

### Phase 6 — Produce the deliverable

Assemble the final Markdown document following the exact section order
in `script-schema.md`:

1. YAML frontmatter (including disclaimer)
2. Executive Brief
3. Concept Map
4. Style Directive
5. Scene Sequence
6. Fact-Check Ledger
7. Production Metadata

Save the file as `<slugified-title>-animation-script.md` and deliver
it to the user.

## Handling different source types

The pipeline above is universal, but certain source types require
additional attention:

**Math proofs:**
- Every step of the proof must map to a scene or sub-scene.
- Animate equation transformations step by step — never show a complete
  derivation in a single frame.
- Use the `blueprint` or `whiteboard` style unless the user specifies
  otherwise.
- The Concept Map should list both the mathematical objects (sets,
  functions, spaces) and the logical moves (assume, derive, contradict).

**News reports:**
- Separate facts from editorial framing. The narration should present
  facts; the `Accuracy notes` should flag any editorial angle in the
  source.
- Attribute claims to their sources in the narration: "According to
  researchers at MIT…", not "Scientists say…".
- Time-sensitive information should be flagged in the frontmatter with
  a `content_date` field.

**Physics / astrophysics:**
- Scale is almost always the hardest thing to convey. Use the
  Quantitative Literacy Scaffolding strategy from `pedagogy.md` heavily.
- If the phenomenon is invisible (radio waves, dark matter, magnetic
  fields), define a visual encoding (colour, glow, particle density)
  in the Style Directive and use it consistently.
- Simulations or computational results should be described as "what our
  best models predict," never as "what happens."

**Medical / biological:**
- Avoid fear-based framing. State risks in both absolute and relative
  terms.
- Anatomical visuals should be schematic, not photorealistic, unless
  the user requests otherwise.
- Drug names and mechanisms should be double-checked against the source;
  never extrapolate dosage or efficacy claims.

**Legal / policy:**
- Distinguish between "the law says X" and "in practice, X happens."
- Quote the relevant statute or clause in the `Accuracy notes`, not in
  the narration.
- Use the `infographic` style to map decision trees and jurisdiction
  boundaries.

## Output expectations

The final deliverable is a single Markdown file that:
- Conforms to every section and field in `references/script-schema.md`.
- Follows every pedagogical strategy in `references/pedagogy.md`.
- Contains zero orphaned concepts and zero unattributed factual claims.
- Can be handed to a renderer or production team as-is.

The file should typically be 1,500–4,000 words for a 3–5 minute
animation, or 4,000–8,000 words for a 5–10 minute animation. Longer
scripts should prompt a scope-reduction conversation with the user.
