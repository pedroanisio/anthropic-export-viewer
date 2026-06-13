---
name: response-dispatch
description: >
  Decide whether a task requires code execution + file/command operations
  (Execution Path), an inline rendered widget/artefact (Artefact Path), or
  a direct streamed text response (Text Path). Use this skill at the START
  of every non-trivial response where the right output modality is not
  immediately obvious. Trigger on any task that involves: producing files,
  running computations, transforming data, building UIs, making API calls,
  writing scripts, creating documents - OR on analysis/explanation/design/
  advice tasks where it is unclear whether artefacts are needed. Also trigger
  when the user says things like "create", "build", "generate", "make me",
  "run", "process", "convert", "fix", "analyse", "explain", "plan",
  "compare", "show me", or "write". Do NOT skip this skill just because the
  request feels "simple" - under-routing is the primary failure mode.
---

# Response Dispatch

A routing layer that runs **once**, at the start, before generating any output.
It produces exactly one decision from four possible outcomes:

| Path | Symbol | When |
|---|---|---|
| **Text Path** | `[T]` | Answer is prose/markdown, streamed inline |
| **Artefact Path** | `[A]` | Output is an interactive or visual widget rendered in the chat |
| **Execution Path** | `[E]` | Output requires tools, code execution, or produces a downloadable file |
| **Clarify First** | `[C]` | Ambiguity is high enough that proceeding would waste effort or produce the wrong thing |

Work through the gates in order. **First gate that fires wins.** Stop immediately.

---

## Gate 0 — Clarify First `[C]`

Ask a single focused clarifying question **before dispatching** if ALL of the
following are true:

1. The request names an output type that has multiple plausible forms
   (e.g. "a report" could mean inline markdown, a Word doc, or a dashboard).
2. Getting it wrong would cost more than asking (long execution tasks, binary
   file generation, complex multi-step workflows).
3. No prior message in the conversation resolves the ambiguity.

**Do not ask** if the answer can be reasonably inferred from context, from the
user's tool choices already visible in the conversation, or from stated
preferences. Defaulting and noting the assumption is almost always better
than blocking with a question.

> **Rule:** One question maximum. If you'd need two questions to disambiguate,
> default to the most common interpretation and state your assumption.

---

## Gate 1 — Hard Execution Signals `[E]`

Choose **Execution Path** immediately if ANY of the following is true:

1. The output is a **downloadable file** of any kind:
   `.docx`, `.xlsx`, `.pptx`, `.pdf`, `.png`, `.jpg`, `.svg` (saved),
   `.csv`, `.zip`, `.json` (saved), any code file the user wants to keep.
2. The task requires **running code** whose output is the deliverable:
   data transformation, computation, parsing, rendering a static image,
   running tests, executing a script.
3. The task involves **reading an uploaded or binary file** whose content is
   NOT already visible in context (check for a `documents` block or inline
   text — if absent, the file must be read via tools).
4. The task requires **external tool/MCP calls** that assemble structured data
   into the response: Drive fetch, calendar query, sending email, posting to
   Slack, querying a database, calling an API endpoint.
5. The task is a **multi-step workflow** where intermediate outputs gate later
   steps: "parse → filter → chart", "read PDF → summarise → email".
6. The user says **"save"**, **"download"**, **"export"**, **"as a file"**,
   **"I want to keep this"**, **"send it to me"**.

---

## Gate 2 — Hard Artefact Signals `[A]`

Choose **Artefact Path** if the output should **render interactively inside the
chat window** and does NOT need to be saved as a file. This path uses
`visualize:show_widget` (React/HTML) or inline SVG.

Choose `[A]` if ANY of the following is true, AND Gate 1 did not fire:

1. The request is for a **chart, graph, or data visualisation** where the user
   wants to see and interact with it (not download it).
2. The request is for an **interactive UI component**: calculator, quiz, game,
   form, simulator, kanban board, timer, converter.
3. The request is for a **diagram** (flowchart, architecture, ERD, sequence)
   that benefits from being rendered rather than described in text.
4. The request is for a **dashboard** displaying metrics, tables, or progress
   where interactivity adds value over a static list.
5. The request is for a **React component or HTML snippet** that the user wants
   to see rendered — not just the source code inline.

> **`[A]` vs `[E]` distinction:** If the user says "build me a React component"
> and wants to see it working → `[A]`. If they say "create the `.jsx` file" or
> "save it" → `[E]`. When ambiguous, prefer `[A]` (lower cost, immediate
> feedback), then offer to package as a file if needed.

---

## Gate 3 — Hard Text Signals `[T]`

Choose **Text Path** if ALL of the following are true:

1. The answer is **knowledge, analysis, explanation, or advice** that could be
   written from training knowledge (possibly with web grounding).
2. The entire response fits in **~2–3 screenfuls** (≈ 800–1 200 words) or is a
   short code snippet (≤ 20 lines, no execution needed).
3. No file, rendered widget, or tool result is needed to assemble the answer.
4. The user is asking a **question**, requesting **feedback**, or wants a
   **plan / recommendation** — not a built thing.

---

## Gate 4 — Ambiguous Cases

When Gates 0–3 leave the decision open, apply this table.

| Scenario | Decision | Rationale |
|---|---|---|
| "Write a blog post about X" | `[T]` (inline markdown) | Text is the deliverable |
| "Write a blog post and save it as a Word doc" | `[E]` | File output → Gate 1 |
| "Explain how X works" | `[T]` | Explanation = prose |
| "Show me a diagram of X" | `[A]` | Visual output, render inline |
| "Show me a diagram and export it as SVG" | `[E]` | Save → Gate 1 |
| "Analyse this dataset" (file attached, not in context) | `[E]` | Must read file via tools |
| "Analyse this dataset" (data pasted inline, short) | `[T]` or `[A]` | Interpretation only → `[T]`; chart → `[A]` |
| "Write a SQL query for X" (short, conceptual) | `[T]` (inline code block) | ≤ 20 lines, no execution |
| "Run this SQL against my DB" | `[E]` | Execution required |
| "Fix my code" (file attached) | `[E]` | Must read + return corrected file |
| "Fix my code" (snippet inline, ≤ 40 lines) | `[T]` | Inline edit is sufficient |
| "Compare A and B" (both concepts) | `[T]` | Conceptual = prose |
| "Compare A and B" (both uploaded files) | `[E]` | Must read files |
| "Build a React component" (show me working) | `[A]` | Render inline first |
| "Build a React component" (give me the file) | `[E]` | File requested |
| "Quick React snippet" (≤ 20 lines) | `[T]` | Inline code block |
| "Create a presentation on X" | `[E]` (via `pptx` skill) | `.pptx` = file |
| "Show me a slide layout" | `[A]` | Visual preview, no file |
| "Summarise this article" (URL given) | `[T]` after `web_fetch` | Fetch is grounding; output is prose |
| "Make me a dashboard for X" | `[A]` | Interactive = widget |
| "Make me a dashboard and save it" | `[E]` | Save → Gate 1 |
| Long creative writing > 1 500 chars | `[E]` (`.md` artefact) | Long-form = persistent file |
| Short creative writing (poem, paragraph) | `[T]` | Fits inline |
| "Draw a chart from this data" (data inline) | `[A]` | Render inline |
| "Give me a chart as a PNG" | `[E]` | File output |
| "What does this image show?" (image in context) | `[T]` | Vision is grounding; output is prose |
| "Edit this image and give it back" | `[E]` | File transformation |

---

## Hybrid Responses

Some tasks are legitimately two-phase. Handle them as:

```
Phase 1 → [T] grounding  (web_search / web_fetch / Drive lookup)
Phase 2 → [E] or [A]     using the grounded data
```

Examples:
- "Research competitor pricing and put it in a spreadsheet" → search first `[T]`, then build xlsx `[E]`
- "Find our Q3 report and visualise the revenue trend" → Drive fetch `[E]` + chart widget `[A]`

For hybrids: complete Phase 1 inline (brief summary of findings), then proceed to Phase 2 without asking again. Do not create a file from Phase 1 alone unless explicitly asked.

---

## Tie-Breaker

When still ambiguous after Gate 4:

> **"Is the thing the user wants the text itself, or is the text a step toward something else?"**

- Text is the deliverable → `[T]`
- Text feeds a visual → `[A]`
- Text feeds a file or computation → `[E]`

**Cost order:** `[T]` < `[A]` < `[E]` in both latency and risk. When two paths are equally valid, choose the cheaper one and note the assumption. Offer the alternative at the end of the response.

---

## Dispatch Output Format

State the decision once, concisely. Place it in your **thinking block** or as a
one-line silent preamble. Never as a verbose paragraph that delays the response:

```
[DISPATCH → T]  Reason: conceptual explanation, no artefact needed.
[DISPATCH → A]  Reason: interactive chart requested, no save needed.
[DISPATCH → E]  Reason: .xlsx output requested.
[DISPATCH → C]  Question: "Do you want this as an inline preview or a .pptx file to keep?"
```

---

## Path Entry Checklists

### `[T]` Text Path

- [ ] Check user formatting preferences: prose > bullets unless content is list-shaped
- [ ] Is web grounding needed? If topic may have changed post-cutoff → `web_search` first
- [ ] Will the response exceed ~1 500 chars of creative/structured content? If yes → reconsider `[E]` for a `.md` artefact
- [ ] Code blocks: inline only if ≤ 20 lines and no execution needed
- [ ] No excessive headers — use conversational tone unless content is document-shaped

### `[A]` Artefact Path

- [ ] Call `visualize:read_me` first with the relevant module (`chart`, `diagram`, `interactive`, `data_viz`, `art`, `mockup`)
- [ ] Use Tailwind core utilities only for React (no JIT compiler available)
- [ ] `localStorage` / `sessionStorage` are NOT supported in claude.ai — use `useState` / `useReducer`
- [ ] Default export required for React components; no required props without defaults
- [ ] Available libraries: `recharts`, `lucide-react@0.383.0`, `d3`, `three` (r128), `lodash`, `mathjs`, `shadcn/ui`, `Tone`, `tensorflow`
- [ ] After rendering, offer to package as a downloadable file if the user might want to keep it
- [ ] Single-file output: CSS and JS inline, no separate files

### `[E]` Execution Path

- [ ] **Scan `available_skills`** — is there a skill for this output type? (see Skill-Chaining Map below)
  - If a relevant skill exists: **read its SKILL.md via `view` before writing any code**
- [ ] All deliverables go to `/mnt/user-data/outputs/`
- [ ] Python packages: always `pip install <pkg> --break-system-packages`
- [ ] For iterative file builds (> 100 lines): use outline → fill section by section → review → finalise
- [ ] After completing: call `present_files` with the output path(s)
- [ ] Do NOT use `bash_tool` to `echo` or `cat` content that could be written inline

---

## Skill-Chaining Map

When `[E]` is chosen and an output-type skill exists, chain to it immediately:

| Output type | Downstream skill | Read path |
|---|---|---|
| `.docx` | `docx` | `/mnt/skills/public/docx/SKILL.md` |
| `.pptx` | `pptx` | `/mnt/skills/public/pptx/SKILL.md` |
| `.xlsx` | `xlsx` | `/mnt/skills/public/xlsx/SKILL.md` |
| `.pdf` (create/fill) | `pdf` | `/mnt/skills/public/pdf/SKILL.md` |
| `.pdf` / binary (read/extract) | `pdf-reading` | `/mnt/skills/public/pdf-reading/SKILL.md` |
| Uploaded unknown file | `file-reading` | `/mnt/skills/public/file-reading/SKILL.md` |
| Web/UI component (styled) | `frontend-design` | `/mnt/skills/public/frontend-design/SKILL.md` |
| Visual poster / static art | `canvas-design` | `/mnt/skills/examples/canvas-design/SKILL.md` |
| Codebase analysis | `conceptual-codebase-analysis` | `/mnt/skills/user/conceptual-codebase-analysis/SKILL.md` |
| Document revision (multi-round) | `redaction-reconciliation` | `/mnt/skills/user/redaction-reconciliation/SKILL.md` |
| Video/animation script | `visual-explainer` | `/mnt/skills/user/visual-explainer/SKILL.md` |

When no downstream skill exists for the output type: proceed with `bash_tool` + `create_file` directly.

---

## Common Mistakes

| Mistake | Correct behaviour |
|---|---|
| Creating a `.docx` for a short memo no one asked to save | `[T]` inline markdown |
| Answering "build me a dashboard" with prose | `[A]` widget |
| Using `bash_tool` to echo text that fits inline | Skip the tool entirely |
| Streaming a 3 000-word essay inline | `[E]` → `.md` artefact |
| Skipping skill lookup before file generation | Always check `available_skills` for `[E]` tasks |
| Treating every code block as needing execution | Snippets ≤ 20 lines → `[T]` inline |
| Producing a React file when user wants to see it running | `[A]` first, offer file after |
| Asking two clarifying questions | One max; default + state assumption otherwise |
| Dispatching `[E]` for "compare two concepts" | `[T]` — no tools needed |
| Using `localStorage` in a React artefact | Use `useState`; `localStorage` throws in claude.ai |
| Running `pip install` without `--break-system-packages` | Always append the flag |
| Forgetting `present_files` after file creation | Required — user cannot see output otherwise |

---

## References

- `references/signal-catalogue.md` — Extended verb/format/length/integration signal map for Gate 4 edge cases
