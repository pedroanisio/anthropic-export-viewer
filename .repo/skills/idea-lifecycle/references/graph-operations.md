# Graph Operations Reference

This document defines the protocols for document extraction,
graph construction, incremental patching, merging, and diagnostic
analysis. Load this reference before performing any `extract`,
`diagnose`, or `graph` operation.

---

## 1. Document Extraction Protocol

### Purpose

Transform an uploaded document into portfolio items with full
provenance, then integrate those items into the existing graph.

### Pre-Extraction Checks

Before extracting from any document:

1. **Hash check**: Compute the SHA-256 of the file content. Check
   the document registry for an existing entry with the same hash.
   - If found: warn the user. Offer to skip, re-process (which
     may produce duplicates), or diff against previous extraction.
   - If not found: proceed.

2. **Register the document**: Create a document registry entry
   before extracting any items. This ensures provenance tracking
   even if extraction is interrupted.

3. **Read the appropriate file-reading skill**: Use the correct
   tool for the file type (PDF reader for PDFs, view for markdown,
   etc.). Do not attempt to read binary files as text.

### Extraction Strategy by Document Type

| Document Type | Strategy |
|---|---|
| **Notes / brain dumps** (md, txt) | Sentence-level scan. Each distinct thought, question, or claim becomes a candidate item. Preserve paragraph boundaries as context. |
| **Articles / papers** (pdf, docx) | Section-level scan. Extract: thesis/argument, key claims, methodology (if relevant), conclusions, open questions. Each becomes an item. The document itself becomes a `reference` item. |
| **Specs / briefs** (md, docx) | Goal-level extraction. Extract: problem statement, constraints, proposed approaches, open decisions. Map to concept or project items. |
| **Lists / collections** (csv, bullet lists) | Row/item-level extraction. Each row or bullet is a candidate item. |
| **Images / diagrams** | Describe what is depicted. Extract any text. Create a spark or reference item depending on content. |
| **Code / repos** | Extract: purpose, architecture decisions, open TODOs, dependencies. Map to project or concept items. |
| **Conversations / chat logs** | Extract: decisions made, questions raised, ideas proposed, action items committed. Each becomes a separate item. |

### Extraction Process

For each candidate item found in the document:

1. **Capture raw_input**: The exact text from the document
   (quote or close paraphrase with page/section reference).

2. **Classify type**: Using taxonomy definitions. Most document
   extractions produce sparks, insights, or references. Concepts
   and projects are rarer — they require more structure than a
   single document passage usually provides.

3. **Write core_statement**: One sentence, problem-language.

4. **Set provenance**:
   ```json
   {
     "source_type": "document",
     "document_id": "<registered doc id>",
     "page_or_section": "<where in the document>",
     "extraction_method": "full-read | section-scan | key-extraction"
   }
   ```

5. **Cross-reference against existing portfolio**: For each
   extracted item, scan existing items for potential relationships.
   This is where the graph grows — extraction is not just ingestion,
   it is integration.

6. **Detect duplicates**: Compare the `core_statement` of each
   extracted item against all existing items. If similarity is
   high, flag as potential duplication (do not auto-merge — present
   to user).

### Extraction Output

Present the extraction results to the user as a structured summary:

```
## Extraction Report: [filename]

### Document registered
- ID: [doc_id]
- Type: [type]
- Pages/sections processed: [count]

### Items extracted: [count]
[For each item: title, type, core_statement, proposed tags]

### New relationships detected: [count]
[For each: source → type → target, with reasoning]

### Potential duplicates: [count]
[For each: extracted item vs existing item, similarity explanation]

### Patterns triggered: [count]
[Any new patterns detected by adding these items to the graph]
```

The user confirms, modifies, or rejects before items are committed.

---

## 2. Incremental Graph Patching

### Principle

The graph is never rebuilt from scratch. It grows through patches.
Each patch is a discrete, logged, reversible set of changes.

### Patch Construction

When any operation modifies the graph, construct a patch object:

1. **Collect all operations** performed in the session:
   - Items added, updated, killed
   - Relationships added, removed, retyped
   - Clusters detected, promoted
   - Merges, splits

2. **Record before/after** for each operation that modifies
   existing state (stage changes, relationship retypes, field
   updates). This enables rollback.

3. **Summarize** the patch in human-readable form.

4. **Append** the patch to the portfolio's `patches` array.

5. **Increment** relevant counters in the session log.

### Patch Application Order

When replaying patches (e.g., after a graph merge or to audit
history), apply in chronological order. Patches are idempotent
by design — applying the same patch twice should not corrupt state
because each operation targets specific IDs and checks preconditions.

### Conflict Resolution During Patching

If a patch operation targets an item that no longer exists (was
killed or merged since the patch was created):

- **node-update on dead item**: Skip, log warning.
- **edge-add to dead item**: Skip, log warning.
- **node-kill on already-dead item**: Skip silently (idempotent).
- **merge involving dead item**: Skip, flag for user.

---

## 3. Graph Merge Protocol

When combining two portfolio state files:

### Step 1: Inventory

List all items from both sources. Identify:
- Items unique to source A
- Items unique to source B
- Items present in both (by ID match)
- Items with different IDs but similar core_statements (potential
  cross-source duplicates)

### Step 2: Resolve Conflicts

For items present in both sources:
- Take the version with the most recent `last_touched`
- Merge histories: interleave by date
- Union relationships (dedup by source+target+type)

For potential cross-source duplicates:
- Present side-by-side to the user
- Offer: merge, keep both, kill one

### Step 3: Rebuild Graph

After merging items:
- Re-run cluster detection on the full graph
- Re-run pattern detection (the merge itself may reveal new
  patterns — especially recurrence across sources)
- Generate a merge patch recording everything

### Step 4: Validate

- Check for dangling references (relationships pointing to
  non-existent items)
- Check for orphaned clusters (clusters whose members were killed)
- Report any anomalies to the user

---

## 4. Diagnostic Analysis Protocol

The **diagnose** operation analyzes the graph structure to surface
patterns, health issues, and actionable recommendations.

### Diagnostic Dimensions

Run these analyses in order:

#### 4a. Duplication Scan

Compare all non-dead items pairwise by `core_statement`.
Flag pairs where the statements express the same idea with
surface variation. Present as merge candidates.

Heuristic: two items are duplication candidates when:
- They share 3+ tags AND their core_statements address the same
  problem, OR
- One item's core_statement is a strict subset of another's

Do NOT flag items that merely address the same *domain* — they
must address the same *specific claim or question*.

#### 4b. Recurrence Detection

Find themes that appear across 3+ independently-created items.
"Independently created" means: different sessions, different
documents, or different source types.

Method:
1. Group items by shared tags (groups of 3+).
2. Within each group, check if items were created independently.
3. If yes, check if `echoes` relationships exist or should exist.
4. Flag as recurrence pattern.

Recurrence is the strongest signal of a core preoccupation. It
means the user's mind keeps returning to this theme even when
not trying to. These deserve concept-level promotion.

#### 4c. Convergence / Divergence Analysis

For each item with 4+ relationships:
- If most relationships are `supports` / `subsumes` inbound:
  check for convergence pattern.
- If most relationships are `contradicts` / `tensions-with`
  outbound: check for divergence pattern.
- If in-degree > 2× portfolio average: flag as gravity well.

#### 4d. Dependency Chain Detection

Find all maximal paths through `depends-on` relationships.
For chains of length 3+:
- Identify the bottleneck (earliest unresolved item).
- Compute how many items are transitively blocked.
- Present the chain with the bottleneck highlighted.

#### 4e. Staleness Analysis

For each cluster:
- Compute the most recent `last_touched` across all members.
- If older than 3 sessions: flag as staleness wave.
- If the cluster contains active items that haven't been
  touched: flag those individually.

For the portfolio as a whole:
- Compute the ratio of raw items to total items.
- If > 40%: the user is ingesting faster than processing.
  Recommend a processing session before more ingestion.

#### 4f. Consolidation Opportunities

Look for sets of items that could be merged or restructured:
- Items in the same cluster with `merges-with` relationships
- Sparks that are subsumed by an existing concept
- References that support only dead items (orphaned references)
- Concepts that have been validated and could be promoted to
  projects

### Diagnostic Output

Present as a structured report:

```
## Portfolio Diagnostic Report
Date: [ISO 8601]
Items analyzed: [count non-dead]
Relationships analyzed: [count]

### Health Indicators
- Processing backlog: [raw count] / [total] ([percentage])
- Orphan items: [count]
- Average cluster size: [number]
- Longest dependency chain: [length] items
- Gravity wells: [count]

### Duplication Candidates ([count])
[For each: item A vs item B, similarity explanation]

### Recurrence Patterns ([count])
[For each: theme, involved items, recommendation]

### Convergence Opportunities ([count])
[For each: converging items, proposed consolidation]

### Divergence Tensions ([count])
[For each: source item, conflicting directions, proposed resolution]

### Dependency Bottlenecks ([count])
[For each: chain, bottleneck item, items blocked]

### Staleness Warnings ([count])
[For each: cluster or item, last touched, recommendation]

### Consolidation Actions ([count])
[For each: what to merge/promote/prune, with reasoning]
```

Each finding includes a recommended action. The user decides
which actions to take. Approved actions become operations in
the session's patch.

---

## 5. Graph Visualization Protocol

### When to Generate

Generate the interactive graph artifact when the user:
- Asks to "see the graph", "show connections", "visualize"
- Completes a diagnose operation (show patterns on the graph)
- Completes an extract operation (show new items in context)
- Asks for "the mosaic", "the big picture", "map my thinking"

### What to Show

The default view shows all non-dead items as nodes, all
relationships as edges, clusters as background regions, and
active patterns as highlights.

Offer filter controls:
- By type (spark/insight/concept/project/reference)
- By stage (raw/processed/validated/active/parked)
- By tag
- By cluster
- By document source
- By pattern involvement

### Interaction Model

The graph artifact supports:
- **Pan and zoom** for navigation
- **Click node** to see item detail (core_statement, tags,
  relationships, provenance, priority signals)
- **Click edge** to see relationship detail (type, note,
  confidence)
- **Click cluster background** to see cluster info
- **Click pattern highlight** to see diagnostic finding
- **Drag node** to manually reposition
- **Filter panel** to show/hide by type, stage, tag

### Layout

Use a force-directed layout (d3-force) with:
- Cluster gravity: items in the same cluster attract
- Type repulsion: same-type nodes spread apart slightly
  (avoids homogeneous clumps)
- Edge length proportional to relationship type:
  - `depends-on`, `subsumes`: short (tight coupling)
  - `supports`, `echoes`: medium
  - `contradicts`, `tensions-with`: long (push apart)
  - `inspired-by`, `extracted-from`: medium-long
