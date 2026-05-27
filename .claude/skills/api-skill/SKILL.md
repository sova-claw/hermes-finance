---
name: api-skill
description: MUST invoke before any edit or review inside finance_api/. Enforces repo-specific conventions for layering, bot handlers, Claude tool use, sync, queries, and migrations.
version: 1.0.0
---

# hermes-finance Backend Guidelines

Concise rules for agents working inside `finance_api/`. **These override generic FastAPI/aiogram advice where they differ.**

## Layering (do not skip)

```
bot/handlers.py  →  domains/insights/tools.py  →  domains/insights/queries.py
                                                →  domains/insights/charts.py
domains/sync/monobank.py  →  DB directly (SQLModel Session)
```

- **Bot handlers** — Telegram boundary: parse messages, owner gate, call dispatch or queries, send responses. No analytics logic.
- **tools.py** — Claude tool definitions + `dispatch()`. Orchestrates calls to queries and charts. Returns data Claude can use in tool results.
- **queries.py** — All read-side analytics. Takes `Session`, returns plain Python dicts/lists. No HTTP, no Telegram, no AI.
- **charts.py** — matplotlib generators. Take plain data, return tmp PNG path. No DB access.
- **monobank.py** — Sync logic. Writes accounts, transactions, sync_runs. Owns idempotency via `monobank_id`.
- **models.py** — SQLModel table definitions only (`table=True`). No logic.
- **core/** — config (pydantic-settings), db engine + session, structlog setup.

## Config — env-first, fail loud

All settings live in `core/config.py` as `Settings(BaseSettings)`. Required fields have no default. Access via `get_settings()` (cached with `@lru_cache`). Never hardcode tokens, URLs, intervals, or limits in call sites.

## Logging

`structlog` only. `log = structlog.get_logger(__name__)`. Snake_case event names with `key=value` pairs. Never use `print()` or stdlib `logging` directly.

## Bot handlers

- Owner-gate every handler: check `message.from_user.id == settings.telegram_owner_id` before processing.
- Never do analytics inline in a handler — call `dispatch()` or a query function.
- Charts: use `FSInputFile(path)` to send PNGs. Always clean up the tmp file after sending.
- Free-text messages → Claude tool use loop via `bot/claude_client.py` (or equivalent).

## Claude tool use

- Tool definitions live in `domains/insights/tools.py` as a `TOOLS` list.
- `dispatch(tool_name, tool_input, session)` dispatches to the correct query/chart function.
- Tool results must be JSON-serializable plain dicts or lists. No SQLModel objects.
- Never inline tool logic in bot handlers or the main Claude loop.

## Monobank sync

- Idempotency: `monobank_id` unique constraint on `transactions`. Use `INSERT ... ON CONFLICT DO NOTHING` or catch `IntegrityError`.
- MCC → category mapping lives in a lookup dict in `monobank.py`. New MCCs extend the dict.
- Rate limit: Monobank allows one API call per 60 seconds per token. Respect this with `time.sleep` between account fetches.
- `SyncRun` records: always write a `started_at` row first, update `completed_at`, `tx_imported`, and `status` at end. On exception, set `status = "error"` and `error = str(exc)`.

## Alembic migrations

- Filename: `NNNN_<slug>.py` (4-digit sequence, e.g. `0001_initial_schema.py`).
- One migration = one logical unit. Don't mix unrelated table changes.
- Wrap `alter_column` / `add_column` in `op.batch_alter_table(...)` for SQLite compatibility during tests.
- Provide a real `downgrade()` — never `pass`.
- `server_default` on every new NOT NULL column.

## Time

Always `datetime.now(timezone.utc)`. Never `datetime.utcnow()`.

## Anti-patterns (reject in review)

- Analytics logic in bot handlers.
- Direct DB access in `charts.py`.
- HTTP or Telegram imports in `queries.py` or `charts.py`.
- `print()` or stdlib `logging` anywhere — use structlog.
- Hardcoded tokens, API keys, or intervals — must come from `Settings`.
- `Optional[X]` — use `X | None` (PEP 604).
- Unhandled `monobank_id` conflicts — always handle duplicates explicitly.
- Sending charts without cleaning up tmp files.
- Missing owner gate in a bot handler.
