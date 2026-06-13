# Signal Catalogue — Extended Trigger → Path Mappings

Used by `response-dispatch` when Gate 4 (ambiguous cases) is insufficient.
Paths: `[T]` Text · `[A]` Artefact (inline widget) · `[E]` Execution (file/tools) · `[C]` Clarify

---

## 1. Verb-based signals

| Verb / phrase | Default path | Override condition |
|---|---|---|
| "create", "make", "build", "generate" | `[E]` | + "a plan / outline / explanation" → `[T]`; + "show me" → `[A]` |
| "write" | `[T]` (inline) | + "save / download / as a .X file" → `[E]` |
| "show me", "display", "render", "visualise" | `[A]` | + "save / export / as a file" → `[E]`; conceptual ("show me how X works") → `[T]` |
| "explain", "describe", "summarise" | `[T]` | + "from this attached file" → `[E]` (must read file) |
| "analyse", "analyze" | `[T]` (inline data) / `[E]` (file attached) | + chart/table output requested → `[A]` or `[E]` |
| "compare" | `[T]` (concepts) / `[E]` (files) | — |
| "fix", "debug", "refactor" | `[T]` if ≤ 40 lines inline; `[E]` if file attached | — |
| "run", "execute", "test" | `[E]` | — |
| "convert", "transform", "export" | `[E]` | — |
| "plan", "design", "outline" | `[T]` | + "and save it" → `[E]` |
| "give me", "tell me" | `[T]` | + "a file / script / component" → `[E]` or `[A]` |
| "draft" | `[T]` | + "as a Word doc / .docx" → `[E]` |
| "draw", "chart", "plot", "graph" | `[A]` | + "as PNG / SVG / file" → `[E]` |
| "build a form / calculator / game / quiz" | `[A]` | + "save it / give me the file" → `[E]` |
| "animate", "make it interactive" | `[A]` | — |

---

## 2. Output-format signals

| Output mentioned | Path |
|---|---|
| `.docx`, `.pdf`, `.pptx`, `.xlsx`, `.csv` | `[E]` |
| `.md` (explicitly to save / download) | `[E]` |
| `.md` (inline, conversational) | `[T]` |
| `.jsx`, `.tsx`, `.html` (to save / use in project) | `[E]` |
| React component / HTML snippet (to preview / interact) | `[A]` |
| Chart / graph / visualisation (interactive, inline) | `[A]` |
| Chart / graph / visualisation (static file PNG/SVG) | `[E]` |
| Code snippet ≤ 20 lines, no run needed | `[T]` |
| Code snippet > 20 lines, or must run | `[E]` |
| Diagram (flowchart, ERD, sequence) — inline | `[A]` |
| Diagram — exported file | `[E]` |
| Small table (inline markdown) | `[T]` |
| Large or interactive table / sortable grid | `[A]` |
| Dashboard (interactive) | `[A]` |
| Dashboard (static report file) | `[E]` |

---

## 3. File attachment signals

| Situation | Path |
|---|---|
| File attached AND content already in context (text/image in `documents` block) | `[T]` unless transformation output required |
| File attached AND content NOT in context (binary, large, unsupported type) | `[E]` — must read via tools |
| Multiple files for batch processing | `[E]` |
| File attached for reference/context only | `[T]` |
| Image attached, user asks to describe/transcribe | `[T]` (vision grounding) |
| Image attached, user asks to edit/transform/return | `[E]` |

---

## 4. Length and complexity signals

| Estimated response size | Path |
|---|---|
| ≤ 300 words, single topic | `[T]` |
| 300–1 200 words, structured prose | `[T]` (with headers if document-shaped) |
| > 1 200 words creative or document content | `[E]` (`.md` artefact) |
| Multi-step workflow, > 3 dependent steps | `[E]` |
| Single-step, no dependencies | `[T]` or `[A]` |
| Interactive / stateful (user clicks, inputs, games) | `[A]` |

---

## 5. Integration and side-effect signals

| Signal | Path |
|---|---|
| "Send email / create event / post to Slack / add to CRM" | `[E]` (MCP tools) |
| "Search my Drive / find in my docs" | `[E]` (Drive tool); result summary in `[T]` or fed to `[A]` |
| "Look up current X" (web) | `[T]` after `web_search` / `web_fetch` grounding |
| "Add to my database / sheet" | `[E]` |
| "Read my calendar and show me this week" | `[E]` fetch + `[A]` visual, or `[T]` prose list |

---

## 6. Clarification triggers `[C]`

Always prefer defaulting + stating assumption over asking. Only use `[C]` when:

| Ambiguity | Default if no clarification | Question to ask |
|---|---|---|
| "Make me a report" — format unknown, long task | Default `[E]` `.md`; state assumption | "Should this be a Word doc, a PDF, or inline markdown?" |
| "Build X" — interactive preview vs file | Default `[A]`; offer file after | "Do you want to see it here in chat, or download it as a file?" |
| "Analyse this" — no file visible, no inline data | Can't proceed | "Could you paste the data or attach the file?" |
| "Create a presentation" — topic unclear | Default: ask for topic only | "What topic/content should the presentation cover?" |
