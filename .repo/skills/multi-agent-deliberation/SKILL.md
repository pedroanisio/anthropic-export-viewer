---
name: multi-agent-deliberation
description: >
  Run multi-agent deliberation to decompose problems and converge on
  solution plans. Four AI agents (Decomposer, Strategist, Critic,
  Synthesizer) independently propose breakdowns, then iterate through
  adversarial rounds until convergence. Trigger on: "deliberate on",
  "multi-agent solve", "agent deliberation", "converge on a solution",
  "run deliberation", "agent debate", "adversarial planning",
  "multi-perspective breakdown", "structured problem solving",
  "break this problem down with agents", "think through X from
  multiple angles", "give me a real plan not just one take", or
  any request for multiple independent reasoning perspectives
  iterating toward a solution plan. Even "think hard about how
  to solve this" should trigger this skill.
---

# Multi-Agent Deliberation

A structured framework where multiple AI agents with distinct reasoning
roles independently analyze a problem, propose decompositions and
solutions, then iterate through adversarial deliberation rounds until
they converge on a concrete, actionable solution plan.

## Why This Exists

Single-perspective problem solving is brittle. A lone reasoner tends to
anchor on the first decomposition that feels right and optimize within
that frame, missing structural alternatives and downstream risks. This
skill forces the problem through four independent cognitive lenses,
then makes those lenses argue until the surviving plan has been stress-
tested from decomposition through execution strategy.

---

## Core Architecture

### The Four Agents

Each agent is an independent Anthropic API call with a specialized
system prompt. Agents do NOT share state within a round — they see only
the problem statement (round 1) or the prior round's full deliberation
record (round 2+).

| Agent | Role | Failure Mode It Fights |
|---|---|---|
| **Decomposer** | Breaks the problem into orthogonal sub-problems with dependency ordering | Monolithic thinking, hidden coupling |
| **Strategist** | Proposes concrete solution approaches for each sub-problem | Analysis paralysis, abstraction without action |
| **Critic** | Finds gaps, risks, contradictions, unstated assumptions, and integration failures | Groupthink, blind spots, premature consensus |
| **Synthesizer** | Merges the strongest elements into a coherent plan with explicit trade-off rationale | Fragmentation, idea-salad, loss of coherence |

Agent system prompts are defined in `references/agent-prompts.md`.
**Read that file before building the deliberation artifact.**

The visual design system for React artifacts is defined in
`references/claude-react-ds.md`. **Read that file before writing any
`.jsx` artifact.** It contains the design tokens (colors, typography,
spacing, shadows, motion), reusable component patterns (buttons,
cards, badges, agent panels), theming setup, and hard sandbox
constraints. All React artifacts produced by this skill must follow
the Claude React Design System — not ad-hoc Tailwind or improvised
inline styles.

### Deliberation Protocol

```
PROBLEM STATEMENT
       │
       ▼
┌─────────────────────────────────────────┐
│  ROUND 1: Independent Proposals         │
│                                         │
│  Decomposer ──► breakdown proposal      │
│  Strategist ──► solution approaches     │
│  Critic     ──► risk/gap analysis       │
│  Synthesizer ──► initial plan draft     │
│                                         │
│  (No agent sees another's output)       │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  ROUND 2+: Deliberation                 │
│                                         │
│  All agents receive the FULL record     │
│  from all prior rounds.                 │
│                                         │
│  Decomposer: revises breakdown based    │
│    on Critic's objections               │
│  Strategist: adapts approaches to the   │
│    revised breakdown                    │
│  Critic: re-evaluates — flags new       │
│    issues OR downgrades prior ones      │
│  Synthesizer: produces updated plan     │
│    with explicit delta from last round  │
│                                         │
│  Convergence check after each round.    │
└────────────────┬────────────────────────┘
                 │
                 ▼
        CONVERGED SOLUTION PLAN
```

---

## Execution — Step by Step

### Phase 0: Problem Framing

Before spawning any agents, Claude must establish:

1. **Problem Statement**: Restate the user's problem in precise,
   unambiguous language. Ask for clarification if the problem is
   vague. The statement must include:
   - What needs to be achieved (goal)
   - Known constraints (time, resources, technical, political)
   - Known context (domain, stakeholders, prior attempts)
   - Success criteria (how do we know the plan is good?)

2. **Deliberation Configuration**:
   - `max_rounds`: Default 3. User can override. Hard cap at 5.
   - `convergence_threshold`: The Critic must have zero *blocking*
     objections (non-blocking concerns are OK and get documented).
   - `agent_roles`: Default all four. User can add custom agents
     with specialized domain expertise (e.g., "Security Auditor",
     "Cost Analyst"). Custom agents get custom system prompts.

3. **Domain Context** (optional but valuable): If the user provides
   documents, code, specs, or other context, include it in every
   agent's prompt as reference material.

Save the framing to `workspace/problem-framing.json`.

### Phase 1: Round 1 — Independent Proposals

Build a React artifact (`.jsx`) that orchestrates the API calls.
Before writing any code, read both `references/agent-prompts.md` and
`references/claude-react-ds.md` — the former defines agent behavior,
the latter defines the visual system.

The artifact must:

1. Call the Anthropic API four times (once per agent), each with:
   - The agent's system prompt (see agent prompt guidelines below)
   - The problem statement from Phase 0
   - Any domain context
   - Model and token settings per the **Model & Token Selection**
     table in `references/agent-prompts.md` (§Notes on Prompt
     Engineering, item 4). Summary:

     | Tier | Model ID | `max_tokens` | Use when |
     |---|---|---|---|
     | Standard | `claude-sonnet-4-6` | 8192 | ≤4 sub-problems, short problem statement |
     | Complex | `claude-sonnet-4-6` | 16000 | 4–6 sub-problems, moderate context |
     | Heavy | `claude-opus-4-6` | 32000 | 6+ sub-problems, dense context, or lower tier truncates |

     **Tier selection heuristic:** if problem + domain context >10K
     input tokens → Complex. If >25K → Heavy. If any agent truncates,
     escalate to the next tier. See `agent-prompts.md` for full
     guidance including cost estimates.

     **Do NOT use deprecated model strings** like
     `claude-sonnet-4-20250514`. The current Sonnet is `claude-sonnet-4-6`.

   - `temperature: 0.7` (Round 1 — diversity) or `temperature: 0.3`
     (Round 2+ — convergence). The Convergence Judge always uses
     `temperature: 0.3`.

2. Display a live status panel showing which agents have responded.

3. Once all four respond, display each agent's output in a tabbed
   or accordion layout with clear role labels.

4. Save raw outputs to `workspace/round-1/`.

**Critical constraint**: Round 1 agents must NOT see each other's
outputs. This ensures genuine independence. The Synthesizer in
Round 1 works only from the problem statement — it produces a
"naive first plan" that later rounds will improve.

### Phase 2: Rounds 2–N — Deliberation

For each subsequent round:

1. **Assemble the deliberation record**: All prior rounds' outputs
   from all agents, in chronological order, clearly labeled.

2. **Call each agent** with:
   - Their system prompt (same as Round 1)
   - The full deliberation record
   - A round-specific instruction: each agent should explicitly
     reference what changed since the prior round and explain
     why it revised (or maintained) its position.

3. **Display the round's outputs** alongside prior rounds for
   comparison.

4. **Run convergence check** (see below).

5. **Ask the user** after each round:
   ```
   Round {N} complete. The Critic has {blocking_count} blocking
   objections and {concern_count} non-blocking concerns.

   Do you want to:
   (a) Continue to next deliberation round
   (b) Inject your own input into the next round
   (c) Accept the current plan
   (d) Restart with a modified problem statement
   ```

### Phase 3: Convergence Detection

After each round ≥ 2, evaluate convergence. The deliberation has
converged when ALL of:

1. **Critic's blocking objections = 0**: The Critic explicitly
   states no blocking issues remain. Non-blocking concerns (risks
   to monitor, open questions for implementation) are acceptable.

2. **Structural stability**: The Decomposer's sub-problem breakdown
   has not changed materially from the prior round (same sub-problems,
   possibly refined descriptions).

3. **Plan coherence**: The Synthesizer's plan addresses every
   sub-problem identified by the Decomposer with a concrete approach
   endorsed by the Strategist.

If convergence is not reached by `max_rounds`, the Synthesizer
produces a "best-effort plan" with explicit documentation of
unresolved issues.

To evaluate convergence programmatically, add a fifth API call:
a **Convergence Judge** that receives the last two rounds and
outputs a structured JSON verdict:

```json
{
  "converged": true | false,
  "blocking_objections_remaining": 0,
  "structural_delta": "none | minor | major",
  "unresolved_items": [],
  "confidence": 0.0-1.0,
  "recommendation": "accept | continue | restart"
}
```

### Phase 4: Solution Plan Output

Once converged (or max rounds hit), produce the final deliverable:

**A Markdown document** (`solution-plan.md`) containing:

```markdown
---
disclaimer: >
  This document was produced by an automated multi-agent deliberation
  process. No information within should be taken for granted. Any
  statement or premise not backed by a real logical definition or
  verifiable reference may be invalid, erroneous, or a hallucination.
  All claims require independent verification before acting on them.
---

# Solution Plan: {problem_title}

## Problem Statement
{The precise framing from Phase 0}

## Sub-Problem Decomposition
{Final decomposition with dependency graph}

## Solution Approach
{For each sub-problem: the chosen approach, rationale, and trade-offs}

## Risk Register
{All concerns from the Critic — blocking (resolved) and non-blocking}

## Implementation Sequence
{Ordered steps with dependencies, milestones, and decision points}

## Deliberation Provenance
{Summary of how the plan evolved across rounds — what changed and why}

## Unresolved Items
{Anything the deliberation did not settle — explicitly documented}
```

Save to `/mnt/user-data/outputs/solution-plan.md`.

---

## Implementation Modes

### Mode A: Interactive React Artifact (Default)

Build a `.jsx` artifact that:
- Takes the problem statement as input (text area)
- Manages deliberation state in React state (NOT localStorage)
- Calls the Anthropic API for each agent per round
- Displays all rounds with expand/collapse
- Shows convergence status after each round
- Allows user injection between rounds
- Exports the final plan as copyable Markdown
- Includes a light/dark theme toggle

**Styling: use the Claude React Design System.** Before writing any
artifact code, read `references/claude-react-ds.md` and apply its
tokens and patterns:

1. **Inject CSS custom properties** from the DS color primitives via
   an inline `<style>` tag. Support both `:root` (light) and
   `[data-theme="dark"]` variants.
2. **Load Google Fonts** (Playfair Display, DM Sans, Source Sans 3,
   JetBrains Mono) via the font URL in the DS reference.
3. **Color-code agents by semantic role** using the DS palette:
   - Decomposer → `var(--info)` (analytical blue)
   - Strategist → `var(--success)` (constructive green)
   - Critic → `var(--danger)` (adversarial red)
   - Synthesizer → `var(--accent)` (convergence terracotta)
4. **Use DS component patterns** for buttons, cards, badges, inputs,
   and agent output panels. Do not invent new component styles — use
   the `Button`, `Card`, `Badge`, `AgentPanel`, `SectionHeading`,
   and textarea patterns documented in the DS reference.
5. **Apply DS motion tokens** for mount animations: use the stagger
   pattern (`fadeUp` keyframes with 60ms delays) when agent cards
   appear after each round completes.
6. **Respect hard constraints**: no localStorage, no `<form>` tags,
   single default export, Tailwind core classes only (use inline
   styles for precision), all scripts execute after streaming.
7. **Organize the single `.jsx` file** using comment-delimited
   sections as shown in the DS reference §6 (File Structure):
   design tokens → utility components → deliberation engine → main app.

### Mode B: Sequential Execution (Fallback)

If the user prefers not to use an interactive artifact, Claude
executes the deliberation sequentially:
- Make each API call in turn via bash/code execution
- Present each round's outputs in the conversation
- Ask for user input between rounds
- Produce the final plan as a Markdown file

### Mode C: Extended Agents

The user can request additional specialized agents beyond the core
four. Examples:
- **Security Auditor**: Evaluates attack surface of proposed solutions
- **Cost Analyst**: Estimates resource requirements and trade-offs
- **Domain Expert**: Given a specific knowledge domain, evaluates
  technical feasibility
- **Devil's Advocate**: Argues for the opposite of whatever the
  Synthesizer proposes

Custom agents follow the same prompt template structure (see
`references/agent-prompts.md`) with a modified role description
and evaluation criteria.

---

## Workspace Structure

```
deliberation-{problem-slug}/
├── problem-framing.json         # Phase 0 definition
├── config.json                  # max_rounds, agents, thresholds
├── round-1/
│   ├── decomposer.json          # Raw API response
│   ├── strategist.json
│   ├── critic.json
│   ├── synthesizer.json
│   └── user-input.md            # Optional user injection
├── round-2/
│   ├── ...
│   └── convergence-check.json   # Judge verdict
├── round-N/
│   └── ...
└── output/
    ├── solution-plan.md          # Final deliverable
    └── deliberation-log.json     # Full provenance record
```

Save workspace under `/home/claude/deliberation-{slug}/`.
Copy final outputs to `/mnt/user-data/outputs/`.

---

## Constraints

1. **Independence in Round 1 is sacred.** Never let an agent's
   Round 1 output contaminate another agent's Round 1 call.

2. **The Critic must be adversarial.** The Critic's system prompt
   explicitly instructs it to find problems, not to be agreeable.
   If the Critic agrees with everything in Round 1, the prompt is
   broken.

3. **No hallucinated convergence.** The Convergence Judge must have
   concrete evidence for its verdict. "It seems fine" is not
   convergence.

4. **User has veto power.** At any round, the user can override
   any agent, inject constraints, or restart. The framework serves
   the user, not itself.

5. **Provenance is mandatory.** Every element of the final plan
   must trace to a specific agent, round, and deliberation exchange.

6. **The Synthesizer does not invent.** It combines and reconciles
   what other agents produced. If the Synthesizer introduces a
   novel approach not present in any agent's output, it must
   explicitly flag this as its own addition (not attributed to
   the deliberation).

7. **Max token budget awareness.** Token consumption depends on
   problem complexity and model tier. See `references/agent-prompts.md`
   §Notes on Prompt Engineering, item 4 for full cost estimates.
   Approximate budgets per tier:
   - **Standard** (`claude-sonnet-4-6`, 8K output): ~4 agents × 3
     rounds × 8K ≈ 96K output tokens + input context.
   - **Complex** (`claude-sonnet-4-6`, 16K output): ~4 agents × 3
     rounds × 16K ≈ 192K output tokens + input context.
   - **Heavy** (`claude-opus-4-6`, 32K output): ~4 agents × 3
     rounds × 32K ≈ 384K output tokens + input context (~$9.60
     output cost alone). Warn the user before selecting this tier.
   - Add ~20% overhead for convergence checks and retries.
   - Input context grows across rounds (Round 3 can reach 80–120K
     input tokens for Complex-tier problems). Monitor
     `usage.input_tokens` and warn if costs escalate unexpectedly.

8. **Truncation detection is mandatory.** Every API response must
   check `stop_reason`. If `stop_reason === "max_tokens"`, the
   output was truncated mid-generation. The artifact must:
   - Surface the truncation visibly to the user (not silently fail)
   - Report the actual token count from `usage.output_tokens`
   - Note that truncated JSON will fail to parse — this is the
     expected failure mode, not a bug. The fix is to increase
     `max_tokens` or switch to a higher-capacity model tier.
