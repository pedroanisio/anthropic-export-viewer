---
name: technical-howto
description: >
  Write, review, or improve technical how-to guides — the goal-oriented,
  step-by-step kind aimed at practitioners who already have baseline knowledge.
  Use this skill whenever the user asks to "write a how-to", "create a tutorial",
  "document how to do X", "write a guide for X", "step-by-step instructions for X",
  "help me write technical documentation", "draft setup instructions", "write an
  onboarding guide", "create a runbook", "write a migration guide", "document this
  process", or any request to produce instructional technical content. Also trigger
  when the user asks to review, critique, restructure, or improve an existing how-to
  guide, or when they paste a draft how-to and ask for feedback. If the user mentions
  "Diátaxis", "documentation quadrants", or "how-to vs tutorial vs reference", use
  this skill. Covers Markdown, HTML, and docx output. Does NOT cover pure API
  reference docs (use reference-doc patterns instead) or conceptual explainers
  (those are the "explanation" quadrant, not "how-to").
---

# Technical How-To Skill

## Purpose

Most technical how-to guides are mediocre. They conflate teaching (tutorials)
with directing (how-tos) with describing (reference) with discussing
(explanation). The result is a document that half-teaches, half-directs,
and fully frustrates.

This skill produces how-to guides that are single-purpose instruments: one
problem, one audience, concrete sequential steps, no digression.

The framework here is grounded in the Diátaxis documentation system (Daniele
Procida), Cognitive Load Theory (John Sweller, 1988), and the Google Developer
Documentation Style Guide. See `references/foundations.md` for details on these
sources.

---

## Genre Definition: What a How-To IS and IS NOT

Get this wrong and nothing else matters. A how-to guide is ONE of four
documentation types. It is not the other three.

| Quadrant      | Purpose             | Reader state                    | Example                                   |
|---------------|---------------------|---------------------------------|-------------------------------------------|
| **Tutorial**  | Learning-oriented   | "I don't know what I don't know"| "Getting started with Docker"              |
| **How-To**    | Goal-oriented       | "I know what I need, not how"   | "How to configure mTLS between services"  |
| **Reference** | Information-oriented | "I need exact specs"            | "API endpoint reference for /v2/users"    |
| **Explanation**| Understanding-oriented | "I want to understand why"   | "Why Kubernetes uses etcd for state"      |

A how-to guide:
- Assumes the reader has baseline competence (they've done the tutorial).
- Solves a specific, nameable problem.
- Contains ordered steps that produce a verifiable result.
- Does NOT teach foundational concepts inline — it links to them.
- Does NOT exhaustively describe every parameter — that's reference.
- Does NOT discuss trade-offs or architectural reasoning at length — that's
  explanation.

If the user's request actually needs a tutorial, reference, or explainer, say
so and offer to write the correct type instead. Don't silently produce a
how-to when they need something else.

---

## Workflow

### Phase 0 — Classify the Request

Before writing a single word, determine:

1. **Is this actually a how-to?** Check against the genre table above. If the
   user says "write a tutorial on X" but the content is goal-oriented for
   practitioners, it's a how-to regardless of what they called it. Clarify the
   genre with the user if ambiguous.

2. **Does a how-to already exist?** If the user is editing or reviewing an
   existing guide, switch to Review Mode (Phase 5).

### Phase 1 — Scope Declaration

Every great how-to begins with a precise scope. Extract or ask for:

1. **The outcome sentence.** One sentence describing what the reader will have
   accomplished by the end. This becomes the title and the contract.
   - Bad: "Docker Networking"
   - Good: "How to route traffic between two Docker containers on a custom
     bridge network"

2. **The audience line.** Who is this for and what do they already know?
   - Bad: "developers"
   - Good: "Backend developers who have deployed at least one Docker container
     but haven't configured custom networks"

3. **Prerequisites.** An explicit, testable list of what the reader must have
   before starting. Every item should be verifiable:
   - Bad: "Some experience with Docker"
   - Good: "Docker Engine ≥ 24.0 installed (`docker --version`), a running
     Docker daemon (`docker info` returns without error)"

4. **Environment assumptions.** OS, shell, language versions, cloud provider,
   tool versions. Pin them. An unversioned how-to is a time bomb.

5. **Non-goals.** What this guide explicitly does NOT cover. This prevents
   scope creep during writing and manages reader expectations.

If the user hasn't provided enough to fill this out, ask — but in a single
round, not an interview chain. If reasonable defaults exist, state them and
proceed. The user can redirect.

### Phase 2 — Step Design

This is the structural core. Each step in a how-to must satisfy these
properties:

#### The OVER Properties

Every step must be:

- **O — Observable.** The reader can see that the step happened. There is
  output, a state change, a file created, a response returned.

- **V — Verifiable.** The reader can confirm the step succeeded. Include the
  expected output, a check command, or a success criterion.

- **E — Executable.** The step contains everything needed to perform it. No
  implicit knowledge, no "configure as appropriate."

- **R — Reversible (when possible).** If the step can be undone, say how.
  If it can't (destructive operations), warn clearly before the step, not after.

#### Step Structure Template

Each step follows this structure:

```
## Step N: [Verb phrase describing the action]

[1-2 sentences of context: WHY this step exists in the sequence. Not a lecture —
just enough to orient the reader.]

[The command, code block, or action to perform]

[Expected output or success criterion]

[If applicable: common failure modes and what to do about them]
```

#### Step Sequencing Rules

- **One action per step.** If you catch yourself writing "and then" inside a
  step, split it into two steps.

- **Forward-only dependencies.** Step N must never require knowledge from
  Step N+2. Each step depends only on the initial prerequisites and the
  results of preceding steps.

- **No orphan state.** Every step must leave the system in a valid,
  recoverable state. If the reader stops after Step 4 of 7, the system
  should not be broken.

- **Checkpoint steps.** For long guides (>7 steps), insert explicit checkpoint
  steps: "At this point, your system should look like [X]. Verify with [Y]
  before proceeding."

### Phase 3 — Failure Path Documentation

This is what separates great from average. Average guides describe the happy
path. Great guides document reality.

For each step, identify:

1. **Common errors.** What goes wrong most often? Include the actual error
   message (or the first 2-3 lines of it), not a paraphrase.

2. **Diagnostic commands.** How does the reader figure out what went wrong?

3. **Recovery actions.** What do they do about it? Be specific — "check your
   configuration" is not a recovery action. "Open `config.yaml` and verify
   that `tls.enabled` is set to `true` (not `True` or `yes`)" is.

4. **Bail-out points.** Sometimes the right answer is "stop and try a
   different approach." Name these. Link to alternatives.

Not every step needs all four. Use judgment — but err toward including too
many failure paths rather than too few. The happy path is the easy part.
The failure paths are where the reader actually needs you.

### Phase 4 — Prose Discipline

Apply these rules to every sentence:

#### Concreteness Over Abstraction

- Bad: "Wait for the process to complete."
- Good: "Wait approximately 90 seconds. The command exits with
  `Deployment complete` when finished."

- Bad: "You may need to adjust the timeout."
- Good: "Set `timeout_ms` to `30000` in `config.yaml`, line 12."

- Bad: "Make sure the service is running."
- Good: "Run `systemctl status myservice`. The output should show
  `Active: active (running)`."

#### Cognitive Load Rules

These derive from Sweller's Cognitive Load Theory. Working memory holds
~4 chunks. Every unnecessary element competes for those slots.

1. **No inline explanations.** If a concept needs explaining, link to an
   explanation document. Do not interrupt the step sequence with "Note: the
   reason this works is because..."

2. **No tangential tips.** "Pro tip:" blocks are almost always extraneous
   cognitive load. If the information is necessary, it belongs in a step.
   If it's not necessary, it belongs in a separate "Tips" section at the
   end, or nowhere.

3. **No "wall of prerequisites."** If the prerequisites list exceeds 6
   items, the guide's scope is too wide. Split into multiple guides.

4. **Progressive disclosure.** Front-load the minimal viable path. Put
   optional parameters, alternative approaches, and advanced configuration
   in clearly marked sections after the core steps.

#### Voice and Tone

Follow the Google Developer Documentation Style Guide conventions:

- Second person, present tense, active voice.
- Imperative mood for instructions: "Run the command" not "You should run
  the command" or "The command can be run."
- No humor, no personality, no "we" (unless the author is a named team).
- Conversational but not casual. Respect the reader's time.
- Define acronyms on first use. Don't assume shared jargon.

### Phase 5 — Review Mode

When reviewing or improving an existing how-to, evaluate against these axes
(in priority order):

1. **Genre purity.** Is it actually a how-to, or has it drifted into
   tutorial/reference/explanation territory? Identify the drifted sections
   and recommend extraction.

2. **Scope clarity.** Does the title promise exactly what the guide
   delivers? No more, no less?

3. **Step quality.** Run each step against the OVER properties. Flag steps
   that are unobservable, unverifiable, incomplete, or irreversibly
   destructive without warning.

4. **Failure coverage.** Is the happy path the ONLY path? Flag steps with
   zero failure documentation that have known failure modes.

5. **Cognitive load.** Count inline digressions, tangential notes, undefined
   terms, and "pro tips." Each one is a load violation.

6. **Freshness.** Are versions pinned? When was the guide last verified?
   Do the code samples compile/run against the current release?

7. **Concreteness.** Flag every instance of vague language: "some,"
   "appropriate," "as needed," "may need to," "a few minutes." Replace
   with specifics.

Produce the review as a prioritized list of findings, not a rewrite. The
user decides what to fix.

---

## Output Format

### Default: Markdown

Unless the user specifies otherwise, output Markdown. Structure as follows:

```markdown
---
disclaimer: >
  No information within this document should be taken for granted. Any
  statement or premise not backed by a verifiable reference, reproducible
  command, or logical definition may be invalid, erroneous, or a
  hallucination. Verify all steps against your own environment before
  relying on them.
last_verified: YYYY-MM-DD
tool_versions:
  - tool: "name"
    version: "x.y.z"
---

# How to [Verb Phrase Describing the Outcome]

## Overview

[2-3 sentences: what this guide accomplishes, who it's for, and what
the end state looks like.]

## Prerequisites

[Numbered list. Each item is testable — includes a command or check
the reader can run to verify they meet the prerequisite.]

## Steps

### Step 1: [Verb phrase]

[Context sentence]

[Action: command/code block/instruction]

[Verification: expected output or check command]

[If applicable: troubleshooting for this step]

### Step 2: ...

[Repeat pattern]

## Verification

[A final end-to-end check that confirms the entire guide succeeded.
This is distinct from per-step checks — it validates the integrated
result.]

## Troubleshooting

[Common issues that span multiple steps or aren't tied to a single
step. Organized by symptom, not by cause.]

## Next Steps

[Links to related how-tos, relevant explanation docs, or reference
material. NOT a continuation of this guide — that would mean the
scope was wrong.]
```

### Alternative Outputs

- If the user requests **docx**, read `/mnt/skills/public/docx/SKILL.md`
  first, then apply this same structure through that pipeline.
- If the user requests **HTML**, produce a single self-contained HTML file
  with semantic markup (`<article>`, `<section>`, `<code>`, `<pre>`).

---

## Quality Checklist

Before presenting the final output, verify:

- [ ] Title is a verb phrase that names the exact outcome.
- [ ] Audience and prerequisites are explicit and testable.
- [ ] Every step satisfies all four OVER properties.
- [ ] No step performs more than one action.
- [ ] No inline explanations or "pro tips" interrupt the step flow.
- [ ] Failure paths exist for every step with known failure modes.
- [ ] All versions are pinned (tools, languages, OS, APIs).
- [ ] A final end-to-end verification step exists.
- [ ] Vague language count is zero (grep for: "some", "appropriate",
      "as needed", "may", "might", "a few", "several", "various").
- [ ] Frontmatter includes the disclaimer and `last_verified` date.
- [ ] Links exist for concepts that aren't explained inline.

---

## Anti-Patterns

Recognize and avoid these common failure modes:

- **The Tutori-How-To.** Starts by teaching basics the audience should
  already know. Symptom: the first three steps are installation and setup
  that belong in a tutorial or prerequisites list.

- **The Reference Dump.** Lists every flag, parameter, and option for a
  command instead of showing the one invocation that solves the problem.
  Symptom: a step that is a table of 20 CLI flags.

- **The Explainer Drift.** Interrupts steps with paragraphs about why
  things work the way they do. Symptom: paragraphs between steps that
  don't contain commands or actions.

- **The Happy-Path-Only Guide.** Describes what happens when everything
  goes right. Symptom: no troubleshooting sections, no error messages
  shown, no "if you see X, do Y" blocks.

- **The Vague Step.** "Configure the service appropriately for your
  environment." This is not a step. It's an abdication.

- **The Version Roulette.** No pinned versions. Symptom: commands that
  work in 2024 and fail in 2025 with no indication of what changed.

- **The Zombie Guide.** No `last_verified` date. No indication of whether
  the steps still work. The guide may be actively harmful.

---

## Edge Cases

- **User wants a guide but the technology doesn't exist yet or is too
  new.** Use web search to find the current state. If documentation is
  too thin to write a reliable guide, say so. A guide based on guesses
  is worse than no guide.

- **User provides a transcript or log and says "turn this into a how-to."**
  Extract the steps, verify sequencing, add failure paths, strip
  conversation artifacts. The raw transcript is input, not output.

- **User wants a guide for an opinionated process (e.g., "how to do code
  review").** These are partially how-to (the mechanical steps) and
  partially explanation (the judgment calls). Separate them. Write the
  how-to for the mechanical part and link to an explainer for the
  judgment calls.

- **The guide would be dangerously long (>15 steps).** Split into
  multiple guides. Each sub-guide should be independently completeable
  and leave the system in a valid state. Link them sequentially.

- **User asks for a how-to but what they actually need is a runbook
  (operational procedure with decision trees).** Runbooks have branching
  logic; how-tos are linear. Clarify which they need.
