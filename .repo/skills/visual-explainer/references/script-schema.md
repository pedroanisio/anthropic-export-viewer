# Animation Script Schema

This document defines the output format for the visual-explainer skill.
Every animation script must conform to this schema so that a downstream
renderer — human or automated — can produce a complete animation without
ambiguity.

## Top-level structure

The output is a single Markdown document with YAML frontmatter. The body
contains ordered sections that map 1-to-1 to production phases.

```yaml
---
title: "Human-readable title of the explainer"
source_type: paper | news | proof | lecture | report | other
source_title: "Original document title"
target_duration_seconds: <integer, estimated total runtime>
target_audience: "young-adult general audience (16–25, no domain expertise)"
visual_style: <style-key from the Style Catalogue below>
date_generated: YYYY-MM-DD
disclaimer: >
  This script is a pedagogical simplification. Statements not backed by
  a cited source or formal definition may be inaccurate or incomplete.
  Always consult the original material for authoritative information.
---
```

## Section 1 — Executive Brief

A 3–5 sentence plain-language summary of what the source document says and
why it matters. This is not narration — it is metadata for the production
team (or the automated pipeline) to understand scope.

## Section 2 — Concept Map

A flat, numbered list of every concept the animation must convey, in
dependency order (concept N depends only on concepts 1..N-1). Each entry:

```
N. **Concept name** — One-sentence definition.
   Depends on: [list of prerequisite concept numbers, or "none"]
   Source anchor: [section/page/paragraph in the original document]
```

The concept map is the backbone of the script. Every scene in Section 4
must reference at least one concept from this map by number.

## Section 3 — Style Directive

A self-contained brief that tells the renderer *how* the animation should
look and feel. It must specify:

1. **Palette** — 4–6 hex colours with named roles (background, primary,
   secondary, accent, text, highlight).
2. **Typography direction** — serif / sans-serif / mono / mixed, and the
   emotional register (e.g., "clean and clinical" vs "warm and sketchy").
3. **Visual idiom** — the dominant metaphor family for the entire piece.
   Examples: "mechanical / gears and pistons", "biological / cells and
   growth", "architectural / blueprints and scaffolding", "cosmic / stars
   and orbits". This idiom must be consistent across all scenes.
4. **Motion language** — how elements enter, transition, and exit.
   Describe default transitions (fade, slide, morph, draw-on, etc.) and
   any recurring motion motifs (e.g., "equations assemble letter by letter
   like a typewriter").
5. **Character / narrator presence** — whether a visible narrator or
   character guides the viewer, or whether the narration is voice-over
   only. If a character is used, describe their visual design.

### Style Catalogue (non-exhaustive, pick or blend)

| Key               | Description                                         |
|--------------------|-----------------------------------------------------|
| `whiteboard`       | Hand-drawn look, black on white, sketch animations  |
| `infographic`      | Flat design, bold colours, icon-driven               |
| `cinematic`        | Dark backgrounds, dramatic lighting, 3D feel         |
| `paper-cutout`     | Layered paper textures, soft shadows, craft feel     |
| `neon-dark`        | Dark background, glowing neon accents, tech feel     |
| `blueprint`        | Grid lines, monochrome blue, technical drafting      |
| `watercolour`      | Soft edges, bleed colours, organic and gentle        |
| `retro-pixel`      | 8-bit aesthetic, chunky pixels, nostalgic            |
| `comic-panel`      | Speech bubbles, bold outlines, panel-based layout    |
| `minimal-motion`   | White space, restrained movement, typographic focus  |

## Section 4 — Scene Sequence

This is the core of the script. Each scene is a self-contained unit of
meaning. The animation is the ordered playback of all scenes.

### Scene template

```markdown
### Scene <N>: <Short descriptive title>

**Concepts covered:** [list concept numbers from Section 2]
**Duration:** <seconds>
**Transition in:** <how this scene appears — e.g., "crossfade from Scene N-1">

#### Visual description
<Paragraph describing exactly what the viewer sees on screen at each
beat of the scene. Write in present tense, imperative mood where
helpful ("A circle expands from centre…", "The label 'mass' fades in
above the object…"). Be specific enough that a motion designer or an
AI renderer can reproduce the frame layout without guessing.>

#### Narration (voice-over)
<The exact spoken words. Written for reading aloud: short sentences,
conversational register, no jargon without immediate in-line
definition. Target reading speed: ~150 words per minute. The word
count here must be consistent with the scene duration.>

#### On-screen text
<Any text that appears on screen — labels, equations, data points,
captions. Specify position (top-left, centre, beside element X) and
timing (appears at second Y of the scene, disappears at second Z).>

#### Sound / music cue (optional)
<Background music mood shift, sound effect, silence beat.>

#### Accuracy notes
<Mandatory. List every simplification, analogy, or omission made in
this scene relative to the source material. If the narration says
"think of it like X," note here what the real phenomenon is and how
the analogy breaks down. This section is for editorial review, not
for the viewer.>
```

### Scene-sequencing rules

1. **Hook first.** Scene 1 must be a hook — a concrete, relatable
   question, surprising fact, or dramatic visual that gives the viewer a
   reason to keep watching. It must not start with definitions.
2. **Progressive disclosure.** Introduce one new concept per scene (two
   at most if they are tightly coupled). Never forward-reference a concept
   that hasn't been introduced yet.
3. **Analogy-then-precision.** When introducing an abstract concept, first
   present the analogy (visual metaphor + narration), then — in the same
   scene or the next — tighten the definition. Never leave an analogy
   unqualified.
4. **Recap beats.** Every 3–5 scenes, insert a brief recap scene
   (10–15 s) that visually reassembles the concepts covered so far into a
   single frame. This combats cognitive overload.
5. **Closing scene.** The last scene must do three things: (a) restate
   the core takeaway in one sentence, (b) show the full concept map as a
   visual summary, (c) point the viewer to the original source for depth.

## Section 5 — Fact-Check Ledger

A table with one row per scene, listing every factual claim made in the
narration, the source location it came from (page, section, DOI, URL),
and a confidence tag:

| Scene | Claim (paraphrased) | Source location | Confidence |
|-------|---------------------|-----------------|------------|
| 1     | "X happens because…" | §3.2, p.14     | verified   |
| 2     | "Roughly Y percent…" | Fig.4, p.18    | approximated |

Confidence tags:
- `verified` — directly stated in the source.
- `approximated` — a rounded or simplified version of a source claim.
- `inferred` — a logical consequence not explicitly stated; flag for
  review.
- `analogical` — a metaphor with no direct source equivalent; flag the
  accuracy note in the scene.

## Section 6 — Production Metadata

```yaml
total_scenes: <integer>
estimated_runtime_seconds: <integer>
narration_word_count: <integer>
concepts_covered: <integer>
simplifications_flagged: <integer>
unresolved_accuracy_notes: <integer, ideally 0>
```

This block lets the production team (or CI pipeline) sanity-check the
script before rendering begins.
