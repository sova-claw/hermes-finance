"""Format Finance API data as Telegram HTML messages."""

from datetime import date
from typing import Any

CATEGORY_EMOJI: dict[str, str] = {
    "Groceries": "🛒",
    "Supermarket": "🛒",
    "Restaurants": "🍔",
    "Food": "🍔",
    "Outside food": "🍔",
    "Cafe": "🍔",
    "Transport": "🚇",
    "Commuting": "🚇",
    "Taxi": "🚕",
    "Housing": "🏠",
    "Utilities": "🏠",
    "Rent": "🏠",
    "Health": "💊",
    "Pharmacy": "💊",
    "Clothes": "👗",
    "Shopping": "🛍️",
    "Entertainment": "🎮",
    "Travel": "✈️",
    "Financial": "💳",
    "Transfers": "💸",
    "Income": "💰",
    "Salary": "💰",
    "Other": "📦",
    "Uncategorized": "📦",
}

CURRENCY_SYMBOL: dict[str, str] = {"UAH": "₴", "USD": "$", "EUR": "€", "GBP": "£"}

_PERIOD_LABEL: dict[str, str] = {
    "this_month": date.today().strftime("%B %Y"),
    "last_month": "last month",
    "last_7d": "last 7 days",
    "last_30d": "last 30 days",
    "last_90d": "last 90 days",
}


def _emoji(category: str) -> str:
    return CATEGORY_EMOJI.get(category, "📦")


def _sym(currency: str) -> str:
    return CURRENCY_SYMBOL.get(currency, currency)


def format_balance(accounts: list[dict[str, Any]]) -> str:
    """Format account balances as HTML."""
    if not accounts:
        return "No accounts synced yet. Run /sync first."
    lines = ["<b>💳 Accounts</b>", ""]
    for a in accounts:
        sym = _sym(a["currency"])
        name = a["name"]
        bal = a["balance"]
        lines.append(f"<code>{name:<20} {bal:>12,.2f} {sym}</code>")
    return "\n".join(lines)


def format_stats(spending: dict[str, float], period: str = "this_month") -> str:
    """Format spending breakdown as HTML."""
    if not spending:
        return f"No spending data for {_PERIOD_LABEL.get(period, period)}."
    total = sum(spending.values())
    label = _PERIOD_LABEL.get(period, period)
    lines = [f"<b>📊 Spending — {label}</b>", ""]
    for cat, amount in sorted(spending.items(), key=lambda x: x[1], reverse=True):
        pct = round(amount / total * 100) if total else 0
        em = _emoji(cat)
        lines.append(f"{em} <b>{cat}</b>  {amount:,.0f} ₴  <i>{pct}%</i>")
    lines += ["", f"<b>Total: {total:,.0f} ₴</b>"]
    return "\n".join(lines)


def format_budget(budgets: list[dict[str, Any]]) -> str:
    """Format budget limits vs spending as HTML."""
    label = date.today().strftime("%B %Y")
    if not budgets:
        return (
            f"<b>📉 Budget — {label}</b>\n\n"
            "No limits set yet.\n"
            "Use <code>/budget set &lt;category&gt; &lt;amount&gt;</code> to add one."
        )
    lines = [f"<b>📉 Budget — {label}</b>", ""]
    for b in budgets:
        em = _emoji(b["category"])
        spent = b["spent"]
        limit = b["monthly_limit"]
        sym = _sym(b["currency"])
        if b["exceeded"]:
            over = spent - limit
            lines.append(
                f"{em} <b>{b['category']}</b>  {spent:,.0f} / {limit:,.0f} {sym}  "
                f"⚠️ <i>over by {over:,.0f}</i>"
            )
        else:
            left = b["remaining"]
            lines.append(
                f"{em} <b>{b['category']}</b>  {spent:,.0f} / {limit:,.0f} {sym}  "
                f"✅ <i>{left:,.0f} left</i>"
            )
    return "\n".join(lines)


def format_sync_status(status: dict[str, Any]) -> str:
    """Format sync status as HTML."""
    if status.get("status") == "never_synced":
        return "🔄 Sync started. No previous sync on record."
    s = status.get("status", "unknown")
    imported = status.get("tx_imported", 0)
    completed = status.get("completed_at", "—")
    return (
        f"🔄 Sync triggered.\n"
        f"Last run: <b>{s}</b>, {imported} tx imported\n"
        f"Completed: {completed}"
    )
