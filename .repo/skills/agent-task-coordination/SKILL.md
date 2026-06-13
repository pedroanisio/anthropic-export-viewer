---
name: agent-task-coordination
description: >
  Enforces a task-based coordination protocol for AI agents editing a shared
  repository. Every coding session MUST begin by opening a task, declaring
  target files and objectives, and checking for file locks held by other
  agents. The agent MUST announce completion and release locks when done.
  Trigger this skill whenever an AI agent is about to write, edit, refactor,
  delete, or move any file in a shared codebase. Also trigger on: "start
  coding", "open a task", "edit files", "begin work on", "implement",
  "fix bug in", "refactor", "modify", "update code", "coordinate agents",
  "lock file", "unlock file", "check locks", "task status", "agent
  coordination", "multi-agent editing", or any request that results in
  file modifications within a repository. If in doubt about whether another
  agent might be working on the same repo, trigger this skill. The cost
  of coordination is low; the cost of a merge conflict or overwritten
  work is high.
---

# Agent Task Coordination Protocol

## Purpose

When multiple AI agents operate on the same repository, uncoordinated
edits produce conflicts, overwrites, and wasted work. This skill
enforces a lightweight task protocol:

1. **Before touching any file**, the agent opens a task and declares
   intent.
2. **Before editing a file**, the agent checks whether another agent
   holds a lock on it.
3. **When work is done** (or abandoned), the agent closes the task and
   releases all locks.

The protocol uses a `.agent-tasks/` directory at the repository root
as its coordination surface. No external service is required — the
filesystem is the source of truth.

## Before starting — read the reference files

Before producing any output or writing any code, read:

1. `references/protocol-spec.md` — the full protocol specification
   including file formats, state machines, lock semantics, and
   conflict-resolution rules.
2. `references/procedures.md` — step-by-step procedures for every
   operation (open task, acquire lock, check locks, complete task,
   handle conflicts, recover stale locks).

**Both files are mandatory reading before any action.** The procedures
file contains the exact sequences to follow and the spec file contains
the data structures and invariants the protocol depends on.

## Quick reference — the lifecycle

```
  ┌─────────┐   agent declares   ┌─────────────┐
  │  (none)  │ ───────────────► │    open      │
  └─────────┘    intent + files  └──────┬──────┘
                                        │
                          locks acquired │
                                        ▼
                                 ┌─────────────┐
                                 │ in-progress  │◄──── (editing files)
                                 └──────┬──────┘
                                        │
                    ┌───────────┬────────┼────────┐
                    ▼           ▼        ▼        ▼
             ┌───────────┐ ┌────────┐ ┌────────┐ ┌─────────┐
             │ completed │ │ failed │ │ blocked│ │abandoned│
             └───────────┘ └────────┘ └────────┘ └─────────┘
                    │           │        │            │
                    └───────────┴────────┴────────────┘
                              locks released
```

Every terminal state releases all held locks. No exceptions.

## The mandatory sequence

Every coding session follows this exact sequence. Deviations are
protocol violations.

### 1. Initialize (if needed)

If `.agent-tasks/` does not exist at the repo root, create it:

```
.agent-tasks/
├── registry.json      # task registry (array of task objects)
├── locks/             # one file per locked path
└── archive/           # completed/failed tasks moved here
```

### 2. Open a task

Before writing or editing any file, create a task entry. See
`references/procedures.md` §1 for the exact procedure, but the
minimum announcement to the user/log is:

```
📋 TASK OPENED: <task-id>
   Agent:     <agent-identifier>
   Objective: <what you intend to accomplish>
   Files:     <list of files you intend to edit>
   Status:    open
```

The agent MUST identify itself. If no explicit agent ID is available,
generate one from context: `agent-<model>-<session-hash-prefix>`.

### 3. Check for lock conflicts

Before acquiring locks, check every declared file against existing
locks. See `references/procedures.md` §2. If ANY file is locked by
another agent:

- **DO NOT proceed with editing that file.**
- Report the conflict to the user with the blocking task ID and agent.
- Either wait, negotiate scope, or adjust the file list to avoid the
  conflict.

### 4. Acquire locks and begin work

Once all declared files are conflict-free, acquire locks and
transition the task to `in-progress`. Only then may the agent begin
editing files.

### 5. Announce completion

When the objective is accomplished (or the task fails/is abandoned),
the agent MUST:

1. Transition the task to a terminal state.
2. Release ALL held locks.
3. Announce the outcome:

```
✅ TASK COMPLETED: <task-id>
   Agent:     <agent-identifier>
   Objective: <original objective>
   Result:    <brief summary of what was done>
   Files:     <files that were actually modified>
   Status:    completed
```

### 6. Handle abnormal termination

If the agent encounters an unrecoverable error or the user aborts
the session, the agent must still release locks. See
`references/procedures.md` §5 for the fail-safe release procedure.

## Critical constraints

### Locks are mandatory, not optional

An agent that edits a file without holding its lock is in violation
of the protocol. The purpose of this skill is to prevent exactly
that scenario. Even if the agent is "certain" no other agent is
active, the lock must be acquired — certainty about concurrent
agents is not something any single agent can have.

### Stale lock recovery

Locks older than a configurable TTL (default: 2 hours) are
considered stale and may be forcibly released. See
`references/protocol-spec.md` §4 for the staleness rules and
`references/procedures.md` §6 for the recovery procedure.

### Scope changes require re-declaration

If during the course of work the agent discovers it needs to edit
a file not in the original declaration, it MUST:

1. Pause editing.
2. Check for locks on the new file.
3. Acquire the lock.
4. Update the task entry with the new file.
5. Announce the scope change.

### Never silently drop a task

Every opened task must reach a terminal state. If the user says
"never mind" or "stop", the agent must still close the task as
`abandoned` and release locks.

## What this skill is NOT

- **Not a version control system.** This protocol coordinates
  intent, not code. It does not replace git, handle merges, or
  track diffs. It prevents agents from stepping on each other
  before conflicts arise.
- **Not an access control system.** Locks are cooperative, not
  enforced by the filesystem. An agent that ignores this skill can
  still write anywhere. The protocol works because agents that
  load this skill follow it.
- **Not a project management tool.** Tasks here are ephemeral
  coordination units, not user stories or tickets.

## Common pitfalls

- **Forgetting to release locks on failure.** The terminal-state
  rule exists precisely for this. Every exit path must release locks.
- **Locking too broadly.** Lock individual files, not directories.
  If you need to edit `src/auth/login.ts`, lock that file — not all
  of `src/auth/`.
- **Not checking locks after scope changes.** Adding a file to your
  task mid-work without checking is a protocol violation.
- **Assuming "I'm the only agent."** You do not know that. Follow
  the protocol regardless.
