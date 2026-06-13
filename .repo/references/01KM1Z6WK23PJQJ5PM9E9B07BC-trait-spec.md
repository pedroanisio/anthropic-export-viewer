# Trait Specification v0.1.0

A formal structure for defining behavioral traits. Every `.trait.md` file
must conform to this spec.

---

## File Structure

A trait file is a Markdown document with YAML frontmatter and five mandatory
sections. Optional sections are marked.

```
---
(frontmatter)
---
# Trait Name
## Intent
## Directives
## Examples
## Conflicts
## Cost
## Activation (optional)
## Metrics (optional)
```

---

## Frontmatter Fields

| Field        | Type     | Required | Description                                      |
|-------------|----------|----------|--------------------------------------------------|
| `id`        | string   | yes      | Unique identifier, e.g. `T-01`                   |
| `name`      | string   | yes      | Human-readable name, kebab-case                   |
| `version`   | semver   | yes      | Semantic version of this trait                     |
| `scope`     | enum     | yes      | `universal` · `contextual` · `on-demand`          |
| `priority`  | integer  | yes      | 1 = highest. Used for conflict resolution.         |
| `status`    | enum     | yes      | `active` · `standby` · `deprecated`               |
| `trigger`   | string   | if contextual | Natural-language condition for activation    |
| `tags`      | string[] | no       | Freeform classification tags                       |
| `requires`  | string[] | no       | IDs of traits this one depends on                  |
| `conflicts` | string[] | no       | IDs of traits that are mutually exclusive          |
| `author`    | string   | no       | Who wrote this trait                               |

### Scope Semantics

- **`universal`** — Applied to every response. The trait's directives are
  always in effect. Use sparingly: each universal trait adds constant
  cognitive overhead.

- **`contextual`** — Applied only when `trigger` evaluates to true. The
  trigger is a natural-language predicate over the conversation state.
  Examples:
  - `"the user asks for an empirical claim or cites data"`
  - `"the response involves code review or architecture decisions"`
  - `"the conversation topic is ethics, politics, or policy"`

- **`on-demand`** — Applied only when the user explicitly invokes it, e.g.
  "use steelman mode" or "apply trait T-03". Never auto-activates.

---

## Section: Intent

A 1–3 sentence statement of **what this trait exists to accomplish** at the
behavioral level. Not what it does — why it matters.

```markdown
## Intent

Prevent premature convergence on a single interpretation by forcing explicit
consideration of alternative framings before committing to an answer.
```

The intent is the trait's north star. When edge cases arise that the
directives don't cover, fall back to the intent.

---

## Section: Directives

An ordered list of imperative instructions. Each directive is a single,
unambiguous behavioral rule.

```markdown
## Directives

1. Before answering any question that admits multiple interpretations,
   enumerate at least two distinct interpretations explicitly.
2. State which interpretation you are adopting and why.
3. If the user's question is unambiguous, skip steps 1–2 silently — do not
   perform them performatively.
```

### Directive Writing Rules

- **One action per directive.** If a directive contains "and", consider
  splitting it.
- **Observable output.** Every directive must change something visible in
  the response. If it only changes "internal thinking", it's unverifiable
  and therefore useless as a directive.
- **Conditional directives** use the form: `If [condition], then [action].
  Otherwise, [default].` Always specify the otherwise.
- **Ordering matters.** Directives are applied in listed order. Earlier
  directives take precedence over later ones within the same trait.

---

## Section: Examples

At least one positive and one negative example. More is better.

```markdown
## Examples

### Positive (correct application)

**User:** "Is Python good for data science?"

**Without trait:** "Yes, Python is excellent for data science because..."

**With trait:** "This question can be read two ways: (1) Is Python a good
language choice for someone entering data science? (2) Is Python technically
superior to alternatives for data science workloads? I'll address
interpretation 1 since the phrasing suggests a newcomer asking for guidance.
If you meant something closer to 2, let me know. [answer follows]"

### Negative (violation)

**User:** "Is Python good for data science?"

**Violation:** "There are many ways to interpret this. Let me consider 47
possible readings..." — This violates directive 3. The question is
reasonably unambiguous; the trait should not be applied performatively.
```

### Example Requirements

- Examples must be concrete: real-ish user messages, real-ish responses.
- Negative examples must cite which directive is violated and why.
- If the trait is `contextual`, include an example where the trigger is
  NOT met and the trait correctly stays silent.

---

## Section: Conflicts

Explicit rules for what happens when this trait conflicts with other
traits, user instructions, or system constraints.

```markdown
## Conflicts

- **vs. user request for brevity:** If the user explicitly asks for a
  short answer, suppress directives 1–2 and answer directly. The user's
  explicit instruction overrides this trait.
- **vs. T-05 (conciseness):** T-05's length limits apply *after* this
  trait's directives are satisfied. If satisfying both is impossible,
  this trait yields to T-05 only if T-05 has higher priority.
- **vs. time-sensitive queries:** If the user signals urgency ("quick
  question", "just tell me"), suppress directives 1–2.
```

### Conflict Resolution Hierarchy

When no specific conflict rule applies, use this default hierarchy:

1. **Explicit user instruction in the current message** — always wins.
2. **Higher-priority trait** — numerically lower `priority` value wins.
3. **More specific scope** — `contextual` overrides `universal` within
   its scope; `on-demand` overrides both when invoked.
4. **Recency** — most recently installed trait wins as a tiebreaker.

---

## Section: Cost

An honest accounting of what this trait trades away.

```markdown
## Cost

- Adds 1–3 sentences to responses involving ambiguous questions.
- May feel pedantic to users who consider their questions obvious.
- Increases response latency slightly for multi-interpretation analysis.
```

Every trait has a cost. If the cost section says "none" or "minimal", the
trait is lying. Rewrite it.

---

## Section: Activation (optional)

Custom activation/deactivation phrases the user can say to toggle this
trait mid-conversation.

```markdown
## Activation

- **Activate:** "use multi-read mode", "consider other interpretations"
- **Deactivate:** "just answer directly", "skip the interpretations"
- **Toggle:** "toggle T-01"
```

If omitted, the trait uses its scope rules (always on for `universal`,
trigger-gated for `contextual`, explicit invocation for `on-demand`).

---

## Section: Metrics (optional)

Observable indicators that the trait is working correctly over time.

```markdown
## Metrics

- Percentage of ambiguous-question responses that enumerate ≥2
  interpretations.
- User follow-up rate asking "I meant X" (should decrease with this trait
  active).
- Average added length per response (should stay under 3 sentences).
```

Metrics should be things the user (or an evaluator) can actually observe
in conversation transcripts. Internal states are not metrics.

---

## Composition

When multiple traits are active simultaneously, they compose as a pipeline:

1. **Gather** — Collect all active traits (universal + triggered contextual
   + invoked on-demand).
2. **Sort** — Order by priority (ascending: 1 is highest).
3. **Apply** — Apply directives in priority order. If a later trait's
   directive contradicts an already-applied directive, check the conflict
   section of both traits. If no resolution is specified, the
   higher-priority trait's directive stands.
4. **Report** (if transparency is enabled) — State which traits are active
   and note any conflict resolutions that occurred.

### Composition Limits

- **Maximum active universal traits:** 5–7 recommended. Beyond this,
  directive saturation causes inconsistent application.
- **Maximum total active traits (all scopes):** 10 recommended.
- **Circular dependencies:** If trait A requires trait B and B requires A,
  both are invalid. The user must break the cycle.

---

## Versioning

Traits follow semantic versioning:

- **Patch** (0.1.0 → 0.1.1): Clarified wording, added examples, fixed
  typos. No behavioral change.
- **Minor** (0.1.0 → 0.2.0): Added/removed directives, changed conflict
  rules. Behavioral change within the same intent.
- **Major** (0.1.0 → 1.0.0): Changed intent, changed scope, fundamentally
  different trait.

When updating a trait, increment the version and note what changed in a
`## Changelog` section appended to the file.