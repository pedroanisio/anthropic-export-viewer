# Portfolio State Schema

This document defines the JSON structure for persisting the idea
portfolio, its graph state, document registry, patch history, and
diagnostic results. The state file is the single source of truth.

---

## Top-Level Schema

```json
{
  "portfolio": {
    "version": "2.0.0",
    "owner": "<user identifier or alias>",
    "created": "<ISO 8601>",
    "last_triage": "<ISO 8601 or null>",
    "triage_count": 0,
    "items": [],
    "clusters": [],
    "documents": [],
    "patches": [],
    "patterns": [],
    "session_log": []
  }
}
```

---

## Item Schema

```json
{
  "id": "<ULID>",
  "title": "<concise label, max 80 chars>",
  "type": "spark | insight | concept | project | reference",
  "stage": "raw | processed | validated | active | parked | dead",
  "created": "<ISO 8601>",
  "last_touched": "<ISO 8601>",
  "raw_input": "<original text, preserved verbatim>",
  "core_statement": "<one sentence in problem-language>",
  "tags": ["<freeform>"],
  "provenance": {
    "source_type": "manual | document | web | derived | merged",
    "document_id": "<if source_type is document>",
    "page_or_section": "<location within document>",
    "url": "<if source_type is web>",
    "source_item_ids": ["<if derived or merged>"],
    "extraction_method": "full-read | section-scan | key-extraction | cross-reference",
    "session_id": "<session date or identifier>"
  },
  "relationships": [
    {
      "target_id": "<id>",
      "type": "supports | contradicts | subsumes | depends-on | inspired-by | merges-with | echoes | tensions-with | extracted-from",
      "note": "<why this relationship exists>",
      "confidence": "strong | tentative",
      "created": "<ISO 8601>"
    }
  ],
  "priority_signals": {
    "urgency": "none | low | high | critical",
    "energy_match": "draining | neutral | energizing",
    "leverage": 0,
    "novelty_decay": "stable | slow-decay | fast-decay",
    "feasibility": "blocked | constrained | clear",
    "conviction": "low | medium | high"
  },
  "next_action": "<concrete next step, or null>",
  "park_trigger": "<reactivation condition, or null>",
  "kill_reason": "<why killed, or null>",
  "history": [
    {
      "date": "<ISO 8601>",
      "event": "created | promoted | demoted | linked | triaged | parked | killed | revived | merged | split | extracted | retagged",
      "detail": "<what happened>"
    }
  ]
}
```

---

## Document Registry Entry

```json
{
  "document_id": "<ULID>",
  "filename": "<original filename>",
  "type": "pdf | md | txt | docx | html | csv | image",
  "processed_date": "<ISO 8601>",
  "content_hash": "<SHA-256>",
  "pages_or_sections": "<count or descriptive list>",
  "items_extracted": ["<item ids>"],
  "extraction_summary": "<brief: what was found and extracted>"
}
```

The `content_hash` is used to detect duplicate uploads. If a user
uploads a document whose hash matches an existing registry entry,
warn them and ask whether to re-process or skip.

---

## Cluster Schema

```json
{
  "id": "<ULID>",
  "label": "<emergent theme name>",
  "member_ids": ["<item id>"],
  "detected": "<ISO 8601>",
  "promoted_to": "<item id if became a concept, else null>",
  "strength": "<number of cross-member relationships>"
}
```

---

## Patch Schema

A patch is the atomic unit of graph evolution. Every session that
modifies state produces exactly one patch.

```json
{
  "patch_id": "<ULID>",
  "date": "<ISO 8601>",
  "summary": "<human-readable: what this patch did>",
  "operations": [
    {
      "op": "node-add | node-update | node-kill | edge-add | edge-remove | edge-retype | cluster-detect | cluster-promote | merge | split | graph-merge",
      "target_ids": ["<affected item/cluster ids>"],
      "detail": "<specifics of the change>",
      "before": "<previous value, for reversibility>",
      "after": "<new value>"
    }
  ],
  "items_added": 0,
  "items_killed": 0,
  "edges_added": 0,
  "edges_removed": 0,
  "patterns_detected": ["<pattern type>"]
}
```

### Patch Diffing

To compute a diff between two states, compare the last N patches.
The diff output structure:

```json
{
  "from_patch": "<patch_id>",
  "to_patch": "<patch_id>",
  "nodes_added": [],
  "nodes_removed": [],
  "nodes_modified": [],
  "edges_added": [],
  "edges_removed": [],
  "clusters_formed": [],
  "clusters_dissolved": [],
  "patterns_emerged": [],
  "patterns_resolved": []
}
```

---

## Pattern Record

When a pattern is detected during a **diagnose** operation, it is
recorded here. Patterns can be `active` (still present), `resolved`
(user acted on it), or `dismissed` (user acknowledged but chose not
to act).

```json
{
  "pattern_id": "<ULID>",
  "type": "recurrence | duplication | convergence | divergence | dependency-chain | orphan-cluster | gravity-well | staleness-wave",
  "detected": "<ISO 8601>",
  "status": "active | resolved | dismissed",
  "involved_items": ["<item ids>"],
  "description": "<what was detected and why it matters>",
  "recommended_action": "<specific action from taxonomy>",
  "resolution": "<what was done, if resolved>"
}
```

---

## Session Log Entry

```json
{
  "date": "<ISO 8601>",
  "type": "ingest | triage | prune | review | relate | extract | diagnose | graph-patch | graph-merge",
  "summary": "<what happened>",
  "items_affected": ["<item id>"],
  "documents_processed": ["<document_id>"],
  "decisions": ["<key decision>"],
  "patch_id": "<associated patch>"
}
```

---

## File Conventions

- **Filename**: `portfolio-state.json`
- **Backup**: Before destructive ops: `portfolio-state.backup-<ISO-date>.json`
- **Output**: Always write updated state to `/mnt/user-data/outputs/`
- **First session**: If no state file uploaded, create empty portfolio.
- **Persistent storage key**: `portfolio-state` (shared: false) for
  React artifact persistence via `window.storage` API.

---

## Graph Visualization Data

For the React graph artifact, the portfolio state is projected into
a visualization-ready structure:

```json
{
  "nodes": [
    {
      "id": "<item id>",
      "label": "<title>",
      "type": "<item type>",
      "stage": "<maturity stage>",
      "tags": [],
      "cluster_id": "<cluster id or null>",
      "in_degree": 0,
      "out_degree": 0,
      "leverage": 0,
      "provenance_type": "<source type>"
    }
  ],
  "edges": [
    {
      "source": "<item id>",
      "target": "<item id>",
      "type": "<relationship type>",
      "confidence": "strong | tentative"
    }
  ],
  "clusters": [
    {
      "id": "<cluster id>",
      "label": "<theme>",
      "member_ids": []
    }
  ],
  "patterns": [
    {
      "type": "<pattern type>",
      "involved_ids": [],
      "status": "active | resolved | dismissed"
    }
  ]
}
```

### Visual Encoding

The graph artifact encodes meaning through visual properties:

**Node shape by type:**
- spark: small circle
- insight: diamond
- concept: rounded rectangle
- project: rectangle
- reference: triangle

**Node color by stage:**
- raw: gray
- processed: blue
- validated: teal
- active: green
- parked: amber
- dead: faded/transparent

**Edge style by relationship:**
- supports: solid green
- contradicts: dashed red
- subsumes: thick dark gray
- depends-on: dotted orange
- inspired-by: thin light blue
- merges-with: double-line purple
- echoes: wavy cyan (recurrence signal)
- tensions-with: dashed amber
- extracted-from: dotted gray (provenance)

**Edge width by confidence:**
- strong: 2px
- tentative: 1px, lower opacity

**Cluster visualization:**
- Convex hull or background shading grouping cluster members
- Cluster label floating above the group

**Pattern highlighting:**
- Active patterns get a pulsing highlight on involved nodes
- Gravity wells get a size increase proportional to in-degree
- Dependency chains get a sequential highlight animation
