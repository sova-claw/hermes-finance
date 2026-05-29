"""Telegram command handlers for the finance bot."""

import structlog
from telegram import Update
from telegram.ext import ContextTypes

from finance_api.domains.bot.formatter import (
    CATEGORY_EMOJI,
    _sym,
    format_balance,
    format_budget,
    format_stats,
    format_sync_status,
)
from finance_api.domains.budgets.queries import list_budgets_vs_spending, upsert_budget
from finance_api.domains.insights.queries import (
    get_account_balances,
    get_spending_by_category,
    get_sync_health,
)
from finance_api.domains.sync.monobank import run_sync

log = structlog.get_logger(__name__)

_VALID_PERIODS = {"this_month", "last_month", "last_7d", "last_30d", "last_90d"}


async def balance(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /balance command."""
    try:
        accounts = get_account_balances()
        await update.message.reply_html(format_balance(accounts))
    except Exception as e:
        log.error("balance_failed", error=str(e))
        await update.message.reply_html(f"❌ Error: <code>{e}</code>")


async def stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /stats [period] command."""
    try:
        period = (
            ctx.args[0] if ctx.args and ctx.args[0] in _VALID_PERIODS else "this_month"
        )
        spending = get_spending_by_category(period=period, exclude_uncategorized=False)
        await update.message.reply_html(format_stats(spending, period))
    except Exception as e:
        log.error("stats_failed", error=str(e))
        await update.message.reply_html(f"❌ Error: <code>{e}</code>")


async def budget(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /budget and /budget set <category> <amount> commands."""
    args = ctx.args or []

    if args and args[0] == "set":
        if len(args) < 3:
            await update.message.reply_html(
                "Usage: <code>/budget set &lt;category&gt; &lt;amount&gt;</code>\n"
                "Example: <code>/budget set Groceries 5000</code>"
            )
            return
        category = args[1]
        try:
            amount = float(args[2])
        except ValueError:
            await update.message.reply_html("Amount must be a number.")
            return
        upsert_budget(category, amount)
        em = CATEGORY_EMOJI.get(category, "📦")
        await update.message.reply_html(
            f"✅ Budget set: {em} <b>{category}</b> → {amount:,.0f} {_sym('UAH')}/month"
        )
        return

    if args and args[0] == "delete" and len(args) >= 2:
        from finance_api.domains.budgets.queries import delete_budget

        category = args[1]
        if delete_budget(category):
            await update.message.reply_html(f"🗑 Budget for <b>{category}</b> removed.")
        else:
            await update.message.reply_html(f"No budget found for <b>{category}</b>.")
        return

    budgets = list_budgets_vs_spending()
    await update.message.reply_html(format_budget(budgets))


async def sync(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /sync command — trigger Monobank sync in background."""
    try:
        await update.message.reply_html("🔄 Syncing…")
        run_sync()
        status = get_sync_health()
        await update.message.reply_html(format_sync_status(status))
    except Exception as e:
        log.error("sync_failed", error=str(e))
        await update.message.reply_html(f"❌ Sync failed: <code>{e}</code>")
