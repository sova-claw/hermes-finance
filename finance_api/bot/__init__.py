"""Telegram bot setup — creates aiogram Bot + Dispatcher with memorybased FSM."""
from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from finance_api.core.config import settings

storage = MemoryStorage()
bot = Bot(token=settings.telegram_bot_token)
dp = Dispatcher(storage=storage)
