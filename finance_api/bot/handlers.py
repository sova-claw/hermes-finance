"""Telegram command & message handlers."""
from __future__ import annotations

import threading
from typing import Any

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import FSInputFile, Message

from finance_api.bot import dp
from finance_api.core.config import settings
from finance_api.domains.insights import tools
from finance_api.domains.insights.queries import get_account_balances
from finance_api.domains.sync.monobank import run_sync

router = Router()


def _owner_only(func):
    """Decorator: only allow the owner to use the handler.

    Returns:
        The result of func if the user is the owner, None otherwise.
    """
    async def wrapper(message: Message, **kwargs: Any):
        if message.from_user is None:
            return
        if message.from_user.id != settings.telegram_owner_id:
            await message.answer("⛔ This is a private bot.")
            return
        return await func(message, **kwargs)
    return wrapper


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Handle /start command — show welcome message."""
    await message.answer(
        "👋 Welcome to your Finance Bot!\n\n"
        "Commands:\n"
        "  /status — Account balances\n"
        "  /sync   — Sync Monobank now\n"
        "  /report — This month + spending chart\n\n"
        "Or just ask me anything about your money."
    )


@router.message(Command("status"))
async def cmd_status(message: Message) -> None:
    """Handle /status — show account balances."""
    balances = get_account_balances()
    if not balances:
        await message.answer("No accounts synced yet. Use /sync first.")
        return
    lines = []
    for a in balances:
        bal = (
            f"{a['balance']:,.2f}"
            if isinstance(a["balance"], float)
            else str(a["balance"])
        )
        lines.append(f"• {a['name']}: {bal} {a['currency']}")
    await message.answer("\n".join(lines))


@router.message(Command("sync"))
async def cmd_sync(message: Message) -> None:
    """Handle /sync — trigger Monobank sync."""
    await message.answer("🔄 Syncing Monobank…")
    threading.Thread(target=run_sync, daemon=True).start()


@router.message(Command("report"))
async def cmd_report(message: Message) -> None:
    """Handle /report — this month summary + charts."""
    await message.answer("⏳ Generating report…")

    spending_raw = tools.dispatch(
        "get_spending_by_category", period="this_month"
    )
    spending_dict: dict[str, float] = (
        spending_raw if isinstance(spending_raw, dict) else {}
    )
    if not spending_dict:
        await message.answer("No spending data this month.")
        return

    lines = ["📊 This Month's Spending\n"]
    total = sum(spending_dict.values())
    sorted_spending = sorted(
        spending_dict.items(), key=lambda kv: kv[1], reverse=True
    )
    for cat, amount in sorted_spending:
        pct = amount / total * 100 if total else 0
        lines.append(f"• {cat}: {amount:,.2f} UAH ({pct:.0f}%)")
    lines.append(f"\nTotal: {total:,.2f} UAH")
    await message.answer("\n".join(lines))

    chart_path = tools.dispatch("generate_chart", chart_type="spending_pie")
    if isinstance(chart_path, str) and chart_path.endswith(".png"):
        await message.answer_photo(
            FSInputFile(chart_path), caption="Spending by category"
        )

    trend_path = tools.dispatch("generate_chart", chart_type="monthly_bar")
    if isinstance(trend_path, str) and trend_path.endswith(".png"):
        await message.answer_photo(
            FSInputFile(trend_path), caption="Monthly trend"
        )


@router.message(F.text)
async def handle_text(message: Message) -> None:
    """Handle free-text questions about finances."""
    text = message.text.strip()
    if not text:
        return

    await message.answer("💭 Thinking…")

    balances = tools.dispatch("get_account_balances")
    spending_raw = tools.dispatch(
        "get_spending_by_category", period="this_month"
    )
    trend_raw = tools.dispatch("get_monthly_trend", months=3)

    spending_dict: dict[str, float] = (
        spending_raw if isinstance(spending_raw, dict) else {}
    )
    trend_list: list[dict[str, Any]] = (
        trend_raw if isinstance(trend_raw, list) else []
    )
    balances_list: list[dict[str, Any]] = (
        balances if isinstance(balances, list) else []
    )

    reply = _build_reply(text, balances_list, spending_dict, trend_list)
    await message.answer(reply)


def _build_reply(
    question: str,
    balances: list[dict[str, Any]],
    spending: dict[str, float],
    trend: list[dict[str, Any]],
) -> str:
    """Build a concise text reply from financial data.

    Returns:
        A formatted string answering the user's question.
    """
    q = question.lower()

    if any(w in q for w in ["balance", "how much", "скільки", "баланс", "money"]):
        if not balances:
            return "No synced accounts. Use /sync first."
        lines = ["Your accounts:"]
        for a in balances:
            lines.append(f"• {a['name']}: {a['balance']:,.2f} {a['currency']}")
        return "\n".join(lines)

    spending_keywords = [
        "spent", "spending", "витрати", "spend", "expense", "food", "groceries"
    ]
    if any(w in q for w in spending_keywords):
        if not spending:
            return "No spending data this month."
        lines = ["Spending this month:"]
        for cat, amt in sorted(spending.items(), key=lambda kv: kv[1], reverse=True):
            lines.append(f"• {cat}: {amt:,.2f}")
        lines.append(f"\nTotal: {sum(spending.values()):,.2f}")
        return "\n".join(lines)

    trend_keywords = [
        "trend", "income", "earned", "заробіток", "тренд", "прибуток"
    ]
    if any(w in q for w in trend_keywords):
        if not trend:
            return "No trend data available."
        lines = ["Monthly trend:"]
        for row in trend:
            emoji = "✅" if row["income"] >= row["expenses"] else "🔴"
            inc = f"{row['income']:,.2f}"
            exp = f"{row['expenses']:,.2f}"
            lines.append(f"{emoji} {row['month']}: +{inc} / -{exp}")
        return "\n".join(lines)

    # Default summary
    lines: list[str] = []
    if balances:
        lines.append("💰 Balances:")
        for a in balances:
            lines.append(f"  {a['name']}: {a['balance']:,.2f} {a['currency']}")
    if spending:
        lines.append(f"\n📊 This month spent: {sum(spending.values()):,.2f}")
    if trend:
        last = trend[-1]
        inc = f"{last['income']:,.2f}"
        exp = f"{last['expenses']:,.2f}"
        lines.append(f"\n📈 {last['month']}: +{inc} / -{exp}")
    if not lines:
        return "I don't have any synced data yet. Use /sync to pull from Monobank."
    return "\n".join(lines)


dp.include_router(router)
