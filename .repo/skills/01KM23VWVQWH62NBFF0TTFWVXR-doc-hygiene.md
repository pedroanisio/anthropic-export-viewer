---
name: doc-hygiene
version: "1.0.0"
description: >
  Inspect a codebase to discover, classify, and manage all documentation files.
  Detects active, stale, deprecated, and orphaned docs; quarantines dead weight
  with TL;DR summaries; validates active docs against the codebase; recommends
  automating variable elements (directory trees, file counts, API routes,
  dependency lists, badge values, config key inventories).
  Use when the user mentions: doc cleanup, stale docs, documentation audit,
  doc hygiene, dead docs, outdated README, docs out of sync, doc rot,
  documentation health, prune docs, doc inventory, sync README, automate docs,
  living documentation, doc freshness — or says "my README is lying",
  "are my docs up to date", "which docs can I delete", "help me keep my
  docs honest", or wants to triage the documentation posture of any codebase.
allowed-tools: Bash Read Write Glob Grep
effort: high
metadata:
  ulid: 01KM23VWVQWH62NBFF0TTFWVXR
---

# Doc-Hygiene

Produce a full documentation audit of a codebase: discover every doc, classify
its lifecycle state, quarantine the dead weight, summarize what gets removed,
and ensure every surviving doc tells the truth — preferably via automation
rather than human memory.

## Why this matters

Documentation rots faster than code because nothing breaks when a doc lies.
A stale README is worse than no README — it actively misleads. This skill
treats docs as first-class artifacts with a lifecycle: birth, maintenance,
deprecation, and retirement. The goal is a repo where every doc is either
provably current or explicitly archived.

---

## Workflow

### Phase 0 — Orient

Before touching any file, understand the project:

1. Read the repo root: directory tree (2–3 levels), build configs
   (`package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `pom.xml`,
   `Makefile`, etc.), and CI configs (`.github/workflows/`, `.gitlab-ci.yml`,
   `Jenkinsfile`, `Taskfile.yml`, etc.).
2. Identify the **tech stack** — language(s), framework(s), monorepo tool
   (if any), doc-site generator (Docusaurus, Sphinx, MkDocs, VitePress,
   Nextra, mdBook, Doxygen, etc.).
3. Note the **repo layout convention** — is it flat? monorepo with packages?
   `src/` + `docs/`? Feature folders? This determines where docs might hide.
4. Identify any existing **doc automation** — codegen steps that produce docs,
   `typedoc`, `swagger-jsdoc`, `pdoc`, `cargo doc`, `godoc`, `openapi`
   generators, `tree` commands in CI, badge generators, changelog tools
   (e.g., `standard-version`, `conventional-changelog`, `changesets`).

Read `.repo/references/01KM23VWVQWH62NBFF0TTFWVXR-detection-patterns.md` before proceeding to Phase 1.

### Phase 1 — Discover all documentation

Scan the entire repo. A "documentation artifact" is any file whose primary
purpose is to communicate information to humans (developers, users, ops).

**Hidden directories are excluded from all discovery sweeps.** Any directory
whose name begins with `.` (e.g. `.iande/`, `.cache/`, `.venv/`, `.git/`,
`.doc-quarantine/`) must be excluded. The sole exception is `.github/`, which
contains legitimate documentation (issue templates, PR templates, funding
config). See `references/detection-patterns.md` §6 for the exact `find` and
`grep` predicates to use.

**File types to detect** (non-exhaustive):

- Markdown: `*.md`, `*.mdx`
- ReStructuredText: `*.rst`
- Plain text: `*.txt` (only if content is prose — skip `requirements.txt`, etc.)
- AsciiDoc: `*.adoc`, `*.asciidoc`
- HTML doc pages: `docs/**/*.html`, `site/**/*.html`
- Jupyter notebooks with prose: `*.ipynb` (if >50% markdown cells)
- Inline doc blocks: JSDoc, docstrings, Rustdoc, Godoc, Javadoc — note their
  presence but do not individually classify each one in Phase 2 (treat them as
  a bulk category).
- Man pages: `man/*.1`, etc.
- Wiki pages: `.github/wiki/`, `wiki/`
- Config-as-doc: `.env.example`, `docker-compose.yml` (when heavily commented
  as usage reference).

**Discovery commands** — use `find`, `grep`, `rg` (if available), `wc`.
See `references/detection-patterns.md` for the exact commands.

Record every discovered file with:

| Field | Description |
|---|---|
| **Path** | Relative path from repo root |
| **Type** | `markdown`, `rst`, `txt`, `adoc`, `html`, `ipynb`, `inline`, `man`, `config-doc` |
| **Size** | Lines / words |
| **Last modified** | Git date if available: `git log -1 --format=%aI -- <path>` |
| **Last related code change** | Date of the last commit that touched _both_ the doc and a code file in the same commit (heuristic for "maintained together") |

### Phase 2 — Classify lifecycle state

For every discovered doc (except bulk inline docs), assign one of:

| State | Meaning | Criteria |
|---|---|---|
| **ACTIVE** | Currently relevant, describes live behavior | References existing code paths; modified within the last N commits or calendar window the user defines (default: 6 months); content matches observable code behavior |
| **DRIFTED** | Was active but now contains inaccuracies | References code paths that have changed since the doc was last touched; structural content (trees, routes, config keys) does not match reality |
| **STALE** | Not updated for a long time, accuracy unknown | Not modified in >6 months (configurable), no co-commits with code files, but no obvious inaccuracy detected either — it might be fine, might not |
| **DEPRECATED** | Explicitly marked or superseded | Contains words like "deprecated", "moved to", "replaced by", "no longer maintained", "archived", "legacy"; or lives under a path like `docs/archive/`, `old/`, `deprecated/` |
| **ORPHANED** | References entities that no longer exist | Mentions files, modules, functions, routes, commands, or config keys that cannot be found in the current codebase |

**Classification is heuristic, not proof.** Always flag certainty level:
`HIGH` (strong signal), `MEDIUM` (pattern match but not confirmed),
`LOW` (age-based inference only).

Read `.repo/references/01KM23VWVQWH62NBFF0TTFWVXR-sync-checks.md` for the concrete checks per doc type.

### Phase 3 — Quarantine inactive docs

For every doc classified as DEPRECATED, ORPHANED, or STALE-with-HIGH-confidence:

1. **Create a quarantine manifest** — a structured file listing every doc
   proposed for retirement with its classification, evidence, and recommended
   action (`archive` or `delete`).
2. **Generate a TL;DR summary** for each quarantined doc: 2–5 sentences
   capturing what the doc covered, why it existed, and what (if anything)
   superseded it. This summary survives even if the doc is deleted — it is the
   institutional memory.
3. **Do NOT move or delete files automatically.** Produce a shell script
   (or set of `git mv` / `rm` commands) that the user can review and execute.
   The script should:
   - Move docs to a `.doc-quarantine/` directory (preserving relative paths).
   - Write a `quarantine-manifest.json` with all metadata.
   - Write a `quarantine-summaries.md` with all TL;DRs.
   - Optionally, add a deprecation notice header to each quarantined markdown
     file instead of moving it (user's choice).

**The user decides.** The skill's job is to surface, classify, and prepare —
never to unilaterally destroy.

### Phase 4 — Validate active docs

For every doc classified as ACTIVE or DRIFTED, run the sync checks defined
in `.repo/references/01KM23VWVQWH62NBFF0TTFWVXR-sync-checks.md`. At minimum, check:

#### 4a. Structural accuracy

- **Directory trees** in docs vs. actual `find`/`tree` output.
- **File counts / module lists** mentioned in prose vs. reality.
- **API route tables** vs. actual route definitions in code (framework-specific:
  Express `app.get`, FastAPI `@app.get`, Rails `routes.rb`, etc.).
- **CLI command/flag documentation** vs. actual `--help` output or arg-parser
  definitions.
- **Config key inventories** (`.env.example` docs, config schema docs) vs.
  actual `process.env` / `os.getenv` call sites.
- **Dependency lists** mentioned in docs vs. `package.json` / `Pipfile` /
  `Cargo.toml` / etc.
- **Version numbers** in badges, install instructions, compatibility matrices.

#### 4b. Semantic accuracy (best-effort)

- **Installation instructions**: Do the commands actually work given the
  current build config?
- **Code examples**: Do referenced imports, function names, and signatures
  still exist?
- **Architecture descriptions**: Do module boundaries and data-flow claims
  match the import graph?

#### 4c. Completeness (gap detection)

- **Exported modules with no docs**: public API surface with zero doc coverage.
- **New config keys with no mention**: env vars or config entries consumed in
  code but absent from `.env.example` or config docs.
- **New CLI commands/flags with no docs**: arg-parser definitions not reflected
  in usage docs.

For each check, record: `PASS`, `DRIFT` (specific mismatch described), or
`SKIP` (check not applicable or infeasible).

### Phase 5 — Recommend automation

This is the most valuable phase. Every variable element in a doc is a future
lie waiting to happen. The skill must identify every such element and
recommend a concrete automation strategy.

**Variable elements to look for** (non-exhaustive — think broadly):

| Element | Automation strategy |
|---|---|
| Directory tree | `tree` command piped into a fenced block, run by CI or a pre-commit hook |
| File/module count | Script that counts and injects into a template placeholder |
| API route table | Extract from framework router (e.g., `express-list-endpoints`, FastAPI's `openapi.json`, Rails `rake routes`) and inject |
| CLI usage / help text | Capture `--help` output and inject; or generate from arg-parser schema |
| Dependency table | Parse lockfile / manifest and render as table |
| Config key inventory | Grep all env-var reads, diff against `.env.example`, generate table |
| Badge values (version, coverage, build status) | Dynamic badge services (shields.io) with live query params |
| Contributor list | `git shortlog` or GitHub API, injected by `all-contributors` or custom script |
| Changelog | `conventional-changelog`, `changesets`, `git-cliff`, or similar |
| Code examples / snippets | Embed from actual source files using tools like `mdx-embed`, `literalinclude` (Sphinx), `rustdoc` include, or custom fence-replacement scripts |
| OpenAPI spec rendering | Auto-generated from code annotations (`swagger-jsdoc`, `drf-spectacular`, etc.) |
| Architecture diagrams | Generate from code (e.g., `madge` for JS dependency graphs, `pyreverse` for Python, `tsdoc` for TS) |
| License header | Injected by CI check or `addlicense` tool |
| Table of contents | Auto-generated by `doctoc`, `markdown-toc`, or doc-site framework |

For each recommendation, specify:

1. **What tool or script** to use (name it; don't say "a script").
2. **Where to hook it** — pre-commit, CI step, Makefile target, doc-site
   build, npm script, or manual command.
3. **What it replaces** — the manual section that would become auto-generated.
4. **Drift risk if not automated** — what goes wrong when someone forgets.

### Phase 6 — Emit the report

Produce a Markdown report following the structure in
`.repo/references/01KM23VWVQWH62NBFF0TTFWVXR-report-template.md`. Place it in the repo root as
`doc-hygiene-report.md` (or user-specified path).

Also produce the quarantine artifacts from Phase 3 (script, manifest,
summaries) as separate files.

### Phase 7 — Produce the quarantine script

Generate `doc-quarantine.sh` (or equivalent for the project's ecosystem):

```bash
#!/usr/bin/env bash
set -euo pipefail

# Doc-Hygiene Quarantine Script
# Generated: <ISO 8601 timestamp>
# Review every command before executing.

QUARANTINE_DIR=".doc-quarantine"
mkdir -p "$QUARANTINE_DIR"

# --- DEPRECATED docs ---
mkdir -p "$QUARANTINE_DIR/deprecated"
# mv docs/old-api.md "$QUARANTINE_DIR/deprecated/docs/old-api.md"
# ... one line per doc, commented out by default for safety ...

# --- ORPHANED docs ---
mkdir -p "$QUARANTINE_DIR/orphaned"
# ...

# --- STALE docs (HIGH confidence) ---
mkdir -p "$QUARANTINE_DIR/stale"
# ...

echo "Quarantine complete. Review .doc-quarantine/ before committing."
```

Commands are commented out by default. The user uncomments what they
approve.

---

## Key Principles

**Docs are artifacts with a lifecycle.** They are born, maintained,
deprecated, and retired — just like code. This skill enforces that lifecycle.

**Never delete without a summary.** Institutional memory matters. Every
retired doc gets a TL;DR that outlives it.

**Automation over discipline.** If a human has to remember to update a doc
section, that section will eventually lie. The right answer is almost always
"generate it from the source of truth".

**Err toward flagging, not ignoring.** A false positive (flagging a healthy
doc as stale) is cheap — the user reviews it for 10 seconds and moves on.
A false negative (missing a doc that's actively misleading) causes real
damage.

**Show your evidence.** Every classification must cite the signal that led
to it: the git dates, the missing files, the mismatched routes. No
classification without receipts.

**The user decides.** This skill proposes; the user disposes. Never move,
delete, or modify docs without producing a reviewable plan first.

---

## Reference files

Read these at the indicated phases:

- `.repo/references/01KM23VWVQWH62NBFF0TTFWVXR-detection-patterns.md` — File-discovery commands, glob
  patterns, and edge-case file types to watch for. **Read before Phase 1.**
- `.repo/references/01KM23VWVQWH62NBFF0TTFWVXR-sync-checks.md` — Concrete validation checks per doc type
  (README, CONTRIBUTING, CHANGELOG, API docs, config docs). **Read before
  Phase 4.**
- `.repo/references/01KM23VWVQWH62NBFF0TTFWVXR-report-template.md` — Exact Markdown structure for the
  output report and quarantine manifest. **Read before Phase 6.**