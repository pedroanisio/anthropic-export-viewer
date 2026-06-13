---
name: incremental-validation
version: "1.0.0"
description: Enforce continuous validation throughout implementation — validate after every TDD phase, code change, and plan generation step instead of batching all checks at the end. Use when implementing features, fixing bugs, generating plans, or reviewing code to ensure issues are caught immediately while context is fresh.
allowed-tools: Bash Read Glob Grep
metadata:
  ulid: 01KM1BKXK7ST4DT8P6YC1BTMRD
---

# Incremental Validation

Validate work continuously throughout implementation, not just at the end. Catch issues immediately while context is fresh.

**Announce at start:** "I'm using the incremental-validation skill to validate continuously throughout this task."

## When to Use This Skill

- Implementing features or fixing bugs (validate after each TDD phase)
- Generating formal plans (validate skeleton before filling details)
- Reviewing code for quality and correctness
- Any multi-step implementation where late-discovered issues are expensive
- Refactoring code (verify no regressions after each change)

## Core Principle: Don't Batch Validation

**Anti-pattern:**
```
1. Write all code
2. Write all tests
3. Run formatter
4. Run linter
5. Run tests
6. Fix everything at once
```

**Problem:** Fixing issues is expensive and time-consuming when found late.

**Correct approach:** Validate after every meaningful change.

## TDD Phase Validation

### Red Phase → Validate

```bash
# Write failing test
# Verify test fails for the right reason
pytest test_module.py::test_new_feature
# ✓ Confirm it fails as expected
```

### Green Phase → Validate

```bash
# Implement minimal code
# Verify test passes
pytest test_module.py::test_new_feature
# ✓ Confirm it passes now

# Quick lint check
ruff check module.py
# ✓ Confirm no new warnings
```

### Refactor Phase → Validate

```bash
# Optimize code
# Verify tests still pass
pytest test_module.py
# ✓ Confirm refactoring didn't break anything

# Check coverage
pytest --cov=module
# ✓ Confirm coverage maintained/improved
```

### Cleanup Phase → Validate

```bash
# Remove dead code
git diff

# Verify all tests still pass
pytest
# ✓ Confirm cleanup didn't break anything
```

## Validation Frequency

### Every Code Change

- [ ] Does it compile/parse?
- [ ] Do related tests still pass?
- [ ] Any obvious linter warnings?

### Every Few Minutes

- Run specific test you're working on
- Quick linter check on modified files
- Verify behavior matches expectation

### Before Committing

- [ ] All tests pass
- [ ] Formatter applied
- [ ] Linter clean (zero warnings)
- [ ] Coverage targets met
- [ ] No TODOs or placeholders

### During Code Review

- [ ] ADR compliance
- [ ] Test coverage adequate
- [ ] Error handling proper
- [ ] Documentation updated
- [ ] No anti-patterns

## Validation Tools by Phase

### Phase 1: Syntax/Compilation (after every few lines)

```bash
# Python
python -m py_compile module.py

# TypeScript
tsc --noEmit

# Rust
cargo check

# Go
go build
```

**Why:** Catch syntax errors immediately, not after 100 lines.

### Phase 2: Unit Tests (after implementing each function)

```bash
# Run specific test
pytest test_module.py::test_specific -v

# Run test file
pytest test_module.py

# Run related tests
pytest -k "module_name"
```

**Why:** Confirm logic works before moving to next function.

### Phase 3: Linting (every 5-10 minutes)

```bash
# Lint single file
eslint src/module.js

# Lint with autofix
ruff check --fix module.py

# Type checking
mypy module.py
```

**Why:** Fix style issues while context is fresh.

### Phase 4: Formatting (before commit)

```bash
# Format code
black module.py
prettier --write module.js
rustfmt module.rs
```

### Phase 5: Integration Tests (after component complete)

```bash
pytest tests/integration/ --cov
```

### Phase 6: Full Test Suite (before pushing)

```bash
pytest --cov --cov-fail-under=80
```

## Plan Validation (For M/L/XL Tasks)

Incremental validation applies to plan generation, not just code.

### After Skeleton Generation → Validate

- Referential integrity: all step IDs in execution order, all dependsOn targets exist
- DAG acyclicity: no circular dependencies
- Actor-zone authorization: assigned actors have access to declared scope zones

### After Filling Step Details → Validate Per Step

- Size ↔ file count consistency against T-shirt table
- Conditional fields populated (stopConditions, resourceRequirements for M+ steps)
- Detection adequacy: L/XL steps have human verification checks

### Before Emitting Plan → Validate

- Full self-check (structural + semantic)
- Verification economics: `bwDecl + bwReview ≤ bwVerify`
- Domain confidence: no unverified entity names

## ADR Compliance Checks

During implementation, validate against ADRs frequently:

- [ ] Following established error handling patterns?
- [ ] Using approved libraries and tools?
- [ ] Following the testing strategy?
- [ ] Aligning with architectural decisions?

**When:** Before committing each logical unit of work.

## Incremental Coverage Tracking

Track coverage as you go — don't discover gaps at the end:

```bash
# Baseline
pytest --cov --cov-report=term-missing
# Current: 78% (need 80%)

# After adding feature + tests
pytest --cov --cov-report=term-missing
# Current: 81% (✓ Target met!)
```

### Per-File Coverage

```bash
# Check specific file
pytest --cov=src/module --cov-report=term-missing

# Identify uncovered lines, add tests, re-check
```

## Watch Mode (Continuous Feedback)

Automatically re-run on file changes:

```bash
# Python
pytest-watch

# JavaScript
jest --watch

# Rust
cargo watch -x test

# Go
got watch
```

## Checklist

When applying this skill, verify after each significant change:

- [ ] Syntax/compilation clean
- [ ] Specific test passes
- [ ] No new linter warnings
- [ ] No new type errors
- [ ] Coverage maintained/improved
- [ ] Follows ADR patterns
- [ ] No placeholders added
- [ ] Error handling proper
