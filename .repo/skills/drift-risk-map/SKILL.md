---
name: drift-risk-map
description: >
  Inspect a codebase and produce a drift-risk map — a structured inventory of
  every coupling between source-of-truth artifacts and their dependents, scored
  by the risk of silent desynchronization. Use this skill whenever the user asks
  to audit, map, or analyze coupling, drift, consistency, synchronization, or
  contract alignment across a codebase. Also trigger when the user mentions
  "what breaks if I change X", "are my types/schemas/docs in sync",
  "find manual mirrors", "coupling audit", "contract drift", "schema drift",
  "consistency check across layers", or any request to understand how changes
  propagate (or fail to propagate) through a project. Trigger even when the
  user phrases it casually, e.g. "I keep finding stale docs" or "my SDK is out
  of date with the API spec" or "how tightly coupled is this repo". If the user
  wants to know where their codebase is fragile to silent breakage, use this
  skill.
---

# Drift-Risk Map

Produce a structured report that answers: **"Where in this codebase can a
change in one artifact silently invalidate another?"**

Silent drift — where artifacts fall out of sync without any build error, test
failure, or linter warning — is one of the most expensive classes of bugs
because it ships undetected. This skill systematically identifies those
vectors.

## Workflow

### Phase 0 — Orient

Before scanning files, understand the project topology:

1. Read the repo root: directory tree (2–3 levels), `README`, `package.json` /
   `pyproject.toml` / `go.mod` / `Cargo.toml` / `pom.xml` / build config.
2. Identify the **tech stack** (language, frameworks, ORM, API framework, doc
   tooling, codegen tooling).
3. Identify the **build/CI pipeline** — look for `Makefile`, `justfile`,
   `.github/workflows/`, `Taskfile.yml`, `docker-compose.yml`, `turbo.json`,
   `nx.json`, monorepo configs. CI files reveal which automated checks exist.
4. List candidate **source-of-truth artifacts** — files that other things
   derive from or must agree with. Typical examples below.

Do not assume a repo follows any convention. Read before classifying.

### Phase 1 — Build the coupling inventory

Walk the coupling domains below. For each, scan the actual codebase files.
Use `grep`, `find`, `ripgrep` (if available), and file reads to confirm or
rule out each coupling type. See `references/detection-heuristics.md` for
concrete patterns per ecosystem.

The coupling domains are:

#### 1. API contract ↔ SDK / client codegen

Source artifacts: OpenAPI / Swagger specs, GraphQL SDL, Protobuf `.proto`
files, TRPC router definitions, gRPC service definitions.

Look for: codegen config (`openapi-generator-cli.yaml`,
`buf.gen.yaml`, `graphql-codegen.yml`, `.openapi-generator/`), generated
output directories, import paths from generated code, manual HTTP client
wrappers that restate paths/methods/payloads from the spec.

#### 2. API contract ↔ request/response validation

Source artifacts: same as above, plus framework-level schema decorators
(e.g., Pydantic models, Zod schemas, `class-validator` decorators, Marshmallow
schemas, JSON Schema files).

Look for: validation middleware that references types also used in routing,
hand-written validators that duplicate constraints already expressed elsewhere,
runtime validators disconnected from the spec that generated the types.

#### 3. Data models ↔ DB schema / migrations

Source artifacts: ORM model definitions (SQLAlchemy, Prisma, TypeORM, Django
models, Ecto schemas, ActiveRecord), raw SQL migration files, Alembic/Knex/
Flyway/Liquibase migration directories.

Look for: model fields that don't match the latest migration state, nullable
mismatches, default-value discrepancies, index definitions in code vs. in
migrations, enum types defined in application code vs. DB-level enums.

#### 4. Data models ↔ serializers / DTOs

Source artifacts: ORM models, domain entities.

Look for: serializer/DTO classes that manually mirror model fields (DRF
serializers, MapStruct mappers, manual `toJSON` / `fromJSON`, Pydantic
`model_validator` / `from_orm`, Go struct tags), field additions in the model
not reflected in the serializer or vice-versa.

#### 5. Public interfaces ↔ documentation

Source artifacts: code signatures (exported functions, class APIs, CLI flags),
configuration schemas.

Look for: `README.md` sections that describe API usage, `CHANGELOG.md`,
OpenAPI specs hand-maintained separately from code, JSDoc/docstring examples,
`man` pages, `--help` strings generated from or separate to code, published
docs sites (Docusaurus, Sphinx, MkDocs) with content authored independently
from the code they document.

#### 6. Config / env definitions ↔ runtime consumers

Source artifacts: `.env.example`, `config.ts` / `settings.py`, Helm
`values.yaml`, Terraform variable definitions, Kubernetes ConfigMap templates,
`docker-compose.yml` environment blocks.

Look for: every call site that reads an env var or config key — `os.getenv()`,
`process.env.X`, `viper.Get()`, `std::env::var()`, `@Value` annotations.
Compare the set of keys consumed at runtime against the set of keys defined
in config templates. Missing keys in the template = silent drift risk.

#### 7. Shared types / constants ↔ all import sites

Source artifacts: shared type definition files, constants modules, enums.

Look for: re-declarations of the same logical constant or type in multiple
places (string literal unions repeated across files, magic numbers, duplicated
enum members), barrel exports that may mask stale re-exports.

#### 8. Infra-as-Code ↔ application expectations

Source artifacts: Terraform/Pulumi/CloudFormation definitions, Helm charts,
Docker build files.

Look for: port numbers, hostnames, resource names, IAM role ARNs, or queue
names that appear both in infra definitions and application config/code, with
no shared reference linking them.

#### 9. Test fixtures / mocks ↔ production schemas

Source artifacts: production type definitions, API specs.

Look for: hard-coded JSON fixtures, mock factories, snapshot files, seed data
scripts that embed a schema shape. If the production schema changes, fixtures
that aren't generated from it will silently lie.

### Phase 2 — Classify each coupling

For every coupling found, record:

| Field | Description |
|---|---|
| **Source artifact** | The file/spec that is the logical source of truth. |
| **Dependent artifact(s)** | File(s) that must agree with the source. |
| **Coupling mechanism** | How they stay (or fail to stay) in sync: `codegen`, `shared-import`, `manual-mirror`, `contract-test`, `lint-rule`, `build-step`, `runtime-validation`, `none`. |
| **Consistency guard** | The specific automated check, if any: CI job name, test file, linter rule, codegen command. `⚠ NONE` if absent. |
| **Propagation mode** | What happens when the source changes and the dependent is NOT updated: `build-error`, `type-error`, `test-failure`, `lint-failure`, `runtime-error`, `silent` — ranked roughly from loud to quiet. |
| **Drift risk** | **CRITICAL** (no guard + silent propagation), **HIGH** (weak guard or delayed feedback), **MODERATE** (guard exists but has known gaps), **LOW** (strong automated guard, fast feedback). |

### Phase 3 — Score and prioritize

After the full inventory:

1. **Count** the couplings by risk level.
2. **Sort** CRITICAL first, then HIGH.
3. For each CRITICAL coupling, draft a concrete **remediation recommendation**:
   suggest a codegen step, a test, a linter rule, or a CI check that would
   convert it from silent to loud. Be specific — name the tool, the rough
   shape of the check, and where in the pipeline it should run.
4. For each HIGH coupling, note what makes the existing guard insufficient
   and what would upgrade it to MODERATE or LOW.

### Phase 4 — Emit the Markdown report

Produce a Markdown document with the structure defined in
`references/report-template.md`. Place the output in the user's preferred
location (default: `drift-risk-map.md` in the repo root or working
directory).

The report must include:

1. **Header & disclaimer** per user preferences.
2. **Executive summary**: total couplings found, count by risk tier, top-3
   most dangerous vectors, one-paragraph overall posture assessment.
3. **Coupling inventory table**: one row per coupling, all fields from Phase 2.
4. **CRITICAL findings detail**: one subsection per CRITICAL coupling with
   file paths, a concrete example of how drift would manifest, and the
   recommended fix.
5. **Methodology notes**: what was inspected, what was skipped, known
   limitations of static heuristic analysis.

### Phase 5 — Generate the SVG visual

After the Markdown report, produce a standalone SVG file
(`drift-risk-map.svg`) that provides a visual overview of the entire
coupling topology. This is not a decoration — it is the report's primary
navigational artifact, letting someone scan the full risk landscape in
seconds instead of reading a table.

Read `references/svg-spec.md` before generating the SVG. It defines the
exact layout, color system, typography, and construction rules.

The SVG has five vertical sections, stacked top-to-bottom:

1. **Header + stat cards** — project name, coupling count, and four
   color-coded stat cards showing the count per risk tier (CRITICAL,
   HIGH, MODERATE, LOW).

2. **Hub-and-spoke diagram** — the core visual. One or more hub nodes
   at the center (the primary source(s) of truth in the codebase),
   surrounded by concentric dashed risk rings (P0 innermost → P3
   outermost). Every coupling from Phase 2 becomes a spoke node
   positioned on its risk ring, connected to its hub by a line whose
   weight and style encode the risk tier. See `references/svg-spec.md`
   for the exact color, stroke, and layout rules.

3. **Coupling inventory table** — a rendered SVG table mirroring the
   Markdown inventory: one row per coupling, color-banded by tier, with
   columns for relationship, mechanism, guard, propagation, and risk.

4. **Top-N mitigations** — the highest-priority remediation actions from
   Phase 3, rendered as color-coded action cards with priority badges.

5. **Footer disclaimer** — single-line static analysis caveat.

Place the SVG alongside the Markdown report (default:
`drift-risk-map.svg` in the same directory as `drift-risk-map.md`).

The SVG must be fully standalone — no external dependencies except an
optional Google Fonts import for typography. It must render correctly
when opened in a browser, embedded in a README, viewed in Figma, or
printed.

## Key principles

**Err toward false positives, not false negatives.** If you're uncertain
whether a coupling exists, flag it with a note explaining the uncertainty.
A spurious row is cheap to dismiss; a missed CRITICAL vector is expensive.

**Show your evidence.** Every coupling entry must reference concrete file
paths and line-number ranges (or glob patterns for generated directories).
Do not produce entries that say "there might be drift" without pointing at
files.

**Do not invent couplings.** Only report what you can actually observe in the
codebase. If a coupling domain from the list above doesn't apply (e.g., no
protobuf in the repo), skip it — don't pad the report.

**Respect scope.** If the user scopes the audit (e.g., "just the API layer"),
honor it. If they don't, default to full coverage.

## Reference files

Read these before scanning:

- `references/detection-heuristics.md` — Concrete file patterns, grep
  commands, and ecosystem-specific signals for each coupling domain. **Read
  this before Phase 1.**
- `references/report-template.md` — The exact Markdown structure for the
  output report. **Read this before Phase 4.**
- `references/svg-spec.md` — Layout rules, color system, typography, and
  construction patterns for the SVG visual. **Read this before Phase 5.**
