---
name: tests-runner
description: Use when running tests, checking test output, debugging failures, or verifying coverage. Covers the right commands to run from the right directory and how to read failures. Invoke before running any pytest command.
version: 1.0.0
---

# Test Runner — hermes-finance

## Where to run from

Always run pytest from the **repo root** (`/path/to/hermes-finance/`), never from `api/`. The root `pyproject.toml` owns the authoritative pytest config:

```toml
[tool.pytest.ini_options]
pythonpath = ["api"]
asyncio_mode = "auto"
env_files = [".env.test"]
```

## Commands

```bash
# Full suite
uv run pytest

# Single file
uv run pytest tests/integration/test_health.py

# Single test by name
uv run pytest tests/integration/test_health.py::test_health_ok

# Verbose output
uv run pytest -v

# Stop on first failure
uv run pytest -x

# Skip slow tests
uv run pytest -m "not slow"

# Rerun only failures from last run
uv run pytest --lf
```

## Test categories

| Path | Category | Needs |
|------|----------|-------|
| `tests/integration/` | API + bot integration | In-memory SQLite, `.env.test` |
| `tests/unit/` | Pure logic (queries, tools) | No DB needed |

Integration tests run via `uv run pytest`. There are no e2e tests that hit live Telegram or Monobank.

## Environment

`.env.test` at repo root provides test env vars. `conftest.py` overrides any required `Settings` fields via `monkeypatch`. Never set env vars directly in test files.

## Reading failures

**Import error on startup** — almost always a missing env var. Check `.env.test` covers all required `Settings` fields.

**`sqlalchemy.exc.OperationalError`** — schema mismatch. The test `session` fixture uses `SQLModel.metadata.create_all(engine)` on in-memory SQLite — if a model changed, the in-memory schema reflects current models, not migrations. Tests always reflect current models.

**`assert resp.status_code == ...` fails** — print `resp.json()` to see the actual error body.

**Bot handler not triggered** — aiogram handlers are tested by directly calling the handler function with a mocked `Message`, not by starting polling. Check `conftest.py` for the mock pattern.

## Before marking a task done

Run the full suite once: `uv run pytest -q`. If it passes, report the count. Never claim tests pass without running them.
