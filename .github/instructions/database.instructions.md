---
description: "Use when creating or modifying Alembic migrations, SQLAlchemy models, or database seed data. Covers safety rules, migration smoke checks, naming conventions, and safe schema change patterns."
applyTo: "backend/alembic/**"
---

# Database & Migrations Guidelines

## Alembic conventions
- Message slug: `alembic revision --autogenerate -m "<verb>_<object>"` (e.g., `add_currency_to_transactions`).
- Always review the generated `upgrade()` and `downgrade()` before applying.
- Never apply a migration with an empty or incorrect `downgrade()`.
- Smoke check sequence: `alembic upgrade head` → `alembic downgrade -1` → `alembic upgrade head`.

## Safe schema change patterns
| Change | Safe? | Rule |
|---|---|---|
| Add nullable column | ✅ | Apply directly |
| Add NOT NULL column | ⚠️ | Provide `server_default` or backfill first |
| Drop column | ⚠️ | Remove from code in one release, drop in the next |
| Rename column/table | ⚠️ | Add new → backfill → remove old (across releases) |
| Drop table | 🚫 | Requires explicit confirmation and data export |

## SQLAlchemy models (`app/models/`)
- Use `Mapped[T]` and `mapped_column()` (SQLAlchemy 2.0+ syntax).
- Avoid `Mapped[str | None]` union syntax if targeting Python < 3.12 — use `Optional[str]`.
- Always define `__tablename__` explicitly.
- Add indexes to columns used in WHERE / ORDER BY / JOIN conditions.
- Use `app/models/columns.py` for shared column definitions (audit timestamps, etc.).

## Data risk
- If a migration may cause data loss, document a mitigation plan in the file header.
- Backfill scripts go in `backend/db/seed.py` or a dedicated migration step, not ad-hoc.
