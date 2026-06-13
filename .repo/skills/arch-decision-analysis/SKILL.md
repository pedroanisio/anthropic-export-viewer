---
name: arch-decision-analysis
description: >
  Analyze architectural implications of design choices across any domain — software,
  business, infrastructure, data, or process design. Produces a decision report with
  SVG visualizations (option-space maps, enables/blocks flows, composition matrices),
  a Markdown document, and interactive follow-up suggestions. Use this skill when the
  user asks about trade-offs, design decisions, "should I use X or Y", "pros and cons",
  "what does choosing X block or enable", "help me decide between", "decision matrix",
  "option analysis", "downstream effects", or any request to understand the consequence
  landscape of a choice. Also trigger when the user pastes technical context and asks
  what the options or trade-offs are. If the user wants structured analysis — not just
  a list of pros and cons — this is the skill.
---

# Architectural Decision Analysis

## Purpose

Most "pros and cons" analyses fail because they flatten a multi-dimensional
decision space into a one-dimensional list. Real design decisions have:

- **Asymmetric reversibility** — some choices are cheap to undo, others aren't.
- **Compositional structure** — options aren't always mutually exclusive; some
  compose, some conflict, some are orthogonal.
- **Context-dependent weight** — a "con" in one context is irrelevant in another.
- **Downstream gating** — a choice today enables or blocks future choices.

This skill produces analysis that captures these dimensions.

---

## Workflow

### Phase 1 — Context Extraction

Before analyzing anything, establish the decision's coordinate system:

1. **What is being decided?** Name the decision precisely. "Should we use X" is
   too vague. "Should we adopt X for Y given constraints Z" is actionable.

2. **What are the binding constraints?** These are non-negotiable. They prune the
   option space before analysis begins. Examples: budget ceiling, team size,
   existing tech stack, regulatory requirements, timeline.

3. **What are the soft constraints?** These are preferences, not requirements.
   They influence ranking but don't eliminate options. Examples: team familiarity,
   aesthetic preferences, organizational inertia.

4. **What is the decision horizon?** Is this a 3-month experiment or a 5-year
   commitment? Reversibility cost scales with horizon.

5. **What does success look like?** Define the evaluation axes — not just "it
   works" but the specific dimensions that matter (latency, DX, cost,
   maintainability, hiring pool, etc.).

If the user's prompt already provides enough context to answer these, proceed
directly. If not, ask — but do it in a single focused round, not a drawn-out
interview.

### Phase 2 — Option Discovery

Don't just enumerate the obvious options. Systematically search for:

- **Canonical options**: The standard approaches anyone would list.
- **Hybrid options**: Combinations of canonical options that compose well.
- **Deferred options**: "Do nothing now, decide later" is often a real option.
  Name it explicitly. What information would you need to decide later?
- **Orthogonal options**: Approaches that reframe the problem entirely. These
  often come from questioning an assumption in the problem statement.
- **Partial options**: Solutions that solve 80% of the problem with 20% of the
  cost. Name what they leave unsolved.

For each option, establish:
- A short label (used in diagrams)
- A one-sentence description
- Key mechanism (how it achieves the goal)

### Phase 3 — Implication Mapping

For each option, analyze along these dimensions:

#### 3a. Enables / Blocks Matrix

What does choosing this option make possible or impossible? Be specific:
- **Enables**: Future options, capabilities, integrations that become available.
- **Blocks**: Future options that become impossible or prohibitively expensive.
- **Degrades**: Things that remain possible but become harder or more expensive.

#### 3b. Reversibility Assessment

- **Cost to adopt**: Implementation effort, learning curve, migration cost.
- **Cost to abandon**: What does unwinding this choice cost? Data migration?
  Retraining? Rewriting?
- **Lock-in mechanisms**: What creates coupling? Proprietary formats? Network
  effects? Team knowledge concentration?

#### 3c. Risk Profile

- **Known risks**: Failure modes you can name and plan for.
- **Unknown-risk surface area**: Where does this option expose you to surprises?
  (e.g., dependency on a single vendor's roadmap, reliance on bleeding-edge
  technology with thin community support)
- **Failure severity**: If this goes wrong, is it a speed bump or a brick wall?

#### 3d. Composition Analysis

Which options combine well? Build a composition matrix:
- **Composes**: These options can be layered or used together with net benefit.
- **Conflicts**: These options are mutually exclusive or create harmful
  interference when combined.
- **Orthogonal**: These options are independent — choosing one says nothing
  about the other.

### Phase 4 — Output Generation

Produce three artifacts:

#### Artifact 1: SVG Visualizations (via `visualize:show_widget`)

Generate the following diagrams inline using `visualize:show_widget`. Read the
appropriate `visualize:read_me` modules before generating (typically `diagram`
and/or `chart`).

**Diagram A — Option-Space Map**
A node graph showing all identified options as nodes, with edges representing
relationships:
- Green solid edges → "composes well with"
- Red dashed edges → "conflicts with"
- Gray dotted edges → "orthogonal to"
- Node size or weight → reflects adoption cost (larger = more expensive)
- Node border style → reflects reversibility (solid = easily reversed,
  dashed = expensive to reverse)

**Diagram B — Enables/Blocks Flow**
A directed graph showing downstream consequences:
- Each option as a source node
- Arrows to future capabilities it enables (green)
- Arrows to future capabilities it blocks (red, dashed)
- Arrows to things it degrades (amber, dotted)

**Diagram C — Decision Matrix Heatmap** (if 3+ options and 3+ evaluation axes)
A grid where rows are options, columns are evaluation axes, and cells are
color-coded (green/yellow/red) based on how well each option scores on each
axis. Include a legend.

Use the CSS variables from `visualize:read_me` for theming. Keep diagrams
readable — if the option space is large (>8 options), split into sub-diagrams
or use collapsible grouping.

#### Artifact 2: Markdown Report

Structure the report as follows. Include the frontmatter disclaimer per user
preferences if the user has that preference set.

```
# Decision Analysis: [Decision Title]

## Context
[Binding constraints, soft constraints, decision horizon, success criteria]

## Options Inventory
[For each option: label, description, mechanism, adoption cost, reversibility]

## Implication Map
[Enables/blocks for each option — prose, not just tables]

## Composition Analysis
[Which options layer well, which conflict, which are independent]

## Risk Landscape
[Known risks, unknown-risk surface area, failure severity per option]

## Recommendations
[Not a single "best" pick — instead, a ranked set of viable paths with
explicit trade-off statements: "If you value X over Y, choose A.
If Y matters more, choose B."]

## Follow-Up Questions
[Specific questions the user should investigate next to narrow the decision
further. Frame as concrete next steps, not vague "consider X".]
```

#### Artifact 3: Interactive Follow-Up Menu

After presenting the report, offer the user a structured set of follow-up
interactions using prose suggestions (not tool-based elicitation). Frame these
as actionable deep-dives:

- "Deep-dive into the composition space between [Option A] and [Option B]"
- "Stress-test [Option C] against failure scenario [X]"
- "Map the migration path from current state to [Option D]"
- "Explore the 'do nothing' option — what information would change the calculus?"
- "Compare reversibility costs across the top 3 options"

These are not generic — they must reference the specific options and constraints
from the analysis.

---

## Quality Criteria

The analysis must satisfy these properties:

1. **No false dilemmas.** Never present exactly two options as if they exhaust
   the space. There are always more paths.

2. **No unanchored claims.** Every "pro" or "con" must be grounded in a
   mechanism. "X is more performant" is meaningless without "because Y, which
   matters when Z."

3. **No symmetry bias.** Don't artificially balance pros and cons to appear
   even-handed. If one option is strictly dominated, say so.

4. **Context-specificity.** Generic advice is worthless. Every recommendation
   must reference the user's stated constraints. If a recommendation would be
   the same regardless of the user's context, it's too generic — rethink it.

5. **Compositional awareness.** Always check whether options compose. The best
   solution is often a layered combination, not a single pick.

6. **Reversibility honesty.** Clearly distinguish "easy to try, easy to abandon"
   from "easy to try, expensive to abandon." These look identical at adoption
   time and diverge sharply later.

---

## Edge Cases

- **User provides only two options**: Explicitly search for a third (hybrid,
  deferred, orthogonal). Present it even if they didn't ask.
- **Decision is already made**: Shift to "implications of this decision" mode —
  what does the chosen path enable/block going forward?
- **Domain is unfamiliar**: Use web search to ground the analysis in real
  technical constraints. Do not hallucinate domain-specific facts.
- **Too many options**: Group into families (e.g., "managed services" vs
  "self-hosted" vs "hybrid") and analyze at the family level first, then
  drill into the most promising family.

---

## Anti-Patterns to Avoid

- **The false balance table**: A table with equal numbers of green and red cells
  for every option. Real analysis is asymmetric.
- **The kitchen-sink list**: Listing every conceivable consideration without
  weighting by relevance to the user's context.
- **The recommendation dodge**: "It depends on your needs." The user already
  knows that. Tell them *how* it depends — map the decision function explicitly.
- **The single-axis ranking**: Sorting options by one dimension and ignoring the
  rest. Use the full evaluation axis set.
- **Copy-paste pros/cons**: If a "pro" for Option A is identical to a "pro" for
  Option B, the analysis isn't differentiating — dig deeper.
