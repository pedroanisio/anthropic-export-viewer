# Clap Recipes

Concrete Rust/clap v4 implementation patterns for each CLI UX concern.
Cross-references pattern rationale in `clig-patterns.md`.

---

## Table of Contents

1. [Project Setup](#1-project-setup)
2. [Derive-Based Architecture](#2-derive-based-architecture)
3. [Subcommands](#3-subcommands)
4. [Value Parsing and Validation](#4-value-parsing-and-validation)
5. [Environment Variables](#5-environment-variables)
6. [Configuration Layering](#6-configuration-layering)
7. [Error Handling](#7-error-handling)
8. [Help Text Design](#8-help-text-design)
9. [Output Discipline](#9-output-discipline)
10. [Progress Indication](#10-progress-indication)
11. [Color](#11-color)
12. [Interactive Prompts](#12-interactive-prompts)
13. [Shell Completions](#13-shell-completions)
14. [Testing](#14-testing)
15. [Ecosystem Crate Map](#15-ecosystem-crate-map)

---

## 1. Project Setup

Minimal Cargo.toml for a production CLI:

```toml
[package]
name = "mytool"
version = "0.1.0"
edition = "2021"

[dependencies]
clap = { version = "4.5", features = ["derive", "env"] }
anyhow = "1"
thiserror = "2"
colored = "2"
indicatif = "0.17"
is-terminal = "0.4"

[dev-dependencies]
assert_cmd = "2"
predicates = "3"
```

Add `clap_complete` if generating shell completions. Add `dialoguer` if using
interactive prompts. Add `serde` + `toml` if layering config files.

---

## 2. Derive-Based Architecture

Use derive for ~90% of CLIs. Reserve the builder API for dynamic CLI
construction (plugin systems, runtime-configured commands).

### Flat single-command tool

```rust
use clap::Parser;
use std::path::PathBuf;

/// MyTool — a brief description of what it does
#[derive(Parser, Debug)]
#[command(version, about, long_about = None)]
struct Cli {
    /// Input file to process
    #[arg(short, long)]
    input: PathBuf,

    /// Enable verbose output
    #[arg(short, long)]
    verbose: bool,

    /// Output format
    #[arg(long, default_value = "text", value_parser = ["text", "json", "csv"])]
    format: String,
}
```

### Multi-command tool

```rust
use clap::{Parser, Subcommand, ValueEnum};
use std::path::PathBuf;

#[derive(Parser, Debug)]
#[command(name = "mytool", version, about, propagate_version = true)]
struct Cli {
    /// Enable verbose output
    #[arg(short, long, global = true)]
    verbose: bool,

    /// Configuration file path
    #[arg(short, long, global = true, env = "MYTOOL_CONFIG")]
    config: Option<PathBuf>,

    /// Output format
    #[arg(long, default_value = "text", global = true)]
    format: OutputFormat,

    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand, Debug)]
enum Commands {
    /// Initialize a new project
    Init {
        /// Project name
        name: String,
        /// Target directory
        #[arg(short, long)]
        path: Option<PathBuf>,
    },
    /// Build the project
    Build {
        /// Build in release mode
        #[arg(long)]
        release: bool,
    },
    /// Generate shell completions
    Completions {
        /// Shell to generate for
        #[arg(value_enum)]
        shell: clap_complete::Shell,
    },
}

#[derive(ValueEnum, Clone, Debug)]
enum OutputFormat {
    Text,
    Json,
    Csv,
}
```

---

## 3. Subcommands

### Optional subcommands

Wrap in `Option<Commands>` so the tool can run without a subcommand:

```rust
#[command(subcommand)]
command: Option<Commands>,
```

In `main`, match on `None` to show a welcome message or default behavior.

### Global flags

Use `#[arg(global = true)]` on the parent struct. These propagate to all
subcommands automatically:

```rust
#[arg(short, long, global = true)]
verbose: bool,
```

### Nested subcommands

Use `#[command(flatten)]` on enum variants that themselves implement
`Subcommand`:

```rust
#[derive(Subcommand)]
enum Commands {
    /// Resource management
    #[command(flatten)]
    Resource(ResourceCommands),
}

#[derive(Subcommand)]
enum ResourceCommands {
    Create { name: String },
    Delete { name: String },
    List,
}
```

### Arg groups and conflicts

For mutually exclusive options:

```rust
#[arg(long, conflicts_with = "stdin")]
file: Option<PathBuf>,

#[arg(long, conflicts_with = "file")]
stdin: bool,
```

For "exactly one of N" constraints, use `ArgGroup`:

```rust
#[derive(Parser)]
#[command(group = clap::ArgGroup::new("input").required(true))]
struct Cli {
    #[arg(long, group = "input")]
    file: Option<PathBuf>,

    #[arg(long, group = "input")]
    url: Option<String>,
}
```

---

## 4. Value Parsing and Validation

### Typed fields (clap infers parser)

```rust
#[arg(long)]
port: u16,               // parses integer, rejects non-numeric

#[arg(long)]
output: PathBuf,          // accepts filesystem paths

#[arg(long)]
bind: std::net::IpAddr,   // parses IP addresses
```

### ValueEnum for closed sets

```rust
#[derive(ValueEnum, Clone, Debug)]
enum LogLevel {
    Error,
    Warn,
    Info,
    Debug,
    Trace,
}

#[arg(long, value_enum, default_value_t = LogLevel::Info)]
log_level: LogLevel,
```

### Ranged numeric validation

```rust
#[arg(long, value_parser = clap::value_parser!(u16).range(1..=65535))]
port: u16,
```

### Custom validation function

```rust
fn parse_duration(s: &str) -> Result<std::time::Duration, String> {
    let secs: u64 = s.strip_suffix('s')
        .ok_or_else(|| format!("duration must end with 's', got '{s}'"))?
        .parse()
        .map_err(|_| format!("'{s}' is not a valid duration"))?;
    Ok(std::time::Duration::from_secs(secs))
}

#[arg(long, value_parser = parse_duration, default_value = "30s")]
timeout: std::time::Duration,
```

### Newtype pattern for domain types

```rust
use std::str::FromStr;

#[derive(Clone, Debug)]
struct ProjectName(String);

impl FromStr for ProjectName {
    type Err = String;
    fn from_str(s: &str) -> Result<Self, String> {
        if s.is_empty() {
            return Err("project name cannot be empty".into());
        }
        if !s.chars().all(|c| c.is_alphanumeric() || c == '-' || c == '_') {
            return Err("project name may only contain alphanumerics, hyphens, and underscores".into());
        }
        Ok(ProjectName(s.to_owned()))
    }
}

// Usage:
#[arg(long)]
name: ProjectName,
```

---

## 5. Environment Variables

Enable the `env` feature in Cargo.toml, then annotate:

```rust
#[arg(long, env = "MYTOOL_PORT", default_value_t = 8080)]
port: u16,

#[arg(long, env = "MYTOOL_TOKEN")]
token: Option<String>,

// Comma-separated list from env
#[arg(long, env = "MYTOOL_HOSTS", value_delimiter = ',')]
hosts: Vec<String>,
```

Help text automatically shows: `[env: MYTOOL_PORT=]`

### Precedence

Clap enforces: CLI arg > env var > default. This is the expected behavior.

---

## 6. Configuration Layering

For CLI > env > config file > defaults, integrate with figment or a manual
merge:

### Manual merge pattern

```rust
use serde::Deserialize;

#[derive(Deserialize, Default)]
struct FileConfig {
    port: Option<u16>,
    host: Option<String>,
    verbose: Option<bool>,
}

fn resolve_config(cli: &Cli) -> ResolvedConfig {
    let file_cfg = load_config_file(cli.config.as_deref());
    ResolvedConfig {
        port: cli.port.or(file_cfg.port).unwrap_or(8080),
        host: cli.host.clone().or(file_cfg.host).unwrap_or_else(|| "127.0.0.1".into()),
        verbose: cli.verbose || file_cfg.verbose.unwrap_or(false),
    }
}
```

Key: CLI struct fields that participate in config layering should be
`Option<T>` so that "not specified on CLI" is distinguishable from "specified
as the default". Then merge manually with config file values.

---

## 7. Error Handling

### Domain errors (thiserror)

```rust
use thiserror::Error;
use std::path::PathBuf;

#[derive(Error, Debug)]
pub enum CliError {
    #[error("Project '{0}' already exists. Choose a different name or delete the existing project.")]
    ProjectExists(String),

    #[error("Config file not found at {0}. Run 'mytool init' to create one.")]
    ConfigNotFound(PathBuf),

    #[error("Invalid port {port}: must be between 1 and 65535.")]
    InvalidPort { port: u16 },

    #[error("Build failed: {reason}")]
    BuildFailed { reason: String },
}
```

### Handler functions (anyhow)

```rust
use anyhow::{Context, Result, bail};

fn cmd_init(name: &str, path: Option<PathBuf>) -> Result<()> {
    let target = path.unwrap_or_else(|| PathBuf::from(".")).join(name);
    if target.exists() {
        bail!(CliError::ProjectExists(name.to_owned()));
    }
    std::fs::create_dir_all(&target)
        .with_context(|| format!("Failed to create directory {}", target.display()))?;
    Ok(())
}
```

### Main with exit codes

```rust
use std::process::ExitCode;
use colored::Colorize;

mod exit_code {
    pub const SUCCESS: u8 = 0;
    pub const GENERAL: u8 = 1;
    pub const USAGE: u8 = 2;
    pub const CONFIG: u8 = 3;
    pub const IO: u8 = 4;
}

fn main() -> ExitCode {
    let cli = Cli::parse();
    match run(cli) {
        Ok(()) => ExitCode::from(exit_code::SUCCESS),
        Err(e) => {
            eprintln!("{}: {}", "error".red().bold(), e);
            if std::env::var("RUST_BACKTRACE").is_ok() {
                for cause in e.chain().skip(1) {
                    eprintln!("  {}: {}", "caused by".yellow(), cause);
                }
            }
            ExitCode::from(determine_exit_code(&e))
        }
    }
}

fn determine_exit_code(err: &anyhow::Error) -> u8 {
    if err.downcast_ref::<std::io::Error>().is_some() {
        return exit_code::IO;
    }
    if err.downcast_ref::<CliError>().is_some() {
        return exit_code::GENERAL;
    }
    exit_code::GENERAL
}
```

---

## 8. Help Text Design

### Doc comments become help text

```rust
/// MyTool — processes files with style
///
/// EXAMPLES:
///     mytool process input.csv --format json
///     mytool process input.csv --output result.json --verbose
///     cat data.csv | mytool process - --format table
#[derive(Parser)]
#[command(version, about, after_help = "See https://example.com/docs for full documentation.")]
struct Cli { /* ... */ }
```

### Concise default behavior

Use `#[command(arg_required_else_help = true)]` to show help when no args are
provided instead of erroring.

### Subcommand-required pattern

```rust
#[derive(Parser)]
#[command(
    arg_required_else_help = true,
    subcommand_required = true,
)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}
```

---

## 9. Output Discipline

### TTY detection

```rust
use is_terminal::IsTerminal;

fn is_tty() -> bool {
    std::io::stdout().is_terminal()
}

fn should_use_color() -> bool {
    is_tty() && std::env::var("NO_COLOR").is_err()
}
```

### Conditional formatting

```rust
fn print_result(item: &Item, format: &OutputFormat) {
    match format {
        OutputFormat::Json => {
            println!("{}", serde_json::to_string(item).unwrap());
        }
        OutputFormat::Text if is_tty() => {
            println!("{}: {}", item.name.bold(), item.value.green());
        }
        OutputFormat::Text => {
            println!("{}\t{}", item.name, item.value);
        }
    }
}
```

---

## 10. Progress Indication

### Spinner (unknown duration)

```rust
use indicatif::{ProgressBar, ProgressStyle};
use std::time::Duration;

let spinner = ProgressBar::new_spinner();
spinner.set_style(
    ProgressStyle::with_template("{spinner:.cyan} {msg}")
        .unwrap()
        .tick_strings(&["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]),
);
spinner.set_message("Downloading dependencies...");
spinner.enable_steady_tick(Duration::from_millis(80));

// ... do work ...

spinner.finish_with_message("Done.");
```

### Progress bar (known total)

```rust
use indicatif::{ProgressBar, ProgressStyle};

let bar = ProgressBar::new(total_items as u64);
bar.set_style(
    ProgressStyle::with_template(
        "{spinner:.green} [{bar:40.cyan/blue}] {pos}/{len} ({eta}) {msg}"
    )
    .unwrap()
    .progress_chars("█▓░"),
);

for item in items {
    bar.set_message(format!("Processing {}", item.name));
    process(&item)?;
    bar.inc(1);
}
bar.finish_with_message("All items processed.");
```

### Multi-progress (parallel tasks)

```rust
use indicatif::{MultiProgress, ProgressBar, ProgressStyle};

let multi = MultiProgress::new();
let style = ProgressStyle::with_template(
    "{prefix:.bold} [{bar:30}] {pos}/{len} {msg}"
).unwrap();

let handles: Vec<_> = tasks.into_iter().map(|task| {
    let bar = multi.add(ProgressBar::new(task.total as u64));
    bar.set_style(style.clone());
    bar.set_prefix(task.name.clone());
    std::thread::spawn(move || {
        for step in task.steps {
            bar.set_message(step.label.clone());
            step.execute();
            bar.inc(1);
        }
        bar.finish_with_message("done");
    })
}).collect();

for h in handles { h.join().unwrap(); }
```

### Gate progress behind TTY

Only show interactive progress when stderr is a TTY. When piped, fall back to
log lines:

```rust
fn create_progress(total: u64) -> ProgressBar {
    if std::io::stderr().is_terminal() {
        let bar = ProgressBar::new(total);
        // ... configure style ...
        bar
    } else {
        ProgressBar::hidden()
    }
}
```

---

## 11. Color

### Conditional color with colored crate

```rust
use colored::Colorize;

fn setup_color() {
    if std::env::var("NO_COLOR").is_ok() || !std::io::stdout().is_terminal() {
        colored::control::set_override(false);
    }
}
```

### Semantic helpers

```rust
fn print_error(msg: &str) {
    eprintln!("{}: {}", "error".red().bold(), msg);
}

fn print_warning(msg: &str) {
    eprintln!("{}: {}", "warning".yellow().bold(), msg);
}

fn print_success(msg: &str) {
    eprintln!("{}: {}", "✓".green().bold(), msg);
}

fn print_info(msg: &str) {
    eprintln!("{}: {}", "info".cyan(), msg);
}
```

---

## 12. Interactive Prompts

### Confirmation before destructive action

```rust
use dialoguer::Confirm;

fn confirm_delete(name: &str, force: bool) -> anyhow::Result<bool> {
    if force {
        return Ok(true);
    }
    if !std::io::stdin().is_terminal() {
        anyhow::bail!(
            "Deleting '{name}' requires confirmation. \
             Pass --force to skip, or run in an interactive terminal."
        );
    }
    Ok(Confirm::new()
        .with_prompt(format!("Delete project '{name}'? This cannot be undone"))
        .default(false)
        .interact()?)
}
```

### Selection menu

```rust
use dialoguer::Select;

let options = &["Development", "Staging", "Production"];
let selection = Select::new()
    .with_prompt("Choose deployment target")
    .items(options)
    .default(0)
    .interact()?;
```

---

## 13. Shell Completions

### Runtime subcommand approach

```rust
// In your Commands enum:
/// Generate shell completions
Completions {
    #[arg(value_enum)]
    shell: clap_complete::Shell,
},

// In your dispatch:
Commands::Completions { shell } => {
    let mut cmd = Cli::command();
    clap_complete::generate(
        shell,
        &mut cmd,
        "mytool",
        &mut std::io::stdout(),
    );
}
```

### Build-time approach (build.rs)

```rust
// build.rs
use clap::CommandFactory;
use clap_complete::{generate_to, Shell};

include!("src/cli.rs");

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let outdir = std::env::var_os("OUT_DIR").ok_or("OUT_DIR not set")?;
    let mut cmd = Cli::command();
    for shell in [Shell::Bash, Shell::Zsh, Shell::Fish, Shell::PowerShell] {
        generate_to(shell, &mut cmd, "mytool", &outdir)?;
    }
    println!("cargo:rerun-if-changed=src/cli.rs");
    Ok(())
}
```

---

## 14. Testing

### Argument parsing unit tests

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use clap::Parser;

    #[test]
    fn parse_minimal() {
        let cli = Cli::try_parse_from(["mytool", "init", "myproject"]).unwrap();
        assert!(matches!(cli.command, Commands::Init { name, .. } if name == "myproject"));
    }

    #[test]
    fn parse_rejects_invalid_port() {
        let result = Cli::try_parse_from(["mytool", "--port", "99999"]);
        assert!(result.is_err());
    }

    #[test]
    fn parse_verbose_is_global() {
        let cli = Cli::try_parse_from(["mytool", "-v", "build"]).unwrap();
        assert!(cli.verbose);
    }

    #[test]
    fn parse_env_fallback() {
        std::env::set_var("MYTOOL_PORT", "9090");
        let cli = Cli::try_parse_from(["mytool", "build"]).unwrap();
        assert_eq!(cli.port, 9090);
        std::env::remove_var("MYTOOL_PORT");
    }
}
```

### Integration tests with assert_cmd

```rust
// tests/integration.rs
use assert_cmd::Command;
use predicates::str::contains;

#[test]
fn help_shows_examples() {
    Command::cargo_bin("mytool")
        .unwrap()
        .arg("--help")
        .assert()
        .success()
        .stdout(contains("EXAMPLES"));
}

#[test]
fn invalid_subcommand_suggests_correction() {
    Command::cargo_bin("mytool")
        .unwrap()
        .arg("biuld")  // typo
        .assert()
        .failure()
        .stderr(contains("build"));  // should suggest "build"
}

#[test]
fn no_args_shows_help() {
    Command::cargo_bin("mytool")
        .unwrap()
        .assert()
        .failure()
        .stderr(contains("Usage"));
}

#[test]
fn json_output_is_valid() {
    let output = Command::cargo_bin("mytool")
        .unwrap()
        .args(["list", "--format", "json"])
        .assert()
        .success()
        .get_output()
        .stdout
        .clone();
    let _: serde_json::Value = serde_json::from_slice(&output).unwrap();
}
```

---

## 15. Ecosystem Crate Map

| Concern | Crate | Purpose |
|---|---|---|
| Arg parsing | `clap` (derive + env features) | CLI definition and parsing |
| Shell completions | `clap_complete` | Generate bash/zsh/fish/powershell scripts |
| Domain errors | `thiserror` | Derive `Error` on custom error enums |
| Error chaining | `anyhow` | `Result<T>` with context and cause chains |
| Color output | `colored` or `owo-colors` | Semantic terminal colors |
| Progress bars | `indicatif` | Spinners, bars, multi-progress |
| Interactive prompts | `dialoguer` | Confirm, Select, Input, MultiSelect |
| TTY detection | `is-terminal` | Check if stdout/stderr/stdin is a TTY |
| Tables | `comfy-table` or `tabled` | Pretty terminal tables |
| Terminal control | `crossterm` | Low-level terminal manipulation |
| Config files | `figment` or `config` | Layered configuration merging |
| Serialization | `serde` + `toml`/`serde_json` | Config and structured output |
| Reusable flags | `clap-verbosity-flag` | Standard `--verbose`/`--quiet` via flatten |
| XDG dirs | `dirs` or `directories` | Cross-platform config/data/cache paths |
| Integration tests | `assert_cmd` + `predicates` | Binary invocation testing |
| Snapshot tests | `trycmd` or `snapbox` | Help text and output stability |
| Rich error display | `miette` | Fancy diagnostic error rendering (alternative to manual colored errors) |
