# Procedures — Agent Task Coordination v1.0

This file contains the exact step-by-step procedures for every
protocol operation. Follow them in order. Do not skip steps.

---

## §1 — Opening a task

Execute these steps before editing any file in the repository.

### Step 1.1: Ensure `.agent-tasks/` exists

```bash
# At the repository root:
mkdir -p .agent-tasks/locks .agent-tasks/archive
# Initialize registry if it doesn't exist:
[ -f .agent-tasks/registry.json ] || echo '[]' > .agent-tasks/registry.json
```

### Step 1.2: Generate identifiers

Generate the task ID and agent ID per the format rules in
`protocol-spec.md` §2:

```bash
TASK_ID="task-$(date +%s%3N)-$(openssl rand -hex 2)"
```

For the agent ID, prefer any externally provided identifier. If
none exists, generate one that is stable for the session.

### Step 1.3: Enumerate target files

List every file you intend to create, edit, or delete. Be specific:

- Use repo-relative paths (e.g., `src/auth/login.ts`, not `login.ts`).
- If you are not yet certain which files you will touch, list your
  best estimate and note that scope may change.
- Do NOT list files you intend only to read.

### Step 1.4: Write the task entry

Create the task object and append it to `registry.json`:

```jsonc
{
  "task_id": "<generated>",
  "agent_id": "<your agent ID>",
  "objective": "<clear, specific description of what you will accomplish>",
  "declared_files": ["path/to/file1.ts", "path/to/file2.ts"],
  "status": "open",
  "opened_at": "<ISO 8601 now>",
  "updated_at": "<ISO 8601 now>",
  "closed_at": null,
  "result_summary": null,
  "actual_files": null,
  "scope_changes": [],
  "blocked_by": null
}
```

Read `registry.json`, append your task, write it back. Use
atomic-write-via-rename if possible:

```bash
# Read, append, write atomically
tmp=$(mktemp)
jq --argjson task "$TASK_JSON" '. += [$task]' .agent-tasks/registry.json > "$tmp" \
  && mv "$tmp" .agent-tasks/registry.json
```

### Step 1.5: Announce

Print to the user/log:

```
📋 TASK OPENED: <task-id>
   Agent:     <agent-id>
   Objective: <objective text>
   Files:     <comma-separated file list>
   Status:    open
```

This announcement is not optional. The user must see what the agent
intends to do before it does it.

---

## §2 — Checking for lock conflicts

Execute these steps after opening a task and before acquiring locks.

### Step 2.1: List existing locks

```bash
ls .agent-tasks/locks/*.lock 2>/dev/null
```

For each `.lock` file found, read its content.

### Step 2.2: Compute hashes for your declared files

For each file in your `declared_files`, compute the lock hash:

```bash
echo -n "<repo-relative-path>" | sha256sum | cut -c1-16
```

### Step 2.3: Check for conflicts

For each of your declared files, check whether a `.lock` file with
the matching hash exists AND is not stale AND is not owned by you.

Decision matrix:

| Lock exists? | Stale? | Owned by you? | Action |
|-------------|--------|---------------|--------|
| No | — | — | Proceed (no conflict) |
| Yes | Yes | — | Recover stale lock (§6), then proceed |
| Yes | No | Yes | Already locked by your task — proceed |
| Yes | No | No | **CONFLICT** — do not proceed |

### Step 2.4: Handle conflicts

If any conflict is found:

1. **Report** to the user which files are blocked and by which
   agent/task:

   ```
   ⚠️ LOCK CONFLICT on task <your-task-id>:
      File:       src/auth/login.ts
      Locked by:  agent-claude-8a3f (task-1712345678901-b1c2)
      Acquired:   2026-04-05T14:30:00Z
      TTL:        120 min (expires ~16:30 UTC)
   ```

2. **Transition** your task to `blocked`, setting `blocked_by` to
   the conflicting task ID.

3. **Present options** to the user:
   - Wait for the blocking task to complete.
   - Remove the conflicting files from your scope and proceed
     with the rest.
   - Ask the user to coordinate with the other agent.

4. **Do not proceed with editing the blocked files.** You may
   proceed with unblocked files if you adjust your scope.

---

## §3 — Acquiring locks

Execute only after §2 confirms no conflicts.

### Step 3.1: Create lock files

For each file in `declared_files`, create the lock file:

```bash
HASH=$(echo -n "src/auth/login.ts" | sha256sum | cut -c1-16)
cat > ".agent-tasks/locks/${HASH}.lock" << 'EOF'
{
  "locked_path": "src/auth/login.ts",
  "task_id": "task-...",
  "agent_id": "agent-...",
  "acquired_at": "2026-04-05T14:30:00Z",
  "ttl_minutes": 120
}
EOF
```

### Step 3.2: Verify acquisition

Re-read each lock file you just wrote and confirm your agent_id
is the owner. If another agent overwrote a lock between your check
(§2) and your acquire (§3), you have a race condition — back off,
re-check, and retry.

### Step 3.3: Transition task to `in-progress`

Update your task entry in `registry.json`:
- `status` → `"in-progress"`
- `updated_at` → current timestamp

### Step 3.4: Announce transition

```
🔒 TASK IN PROGRESS: <task-id>
   Agent:     <agent-id>
   Locks:     <list of locked files>
   Status:    in-progress
```

Now — and only now — the agent may begin editing files.

---

## §4 — Completing a task

Execute when the objective is accomplished.

### Step 4.1: Compile results

Determine:
- Which files were actually modified (may differ from declared).
- A brief summary of what was done.

### Step 4.2: Release all locks

For each file in your `declared_files` (and any files added via
scope changes), delete the lock file:

```bash
HASH=$(echo -n "src/auth/login.ts" | sha256sum | cut -c1-16)
rm -f ".agent-tasks/locks/${HASH}.lock"
```

**Release ALL locks**, including for files you declared but did not
end up modifying. Dangling locks block other agents for no reason.

### Step 4.3: Transition task to `completed`

Update your task entry:
- `status` → `"completed"`
- `closed_at` → current timestamp
- `updated_at` → current timestamp
- `result_summary` → brief summary
- `actual_files` → list of files actually modified

### Step 4.4: Archive

1. Write the final task object to `.agent-tasks/archive/<task-id>.json`.
2. Remove your entry from `registry.json`.

### Step 4.5: Announce completion

```
✅ TASK COMPLETED: <task-id>
   Agent:     <agent-id>
   Objective: <original objective>
   Result:    <summary of what was done>
   Files:     <actual files modified>
   Status:    completed
```

---

## §5 — Failing or abandoning a task

If the task cannot be completed (error) or is cancelled (user abort),
the procedure mirrors §4 with different status values.

### For failure:

- Status: `"failed"`
- Result summary: describe the error and what was attempted.
- Announcement prefix: `❌ TASK FAILED`

### For abandonment:

- Status: `"abandoned"`
- Result summary: describe why (e.g., "user cancelled",
  "scope no longer relevant").
- Announcement prefix: `🚫 TASK ABANDONED`

### Critical: locks MUST still be released

This is the most common protocol violation. Failure and abandonment
do not exempt the agent from releasing locks. Execute §4.2 (release
locks) before any terminal announcement.

### Fail-safe for unclean exit

If the agent's session ends without a clean shutdown (crash, timeout,
disconnection), locks will remain until TTL expiry. This is why TTL
exists — it is the fail-safe for scenarios where the clean shutdown
procedure cannot execute. Other agents can recover these stale locks
via §6.

---

## §6 — Stale lock recovery

Any agent may recover stale locks discovered during §2.

### Step 6.1: Determine staleness

A lock is stale when:

```
now > lock.acquired_at + lock.ttl_minutes
```

### Step 6.2: Check owning task

Read `registry.json` and find the task referenced by
`lock.task_id`. Three cases:

| Task exists? | Task status | Action |
|-------------|------------|--------|
| No | — | Lock is orphaned. Delete it. |
| Yes | `in-progress` | Transition task to `failed` (stale recovery). Then delete lock. |
| Yes | any terminal | Lock is orphaned (task closed but forgot to release). Delete it. |

### Step 6.3: Delete the stale lock

```bash
rm -f ".agent-tasks/locks/<hash>.lock"
```

### Step 6.4: Log the recovery

Append to your task's scope changes or announce to the user:

```
🔓 STALE LOCK RECOVERED:
   File:           src/auth/login.ts
   Original owner: agent-claude-8a3f (task-1712345678901-b1c2)
   Acquired:       2026-04-05T14:30:00Z
   TTL expired:    2026-04-05T16:30:00Z
   Recovered by:   <your agent-id>
```

---

## §7 — Scope changes (adding/removing files mid-task)

If during work the agent discovers it needs to edit a file not in
the original `declared_files`:

### Step 7.1: Pause editing

Do not touch the new file yet.

### Step 7.2: Check for locks (§2) on the new file only

### Step 7.3: Acquire the lock (§3) if no conflict

### Step 7.4: Update your task

Add the file to `declared_files` and log the scope change:

```jsonc
{
  "action": "added",
  "file": "src/utils/helpers.ts",
  "reason": "discovered shared utility needs updating for new auth flow",
  "timestamp": "2026-04-05T15:10:00Z"
}
```

### Step 7.5: Announce

```
📝 SCOPE CHANGE on task <task-id>:
   Added:  src/utils/helpers.ts
   Reason: <why this file is now needed>
```

To remove a file from scope (you realize you do not need to edit it):

1. Release its lock.
2. Remove from `declared_files`.
3. Log the scope change with action `"removed"`.
4. Announce the change.

---

## §8 — Reading the task board (status overview)

To understand the current state of all active work:

```bash
# Pretty-print the active task registry
cat .agent-tasks/registry.json | jq '
  .[] | {
    task_id,
    agent_id,
    status,
    objective: .objective[0:80],
    files: (.declared_files | length),
    opened: .opened_at
  }
'

# List all current locks
for f in .agent-tasks/locks/*.lock; do
  [ -f "$f" ] && jq '{locked_path, agent_id, acquired_at}' "$f"
done
```

Agents should consult the task board before opening a task to
understand the landscape — not just to check locks but to understand
what other agents are working on. Two agents editing different files
in the same module may still want to coordinate even if there is no
lock conflict.

---

## §9 — Example: full session walkthrough

Agent `agent-claude-a1b2c3d4` needs to fix a bug in the login flow.

**1. Open task:**
```
📋 TASK OPENED: task-1712345678901-f3e2
   Agent:     agent-claude-a1b2c3d4
   Objective: Fix null-pointer exception in login validation
   Files:     src/auth/login.ts, src/auth/__tests__/login.test.ts
   Status:    open
```

**2. Check locks:**
- `src/auth/login.ts` → hash `a1b2c3d4e5f6a7b8` → no lock file found ✓
- `src/auth/__tests__/login.test.ts` → hash `9f8e7d6c5b4a3210` → no lock file found ✓

**3. Acquire locks and begin:**
```
🔒 TASK IN PROGRESS: task-1712345678901-f3e2
   Agent:     agent-claude-a1b2c3d4
   Locks:     src/auth/login.ts, src/auth/__tests__/login.test.ts
   Status:    in-progress
```

**4. Mid-work scope change:**
Agent discovers it also needs to update a shared validator:
```
📝 SCOPE CHANGE on task task-1712345678901-f3e2:
   Added:  src/shared/validators.ts
   Reason: login validation uses shared email validator that also has the bug
```

**5. Complete:**
```
✅ TASK COMPLETED: task-1712345678901-f3e2
   Agent:     agent-claude-a1b2c3d4
   Objective: Fix null-pointer exception in login validation
   Result:    Added null check in validateEmail(), updated tests, all passing
   Files:     src/auth/login.ts, src/auth/__tests__/login.test.ts, src/shared/validators.ts
   Status:    completed
```

All three locks released. Task archived.
