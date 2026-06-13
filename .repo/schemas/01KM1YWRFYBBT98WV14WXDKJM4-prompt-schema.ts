// ─────────────────────────────────────────────
// Prompt Schema
// ─────────────────────────────────────────────
//
// Versioned, composable prompt schema (Zod v4) with two layers:
// Layer 1 (CallSpec) defines a single API call; Layer 2
// (Orchestration) coordinates multiple calls via a recursive
// discriminated union.
//
// Design proposal — not battle-tested. Validate against your
// own use case. See docs/prompt-schema.md for architecture,
// references, and migration guide.

import * as z from "zod/v4";

// ── § 0  Schema Version — version literal and metadata ──

/** Current schema version literal. */
export const SCHEMA_VERSION = "0.3.0" as const;

/** Validate that the schema version matches the current release. */
export const SchemaVersionSchema = z.literal(SCHEMA_VERSION);

// ── § 0.1  Shared Regex — reusable validation patterns ──

/** Semver regex (major.minor.patch with optional pre-release and build metadata). */
const SEMVER_RE = /^\d+\.\d+\.\d+(-[\w.]+)?(\+[\w.]+)?$/;

/** Matches {{variableName}} template interpolation slots. */
const TEMPLATE_VAR_RE = /\{\{(\w+)\}\}/g;

// ── § 0.2  Validation Helpers — internal refinement utilities ──

/** Extract all {{variableName}} references from a template string into a Set. */
function extractTemplateVars(template: string): Set<string> {
  const vars = new Set<string>();
  const re = new RegExp(TEMPLATE_VAR_RE.source, "g");
  let match: RegExpExecArray | null;
  while ((match = re.exec(template)) !== null) {
    vars.add(match[1]);
  }
  return vars;
}

/** Detect a cycle in a directed graph, returning the cycle path or null. */
function findCycle(
  nodes: string[],
  edges: Map<string, string[]>,
): string[] | null {
  const WHITE = 0, GRAY = 1, BLACK = 2;
  const color = new Map<string, number>(nodes.map((n) => [n, WHITE]));
  const parent = new Map<string, string | null>();

  for (const node of nodes) {
    if (color.get(node) !== WHITE) continue;
    const stack: string[] = [node];

    while (stack.length > 0) {
      const u = stack[stack.length - 1];
      if (color.get(u) === WHITE) {
        color.set(u, GRAY);
        for (const v of edges.get(u) ?? []) {
          if (color.get(v) === GRAY) {
            // Back edge → cycle. Reconstruct it.
            const cycle = [v, u];
            let cur = u;
            while (cur !== v) {
              cur = parent.get(cur)!;
              if (cur == null) break;
              cycle.push(cur);
            }
            return cycle.reverse();
          }
          if (color.get(v) === WHITE) {
            parent.set(v, u);
            stack.push(v);
          }
        }
      } else {
        color.set(u, BLACK);
        stack.pop();
      }
    }
  }
  return null;
}

// ── § 1  Primitives — shared atoms reused across layers ──

/** Semantic role the model should adopt. */
export const RoleSchema = z.object({
  persona: z.string().meta({
    description: "Who the model is (e.g. 'Senior security analyst')",
  }),
  expertise: z.array(z.string()).optional().meta({
    description: "Domains of knowledge to activate",
  }),
  constraints: z.array(z.string()).optional().meta({
    description: "Behavioral limits (e.g. 'Do not speculate')",
  }),
  tone: z.string().optional().meta({
    description: "Communication style (e.g. 'concise and technical')",
  }),
});

/** A single input→output example for few-shot prompting. */
export const ExampleSchema = z.object({
  input: z.string(),
  output: z.string(),
  reasoning: z.string().optional().meta({
    description:
      "Intermediate reasoning trace (makes this a CoT exemplar)",
  }),
  label: z.string().optional().meta({
    description: "Human-readable tag for this example",
  }),
});

/** Validate output format type, optional JSON Schema, and constraints. */
export const OutputFormatSchema = z.object({
  type: z.enum(["text", "json", "xml", "markdown", "csv", "code", "custom"]),
  schema: z
    .record(z.string(), z.unknown())
    .refine(
      (s) => typeof s.type === "string" || typeof s.properties === "object",
      {
        message:
          "Output schema must include a top-level 'type' or 'properties' field",
      },
    )
    .optional()
    .meta({
      description:
        "JSON Schema or equivalent structure definition for the output",
    }),
  constraints: z.array(z.string()).optional().meta({
    description:
      "Additional format rules (e.g. 'max 200 words', 'include headers')",
  }),
});

/**
 * Extended thinking configuration, discriminated on `type`.
 *
 * @remarks
 * `"disabled"` omits the thinking parameter; `"enabled"` requires
 * `budgetTokens` (Anthropic API contract). The runtime translates
 * this to the provider-specific API format.
 */
export const ThinkingConfigSchema = z.discriminatedUnion("type", [
  z.object({
    type: z.literal("disabled"),
  }),
  z.object({
    type: z.literal("enabled"),
    budgetTokens: z.number().int().min(1024).meta({
      description:
        "Token budget for extended thinking. Required by the Anthropic API " +
        "when thinking is enabled. Minimum 1024.",
    }),
  }),
]);

/** Model-level inference parameters for a single API call. */
export const ModelParamsSchema = z.object({
  model: z.string().optional().meta({
    description: "Model identifier (e.g. 'claude-opus-4-6')",
  }),
  temperature: z.number().min(0).max(2).optional(),
  topP: z.number().min(0).max(1).optional(),
  topK: z.number().int().min(1).optional(),
  maxTokens: z.number().int().min(1).optional(),
  stopSequences: z.array(z.string()).optional(),
  thinking: ThinkingConfigSchema.optional().meta({
    description: "Extended thinking / reasoning mode (Claude 3.7+)",
  }),
});

// ── § 1.1  Tool Definition — canonical tool shape for all layers ──

/**
 * Canonical tool definition used across all schema layers.
 *
 * @remarks
 * Shared by {@link CallSpecSchema} and {@link OrchestrationSchema}.
 * When both declare tools, orchestration-level tools take precedence;
 * call-level tools pass through to the API's `tools` parameter.
 */
export const ToolDefinitionSchema = z.object({
  name: z.string(),
  description: z.string(),
  inputSchema: z.record(z.string(), z.unknown()).optional().meta({
    description: "JSON Schema describing the tool's input parameters",
  }),
  when: z.string().optional().meta({
    description: "Guidance on when to use this tool",
  }),
});

// ── § 2  Prompt Techniques — single-call reasoning strategies ──

/** Valid prompt-level technique discriminator values. */
export const PROMPT_TECHNIQUE_NAMES = [
  "zero_shot",
  "few_shot",
  "chain_of_thought",
] as const;

/** Union type of valid prompt-level technique names. */
export type PromptTechniqueName = (typeof PROMPT_TECHNIQUE_NAMES)[number];

/** Validate a string as a prompt-level technique name. */
export const PromptTechniqueNameSchema = z.enum(PROMPT_TECHNIQUE_NAMES);

/** Zero-shot: instruction only, no examples. */
export const ZeroShotSchema = z.object({
  technique: z.literal("zero_shot"),
});

/** Few-shot: provide input/output examples. */
export const FewShotSchema = z.object({
  technique: z.literal("few_shot"),
  examples: z.array(ExampleSchema).min(1).meta({
    description:
      "Technique-scoped examples. When present, these are the canonical " +
      "examples for this technique. Top-level `examples` on CallSpec " +
      "serves as a shared pool; technique-scoped examples take precedence.",
  }),
  includeEdgeCases: z.boolean().optional().meta({
    description: "Whether the example set intentionally covers edge cases",
  }),
});

/** Chain-of-Thought: elicit step-by-step reasoning. */
export const ChainOfThoughtSchema = z.object({
  technique: z.literal("chain_of_thought"),
  variant: z.enum(["zero_shot", "few_shot"]).meta({
    description:
      "'zero_shot' = append trigger phrase; 'few_shot' = provide CoT exemplars",
  }),
  triggerPhrase: z.string().optional().meta({
    description: "Custom CoT trigger (default: 'Let\\'s think step by step')",
  }),
  thinkingTag: z.string().optional().meta({
    description: "XML tag to contain reasoning (e.g. 'thinking')",
  }),
});

/** Discriminated union of prompt-level technique variants. */
export const PromptTechniqueSchema = z.discriminatedUnion("technique", [
  ZeroShotSchema,
  FewShotSchema,
  ChainOfThoughtSchema,
]);

// ── § 3  CallSpec — Layer 1: content of a single API call ──

/**
 * Define everything that goes into a single API call.
 *
 * @remarks
 * Compilation target: given a CallSpec and variable bindings, a runtime
 * deterministically produces an Anthropic Messages API request body.
 * A bidirectional refinement ensures every `{{var}}` in `userTemplate`
 * is declared, and every required variable is referenced.
 * See docs/prompt-schema.md for full compilation semantics.
 */
export const CallSpecSchema = z
  .object({
    /** System-level instructions (role, behavior, rules). */
    system: z
      .object({
        role: RoleSchema.optional(),
        instructions: z.string().meta({
          description: "Primary task description and behavioral rules",
        }),
        xmlTags: z
          .array(
            z.object({
              tag: z.string(),
              purpose: z.string(),
            }),
          )
          .optional()
          .meta({ description: "Semantic XML tags used in this prompt" }),
      })
      .meta({ description: "System prompt configuration" }),

    /** User message template. Supports {{variable}} interpolation. */
    userTemplate: z.string().meta({
      description:
        "User message template; use {{variableName}} for interpolation slots",
    }),

    /** Declared template variables with types and descriptions. */
    variables: z
      .record(
        z.string(),
        z.object({
          type: z.enum(["string", "number", "boolean", "array", "object"]),
          description: z.string().optional(),
          required: z.boolean().optional(),
          default: z.unknown().optional(),
        }),
      )
      .optional(),

    /** Output format specification. */
    outputFormat: OutputFormatSchema.optional(),

    /**
     * Shared few-shot examples pool.
     * Technique-scoped examples (inside a `few_shot` technique entry)
     * take precedence over these when both are present.
     */
    examples: z.array(ExampleSchema).optional(),

    /**
     * Prompt-level techniques applied to this call.
     * Only prompt-level techniques are valid here — orchestration
     * strategies belong in the OrchestrationSchema wrapper.
     */
    techniques: z.array(PromptTechniqueSchema).optional(),

    /** Partial assistant response pre-seeded before generation. */
    prefill: z.string().optional().meta({
      description:
        "Partial response to pre-seed the assistant's output " +
        "(e.g. '{' for JSON, '<analysis>\\n' for XML)",
    }),

    /** Tools passed to the API's `tools` parameter for this call. */
    tools: z.array(ToolDefinitionSchema).optional(),

    /** Recommended model and inference parameters. */
    modelParams: ModelParamsSchema.optional(),
  })
  .refine(
    // Bidirectional variable cross-check
    (spec) => {
      if (spec.variables == null) return true;
      const declared = new Set(Object.keys(spec.variables));
      const referenced = extractTemplateVars(spec.userTemplate);

      // Forward: every referenced var must be declared
      for (const ref of referenced) {
        if (!declared.has(ref)) return false;
      }

      // Reverse: every required declared var must be referenced
      for (const [name, def] of Object.entries(spec.variables)) {
        if (def.required && !referenced.has(name)) return false;
      }

      return true;
    },
    {
      message:
        "Variable cross-check failed. Forward: every {{var}} in userTemplate " +
        "must be declared in `variables`. Reverse: every required variable " +
        "must be referenced in userTemplate.",
    },
  );

// ── § 4  Context Engineering — retrieval, memory, and token budgets ──

/** Validate a single RAG / retrieval source configuration. */
export const RetrievalSchema = z.object({
  source: z.string().meta({
    description:
      "Retrieval source identifier (e.g. 'vector_store', 'web_search')",
  }),
  query: z.string().optional(),
  topK: z.number().int().min(1).optional(),
  filter: z.record(z.string(), z.unknown()).optional(),
  maxTokens: z.number().int().optional().meta({
    description: "Token budget allocated to retrieved content",
  }),
});

/** Validate short-term and long-term memory configuration. */
export const MemorySchema = z.object({
  shortTerm: z
    .object({
      maxTurns: z.number().int().optional(),
      compaction: z
        .object({
          enabled: z.boolean(),
          strategy: z
            .enum([
              "summarize",
              "trim_oldest",
              "sliding_window",
              "clear_tool_results",
            ])
            .optional(),
          triggerTokens: z.number().int().optional().meta({
            description: "Token count at which compaction is triggered",
          }),
        })
        .optional(),
    })
    .optional(),
  longTerm: z
    .object({
      enabled: z.boolean(),
      store: z.string().optional().meta({
        description:
          "Backing store (e.g. 'redis', 'sqlite', 'anthropic_memory')",
      }),
      retrievalQuery: z.string().optional(),
    })
    .optional(),
});

/**
 * Validate full context engineering configuration.
 *
 * @remarks
 * Token budget refinement ensures the sum of sub-budgets does not
 * exceed the total when all are specified.
 */
export const ContextConfigSchema = z.object({
  retrieval: z.array(RetrievalSchema).optional(),
  memory: MemorySchema.optional(),
  tools: z.array(ToolDefinitionSchema).optional().meta({
    description:
      "Shared tool pool for the entire prompt document. Individual " +
      "CallSpecs and orchestration strategies may declare their own tools, " +
      "which take precedence over this shared pool.",
  }),
  injectedDocuments: z
    .array(
      z.object({
        id: z.string(),
        content: z.string(),
        metadata: z.record(z.string(), z.unknown()).optional(),
      }),
    )
    .optional()
    .meta({ description: "Static documents pre-loaded into context" }),
  tokenBudget: z
    .object({
      total: z.number().int().optional(),
      instructions: z.number().int().optional(),
      context: z.number().int().optional(),
      output: z.number().int().optional(),
    })
    .refine(
      (b) => {
        if (b.total == null) return true;
        const sum =
          (b.instructions ?? 0) + (b.context ?? 0) + (b.output ?? 0);
        if (sum === 0) return true;
        return sum <= b.total;
      },
      {
        message:
          "Sum of instructions + context + output token budgets must not exceed total",
      },
    )
    .optional()
    .meta({
      description: "Advisory token allocation across context sections",
    }),
});

// ── § 5  Orchestration — Layer 2: multi-call coordination strategies ──

/** Named stage in a sequential/DAG pipeline. */
const ChainStepSchema = z.object({
  id: z.string().meta({
    description: "Unique step identifier within this chain",
  }),
  description: z.string().optional().meta({
    description: "Human-readable description of what this step does",
  }),
  inputFrom: z.array(z.string()).optional().meta({
    description: "IDs of prior steps whose output feeds this step's env",
  }),
  validation: z.string().optional().meta({
    description: "Validation rule to check before passing output forward",
  }),
  /** Orchestration to execute at this step (recursive via `z.lazy()`). */
  orchestration: z.lazy(() => OrchestrationSchema),
});

/**
 * Discriminated union of multi-call coordination strategies.
 *
 * @remarks
 * Recursive via `z.lazy()`: a chain step's orchestration field is
 * itself an OrchestrationSchema, enabling arbitrary nesting.
 * Each variant wraps one or more {@link CallSpecSchema} instances.
 * See docs/prompt-schema.md for execution semantics per strategy.
 */
export const OrchestrationSchema: z.ZodType<Orchestration> =
  z.discriminatedUnion("strategy", [
    /** Direct execution: compile and execute a single CallSpec. */
    z.object({
      strategy: z.literal("single"),
      call: CallSpecSchema,
    }),

    /** Generate N independent reasoning paths and reduce to a final answer [Wang et al. 2022]. */
    z.object({
      strategy: z.literal("self_consistency"),
      call: CallSpecSchema,
      numPaths: z.number().int().min(2).meta({
        description: "Number of independent reasoning paths to generate",
      }),
      selectionStrategy: z
        .enum(["majority_vote", "weighted", "best_of_n"])
        .optional()
        .meta({
          description:
            "How to select the final answer from N paths (default: majority_vote)",
        }),
      temperature: z.number().min(0).max(2).optional().meta({
        description: "Temperature override for diverse path generation",
      }),
    }),

    /** Branching search over reasoning paths with self-evaluation [Yao et al. 2023]. */
    z.object({
      strategy: z.literal("tree_of_thoughts"),
      nodeCall: CallSpecSchema.meta({
        description: "Prompt used to generate thought branches at each node",
      }),
      evaluatorCall: CallSpecSchema.optional().meta({
        description:
          "Prompt used to evaluate/rank branches. If omitted, " +
          "the runtime must provide a default evaluation mechanism.",
      }),
      searchAlgorithm: z.enum(["bfs", "dfs", "beam"]),
      maxBranches: z.number().int().min(1).optional(),
      maxDepth: z.number().int().min(1).optional(),
    }),

    /** Sequential or DAG-structured pipeline of recursive orchestration steps. */
    z
      .object({
        strategy: z.literal("chain"),
        steps: z.array(ChainStepSchema).min(2),
      })
      .refine(
        // Validate: step IDs must be unique
        (chain) => {
          const ids = chain.steps.map((s) => s.id);
          return new Set(ids).size === ids.length;
        },
        { message: "Chain step IDs must be unique" },
      )
      .refine(
        // Validate: inputFrom must reference existing step IDs
        (chain) => {
          const ids = new Set(chain.steps.map((s) => s.id));
          return chain.steps.every((step) =>
            (step.inputFrom ?? []).every((ref) => ids.has(ref)),
          );
        },
        {
          message:
            "Every inputFrom reference must correspond to a step ID in the same chain",
        },
      )
      .refine(
        // Validate: the dependency graph must be acyclic (DAG)
        (chain) => {
          const nodes = chain.steps.map((s) => s.id);
          const edges = new Map<string, string[]>(
            chain.steps.map((s) => [s.id, s.inputFrom ?? []]),
          );
          return findCycle(nodes, edges) === null;
        },
        {
          message:
            "Chain step dependencies contain a cycle. The dependency graph must be a DAG.",
        },
      ),

    /** Interleaved reasoning and tool-use action loop [Yao et al. 2022]. */
    z.object({
      strategy: z.literal("react"),
      call: CallSpecSchema,
      tools: z.array(ToolDefinitionSchema).min(1).meta({
        description: "Tools available to the ReAct loop",
      }),
      maxIterations: z.number().int().min(1).optional().meta({
        description: "Maximum reasoning-action cycles before termination",
      }),
      observationFormat: z.string().optional().meta({
        description:
          "Template for how tool results are fed back (e.g. 'Observation: {result}')",
      }),
    }),

    /** Generate or refine a prompt via a meta-level call. */
    z.object({
      strategy: z.literal("meta_prompt"),
      generatorCall: CallSpecSchema.meta({
        description: "The call that generates/improves a prompt",
      }),
      objective: z.string().meta({
        description: "What the generated/improved prompt should accomplish",
      }),
      sourcePromptId: z.string().optional().meta({
        description:
          "ID of an existing PromptDocument to improve (if refining)",
      }),
      targetType: z
        .enum(["call.iande", "prompt_document"])
        .optional()
        .meta({
          description:
            "Expected output type of the generator (default: call.iande)",
        }),
    }),
  ]);

// ── § 5.1  Orchestration Type — manual recursive type for z.lazy() ──

// Zod cannot infer recursive types with z.lazy(); defined manually.

interface ChainStep {
  id: string;
  description?: string;
  inputFrom?: string[];
  validation?: string;
  orchestration: Orchestration;
}

/** Recursive orchestration strategy union, defined manually for `z.lazy()` compatibility. */
export type Orchestration =
  | { strategy: "single"; call: CallSpec }
  | {
      strategy: "self_consistency";
      call: CallSpec;
      numPaths: number;
      selectionStrategy?: "majority_vote" | "weighted" | "best_of_n";
      temperature?: number;
    }
  | {
      strategy: "tree_of_thoughts";
      nodeCall: CallSpec;
      evaluatorCall?: CallSpec;
      searchAlgorithm: "bfs" | "dfs" | "beam";
      maxBranches?: number;
      maxDepth?: number;
    }
  | {
      strategy: "chain";
      steps: ChainStep[];
    }
  | {
      strategy: "react";
      call: CallSpec;
      tools: ToolDefinition[];
      maxIterations?: number;
      observationFormat?: string;
    }
  | {
      strategy: "meta_prompt";
      generatorCall: CallSpec;
      objective: string;
      sourcePromptId?: string;
      targetType?: "call.iande" | "prompt_document";
    };

// ── § 6  Evaluation — criteria and reference outputs for quality scoring ──

/**
 * Validate evaluation criteria and optional reference outputs.
 *
 * @remarks
 * Weights are relative (normalized by the consumer). When all
 * criteria specify weights, they must sum to ~1.0 (±0.01).
 * Partial weighting (some criteria without weights) is valid.
 */
export const EvaluationSchema = z
  .object({
    criteria: z.array(
      z.object({
        name: z.string(),
        description: z.string(),
        weight: z.number().min(0).max(1).optional(),
      }),
    ),
    goldenOutputs: z.array(z.string()).optional().meta({
      description: "Reference outputs for automated comparison",
    }),
  })
  .refine(
    (ev) => {
      const weights = ev.criteria
        .map((c) => c.weight)
        .filter((w): w is number => w != null);

      // Only validate sum if ALL criteria have weights
      if (weights.length !== ev.criteria.length) return true;
      if (weights.length === 0) return true;

      const sum = weights.reduce((a, b) => a + b, 0);
      return Math.abs(sum - 1.0) <= 0.01;
    },
    {
      message:
        "When all evaluation criteria specify weights, they must sum to " +
        "approximately 1.0 (±0.01). Either ensure they sum correctly or " +
        "leave some weights unspecified for relative weighting.",
    },
  );

// ── § 7  PromptDocument — top-level versionable prompt artifact ──

/**
 * Validate a top-level prompt document combining identity, orchestration,
 * context engineering, and evaluation into a single versionable artifact.
 */
export const PromptDocumentSchema = z.object({
  /** Schema version for forward compatibility. */
  schemaVersion: SchemaVersionSchema,

  /** Unique identifier for this prompt document. */
  id: z.string().meta({
    description: "Unique prompt identifier (e.g. UUID or slug)",
  }),

  /** Human-readable name. */
  name: z.string(),

  /** Semver for the prompt content itself. */
  version: z.string().regex(SEMVER_RE, {
    message: "version must be valid semver (e.g. '1.0.0', '1.2.3-beta.1')",
  }),

  /** Optional description of what this prompt does. */
  description: z.string().optional(),

  /** Tags for categorization and search. */
  tags: z.array(z.string()).optional(),

  // ── Core: what to do and how to coordinate ──

  /** The orchestration strategy (embeds one or more CallSpecs). */
  orchestration: OrchestrationSchema,

  // ── Context engineering ──

  /** Context engineering configuration for production / agentic use. */
  context: ContextConfigSchema.optional(),

  // ── Evaluation ──

  /** Evaluation criteria to judge output quality. */
  evaluation: EvaluationSchema.optional(),

  // ── Audit trail ──

  metadata: z
    .object({
      author: z.string().optional(),
      createdAt: z.iso.date().optional(),
      updatedAt: z.iso.date().optional(),
      changelog: z
        .array(
          z.object({
            version: z.string().regex(SEMVER_RE, {
              message: "changelog version must be valid semver",
            }),
            date: z.iso.date(),
            changes: z.string(),
          }),
        )
        .optional(),
    })
    .optional(),
});

// ── § 8  Type Exports — inferred types for consumer code ──

/** Validated top-level prompt document, inferred from {@link PromptDocumentSchema}. */
export type PromptDocument = z.infer<typeof PromptDocumentSchema>;

/** Validated single-call specification, inferred from {@link CallSpecSchema}. */
export type CallSpec = z.infer<typeof CallSpecSchema>;

/** Validated prompt technique variant, inferred from {@link PromptTechniqueSchema}. */
export type PromptTechnique = z.infer<typeof PromptTechniqueSchema>;

// Orchestration is manually defined above (recursive type).

/** Validated model persona and behavioral constraints, inferred from {@link RoleSchema}. */
export type Role = z.infer<typeof RoleSchema>;

/** Validated few-shot example pair, inferred from {@link ExampleSchema}. */
export type Example = z.infer<typeof ExampleSchema>;

/** Validated output format descriptor, inferred from {@link OutputFormatSchema}. */
export type OutputFormat = z.infer<typeof OutputFormatSchema>;

/** Validated model inference parameters, inferred from {@link ModelParamsSchema}. */
export type ModelParams = z.infer<typeof ModelParamsSchema>;

/** Validated thinking configuration variant, inferred from {@link ThinkingConfigSchema}. */
export type ThinkingConfig = z.infer<typeof ThinkingConfigSchema>;

/** Validated context engineering config, inferred from {@link ContextConfigSchema}. */
export type ContextConfig = z.infer<typeof ContextConfigSchema>;

/** Validated retrieval source entry, inferred from {@link RetrievalSchema}. */
export type Retrieval = z.infer<typeof RetrievalSchema>;

/** Validated memory configuration, inferred from {@link MemorySchema}. */
export type Memory = z.infer<typeof MemorySchema>;

/** Validated tool definition, inferred from {@link ToolDefinitionSchema}. */
export type ToolDefinition = z.infer<typeof ToolDefinitionSchema>;

/** Validated evaluation criteria set, inferred from {@link EvaluationSchema}. */
export type Evaluation = z.infer<typeof EvaluationSchema>;

// ── § 9  JSON Schema Export — interop with non-TypeScript tooling ──

/**
 * JSON Schema representation of {@link PromptDocumentSchema} (draft-2020-12).
 *
 * @remarks
 * `.refine()` validations and `z.lazy()` recursive references are
 * runtime-only and not expressible in JSON Schema. Consumers must
 * implement equivalent checks in their validation layer.
 */
export const promptDocumentJsonSchema = z.toJSONSchema(PromptDocumentSchema, {
  target: "draft-2020-12",
});

// ── § 10  Example Instance — type-checked sample document ──

const sharedExamples: Example[] = [
  {
    input: "const x: any = fetchData();\nconsole.log(x.name);",
    output: JSON.stringify([
      {
        severity: "warning",
        line: 1,
        message:
          "Avoid `any` — use a proper type or `unknown` with narrowing.",
        fix: "const x: User = fetchData();",
      },
    ]),
    label: "any-type-detection",
  },
];

/** Type-checked sample prompt document for a TypeScript code review. */
export const examplePromptDocument: PromptDocument = {
  schemaVersion: "0.3.0",
  id: "code-review-v1",
  name: "TypeScript Code Review",
  version: "1.0.0",
  description:
    "Reviews TypeScript code for bugs, style, and performance issues.",
  tags: ["code-review", "typescript", "engineering"],

  orchestration: {
    strategy: "single",
    call: {
      system: {
        role: {
          persona: "Senior TypeScript engineer with 10 years of experience",
          expertise: ["TypeScript", "Node.js", "performance optimization"],
          constraints: [
            "Only flag real issues, not stylistic preferences",
            "Do not rewrite code unless asked",
          ],
          tone: "direct and constructive",
        },
        instructions: [
          "Review the provided TypeScript code.",
          "Identify bugs, type-safety issues, and performance concerns.",
          "Classify each finding as: critical | warning | suggestion.",
          "Output your findings inside <findings> tags as a JSON array.",
        ].join("\n"),
        xmlTags: [
          { tag: "code", purpose: "Wraps the user-supplied code to review" },
          {
            tag: "findings",
            purpose: "Contains the structured review output",
          },
        ],
      },

      userTemplate: "<code>\n{{sourceCode}}\n</code>",

      variables: {
        sourceCode: {
          type: "string",
          description: "The TypeScript source code to review",
          required: true,
        },
      },

      outputFormat: {
        type: "json",
        schema: {
          type: "array",
          items: {
            type: "object",
            properties: {
              severity: {
                type: "string",
                enum: ["critical", "warning", "suggestion"],
              },
              line: { type: "number" },
              message: { type: "string" },
              fix: { type: "string" },
            },
            required: ["severity", "message"],
          },
        },
        constraints: ["Return ONLY the JSON array, no preamble"],
      },

      examples: sharedExamples,

      techniques: [
        {
          technique: "few_shot",
          examples: sharedExamples,
          includeEdgeCases: true,
        },
        {
          technique: "chain_of_thought",
          variant: "zero_shot",
          thinkingTag: "analysis",
        },
      ],

      prefill: "<analysis>\n",

      modelParams: {
        model: "claude-opus-4-6",
        temperature: 0.2,
        maxTokens: 4096,
        thinking: { type: "enabled", budgetTokens: 8192 },
      },
    },
  },

  evaluation: {
    criteria: [
      {
        name: "precision",
        description: "Flagged issues are real issues",
        weight: 0.4,
      },
      {
        name: "recall",
        description: "No critical issues are missed",
        weight: 0.4,
      },
      {
        name: "clarity",
        description: "Findings are clearly explained",
        weight: 0.2,
      },
    ],
  },

  metadata: {
    author: "prompt-engineering-team",
    createdAt: "2026-02-15",
    changelog: [
      {
        version: "0.1.0",
        date: "2026-02-15",
        changes: "Initial version",
      },
      {
        version: "0.2.0",
        date: "2026-02-15",
        changes:
          "Structural fixes: renamed $schema → schemaVersion, unified " +
          "ToolDefinitionSchema, typed LayeredSchema.layers, fixed example " +
          "instance validation, added cross-field refinements, enforced " +
          "semver and ISO dates, documented orchestration scope.",
      },
      {
        version: "0.3.0",
        date: "2026-02-15",
        changes:
          "Two-layer architecture: split CallSpec (single-call) from " +
          "Orchestration (multi-call). Removed `layered` and `prefill` " +
          "techniques. Made orchestration recursive via z.lazy(). Added " +
          "DAG validation for chains, bidirectional variable cross-check, " +
          "evaluation weight sum validation, conditional budgetTokens " +
          "requirement for thinking, and explicit compilation semantics.",
      },
    ],
  },
};

// ── § 11  Chained Example — recursive composition demo ──

/** Type-checked example of recursive chain composition. */
export const chainedExample: PromptDocument = {
  schemaVersion: "0.3.0",
  id: "research-pipeline-v1",
  name: "Research Analysis Pipeline",
  version: "1.0.0",
  description:
    "Two-stage pipeline: extract claims with self-consistency, " +
    "then synthesize a report.",
  tags: ["research", "pipeline", "multi-stage"],

  orchestration: {
    strategy: "chain",
    steps: [
      {
        id: "extract",
        description: "Extract key claims using self-consistency for reliability",
        orchestration: {
          strategy: "self_consistency",
          numPaths: 3,
          selectionStrategy: "majority_vote",
          temperature: 0.7,
          call: {
            system: {
              instructions:
                "Extract the top 5 factual claims from the provided document. " +
                "Output as a JSON array of strings.",
            },
            userTemplate: "<document>\n{{paperText}}\n</document>",
            variables: {
              paperText: {
                type: "string",
                description: "The research paper text",
                required: true,
              },
            },
            outputFormat: { type: "json" },
            prefill: "[",
          },
        },
      },
      {
        id: "synthesize",
        description: "Synthesize extracted claims into a structured report",
        inputFrom: ["extract"],
        orchestration: {
          strategy: "single",
          call: {
            system: {
              role: {
                persona: "Academic research analyst",
                tone: "precise and balanced",
              },
              instructions:
                "Given the extracted claims from a prior analysis step, " +
                "write a structured research summary with sections: " +
                "Overview, Key Findings, Limitations, and Open Questions.",
            },
            userTemplate:
              "Claims extracted from the paper:\n{{extractedClaims}}\n\n" +
              "Original document:\n{{paperText}}",
            variables: {
              extractedClaims: {
                type: "string",
                description: "JSON array of claims from the extract step",
                required: true,
              },
              paperText: {
                type: "string",
                description: "The original research paper text",
                required: true,
              },
            },
            outputFormat: { type: "markdown" },
            techniques: [
              {
                technique: "chain_of_thought",
                variant: "zero_shot",
                thinkingTag: "reasoning",
              },
            ],
            modelParams: {
              model: "claude-opus-4-6",
              maxTokens: 8192,
              thinking: { type: "enabled", budgetTokens: 4096 },
            },
          },
        },
      },
    ],
  },

  evaluation: {
    criteria: [
      {
        name: "factual_accuracy",
        description: "Claims extracted are actually in the source document",
        weight: 0.5,
      },
      {
        name: "coverage",
        description: "Report addresses all major claims",
        weight: 0.3,
      },
      {
        name: "coherence",
        description: "Report reads as a unified analysis, not a list",
        weight: 0.2,
      },
    ],
  },

  metadata: {
    author: "prompt-engineering-team",
    createdAt: "2026-02-15",
  },
};

// ── § 12  Validation Helpers — parse and safe-parse entry points ──

/**
 * Parse and validate raw data as a {@link PromptDocument}.
 *
 * @param input - Unvalidated prompt document data.
 * @returns A validated {@link PromptDocument}.
 * @throws {@link z.ZodError} If `input` fails schema validation.
 */
export function parsePromptDocument(input: unknown): PromptDocument {
  return PromptDocumentSchema.parse(input);
}

/**
 * Safely parse raw data as a {@link PromptDocument} without throwing.
 *
 * @param input - Unvalidated prompt document data.
 * @returns A Zod safe-parse result with `success`, `data`, or `error`.
 */
export function safeParsePromptDocument(input: unknown) {
  return PromptDocumentSchema.safeParse(input);
}

/**
 * Parse and validate raw data as a {@link CallSpec}.
 *
 * @param input - Unvalidated call spec data.
 * @returns A validated {@link CallSpec}.
 * @throws {@link z.ZodError} If `input` fails schema validation.
 */
export function parseCallSpec(input: unknown): CallSpec {
  return CallSpecSchema.parse(input);
}

/**
 * Safely parse raw data as a {@link CallSpec} without throwing.
 *
 * @param input - Unvalidated call spec data.
 * @returns A Zod safe-parse result with `success`, `data`, or `error`.
 */
export function safeParseCallSpec(input: unknown) {
  return CallSpecSchema.safeParse(input);
}

// Changelog and migration guide: see docs/prompt-schema.md
