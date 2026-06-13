#!/usr/bin/env bash
# agent-task-coordination helper — source this or call functions directly.
# Usage:  source /path/to/task-helpers.sh
#         atc_init
#         atc_open "Fix login bug" "src/auth/login.ts src/auth/login.test.ts"
#         atc_check_locks
#         atc_acquire_locks
#         ... do work ...
#         atc_complete "Added null check, tests passing"

set -euo pipefail

# ── Configuration ──────────────────────────────────────────────────
ATC_DIR=".agent-tasks"
ATC_REGISTRY="$ATC_DIR/registry.json"
ATC_LOCKS="$ATC_DIR/locks"
ATC_ARCHIVE="$ATC_DIR/archive"
ATC_CONFIG="$ATC_DIR/config.json"
ATC_DEFAULT_TTL=120

# ── State (set by atc_open) ───────────────────────────────────────
ATC_TASK_ID=""
ATC_AGENT_ID="${ATC_AGENT_ID:-agent-$(whoami)-$(head -c4 /dev/urandom | xxd -p)}"
ATC_OBJECTIVE=""
ATC_FILES=()

# ── Helpers ────────────────────────────────────────────────────────
_atc_now()   { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
_atc_millis(){ date +%s%3N 2>/dev/null || python3 -c "import time; print(int(time.time()*1000))"; }
_atc_hash()  { echo -n "$1" | sha256sum | cut -c1-16; }
_atc_ttl()   {
  if [ -f "$ATC_CONFIG" ]; then
    jq -r '.lock_ttl_minutes // 120' "$ATC_CONFIG"
  else
    echo "$ATC_DEFAULT_TTL"
  fi
}

# ── §1: Initialize ────────────────────────────────────────────────
atc_init() {
  mkdir -p "$ATC_LOCKS" "$ATC_ARCHIVE"
  [ -f "$ATC_REGISTRY" ] || echo '[]' > "$ATC_REGISTRY"
  echo "✓ .agent-tasks/ initialized"
}

# ── §1: Open a task ───────────────────────────────────────────────
# Usage: atc_open "objective" "file1 file2 file3"
atc_open() {
  local objective="$1"
  local files_str="$2"
  read -ra ATC_FILES <<< "$files_str"

  ATC_TASK_ID="task-$(_atc_millis)-$(openssl rand -hex 2)"
  ATC_OBJECTIVE="$objective"
  local now; now=$(_atc_now)

  local files_json
  files_json=$(printf '%s\n' "${ATC_FILES[@]}" | jq -R . | jq -s .)

  local task_json
  task_json=$(jq -n \
    --arg tid "$ATC_TASK_ID" \
    --arg aid "$ATC_AGENT_ID" \
    --arg obj "$objective" \
    --argjson files "$files_json" \
    --arg now "$now" \
    '{
      task_id: $tid,
      agent_id: $aid,
      objective: $obj,
      declared_files: $files,
      status: "open",
      opened_at: $now,
      updated_at: $now,
      closed_at: null,
      result_summary: null,
      actual_files: null,
      scope_changes: [],
      blocked_by: null
    }')

  local tmp; tmp=$(mktemp)
  jq --argjson task "$task_json" '. += [$task]' "$ATC_REGISTRY" > "$tmp" \
    && mv "$tmp" "$ATC_REGISTRY"

  echo "📋 TASK OPENED: $ATC_TASK_ID"
  echo "   Agent:     $ATC_AGENT_ID"
  echo "   Objective: $objective"
  echo "   Files:     ${ATC_FILES[*]}"
  echo "   Status:    open"
}

# ── §2: Check locks ──────────────────────────────────────────────
# Returns 0 if all clear, 1 if conflicts found.
# Prints conflict details to stdout.
atc_check_locks() {
  local conflicts=0
  local ttl; ttl=$(_atc_ttl)
  local now_epoch; now_epoch=$(date +%s)

  for filepath in "${ATC_FILES[@]}"; do
    local hash; hash=$(_atc_hash "$filepath")
    local lockfile="$ATC_LOCKS/${hash}.lock"

    if [ -f "$lockfile" ]; then
      local lock_agent lock_task lock_time lock_ttl
      lock_agent=$(jq -r '.agent_id' "$lockfile")
      lock_task=$(jq -r '.task_id' "$lockfile")
      lock_time=$(jq -r '.acquired_at' "$lockfile")
      lock_ttl=$(jq -r '.ttl_minutes' "$lockfile")

      # Check staleness
      local lock_epoch; lock_epoch=$(date -d "$lock_time" +%s 2>/dev/null || python3 -c "from datetime import datetime; print(int(datetime.fromisoformat('${lock_time}'.replace('Z','+00:00')).timestamp()))")
      local expires_epoch=$(( lock_epoch + lock_ttl * 60 ))

      if [ "$now_epoch" -gt "$expires_epoch" ]; then
        echo "🔓 STALE LOCK on $filepath — recovering..."
        rm -f "$lockfile"
        echo "   Recovered stale lock (owner: $lock_agent, task: $lock_task)"
        continue
      fi

      # Not stale — check ownership
      if [ "$lock_agent" = "$ATC_AGENT_ID" ] && [ "$lock_task" = "$ATC_TASK_ID" ]; then
        echo "   $filepath — already locked by this task ✓"
        continue
      fi

      # Conflict
      conflicts=1
      echo "⚠️  LOCK CONFLICT:"
      echo "   File:       $filepath"
      echo "   Locked by:  $lock_agent ($lock_task)"
      echo "   Acquired:   $lock_time"
      echo "   TTL:        ${lock_ttl} min"
    else
      echo "   $filepath — available ✓"
    fi
  done

  return $conflicts
}

# ── §3: Acquire locks ────────────────────────────────────────────
atc_acquire_locks() {
  local now; now=$(_atc_now)
  local ttl; ttl=$(_atc_ttl)

  for filepath in "${ATC_FILES[@]}"; do
    local hash; hash=$(_atc_hash "$filepath")
    local lockfile="$ATC_LOCKS/${hash}.lock"

    jq -n \
      --arg path "$filepath" \
      --arg tid "$ATC_TASK_ID" \
      --arg aid "$ATC_AGENT_ID" \
      --arg now "$now" \
      --argjson ttl "$ttl" \
      '{
        locked_path: $path,
        task_id: $tid,
        agent_id: $aid,
        acquired_at: $now,
        ttl_minutes: $ttl
      }' > "$lockfile"
  done

  # Transition to in-progress
  local tmp; tmp=$(mktemp)
  jq --arg tid "$ATC_TASK_ID" --arg now "$now" \
    'map(if .task_id == $tid then .status = "in-progress" | .updated_at = $now else . end)' \
    "$ATC_REGISTRY" > "$tmp" && mv "$tmp" "$ATC_REGISTRY"

  echo "🔒 TASK IN PROGRESS: $ATC_TASK_ID"
  echo "   Locks:  ${ATC_FILES[*]}"
  echo "   Status: in-progress"
}

# ── §4: Release locks ────────────────────────────────────────────
_atc_release_locks() {
  for filepath in "${ATC_FILES[@]}"; do
    local hash; hash=$(_atc_hash "$filepath")
    rm -f "$ATC_LOCKS/${hash}.lock"
  done
}

# ── §4: Complete task ─────────────────────────────────────────────
# Usage: atc_complete "summary of what was done" ["file1 file2"]
atc_complete() {
  local summary="$1"
  local actual_files="${2:-${ATC_FILES[*]}}"
  local now; now=$(_atc_now)

  _atc_release_locks

  local actual_json
  read -ra actual_arr <<< "$actual_files"
  actual_json=$(printf '%s\n' "${actual_arr[@]}" | jq -R . | jq -s .)

  # Update registry entry
  local tmp; tmp=$(mktemp)
  jq --arg tid "$ATC_TASK_ID" --arg now "$now" \
     --arg summary "$summary" --argjson actual "$actual_json" \
    'map(if .task_id == $tid then
       .status = "completed" |
       .closed_at = $now |
       .updated_at = $now |
       .result_summary = $summary |
       .actual_files = $actual
     else . end)' \
    "$ATC_REGISTRY" > "$tmp" && mv "$tmp" "$ATC_REGISTRY"

  # Archive
  jq --arg tid "$ATC_TASK_ID" '.[] | select(.task_id == $tid)' \
    "$ATC_REGISTRY" > "$ATC_ARCHIVE/${ATC_TASK_ID}.json"

  # Remove from registry
  tmp=$(mktemp)
  jq --arg tid "$ATC_TASK_ID" 'map(select(.task_id != $tid))' \
    "$ATC_REGISTRY" > "$tmp" && mv "$tmp" "$ATC_REGISTRY"

  echo "✅ TASK COMPLETED: $ATC_TASK_ID"
  echo "   Agent:     $ATC_AGENT_ID"
  echo "   Objective: $ATC_OBJECTIVE"
  echo "   Result:    $summary"
  echo "   Files:     $actual_files"
  echo "   Status:    completed"
}

# ── §5: Fail task ─────────────────────────────────────────────────
atc_fail() {
  local reason="$1"
  local now; now=$(_atc_now)

  _atc_release_locks

  local tmp; tmp=$(mktemp)
  jq --arg tid "$ATC_TASK_ID" --arg now "$now" --arg reason "$reason" \
    'map(if .task_id == $tid then
       .status = "failed" | .closed_at = $now | .updated_at = $now | .result_summary = $reason
     else . end)' \
    "$ATC_REGISTRY" > "$tmp" && mv "$tmp" "$ATC_REGISTRY"

  jq --arg tid "$ATC_TASK_ID" '.[] | select(.task_id == $tid)' \
    "$ATC_REGISTRY" > "$ATC_ARCHIVE/${ATC_TASK_ID}.json"

  tmp=$(mktemp)
  jq --arg tid "$ATC_TASK_ID" 'map(select(.task_id != $tid))' \
    "$ATC_REGISTRY" > "$tmp" && mv "$tmp" "$ATC_REGISTRY"

  echo "❌ TASK FAILED: $ATC_TASK_ID"
  echo "   Agent:  $ATC_AGENT_ID"
  echo "   Reason: $reason"
}

# ── §5: Abandon task ──────────────────────────────────────────────
atc_abandon() {
  local reason="${1:-User cancelled}"
  local now; now=$(_atc_now)

  _atc_release_locks

  local tmp; tmp=$(mktemp)
  jq --arg tid "$ATC_TASK_ID" --arg now "$now" --arg reason "$reason" \
    'map(if .task_id == $tid then
       .status = "abandoned" | .closed_at = $now | .updated_at = $now | .result_summary = $reason
     else . end)' \
    "$ATC_REGISTRY" > "$tmp" && mv "$tmp" "$ATC_REGISTRY"

  jq --arg tid "$ATC_TASK_ID" '.[] | select(.task_id == $tid)' \
    "$ATC_REGISTRY" > "$ATC_ARCHIVE/${ATC_TASK_ID}.json"

  tmp=$(mktemp)
  jq --arg tid "$ATC_TASK_ID" 'map(select(.task_id != $tid))' \
    "$ATC_REGISTRY" > "$tmp" && mv "$tmp" "$ATC_REGISTRY"

  echo "🚫 TASK ABANDONED: $ATC_TASK_ID"
  echo "   Agent:  $ATC_AGENT_ID"
  echo "   Reason: $reason"
}

# ── §7: Add file to scope ────────────────────────────────────────
# Usage: atc_add_file "path/to/new/file.ts" "reason"
atc_add_file() {
  local filepath="$1"
  local reason="$2"
  local now; now=$(_atc_now)

  # Check lock on new file
  local hash; hash=$(_atc_hash "$filepath")
  local lockfile="$ATC_LOCKS/${hash}.lock"

  if [ -f "$lockfile" ]; then
    local lock_agent; lock_agent=$(jq -r '.agent_id' "$lockfile")
    if [ "$lock_agent" != "$ATC_AGENT_ID" ]; then
      echo "⚠️  Cannot add $filepath — locked by $lock_agent"
      return 1
    fi
  fi

  # Acquire lock
  local ttl; ttl=$(_atc_ttl)
  jq -n --arg path "$filepath" --arg tid "$ATC_TASK_ID" \
    --arg aid "$ATC_AGENT_ID" --arg now "$now" --argjson ttl "$ttl" \
    '{ locked_path: $path, task_id: $tid, agent_id: $aid, acquired_at: $now, ttl_minutes: $ttl }' \
    > "$lockfile"

  ATC_FILES+=("$filepath")

  # Update registry
  local tmp; tmp=$(mktemp)
  local change
  change=$(jq -n --arg act "added" --arg f "$filepath" --arg r "$reason" --arg t "$now" \
    '{ action: $act, file: $f, reason: $r, timestamp: $t }')
  jq --arg tid "$ATC_TASK_ID" --arg f "$filepath" --argjson ch "$change" --arg now "$now" \
    'map(if .task_id == $tid then
       .declared_files += [$f] | .scope_changes += [$ch] | .updated_at = $now
     else . end)' \
    "$ATC_REGISTRY" > "$tmp" && mv "$tmp" "$ATC_REGISTRY"

  echo "📝 SCOPE CHANGE on $ATC_TASK_ID:"
  echo "   Added:  $filepath"
  echo "   Reason: $reason"
}

# ── §8: Show task board ──────────────────────────────────────────
atc_board() {
  echo "═══ ACTIVE TASKS ═══"
  jq -r '.[] | "  \(.status | ascii_upcase) | \(.task_id) | \(.agent_id) | \(.objective[0:60]) | files: \(.declared_files | length)"' \
    "$ATC_REGISTRY" 2>/dev/null || echo "  (no active tasks)"

  echo ""
  echo "═══ CURRENT LOCKS ═══"
  local found=0
  for f in "$ATC_LOCKS"/*.lock; do
    [ -f "$f" ] || continue
    found=1
    jq -r '"  \(.locked_path) ← \(.agent_id) (\(.task_id))"' "$f"
  done
  [ $found -eq 0 ] && echo "  (no active locks)"
}
