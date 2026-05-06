---
description: "Use when writing commit messages, creating branches, reviewing git operations, or any git-related task. Covers Conventional Commits, branch naming, PR guidelines, and forbidden operations."
applyTo: "**"
---

# Git & Contribution Guidelines

Source of truth: [`CONTRIBUTING.md`](../../CONTRIBUTING.md). This file is a condensed reference for agent use.

## Branch naming

```
feature/<short-description>   # new functionality
fix/<short-description>        # bug fix
chore/<short-description>      # refactor, deps, infra, docs
docs/<short-description>       # documentation only
```

- Branch from `develop` (or `main` if `develop` does not exist).
- One PR = one focused objective. Keep branches short-lived.

## Commit messages — Conventional Commits (English)

```
<type>(<scope>): <imperative description, max 72 chars>

[optional body — why, not what]

[optional footer — BREAKING CHANGE: ..., Closes #<issue>]
```

**Allowed types:**

| Type | When to use |
|---|---|
| `feat` | New user-facing feature |
| `fix` | Bug fix |
| `chore` | Build, deps, tooling, CI — no production logic change |
| `docs` | Documentation only |
| `test` | Adding or fixing tests |
| `refactor` | Code change that is neither feat nor fix |
| `perf` | Performance improvement |
| `ci` | CI/CD configuration changes |
| `revert` | Reverts a previous commit |

**Rules:**
- Description in lowercase imperative mood: `add`, `fix`, `remove` — not `added`, `fixes`, `removing`.
- No period at the end of the subject line.
- Scope is optional but recommended: module, layer, or feature area (e.g., `auth`, `transactions`, `migrations`).
- Mark breaking changes with `BREAKING CHANGE:` in the footer.

**Good examples:**
```
feat(transactions): add csv export endpoint
fix(auth): prevent refresh token race on parallel requests
chore(deps): bump fastapi to 0.136.1
test(investments): cover negative balance rollback path
ci(quality): add frontend ESLint step
```

## Pull Request checklist

Before opening a PR, ALL of the following must pass:

**Backend:**
- `ruff check backend/app backend/tests`
- `pylint backend/app --fail-under=8.0`
- `bandit -q -r backend/app -ll`
- `pytest backend/tests --cov=backend/app --cov-fail-under=85`

**Frontend:**
- `npm run lint`
- `npm run typecheck`
- `npm run test:coverage`
- `npm run build`

**Migrations (if SQLAlchemy models changed):**
- Alembic revision generated, reviewed, and `upgrade`/`downgrade` both validated.

**PR description must include:** problem, approach, risks, test evidence, and the checklist from CONTRIBUTING.md.

## Forbidden operations (require explicit user confirmation)

- `git push --force` / `git push -f`
- `git reset --hard`
- `git commit --no-verify`
- Amending or rebasing published commits on shared branches
- Deleting remote branches without confirmation

## What agents must NOT do

- Generate commit messages that omit the type prefix.
- Use past tense or third person in commit subjects.
- Commit secrets, tokens, credentials, or `.env` files.
- Bypass pre-commit hooks with `--no-verify`.
- Squash or rebase `develop`/`main` without user confirmation.
