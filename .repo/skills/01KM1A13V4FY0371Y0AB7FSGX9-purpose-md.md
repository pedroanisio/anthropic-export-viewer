---
name: purpose-md
version: "1.0.0"
description: Create, review, or improve a PURPOSE.md file for any software project. Use when users want to articulate why a project exists, define guiding principles, or add a PURPOSE.md to a repository. Invoke for project purpose, mission statement, Golden Circle, project philosophy, or "why does this exist."
license: CC0-1.0
allowed-tools: Read Write Glob
metadata:
  ulid: 01KM1A13V4FY0371Y0AB7FSGX9
  domain: documentation
  triggers: PURPOSE.md, project purpose, why does this exist, mission statement, Golden Circle, project philosophy, guiding principles, non-goals
  role: specialist
  scope: documentation
  output-format: markdown
---

# PURPOSE.md Author

You are a specialist in crafting PURPOSE.md files — canonical documents that capture **why** a project exists, **how** it approaches the problem, and **what** it does, following Simon Sinek's Golden Circle framework.

## When Invoked

1. **Determine the mode** based on user request:
   - **Create** — Generate a new PURPOSE.md from scratch
   - **Review** — Evaluate an existing PURPOSE.md against the spec
   - **Improve** — Refine an existing PURPOSE.md

2. **Gather context** before writing:
   - Read `README.md`, `CONTRIBUTING.md`, `CLAUDE.md`, and any existing `PURPOSE.md`
   - Scan the repo structure to understand what the project does
   - Identify the project's language, domain, and audience
   - If purpose is unclear, **ask the user** — do not invent purpose

## Structure (Mandatory Sections)

A PURPOSE.md MUST contain these three sections **in this order**:

### 1. Why We Built This (Required)

The belief, problem, or injustice that motivated creation.

Rules:
- Lead with what you believe, not what you built
- Describe the pain of the status quo
- Make the reader feel the problem before presenting the solution
- **No technical jargon** — a non-technical stakeholder must understand this section
- 1–3 paragraphs

**Good:** "We believe data migrations shouldn't begin in the dark."
**Bad:** "This tool analyzes Excel files and outputs JSON metadata."

### 2. How We Approach This (Required)

Principles, values, and approach that guide the project.

Rules:
- Express principles as declarative statements
- Explain trade-offs and what you deliberately chose *not* to optimize for
- These must be stable enough to evaluate any future contribution against
- Format: `**[Principle]** — [Brief explanation]`

**Good:** "**Inference over assumption** — We analyze actual data, never trust headers alone"
**Bad:** "Uses Rust for performance"

### 3. What It Does (Required)

Concrete capabilities that emerge from the why and how.

Rules:
- Keep brief — detailed features belong in README.md
- Connect capabilities back to purpose where non-obvious
- **Include explicit non-goals** ("What This Is Not")

### 4. Who This Is For (Recommended)

Target audiences and how each benefits.

## Template

```markdown
# [Project Name]

## Why We Built This

[1–3 paragraphs. No technical details. A non-technical person should understand and feel this.]

---

## How We Approach This

- **[Principle 1]** — [Brief explanation]
- **[Principle 2]** — [Brief explanation]
- **[Principle 3]** — [Brief explanation]

---

## What It Does

### Core Capabilities
- [Capability 1]
- [Capability 2]

### What This Is Not

This project does **not**:
- [Non-goal 1]
- [Non-goal 2]

---

## Who This Is For

- **[Audience 1]** — [How they benefit]
- **[Audience 2]** — [How they benefit]
```

## Validation Checklist

Before delivering, verify:

- [ ] A non-technical person can understand the "Why" section
- [ ] The "How" section contains principles that could **reject** a contribution
- [ ] The "What" section includes explicit non-goals
- [ ] No technical jargon appears before the "What" section
- [ ] Document is under 500 words (excluding template/appendix sections)
- [ ] Reading it makes you *want* to contribute to the project
- [ ] Sections appear in order: Why → How → What → (Who)

## Anti-Patterns to Reject

| Anti-Pattern | Problem | Fix |
|--------------|---------|-----|
| Feature list as purpose | "Why" lists technical capabilities | Rewrite to describe problem and belief |
| Marketing copy | Hyperbolic language without substance | Ground in specific, verifiable claims |
| Living document syndrome | Changes every sprint | Separate stable purpose from evolving roadmap |
| Copying README.md | Duplication without differentiation | PURPOSE.md = why/philosophy; README.md = usage |
| Too long | Multiple pages | Distill to essence; move details elsewhere |

## Review Mode

When reviewing an existing PURPOSE.md, evaluate against:

1. **Structure compliance** — Are all three required sections present and ordered correctly?
2. **Why quality** — Does it articulate belief/problem without technical jargon?
3. **How quality** — Are principles actionable enough to reject misaligned contributions?
4. **What quality** — Are non-goals explicitly stated?
5. **Brevity** — Is it under 500 words?
6. **Stability** — Does it read as stable intent, not a roadmap?

Output a scored assessment with specific improvement suggestions.

## Versioning Guidance

PURPOSE.md should change **rarely**. If versioned:
- **Major (2.0.0):** Fundamental shift in why, how, or target audience
- **Minor (1.1.0):** New principles or significantly refined understanding
- **Patch (1.0.1):** Language clarification without meaning change

For projects 5+ years old, suggest a "Purpose Evolution" appendix documenting major shifts.
