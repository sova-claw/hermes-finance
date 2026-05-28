"""FastAPI application factory."""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from finance_api.core.config import settings
from finance_api.core.logging.setup import configure_logging
from finance_api.domains.sync.monobank import run_sync
from finance_api.routers import accounts, health, sync, transactions

log = structlog.get_logger(__name__)

_DESCRIPTION = """
Finance API — a thin wrapper around Monobank that syncs your bank data to
PostgreSQL and exposes read-only analytics endpoints.

## What Hermess bot should call

| Goal | Endpoint |
|---|---|
| Account balances | `GET /accounts` |
| Spending by category | `GET /transactions/spending?period=this_month` |
| Monthly income/expense trend | `GET /transactions/trend?months=3` |
| Recent transactions | `GET /transactions?limit=20` |
| Trigger a sync | `POST /sync` |
| Last sync status | `GET /sync/status` |

## Periods

`this_month`, `last_month`, `last_7d`, `last_30d`, `last_90d`

## Sync

Monobank is synced automatically every `SYNC_INTERVAL_HOURS` (default 1h).
Trigger a manual sync with `POST /sync` — it returns immediately and runs in
the background.
"""


def _custom_openapi(app: FastAPI) -> dict:
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title="Finance API",
        version="0.1.0",
        summary="Monobank analytics wrapper for Hermess bot",
        description=_DESCRIPTION,
        routes=app.routes,
    )
    app.openapi_schema = schema
    return schema


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
        yield
        scheduler.shutdown(wait=False)

    app = FastAPI(
        title="Finance API",
        version="0.1.0",
        description=_DESCRIPTION,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.openapi = lambda: _custom_openapi(app)  # type: ignore[method-assign]

    app.include_router(health.router, tags=["health"])
    app.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
    app.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
    app.include_router(sync.router, prefix="/sync", tags=["sync"])

    return app
