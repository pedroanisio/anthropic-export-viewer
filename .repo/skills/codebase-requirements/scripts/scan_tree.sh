#!/usr/bin/env bash
# scan_tree.sh — Generate an annotated file tree for codebase orientation.
#
# Usage: bash scan_tree.sh /path/to/repo [max_depth]
#
# Outputs:
#   1. Directory structure with file counts and sizes
#   2. File type distribution (by extension)
#   3. Largest files (potential binaries/generated code)
#   4. Total project stats
#
# Excludes: node_modules, .git, __pycache__, vendor, dist, build,
#           .next, target, coverage, .tox, .mypy_cache, .pytest_cache

set -euo pipefail

REPO="${1:-.}"
MAX_DEPTH="${2:-3}"

if [ ! -d "$REPO" ]; then
  echo "Error: '$REPO' is not a directory" >&2
  exit 1
fi

cd "$REPO"

EXCLUDE_DIRS=(
  node_modules .git __pycache__ vendor dist build .next target
  coverage .tox .mypy_cache .pytest_cache .venv venv env
  .terraform .serverless .parcel-cache .cache .turbo
  .output .nuxt .svelte-kit
)

FIND_PRUNE=""
for dir in "${EXCLUDE_DIRS[@]}"; do
  FIND_PRUNE="$FIND_PRUNE -name $dir -prune -o"
done

echo "=============================="
echo "CODEBASE SCAN — $(basename "$(pwd)")"
echo "=============================="
echo "Path: $(pwd)"
echo "Date: $(date -Iseconds 2>/dev/null || date)"
echo ""

# --- Section 1: Directory tree ---
echo "## Directory Structure (depth $MAX_DEPTH)"
echo ""

find . $FIND_PRUNE -type d -print 2>/dev/null | \
  awk -F/ -v max="$MAX_DEPTH" '
    NF-1 <= max {
      indent = ""
      for (i = 2; i < NF; i++) indent = indent "  "
      dir = $NF
      if (dir == ".") dir = "."
      print indent dir "/"
    }
  ' | head -200

echo ""

# --- Section 2: File type distribution ---
echo "## File Type Distribution"
echo ""
echo "| Extension | Count | Total Lines |"
echo "|-----------|-------|-------------|"

find . $FIND_PRUNE -type f -print 2>/dev/null | \
  sed 's/.*\.//' | sort | uniq -c | sort -rn | head -30 | \
  while read count ext; do
    # Get line count for this extension (approximate, skip binaries)
    lines=$(find . $FIND_PRUNE -type f -name "*.$ext" -print 2>/dev/null | \
            head -500 | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}')
    printf "| .%-8s | %5d | %11s |\n" "$ext" "$count" "${lines:-N/A}"
  done

echo ""

# --- Section 3: Largest files ---
echo "## Largest Files (top 15)"
echo ""
echo "| Size | Path |"
echo "|------|------|"

find . $FIND_PRUNE -type f -print 2>/dev/null | \
  xargs ls -la 2>/dev/null | sort -k5 -rn | head -15 | \
  awk '{ printf "| %s | %s |\n", $5, $NF }'

echo ""

# --- Section 4: Root-level files ---
echo "## Root-Level Files"
echo ""

ls -la 2>/dev/null | grep -v '^d' | grep -v '^total' | \
  awk '{ printf "  %s (%s bytes)\n", $NF, $5 }'

echo ""

# --- Section 5: Summary stats ---
echo "## Summary"
echo ""

total_files=$(find . $FIND_PRUNE -type f -print 2>/dev/null | wc -l)
total_dirs=$(find . $FIND_PRUNE -type d -print 2>/dev/null | wc -l)
total_loc=$(find . $FIND_PRUNE -type f \( -name '*.ts' -o -name '*.tsx' -o -name '*.js' -o -name '*.jsx' -o -name '*.py' -o -name '*.go' -o -name '*.rs' -o -name '*.java' -o -name '*.rb' -o -name '*.cs' -o -name '*.php' -o -name '*.swift' -o -name '*.kt' -o -name '*.scala' -o -name '*.c' -o -name '*.cpp' -o -name '*.h' \) -print 2>/dev/null | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}')

echo "Total files: $total_files"
echo "Total directories: $total_dirs"
echo "Source LOC (approx): ${total_loc:-0}"

# Detect primary language
primary=$(find . $FIND_PRUNE -type f -print 2>/dev/null | \
  sed 's/.*\.//' | sort | uniq -c | sort -rn | \
  grep -E '(ts|tsx|js|jsx|py|go|rs|java|rb|cs|php|swift|kt|scala|c|cpp)$' | \
  head -1 | awk '{print $2}')
echo "Primary language: ${primary:-unknown} (by file count)"

# Detect package manager
if [ -f "pnpm-lock.yaml" ]; then echo "Package manager: pnpm"
elif [ -f "yarn.lock" ]; then echo "Package manager: yarn"
elif [ -f "bun.lockb" ]; then echo "Package manager: bun"
elif [ -f "package-lock.json" ]; then echo "Package manager: npm"
elif [ -f "Pipfile.lock" ]; then echo "Package manager: pipenv"
elif [ -f "poetry.lock" ]; then echo "Package manager: poetry"
elif [ -f "Cargo.lock" ]; then echo "Package manager: cargo"
elif [ -f "go.sum" ]; then echo "Package manager: go modules"
elif [ -f "Gemfile.lock" ]; then echo "Package manager: bundler"
else echo "Package manager: not detected"
fi

echo ""
echo "=============================="
echo "Scan complete."
