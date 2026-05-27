"""FastAPI application factory."""
import asyncio
import threading
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from aiogram import Bot, Dispatcher
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI

from finance_api.bot.handlers import router as bot_router
from finance_api.core.config import settings
from finance_api.core.logging.setup import configure_logging
from finance_api.domains.sync.monobank import run_sync
from finance_api.routers.health import router as health_router

log = structlog.get_logger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    configure_logging(
        level=settings.log_level,
        json=settings.environment != "local",
    )

    bot = Bot(token=settings.telegram_bot_token)
    dp = Dispatcher()
    dp.include_router(bot_router)

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
        threading.Thread(
            target=lambda: asyncio.run(dp.start_polling(bot, handle_signals=False)),
            daemon=True,
        ).start()
        log.info("services_started", interval_hours=settings.sync_interval_hours)
        yield
        scheduler.shutdown(wait=False)
        log.info("services_stopped")

    app = FastAPI(title="Finance Agent API", version="0.1.0", lifespan=lifespan)
    app.include_router(health_router)

    return app
