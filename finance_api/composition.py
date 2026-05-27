"""FastAPI application factory."""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI

from finance_api.core.config import settings
from finance_api.core.logging.setup import configure_logging
from finance_api.domains.sync.monobank import run_sync
from finance_api.routers import accounts, health, sync, transactions

log = structlog.get_logger(__name__)


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

    app = FastAPI(title="Finance API", version="0.1.0", lifespan=lifespan)
    app.include_router(health.router)
    app.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
    app.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
    app.include_router(sync.router, prefix="/sync", tags=["sync"])

    return app
