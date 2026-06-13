---
name: prompt-builder
version: "1.0.0"
description: >
  Guides the design and construction of a valid PromptDocument (prompt-schema.ts v0.3.0) — a
  composable, versionable, schema-conformant prompt artifact. Use whenever the user wants to
  create, design, engineer, or structure a prompt for Claude or similar LLMs, especially for
  tasks involving multi-step pipelines, few-shot examples, chain-of-thought reasoning, extended
  thinking, tool-use loops, RAG/retrieval, self-consistency voting, or evaluation criteria.
  Trigger on phrases like: "create a prompt", "build a prompt", "design a system prompt",
  "engineer a prompt", "write a prompt document", "build a prompt pipeline", "I need a prompt
  that...", "make a prompt for...", "generate a PromptDocument". Also trigger when the user
  describes an LLM task and wants it formalized — even without explicitly saying "prompt".
allowed-tools: Read Write
---

# Prompt Builder

Produces a valid, complete `PromptDocument` conforming to **prompt-schema.ts v0.3.0**.

A `PromptDocument` is a two-layer artifact:
- **Layer 1 (CallSpec)**: defines everything for a single LLM API call — system prompt, user
  template, variables, output format, techniques, prefill, tools, model parameters.
- **Layer 2 (Orchestration)**: coordinates one or more CallSpecs using a named strategy
  (single call, chain, self-consistency, tree-of-thoughts, ReAct, meta-prompt).

See `references/schema-reference.md` for field constraints, validation rules, and examples.

---

## Phase 1 — Interview

Gather enough information before writing anything. Most users won't know schema vocabulary —
translate their answers into schema concepts without requiring them to know the terms.

**Always ask:**
1. What task should this prompt accomplish? (one sentence)
2. What input does the model need? (user-supplied values → `{{variables}}`)
3. What should the output look like? (text, JSON, markdown, code, CSV, or custom)
4. Should the model play a specific role or have domain expertise?

**Ask when unclear:**
5. Is this a single LLM call, or does it need multiple steps with outputs feeding into each other?
6. Should it reason step-by-step before answering? (→ `chain_of_thought`)
7. Are there example input→output pairs to guide the model? (→ `few_shot`)
8. Does it need to use external tools, search, or execute code? (→ `react`)
9. Should it use extended thinking (Claude 3.7+)?

---

## Phase 2 — Select Orchestration Strategy

Pick exactly one strategy based on the user's answers:

| Situation | Strategy |
|-----------|----------|
| Single focused task | `single` |
| Same task, need high-confidence answers (vote across N paths) | `self_consistency` |
| Multi-step pipeline (each step feeds the next) | `chain` |
| Complex problem needing branching exploration | `tree_of_thoughts` |
| Uses external tools in a reasoning loop (Thought → Action → Observation) | `react` |
| Generating or improving prompts programmatically | `meta_prompt` |

For `chain`: identify each step's `id` and `inputFrom` dependencies upfront. The dependency
graph must be a DAG (no cycles, all `inputFrom` IDs must exist in the step list).

---

## Phase 3 — Build the CallSpec

Construct each field in order. Skip optional fields if not needed.

### 3.1 System Prompt

```json
"system": {
  "role": {
    "persona": "Senior security analyst with OSINT expertise",
    "expertise": ["threat intelligence", "OSINT", "incident response"],
    "constraints": ["Do not speculate beyond available evidence", "Flag uncertainty explicitly"],
    "tone": "concise and direct"
  },
  "instructions": "Analyze the provided threat report for indicators of compromise. Classify each IOC by type and severity. Output inside <findings> tags as a JSON array.",
  "xmlTags": [
    { "tag": "report", "purpose": "Wraps the raw threat report text" },
    { "tag": "findings", "purpose": "Contains the structured IOC output" }
  ]
}
```

- `role` is optional but recommended for specialized tasks — it activates relevant knowledge and sets behavioral constraints.
- `xmlTags` documents every XML tag used in `userTemplate`, `prefill`, or output. Listing them helps the model use them consistently.
- `instructions` is the core behavioral contract — be specific about what to do and what to output.

### 3.2 User Template and Variables

```json
"userTemplate": "<report>\n{{reportText}}\n</report>",
"variables": {
  "reportText": {
    "type": "string",
    "description": "The raw threat intelligence report text",
    "required": true
  }
}
```

**Bidirectional constraint (enforced by schema):**
- Every `{{variableName}}` in `userTemplate` must be declared in `variables`.
- Every variable with `"required": true` must appear in `userTemplate`.
- Mismatches fail schema validation — verify both directions before finalizing.

Variable types: `"string"`, `"number"`, `"boolean"`, `"array"`, `"object"`.
Use `"default"` for optional variables with sensible fallbacks.

### 3.3 Output Format

```json
"outputFormat": {
  "type": "json",
  "schema": {
    "type": "array",
    "items": {
      "type": "object",
      "properties": {
        "ioc": { "type": "string" },
        "type": { "type": "string", "enum": ["ip", "domain", "hash", "url"] },
        "severity": { "type": "string", "enum": ["critical", "high", "medium", "low"] }
      },
      "required": ["ioc", "type", "severity"]
    }
  },
  "constraints": ["Return ONLY the JSON array, no preamble or explanation"]
}
```

- `schema` is only meaningful when `type` is `"json"`. For other types, use `constraints` to describe format rules.
- `constraints` are additional format rules that don't fit in a JSON Schema (e.g., word limits, header requirements, language).

Output types: `"text"`, `"json"`, `"xml"`, `"markdown"`, `"csv"`, `"code"`, `"custom"`.

### 3.4 Techniques

Apply zero or more. They compose — `few_shot` and `chain_of_thought` can be used together.

```json
"techniques": [
  {
    "technique": "few_shot",
    "examples": [
      {
        "input": "Alert: connection to 45.33.32.156 on port 4444",
        "output": "[{\"ioc\": \"45.33.32.156\", \"type\": \"ip\", \"severity\": \"high\"}]",
        "label": "single-ip-ioc"
      }
    ],
    "includeEdgeCases": true
  },
  {
    "technique": "chain_of_thought",
    "variant": "zero_shot",
    "thinkingTag": "analysis"
  }
]
```

**Technique options:**
- `zero_shot`: no examples, no trigger phrase — pure instruction following.
- `few_shot`: provide `examples` (at least one). These take precedence over top-level `examples`.
  - For CoT exemplars, add a `"reasoning"` field to each example.
- `chain_of_thought`:
  - `variant: "zero_shot"` — appends a trigger phrase (default: "Let's think step by step").
  - `variant: "few_shot"` — provide CoT exemplars (examples with `reasoning`).
  - `thinkingTag` — encloses intermediate reasoning in `<tagname>...</tagname>`.
  - `triggerPhrase` — override the default trigger phrase.

### 3.5 Prefill (Optional)

Pre-seeds the assistant's first token. Use to guide output format:

```json
"prefill": "<analysis>\n"
```

- `"{"` → forces JSON object start.
- `"["` → forces JSON array start.
- `"<tagname>\n"` → opens an XML section.
- Pair with `thinkingTag` or `xmlTags` when using structured output.

### 3.6 Model Parameters (Optional)

```json
"modelParams": {
  "model": "claude-opus-4-6",
  "temperature": 0.2,
  "maxTokens": 4096,
  "thinking": { "type": "enabled", "budgetTokens": 8192 }
}
```

- `thinking.budgetTokens` minimum is **1024** (API contract). Use `{ "type": "disabled" }` to explicitly turn off.
- `temperature`: 0.0–2.0. Lower for deterministic tasks (extraction, classification); higher for creative tasks.
- Omit `modelParams` entirely if defaults are acceptable.

---

## Phase 4 — Orchestration Wrappers

### single (most common)
```json
"orchestration": {
  "strategy": "single",
  "call": { /* CallSpec */ }
}
```

### self_consistency
```json
"orchestration": {
  "strategy": "self_consistency",
  "call": { /* CallSpec */ },
  "numPaths": 5,
  "selectionStrategy": "majority_vote",
  "temperature": 0.7
}
```
Generates N independent paths and reduces to a final answer. Use when accuracy is critical.
`selectionStrategy`: `"majority_vote"` (default), `"weighted"`, or `"best_of_n"`.

### chain
```json
"orchestration": {
  "strategy": "chain",
  "steps": [
    {
      "id": "extract",
      "description": "Extract raw claims from the document",
      "orchestration": { "strategy": "single", "call": { /* CallSpec */ } }
    },
    {
      "id": "synthesize",
      "description": "Synthesize extracted claims into a report",
      "inputFrom": ["extract"],
      "orchestration": { "strategy": "single", "call": { /* CallSpec */ } }
    }
  ]
}
```
- `steps` minimum: 2.
- `id` values must be unique within the chain.
- `inputFrom`: list of step IDs whose output feeds this step — must reference existing IDs.
- The dependency graph must be a DAG. Cycles fail validation.
- Each step's orchestration can itself be any strategy (recursive composition).

### react
```json
"orchestration": {
  "strategy": "react",
  "call": { /* CallSpec */ },
  "tools": [
    {
      "name": "web_search",
      "description": "Search the web for current information",
      "inputSchema": {
        "type": "object",
        "properties": { "query": { "type": "string" } },
        "required": ["query"]
      },
      "when": "When the task requires real-time or external information"
    }
  ],
  "maxIterations": 10,
  "observationFormat": "Observation: {result}"
}
```

### tree_of_thoughts
```json
"orchestration": {
  "strategy": "tree_of_thoughts",
  "nodeCall": { /* CallSpec for generating branches */ },
  "evaluatorCall": { /* CallSpec for ranking branches, optional */ },
  "searchAlgorithm": "beam",
  "maxBranches": 3,
  "maxDepth": 4
}
```
`searchAlgorithm`: `"bfs"`, `"dfs"`, or `"beam"`.

---

## Phase 5 — Top-Level Document Assembly

```json
{
  "schemaVersion": "0.3.0",
  "id": "kebab-case-unique-slug",
  "name": "Human Readable Name",
  "version": "1.0.0",
  "description": "One sentence: what this prompt does and when to use it.",
  "tags": ["domain", "task-type"],
  "orchestration": { /* ... */ },
  "context": { /* optional — see Phase 6 */ },
  "evaluation": { /* optional — see Phase 7 */ },
  "metadata": {
    "author": "author-identifier",
    "createdAt": "YYYY-MM-DD",
    "changelog": [
      { "version": "1.0.0", "date": "YYYY-MM-DD", "changes": "Initial version" }
    ]
  }
}
```

- `schemaVersion` must be exactly `"0.3.0"`.
- `version` must be valid semver (e.g., `"1.0.0"`, `"2.1.3-beta.1"`).
- `id` is a stable unique identifier — use a descriptive kebab-case slug.

---

## Phase 6 — Context Engineering (Optional)

Add `context` when the prompt needs external information, memory, or shared tools.

```json
"context": {
  "retrieval": [
    {
      "source": "vector_store",
      "query": "{{userQuery}}",
      "topK": 5,
      "maxTokens": 4000
    }
  ],
  "memory": {
    "shortTerm": {
      "maxTurns": 20,
      "compaction": {
        "enabled": true,
        "strategy": "summarize",
        "triggerTokens": 80000
      }
    },
    "longTerm": {
      "enabled": true,
      "store": "redis",
      "retrievalQuery": "{{sessionContext}}"
    }
  },
  "injectedDocuments": [
    {
      "id": "system-kb",
      "content": "Static reference content here...",
      "metadata": { "source": "internal-wiki" }
    }
  ],
  "tokenBudget": {
    "total": 100000,
    "instructions": 5000,
    "context": 75000,
    "output": 20000
  }
}
```

**Token budget constraint:** If `total` and all three sub-budgets are specified, `instructions + context + output` must not exceed `total`.

Memory compaction strategies: `"summarize"`, `"trim_oldest"`, `"sliding_window"`, `"clear_tool_results"`.

---

## Phase 7 — Evaluation Criteria (Optional)

Add `evaluation` to define quality metrics for the prompt's output:

```json
"evaluation": {
  "criteria": [
    { "name": "precision", "description": "Flagged items are genuine findings", "weight": 0.4 },
    { "name": "recall",    "description": "No critical items are missed",       "weight": 0.4 },
    { "name": "format",    "description": "Output matches the required schema",  "weight": 0.2 }
  ],
  "goldenOutputs": [
    "[{\"ioc\": \"45.33.32.156\", ...}]"
  ]
}
```

**Weight constraint:** If ALL criteria specify `weight`, they must sum to **1.0 ± 0.01**. Partial weighting (some criteria without weights) is always valid — no sum check applies.

---

## Validation Checklist

Before delivering the final JSON, verify every item:

- [ ] `schemaVersion` is `"0.3.0"`
- [ ] `version` is valid semver
- [ ] `id` is kebab-case and unique
- [ ] Every `{{var}}` in `userTemplate` is declared in `variables`
- [ ] Every `required: true` variable appears in `userTemplate`
- [ ] `thinking: enabled` has `budgetTokens >= 1024`
- [ ] Chain: all step `id` values are unique
- [ ] Chain: all `inputFrom` values reference existing step IDs
- [ ] Chain: dependency graph is acyclic (no cycles)
- [ ] Evaluation weights: if all criteria specify weights, sum ≈ 1.0 (±0.01)
- [ ] Token budget: if all sub-budgets set, `instructions + context + output ≤ total`
- [ ] `outputFormat.schema` only used when `type` is `"json"`

---

## Delivery Format

Output:

1. **The complete `PromptDocument`** as a fenced JSON code block.
2. **Design rationale** (3–5 bullet points): key choices made — strategy selection, technique stack, variable design, any non-obvious decisions.
3. **Usage note**: what values the caller must supply for each `required` variable, and what the output will look like.
