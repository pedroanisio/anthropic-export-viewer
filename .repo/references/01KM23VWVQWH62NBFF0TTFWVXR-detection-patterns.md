# Detection Patterns

Concrete commands and heuristics for discovering documentation artifacts
in a codebase. Read this before Phase 1.

---

## 1. Primary discovery sweep

Run these commands from the repo root. Adapt paths if the repo has a
non-standard layout.

### Markdown and prose files

```bash
# All markdown (most common doc format)
find . -type f \( -name '*.md' -o -name '*.mdx' \) \
  -not -path '*/node_modules/*' \
  -not -path '*/vendor/*' \
  -not -path '*/dist/*' \
  -not \( -path '*/.*' -not -path '*/.github/*' \) \
  | sort

# ReStructuredText
find . -type f -name '*.rst' \
  -not -path '*/node_modules/*' \
  -not \( -path '*/.*' -not -path '*/.github/*' \) \
  | sort

# AsciiDoc
find . -type f \( -name '*.adoc' -o -name '*.asciidoc' \) \
  -not -path '*/node_modules/*' \
  -not \( -path '*/.*' -not -path '*/.github/*' \) \
  | sort

# Plain text (filter later — many .txt files are not docs)
find . -type f -name '*.txt' \
  -not -path '*/node_modules/*' \
  -not \( -path '*/.*' -not -path '*/.github/*' \) \
  -not -name 'requirements*.txt' \
  -not -name 'constraints*.txt' \
  -not -name 'LICENSE*' \
  | sort
```

### Conventional root docs (case-insensitive search)

```bash
# These are the "canonical" root docs. Check for their presence.
for name in README CONTRIBUTING CHANGELOG CHANGES HISTORY \
            CODE_OF_CONDUCT SECURITY SUPPORT GOVERNANCE \
            ARCHITECTURE ADR MIGRATION UPGRADE RELEASING \
            DEVELOPMENT HACKING TODO; do
  find . -maxdepth 2 -iname "${name}*" -type f 2>/dev/null
done
```

### Doc directories

```bash
# Common doc directory names
for dir in docs doc documentation wiki .github/wiki \
           guides tutorials howto reference api-docs \
           man pages site _site public/docs; do
  [ -d "$dir" ] && echo "DOC_DIR: $dir ($(find "$dir" -type f | wc -l) files)"
done
```

### Doc-site generator configs

```bash
# Detect doc-site generators (presence = structured doc system)
for f in docusaurus.config.js docusaurus.config.ts \
         mkdocs.yml mkdocs.yaml \
         conf.py \
         book.toml \
         .vitepress/config.js .vitepress/config.ts \
         nextra.config.js \
         Doxyfile \
         typedoc.json .typedoc.json \
         jsdoc.json .jsdoc.json; do
  [ -f "$f" ] && echo "DOC_SITE_CONFIG: $f"
done
```

### Generated doc output directories

```bash
# These are output dirs — docs generated FROM code, not hand-written.
# Knowing they exist matters for the automation inventory.
for dir in _build build/docs dist/docs out/docs \
           target/doc api-reference/generated \
           .docusaurus storybook-static; do
  [ -d "$dir" ] && echo "GENERATED_DOC_DIR: $dir"
done
```

## 2. Git metadata extraction

For every discovered doc file, extract modification history:

```bash
# Last modification date of a specific file
git log -1 --format='%aI' -- "$filepath"

# All commits that touched this file (count)
git log --oneline -- "$filepath" | wc -l

# Last commit that touched BOTH this doc and a code file
# (heuristic: "co-maintained" — the doc was updated alongside code)
git log --oneline --name-only -- "$filepath" | head -50
# Then inspect each commit to see if code files changed too.

# Shortcut: files changed in the same commit as the doc
git log -1 --name-only --format='' -- "$filepath"
```

### Bulk age report

```bash
# For all markdown files: path + last-modified date + commit count
find . -name '*.md' \
  -not -path '*/node_modules/*' \
  -not \( -path '*/.*' -not -path '*/.github/*' \) \
  -exec sh -c '
    for f; do
      date=$(git log -1 --format="%aI" -- "$f" 2>/dev/null || echo "unknown")
      commits=$(git log --oneline -- "$f" 2>/dev/null | wc -l)
      echo "$f|$date|$commits"
    done
  ' _ {} +
```

## 3. Deprecated / archived signal detection

```bash
# Files containing deprecation signals in the first 20 lines
for f in $(find . -name '*.md' \
  -not -path '*/node_modules/*' \
  -not \( -path '*/.*' -not -path '*/.github/*' \)); do
  head -20 "$f" | grep -qiE \
    '(deprecated|archived|obsolete|superseded|replaced by|moved to|no longer maintained|do not use|legacy)' \
    && echo "DEPRECATION_SIGNAL: $f"
done

# Files under conventional "dead" directories
find . -type f \( -path '*/archive/*' -o -path '*/archived/*' \
  -o -path '*/old/*' -o -path '*/deprecated/*' \
  -o -path '*/legacy/*' -o -path '*/retired/*' \) \
  -not -path '*/node_modules/*' \
  -not \( -path '*/.*' -not -path '*/.github/*' \)
```

## 4. Orphan signal detection

Orphaned docs reference entities that no longer exist. This requires
cross-referencing doc content against the codebase.

```bash
# Extract code-like references from a markdown file
# (backtick-fenced names, paths, import statements in examples)
grep -oP '`[a-zA-Z0-9_./-]+`' "$filepath" | tr -d '`' | sort -u

# For each extracted reference, check if it exists
# (file path, module name, function name)
# This is heuristic — a reference to `utils.formatDate` should be
# checked against actual exports, not just file existence.
```

### Framework-specific route extraction

These let you compare "routes mentioned in docs" against "routes that
actually exist in code":

```bash
# Express.js
grep -rnE '(app|router)\.(get|post|put|patch|delete|all)\(' src/ \
  | grep -oP "['\"]/[^'\"]*['\"]" | tr -d "'\""

# FastAPI
grep -rnE '@app\.(get|post|put|patch|delete)\(' . \
  | grep -oP '["'"'"']/[^"'"'"']*["'"'"']' | tr -d "\"'"

# Next.js App Router (file-based routing)
find app/ -name 'route.ts' -o -name 'route.js' -o -name 'page.tsx' \
  -o -name 'page.jsx' | sed 's|/route\.[tj]s||;s|/page\.[tj]sx||;s|^app||'

# Flask
grep -rnE "@app\.route\(" . | grep -oP "['\"]/[^'\"]*['\"]" | tr -d "'\""

# Rails
[ -f config/routes.rb ] && cat config/routes.rb

# Django
find . -name 'urls.py' \
  -not -path '*/node_modules/*' \
  -not \( -path '*/.*' -not -path '*/.github/*' \) \
  -exec cat {} +

# Go (net/http, gorilla/mux, chi, gin)
grep -rnE '\.(Handle|HandleFunc|Get|Post|Put|Delete|Patch)\(' . \
  --exclude-dir='.*' \
  | grep -oP '["'"'"']/[^"'"'"']*["'"'"']' | tr -d "\"'"
```

### Config key extraction

```bash
# Node.js env var reads
grep -rnE 'process\.env\.[A-Z_]+' src/ | grep -oP 'process\.env\.\K[A-Z_]+' | sort -u

# Python env var reads
grep -rnE "(os\.getenv|os\.environ)" . --exclude-dir='.*' \
  | grep -oP "['\"]\K[A-Z_]+(?=['\"])" | sort -u

# .env.example keys (what's documented)
[ -f .env.example ] && grep -oP '^[A-Z_]+' .env.example | sort -u

# Diff: keys used in code vs. keys documented
comm -23 <(code_keys_sorted) <(doc_keys_sorted)  # in code but not documented
comm -13 <(code_keys_sorted) <(doc_keys_sorted)  # documented but not in code
```

## 5. Inline documentation detection

Don't individually classify each docstring, but note the overall posture:

```bash
# Python docstrings — rough coverage estimate
total_funcs=$(grep -rc 'def ' --include='*.py' --exclude-dir='.*' . | awk -F: '{s+=$2}END{print s}')
documented=$(grep -rcP '"""' --include='*.py' --exclude-dir='.*' . | awk -F: '{s+=$2}END{print s/2}')
echo "Python: ~$documented docstrings for ~$total_funcs functions"

# JSDoc coverage
total_funcs=$(grep -rcE '(function |=>|export (async )?function)' --include='*.ts' --include='*.js' --exclude-dir='.*' .)
documented=$(grep -rc '/\*\*' --include='*.ts' --include='*.js' --exclude-dir='.*' .)
echo "JS/TS: ~$documented JSDoc blocks"

# Rust doc comments
grep -rc '///' --include='*.rs' --exclude-dir='.*' . | awk -F: '{s+=$2}END{print "Rust: ~"s" doc comments"}'
```

## 6. Edge cases

- **Hidden directories**: Exclude all directories whose names start with `.`
  (e.g. `.iande/`, `.cache/`, `.venv/`, `.doc-quarantine/`, `.git/`) from
  every discovery sweep. Use the compound predicate
  `-not \( -path '*/.*' -not -path '*/.github/*' \)` in `find`, or
  `--exclude-dir='.*'` in `grep`. The sole exception is `.github/` — it
  contains legitimate documentation artifacts (see below).
- **Monorepos**: Each package/workspace may have its own README, CHANGELOG,
  and doc structure. Discover per-package docs separately.
- **Git submodules**: Skip by default. Note their presence.
- **Symlinks**: Follow but note. A symlinked doc is not orphaned just because
  the link target moved.
- **Binary docs**: PDF, DOCX in the repo. Flag them — they are almost always
  stale because they cannot be diffed or auto-generated.
- **GitHub-specific**: `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`,
  `.github/FUNDING.yml` — these are docs too. Include them.
- **License files**: Detect but do not classify as stale/deprecated. License
  files have a different lifecycle.01KM23VWVQWH62NBFF0TTFWVXR