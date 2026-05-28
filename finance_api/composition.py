"""FastAPI application factory."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from apscheduler.schedulers.background import (  # type: ignore[import-untyped]
    BackgroundScheduler,
)
from fastapi import FastAPI

from finance_api.core.config import settings
from finance_api.core.logging.setup import configure_logging
from finance_api.domains.sync.monobank import run_sync
from finance_api.routers import accounts, health, sync, transactions

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

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        scheduler.start()
        log.info("scheduler_started", interval_hours=settings.sync_interval_hours)
        try:
            yield
        finally:
            scheduler.shutdown(wait=False)

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

    return app
