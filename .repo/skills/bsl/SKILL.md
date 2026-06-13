---
name: bsl
description: >
  Read, write, validate, trace, test-derive, translate, and explain
  Behavior Spec Language (BSL) specifications. Use this skill whenever
  the user mentions "BSL", "behavior spec", "behavioral specification",
  ".bsl", or asks to specify observable application behavior declaratively.
  Also trigger when the user asks to "write a spec for [feature]",
  "generate test cases from a spec", "trace a rule evaluation",
  "translate TypeScript to BSL" (or vice versa), "validate this spec",
  "lint this spec", "explain this spec", "review this spec", or any
  request involving declarative behavior specifications with rules,
  invariants, side effects, and state machines. If the user uploads a
  file with BSL-like syntax (SPEC header, INPUT/STATE/OUTPUT/RULES
  sections), use this skill even if they don't say "BSL" explicitly.
---

# Behavior Spec Language (BSL) — Skill

## 0. Before You Begin

**Always read the reference spec first** if the task involves grammar
edge cases, type system details, semantic model nuances, or anything
beyond straightforward spec authoring:

```
references/bsl_spec_v0.1.md
```

That file is the canonical v0.1 language specification (~1500 lines).
This SKILL.md inlines the essentials for common tasks; the reference
is authoritative when they conflict.

---

## 1. What BSL Is

BSL is a declarative DSL for specifying **observable application behavior**.
A valid spec defines: accepted inputs, tracked state, produced outputs,
condition→outcome rules, named errors, universal invariants, and
observable side effects — **without prescribing implementation**.

Core design properties:
- **First-match rule evaluation** — rules sorted by priority (ascending),
  first `TRUE` condition fires, remaining are skipped.
- **Atomic outcome application** — all RHS expressions evaluated against
  pre-transition state, applied simultaneously.
- **Mandatory qualification** — field references require `input.`,
  `state.`, or `output.` prefix.
- **Single-fire per invocation** — one EVALUATE call fires at most one rule.
- **HINTS carry zero semantics** — conforming tools must ignore them.

---

## 2. Capabilities

This skill supports six modes. Identify which one the user needs
(they may combine several in one request):

| Mode | Trigger phrases |
|------|----------------|
| **Author** | "write a spec for", "create a BSL spec", "specify behavior" |
| **Validate** | "validate", "lint", "check this spec", "is this valid BSL" |
| **Trace** | "trace", "dry-run", "evaluate this input against", "walk through" |
| **Test-derive** | "generate tests", "derive test cases", "test suite from spec" |
| **Translate** | "convert to TypeScript", "BSL from this TS", "translate" |
| **Explain** | "explain", "review", "walk me through", "what does this spec do" |

---

## 3. Section Structure (Mandatory Order)

Sections MUST appear in this exact order. Optional sections may be
omitted entirely (no empty stubs).

```
SPEC <Name> [v<Major>.<Minor>]

PURPOSE:          # Human-readable behavioral summary
EXTERN:           # Opaque function/predicate signatures
INPUT:            # Incoming data fields (read-only in RULES)
STATE:            # Tracked mutable fields (read-write in RULES)
OUTPUT:           # Produced data fields (write-only in RULES)
RULES:            # Condition → outcome mappings
ERRORS:           # Named error conditions + payloads
INVARIANTS:       # Universal post-transition state predicates
SIDEFX:           # Observable effects bound to rule names
HINTS:            # Non-binding implementation notes (no semantics)
```

---

## 4. Type System Summary

### 4.1 Primitives
```
str  int  float  bool  timestamp  duration
```

### 4.2 Optionals, Collections, Compounds
```
T?                        # T or NONE
list<T>                   # ordered, int-indexed
set<T>                    # unordered, unique
map<K, V>                 # K: str | int | enum variant
record { field: Type }    # structural (duck-typed)
enum { A, B, C }          # closed set of variants
```

### 4.3 Compatibility Rules
- `T` assignable to `T?`. `NONE` assignable to any `T?`.
- `int` assignable to `float` (numeric widening).
- `duration + duration → duration`
- `timestamp + duration → timestamp`
- `timestamp - timestamp → duration`
- No other implicit conversions.

---

## 5. Expression Language Summary

Precedence (highest to lowest):

| Level | Operators |
|-------|-----------|
| Primary | `()`, literals, qualified names, function calls, quantifiers, `??` |
| Unary | `-`, `NOT` |
| Multiplicative | `*`, `/`, `%` |
| Additive | `+`, `-` (also set union/difference when operands are sets) |
| Comparison | `=`, `!=`, `<`, `>`, `<=`, `>=`, `IN` |
| Logical AND | `AND` |
| Logical OR | `OR` |
| Implication | `IMPLIES` |

### Key constructs
- **Coalesce**: `expr ?? fallback` (tightly binding, inside Primary)
- **Quantifiers**: `ALL(collection, var => predicate)`,
  `ANY(collection, var => predicate)`
- **Qualified names**: `input.field`, `state.field`, `output.field`,
  `state.map_field[key_expr]`
- **`IN` operator**: only against set literals: `expr IN {A, B, C}`.
  For dynamic sets use `ANY(set, elem => elem = target)`.
- **Duration literals**: `30s`, `15m`, `48h`, `7d`
- **Temporal**: `NOW` (current timestamp), arithmetic with durations

---

## 6. Rule Syntax

```bsl
rule_name [priority N]:
  <condition_expr>
  =>
    state.field -> <expr>
    output.field -> <expr>
    ERROR <ErrorName>
```

- Priority is optional; default is 100. Lower number = higher priority.
- Condition is a single boolean expression (no `LET` bindings in v0.1).
- Outcome block: zero or more state/output assignments + at most one ERROR.
- All RHS expressions evaluate against **pre-transition** state (atomic).
- `->` is the assignment operator in outcomes (not `=`).

---

## 7. ERRORS, INVARIANTS, SIDEFX Syntax

### ERRORS
```bsl
ERRORS:
  ERROR_NAME:
    message: "Human-readable message"
    field: <expr>          # evaluated against POST-transition state
```

### INVARIANTS
```bsl
INVARIANTS:
  invariant_name:
    <boolean_expr>         # checked against POST-transition state
```
Violations are spec bugs, not runtime errors. They cannot trigger
error handling.

### SIDEFX
```bsl
SIDEFX:
  ON rule_name:
    EMIT event_name {
      field: <expr>        # evaluated against POST-transition state
    }
```
Side effects are post-commit. Declaration order within an ON block
is execution order.

---

## 8. EVALUATE Algorithm (Condensed)

```
EVALUATE(input, state):
1. Sort rules by (priority ASC, textual order ASC). Default priority = 100.
2. For each rule: evaluate condition against (input, state).
   First TRUE condition → FIRING rule. If none fire → no output, no change.
3. Evaluate all outcome RHS against PRE-transition state (snapshot).
4. Apply: state mutations, output assignments.
5. If ERROR triggered: evaluate error fields against POST-transition state.
6. Execute SIDEFX for firing rule (post-commit, POST-transition state).
7. Check INVARIANTS against POST-transition state.
8. Return (output, state', error?, side_effects, violations).
```

---

## 9. Mode-Specific Instructions

### 9.1 Author Mode

When the user describes a feature in natural language:

1. **Identify the behavioral boundary.** What is one invocation?
   What persists across invocations (STATE)? What comes in (INPUT)?
   What goes out (OUTPUT)?
2. **Extract external dependencies.** Any function the spec calls but
   doesn't define → EXTERN. Declare full signatures with types.
3. **Draft rules.** Each rule should be a single behavioral case.
   Assign priorities to establish evaluation order. Use explicit
   priorities when order matters; omit when rules are mutually exclusive
   by condition.
4. **Define errors.** Every ERROR referenced in RULES must have a
   definition in ERRORS.
5. **Write invariants.** Think: "what must ALWAYS be true about the
   state, regardless of which rule fired?" These are the spec's
   self-consistency guarantees.
6. **Add SIDEFX.** Observable events that external systems care about.
   Bind each to the rule that triggers it.
7. **HINTS last.** Implementation notes that don't affect behavior.

**Output format**: Markdown file with the spec in a ````bsl` fenced
code block. Include a brief prose explanation before the spec.

**Validation pass**: After drafting, mentally run through the validate
checklist (§9.2) before presenting to the user. Flag any issues inline.

### 9.2 Validate Mode

Check the following in order. Report ALL violations, not just the first:

**Structural checks:**
- [ ] SPEC header present with name (version optional)
- [ ] Sections appear in mandatory order (§3)
- [ ] No empty section stubs
- [ ] Indentation is consistent (spaces only)

**Declaration checks:**
- [ ] Every field reference uses `input.`/`state.`/`output.` prefix
- [ ] Every EXTERN call in RULES has a matching declaration in EXTERN
- [ ] Every ERROR trigger in RULES has a definition in ERRORS
- [ ] Every SIDEFX `ON rule_name` matches a rule name in RULES
- [ ] STATE fields with defaults use `=` syntax
- [ ] No duplicate field names within a section
- [ ] No duplicate rule names

**Type checks:**
- [ ] Comparison operands are type-compatible
- [ ] `IN` only used with set literals (not dynamic sets)
- [ ] `??` operands: LHS is `T?`, RHS is `T`
- [ ] Duration arithmetic only with timestamps/durations
- [ ] Quantifier collection arg matches declared collection type
- [ ] Enum variants are unambiguous in context

**Semantic checks:**
- [ ] No two rules at same priority with overlapping conditions
  (warn, not error — may be intentional)
- [ ] Invariants reference only state/input fields (not output)
  — wait, invariants CAN reference input (§6.4: "with input still
  available for read"). This is valid.
- [ ] EXTERN functions used in conditions are treated as pure
- [ ] No assignment to `input.*` fields in outcomes
- [ ] Outcome assignments target only `state.*` or `output.*`

### 9.3 Trace Mode

Given: a spec, input values, and initial state.

1. List all rules sorted by (priority, textual order).
2. For each rule, evaluate the condition step by step.
   Show intermediate expression values.
3. When a condition evaluates TRUE, mark it as FIRING. Stop checking.
4. Show the outcome RHS evaluations (against pre-transition snapshot).
5. Show the post-transition state.
6. Evaluate error fields if ERROR triggered (against post-state).
7. List SIDEFX that execute.
8. Evaluate each invariant against post-state. Show pass/fail.
9. Present final result tuple.

Format traces as numbered steps with clear state snapshots.
Use a table for before/after state comparison.

### 9.4 Test-Derive Mode

From a spec, generate test cases covering:

1. **Happy path per rule**: one test where each rule fires successfully.
2. **Boundary conditions**: edge values for numeric comparisons
   (e.g., `attempts = 4` vs `attempts = 5` for `>= 5`).
3. **Error paths**: one test per ERROR trigger.
4. **Invariant probes**: inputs that, if the implementation is buggy,
   would violate each invariant. These tests assert the invariant holds.
5. **No-rule-fires case**: input/state combo where no condition is TRUE.
6. **Priority ordering**: two rules whose conditions overlap — verify
   the higher-priority one fires.
7. **EXTERN mock scenarios**: for each EXTERN function, test with
   different return values to exercise branching.

Output format: Markdown with a table of test cases, or TypeScript
test code if the user requests executable tests. Each test case:
- Name, description
- Input values
- Initial state
- Expected: firing rule, post-state, output, error, side effects

### 9.5 Translate Mode

#### BSL → TypeScript
1. Map each section to its TS equivalent:
   - INPUT/STATE/OUTPUT → interfaces
   - EXTERN → `declare function` stubs
   - RULES → `evaluate()` function with if/return chain (priority order)
   - ERRORS → error return objects
   - INVARIANTS → `checkInvariants()` function
   - SIDEFX → side effect array population after each rule
2. Preserve atomic semantics: read all pre-state values before mutating.
   Use `const snapshot = { ...state }` or similar.
3. Use `??` for coalesce (TS supports it natively).
4. Duration → milliseconds constants. Timestamp → `Date`.

#### TypeScript → BSL
1. Identify the evaluate-like function (input + state → output + state').
2. Each `if/return` branch → one RULES entry.
3. Extract interfaces → INPUT/STATE/OUTPUT sections.
4. `declare function` → EXTERN.
5. Post-evaluation assertions → INVARIANTS.
6. Event emissions → SIDEFX.
7. Verify: does the BSL spec reproduce the same behavior for all
   inputs? Flag any TS behavior that BSL v0.1 cannot express
   (e.g., loops, multi-step pipelines within one call).

### 9.6 Explain Mode

Walk through the spec section by section:
1. **PURPOSE**: what this spec is about, in plain language.
2. **Data model**: what goes in (INPUT), what's tracked (STATE),
   what comes out (OUTPUT). Highlight defaults and optionals.
3. **External dependencies**: what the spec assumes exists (EXTERN).
4. **Rule-by-rule walkthrough**: for each rule, explain the condition
   in plain English, what happens when it fires, and why the priority
   makes sense relative to other rules.
5. **Error conditions**: when each error triggers and what data it carries.
6. **Invariants**: what guarantees the spec makes about consistency.
7. **Side effects**: what observable events are emitted and when.
8. **Design review**: flag potential issues — overlapping conditions,
   missing edge cases, invariants that might not hold, unused EXTERN
   functions, unreachable rules.

---

## 10. Common Pitfalls (Warn Users)

1. **`=` vs `->` confusion**: `=` is comparison (in conditions) and
   default-value assignment (in STATE declarations). `->` is the
   outcome assignment operator. Never use `=` in outcome blocks.
2. **Missing qualification**: `status` is invalid; must be `state.status`.
3. **Sequential thinking in outcomes**: outcomes are atomic. Don't
   assume one assignment is visible to another within the same rule.
4. **`IN` with dynamic sets**: `x IN state.my_set` is invalid in v0.1.
   Use `ANY(state.my_set, elem => elem = x)`.
5. **Duplicate EXTERN calls in conditions**: if two rules branch on
   the same EXTERN result (e.g., `charge_payment().status`), the
   function appears in both conditions. This is valid (EXTERN calls
   in conditions are pure/cacheable) but ergonomically rough.
   Acknowledge the `LET` gap (v0.2 candidate).
6. **Invariant vs guard confusion**: invariants don't prevent bad state —
   they detect it. If you want to block a transition, use a rule
   condition, not an invariant.
7. **Set literal syntax**: `{A, B}` is a set; `{a: 1}` is a record.
   The parser distinguishes by `:` presence. Don't mix.
8. **No composition**: one spec cannot import another (v0.1 limitation).
   Multi-spec systems need external orchestration.

---

## 11. Output Conventions

- **File format**: Markdown (`.md`) with BSL in ````bsl` fenced blocks.
- **File location**: save to `/mnt/user-data/outputs/`.
- **Naming**: `<spec_name_snake_case>.md`
  (e.g., `user_login.md`, `cart_checkout.md`).
- **Structure**:
  1. Frontmatter disclaimer (per user preferences)
  2. Brief prose overview
  3. The BSL spec in a fenced code block
  4. Any additional notes (trace results, test cases, review findings)

---

## 12. Reference

For the full formal grammar (PEG), complete semantic model, worked
examples with traces, token comparison methodology, and design
rationale, read:

```
references/bsl_spec_v0.1.md
```

Consult the reference when:
- A user asks about grammar edge cases (CoalesceExpr placement,
  set/record literal disambiguation, INDENT/DEDENT semantics)
- You need to verify a type compatibility rule
- You need the exact EVALUATE algorithm (not the condensed version)
- The user asks about design rationale (§9 of the reference)
- The user asks about known limitations (§10 of the reference)
