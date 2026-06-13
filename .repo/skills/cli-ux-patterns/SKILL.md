---
name: cli-ux-patterns
description: >
  Design and implement high-quality CLI user experiences in Rust using clap.
  Trigger this skill whenever the user is building a command-line tool, designing
  CLI arguments/subcommands, implementing error handling for a CLI, adding progress
  indicators, color output, shell completions, interactive prompts, help text,
  or any aspect of how a terminal program communicates with its human operator.
  Also trigger when the user asks to "review my CLI", "improve the UX of my CLI",
  "make my CLI more user-friendly", "add --help", "design subcommands", "add
  shell completions", "add color output", "handle errors nicely", or any phrasing
  about making a command-line program pleasant, discoverable, or robust for
  humans. If the user is writing a Rust CLI and the conversation touches argument
  structure, output formatting, error messages, or user interaction — use this
  skill. Even if the user just says "build me a CLI for X", this skill applies
  because every CLI needs good UX from the start.
---

# CLI UX Patterns

Build command-line tools that are **human-first, composable, and robust** by
applying established interaction design patterns from the CLI domain and
implementing them idiomatically in Rust with clap v4.

## Before you begin

1. **Read the pattern catalog** — `references/clig-patterns.md` contains the
   full set of CLI UX patterns organized by concern: philosophy, help text,
   output, errors, arguments, interactivity, progress, color, composability,
   naming, and type-safety. Read it before designing any CLI surface.

2. **Read the clap recipes** — `references/clap-recipes.md` contains concrete
   Rust/clap implementation patterns for each UX concern: derive-based
   architecture, subcommands, value parsing, environment variables, error
   handling with thiserror/anyhow, shell completions, testing, and the
   ecosystem crate map. Read it before writing clap code.

---

## Core Workflow

### Phase 1 — Understand the CLI's Purpose

Before writing any argument definitions, establish:

| Question | Why it matters |
|---|---|
| Who is the primary audience — humans, scripts, or both? | Drives output format defaults (human-readable vs JSON). |
| What is the single most common invocation? | Becomes the lead example in `--help` and onboarding. |
| How many distinct operations does the tool perform? | Determines whether you need subcommands or a flat arg set. |
| What is the expected execution duration? | Dictates progress indication pattern (none / spinner / X-of-Y / bar). |
| What environment does it run in? | Determines config layering (CLI > env > file > defaults). |
| Is it destructive or irreversible? | Drives confirmation prompts, dry-run flags, and colored warnings. |
| Will it be composed in pipelines? | Mandates stdout/stderr discipline and `--plain`/`--json` flags. |

Bias toward producing a concrete draft the user can react to. State assumptions
explicitly rather than blocking on questions.

### Phase 2 — Design the Argument Surface

Apply the following in order. This is not a post-hoc checklist — each decision
shapes the next.

**Pass 1 — Command topology**
- If ≤5 flags and one action: flat struct, no subcommands.
- If 2+ distinct operations: subcommand enum. Each variant owns its args.
- If operations share flags (verbose, config, output-format): declare those
  as `#[arg(global = true)]` on the top-level struct.
- If the tool has natural modes (serve, build, deploy): each mode is a subcommand.
- Use `#[command(propagate_version = true)]` so `--version` works everywhere.

**Pass 2 — Argument types and validation**
- Use the narrowest possible Rust type for each argument: `PathBuf` for paths,
  `u16` for ports, `IpAddr` for addresses. Clap infers the parser.
- For finite option sets: derive `ValueEnum` on an enum. Never accept a raw
  `String` when the domain is closed.
- For constrained ranges: use `value_parser!(u16).range(1..=65535)`.
- For custom validation: write a `fn(&str) -> Result<T, String>` and point
  `#[arg(value_parser = ...)]` at it.
- Prefer enum-style flags over boolean pairs. `--color=always|auto|never` is
  better than `--color` / `--no-color`.

**Pass 3 — Environment and config layering**
- Enable the `env` feature in clap.
- Annotate args with `#[arg(env = "MY_TOOL_PORT")]` where env configuration
  makes sense (ports, hosts, tokens, log levels).
- Precedence is: CLI arg > env var > config file > default.
- For config files, consider integrating figment: defaults → TOML → CLI.

**Pass 4 — Help text**
- Every struct and every field gets a doc comment (`///`). These become help text.
- Use `#[command(about, long_about)]` for the program description.
- Put the most common flags first in the struct — clap preserves field order
  in help output.
- Lead with examples in `long_about` or `after_help`.
- Show concise help by default (no args → show usage + one example + hint to
  use `--help`). Show full help on `-h` / `--help`.

### Phase 3 — Implement Human-Facing Behaviors

Refer to `references/clig-patterns.md` for the full rationale behind each
pattern. Here is the implementation checklist:

**Errors**
- Define domain errors with `thiserror`. Each variant gets a user-facing
  `#[error("...")]` message that explains what went wrong and what to try.
- Use `anyhow` in handler functions for chaining and context.
- In `main`, catch errors, print them to stderr with color, print the cause
  chain in verbose mode, and exit with a meaningful code.
- Never print raw stack traces to humans. Reserve those for `RUST_BACKTRACE=1`.

**Output discipline**
- Primary output → stdout. Messages, warnings, errors → stderr.
- Detect whether stdout is a TTY (`atty` or `is-terminal` crate). If not,
  suppress color, spinners, and interactive prompts automatically.
- Offer `--json` for machine-readable structured output.
- Offer `--plain` or `--no-color` as escape hatches.
- Respect the `NO_COLOR` environment variable (see https://no-color.org).

**Progress indication** (choose by duration and information available)
- < 1 second: no indicator needed.
- 1–10 seconds, unknown total: spinner (`indicatif::ProgressBar::new_spinner`).
- Known total: X of Y pattern or progress bar (`indicatif::ProgressBar`).
- Multiple parallel tasks: multi-progress bar (`indicatif::MultiProgress`).
- Always show *what* is happening, not just *that* something is happening.

**Color**
- Use color semantically: red for errors, yellow for warnings, green for
  success, dim/gray for secondary info. Use `colored` or `owo-colors`.
- Never use color as the *only* signal — always pair with text (e.g.,
  "error:" prefix + red).
- Gate all color behind TTY detection + NO_COLOR check.

**Interactive prompts**
- Use `dialoguer` for confirmations, selections, and text input.
- Only prompt when stdin is a TTY. If not interactive, either use defaults or
  fail with a clear error explaining which flag to pass.
- Interactive mode complements non-interactive mode; it never replaces it.

**Typo suggestions**
- Clap provides this automatically for subcommands and value enums. Ensure
  `suggest_edit_distance` is not disabled.

**Shell completions**
- Add `clap_complete` as a dependency.
- Either generate at build time in `build.rs` or expose a `completions`
  subcommand that generates scripts for bash/zsh/fish/powershell on demand.

### Phase 4 — Review Against the Pattern Catalog

Before delivering, score the CLI against these questions (details in
`references/clig-patterns.md`):

1. Does `--help` lead with examples?
2. Does an empty invocation show concise, actionable guidance?
3. Are errors human-readable with recovery suggestions?
4. Is stdout/stderr discipline correct?
5. Does it respect `NO_COLOR` and detect TTY?
6. Are progress indicators present for anything > 1 second?
7. Are invalid argument states unrepresentable at the type level?
8. Are exit codes meaningful and documented?
9. Can a script consume the output (`--json` / `--plain`)?
10. Are shell completions available?

If any answer is "no" and the tool targets humans, address it before shipping.

---

## Architecture Patterns by Scale

**Single-command tool** (e.g., a formatter, a linter):
```
src/
├── main.rs      // parse args, call run(), handle errors, exit
├── cli.rs       // #[derive(Parser)] struct + types
└── lib.rs       // business logic, no CLI awareness
```

**Multi-command tool** (e.g., a project manager, a deploy tool):
```
src/
├── main.rs      // parse args, dispatch subcommands
├── cli.rs       // Cli struct + Commands enum
├── commands/    // one module per subcommand
│   ├── init.rs
│   ├── build.rs
│   └── deploy.rs
├── error.rs     // CliError enum (thiserror)
└── config.rs    // config layering
```

Separate CLI surface from logic. The `commands/` modules call into a library
crate or core modules that know nothing about clap. This makes both testing
and library reuse straightforward.

---

## The Golden Rules (always apply)

1. **Human-first, composable-second.** Design for the person at the keyboard,
   then ensure scripts can consume your output too.
2. **Make invalid states unrepresentable.** If a flag combination is illegal,
   model it so it cannot be constructed. Use enums, arg groups, and
   `conflicts_with` / `requires`.
3. **Show, don't just tell.** Lead help text with examples. Show what the tool
   *does*, not just what flags it *has*.
4. **Errors are conversation.** Every error message should answer: what happened,
   why, and what to try next.
5. **Silence is hostile.** If something takes time, show progress. If something
   succeeds, confirm it briefly.
6. **Respect the terminal.** Detect TTY, respect NO_COLOR, don't break pipes.
