---
name: experiment-lab
description: >
  Run structured AI experiments with iterative hypothesis-test-learn cycles,
  vision-based validation, and multi-agent evaluation via Anthropic API.
  Trigger on: "experiment with", "try different approaches", "which method
  works best", "compare techniques", "find the best way to", "A/B test",
  "run experiments", "optimize visually", "find the most realistic",
  "try multiple versions", "evolutionary approach", "explore the design
  space", "run trials", "benchmark approaches", or any request to
  systematically try N alternatives, measure outcomes, and converge on
  the best. Also trigger when the user wants to discover the best method
  through experimentation. Even "play around with different ways" or
  "figure out the best approach" should trigger this skill.
---

# Experiment Lab

A structured framework for running AI-driven experiments: define hypotheses,
execute variant trials, collect evidence (including vision-based assessment),
and iteratively converge on the best solution.

## Why This Exists

Some problems can't be solved by picking one approach and hoping. The best
3D model, the most readable chart layout, the most natural animation — these
require *trying things, measuring, and learning*. This skill turns Claude
into an experimental researcher: it formulates hypotheses, runs controlled
trials, gathers structured evidence, and synthesizes findings into improved
candidates.

---

## Core Loop

Every experiment follows this cycle. Don't skip steps.

```
DEFINE → HYPOTHESIZE → EXECUTE → OBSERVE → ANALYZE → SYNTHESIZE → ITERATE
  ↑                                                                   |
  └───────────────────────────────────────────────────────────────────┘
```

### Phase 0: DEFINE — Frame the Experiment

Before generating anything, establish:

1. **Objective**: What are we trying to achieve? Be specific.
   - BAD: "Make a 3D femur"
   - GOOD: "Produce a browser-rendered 3D femur model that a medical
     student would mistake for a textbook illustration at first glance"

2. **Evaluation Dimensions**: What axes matter? Each gets a 1–10 rubric.
   Example for the femur:
   - Anatomical accuracy (shape, proportions, landmarks)
   - Surface realism (texture, color, material response to light)
   - Structural detail (cortical vs cancellous bone distinction, periosteum)
   - Technical quality (polygon count, render performance, code clarity)

3. **Reference Material**: Gather ground truth BEFORE experimenting.
   - Use `web_search` and `image_search` to find reference images
   - Save reference descriptions and URLs to the experiment log
   - These references anchor all subsequent visual evaluations

4. **Success Threshold**: What score across dimensions means "done"?

5. **Iteration Budget**: How many rounds? (Default: 3 rounds, 3–4 variants
   per round. More rounds beat more variants per round.)

Save all of this to `experiment.json` — see the schema in
`references/experiment-schema.md`.

### Phase 1: HYPOTHESIZE — Generate Candidate Approaches

For each variant, write a concrete hypothesis:

```
VARIANT: "displacement-mapped-sphere"
HYPOTHESIS: "Starting from a UV sphere and applying a displacement map
derived from a femur heightmap will produce better anatomical accuracy
than pure parametric geometry, because displacement maps can encode
organic irregularity that parametric equations struggle to capture."
PREDICTED STRENGTHS: surface detail, organic feel
PREDICTED WEAKNESSES: may lose sharp anatomical landmarks
```

Generate 3–4 variants per round. Variants should be **meaningfully
different strategies**, not minor parameter tweaks. Diversity of approach
matters more than quantity.

Good variant differentiation examples:
- Parametric geometry vs. displacement mapping vs. SDF raymarching
- Hand-coded keyframes vs. spring physics vs. procedural noise
- Template-based layout vs. force-directed vs. constraint solver

### Phase 2: EXECUTE — Run the Trials

For each variant:

1. **Implement**: Write the full code (Three.js, SVG, React, HTML —
   whatever the medium requires).
   
2. **Render as artifact**: Create the artifact in `/mnt/user-data/outputs/`
   so the user can see it. Name files clearly:
   `experiment-{name}-round{N}-variant-{id}.{ext}`

3. **Self-document**: Each variant's code MUST include a comment block:
   ```
   /*
    * EXPERIMENT: {experiment_name}
    * ROUND: {N}
    * VARIANT: {variant_id}
    * HYPOTHESIS: {one-line hypothesis}
    * APPROACH: {technical approach summary}
    */
   ```

4. **Capture metadata**: Record render time, file size, and any
   programmatic metrics (polygon count, node count, etc.) in the
   trial log.

#### Execution Strategy (Claude.ai — No Subagents)

Since Claude.ai cannot spawn parallel subagents, run variants
**sequentially** but maintain strict separation:

- Implement each variant as a self-contained file
- Do NOT let knowledge from variant A's implementation leak into
  variant B's design (the hypothesis was written before execution)
- After ALL variants for a round are implemented, move to OBSERVE

#### Execution Strategy (With Anthropic API — Pseudo-Parallel Agents)

When the experiment benefits from independent evaluation agents, build
a React artifact that calls the Anthropic API. Each "agent" is a
separate API call with a specialized system prompt (see
`references/agent-prompts.md`). Use cases:

- **Evaluation agents**: N agents each score a rendered image from a
  different dimension (anatomy, texture, lighting, etc.)
- **Variation agents**: Each agent proposes a different approach given
  the same brief, reducing single-perspective bias
- **Critic agents**: Adversarial reviewers who try to find flaws

### Phase 3: OBSERVE — Collect Evidence

This is where vision-based validation happens.

#### Vision Assessment Protocol

For visual artifacts (3D models, charts, UIs, illustrations):

1. **Render the artifact** — present it to the user via `present_files`
   or as an inline React/HTML artifact.

2. **Describe what you see** — When Claude can view a rendered artifact
   or screenshot, produce a structured observation:
   ```json
   {
     "variant_id": "displacement-sphere",
     "visual_observations": {
       "overall_impression": "Organic shape but lacks sharp landmarks",
       "strengths": ["smooth surface curvature", "realistic color gradient"],
       "weaknesses": ["greater trochanter too rounded", "no visible texture grain"],
       "comparison_to_reference": "Shape ~70% match to reference anatomy"
     }
   }
   ```

3. **Score each dimension** — Apply the rubric from Phase 0.
   Be honest. A 5/10 is not an insult; it's data.

4. **Collect user feedback** — Ask the user to look at each variant
   and provide their assessment. Their observations are evidence too.
   Format:
   ```
   Which variants look most promising to you? Any specific strengths
   or flaws you notice? (You can rate 1-10 per dimension, or just
   describe what you see.)
   ```

#### Programmatic Metrics

Where possible, measure things with code, not vibes:
- Polygon/vertex count for 3D models
- Lighthouse scores for web artifacts
- Byte size, render framerate
- Color histogram similarity to reference (if reference image available)
- Silhouette comparison (bounding box aspect ratio vs known anatomy)

Save all observations to the trial log:
`workspace/round-{N}/variant-{id}/observations.json`

### Phase 4: ANALYZE — Compare and Rank

Build a comparison matrix:

| Dimension          | Variant A | Variant B | Variant C |
|--------------------|-----------|-----------|-----------|
| Anatomical accuracy| 6/10      | 4/10      | 8/10      |
| Surface realism    | 7/10      | 8/10      | 5/10      |
| Structural detail  | 5/10      | 3/10      | 7/10      |
| Technical quality  | 8/10      | 6/10      | 6/10      |
| **Weighted Total** | **6.4**   | **5.1**   | **6.7**   |

Then write an analysis:
- What approach produced the best results per dimension?
- Were the hypotheses confirmed or refuted?
- What **mechanism** drove the good/bad results? (Not "it looked better"
  but "the displacement map encoded curvature data that parametric
  equations couldn't represent")
- What specific techniques from different variants could be combined?

### Phase 5: SYNTHESIZE — Breed the Next Generation

This is the evolutionary step. Based on analysis:

1. **Carry forward** the best-performing variant as a baseline
2. **Cross-pollinate**: Take the best technique from each variant and
   combine them into 1–2 hybrid candidates
3. **Mutate**: Try one genuinely new approach informed by what was
   learned (not just a tweak — a new idea that the evidence suggests)
4. **Drop** approaches that clearly underperformed with no redeeming
   traits

Write new hypotheses for each next-round variant. These hypotheses
should reference specific evidence from the current round:

```
VARIANT: "parametric-with-displacement-detail"
HYPOTHESIS: "Variant C's parametric skeleton scored 8/10 on anatomy
but only 5/10 on surface realism. Variant B's displacement mapping
scored 8/10 on surface realism. Combining C's skeleton with B's
displacement technique as a detail pass should score ≥7 on both."
EVIDENCE BASIS: Round 1 observations for variants B and C
```

### Phase 6: ITERATE

Go back to Phase 2 with the new variants. Each round should:
- Show measurable improvement on at least one dimension
- Not regress more than 1 point on any dimension without justification
- Narrow the variant count as convergence approaches

Stop when:
- Success threshold is met
- Iteration budget is exhausted
- Marginal improvement drops below 0.5 points per round
- User says "good enough"

---

## Workspace Structure

```
experiment-{name}/
├── experiment.json          # Phase 0 definition
├── references/              # Reference images, descriptions, URLs
├── round-1/
│   ├── hypotheses.json      # All variant hypotheses for this round
│   ├── variant-a/
│   │   ├── implementation.{ext}  # The actual code/artifact
│   │   ├── observations.json     # Vision + metric evidence
│   │   └── metadata.json         # Timing, sizes, programmatic metrics
│   ├── variant-b/
│   │   └── ...
│   ├── comparison.json      # Phase 4 matrix and analysis
│   └── synthesis.md         # Phase 5 decisions and rationale
├── round-2/
│   └── ...
└── final/
    ├── best-variant/        # The winning implementation
    ├── experiment-report.md # Full report with all evidence
    └── learnings.json       # Distilled insights for future experiments
```

Save this workspace under `/home/claude/experiment-{name}/`.
Copy final artifacts to `/mnt/user-data/outputs/`.

---

## Vision Validation — Detailed Protocol

When assessing visual output, follow this structured approach:

### Step 1: Establish Visual Criteria Before Viewing

Write down what you expect to see BEFORE looking at the render.
This prevents post-hoc rationalization.

### Step 2: Systematic Scan

For 3D models:
- Silhouette check: Does the outline match reference anatomy?
- Proportion check: Are relative sizes correct?
- Landmark check: Are key anatomical features present and positioned?
- Surface check: Texture, color, specular response
- Lighting check: Do shadows reveal or hide geometry?

For UI/charts/2D:
- Hierarchy: Is the visual hierarchy correct?
- Readability: Can you parse the information?
- Aesthetics: Does it look intentional, not accidental?
- Accuracy: Does the visualization truthfully represent the data?

### Step 3: Comparative Assessment

Always compare against:
1. The reference material (ground truth)
2. The other variants in the same round
3. The best variant from the previous round (if not round 1)

### Step 4: Record BOTH Strengths and Weaknesses

A variant that scores 4/10 overall might have one technique that
scores 9/10 on a specific dimension. That technique is gold.
Don't discard losing variants without extracting their insights.

---

## Multi-Agent Evaluation via Anthropic API

For experiments that benefit from diverse evaluation perspectives,
build a React artifact that spawns evaluation agents. See
`references/agent-prompts.md` for agent system prompts.

### Architecture

```
┌─────────────────────────────────┐
│  Experiment Controller (React)  │
│                                 │
│  ┌─────────┐  ┌─────────┐      │
│  │ Agent 1  │  │ Agent 2  │ ... │
│  │ Anatomy  │  │ Texture  │     │
│  │ Expert   │  │ Expert   │     │
│  └────┬─────┘  └────┬─────┘     │
│       │              │           │
│       ▼              ▼           │
│  ┌──────────────────────┐       │
│  │  Evidence Aggregator  │       │
│  └──────────────────────┘       │
└─────────────────────────────────┘
```

Each agent:
- Receives the same rendered output (as image or code)
- Has a specialized system prompt (e.g., "You are an orthopedic
  surgeon evaluating anatomical accuracy...")
- Scores on its assigned dimension with justification
- Is independent — agents don't see each other's scores

The controller aggregates scores and presents a unified scorecard.

### When to Use Multi-Agent

- When evaluation dimensions require genuinely different expertise
- When you want to reduce single-evaluator bias
- When the user wants a thorough assessment

### When NOT to Use Multi-Agent

- For simple comparisons (just score it yourself)
- When speed matters more than rigor
- When the variants are so clearly different that scoring is obvious

---

## Example: 3D Femur Experiment

This section walks through the femur use case end-to-end.
Read `references/example-femur.md` for the full worked example.

Quick summary:

**Round 1** — Explore radically different approaches:
- Variant A: Parametric geometry (mathematical bone shape functions)
- Variant B: Displacement-mapped sphere (heightmap from anatomy)
- Variant C: SDF raymarching (signed distance field in fragment shader)
- Variant D: Subdivision surface with hand-placed control points

**Round 2** — Cross-pollinate winners:
- Hybrid AB: Parametric skeleton + displacement detail
- Hybrid CD: SDF base shape + subdivision surface refinement
- New E: Procedural bone texture via noise functions

**Round 3** — Refine the leader:
- Best hybrid from R2 with tweaked parameters
- Same hybrid with different lighting/material model
- Same hybrid optimized for polygon count / performance

---

## Important Constraints

1. **Honesty over optimism.** If all variants score poorly, say so.
   The point is to learn, not to declare victory.

2. **Evidence over intuition.** Every claim about why something works
   must reference specific observations or metrics, not feelings.

3. **Diversity over quantity.** 3 genuinely different approaches beat
   10 minor variations on the same idea.

4. **User involvement.** The user's eyes and domain knowledge are the
   most valuable evaluation instrument. Always ask for their assessment
   before synthesizing the next round.

5. **No hallucinated metrics.** If you can't measure it, say "not
   measured." Never invent a number.

6. **Preserve provenance.** Every score, observation, and decision
   must trace back to a specific variant, round, and evidence source.
