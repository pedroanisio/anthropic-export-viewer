# Folder Schema & Naming Conventions

## Drive Folder Hierarchy

All agent-generated content lives under a single root folder in the
user's Google Drive. The default root name is `claude-agent-workspace`.

```
claude-agent-workspace/
│
├── _agent/                          ← internal agent data
│   ├── sessions/                    ← session state and history
│   │   ├── session-index.md         ← master session index
│   │   └── {date}_{slug}/           ← per-session folder
│   │       ├── session-meta.json
│   │       └── artifacts/
│   ├── memory/                      ← persistent memory store
│   │   ├── memory-index.md
│   │   ├── preferences.json
│   │   ├── decisions.json
│   │   └── facts.json
│   └── logs/                        ← audit trail (optional)
│       └── {date}_operations.jsonl
│
├── documents/                       ← reports, memos, letters
│   └── {date}_{slug}.{ext}
│
├── spreadsheets/                    ← data files, analyses
│   └── {date}_{slug}.{ext}
│
├── presentations/                   ← slide decks
│   └── {date}_{slug}.{ext}
│
├── code/                            ← scripts, components, apps
│   └── {project-slug}/
│       └── {files}
│
├── data/                            ← raw data, CSVs, JSON
│   └── {date}_{slug}.{ext}
│
├── exports/                         ← PDFs, rendered outputs
│   └── {date}_{slug}.pdf
│
└── scratch/                         ← temporary, low-importance files
    └── {anything}
```

## Naming Rules

| Rule | Convention | Example |
|---|---|---|
| Date prefix | ISO 8601 date, no time | `2026-04-01` |
| Slug | Lowercase, hyphens, no spaces | `quarterly-report` |
| Combined | `{date}_{slug}.{ext}` | `2026-04-01_quarterly-report.docx` |
| Session folder | `{date}_{slug}/` | `2026-04-01_project-alpha/` |
| No special chars | Only `a-z`, `0-9`, `-`, `_`, `.` | — |

## Searching with the Schema

When searching for files, use the folder schema to build targeted
queries with `google_drive_search`:

```
# Find a specific document
api_query: "name contains 'quarterly-report' and mimeType = 'application/vnd.google-apps.document'"
semantic_query: "quarterly report Q2 2026"

# Find all session metadata
api_query: "name = 'session-meta.json'"
semantic_query: "active sessions"

# Find files in the workspace root
api_query: "name contains 'claude-agent-workspace' and mimeType = 'application/vnd.google-apps.folder'"

# Find recent documents
api_query: "modifiedTime > '2026-03-01' and name contains '2026-'"
semantic_query: "recent agent-generated documents"
```

## Category Routing

When creating a file, determine its category from the output type:

| Output type | Folder | Extension |
|---|---|---|
| Report, memo, letter, article | `documents/` | `.docx` or `.md` |
| Spreadsheet, data analysis | `spreadsheets/` | `.xlsx` or `.csv` |
| Presentation, deck | `presentations/` | `.pptx` |
| Script, component, application | `code/{project}/` | `.ts`, `.py`, etc. |
| Raw data, import/export | `data/` | `.csv`, `.json`, `.xml` |
| Rendered PDF | `exports/` | `.pdf` |
| Temporary, one-off | `scratch/` | any |
| Session state | `_agent/sessions/` | `.json`, `.md` |
| Memory entries | `_agent/memory/` | `.json`, `.md` |
