---
name: gdrive-storage
description: >
  Route all AI-agent-generated files, memory, session data, and outputs to
  Google Drive as the primary persistent storage backend. Trigger on: "save
  to Drive", "upload to Drive", "store in Drive", "find my file", "resume
  session", "load my memory", "where did we leave off", "sync to Drive",
  "persist this", "save my work", or any request to create a durable file.
  Also trigger when the user mentions "Google Drive", "Drive folder", "my
  Drive", or references a Drive URL. Trigger proactively when creating any
  output file — Drive is the default, not the ephemeral local filesystem.
  If the user says "save", "keep", "store", "remember", or "don't lose
  this", use this skill. Even "create a report" without specifying where
  triggers this skill because Drive is the configured default.
---

# Google Drive as Primary Agent Storage

This skill makes Google Drive the canonical, persistent storage layer for
all AI-agent-generated artifacts. The local container filesystem is
ephemeral — it resets between sessions. Drive does not.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│                  User Request                    │
└──────────────────────┬──────────────────────────┘
                       │
              ┌────────▼────────┐
              │  Dispatch Layer  │
              │  (this skill)    │
              └────────┬────────┘
                       │
         ┌─────────────┼─────────────┐
         │             │             │
    ┌────▼────┐  ┌─────▼─────┐ ┌────▼────┐
    │  READ   │  │   WRITE   │ │  INDEX  │
    │ (fetch) │  │ (create)  │ │(search) │
    └────┬────┘  └─────┬─────┘ └────┬────┘
         │             │             │
    google_drive  local build   google_drive
    _fetch        + present     _search
                  + user sync
```

There are two operational paths and one index path. Read the appropriate
reference file before executing:

- **READ path** → `references/read-path.md`
- **WRITE path** → `references/write-path.md`
- **Folder schema & naming** → `references/folder-schema.md`

---

## Tooling Inventory — What Exists and What Does Not

Be honest about capabilities. Do not hallucinate tools that do not exist.

### Available Now (built-in)

| Tool | Direction | What it does |
|---|---|---|
| `google_drive_search` | READ | Search files by name, content, MIME type, folder, date, owner |
| `google_drive_fetch` | READ | Fetch full content of a Google Doc by document ID |
| `present_files` | WRITE (local) | Make a locally-created file visible and downloadable to the user |

### Available via MCP Registry (requires user to connect)

| Server | UUID | Status |
|---|---|---|
| Google Drive MCP | `37fb5d42-ef62-4 5d4-a12e-66551527a003` | **Not connected** — suggest connection when write operations are needed |

### Not Available

- There is **no built-in tool** that directly creates or uploads files
  into Google Drive from the container.
- The `google_drive_fetch` tool only reads Google Docs (not Sheets,
  Slides, PDFs, or binary files stored in Drive).

This asymmetry (read-capable, write-limited) is a real constraint. The
skill works around it — see the WRITE path reference.

---

## Decision Flow

Run this flow at the start of any task involving persistence.

### Step 1 — Does the task involve a persistent artifact?

If the output is a file, dataset, report, session log, memory entry,
or anything the user may want to access later: **yes → continue**.
If the task is purely conversational (no artifact): **stop, no storage
needed**.

### Step 2 — Is this a READ or a WRITE?

- **READ**: User wants to find, open, resume, or reference an existing
  file in Drive → go to READ path.
- **WRITE**: User wants to create, update, or persist a new artifact →
  go to WRITE path.
- **BOTH**: User wants to read something from Drive, modify it, and save
  it back → execute READ then WRITE sequentially.

### Step 3 — Execute the appropriate path

Read the corresponding reference file and follow its protocol.

---

## READ Path (Summary)

1. Use `google_drive_search` with the folder schema conventions to
   locate the file.
2. If the file is a Google Doc, use `google_drive_fetch` with the
   document ID.
3. If the file is not a Google Doc (PDF, xlsx, etc.), inform the user
   of its location and metadata — the content cannot be fetched
   directly.
4. For session/memory resumption, search for the session index doc
   in the `_agent/sessions/` folder.

Full protocol: `references/read-path.md`

---

## WRITE Path (Summary)

1. Build the file locally in `/home/claude/` using the appropriate
   skill (docx, xlsx, pptx, pdf, etc.).
2. Name the file according to the folder schema conventions.
3. Copy to `/mnt/user-data/outputs/` and call `present_files`.
4. **Attempt automated upload**: Check if the Google Drive MCP is
   connected. If yes, use it. If no, suggest the user connect it
   via the MCP registry.
5. **Fallback — manual sync**: Tell the user the file is ready for
   download and provide the target Drive folder path where it
   should be placed.

Full protocol: `references/write-path.md`

---

## Session & Memory Persistence

Agent sessions and memory are stored as structured Markdown or JSON
files in Drive under the `_agent/` folder hierarchy.

### Session Files

A session captures the state of an ongoing multi-turn workflow.

```
_agent/sessions/
├── session-index.md          ← master index of all sessions
├── 2026-04-01_project-alpha/ ← one folder per session
│   ├── session-meta.json     ← status, timestamps, context summary
│   └── artifacts/            ← files produced during the session
└── ...
```

**session-meta.json schema:**

```json
{
  "session_id": "2026-04-01_project-alpha",
  "status": "active | paused | completed",
  "created": "2026-04-01T14:30:00Z",
  "updated": "2026-04-01T16:45:00Z",
  "summary": "Brief description of what this session is about",
  "context_keys": ["project-alpha", "quarterly-report", "Q2-2026"],
  "artifacts": [
    {
      "name": "q2-report-draft.docx",
      "type": "docx",
      "drive_path": "_agent/sessions/2026-04-01_project-alpha/artifacts/"
    }
  ]
}
```

### Memory Files

Memory entries are long-lived facts, preferences, or decisions the
user wants the agent to retain across sessions.

```
_agent/memory/
├── memory-index.md    ← master index
├── preferences.json   ← user preferences and defaults
├── decisions.json     ← recorded decisions with rationale
└── facts.json         ← factual context the user has provided
```

To resume a session or load memory, search Drive for the index files
first, then fetch the relevant entries.

---

## Critical Rules

1. **Drive is the source of truth.** If a file exists in Drive and
   a different version exists locally, the Drive version is
   authoritative unless the user explicitly says otherwise.

2. **Never silently discard.** If a file cannot be uploaded to Drive
   (MCP not connected, error, etc.), always inform the user and
   provide the local download. Never let work vanish.

3. **Name files predictably.** Follow the folder schema. Timestamps
   in ISO 8601. No spaces in filenames — use hyphens.

4. **Suggest MCP connection when needed.** If the user attempts a
   write operation and the Google Drive MCP is not connected, use
   `suggest_connectors` with UUID
   `37fb5d42-ef62-45d4-a12e-66551527a003` to prompt connection.

5. **Do not fabricate Drive capabilities.** If a tool does not exist,
   say so. Provide the manual workaround. Do not pretend the file
   was uploaded when it was only saved locally.

6. **Respect the read-only constraint.** `google_drive_fetch` only
   works with Google Docs. For other file types found via search,
   report metadata (name, ID, URL, modified date) but do not claim
   to have read the content unless you actually have it.
