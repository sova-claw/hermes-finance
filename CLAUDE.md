# hermes-finance Claude Scope

Personal finance assistant delivered via Telegram. Connects to Monobank, stores transactions in PostgreSQL, and uses Claude tool use to answer financial questions conversationally with charts.

```
api/finance_api/   — FastAPI + aiogram + APScheduler (single Railway service)
src/               — SDK package (future)
tests/             — pytest integration + unit tests
```

## Route Work To The Right Context

- `api/finance_api/`: use `backend-developer` agent. Load `api-skill` before any edit or review.
- Architecture questions, new domains, structural decisions: use `software-architect` agent.

## Core Architecture Rules

```
bot/handlers.py  →  domains/insights/tools.py (Claude dispatch)
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

Use the `/use-railway` skill for any Railway operations.

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
chore(deps): bump anthropic to 0.41.0
```

## Workflow

- `/lint-check` before committing.
- `/tests-runner` to verify tests pass.
- `/pr-description` to generate PR body.
- `/code-review` before merging.

## Context Rules

- `/compact` when context grows large.
- `/clear` when switching features.
