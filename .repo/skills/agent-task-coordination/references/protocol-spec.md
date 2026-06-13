# Protocol Specification — Agent Task Coordination v1.0

## §1 — Directory structure

The protocol operates entirely within `.agent-tasks/` at the
repository root. All paths below are relative to that directory.

```
.agent-tasks/
├── registry.json          # active task registry
├── locks/                 # lock files (one per locked path)
│   └── <hash>.lock        # individual lock file
├── archive/               # terminal tasks moved here
│   └── <task-id>.json     # archived task snapshot
└── config.json            # optional protocol configuration
```

### Why `.agent-tasks/`?

The dot-prefix keeps it hidden from most file browsers and clearly
marks it as tooling infrastructure. It SHOULD be added to
`.gitignore` unless the team wants coordination state versioned
(unusual but valid for audit purposes).

## §2 — Task object schema

Every task is a JSON object with these fields:

```jsonc
{
  // Required fields
  "task_id":        "string",   // unique, format: "task-<timestamp>-<random4>"
  "agent_id":       "string",   // who opened it
  "objective":      "string",   // what the agent intends to accomplish
  "declared_files": ["string"], // repo-relative paths the agent intends to edit
  "status":         "string",   // one of the lifecycle states (see §3)
  "opened_at":      "string",   // ISO 8601 timestamp
  "updated_at":     "string",   // ISO 8601 timestamp, updated on every transition

  // Set on transition to terminal state
  "closed_at":      "string | null",
  "result_summary": "string | null",  // what was actually done
  "actual_files":   ["string"] | null, // files actually modified (may differ from declared)

  // Optional
  "scope_changes":  [           // log of files added/removed mid-task
    {
      "action":     "added | removed",
      "file":       "string",
      "reason":     "string",
      "timestamp":  "string"
    }
  ],
  "blocked_by":     "string | null"   // task_id of blocking task (if status = blocked)
}
```

### Task ID generation

Format: `task-<unix-millis>-<random4hex>`

Example: `task-1712345678901-a3f2`

The combination of timestamp and random suffix is sufficient to
avoid collisions across concurrent agents. If a collision occurs
(astronomically unlikely), the second agent re-generates.

### Agent ID generation

Prefer an externally assigned identifier if available (environment
variable, CLI flag, session ID). If none exists, generate:

`agent-<model-short-name>-<first-8-chars-of-session-hash>`

Example: `agent-claude-4f9a2b1c`

The agent ID should remain stable within a session so that lock
ownership can be validated.

## §3 — Task lifecycle states

```
States:        open → in-progress → completed
                                  → failed
                                  → abandoned
               open → blocked     → (re-opened as open when unblocked)
```

| State | Meaning | Locks held? |
|-------|---------|-------------|
| `open` | Task declared, locks not yet acquired | No |
| `in-progress` | Locks acquired, agent is editing files | Yes |
| `completed` | Objective accomplished, locks released | No |
| `failed` | Unrecoverable error, locks released | No |
| `abandoned` | User or agent cancelled, locks released | No |
| `blocked` | Cannot proceed — file conflict detected | No |

**Invariant**: locks are held if and only if status is `in-progress`.

Transitions:

| From | To | Trigger | Action |
|------|----|---------|--------|
| `open` | `in-progress` | All locks acquired | Acquire locks |
| `open` | `blocked` | Lock conflict found | Set `blocked_by` |
| `blocked` | `open` | Blocking task completed | Clear `blocked_by` |
| `in-progress` | `completed` | Objective done | Release locks, archive |
| `in-progress` | `failed` | Unrecoverable error | Release locks, archive |
| `in-progress` | `abandoned` | User/agent cancels | Release locks, archive |

**Illegal transitions**: any transition not listed above is a protocol
violation. In particular, `open → completed` is illegal — you cannot
complete a task without having been `in-progress` (which means locks
were acquired and files were actually edited).

## §4 — Lock semantics

### Lock file format

Each lock is a file in `.agent-tasks/locks/`. The filename is a
deterministic hash of the locked path:

Filename: `<sha256-hex-prefix-16>.lock`

Content (JSON):

```jsonc
{
  "locked_path": "string",     // repo-relative path being locked
  "task_id":     "string",     // which task holds this lock
  "agent_id":    "string",     // which agent holds this lock
  "acquired_at": "string",     // ISO 8601
  "ttl_minutes": 120           // time-to-live in minutes (default 120)
}
```

### Lock granularity

Locks are per-file. Locking a directory is not supported — lock
each file individually. This prevents over-broad locks that block
agents unnecessarily.

If an agent needs to create a new file that does not yet exist,
it locks the *intended path* before creating it. This prevents two
agents from racing to create the same file.

### Hash computation

Use the first 16 hex characters of SHA-256 of the repo-relative
path (normalized: forward slashes, no leading `./`, no trailing `/`).

Example:
- Path: `src/auth/login.ts`
- SHA-256: `a1b2c3d4e5f6a7b8...`
- Lock file: `.agent-tasks/locks/a1b2c3d4e5f6a7b8.lock`

In bash:
```bash
echo -n "src/auth/login.ts" | sha256sum | cut -c1-16
```

In TypeScript:
```typescript
import { createHash } from "crypto";
const lockHash = (path: string) =>
  createHash("sha256").update(path).digest("hex").slice(0, 16);
```

### Lock ownership

A lock is owned by the `(agent_id, task_id)` pair. Only the owning
agent may release the lock, with one exception: stale lock recovery
(see below).

### Stale locks

A lock is stale when:

```
current_time > acquired_at + ttl_minutes
```

Any agent may forcibly release a stale lock. The releasing agent
MUST:

1. Log the forced release (who released, original owner, how stale).
2. Check whether the owning task is still in `in-progress`. If so,
   transition it to `failed` with reason "stale lock recovery".

Default TTL is 120 minutes. Override via `.agent-tasks/config.json`:

```json
{
  "lock_ttl_minutes": 180,
  "max_files_per_task": 20,
  "archive_completed_tasks": true
}
```

### No nested locks

If agent A holds a lock on `src/utils.ts` under task T1, agent A
cannot acquire a second lock on the same file under task T2. One
file, one lock, one task.

## §5 — Registry file (`registry.json`)

The registry is a JSON array of active task objects:

```json
[
  { "task_id": "task-...", "agent_id": "...", ... },
  { "task_id": "task-...", "agent_id": "...", ... }
]
```

When a task reaches a terminal state (`completed`, `failed`,
`abandoned`), it is:

1. Removed from `registry.json`.
2. Written to `archive/<task-id>.json`.

This keeps the registry small and fast to parse.

### Concurrency on the registry file

Multiple agents may try to read/write `registry.json`
simultaneously. The protocol uses a simple last-write-wins model
with conflict detection:

1. Read the file.
2. Parse it.
3. Make your change (add/update/remove your task).
4. Write the file.

If another agent's task appears or disappears between your read
and write, that is acceptable — you are only modifying your own
entry. However, if your own entry was modified by another process
between read and write, re-read and retry.

For filesystems that support atomic writes, prefer
write-to-temp-then-rename.

## §6 — Archival

Archived tasks are stored as individual JSON files at:

```
.agent-tasks/archive/<task-id>.json
```

The archive serves two purposes:

1. **Audit trail**: who changed what, when, and why.
2. **Conflict analysis**: if files keep conflicting, the archive
   reveals patterns.

Archive files are never modified once written. They may be pruned
periodically (manually or via configuration).

## §7 — Configuration (`config.json`)

Optional file at `.agent-tasks/config.json`:

```jsonc
{
  "lock_ttl_minutes": 120,          // default lock TTL
  "max_files_per_task": 20,         // guard against over-broad tasks
  "archive_completed_tasks": true,  // if false, terminal tasks are deleted
  "require_objective": true,        // if false, objective can be empty
  "allowed_agents": []              // if non-empty, only these agent IDs may open tasks
}
```

All fields are optional. Defaults are used for any missing field.
