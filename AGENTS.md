# AGENTS Guide - rpa-doc-generator

This file defines the default steering context for AI agents working in this repository.

## Goal

Build and maintain a FastAPI service that generates technical documentation for Automation Anywhere projects with clear architecture boundaries, test coverage, and safe operations.

## Repository map

- Runtime entrypoint: `app/main.py`
- API layer: `app/api/`
- Application/use-cases: `app/application/`
- Domain analysis/parsing logic: `app/analysis/`, `app/parser/`
- Infrastructure/adapters: `app/ingestion/`, `app/generator/`
- Tests: `tests/`
- CI: `.github/workflows/ci.yml`

## Mandatory working rules

1. Preserve Clean Architecture boundaries.
2. Keep business logic out of API routes.
3. Add or update tests for non-trivial changes.
4. Avoid unrelated refactors in focused tasks.
5. Never use destructive commands without explicit user confirmation.

## Quality gates before closing changes

Run the same validations used in CI:

```bash
ruff check --select E9,F63,F7,F82 app tests
python -m coverage erase
python -m coverage run -m pytest tests -q
python -m coverage report --fail-under=90 -m
```

## AI steering sources

Agents must read and follow these files when applicable:

- Global guidance: `.github/copilot-instructions.md`
- Rules by area: `.github/instructions/*.instructions.md`
- Reusable prompts: `.github/prompts/*.prompt.md`
- Agent profiles: `.github/agents/*.agent.md`
- Hook policy: `.github/hooks/policy.json`
- Hook script: `.github/hooks/scripts/pre-safety.js`

## Agent selection guidance

- Use **Implementer** for writing/fixing code and tests.
- Use **Reviewer** for audits and findings-only reviews.
- Use **Explore** for fast, read-only repository discovery.

## Hook behavior

`PreToolUse` hook requests confirmation when potentially destructive patterns are detected (for example: `git reset --hard`, `git push --force`, `rm -rf`, `drop table`).

## Notes

- `tmp/` and `output/` are runtime artifacts and should not be committed.
- `.github/` assets are intentionally versioned to preserve AI behavior consistency across collaborators.
