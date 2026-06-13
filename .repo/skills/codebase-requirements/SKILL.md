---
name: codebase-requirements
description: >
  Inspect an entire codebase and produce a comprehensive REQUIREMENTS.md
  covering project overview, provenance, asset inventory, functional and
  non-functional requirements, data models, API contracts, configuration,
  testing, dependencies, build/deploy, and gaps/risks. Use this skill for:
  "document a codebase", "reverse-engineer requirements", "generate
  REQUIREMENTS.md", "audit a project", "codebase report", "map out what
  this repo does", "onboarding doc from code", "project handoff document",
  "full codebase analysis", "requirements extraction", "document everything
  in this repo", "write a spec from code", "technical documentation from
  source". If the user wants a single document that lets a new developer
  understand the full scope and behavior of a system — use this skill.
---

# Codebase Requirements Extraction

Produce a single, self-contained `REQUIREMENTS.md` that captures the full scope,
purpose, architecture, and behavior of a codebase — written so a developer with
zero prior context can understand the system solely by reading it.

This is a forensic-analysis task, not a creative one. Every statement in the
report must be traceable to evidence found in the codebase. When something is
ambiguous, say so explicitly rather than guessing.

## Before you begin

Read the reference files in order:

1. `references/scanning-playbook.md` — **Read before Phase 1.** Contains the
   concrete detection heuristics: file patterns, grep commands, and
   ecosystem-specific signals for each report section. This is the operational
   backbone of the skill.
2. `references/report-template.md` — **Read before Phase 4.** Contains the
   exact Markdown structure, heading hierarchy, table formats, and
   cross-referencing conventions for the output.
3. `references/asset-taxonomy.md` — **Read before the asset inventory step.**
   Contains the classification taxonomy for categorizing files by type.

## Workflow

### Phase 0 — Orient

Before touching individual files, build a mental map of the project:

1. Run the `scripts/scan_tree.sh` helper (if bash is available) against the
   repo root. It produces a file tree with line counts and file types. If the
   script is unavailable, use `find . -type f | head -500` and
   `wc -l $(find . -type f -name '*.ts' -o -name '*.py' -o -name '*.go' -o -name '*.rs' -o -name '*.java' -o -name '*.rb' -o -name '*.cs')`.
2. Read the root-level files first: `README*`, `LICENSE*`, `CHANGELOG*`,
   `CONTRIBUTING*`, `package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`,
   `pom.xml`, `build.gradle`, `Makefile`, `Dockerfile*`, `docker-compose*`,
   `*.toml`, `*.yaml`, `*.yml` at root.
3. Identify the **tech stack**: language(s), framework(s), ORM, API layer,
   bundler, test runner, CI system.
4. Identify the **project topology**: monorepo vs single-package, client-server
   split, microservices, workspace layout.
5. Estimate **scale**: total files, total LOC, number of distinct modules or
   packages. This determines whether the asset inventory can be per-file or
   must be per-directory/per-module.

**Scale thresholds for the asset inventory (Section 3):**

| Scale | Strategy |
|---|---|
| ≤ 80 files | Per-file inventory. Every file gets its own row. |
| 81–300 files | Per-file for source code, config, and docs. Per-directory for assets, generated code, and vendor. |
| 301–1000 files | Per-module/per-package inventory with representative file listings. |
| > 1000 files | Per-module summaries only. Call out individually only files that are architecturally significant (entry points, routers, models, schemas, migrations, CI configs). |

These thresholds exist because a 2000-row table helps nobody. The goal is
actionable understanding, not mechanical enumeration. When grouping, still list
the key components inside each group.

### Phase 1 — Scan

Walk the codebase systematically. The scanning playbook
(`references/scanning-playbook.md`) has the concrete detection patterns.
The high-level order:

1. **Provenance**: author/contributor metadata, license, repo origin, version
   history.
2. **Asset inventory**: classify every file/directory using the taxonomy in
   `references/asset-taxonomy.md`. Record path, type, objective, key
   components, internal deps, and external deps.
3. **Functional requirements**: read routes, handlers, controllers, CLI
   commands, UI components, state machines, cron jobs, queue consumers,
   event listeners. Each distinct behavior becomes a functional requirement.
4. **Non-functional requirements**: scan for caching, rate limiting, auth
   middleware, CORS config, CSP headers, logging setup, error handlers,
   i18n config, a11y attributes, lazy loading, pagination.
5. **Data models**: ORM models, migration files, schema definitions, seed
   data, storage config.
6. **API contracts**: route definitions, GraphQL schemas, protobuf files,
   OpenAPI specs, WebSocket handlers, CLI argument parsers.
7. **Configuration**: env files, config modules, build configs, infra-as-code,
   deployment manifests.
8. **Testing**: test files, test config, coverage settings, linting rules.
9. **Dependencies**: manifest files, lock files, version constraints.
10. **Build/deploy**: scripts, CI/CD pipelines, Docker configs, task runners.

For each section, collect **evidence first, write prose second**. Keep a
scratch list of file paths and line references as you go — these become the
traceability links in the final report.

### Phase 2 — Analyze

After scanning, before writing:

1. **Cross-reference**: identify relationships between sections. A data model
   should map to API endpoints, which should map to functional requirements,
   which should map to test coverage. Note where these chains break.
2. **Gap detection**: look for orphaned files (imported nowhere), dead routes
   (defined but unreachable), missing tests for critical paths, hardcoded
   secrets, env vars consumed but not documented, config keys defined but
   never read.
3. **Risk assessment**: architectural coupling, single points of failure,
   missing error handling on critical paths, outdated dependencies with
   known CVEs (check package age and major version distance from latest).
4. **Assign identifiers**: create the FR-xxx, NFR-xxx, DM-xxx, API-xxx, etc.
   identifiers that will be used for cross-referencing. Use a consistent
   numbering scheme per section.

### Phase 3 — Emit the report

Write the REQUIREMENTS.md following the exact structure in
`references/report-template.md`.

Key writing rules:

- **Traceability**: every claim references a file path. Use relative paths
  from the project root.
- **No speculation**: if something is ambiguous, state the ambiguity. Use
  phrases like "appears to", "likely intended as", "could not be determined
  from source" — never fabricate certainty.
- **No filler**: every sentence must carry information. No "this section
  covers..." preambles.
- **Cross-references**: use the identifier system (FR-001, DM-003, etc.)
  to link between sections. If a functional requirement touches a data model
  and an API endpoint, say so with identifiers.
- **Tables over prose** for structured data (asset inventory, data model
  fields, API endpoints, env vars, dependencies).
- **Disclaimer header**: include a frontmatter disclaimer per the report
  template. This is non-negotiable — the report is a forensic extraction,
  not a guarantee.

### Phase 4 — Self-review

Before delivering, verify:

1. Every section from the template is present (even if marked "N/A — not
   found in codebase").
2. Every functional requirement has at least one associated source file.
3. Every data model field references its source (ORM model file + line, or
   migration file).
4. Every API endpoint references its handler file.
5. The dependency list matches the actual manifest files (diff if needed).
6. No identifier is used but never defined, and no identifier is defined
   but never referenced.
7. The disclaimer header is present.

Place the output at the location the user specifies, or default to
`REQUIREMENTS.md` in the project root or working directory.

## Key principles

**Evidence over inference.** The report is a mirror of the codebase, not an
interpretation. When you infer intent (e.g., "this middleware appears to
handle rate limiting"), mark it as inference.

**Completeness over brevity for critical sections.** The asset inventory can
be grouped at scale, but functional requirements, data models, and API
contracts must be exhaustive — missing an endpoint is worse than a long
table.

**Structured data over prose.** If information has a fixed schema (fields,
endpoints, env vars, dependencies), present it as a table. Prose is for
explaining intent, trade-offs, and gaps.

**Explicit gaps over silent omissions.** If a section is empty because the
codebase lacks that concern (e.g., no tests, no CI), say so explicitly
and flag it as a risk in Section 12.

**Respect scope.** If the user scopes the analysis (e.g., "just the backend",
"only the API layer"), honor the scope. Note what was excluded and why.

## Handling edge cases

- **Monorepo with multiple packages**: produce one report with a top-level
  overview, then sub-sections per package. Use package-scoped identifiers
  (e.g., `FR-api-001`, `FR-web-001`).
- **Generated code**: identify it, note the generator, but do not document
  generated files at the same granularity as hand-written code. Note the
  codegen config file instead.
- **Vendor / node_modules / third-party copies**: skip internal scanning.
  Document their existence in the dependency section.
- **Binary files**: note their presence and apparent purpose (images, fonts,
  compiled artifacts). Do not attempt to parse.
- **Obfuscated or minified code**: note it, flag as a gap. Do not
  reverse-engineer minified bundles.
- **Empty or stub files**: note them and flag as potential dead code.

## Reference files

Read these before the corresponding phase:

- `references/scanning-playbook.md` — Detection heuristics, grep patterns,
  and ecosystem-specific signals. **Read before Phase 1.**
- `references/report-template.md` — Exact Markdown template for the output.
  **Read before Phase 3.**
- `references/asset-taxonomy.md` — File classification taxonomy. **Read
  before the asset inventory step in Phase 1.**

## Scripts

- `scripts/scan_tree.sh` — Generates an annotated file tree with line
  counts, file types, and directory sizes. Run against the repo root at the
  start of Phase 0 to get a quick structural overview. Usage:
  `bash scripts/scan_tree.sh /path/to/repo`
