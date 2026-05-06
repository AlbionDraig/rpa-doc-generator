---
description: "Use when writing Python backend code, FastAPI endpoints, SQLAlchemy models, Pydantic schemas, services, or repositories. Covers architecture layers, async patterns, error handling, and test conventions."
applyTo: "backend/**/*.py"
---

# Backend (Python / FastAPI) Guidelines

## Architecture layers
- `app/api/v1/` — HTTP routing only: parse request, call service, return response schema.
- `app/services/` — Business logic; injected via `Depends()`; no HTTP concerns.
- `app/repositories/` — All DB access; receive `AsyncSession` as dependency.
- `app/models/` — SQLAlchemy ORM definitions.
- `app/schemas/` — Pydantic contracts (request / response); never expose ORM models directly.

## Async & sessions
- All endpoints and DB operations use `async def`.
- Inject `db: AsyncSession = Depends(get_db)` — never instantiate sessions manually.
- Avoid synchronous blocking calls inside async routes.

## Schemas (Pydantic v2)
- Response schemas: `model_config = ConfigDict(from_attributes=True)`.
- Use `Annotated[type, Field(...)]` for validations and OpenAPI docs.
- Separate `Create`, `Update`, `Response` schemas per resource.

## Error handling
- Client errors → `HTTPException` with a descriptive `detail` string.
- Domain errors → raise custom exceptions in services; translate to `HTTPException` in routers.
- Never silence exceptions with bare `except: pass`.

## Security
- Auth via `app/core/security.py`; never implement custom token logic inline.
- No secrets or tokens in code — use env vars from `app/core/config.py`.
- Validate and sanitize all external input at the schema layer.

## Docstrings & comments
- Module, class, and function docstrings: **English** (OpenAPI/Sphinx compatible).
- Inline comments explaining business logic or non-obvious decisions: **Spanish or English**, consistent with the file's prevailing language.
- Never mix languages within the same docstring or comment block.

## Tests
- Unit (`tests/unit/`): mock DB with `AsyncMock`; test pure service logic.
- Integration (`tests/integration/`): use `httpx.AsyncClient`; test HTTP contracts.
- Runner: `pytest -q --tb=short --cov=app`
