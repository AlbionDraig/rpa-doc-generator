---
description: "Use when writing unit tests, integration tests, or e2e tests. Covers naming conventions, test structure (AAA), mocking patterns, coverage targets, and anti-patterns to avoid."
applyTo: "**/*.{test,spec}.{ts,tsx,py}"
---

# Testing Guidelines

## Naming convention
- Python: `test_should_{behavior}_when_{condition}`
- TypeScript: `should {behavior} when {condition}`
- One behavioral assertion per test — no multi-assert omnibus tests.

## Structure (Arrange / Act / Assert)
1. **Arrange** — set up state, inputs, and mocks.
2. **Act** — invoke the unit under test once.
3. **Assert** — verify exactly one observable outcome.

## Mocking
- Mock at system boundaries: DB sessions, HTTP clients, external services.
- Never mock the unit under test itself.
- Python: `pytest-mock` (`mocker` fixture).
- TypeScript: `vi.mock` / `vi.spyOn` (vitest).

## Coverage targets
- Services and business logic: ≥ 80%.
- API endpoints: happy path + main error codes (400, 401, 404, 422).
- UI components: at minimum render + primary user interaction.

## Test data
- Use fixtures or factories; never hardcode production IDs or tokens.
- Integration tests use isolated DB (in-memory or test schema); never hit production.

## Anti-patterns
- Trivial assertions: `assert True`, `expect(x).toBeDefined()` without checking value.
- Tests that depend on execution order or shared mutable state.
- Tests that call real external APIs or databases without isolation.
- Over-mocking internal implementation details — test behavior, not internals.
