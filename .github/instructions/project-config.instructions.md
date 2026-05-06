---
description: "Use when editing project configuration files: docker-compose.yml, Dockerfiles, pyproject.toml, vite.config.ts, tailwind.config.js, eslint.config.js, tsconfig.json, playwright.config.ts, pytest.ini, alembic.ini, or CI workflow files. Covers naming conventions, environment variable handling, and cross-service consistency."
applyTo: "{docker-compose.yml,docker/**,backend/pyproject.toml,backend/pytest.ini,backend/alembic.ini,frontend/vite.config.ts,frontend/tailwind.config.js,frontend/tsconfig*.json,frontend/eslint.config.js,frontend/playwright.config.ts,.github/workflows/**}"
---

# Project Configuration Guidelines

## Environment variables
- Never hardcode secrets, passwords, or tokens in config files.
- Use `.env` files locally (excluded from git via `.gitignore`); reference `example.env` for required keys.
- In Docker/CI, inject via environment or secrets manager — never `ARG` for sensitive values.

## Docker
- `docker-compose.yml` — development only; keep service names consistent with `depends_on` and network aliases.
- Dockerfiles live in `docker/`; build args are non-sensitive only.
- Pin base image tags to a minor version (e.g., `python:3.12-slim`, not `latest`).

## Backend (`pyproject.toml`, `pytest.ini`, `alembic.ini`)
- Dependencies: pin with `~=` (compatible release) for stability.
- Test config: `pytest.ini` is the single source of truth for markers, paths, and coverage settings.
- Alembic: `alembic.ini` must reference `DATABASE_URL` from environment, never inline credentials.

## Frontend (`vite.config.ts`, `tsconfig*.json`, `tailwind.config.js`)
- Vite: keep `server.proxy` entries in sync with backend routes.
- TypeScript: `strict: true` always; do not weaken compiler options.
- Tailwind: all custom tokens live in `tailwind.config.js` — never add ad-hoc colors or spacing.

## CI (`.github/workflows/`)
- Each workflow has a single responsibility (CI, quality, security, frontend-CI).
- Secrets accessed only via `${{ secrets.NAME }}` — never echoed or logged.
- Alembic smoke check: `upgrade head` → `downgrade -1` → `upgrade head` in every backend CI run.
