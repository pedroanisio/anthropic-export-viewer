# Pedagogical Strategies for Visual Explainers

This document contains the simplification and communication strategies
that the visual-explainer skill must follow. Read this before writing
any narration or visual description.

## The cardinal rule: simplify, never falsify

Every simplification must pass this test: **if the viewer later reads
the original source, will anything in the animation contradict what they
find there?** If yes, the simplification is a distortion and must be
reworked. Omission is acceptable; falsehood is not.

Record every simplification in the scene's `Accuracy notes` field. The
goal is zero surprises for a fact-checker.

## Audience model

The target viewer is a curious young adult (16–25) with no domain
expertise. Assume:
- Comfortable with everyday math (percentages, basic algebra, graphs).
- Familiar with common science vocabulary (atom, energy, gravity, DNA)
  but not with specialist terms.
- Attention span of ~90 seconds before needing a new hook or payoff.
- Learns best from concrete examples, then generalisation.
- Retains visual-spatial information better than verbal-sequential.

Do NOT assume:
- Any university-level coursework.
- Familiarity with notation systems (LaTeX, chemical formulae, musical
  scores) unless the animation is explicitly teaching that notation.
- Prior knowledge of the specific topic.

## Strategy 1 — The Analogy Ladder

For every abstract concept, build a three-rung ladder:

1. **Grounding analogy** — map the concept onto something the viewer
   already knows. E.g., "An event horizon is like a one-way door: things
   can go in but nothing comes out."
2. **Precision tightening** — immediately flag where the analogy breaks
   down. E.g., "Unlike a door, the event horizon isn't a physical surface
   — it's a boundary in spacetime where escape velocity exceeds the speed
   of light."
3. **Formal statement** — show (on screen, not necessarily spoken) the
   precise definition or equation, annotated so the viewer can connect
   each symbol to the analogy. E.g., display `r_s = 2GM/c²` with
   labelled arrows: "G = gravity's strength, M = the object's mass,
   c = speed of light."

Not every concept needs all three rungs. Simple concepts can skip rung 1.
Highly abstract concepts must never skip rung 2.

## Strategy 2 — Concrete Before Abstract

Always present a specific instance before the general principle.

- BAD: "Conservation of energy states that energy cannot be created or
  destroyed." (abstract first)
- GOOD: "Drop a ball from a table. It speeds up as it falls. Where does
  that speed come from? It comes from the height it lost — the energy
  just changed form." (concrete first, then generalise)

In the animation, this means: show the specific visual (the ball, the
chemical reaction, the data chart) first. Let the viewer see the pattern.
Then introduce the name and the general rule.

## Strategy 3 — One Idea Per Breath

A "breath" is the unit of comprehension — roughly one sentence of
narration (5–12 words spoken) paired with one visual change on screen.

Rules:
- Never introduce two new terms in the same breath.
- Never show a complex diagram all at once; build it element by element,
  one breath per element.
- If a sentence needs a subordinate clause to be understood, split it
  into two sentences.

This constraint is the single biggest factor in perceived clarity. When
in doubt, slow down.

## Strategy 4 — Spatial Anchoring

Assign each major concept a fixed position on screen for the entire
animation. The viewer builds a mental map:

- Top-left = causes / inputs
- Bottom-right = effects / outputs
- Centre = the main subject

When a recap scene assembles the concept map, each concept returns to
its established position. This leverages spatial memory and reduces
cognitive load.

If the source material has a natural spatial structure (a timeline, a
geographic map, an anatomical diagram, a circuit), adopt that structure
as the screen layout rather than inventing a new one.

## Strategy 5 — Emotional Pacing

Cognitive engagement follows an emotional curve. Structure the scene
sequence like a story:

1. **Hook** (curiosity, surprise, stakes) — Scene 1.
2. **Rising complexity** — each scene adds one layer.
3. **Tension peak** — the hardest concept, introduced as a problem
   the viewer now cares about solving.
4. **Resolution** — the key insight that ties everything together.
5. **Denouement** — recap + "where to go next."

Avoid flat affect. Even in a math proof, the narration should convey
*why* the next step matters ("Here's where it gets interesting…",
"This is the part most people get wrong…").

## Strategy 6 — Jargon Protocol

When a domain-specific term is unavoidable:

1. **Introduce it in context**, never in isolation. Show the thing,
   then name it — not the reverse.
2. **Define it in ≤ 10 spoken words.**
3. **Show the term on screen** as a persistent label for at least 5
   seconds after introduction.
4. **Use it again within 30 seconds** so the viewer hears it twice
   before moving on.
5. **Never use a synonym** after introducing the term — consistency
   over variety.

Maximum jargon budget per animation: roughly one new term per 45 seconds
of runtime. If the source material requires more, the animation is
probably covering too much scope — split it into a series.

## Strategy 7 — Quantitative Literacy Scaffolding

When the source material contains numbers, statistics, or equations:

- Always give a sense of scale before showing the number.
  ("Imagine the entire population of Brazil — now multiply by three.
  That's how many stars are in the Milky Way.")
- Prefer relative comparisons over absolute values.
  ("Twice as hot as the surface of the Sun" > "10,000 Kelvin")
- For equations, animate the derivation step by step. Never flash a
  complete equation on screen. Each algebraic operation should be a
  visible, narrated transformation.
- If an equation has more than 4 symbols, introduce each symbol in a
  prior scene before assembling the full equation.

## Strategy 8 — The Honesty Sidebar

When the animation must oversimplify (and it will), occasionally
acknowledge it explicitly in the narration:

- "In reality, this is more complicated — but the core idea holds."
- "Scientists use a more precise version of this, but for now, this
  gets us 90% of the way."

This builds trust and pre-empts the "well actually" reaction. Use
sparingly — once or twice per animation, at the points of greatest
simplification. Every such sidebar must have a corresponding entry in
the `Accuracy notes` of that scene.

## Anti-patterns to avoid

1. **Definition-first opening.** Never start with "X is defined as…".
   Start with a question, a surprising fact, or a visual that provokes
   curiosity.
2. **Narrator monologue.** If the narration runs for more than 20
   seconds without a visual change, the scene is too static. Add a
   visual beat.
3. **Orphaned jargon.** Introducing a term and never using it again.
   If a term appears only once, it didn't need to be introduced.
4. **Scale blindness.** Showing a molecule and a galaxy at the same
   visual size without flagging the scale difference.
5. **Premature formalism.** Showing an equation before the viewer
   understands what it describes. Equations are the destination, not
   the starting point.
6. **False certainty.** Presenting contested or frontier science
   without flagging uncertainty. If the source says "we believe" or
   "models suggest," the narration must preserve that hedging.
