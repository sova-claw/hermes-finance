import asyncio
import threading

import structlog
from aiogram import Bot, Dispatcher
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI

from hermess_api.bot.handlers import router as bot_router
from hermess_api.core.config import settings
from hermess_api.core.logging.setup import configure_logging
from hermess_api.domains.sync.monobank import run_sync
from hermess_api.routers.health import router as health_router

log = structlog.get_logger(__name__)


def create_app() -> FastAPI:
    configure_logging(
        level=settings.log_level,
        json=settings.environment != "local",
    )

    app = FastAPI(title="Hermess API", version="0.1.0")
    app.include_router(health_router)

    bot = Bot(token=settings.telegram_bot_token)
    dp = Dispatcher()
    dp.include_router(bot_router)

    scheduler = BackgroundScheduler()
    scheduler.add_job(run_sync, "interval", hours=settings.sync_interval_hours, id="monobank_sync")
    scheduler.start()
    log.info("scheduler_started", interval_hours=settings.sync_interval_hours)

    @app.on_event("startup")
    async def start_bot() -> None:
        loop = asyncio.get_event_loop()
        threading.Thread(
            target=lambda: loop.run_until_complete(dp.start_polling(bot)),
            daemon=True,
        ).start()
        log.info("telegram_bot_started")

    @app.on_event("shutdown")
    async def stop_scheduler() -> None:
        scheduler.shutdown(wait=False)

    return app
