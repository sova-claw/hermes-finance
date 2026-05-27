# hermes-finance

Personal finance analyzer delivered via Telegram. Connects to Monobank, stores your transaction history, and lets you ask questions in plain language — answered by Claude with charts.

Built as a foundation for personal assistant agents that need financial context.

---

## What it does

**Talk to your finances:**
> "How much did I spend on food last month?"
> "Show me a trend for the last 3 months."
> "What are my top categories this week?"

Claude uses tool use to query your real transaction data and replies with text or a chart.

**Automatic sync:** Monobank transactions are pulled hourly and stored in PostgreSQL. No manual exports.

**Telegram commands:**
| Command | What it does |
|---------|-------------|
| `/start` | Welcome + setup instructions |
| `/status` | Account balances |
| `/sync` | Trigger a sync immediately |
| `/report` | This month's summary + spending pie chart |
| _(any message)_ | Claude answers conversationally |

---

## Architecture

```
Telegram
   │
   ▼
aiogram (polling)
   │
   ▼
Claude API — tool use
   ├── get_account_balances()
   ├── get_spending_by_category(period)
   ├── get_monthly_trend(months)
   ├── get_recent_transactions(limit)
   └── generate_chart(type)  ──► matplotlib PNG
   │
   ▼
SQLModel / PostgreSQL
   ▲
Monobank Sync (APScheduler, hourly)
```

Single service: FastAPI + aiogram polling + APScheduler in one Railway process.

---

## Stack

| Concern | Choice |
|---------|--------|
| Language | Python 3.12 |
| Web framework | FastAPI + Pydantic v2 |
| ORM + migrations | SQLModel + Alembic |
| DB driver | psycopg 3 |
| Telegram bot | aiogram 3.x |
| LLM | Anthropic Claude (tool use) |
| Charts | matplotlib |
| Scheduler | APScheduler |
| Logging | structlog (JSON) |
| Deploy | Railway, multi-stage Dockerfile |

---

## Quick start

```bash
# 1. Install dependencies
cd api && uv sync

# 2. Configure environment
cp .env.example .env
# Fill in: DATABASE_URL, TELEGRAM_BOT_TOKEN, TELEGRAM_OWNER_ID,
#          ANTHROPIC_API_KEY, MONOBANK_TOKEN

# 3. Run migrations
uv run alembic upgrade head

# 4. Start
uv run python -m finance_api.main
```

---

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | yes | PostgreSQL connection string |
| `TELEGRAM_BOT_TOKEN` | yes | From @BotFather |
| `TELEGRAM_OWNER_ID` | yes | Your Telegram user ID (single-user gate) |
| `ANTHROPIC_API_KEY` | yes | Anthropic API key |
| `MONOBANK_TOKEN` | yes | Monobank personal token |
| `SYNC_INTERVAL_HOURS` | no | Default: `1` |
| `MONOBANK_FETCH_DAYS` | no | Days of history to fetch. Default: `730` |
| `ENVIRONMENT` | no | `local` or `production` |
| `LOG_LEVEL` | no | Default: `INFO` |

---

## Deploy (Railway)

1. Fork this repo under your account.
2. Create a Railway project, add a PostgreSQL service.
3. Add the app service linked to your fork's `main` branch.
4. Set all environment variables (reference `DATABASE_URL` from the Postgres service).
5. Push to `main` — Railway builds via `api/Dockerfile` and runs `alembic upgrade head` before start.

Health check: `GET /health`

---

## Agent integration

hermes-finance exposes financial tools designed for LLM agents:

```python
TOOLS = [
    get_account_balances,       # current balances per account
    get_spending_by_category,   # totals by category for a period
    get_monthly_trend,          # income vs expenses over N months
    get_recent_transactions,    # latest N transactions
    generate_chart,             # renders a PNG chart
]
```

Any agent with access to the PostgreSQL database can import `finance_api.domains.insights.tools` and dispatch the same tools — no Telegram required.
