# Prompt Schema Reference (v0.3.0)

Quick reference for field constraints, types, and validation rules.
Source: `.repo/schemas/01KM1YWRFYBBT98WV14WXDKJM4-prompt-schema.ts`.

---

## Schema Version

```ts
schemaVersion: "0.3.0"   // exact literal — any other value fails
```

---

## PromptDocument (top-level)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `schemaVersion` | `"0.3.0"` | ✅ | Literal — must match exactly |
| `id` | `string` | ✅ | Unique identifier (slug recommended) |
| `name` | `string` | ✅ | Human-readable name |
| `version` | `string` | ✅ | Semver: `major.minor.patch[-pre][+build]` |
| `description` | `string` | — | What this prompt does |
| `tags` | `string[]` | — | Categorization tags |
| `orchestration` | `Orchestration` | ✅ | Strategy + CallSpec(s) |
| `context` | `ContextConfig` | — | RAG, memory, token budgets |
| `evaluation` | `Evaluation` | — | Quality criteria |
| `metadata` | `object` | — | Author, dates, changelog |

---

## Orchestration Strategies

### `single`
```ts
{ strategy: "single", call: CallSpec }
```

### `self_consistency`
```ts
{
  strategy: "self_consistency",
  call: CallSpec,
  numPaths: number,           // int ≥ 2
  selectionStrategy?: "majority_vote" | "weighted" | "best_of_n",
  temperature?: number        // 0–2
}
```

### `chain`
```ts
{
  strategy: "chain",
  steps: ChainStep[]          // min: 2
}

ChainStep = {
  id: string,                 // unique within chain
  description?: string,
  inputFrom?: string[],       // must reference existing step IDs
  validation?: string,
  orchestration: Orchestration  // recursive — any strategy
}
```
**Validations:** step IDs unique · `inputFrom` refs exist · DAG (no cycles)

### `tree_of_thoughts`
```ts
{
  strategy: "tree_of_thoughts",
  nodeCall: CallSpec,
  evaluatorCall?: CallSpec,
  searchAlgorithm: "bfs" | "dfs" | "beam",
  maxBranches?: number,       // int ≥ 1
  maxDepth?: number           // int ≥ 1
}
```

### `react`
```ts
{
  strategy: "react",
  call: CallSpec,
  tools: ToolDefinition[],    // min: 1
  maxIterations?: number,     // int ≥ 1
  observationFormat?: string  // e.g., "Observation: {result}"
}
```

### `meta_prompt`
```ts
{
  strategy: "meta_prompt",
  generatorCall: CallSpec,
  objective: string,
  sourcePromptId?: string,
  targetType?: "call.iande" | "prompt_document"
}
```

---

## CallSpec

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `system` | `object` | ✅ | System prompt config |
| `system.instructions` | `string` | ✅ | Primary task description |
| `system.role` | `Role` | — | Persona + expertise |
| `system.xmlTags` | `{ tag, purpose }[]` | — | Semantic tags used |
| `userTemplate` | `string` | ✅ | Supports `{{variable}}` interpolation |
| `variables` | `Record<string, VarDef>` | — | Variable declarations |
| `outputFormat` | `OutputFormat` | — | Format type + schema + constraints |
| `examples` | `Example[]` | — | Shared few-shot pool |
| `techniques` | `PromptTechnique[]` | — | zero_shot, few_shot, chain_of_thought |
| `prefill` | `string` | — | Pre-seeded assistant response start |
| `tools` | `ToolDefinition[]` | — | Tools for this call |
| `modelParams` | `ModelParams` | — | Model + inference parameters |

**Bidirectional variable cross-check (enforced):**
- Forward: every `{{var}}` in `userTemplate` must exist in `variables`
- Reverse: every `required: true` variable must appear in `userTemplate`

---

## Role

```ts
{
  persona: string,              // "Who the model is"
  expertise?: string[],         // Domains to activate
  constraints?: string[],       // Behavioral limits
  tone?: string                 // Communication style
}
```

---

## Variable Definition

```ts
{
  type: "string" | "number" | "boolean" | "array" | "object",
  description?: string,
  required?: boolean,
  default?: unknown
}
```

---

## OutputFormat

```ts
{
  type: "text" | "json" | "xml" | "markdown" | "csv" | "code" | "custom",
  schema?: Record<string, unknown>,   // JSON Schema — only for type "json"
  constraints?: string[]              // Additional format rules
}
```
`schema` must have a top-level `type` or `properties` field when present.

---

## Prompt Techniques

### zero_shot
```ts
{ technique: "zero_shot" }
```

### few_shot
```ts
{
  technique: "few_shot",
  examples: Example[],         // min: 1
  includeEdgeCases?: boolean
}
```
Technique-scoped examples take precedence over top-level `CallSpec.examples`.

### chain_of_thought
```ts
{
  technique: "chain_of_thought",
  variant: "zero_shot" | "few_shot",
  triggerPhrase?: string,      // Default: "Let's think step by step"
  thinkingTag?: string         // XML tag for reasoning (e.g., "thinking")
}
```

---

## Example

```ts
{
  input: string,
  output: string,
  reasoning?: string,   // Makes this a CoT exemplar
  label?: string        // Human-readable tag
}
```

---

## ModelParams

```ts
{
  model?: string,               // e.g., "claude-opus-4-6"
  temperature?: number,         // 0–2
  topP?: number,                // 0–1
  topK?: number,                // int ≥ 1
  maxTokens?: number,           // int ≥ 1
  stopSequences?: string[],
  thinking?: ThinkingConfig
}
```

### ThinkingConfig
```ts
{ type: "disabled" }
// or
{ type: "enabled", budgetTokens: number }  // budgetTokens: int ≥ 1024
```

---

## ToolDefinition

```ts
{
  name: string,
  description: string,
  inputSchema?: Record<string, unknown>,  // JSON Schema for input params
  when?: string                           // Guidance on when to use this tool
}
```

---

## ContextConfig

```ts
{
  retrieval?: RetrievalSource[],
  memory?: MemoryConfig,
  tools?: ToolDefinition[],       // Shared pool; call-level tools take precedence
  injectedDocuments?: { id, content, metadata? }[],
  tokenBudget?: TokenBudget
}
```

### TokenBudget constraint
If `total` and all sub-budgets (`instructions`, `context`, `output`) are set:
```
instructions + context + output ≤ total
```

### RetrievalSource
```ts
{
  source: string,         // e.g., "vector_store", "web_search"
  query?: string,
  topK?: number,
  filter?: Record<string, unknown>,
  maxTokens?: number
}
```

### MemoryConfig
```ts
{
  shortTerm?: {
    maxTurns?: number,
    compaction?: {
      enabled: boolean,
      strategy?: "summarize" | "trim_oldest" | "sliding_window" | "clear_tool_results",
      triggerTokens?: number
    }
  },
  longTerm?: {
    enabled: boolean,
    store?: string,           // e.g., "redis", "sqlite", "anthropic_memory"
    retrievalQuery?: string
  }
}
```

---

## Evaluation

```ts
{
  criteria: {
    name: string,
    description: string,
    weight?: number       // 0–1
  }[],
  goldenOutputs?: string[]
}
```

**Weight constraint:** If ALL criteria specify `weight`, they must sum to **1.0 ± 0.01**.
Partial weighting (some criteria missing weights) has no sum constraint.

---

## Metadata

```ts
{
  author?: string,
  createdAt?: string,       // ISO date: YYYY-MM-DD
  updatedAt?: string,       // ISO date: YYYY-MM-DD
  changelog?: {
    version: string,        // semver
    date: string,           // ISO date: YYYY-MM-DD
    changes: string
  }[]
}
```

---

## Semver Pattern

Valid: `"1.0.0"`, `"2.1.3"`, `"1.0.0-beta.1"`, `"1.0.0+build.42"`
Regex: `/^\d+\.\d+\.\d+(-[\w.]+)?(\+[\w.]+)?$/`

---

## Key Cross-Field Rules (summary)

| Rule | Where |
|------|-------|
| `{{var}}` in `userTemplate` → must be in `variables` | CallSpec |
| `required: true` variable → must appear in `userTemplate` | CallSpec |
| Chain step `id` values → unique | chain strategy |
| Chain `inputFrom` values → must match existing step IDs | chain strategy |
| Chain dependency graph → must be a DAG (no cycles) | chain strategy |
| `thinking: enabled` → `budgetTokens ≥ 1024` | ModelParams |
| All evaluation weights present → sum ≈ 1.0 (±0.01) | Evaluation |
| Token budget: all sub-budgets set → sum ≤ total | ContextConfig |
| `outputFormat.schema` → only valid when `type: "json"` | OutputFormat |
