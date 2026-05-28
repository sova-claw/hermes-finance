"""FastAPI application factory."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI

from finance_api.core.config import settings
from finance_api.core.logging.setup import configure_logging
from finance_api.domains.sync.monobank import run_sync
from finance_api.routers import accounts, budgets, health, sync, transactions

log = structlog.get_logger(__name__)

_DESCRIPTION = """
Finance API — a thin wrapper around Monobank that syncs your bank data to
PostgreSQL and exposes read-only analytics endpoints.

## Endpoints for Hermess bot

| Goal | Endpoint |
|---|---|
| Account balances | `GET /accounts` |
| Spending by category | `GET /transactions/spending?period=this_month` |
| Exclude bank transfers | `GET /transactions/spending?exclude_uncategorized=true` |
| Monthly income/expense trend | `GET /transactions/trend?months=3` |
| Recent transactions | `GET /transactions?limit=20` |
| Trigger a sync | `POST /sync` |
| Last sync status | `GET /sync/status` |
| Budget limits + spending | `GET /budgets` |
| Set a budget limit | `POST /budgets` |
| Remove a budget limit | `DELETE /budgets/{category}` |

## Periods

`this_month` · `last_month` · `last_7d` · `last_30d` · `last_90d`

## Account filtering

All transaction endpoints accept `?account_id=<uuid>` to scope results to one account.
"""


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    configure_logging(
        level=settings.log_level,
        json=settings.environment != "local",
    )

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        run_sync,
        "interval",
        hours=settings.sync_interval_hours,
        id="monobank_sync",
        max_instances=1,
        coalesce=True,
    )

    bot_app = None
    if settings.telegram_bot_token:
        from finance_api.domains.bot.runner import create_bot

        bot_app = create_bot(settings.telegram_bot_token)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        scheduler.start()
        log.info("scheduler_started", interval_hours=settings.sync_interval_hours)
        if bot_app:
            await bot_app.initialize()
            await bot_app.start()
            await bot_app.updater.start_polling(drop_pending_updates=True)
            log.info("telegram_bot_started")
        try:
            yield
        finally:
            scheduler.shutdown(wait=False)
            if bot_app:
                await bot_app.updater.stop()
                await bot_app.stop()
                await bot_app.shutdown()

    app = FastAPI(
        title="Finance API",
        version="0.1.0",
        description=_DESCRIPTION,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.include_router(health.router, tags=["health"])
    app.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
    app.include_router(
        transactions.router,
        prefix="/transactions",
        tags=["transactions"],
    )
    app.include_router(sync.router, prefix="/sync", tags=["sync"])
    app.include_router(budgets.router, prefix="/budgets", tags=["budgets"])

    return app
