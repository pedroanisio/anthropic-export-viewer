# READ Path — Retrieving Files from Google Drive

## When to Use

Use this path when the user wants to:
- Find a previously saved file
- Resume a session from a prior conversation
- Load memory or preferences
- Reference or continue work on an existing document
- Check whether a file exists in Drive

## Protocol

### 1. Determine What to Search For

Extract search targets from the user's request:

- **Specific file**: name, date, or keywords → use `api_query` with
  `name contains` or `fullText contains`
- **Category of files**: "my reports" → search within `documents/` folder
- **Session resumption**: "where did we leave off" → search for
  `session-index.md` or recent `session-meta.json` files
- **Memory recall**: "what are my preferences" → search for
  `preferences.json` in `_agent/memory/`

### 2. Search Drive

Use `google_drive_search` with the most specific query possible.

**Query construction rules:**

- Start with `api_query` to filter by name, type, or date
- Add `semantic_query` when the user's language is vague or conceptual
- Combine both for best results

**Examples:**

```python
# User says: "find the report I made last week"
google_drive_search(
    api_query="modifiedTime > '2026-03-25' and name contains 'report'",
    semantic_query="report created last week"
)

# User says: "resume my session on project alpha"
google_drive_search(
    api_query="name = 'session-meta.json'",
    semantic_query="project alpha session"
)

# User says: "what did we decide about the API design?"
google_drive_search(
    api_query="name = 'decisions.json'",
    semantic_query="API design decisions"
)
```

### 3. Fetch Content (if Google Doc)

If the search returns a Google Doc (MIME type
`application/vnd.google-apps.document`), extract the document ID from
the result and use `google_drive_fetch`:

```python
google_drive_fetch(document_ids=["extracted-doc-id"])
```

**Important**: `google_drive_fetch` ONLY works with Google Docs. It
does not work with:
- Google Sheets (`application/vnd.google-apps.spreadsheet`)
- Google Slides (`application/vnd.google-apps.presentation`)
- Uploaded PDFs, docx, xlsx, pptx, or any binary file

For non-Doc files, report the metadata (name, link, last modified) and
let the user know you found the file but cannot read its contents
directly. If the user has uploaded the file to the current conversation,
read it from `/mnt/user-data/uploads/` instead.

### 4. Parse and Use the Content

Once you have the content:

- **Session meta**: Parse the JSON, report the session status, and
  reconstruct context from the summary and context_keys.
- **Memory files**: Parse the JSON and apply the stored preferences,
  decisions, or facts to the current conversation.
- **Documents**: Read the content and proceed with whatever the user
  asked (edit, summarize, continue, etc.).

### 5. Handle Missing Files

If the search returns no results:

1. Confirm the search terms with the user — they may have a different
   name or location in mind.
2. Check if the `claude-agent-workspace` folder exists at all. If not,
   this is likely the first time using Drive storage — inform the user
   and offer to initialize the folder structure.
3. Do NOT fabricate content. Say clearly: "I searched Drive for X but
   found no matching files."

## Session Resumption — Full Workflow

When the user says "continue where we left off" or similar:

1. Search for `session-index.md`:
   ```
   api_query: "name = 'session-index.md'"
   semantic_query: "session index agent workspace"
   ```
2. Fetch and parse the index to list recent sessions.
3. If ambiguous, ask the user which session to resume (present the
   session list with dates and summaries).
4. Fetch the selected `session-meta.json`.
5. Load the context: summary, context_keys, artifact list.
6. Report to the user: "Resuming session '{session_id}'. Last active
   on {updated}. Context: {summary}."
7. If the session has artifacts, search for them and report their
   availability.
