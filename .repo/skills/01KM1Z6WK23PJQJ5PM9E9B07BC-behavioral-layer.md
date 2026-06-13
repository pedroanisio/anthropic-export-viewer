---
name: behavioral-layer
version: "1.0.0"
description: >
  Define, install, and manage behavioral traits that shape how Claude reasons,
  prioritizes, and responds — independent of any specific task. Use when the
  user asks to create a trait, define a value, install a behavior, set a
  behavioral rule, add a reasoning principle, define a disposition, set a
  thinking style, or encode persistent behavioral directives, epistemic
  postures, reasoning heuristics, or value orderings. Also trigger for
  "always do X before Y", "never assume Z", "prioritize A over B", "adopt
  this mindset", "think like a ___", "can you always be more ___", or any
  request where the user is defining *how Claude should behave or think*
  rather than *what Claude should produce*.
allowed-tools: Read Write Glob
effort: high
metadata:
  ulid: 01KM1Z6WK23PJQJ5PM9E9B07BC
---

# Behavioral Layer

A skill for creating, validating, installing, and composing **behavioral
traits** — structured directives that shape Claude's reasoning, priorities,
and response patterns across all tasks.

## Key Concepts

A **trait** is not a skill. Skills answer "how do I produce X?" — traits answer
"what kind of thinker am I while producing anything?" Traits operate at a layer
below task execution: they constrain, bias, or redirect reasoning itself.

| Dimension       | Skill                        | Trait                             |
|-----------------|------------------------------|-----------------------------------|
| Trigger         | Task-type match              | Always active or context-gated    |
| Output          | A file or artifact           | A behavioral pattern              |
| Scope           | One task at a time           | All tasks simultaneously          |
| Evaluation      | Output quality               | Reasoning quality over time       |
| Analogy         | A recipe                     | A dietary principle               |

## Before You Begin

1. **Read the trait spec** — `.repo/references/01KM1Z6WK23PJQJ5PM9E9B07BC-trait-spec.md` contains the full
   formal structure: sections, fields, validation rules, and composition
   semantics. Read it before writing any trait.

2. **Review examples** — `.repo/references/01KM1Z6WK23PJQJ5PM9E9B07BC-examples.md` contains 3 fully worked
   traits at different complexity levels.

3. **Use the template** — `.repo/templates/01KM1Z6WK23PJQJ5PM9E9B07BC-trait-template.md` is the blank
   starting point for every new trait.

---

## Core Workflow

### Phase 1 — Elicit the Behavioral Intent

Before writing anything, understand what the user actually wants to change
about Claude's behavior. Ask (or infer from context):

1. **What behavior should change?** Get a concrete before/after. "Be more
   rigorous" is too vague — "always identify unstated assumptions before
   accepting a premise" is actionable.

2. **When should it apply?** Three scopes exist:
   - `universal` — every response, no exceptions
   - `contextual` — only when a condition is met (e.g., "when discussing
     empirical claims", "when writing code")
   - `on-demand` — only when explicitly invoked by the user

3. **What does violation look like?** The user may not articulate this
   directly. Probe with: "If I accidentally ignored this rule, what would
   bother you about the output?"

4. **What are the trade-offs?** Every trait has a cost. "Always show full
   derivations" trades off against conciseness. Name the trade-off explicitly
   and confirm the user accepts it.

### Phase 2 — Draft the Trait

Create a `.trait.md` file following the spec in `.repo/references/01KM1Z6WK23PJQJ5PM9E9B07BC-trait-spec.md`.
Use `.repo/templates/01KM1Z6WK23PJQJ5PM9E9B07BC-trait-template.md` as a starting point.

Key writing principles:

- **Imperative over descriptive.** "Identify the weakest premise before
  responding" not "Claude should tend to look for weak premises."
- **Observable over internal.** Define traits in terms of what changes in the
  output, not in terms of mental states. "State uncertainty ranges explicitly"
  not "be humble internally."
- **Examples are mandatory.** Every trait must have at least one positive
  example (correct application) and one negative example (violation). These
  are the ground truth for whether the trait is working.
- **Conflict rules are mandatory.** If the trait could conflict with another
  trait or with a user instruction, the resolution must be specified.

### Phase 3 — Validate the Trait

Run the trait through these checks before presenting it:

1. **Actionability** — Can you, reading only the trait file, unambiguously
   determine what to do differently in a concrete scenario? If not, the
   directives are too vague.

2. **Consistency** — Do the directives contradict each other? Do any examples
   contradict the directives?

3. **Completeness** — Are edge cases addressed? What happens when the trait
   conflicts with an explicit user instruction?

4. **Cost transparency** — Is the trade-off section honest? Does it name
   real costs, or is it hand-wavy ("minimal impact on response time")?

5. **Scope correctness** — If scoped as `contextual`, is the trigger
   condition precise enough to avoid false positives/negatives?

### Phase 4 — Install the Trait

"Installation" means making the trait available for use. There are three
installation targets, in order of persistence:

| Target                  | Persistence       | How                                |
|-------------------------|-------------------|------------------------------------|
| **Session**             | This conversation  | Read the trait file into context   |
| **User Preferences**    | All conversations  | Encode core directives in prefs   |
| **Skill-embedded**      | Task-triggered     | Embed in a skill's SKILL.md       |

For **session** installation: simply read the trait file, confirm with the
user, and begin applying it immediately. State which trait(s) are active.

For **user preferences** installation: extract the minimal directive set from
the trait and format it for the user to paste into their preferences. Warn
the user about the size constraint.

For **skill-embedded** installation: identify which skill(s) the trait should
attach to, and add a `## Behavioral Directives` section to the skill's
SKILL.md containing the trait's core directives.

### Phase 5 — Compose Multiple Traits

When multiple traits are active, conflicts are inevitable. The composition
rules (see `.repo/references/01KM1Z6WK23PJQJ5PM9E9B07BC-trait-spec.md` § Composition) define resolution:

1. **Explicit priority** — If the user has assigned numeric priorities, higher
   priority wins.
2. **Specificity** — A contextual trait overrides a universal trait within its
   scope.
3. **Recency** — If all else is equal, the most recently installed trait wins.
4. **Transparency** — When a conflict is resolved, state which trait won and
   why, unless the user has opted out of meta-commentary.

---

## Output Format

Every trait is delivered as a single `.trait.md` file with the structure
defined in `.repo/references/01KM1Z6WK23PJQJ5PM9E9B07BC-trait-spec.md`. The file is self-contained and
human-readable.

If the user requests a **trait registry** (multiple traits managed together),
produce a `registry.md` index file alongside the individual trait files:

```markdown
# Trait Registry

| ID   | Name                  | Scope       | Priority | Status  |
|------|-----------------------|-------------|----------|---------|
| T-01 | epistemic-caution     | universal   | 1        | active  |
| T-02 | derivation-first      | contextual  | 2        | active  |
| T-03 | steelman-before-crit  | on-demand   | 3        | standby |
```

---

## Anti-Patterns

- **Vague aspirations.** "Be more thoughtful" is not a trait. It has no
  observable output change, no violation criteria, no examples.
- **Unbounded scope.** A universal trait that touches everything ("always
  consider 10 perspectives") will degrade response quality across the board.
  Scope narrowly or accept the cost explicitly.
- **Contradictory stacking.** Installing "be concise" and "show full
  derivations" without a conflict resolution rule guarantees incoherent
  output.
- **Preference duplication.** If a directive already exists in user
  preferences, don't create a trait for it — just reference the preference.
- **Trait creep.** More than 5-7 active universal traits will saturate
  context and produce diminishing returns. Consolidate or scope down.