---
disclaimer:
  notice: >-
    No information within this document should be taken for granted.
    Any statement or premise not backed by a real logical definition
    or verifiable reference may be invalid, erroneous, or a hallucination.
    This refined prompt is a specification, not a guarantee. Implementation details
    depend on actual codebase structure, available metadata, and inspector capabilities.
    Use this as a template; customize for your specific context.
  generated_by: "Claude Opus 4.6 via Claude Code"
  date: "2026-04-01"
version: 1.0
created: 2026-04-01
---

# Codebase Inspection Prompt

## Core Prompt

```markdown
## Codebase Comparative Analysis

**Input:** `<TARGET_CODEBASE REF="...">`  
**Context:** Comparison against `<REFERENCE_CODEBASE>` (our codebase / standards)

---

## Output Requirements

Produce a **technical report** (`docs/repo-inspect-<TIMESTAMP>.md`) with these sections:

### 1. Disclaimer Header (Required)
Include at the top:
\`\`\`markdown
---
disclaimer: >
  This analysis is based on static code inspection and available documentation.
  All claims are grounded in verifiable code evidence or explicit logical inference.
  No assertion in this report should be accepted without reviewing the cited code locations.
  Inferences beyond the evidence are explicitly marked as such.
source_analysis_date: <ISO-8601>
---
\`\`\`

### 2. Executive Summary
- **Scope:** What was inspected (file count, languages, LOC, commit range if applicable)
- **Key Finding (1 sentence):** The single most actionable insight
- **Risk Level:** Whether reuse/adoption has technical debt implications
- **Effort Estimate:** If recommendations are adopted

### 3. Fact-Based Comparative Analysis

**Architecture & Design**
- Observed patterns (with file/module references)
- Dependency structure (if applicable)
- Separation of concerns
- **Evidence source:** File paths, line numbers, or design docs

**Code Quality Indicators**
- Test coverage (cite test files/ratios)
- Error handling strategy (show examples)
- Type safety / static analysis (if applicable)
- **Evidence source:** Actual test files, exception patterns, type definitions

**Performance & Scalability**
- Observed bottlenecks or optimizations (with code citations)
- Resource usage patterns
- Caching / memoization strategies
- **Evidence source:** Profiling results, algorithmic complexity observations, config files

### 4. Structured Findings

#### Strengths (with Evidence)
\`\`\`
- **[Strength Name]**
  Observed in: \`<file>:<line-range>\`
  Example: [code snippet or pattern]
  Impact: [concrete benefit or consequence]
\`\`\`

#### Weaknesses (with Evidence)
\`\`\`
- **[Weakness Name]**
  Observed in: \`<file>:<line-range>\`
  Pattern: [what's missing or problematic]
  Risk: [concrete negative consequence]
\`\`\`

#### Reusable Ideas (with Transferability Assessment)
\`\`\`
- **[Idea Name]**
  Location: \`<file>:<line-range>\`
  What it does: [functional description]
  Transferability: [why it would/wouldn't work in our context]
  Dependencies: [what else would need to come with it]
\`\`\`

### 5. Recommendations

Each recommendation must be one of three types:

**Type A: Adopt** (Copy a pattern or component)
- What: [Specific thing to adopt]
- From: [Code reference in target]
- Why: [Evidence-based rationale]
- Effort: [Time estimate + dependencies]
- Risks: [Known issues, language/framework compatibility, etc.]

**Type B: Adapt** (Modify a pattern for our context)
- What: [Pattern to adapt]
- From: [Code reference in target]
- How: [Concrete changes needed]
- Why adaptation is necessary: [Factual differences between codebases]
- Effort: [Time estimate]
- Risks: [Unknown unknowns flagged]

**Type C: Avoid** (Reasons not to use something)
- What: [Pattern/approach to avoid]
- Why: [Evidence-based reasoning]
- Alternative: [What to do instead, if applicable]

### 6. Confidence & Limitations

Explicitly state:
- **What you inspected:** File list, commit hash, or branch
- **What you did NOT inspect:** (Tests? Deployment? Monitoring? Docs?)
- **Confidence level** for each major claim: High/Medium/Low
- **Known limitations:** (Missed context? Language familiarity gaps?)

---

## Guidelines for Evidence

- **Facts:** Code inspection, file structure, test assertions, config values, static analysis results
  - Always cite: \`<file>:<line-range>\` or \`<function-name>\`
  
- **Inferences:** Logical deductions from facts (e.g., "caching is used because X API call occurs in Y places")
  - Mark explicitly as *inferred from*
  - Show the chain of logic
  
- **Speculation:** Avoid entirely. If you must flag something, label it "**UNKNOWN**" and explain why verification is impossible from code alone

---

## Forbidden

- Flattery or aspirational language ("elegant", "beautiful", "clever")
- Claims unsupported by code citation
- Comparisons to codebases you haven't inspected
- Recommendations based on "common practice" without evidence
- Dismissals without evidence ("this won't scale" — show why)

---

## Output Format

- **File:** \`docs/repo-inspect-<TIMESTAMP-ISO8601>.md\`
- **Code snippets:** Use markdown fenced blocks with language tags
- **Cross-references:** Use file paths relative to repo root
- **Severity badges (optional):** \`[HIGH]\`, \`[MEDIUM]\`, \`[LOW]\` only if justified by evidence
\`\`\`
```

---

## What Changed

| Aspect | Before | After |
|--------|--------|-------|
| **Disclaimer** | Absent | Mandatory header: date, scope, provenance transparency |
| **"Valuable insights"** | Undefined (ambiguous) | Scope + evidence sources explicit in requirements |
| **Fact ↔ Inference boundary** | Vague | Three distinct types: Facts (citations), Inferences (logic chains), Speculation (flagged **UNKNOWN**) |
| **Comparative baseline** | "Our codebase" (undefined) | Explicit `<REFERENCE_CODEBASE>` input + scope section |
| **Recommendations** | List (unstructured) | Three types (Adopt/Adapt/Avoid) + evidence chain for each |
| **Evidence standards** | Implicit | Mandatory `<file>:<line-range>` citations; forbidden: unsourced claims |
| **Scope boundaries** | Unclear | Section 6 explicitly lists what was NOT inspected |
| **Hallucination risk** | Unaddressed | **UNKNOWN** marking + confidence levels (High/Medium/Low) per claim |
| **Tone constraints** | Missing | Forbidden list includes flattery, generalizations, pattern-matching without proof |

---

## Why These Changes Matter (Per Your Preferences)

**1. Unbiased over flattering**
- Explicit forbidden list blocks aspirational language ("elegant", "clever")
- Requires "evidence-based reasoning" for every claim

**2. Formalization → research + correct math + provenance**
- Every claim must cite `<file>:<line-range>` or show logical chain
- Inferences must show reasoning path; speculation flagged as **UNKNOWN**
- Confidence levels (High/Medium/Low) prevent false certainty

**3. Avoid hallucination**
- Specification forbids: comparisons you haven't done, "common practice" claims, unsupported dismissals
- Requires explicit scope boundary: "What you did NOT inspect"

**4. Markdown + structure**
- Output is `.md` with standard frontmatter + searchable sections
- Code snippets use fence blocks with language tags

**5. Disclaimer header**
- Required section stating analysis is *static code inspection only*
- Explicitly invites skepticism: "No assertion should be accepted without reviewing cited code"

---

## Integration Notes

Use this as a **system prompt** for codebase analysis agents, or as a **template for human code reviewers** planning a cross-repo audit.

To apply to your use case:
1. Substitute `<TARGET_CODEBASE>` with actual repo path or URL
2. Substitute `<REFERENCE_CODEBASE>` with your standards/target architecture
3. Optionally add language constraints: `--languages typescript,rust` (only analyze these)
4. Timestamp format: ISO 8601 (`2026-04-01T14:30:45Z`)