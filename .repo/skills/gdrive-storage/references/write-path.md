# WRITE Path — Persisting Files to Google Drive

## When to Use

Use this path when the user wants to:
- Save a newly created file to Drive
- Update an existing file with new content
- Persist session state for later resumption
- Store a memory entry (preference, decision, fact)
- Export any artifact for long-term storage

## The Write Constraint

There is no built-in tool that directly creates files in Google Drive
from the container. This is a real limitation. The skill works around
it through a layered fallback strategy.

## Protocol

### 1. Build the File Locally

Use the appropriate skill to create the file:

- `docx` skill → Word documents
- `xlsx` skill → Spreadsheets
- `pptx` skill → Presentations
- `pdf` skill → PDFs
- `create_file` tool → Markdown, JSON, code, plain text

Create the file in `/home/claude/` as a working directory.

### 2. Name According to Schema

Apply the folder schema naming convention:

```
{date}_{slug}.{ext}
```

Example: `2026-04-01_quarterly-report.docx`

For session files: `session-meta.json` inside a dated session folder.
For memory files: `preferences.json`, `decisions.json`, `facts.json`.

### 3. Present the File Locally

Copy the file to `/mnt/user-data/outputs/` and call `present_files`.
This ensures the user can always download the file regardless of
whether Drive upload succeeds.

### 4. Attempt Drive Upload — Layered Strategy

Try each layer in order. Stop at the first success.

#### Layer A: Google Drive MCP (preferred)

Check if the Google Drive MCP server is connected. If connected and
its tools include a create/upload capability, use it.

If NOT connected, use `suggest_connectors` to prompt the user:

```python
suggest_connectors(
    uuids=["37fb5d42-ef62-45d4-a12e-66551527a003"],
    keywords=["drive"]
)
```

Tell the user:
> "To enable automatic upload to Google Drive, you can connect the
> Google Drive integration. I've suggested it below. Once connected,
> future files will sync automatically."

Then proceed to Layer B as the immediate fallback.

#### Layer B: Manual User Sync (reliable fallback)

Provide the user with:
1. The downloadable file (already presented via `present_files`).
2. The exact target path in Drive where it should be placed.
3. Clear instructions.

Template:

```
📁 File ready: {filename}
📂 Target Drive path: claude-agent-workspace/{category}/{filename}

To persist this file:
1. Download it using the link above.
2. In Google Drive, navigate to (or create) the folder:
   claude-agent-workspace/{category}/
3. Upload the file there.

Alternatively, connect the Google Drive integration for automatic
uploads in future sessions.
```

#### Layer C: Google Doc Creation via Search Workaround (text content only)

For plain-text or Markdown content that needs to be stored as a Google
Doc (e.g., session indexes, memory files), the user can:

1. Create a new Google Doc manually in the target folder.
2. Paste the content provided inline in the chat.

Offer this option when the content is short and text-based. Provide the
full content formatted for easy copy-paste.

### 5. Update the Session Index (if applicable)

When creating a session or memory file, also generate the updated
index content. If the index already exists in Drive (found via search),
provide the diff or replacement content. If it does not exist, provide
the full initial index.

**Session index template (session-index.md):**

```markdown
# Agent Session Index

Last updated: {ISO timestamp}

## Active Sessions

| Session ID | Status | Created | Summary |
|---|---|---|---|
| {id} | {status} | {date} | {summary} |

## Completed Sessions

| Session ID | Completed | Summary |
|---|---|---|
```

**Memory index template (memory-index.md):**

```markdown
# Agent Memory Index

Last updated: {ISO timestamp}

## Stored Entries

| File | Type | Last Modified | Description |
|---|---|---|---|
| preferences.json | preferences | {date} | User preferences and defaults |
| decisions.json | decisions | {date} | Recorded decisions with rationale |
| facts.json | facts | {date} | Factual context from user |
```

### 6. Confirm to the User

Always close the write path with a clear status report:

```
✅ File created: {filename}
📥 Available for download: yes
☁️  Drive upload: {succeeded | pending user action | MCP not connected}
📂 Target path: claude-agent-workspace/{category}/{filename}
```

Never say "saved to Drive" if the file was only saved locally. The
distinction matters.

## Updating Existing Files

When modifying a file that already exists in Drive:

1. Fetch the current version (READ path).
2. Apply modifications locally.
3. Present the updated file.
4. Instruct the user to replace the old version in Drive, or use the
   MCP if connected.
5. Note in the status that this is an **update**, not a new file.

## Batch Operations

When multiple files are created in one session (e.g., a report + its
data source + a presentation):

1. Create all files locally.
2. Present all files in a single `present_files` call.
3. Provide a batch manifest listing all files and their target Drive
   paths.
4. Suggest MCP connection once (not per file).
