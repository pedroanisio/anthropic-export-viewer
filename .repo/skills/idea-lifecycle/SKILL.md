---
name: idea-lifecycle
description: >
  Portfolio lifecycle management for divergent minds. Processes documents
  into a patchable knowledge graph of ideas, concepts, projects, and
  insights. Operations: ingest, extract, review, relate, triage, prune,
  diagnose, graph. Use when the user mentions: managing ideas, brain dump,
  idea backlog, "too many ideas", "what should I work on", portfolio
  review, "what's stale", "find patterns", "what's duplicated",
  consolidate, "extract ideas from this", "show the graph", mosaic,
  "process my notes", or uploads portfolio-state.json or documents for
  idea extraction. Also trigger on "I keep starting things and not
  finishing" or "I need to get my ideas out of my head".
---

# Idea Lifecycle Management

## Purpose

Divergent minds produce ideas faster than they can process them. The
failure mode is not lack of creativity — it is portfolio collapse:
too many open threads, no triage discipline, no kill criteria, and
no way to see the whole landscape.

This skill provides the scaffolding to prevent that collapse. It
manages a **portfolio** — a persistent, structured collection of
items with typed relationships, provenance tracking, and pattern
detection — exposed as an incrementally-patchable knowledge graph.

The graph is a **mosaic**: each document processed, each brain dump
captured, each connection discovered adds tiles. Over time, the
mosaic reveals the user's core preoccupations, recurring patterns,
productive tensions, and dead weight.

---

## First Steps: Load References

Before any operation, read the relevant reference files:

1. **Always read first:**
   ```
   view <skill-path>/references/taxonomy.md
   ```
   Defines item types, maturity stages, relationship types,
   provenance, pattern types, priority signals, kill criteria,
   and graph operations.

2. **For document processing, graph ops, or diagnostics:**
   ```
   view <skill-path>/references/graph-operations.md
   ```
   Defines extraction protocol, patching, merging, diagnostic
   analysis, and visualization protocol.

3. **For state file handling or artifact building:**
   ```
   view <skill-path>/references/schema.md
   ```
   Defines JSON schemas, file conventions, visual encoding,
   and artifact specifications.

---

## Detecting the User's Intent

Map what the user says to the correct operation:

| User Says (examples) | Operation |
|---|---|
| "I had an idea...", "brain dump", "capture this" | **ingest** |
| "Process this document", "extract ideas from this PDF" | **extract** |
| "Show me my portfolio", "what do I have", "overview" | **review** |
| "How does X connect to Y", "find connections", "map" | **relate** |
| "What should I work on", "prioritize", "triage" | **triage** |
| "What should I kill", "what's stale", "clean up" | **prune** |
| "Find patterns", "what's duplicated", "consolidate", "recurring themes" | **diagnose** |
| "Show the graph", "visualize", "mosaic", "big picture" | **graph** |
| [Uploads portfolio-state.json] | **review** (load state first) |
| [Uploads document + asks about ideas] | **extract** |

If ambiguous, default to **review**.

---

## Operations

### Operation 1: Ingest

**Purpose:** Capture new items from direct user input with minimal
friction.

**Process:**

1. Accept whatever the user provides — sentence fragments, walls
   of text, lists, links, stream-of-consciousness. Do not ask
   the user to restructure their input.

2. For each identifiable item:
   a. Preserve `raw_input` verbatim.
   b. Classify `type` using taxonomy. Explain briefly.
   c. Write `core_statement` in problem-language.
   d. Set `stage` to `raw`, `provenance.source_type` to `manual`.
   e. Suggest 2–4 tags.
   f. Scan existing items for relationships. Propose tentative links.

3. Present items for batch confirmation.

4. Commit to portfolio state. Generate patch.

**Divergent-mind rules:**
- Never say "too vague." Vagueness is normal at spark stage.
- If 20 items are dumped at once, process all 20.
- Untangle compound paragraphs into separate items. Note what
  was split and why.

---

### Operation 2: Extract

**Purpose:** Process uploaded documents into portfolio items with
full provenance, then integrate into the existing graph.

**This is the primary document-to-graph operation.**

**Process:**

Follow the Document Extraction Protocol in `graph-operations.md`:

1. **Pre-flight**: Hash check, document registration, file reading.
2. **Extract**: Apply the strategy for the document type. Each
   distinct idea, claim, question, decision, or reference becomes
   a candidate item with full provenance.
3. **Cross-reference**: Compare every extracted item against the
   existing portfolio. Propose relationships.
4. **Dedup check**: Flag potential duplicates.
5. **Pattern check**: Run a lightweight pattern scan to see if the
   new items trigger any new patterns (especially recurrence).
6. **Present extraction report** for user confirmation.
7. **Commit** confirmed items and relationships. Generate patch.

**Multiple documents**: If the user uploads several files at once,
process each sequentially. After all are extracted, run a cross-
document relationship scan and a full pattern detection pass.

**Key principle**: Extraction is not just ingestion — it is
*integration*. Every extracted item must be checked against the
existing graph. The value is in the connections, not the items
alone.

---

### Operation 3: Review

**Purpose:** Show the user their portfolio state.

**Modes:**

- **Full review**: Markdown portfolio snapshot (schema.md format).
  Group by type → stage. Show counts, clusters, recent session log.
- **Filtered review**: Subset by stage, tag, cluster, document
  source, or pattern involvement.
- **Interactive review**: React graph artifact (see Operation 8).

**Always surface during review:**
1. Unprocessed backlog (raw items, 3+ sessions old).
2. Parked items whose reactivation trigger may have fired.
3. New clusters formed since last review.
4. Orphan items (zero relationships).
5. Active patterns from last diagnostic.

---

### Operation 4: Relate

**Purpose:** Discover and record relationships between items.

**Process:**

1. If user specifies items: analyze and propose relationship type.
2. If user asks for broad scan: pairwise comparison of all non-dead
   items (prioritize shared-tag and same-cluster pairs).
3. Propose relationships with reasoning and confidence level.
4. Detect new clusters (3+ items, 2+ shared relationships).
5. Present for confirmation. User overrides Claude's proposals.
6. Commit. Generate patch.

---

### Operation 5: Triage

**Purpose:** Decide what to focus on next.

**Process:**

1. Get current context (time, energy, constraints) — extract from
   conversation if already stated, otherwise ask once.

2. Re-evaluate priority signals for all non-dead items against
   current context.

3. Produce structured recommendation:
   - **Recommended Focus** (1–3 items): why each ranks here.
   - **Worth a Session** (next tier): what would promote them.
   - **Park Candidates**: with proposed reactivation triggers.
   - **Kill Candidates**: with kill criteria citation.

4. User decides. Update stages. Generate patch.

**Rules:**
- Triage output fits two screens max — even for 50 items.
- Respect conviction as data.
- Name the cost of switching from an active item.

---

### Operation 6: Prune

**Purpose:** Remove dead weight.

**Process:**

1. Scan all items against kill criteria (taxonomy §7).
2. For each candidate: state criterion, summarize item, ask for
   decision (kill / merge / one-more-cycle).
3. Backup state before any kills.
4. Execute approved kills and merges. Generate patch.

---

### Operation 7: Diagnose

**Purpose:** Analyze the graph structure to surface patterns,
health issues, duplications, recurring themes, consolidation
opportunities, and actionable recommendations.

**This is the core analytical operation for the mosaic.**

**Process:**

Follow the Diagnostic Analysis Protocol in `graph-operations.md`:

1. **Duplication scan**: Find near-identical core_statements.
2. **Recurrence detection**: Find themes across 3+ independent items.
3. **Convergence / divergence analysis**: Items clustering or
   fragmenting.
4. **Dependency chain detection**: Find bottlenecks.
5. **Staleness analysis**: Find forgotten clusters and processing
   backlogs.
6. **Consolidation opportunities**: Mergeable items, promotable
   concepts, orphaned references.

Produce the full Diagnostic Report (format in graph-operations.md).

After presenting findings:
- Ask which actions to take.
- Apply approved actions as a patch.
- Update pattern records (mark resolved/dismissed).
- Regenerate the graph artifact if one exists.

**Scheduling**: Recommend running diagnose every 3–5 sessions or
whenever the portfolio exceeds 30 non-dead items.

---

### Operation 8: Graph

**Purpose:** Generate and present the interactive knowledge graph
artifact — the visual mosaic.

**Process:**

1. Project the portfolio state into the visualization data
   structure (schema.md § Graph Visualization Data).

2. Generate a React artifact using d3-force layout with the
   visual encoding defined in schema.md:
   - Node shape = item type
   - Node color = maturity stage
   - Edge style = relationship type
   - Edge width = confidence
   - Cluster regions = background shading
   - Pattern highlights = pulsing on involved nodes

3. Include filter controls (type, stage, tag, cluster, source,
   pattern involvement).

4. Include click-to-inspect for nodes, edges, clusters, patterns.

5. Store the graph state in `window.storage` under key
   `portfolio-state` for cross-session persistence.

6. If a diagnostic has been run, overlay active patterns on the
   graph with visual indicators (see graph-operations.md §5).

**Graph patching**: When new items are added (via ingest or
extract), the graph artifact should be regenerable from the
updated portfolio state. The artifact reads from storage on
mount — it does not maintain its own separate state.

**Diff view**: If the user asks "what changed", render a diff
overlay: new nodes highlighted, removed nodes grayed, new edges
in a contrasting color.

---

## State Management

### Session Start

1. Check for uploaded `portfolio-state.json`.
   - If found: load, validate, report counts.
   - If not found: check `window.storage`. If found there, use it.
   - If neither: ask if this is a first session. If yes, create
     empty portfolio.

2. Read file-reading skill if documents are uploaded alongside
   the state file.

### Session End

After any state-modifying operation:

1. Generate the session's patch object.
2. Append patch and session log entry.
3. Write `portfolio-state.json` to `/mnt/user-data/outputs/`.
4. If a React artifact exists, update `window.storage`.
5. Present the state file for download.
6. Brief summary of session: items added/killed, relationships
   created, patterns detected.

---

## Integration with Other Skills

| Need | Hand Off To |
|---|---|
| Deep problem decomposition on one item | **problem-space-exploration** |
| Choosing between competing approaches | **arch-decision-analysis** |
| Item matured into a full spec | **codebase-requirements** or **bsl** |
| Item needs to become a document | **docx** or **pdf** |
| Surgical edit to a markdown portfolio doc | **doc-patch** |
| Reading uploaded documents for extraction | **file-reading** / **pdf-reading** |

When handing off, pass: `core_statement`, `raw_input`, tags,
relationships, cluster context, and relevant pattern findings.

---

## Anti-Patterns

1. **Over-structuring intake.** Accept raw input. Claude structures.
2. **False precision.** Categorical signals, not numerical scores.
3. **Guilt-tripping kills.** Killing is portfolio hygiene.
4. **Ignoring the graveyard.** Dead items are data. Check them
   during relate and diagnose.
5. **Treating portfolio as a to-do list.** It is a network, not
   a sequence.
6. **Session amnesia.** Always write state. Always generate patch.
7. **Extraction without integration.** Never just add items from
   a document — always cross-reference against existing graph.
8. **Pattern-without-action.** Every diagnosed pattern must include
   a concrete recommended action. Observation without prescription
   is waste.
