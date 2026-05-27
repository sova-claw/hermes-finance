---
name: tests-writer
description: Use when writing any test in this repo — new queries, bot handlers, sync logic, or health endpoints. Covers test layout, fixture usage, assertion patterns, and what every test must include. Invoke before writing any test file.
version: 1.0.0
---

# Test Writer — hermes-finance

Rules for writing tests inside `tests/`. These override generic pytest advice where they differ.

## Test layout

```
tests/
├── conftest.py              # env vars, session, app fixtures
├── integration/
│   ├── test_health.py       # GET /health
│   ├── test_sync.py         # monobank sync logic
│   ├── test_queries.py      # analytics queries
│   └── test_bot_handlers.py # aiogram handler unit tests
└── unit/
    ├── test_charts.py       # chart generators (no DB)
    └── test_tools.py        # dispatch logic
```

New domain → new file under `tests/integration/` or `tests/unit/` depending on whether DB is needed.

## Fixtures

All fixtures come from `tests/conftest.py`.

| Fixture | What it gives you |
|---------|------------------|
| `session` | SQLite in-memory `Session`, schema created fresh each test via `SQLModel.metadata.create_all` |
| `client` | `httpx.AsyncClient` wired to the FastAPI app |
| `settings` | `Settings` with test overrides via `monkeypatch` |

`conftest.py` sets all required env vars via `monkeypatch` (`autouse=True`). Never set env vars directly in test files.

## Test patterns

### Query tests (analytics)

```python
from finance_api.domains.insights.queries import get_account_balances
from finance_api.domains.accounts.models import Account


def test_get_account_balances(session):
    account = Account(
        monobank_id="abc123",
        name="Black",
        currency="UAH",
        account_type="black",
        balance=10000.0,
    )
    session.add(account)
    session.commit()

    result = get_account_balances(session)
    assert len(result) == 1
    assert result[0]["name"] == "Black"
    assert result[0]["balance"] == 10000.0
```

### Bot handler tests

Test handlers by calling the handler function directly with a mocked `Message`. Never start polling in tests.

```python
from unittest.mock import AsyncMock, MagicMock
from finance_api.bot.handlers import cmd_status


async def test_cmd_status_owner_only(session):
    message = MagicMock()
    message.from_user.id = 999  # not owner
    message.answer = AsyncMock()

    await cmd_status(message)
    message.answer.assert_not_called()
```

### Health endpoint tests

```python
async def test_health_ok(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
```

### Sync tests

Test sync logic against in-memory SQLite. Mock `httpx.AsyncClient` calls to Monobank API with `pytest-mock` or `unittest.mock.patch`.

```python
from unittest.mock import patch, AsyncMock
from finance_api.domains.sync.monobank import run_sync


async def test_sync_creates_transactions(session):
    mock_response = [
        {"id": "tx1", "amount": -5000, "description": "Cafe", ...}
    ]
    with patch("finance_api.domains.sync.monobank.fetch_transactions",
               new_callable=AsyncMock, return_value=mock_response):
        imported = await run_sync(session)
    assert imported == 1
```

## Assertion rules

- Assert on specific fields, not entire dicts — makes failures readable.
- After a write operation, call `session.expire_all()` before re-reading to bypass cache.
- Never assert on log output — only on return values and DB state.
- For error paths, assert the exception type and message, not the full traceback.

## Anti-patterns

- Never mock the DB — use in-memory SQLite. We've been burned by mock/real divergence.
- Never hardcode tokens or owner IDs in test files — read from `conftest.py` constants or `settings`.
- Never import from production fixtures or real Monobank responses — build minimal test data inline.
- Never start the full FastAPI app for unit tests — only for integration tests via `client` fixture.
- Never assert on log messages — they are not contract.
