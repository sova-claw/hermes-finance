# hermes-finance Claude Scope

Personal finance assistant delivered via Telegram. Connects to Monobank, stores transactions in PostgreSQL, and answers financial questions conversationally with charts.

```
finance_api/   — FastAPI + aiogram + APScheduler (single Railway service)
  bot/           — aiogram bot, handlers, commands
  domains/
    insights/      — tools.py (dispatch), charts.py (matplotlib), queries.py (DB)
    sync/          — Monobank sync (APScheduler, hourly)
    accounts/      — Account model
    transactions/  — Transaction model
  routers/       — REST API endpoints (HTTP fallback for Hermes)
tests/         — pytest integration + unit tests
```

## Route Work To The Right Context

- `finance_api/`: use `backend-developer` agent. Load `api-skill` before any edit or review.
- Architecture questions, new domains, structural decisions: use `software-architect` agent.

## Core Architecture Rules

```
bot/handlers.py  →  domains/insights/tools.py (tool dispatch)
                 →  domains/insights/queries.py (analytics)
                 →  domains/insights/charts.py (matplotlib PNGs)
domains/sync/monobank.py  →  DB directly (APScheduler, hourly)
```

- Handlers are Telegram boundary only — no analytics logic.
- Queries take `Session`, return plain dicts/lists — no HTTP, no AI.
- Charts take data, return tmp PNG path — no DB access.
- All config from `Settings`. No hardcoded tokens, URLs, or intervals.

## GitHub Account

**Always switch to `sova-claw` before creating PRs:**

```bash
gh auth switch --user sova-claw
gh pr create ...
```

`nazar-khimin` is not a collaborator on the `sova-claw/hermes-finance` repo.

## Railway

Project: `hermes-finance` (sova-claw workspace)
Deploy: push to `main` → Railway auto-deploys via Dockerfile.
Pre-deploy: `alembic upgrade head` (configured in `railway.toml`).

## Guardrails

- Never push directly to `main` for feature work — use a branch.
- Never hardcode secrets, tokens, or API keys in source.
- Required config fails loud if missing (no silent defaults in `Settings`).
- Owner-gate every Telegram handler via `TELEGRAM_OWNER_ID`.

## Commit Style

```
<scope>: <what>  (imperative, lowercase)

feat(sync): add cashback transaction handling
fix(bot): handle empty account list in /status
chore(deps): bump aiogram to 3.14.0
```

## Workflow

- `ruff check finance_api/` before committing.
- `/tests-runner` to verify tests pass.
- `/code-review` before merging.

## Context Rules

- `/compact` when context grows large.
- `/clear` when switching features.
