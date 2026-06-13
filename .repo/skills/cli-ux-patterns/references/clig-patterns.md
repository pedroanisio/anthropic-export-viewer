# CLI UX Pattern Catalog

Comprehensive reference for CLI interaction design patterns. Sourced from
clig.dev (Command Line Interface Guidelines), Lucas Costa's UX Patterns for
CLI Tools, Evil Martians' progress display research, and the Topiary CLI UX
case study. Each pattern includes rationale, anti-patterns, and cross-references
to clap implementation in `clap-recipes.md`.

---

## Table of Contents

1. [Philosophy](#1-philosophy)
2. [Help Text](#2-help-text)
3. [Output](#3-output)
4. [Errors](#4-errors)
5. [Arguments and Flags](#5-arguments-and-flags)
6. [Interactivity](#6-interactivity)
7. [Progress Indication](#7-progress-indication)
8. [Color and Visual Hierarchy](#8-color-and-visual-hierarchy)
9. [Composability](#9-composability)
10. [Context Awareness](#10-context-awareness)
11. [Naming](#11-naming)
12. [Type-Level Safety](#12-type-level-safety)
13. [Configuration](#13-configuration)
14. [Shell Completions](#14-shell-completions)
15. [Testing](#15-testing)

---

## 1. Philosophy

### 1.1 Human-First Design

Traditional UNIX commands were designed for programs-as-consumers. Modern CLIs
are used primarily by humans. If your command targets humans, design for them
first: clear defaults, helpful errors, discoverable features.

This does NOT mean abandoning composability. It means the human-readable path
is the default, and the machine-readable path is opt-in (`--json`, `--plain`).

### 1.2 Saying Just Enough

A command that hangs silently for minutes is saying too little. A command that
dumps pages of debug output is saying too much. Both leave the user confused.

**Rule of thumb:** surface progress for anything > 1 second. Suppress debug
output by default; gate it behind `--verbose` or `-v` (stackable: `-vvv`).

### 1.3 Conversation as the Norm

Using a CLI is inherently conversational: type, get feedback, adjust, repeat.
Design for this loop. Suggest corrections on typos. Show what to run next after
a successful operation. Confirm before destructive actions.

### 1.4 Empathy

The user is not an idiot who typed the wrong thing. They are a person trying to
get something done. Error messages should be helpful, not accusatory. Help text
should teach, not lecture.

### 1.5 Robustness (Subjective)

The tool should *feel* solid. No scary stack traces. No unexplained hangs. No
silent data loss. Subjective robustness comes from: keeping users informed,
explaining errors, handling edge cases gracefully, and confirming important
operations.

---

## 2. Help Text

### 2.1 Concise Default Help

When the tool is invoked with no arguments and requires them, show:
- A one-line description of what the program does.
- One or two example invocations (the most common use cases).
- A hint: "Run `mytool --help` for full options."

Do NOT dump the full flag list by default. That's what `--help` is for.

**Anti-pattern:** Printing a 200-line manual when the user just typed `mytool`.

### 2.2 Full Help on --help / -h

`-h` and `--help` should both show the complete help text. Do not overload `-h`
for another purpose. `--help` at the end of any invocation should show help,
ignoring other flags.

For git-like tools: `mytool help`, `mytool help subcommand`,
`mytool subcommand --help` should all work.

### 2.3 Lead with Examples

Users reach for examples before reading flag descriptions. Put them first or
near the top of help text. Show the actual output if it's short.

Build a narrative: start with the simplest invocation, then layer complexity.

### 2.4 Group by Workflow, Not Alphabet

Display the most common commands first. Group by what the user is trying to do
(e.g., "Getting Started", "Daily Use", "Advanced"). Git does this well.

### 2.5 Provide Escape Hatches

- Link to web documentation from help text.
- Provide a support path (GitHub issues URL, etc.).
- If examples are extensive, put them in a `mytool examples` subcommand or
  web page rather than bloating `--help`.

---

## 3. Output

### 3.1 Human-Readable by Default

If stdout is a TTY, format output for human eyes: aligned columns, color,
headers, sensible truncation.

### 3.2 Machine-Readable on Demand

Provide `--json` for structured output. Provide `--plain` for simple tabular
text that plays well with `grep`, `awk`, `cut`.

When `--json` is active: suppress all decorative output (spinners, color,
headers). Output valid JSON to stdout. Errors still go to stderr.

### 3.3 Respect the TTY

Detect whether stdout and stderr are TTYs. When piped:
- Disable color.
- Disable spinners/progress bars (or switch to log-line output).
- Disable interactive prompts (fail with a message about which flag to use).

### 3.4 Don't Modify Output Between Versions

Scripts depend on your output format. Changes to output structure are breaking
changes. If you must change, provide a versioned output format or a
compatibility flag.

---

## 4. Errors

### 4.1 The Three Components of a Good Error

Every error message should answer:
1. **What** happened — a clear, specific description.
2. **Why** it happened — root cause or context.
3. **What to try** — actionable recovery steps.

**Bad:** `Error: ENOENT`
**Good:** `Error: Configuration file not found at ~/.config/mytool/config.toml.
Run 'mytool init' to create a default configuration.`

### 4.2 Attribute Blame Correctly

Distinguish between:
- **User error:** invalid input, missing required args, wrong directory.
- **Tool error:** bug, unexpected state.
- **External error:** network failure, permissions, missing dependency.

Users need to know whose problem it is so they know where to look for a fix.

### 4.3 Suggest Corrections

When the user types an unrecognized command or value, suggest the closest match.
Clap does this automatically for subcommands via Damerau-Levenshtein distance.

Do NOT auto-correct destructive operations. Suggest, then let the user decide.

### 4.4 Error Codes for Searchability

Consider user-visible error codes (e.g., `E0308`, `HE0030`). They make it
trivial to search for solutions online and to link documentation.

### 4.5 Exit Codes

- 0 = success
- 1 = general error
- 2 = usage error (invalid arguments)
- 3+ = domain-specific errors

Map exit codes to your most important failure modes. Document them.

### 4.6 Never Print Stack Traces by Default

Stack traces are for developers, not users. Gate them behind `RUST_BACKTRACE=1`
or a `--debug` flag. In verbose mode, print the error cause chain — but
formatted, not raw.

---

## 5. Arguments and Flags

### 5.1 Positional Arguments are for the "Direct Object"

The first positional argument should be the direct object of the command's verb.
`mytool compile <FILE>` — FILE is what you're compiling.

If there are multiple positional args, their order should follow natural
English reading order of the operation.

### 5.2 Prefer Flags for Optional Behavior

Flags are self-documenting; positional args require reading the help text.
Use flags for anything optional or behavioral.

### 5.3 Enum Flags Over Boolean Flags

`--output-format=json|csv|table` is better than `--json` / `--csv` / `--table`
because:
- It's one flag instead of three that might conflict.
- Tab completion shows all options.
- It's extensible without new flags.

### 5.4 Short Flags for Common Operations

Provide `-v` for verbose, `-q` for quiet, `-o` for output, `-f` for force.
Follow existing conventions. Don't invent novel short flags for common concepts.

### 5.5 Required Args Should Be Obvious

If an argument is required, it should be obvious from the help text. Clap marks
required args in usage strings. Add clear doc comments explaining what the arg
is for.

### 5.6 Sensible Defaults

Every flag that *can* have a default *should* have a default. The user should
be able to run the most common invocation with minimal flags.

---

## 6. Interactivity

### 6.1 Interactive Mode as Guided Discovery

For complex operations, offer an interactive mode that prompts the user
step-by-step. This is how CLIs replicate GUI discoverability.

Interactive mode is an *addition* to the non-interactive interface, never a
replacement. Non-interactive commands are essential for automation.

### 6.2 Validate Input Inline

In interactive mode, validate each input as it's entered. Don't wait until the
end to report that the third field was invalid.

### 6.3 Confirm Destructive Operations

Before deleting, overwriting, or deploying to production: show what will happen
and ask for confirmation. Provide a `--yes` / `-y` flag to skip confirmation
in scripts.

### 6.4 Detect Non-Interactive Environments

If stdin is not a TTY, do not attempt interactive prompts. Either fall back to
defaults, or exit with a clear error: "This operation requires confirmation.
Pass --yes to skip, or run in an interactive terminal."

---

## 7. Progress Indication

### 7.1 Never Leave the User Staring at a Cursor

If an operation takes more than about one second, show *something*. Silence
makes users think the tool is broken.

### 7.2 Choose the Right Pattern

| Duration | Knowledge of Total | Pattern |
|---|---|---|
| < 1s | Any | No indicator |
| 1–10s | Unknown | Spinner with status text |
| 1–10s | Known | X of Y counter |
| > 10s | Known | Progress bar |
| > 10s, parallel | Known per task | Multi-progress bar |

### 7.3 Show What, Not Just That

A spinner that says "Working..." is barely better than silence. A spinner that
says "Downloading dependency libfoo v2.3.1..." tells the user exactly what's
happening and whether it's stuck.

### 7.4 Tick on Completion, Not on Time

If your spinner advances on a timer, it will keep spinning even if the process
is deadlocked. If it advances when a unit of work completes, a frozen spinner
is a genuine signal that something is wrong.

### 7.5 Log After Completion

After the progress display finishes, leave a clean log of what happened. The
user should be able to scroll up and see: what was done, any warnings, the
final result.

---

## 8. Color and Visual Hierarchy

### 8.1 Semantic Color

- **Red:** errors, failures.
- **Yellow/Amber:** warnings, things that need attention.
- **Green:** success, completion.
- **Cyan/Blue:** informational, highlights.
- **Dim/Gray:** secondary info, timestamps, paths.

### 8.2 Color is Enhancement, Not Information

Never use color as the *sole* carrier of meaning. Always pair with text labels:
`error:`, `warning:`, `✓`, `✗`.

### 8.3 Respect NO_COLOR

Check the `NO_COLOR` environment variable (https://no-color.org). If set,
disable all ANSI color output. Also disable color when the output stream is not
a TTY.

### 8.4 Don't Overuse

If everything is colored, nothing stands out. Use color sparingly to draw
attention to what matters: errors, warnings, success confirmations, key values.

---

## 9. Composability

### 9.1 stdout / stderr Discipline

- All primary output → stdout.
- All messages, logs, progress, errors → stderr.

This is the single most important rule for composability. It ensures piping
works: `mytool list | grep foo` won't be polluted by log messages.

### 9.2 Exit Codes

Scripts use exit codes to branch. Return 0 on success, non-zero on failure.
Map important failure modes to distinct codes.

### 9.3 Line-Based Output

One record per line is the universal contract for UNIX pipelines. If your output
naturally has one item per line, scripts can pipe through `wc -l`, `head`,
`sort`, `uniq`, etc.

### 9.4 Structured Output

For complex data, offer `--json`. JSON is the lingua franca of modern tooling
and integrates with `jq`, APIs, and web services.

### 9.5 Don't Eat stdin

If your command expects piped input and stdin is a TTY, show help or a message
instead of blocking. `cat` blocking on an empty stdin is a classic anti-pattern.

---

## 10. Context Awareness

### 10.1 Read the Working Directory

If your tool operates on projects, detect project files (Cargo.toml,
package.json, etc.) in the current directory and adapt.

### 10.2 Per-Project Configuration

Support config files in the project directory that override global config.
This lets different projects use different settings without flag gymnastics.

### 10.3 Respect XDG Conventions

On Linux, use `$XDG_CONFIG_HOME` (default `~/.config`) for config,
`$XDG_DATA_HOME` (default `~/.local/share`) for data,
`$XDG_CACHE_HOME` (default `~/.cache`) for caches.

The `dirs` or `directories` crate handles this cross-platform.

---

## 11. Naming

### 11.1 Verb-Noun for Subcommands

`mytool create project`, `mytool delete user`. The subcommand reads like an
imperative sentence.

### 11.2 Singular Nouns

`mytool user list`, not `mytool users list`. Consistency with UNIX conventions.

### 11.3 Minimize the Verb Set

Reuse verbs across resources: `create`, `delete`, `list`, `show`, `update`.
Don't introduce a new verb when an existing one fits.

### 11.4 Predictable Flag Names

- `--output` / `-o` for output path.
- `--verbose` / `-v` for verbosity.
- `--quiet` / `-q` for silence.
- `--force` / `-f` for skipping confirmations.
- `--dry-run` for simulating without effect.
- `--config` / `-c` for config file path.

---

## 12. Type-Level Safety

### 12.1 Make Invalid States Unrepresentable

Use Rust's type system to ensure that impossible argument combinations cannot be
constructed. This principle comes from typed functional programming and applies
directly to CLI argument design.

**Patterns:**
- Use `ValueEnum` instead of `String` for fixed option sets.
- Use newtypes (`struct Port(u16)`) with validation in `FromStr`.
- Use subcommand enums so incompatible flag sets live on separate variants.
- Use `#[arg(conflicts_with)]` and `#[arg(requires)]` for mutual exclusions.
- Use `ArgGroup` for "exactly one of these" constraints.

### 12.2 Parse, Don't Validate

All user input should be parsed into typed, validated structures at the boundary
(argument parsing). Internal code should never receive raw strings for things
that have structure (ports, paths, URLs, enums).

---

## 13. Configuration

### 13.1 Layered Precedence

CLI args > environment variables > project config file > user config file > defaults.

This is the standard expectation. Violating it surprises users.

### 13.2 Show Active Configuration

Consider a `mytool config show` or `--show-config` that displays the resolved
configuration, showing which source each value came from. This is invaluable
for debugging "why is it using port 9090?".

### 13.3 Config File Discovery

Look for config files in predictable locations:
1. Explicit `--config` path.
2. `.mytool.toml` in the working directory (project-local).
3. `$XDG_CONFIG_HOME/mytool/config.toml` (user-global).

---

## 14. Shell Completions

### 14.1 Always Provide Them

Shell completions are one of the highest-value UX features relative to
implementation cost. They make the tool feel native and dramatically improve
discoverability.

### 14.2 Two Approaches

**Build-time** (in `build.rs`): Generate completion scripts during compilation.
Package them with your release artifacts.

**Runtime** (subcommand): Expose `mytool completions bash|zsh|fish|powershell`
that writes the script to stdout. User redirects to the appropriate shell
config location.

Both approaches use the `clap_complete` crate.

---

## 15. Testing

### 15.1 Argument Parsing Tests

Use `Cli::try_parse_from(["mytool", "--flag", "value"])` to test parsing
without process exit. Assert on both success cases and error cases.

### 15.2 Integration Tests

Use `assert_cmd` to invoke the compiled binary and check stdout, stderr, and
exit codes end-to-end.

### 15.3 Snapshot Tests

Use `trycmd` or `snapbox` to capture and verify CLI output across invocations.
Particularly useful for help text stability.

### 15.4 Test the Error Paths

The error messages are part of the UX. Test that invalid input produces the
expected human-readable error, not a panic or raw debug output.
