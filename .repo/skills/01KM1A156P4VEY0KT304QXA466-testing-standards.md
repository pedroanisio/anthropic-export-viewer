---
name: testing-standards
version: "1.0.0"
description: Enforce comprehensive testing standards including coverage targets, test organization (unit/integration/E2E), TDD workflow, property-based testing, and test quality requirements (deterministic, isolated, realistic). Use when writing tests, reviewing test quality, setting up test infrastructure, or enforcing coverage thresholds in CI.
allowed-tools: Bash Read Glob Grep
metadata:
  ulid: 01KM1A156P4VEY0KT304QXA466
---

# Testing Standards

Comprehensive testing requirements for all code. Enforce coverage, organization, naming, and quality standards.

**Announce at start:** "I'm using the testing-standards skill to enforce testing requirements."

## When to Use This Skill

- Writing new tests for features or bug fixes
- Reviewing existing test quality and coverage
- Setting up test infrastructure or CI coverage gates
- Deciding test organization (unit vs integration vs E2E)
- Applying TDD workflow (Red → Green → Refactor → Cleanup)
- Adding property-based tests for complex logic

## Coverage Targets

Enforce minimum coverage thresholds

| Metric         | Threshold |
|----------------|-----------|
| Statements     | 70%+      |
| Branches       | 65%+      |
| Functions      | 75%+      |
| Lines          | 70%+      |
| Critical paths | 95%+      |

**CI must fail** if coverage drops below threshold.

**Rationale:**
- 70/65/75/70 establishes a practical baseline across core metrics
- 95% critical-path coverage protects business-critical logic from regressions
- Automated enforcement prevents coverage regression

## Test Organization

### Unit Tests

- Test individual functions/methods in isolation
- Located near the code they test
- Fast, deterministic, no external dependencies
- Focus on single responsibility

**Example structure:**
```
src/
  user.py
  user_test.py          # Co-located unit tests
tests/
  integration/
    test_user_api.py    # Integration tests
```

### Integration Tests

- Test public API interactions
- Verify components work together correctly
- Use realistic data, not mocks when possible
- Test at module boundaries

### End-to-End (E2E) Tests

- Test complete user workflows
- Verify the full system works as intended
- Include visual, accessibility, and behavioral validation
- Slowest tests, run less frequently

### Documentation Tests

- All public APIs should have runnable examples
- Examples should be tested as part of CI
- Examples serve as both documentation and validation

## Test Naming Convention

Use consistent, descriptive test names:
```
test_<unit>_<scenario>_<expected_outcome>
```

**Examples:**
- `test_parser_empty_input_returns_error`
- `test_validator_invalid_email_rejects`
- `test_api_unauthorized_request_returns_401`
- `test_cache_expired_entry_refetches_data`

**Why this matters:**
- Failed test names should explain what broke
- No need to read test body to understand intent
- Grep-friendly for finding specific scenarios

## Property-Based Testing

For complex logic and algebraic laws:
- Use property-based testing frameworks (QuickCheck, Hypothesis, PropTest)
- Verify mathematical properties (associativity, commutativity, identity)
- Test with generated inputs across wide ranges
- Catch edge cases human-written tests miss

**Example properties to test:**
- **Idempotency**: `f(f(x)) == f(x)`
- **Reversibility**: `decode(encode(x)) == x`
- **Invariants**: `sort(sort(list)) == sort(list)`
- **Commutativity**: `add(a, b) == add(b, a)`

## Test Quality Standards

### Deterministic

- No wall-clock time dependencies
- No execution order dependencies
- Same input always produces same output
- No random values without fixed seeds

**Bad:**
```python
def test_session_expires():
    session = create_session()
    time.sleep(2)  # Flaky: depends on wall-clock time
    assert session.is_expired()
```

**Good:**
```python
def test_session_expires():
    clock = FakeClock()
    session = create_session(clock)
    clock.advance(seconds=SESSION_TIMEOUT + 1)
    assert session.is_expired()
```

### Isolated

- Each test runs independently
- No shared mutable state between tests
- Use temporary files/directories, clean up after
- No network calls in unit tests

**Pattern:**
```python
def test_file_processing():
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("content")
        result = process_file(test_file)
        assert result == expected
        # tmpdir automatically cleaned up
```

### Realistic

- Prefer real implementations over mocks
- Mock only at system boundaries (network, file I/O, external APIs)
- Don't mock standard library or framework code
- Test real behavior, not mocked behavior

**Mock boundaries, not internals:**
- Mock HTTP client for external API calls
- Mock database connection for integration tests
- Do NOT mock `json.loads()` or similar stdlib functions
- Do NOT mock your own business logic

## TDD Workflow

1. **Red Phase**: Write failing test first
   ```bash
   run_tests test_new_feature  # Should fail
   ```

2. **Green Phase**: Implement minimal code to pass
   ```bash
   run_tests test_new_feature  # Should pass
   ```

3. **Refactor Phase**: Optimize while keeping tests green
   ```bash
   run_linter
   run_tests  # All tests should still pass
   ```

4. **Cleanup Phase**: Remove old/dead code
   ```bash
   # Remove deprecated code, update docs
   run_tests  # Ensure no regressions
   ```

## Regression Testing

If TDD isn't followed, **regression tests** are the required minimum:

1. Reproduce the bug with a failing test
2. Fix the bug
3. Verify test now passes
4. Commit both test and fix together

This prevents the same bug from recurring.

## Coverage Measurement

**Tools by language:**
- Python: pytest-cov, coverage.py
- JavaScript/TypeScript: Istanbul, c8
- Rust: tarpaulin, llvm-cov
- Go: built-in `go test -cover`
- Java: JaCoCo

**CI integration:**
```yaml
# Example: Enforce coverage in CI
- name: Run tests with coverage
  run: pytest --cov=src --cov-fail-under=80

- name: Report coverage
  run: coverage report --show-missing
```

## Checklist

When applying this skill, verify:

- [ ] Coverage meets thresholds (70/65/75/70, 95% critical)
- [ ] Tests are co-located or properly organized
- [ ] Test names follow `test_<unit>_<scenario>_<expected>` convention
- [ ] No wall-clock dependencies or shared mutable state
- [ ] Mocks only at system boundaries
- [ ] Property-based tests for algebraic/mathematical logic
- [ ] CI fails on coverage regression
- [ ] TDD cycle followed: Red → Green → Refactor → Cleanup
