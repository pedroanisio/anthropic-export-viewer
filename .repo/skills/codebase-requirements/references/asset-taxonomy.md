# Asset Taxonomy

Classification system for the Complete Asset Inventory (Section 3 of the
REQUIREMENTS.md report). Every file in the codebase must be assigned exactly
one **primary type** from the categories below. When a file serves multiple
purposes (e.g., a config file that also contains inline documentation),
classify by primary function and note the secondary role in the "Objective"
column.

---

## Primary Asset Types

### Source Code

Files that contain application logic executed at runtime or compile time.

| Subtype | Description | Typical Patterns |
|---|---|---|
| Entry point | Application bootstrap / main executable | `main.*`, `index.*`, `app.*`, `server.*`, `cmd/main.go`, `src/main.rs` |
| Route / Controller | HTTP route definitions, request handlers | `routes/`, `controllers/`, `handlers/`, `*Router*`, `*Controller*` |
| Service / Business logic | Core domain logic, use cases, services | `services/`, `usecases/`, `domain/`, `*Service*`, `*UseCase*` |
| Model / Entity | Data structures, ORM models, domain entities | `models/`, `entities/`, `schema.*`, `*.model.*`, `*.entity.*` |
| Repository / Data access | Database queries, data layer abstraction | `repositories/`, `*Repository*`, `*DAO*`, `queries/` |
| Middleware | Request/response interceptors, filters | `middleware/`, `*Middleware*`, `guards/`, `interceptors/`, `pipes/` |
| Utility / Helper | Shared utility functions, formatters, parsers | `utils/`, `helpers/`, `lib/`, `common/`, `shared/` |
| Type definition | Type declarations, interfaces, enums | `types/`, `interfaces/`, `*.d.ts`, `*.types.*` |
| UI Component | Frontend components, views, pages | `components/`, `pages/`, `views/`, `screens/`, `*.tsx`, `*.vue`, `*.svelte` |
| State management | Client-side state stores, reducers, atoms | `store/`, `stores/`, `*Store*`, `*Slice*`, `*Atom*` |
| Worker / Job | Background workers, queue processors, cron tasks | `workers/`, `jobs/`, `tasks/`, `consumers/`, `*Worker*`, `*Job*` |
| Plugin / Extension | Plugin system, extension points, hooks | `plugins/`, `extensions/`, `hooks/`, `*Plugin*` |
| CLI command | Command-line interface handlers | `commands/`, `cli/`, `cmd/` |

### Configuration

Files that parameterize build, runtime, or deployment behavior.

| Subtype | Description | Typical Patterns |
|---|---|---|
| Environment | Environment variable definitions | `.env*`, `*.env`, `env.*` |
| Build / Bundler | Build tool and bundler configuration | `webpack.config.*`, `vite.config.*`, `tsconfig.*`, `babel.config.*`, `rollup.config.*` |
| Framework | Framework-specific settings | `next.config.*`, `nuxt.config.*`, `angular.json`, `svelte.config.*` |
| Package manifest | Dependency declarations and project metadata | `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `pom.xml`, `Gemfile` |
| Lock file | Pinned dependency versions | `*.lock`, `*.lockb`, `go.sum` |
| Linter / Formatter | Code style and quality rules | `.eslintrc*`, `eslint.config.*`, `.prettierrc*`, `ruff.toml`, `.flake8` |
| CI/CD | Continuous integration and deployment pipelines | `.github/workflows/*`, `.gitlab-ci.yml`, `Jenkinsfile`, `.circleci/*` |
| Container | Container build and orchestration | `Dockerfile*`, `docker-compose*`, `.dockerignore` |
| Infrastructure | Infrastructure-as-code definitions | `*.tf`, `*.tfvars`, `serverless.yml`, `cdk.*`, `pulumi.*`, `k8s/`, `helm/` |
| Deployment | Platform-specific deployment config | `vercel.json`, `netlify.toml`, `fly.toml`, `render.yaml`, `Procfile` |
| Editor / IDE | Developer tooling preferences | `.vscode/`, `.idea/`, `.editorconfig`, `*.code-workspace` |
| Git | Version control configuration | `.gitignore`, `.gitattributes`, `.gitmodules` |
| Runtime | Runtime configuration consumed by the application | `config/`, `settings.*`, `*config.ts`, `*config.py` |

### Data

Files that store or define data structures, schemas, or seed content.

| Subtype | Description | Typical Patterns |
|---|---|---|
| Database migration | Schema change scripts | `migrations/`, `migrate/`, `db/migrate/`, `alembic/versions/` |
| Schema definition | Database or API schema files | `schema.prisma`, `*.graphql`, `*.gql`, `*.proto`, `*.xsd`, `*.json-schema` |
| Seed / Fixture | Sample or initial data | `seeds/`, `fixtures/`, `seeders/`, `*seed*`, `*fixture*` |
| Static data | Lookup tables, constants files, reference data | `data/`, `*.csv`, `*.json` (non-config), `*.yaml` (non-config) |

### Documentation

Files whose primary purpose is human-readable explanation.

| Subtype | Description | Typical Patterns |
|---|---|---|
| README | Project or module overview | `README*` |
| Changelog | Version history and release notes | `CHANGELOG*`, `CHANGES*`, `HISTORY*`, `RELEASES*` |
| License | Legal terms | `LICENSE*`, `LICENCE*`, `COPYING*` |
| Contributing guide | Contribution guidelines | `CONTRIBUTING*`, `CODE_OF_CONDUCT*` |
| API documentation | Generated or hand-written API docs | `docs/api/`, `openapi.*`, `swagger.*` |
| Architecture docs | Design documents, ADRs | `docs/`, `adr/`, `decisions/`, `*.md` in `docs/` |
| Inline docs | Comments, JSDoc, docstrings (not separate files) | N/A — these are properties of source files, not separate assets |

### Test

Files that verify application behavior.

| Subtype | Description | Typical Patterns |
|---|---|---|
| Unit test | Isolated function/class tests | `*.test.*`, `*.spec.*`, `test_*`, `*_test.*`, `__tests__/` |
| Integration test | Multi-component tests | `*.integration.*`, `integration/`, `*.int.*` |
| E2E test | Full-stack browser/API tests | `e2e/`, `cypress/`, `playwright/`, `*.e2e.*` |
| Performance test | Load, stress, benchmark tests | `bench/`, `benchmark/`, `perf/`, `*.bench.*` |
| Snapshot | UI or output snapshots | `__snapshots__/`, `*.snap` |
| Test utility | Test helpers, factories, mocks | `test/helpers/`, `test/utils/`, `factories/`, `mocks/`, `__mocks__/` |
| Test config | Test framework configuration | `jest.config.*`, `vitest.config.*`, `conftest.py`, `pytest.ini` |

### Static Asset

Files served directly or embedded in output without code transformation.

| Subtype | Description | Typical Patterns |
|---|---|---|
| Image | Raster and vector graphics | `*.png`, `*.jpg`, `*.jpeg`, `*.gif`, `*.webp`, `*.svg`, `*.ico` |
| Font | Typeface files | `*.woff`, `*.woff2`, `*.ttf`, `*.otf`, `*.eot` |
| Stylesheet | CSS and preprocessor files | `*.css`, `*.scss`, `*.sass`, `*.less`, `*.styl` |
| Template | HTML templates, email templates | `*.html`, `*.hbs`, `*.ejs`, `*.pug`, `*.njk`, `templates/` |
| Audio / Video | Media files | `*.mp3`, `*.mp4`, `*.wav`, `*.ogg`, `*.webm` |
| Favicon / Icon | Browser and app icons | `favicon.*`, `icon-*`, `apple-touch-icon*`, `manifest.json` |

### Generated / Build Output

Files produced by build tools, not hand-authored. These should be identified
but not inventoried at the same granularity as source code.

| Subtype | Description | Typical Patterns |
|---|---|---|
| Compiled output | Transpiled or compiled artifacts | `dist/`, `build/`, `out/`, `.next/`, `target/`, `bin/` |
| Generated types | Auto-generated type definitions | `*.generated.*`, `*.g.dart`, `__generated__/`, files with "DO NOT EDIT" headers |
| Coverage report | Test coverage output | `coverage/`, `htmlcov/`, `.nyc_output/` |
| Vendor / Lock | Third-party vendored code | `vendor/`, `node_modules/`, `__pycache__/` |

### Script

Standalone automation scripts not part of the application runtime.

| Subtype | Description | Typical Patterns |
|---|---|---|
| Build script | Compilation, bundling, packaging | `Makefile`, `justfile`, `Taskfile.yml`, `Rakefile`, `gulpfile.*` |
| Deploy script | Deployment automation | `deploy.*`, `scripts/deploy*`, `bin/deploy*` |
| Dev utility | Developer convenience scripts | `scripts/`, `bin/`, `tools/` |
| Database script | Manual DB operations, backups | `scripts/db*`, `bin/migrate*` |

---

## Classification decision tree

When a file is ambiguous, use this precedence:

1. If it defines routes/handlers/controllers → **Source Code — Route**
2. If it defines data structures persisted to a DB → **Data — Schema** or **Source Code — Model**
3. If it parameterizes behavior without containing logic → **Configuration**
4. If it verifies behavior → **Test**
5. If it explains something to humans → **Documentation**
6. If it automates a process → **Script**
7. If it's served unchanged to clients → **Static Asset**
8. If it has a "DO NOT EDIT" header or lives in `dist/`/`build/` → **Generated**
9. Default: **Source Code — Utility**
