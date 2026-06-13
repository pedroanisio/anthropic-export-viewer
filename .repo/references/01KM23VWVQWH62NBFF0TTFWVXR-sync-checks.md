# Sync Checks

Concrete validation checks to determine whether an active doc matches the
current state of the codebase. Read this before Phase 4.

Each section covers one doc type with specific, executable checks. Every
check produces a verdict: `PASS`, `DRIFT` (with description), or `SKIP`.

---

## 1. README.md

The README is the repo's front door. It lies more than any other doc because
it covers the widest surface area.

### 1a. Project description / tagline

- **Check**: Does the description match `package.json#description`,
  `pyproject.toml#[project].description`, `Cargo.toml#[package].description`,
  or the GitHub repo description?
- **Signal**: If they disagree, the README drifted or the manifest did.

### 1b. Installation instructions

- **Check**: Extract every shell command from "Installation" or "Getting
  Started" sections. Verify:
  - Package name matches the published name.
  - Runtime/language version constraints match `engines`, `python_requires`,
    `rust-version`, etc.
  - Dependency install commands reference the correct package manager
    (`npm` vs `yarn` vs `pnpm` vs `bun`; `pip` vs `poetry` vs `uv`).
- **Command**:
  ```bash
  # Extract fenced shell blocks from README
  awk '/^```(bash|sh|shell|zsh|console)$/,/^```$/' README.md
  ```

### 1c. Directory tree

- **Check**: If the README contains a directory tree (ASCII art or fenced
  block), compare against actual `tree` or `find` output.
- **Command**:
  ```bash
  # Generate actual tree (depth 2, ignore noise)
  tree -L 2 -I 'node_modules|.git|dist|build|__pycache__|.venv|target' --charset=ascii
  ```
- **Comparison**: Diff the documented tree against the actual tree. New
  directories or missing directories = DRIFT.

### 1d. Badges

- **Check**: Extract badge URLs. Verify:
  - Version badges point to the correct package name and registry.
  - Build status badges reference the correct CI workflow file name.
  - Coverage badges reference the correct service and repo slug.
- **Command**:
  ```bash
  grep -oP '!\[.*?\]\(https?://[^\)]+\)' README.md
  # or for reference-style badges:
  grep -oP '\[.*?\]:\s*https?://\S+' README.md
  ```

### 1e. API / usage examples

- **Check**: For every code example in the README:
  - Extract import/require statements. Verify the imported names exist as
    actual exports.
  - Extract function calls. Verify the functions exist and signatures are
    compatible (parameter count, required args).
- **Command** (JS/TS example):
  ```bash
  # List actual exports from the package entry point
  grep -rE '^export ' src/index.ts src/index.js 2>/dev/null
  ```

### 1f. Contributing / license pointers

- **Check**: If README says "see CONTRIBUTING.md" or "MIT License", verify
  the referenced files exist and the license type matches the actual
  `LICENSE` file content.

---

## 2. CONTRIBUTING.md

### 2a. Development setup

- **Check**: Extract every setup command. Verify:
  - The expected Node/Python/Rust/Go version matches toolchain config
    (`.nvmrc`, `.python-version`, `rust-toolchain.toml`, `go.mod`).
  - The install command is valid for the current lockfile format.
  - Test commands match the actual test runner config.
- **Command**:
  ```bash
  # What's the actual test command?
  grep -E '"test"' package.json  # npm
  grep -E '\[tool\.pytest' pyproject.toml  # Python
  grep -E 'test:' Makefile  # Make
  ```

### 2b. Branch / PR conventions

- **Check**: If the doc specifies branch naming or PR conventions, compare
  against `.github/workflows/` — do CI triggers match the described branches?
  Does `CODEOWNERS` match the described review process?

### 2c. Code style / linting

- **Check**: If the doc describes a code style or linter, verify the linter
  config exists (`.eslintrc`, `.prettierrc`, `ruff.toml`, `rustfmt.toml`,
  `.editorconfig`).

---

## 3. CHANGELOG.md / HISTORY.md

### 3a. Latest version

- **Check**: The most recent entry in the changelog should match the
  version in the package manifest (`package.json#version`, `Cargo.toml`,
  `pyproject.toml`, `setup.py`, etc.) AND the latest git tag.
- **Command**:
  ```bash
  # Latest git tag
  git describe --tags --abbrev=0 2>/dev/null || echo "no tags"
  
  # Version from manifest
  grep '"version"' package.json | head -1
  # or
  grep '^version' pyproject.toml | head -1
  
  # First version heading in CHANGELOG
  grep -m1 -E '^#{1,3}\s+\[?v?[0-9]+\.' CHANGELOG.md
  ```

### 3b. Unreleased section

- **Check**: If there's an `[Unreleased]` section, verify commits exist
  between the latest tag and HEAD that are not reflected in a versioned
  section.

### 3c. Automation check

- **Check**: Is the changelog auto-generated? Look for:
  - `.changeset/` directory (changesets)
  - `.versionrc` or `.releaserc` (standard-version / semantic-release)
  - `cliff.toml` (git-cliff)
  - CI workflow that runs a changelog generator
- **Verdict**: If manual and >20 entries, strongly recommend automation.

---

## 4. API documentation

Covers OpenAPI/Swagger specs, GraphQL SDL docs, or hand-written API refs.

### 4a. Route completeness

- **Check**: Extract all routes from the code (see `detection-patterns.md`
  §3 for framework-specific commands). Compare against routes documented in
  API docs.
- **Verdicts**:
  - Routes in code but not in docs = `DRIFT:undocumented_routes`
  - Routes in docs but not in code = `DRIFT:phantom_routes`

### 4b. Request/response schema

- **Check**: If the API doc describes request/response shapes, compare
  against actual type definitions, Zod schemas, Pydantic models, or
  validation middleware.
- **This is deep work** — only do it if the user requests it or the repo
  has <30 routes.

### 4c. Authentication / authorization docs

- **Check**: If docs describe auth methods (API keys, OAuth, JWT), verify
  the described flow matches middleware/guard configuration in code.

---

## 5. Configuration documentation

Covers `.env.example`, config schema docs, deployment guides.

### 5a. Env var completeness

- **Check**: Cross-reference every env var read in code against what's
  listed in `.env.example` or config docs. See `detection-patterns.md` §4.
- **Verdicts**:
  - In code but not documented = `DRIFT:undocumented_config`
  - Documented but not in code = `DRIFT:phantom_config`

### 5b. Default values

- **Check**: If docs list default values, verify they match the defaults
  in code (e.g., `process.env.PORT || 3000` → docs should say "default:
  3000").

### 5c. Docker / docker-compose alignment

- **Check**: If `docker-compose.yml` exposes environment variables, verify
  they match what's in `.env.example` and config docs.
- **Command**:
  ```bash
  # Env vars in docker-compose
  grep -oP '(?<=\$\{)[A-Z_]+' docker-compose.yml | sort -u
  # or
  grep -E '^\s+- [A-Z_]+=' docker-compose.yml | sed 's/.*- //' | cut -d= -f1 | sort -u
  ```

---

## 6. Architecture / ADR docs

### 6a. Module references

- **Check**: If the doc names specific modules, services, or packages,
  verify they still exist at the described paths.

### 6b. Dependency flow

- **Check**: If the doc describes "Service A calls Service B", verify
  the import/dependency exists in code.

### 6c. ADR status

- **Check**: ADRs (Architecture Decision Records) should have a `Status`
  field. Verify that ADRs marked `accepted` describe behavior still present
  in code, and ADRs marked `superseded` reference the replacing ADR.

---

## 7. Inline docs (bulk check)

Don't check every docstring individually, but do a coverage scan:

```bash
# Python: public functions missing docstrings
grep -rnP '^\s*def (?!_)\w+' --include='*.py' --exclude-dir='.*' -l . | while read f; do
  python3 -c "
import ast, sys
with open('$f') as fh:
    tree = ast.parse(fh.read())
for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        if not node.name.startswith('_') and not ast.get_docstring(node):
            print(f'$f:{node.lineno}: {node.name}() — no docstring')
" 2>/dev/null
done

# TypeScript: exported functions without JSDoc
# (heuristic — check for /** above export)
grep -rnB1 '^export ' --include='*.ts' --exclude-dir='.*' . | grep -v '/\*\*' | grep 'export '
```

Report:
- Total public functions/methods
- Count with docs vs. without
- Coverage percentage
- Files with worst coverage

---

## 8. CI / automation alignment

### 8a. Documented scripts

- **Check**: If docs say "run `npm test`", verify the `test` script exists
  in `package.json`. If docs say "run `make build`", verify the `build`
  target exists in `Makefile`.

### 8b. CI workflow docs

- **Check**: If docs describe CI behavior ("PRs must pass linting"),
  verify the corresponding workflow file exists and runs the described
  checks.

---

## Verdicts table

For each check, record:

| Doc | Check | Verdict | Detail |
|---|---|---|---|
| `README.md` | 1c. Directory tree | DRIFT | Missing `src/utils/`, extra `legacy/` |
| `README.md` | 1e. Usage example | PASS | — |
| `CONTRIBUTING.md` | 2a. Dev setup | DRIFT | Says Node 18, `.nvmrc` says 20 |
| `.env.example` | 5a. Completeness | DRIFT | `REDIS_URL` in code, not in example |
| ... | ... | ... | ... |