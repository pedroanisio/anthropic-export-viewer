---
name: conceptual-codebase-analysis
description: >
  Perform deep conceptual analysis of codebases — not structural extraction
  (class diagrams, call graphs) but intent inference, design-decision archaeology,
  and predictive modeling. Use this skill whenever the user asks to "analyze",
  "understand", "explain the architecture of", "map out", "reverse-engineer",
  or "onboard me to" a codebase or repository. Also trigger when the user asks
  questions like "how does this system think?", "what are the design decisions?",
  "where are the tensions/tech debt?", "what would break if I changed X?",
  or "give me the mental model for this codebase." Trigger even for partial
  analysis requests like "explain the data flow" or "what are the core concepts?"
  — the lenses can be applied individually. Do NOT trigger for simple file
  reading, syntax questions, single-function explanations, or bug fixes unless
  the user explicitly frames them as architectural/conceptual questions.
---

# Conceptual Codebase Analysis

## The Goal

Given a codebase $C$, produce an output $M$ such that:

1. $M$ captures **intent and design decisions**, not just structure.
2. $M$ is **language-agnostic** in vocabulary.
3. $|M| \ll |C|$ (high compression).
4. $M$ enables a reader to **predict system behavior** in situations not explicitly described.

Property (4) is the acceptance criterion. Test it: given only $M$, can an engineer correctly answer 5 architectural what-if questions about $C$? If yes, $M$ is predictive. If not, it's a census.

**What this is NOT:** a class diagram, a call graph, auto-generated docs, or file-by-file summarization. Those answer "what exists?" — a census. This methodology answers "how does this system think?"

---

## Your Capabilities and Limits

State these honestly when relevant.

**You can do:**
- Intent inference — propose *why* code was written a certain way
- Cross-paradigm recognition — identify equivalent computational ideas across languages
- Boilerplate subtraction — collapse repetitive structural patterns into one semantic node
- Boundary detection — find where data changes shape, trust boundaries, abstraction layers
- Narrative synthesis — turn structural facts into a predictive story

**You cannot do:**
- Runtime behavior (no profiler data, no race conditions, no hot paths)
- Full ingestion of codebases >100K LOC in one pass (context window is finite)
- Verification (your output is hypothesis, not theorem)
- Historical intent without git history or ADRs
- Invisible edges (~1/3 of meaningful dependencies are invisible to static analysis: config wiring, runtime registration, orchestrator data flows)

---

## Intermediate Representation (IR)

You operate on an implicit graph of typed nodes and edges. The IR is infrastructure — the user never sees it unless they ask. For the full node/edge taxonomy and criticality tiers, read `references/ir-schema.md`.

**Key principle:** weight semantic edges (data_flows_to, emits/consumes) and governing edges (validates, enforces, configures) higher than structural edges (imports, calls) when clustering and analyzing. Structural edges are high-frequency but often low-value.

**Auditability:** if the user requests rigor or you are uncertain, offer to emit the inferred IR for human audit before proceeding to lens analysis.

---

## Entry Strategy: Boundaries First

### Step 1 — Ingest boundary artifacts

Before reading implementation code, find and ingest:

- API contracts (OpenAPI, GraphQL, gRPC `.proto`)
- Data schemas (DDLs, migrations, Prisma/Drizzle/Zod schemas)
- Validation schemas (Zod, JSON Schema, Pydantic)
- Event contracts (message schemas, topic/queue configs)
- CLI definitions (argument parsers, command registrations)
- Configuration surface (env vars, feature flags)

These define **what the system does** before you learn **how**.

### Step 2 — Fallback hierarchy

When contracts don't exist, fall back in this order:
tests → routes/handlers → public type exports → README/docs → directory tree.

### Step 3 — Boilerplate subtraction

Filter out plumbing before conceptual analysis. Heuristics: framework naming conventions with no domain logic, generic middleware, DI container config, ORM scaffolds, build/deploy config. Report what you subtracted and why.

### Step 4 — Multi-repo / polyglot systems

When the system spans multiple repos, inter-service contracts are primary:
API gateway configs, schema registries, message broker definitions, shared type packages, IaC service definitions. Analyze individual repos as subordinate steps. The macro-architecture lives in inter-service contracts.

---

## Six Analytical Lenses

### Execution order

Lens 1 first. Lenses 2 and 3 can run in parallel. Lenses 4 and 5 depend on Lens 1. Lens 6 depends on all others.

```
Lens 1 (Ontology)  ──→  Lens 4 (Information Architecture)
       │                         │
       └──→  Lens 5 (Capability Clustering)
                                 │
Lens 2 (Computational Model)  ──┘
       │
Lens 3 (Invariants)  ──────────→  Lens 6 (Tension Mapping)
                                         ↑
                              All lenses feed into Lens 6
```

For partial analysis requests, apply only the relevant lens(es) but note dependencies.

### Lens 1: Ontology — "What does this system believe exists?"

1. Collect all reified nouns (types, classes, tables, config keys).
2. Classify each: **domain** / **control** / **platform** / **integration**.
3. Cluster by co-occurrence in function signatures and module boundaries.
4. Identify the **core ontology** (5–15 concepts).
5. Identify **absent concepts** — things the domain requires but the codebase doesn't reify. These are often the most revealing.

### Lens 2: Computational Model — "What kind of machine is this?"

Classify each subsystem by paradigm: Request-Response, Event-Driven, Pipeline/Dataflow, State Machine, Actor Model, Blackboard, Rule Engine. Most systems are hybrids. Identify paradigm boundaries and mismatches — these are common tension sources.

### Lens 3: Invariants — "What must always be true?"

1. Extract **explicit** invariants: assertions, validations, type constraints, DB constraints.
2. Infer **implicit** ones: ordering, uniqueness, referential integrity, idempotency.
3. Map enforcement points.
4. Identify violations: TODO, HACK, unsafe casts, disabled checks.

### Lens 4: Information Architecture — "What knows about what?"

For each major component: what it exports, imports, hides. Identify:
- Knowledge asymmetries
- Translation layers (membranes)
- Information flow for 2–3 key data items

**Selection criteria:** pick data items that (a) cross the most boundaries, (b) carry the most business value, or (c) are most likely to be change-impact subjects.

### Lens 5: Capability-Centered Clustering — "What are the real feature slices?"

**Clustering signals** (use multiple): shared business nouns, repeated call paths, common transaction boundaries, same DB tables, same event channels, same test suites, same API endpoints, same config scopes.

For each capability, trace all participating nodes. Cluster capabilities with significant overlap. Name by business outcome, not structural location.

### Lens 6: Tension Mapping — "Where does this system struggle?"

Identify complexity hotspots. For each, diagnose the source:

- **Conflicting requirements** — two valid needs that pull design in opposite directions
- **Leaky abstractions** — implementation details escaping their boundary
- **Historical accretion** — layers of decisions that no longer cohere
- **Paradigm mismatch** — subsystems using incompatible computational models
- **Misleading abstractions** — names that lie ("Repository" containing business policy)
- **Contract drift** — divergence between what an API contract promises and what the implementation enforces

Also identify **design bets**: deliberate trade-offs visible in comments, config options, or architectural asymmetries. These are not problems — they are choices with known costs.

---

## Evidence Discipline

Every substantive claim you make must carry evidence. Use this structure:

| Level | Meaning |
|---|---|
| **High** | 3+ files, naming patterns, tests, and config converge |
| **Medium** | 1–2 files; alternative interpretations exist |
| **Low** | Naming conventions alone, or single code path |

**What counts as evidence:** specific file, test, type, config, comment, naming pattern, git history.

**What does NOT count:** "common framework pattern" (prior knowledge, not evidence from *this* codebase), "folder named X" (names lie), "would make sense" (reasoning about *should*, not *is*).

**Narrative form** — weave evidence into prose:

> The system enforces idempotency on all payment operations.
> *(Evidence: `PaymentService.execute()` checks `idempotencyKey`;
> `payments` table has unique constraint;
> `payment.idempotency.spec.ts` verifies duplicate rejection.
> Confidence: high.)*

---

## Output Sections

For the formal TypeScript output schema, read `references/output-schema.ts`.

Produce these sections:

1. **System Thesis** (1 paragraph): predictive summary. A reader who grasps this should predict system behavior in novel situations.

2. **Concept Atlas**: core 5–15 concepts with classification, purpose, implementation locations, stability assessment.

3. **Capability Map**: what the system can do — triggers, entry points, decision points, failure paths.

4. **Flow Narratives**: 3–5 critical flows as prose narratives. Prioritize flows that are (a) user-facing, (b) revenue-carrying, (c) integrity-critical, or (d) most complex/fragile.

5. **Boundary Contracts**: where the seams are, with contract drift assessment.

6. **Tension Report**: 3–5 areas of highest design stress with diagnosis and source classification.

7. **Onboarding Path**: ordered list of files/modules to read first, with rationale for the ordering.

8. **Change Impact Guide**: for 2–3 likely change scenarios, what breaks and what propagation path to trace.

9. **Architecture Map** (SVG): a single visual showing concept nodes (color-coded by classification), capability cluster regions, semantic/governing edges, tension hotspots, and invariant badges. This is the scannable overview — the reader should glance at it and immediately see the major parts, how they connect, and where it hurts. For construction rules, palette, layout algorithm, and the SVG template, read `references/architecture-map-svg.md` before generating.

10. **Compression Ratio**: self-check metric. Total conceptual items should be ≤40. If you exceed this, you are under-compressing — re-cluster.

---

## Execution Strategy

### Small codebases (<10K LOC)

Single-pass: ingest boundaries → populate IR → all six lenses → evidence-check → narrative.

### Medium codebases (10K–100K LOC)

Iterative deepening over 3–5 rounds:
1. Boundary artifacts + boilerplate subtraction.
2. Lens 1 (Ontology) from types and public APIs.
3. Lenses 2–3 from 10–15 most-connected non-plumbing files.
4. Lenses 4–5 from traced data flows and capability clusters.
5. Lens 6 from all prior results.
6. Targeted reads to resolve low-confidence claims.

### Large codebases (>100K LOC)

Sampling + guided exploration over 10+ rounds:
1. Boundary artifacts + build system → subsystem boundaries.
2. Analyze each subsystem as a medium codebase.
3. Analyze inter-subsystem interfaces (this is where the real architecture lives).
4. Synthesize into system-level narrative.
5. Ask the user which areas to explore deeper.

---

## Execution Modes

### Mode A: Conversational Analysis (default)

You read code in conversation, mentally populate the IR, apply lenses, and produce the narrative. No external tooling required.

**Strengths:** works immediately, adapts to any language, handles ambiguity through dialogue.
**Limits:** IR is implicit and non-inspectable; results may vary across sessions; context window constrains codebase size.

### Mode B: Tool-Assisted Pipeline

When the user has tooling available (tree-sitter parsers, graph DBs, scripts):
1. Use per-language parsers to produce a materialized IR.
2. Apply LLM-driven semantic enrichment.
3. Use graph queries for clustering and tension detection.
4. Generate narrative from the enriched graph.

**Strengths:** reproducible, scalable, auditable IR.
**Limits:** requires engineering investment; parser coverage determines language support.

If the user's environment supports file creation and scripting, offer to materialize parts of the IR as JSON for auditability.

---

## Failure Patterns

Recognize and flag these situations — they require adjusted entry strategies:

- **Meta-frameworks / code generation**: real logic lives in generators, not generated code. Analyze the generator config.
- **DSL-heavy systems**: business logic in a custom DSL means the host language code is infrastructure. Apply methodology to the DSL.
- **Highly dynamic runtime wiring**: DI, plugin loading, reflection-based dispatch makes the call graph unknowable statically. Spring Boot at scale is canonical. Flag invisible edges aggressively.
- **Monorepos with unrelated projects**: ask which system to analyze before starting.
- **Polyglot event-driven systems**: the real architecture is the message broker topology. Analyze event schema registry and broker config, not individual services.

When you suspect one of these, say so explicitly and adjust.

---

## Delivering Results

### As Markdown (default)

Produce a single Markdown document with frontmatter disclaimer, all output sections, and inline evidence. Follow the user's formatting preferences.

### Architecture Map (always)

Always generate the Architecture Map SVG as part of the analysis output. Read `references/architecture-map-svg.md` for the full construction spec before generating. The SVG should be emitted as a standalone `.svg` file (if file creation is available) or inline using the Visualizer tool (if available). The map is a synthesis artifact — generate it *after* all lenses complete, not during.

### As structured data

If the user requests machine-readable output, follow the TypeScript schema in `references/output-schema.ts` and emit JSON.

### Partial analysis

If the user asks about a specific aspect (e.g., "what are the tensions?" or "trace the data flow for X"), apply only the relevant lens(es) but note any dependencies you couldn't resolve without running prerequisite lenses.

---

## Reference Files

Read these as needed — do not load them all upfront:

- **`references/ir-schema.md`** — Full IR node types, edge types, and criticality tiers. Read when you need to reason about the graph structure or explain the IR to the user.
- **`references/output-schema.ts`** — Formal TypeScript interfaces for structured output. Read when the user requests machine-readable output or you want to validate your output structure.
- **`references/architecture-map-svg.md`** — SVG construction spec: visual vocabulary, palette, node shapes, edge styles, layout algorithm, and starter template. **Read before generating the Architecture Map.** Contains the full SVG skeleton you adapt to each analysis.
- **`references/worked-example.md`** — Complete worked example applying the methodology to a real codebase (KTree Tester, ~8K LOC). Read for calibration on expected depth, evidence quality, and output format.
- **`references/validation.md`** — Validation protocol for measuring methodology effectiveness. Read if the user asks about rigor, reliability, or how to evaluate the analysis.
