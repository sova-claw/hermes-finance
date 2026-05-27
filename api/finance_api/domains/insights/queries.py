"""Analytics queries over transactions and accounts."""
from datetime import date, timedelta
from typing import Any

from sqlmodel import Session, select, func

from finance_api.core.db.engine import engine
from finance_api.domains.accounts.models import Account
from finance_api.domains.transactions.models import Transaction


def _period_dates(period: str) -> tuple[date, date]:
    today = date.today()
    if period == "this_month":
        start = today.replace(day=1)
        return start, today
    if period == "last_month":
        first_this = today.replace(day=1)
        last_prev = first_this - timedelta(days=1)
        return last_prev.replace(day=1), last_prev
    if period == "last_7d":
        return today - timedelta(days=7), today
    if period == "last_30d":
        return today - timedelta(days=30), today
    if period == "last_90d":
        return today - timedelta(days=90), today
    # default: this_month
    return today.replace(day=1), today


def get_account_balances() -> list[dict[str, Any]]:
    with Session(engine) as session:
        accounts = session.exec(select(Account)).all()
        return [
            {"name": a.name, "currency": a.currency, "balance": a.balance, "type": a.account_type}
            for a in accounts
        ]


def get_spending_by_category(period: str = "this_month") -> dict[str, float]:
    start, end = _period_dates(period)
    with Session(engine) as session:
        rows = session.exec(
            select(Transaction.category, func.sum(Transaction.amount))
            .where(Transaction.date >= start)
            .where(Transaction.date <= end)
            .where(Transaction.amount < 0)
            .where(Transaction.is_pending == False)  # noqa: E712
            .group_by(Transaction.category)
        ).all()
        return {
            (cat or "Uncategorized"): round(abs(total), 2)
            for cat, total in rows
        }


def get_monthly_trend(months: int = 3) -> list[dict[str, Any]]:
    today = date.today()
    result = []
    for i in range(months - 1, -1, -1):
        first = (today.replace(day=1) - timedelta(days=i * 28)).replace(day=1)
        if first.month == 12:
            last = first.replace(year=first.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            last = first.replace(month=first.month + 1, day=1) - timedelta(days=1)

        with Session(engine) as session:
            income_row = session.exec(
                select(func.sum(Transaction.amount))
                .where(Transaction.date >= first)
                .where(Transaction.date <= last)
                .where(Transaction.amount > 0)
                .where(Transaction.is_pending == False)  # noqa: E712
            ).first()
            expense_row = session.exec(
                select(func.sum(Transaction.amount))
                .where(Transaction.date >= first)
                .where(Transaction.date <= last)
                .where(Transaction.amount < 0)
                .where(Transaction.is_pending == False)  # noqa: E712
            ).first()

        result.append({
            "month": first.strftime("%b %Y"),
            "income": round(income_row or 0, 2),
            "expenses": round(abs(expense_row or 0), 2),
        })
    return result


def get_recent_transactions(limit: int = 20) -> list[dict[str, Any]]:
    with Session(engine) as session:
        txs = session.exec(
            select(Transaction)
            .order_by(Transaction.date.desc(), Transaction.created_at.desc())  # type: ignore[attr-defined]
            .limit(limit)
        ).all()
        return [
            {
                "date": str(t.date),
                "description": t.description,
                "amount": t.amount,
                "currency": t.currency,
                "category": t.category,
            }
            for t in txs
        ]


def get_sync_health() -> dict[str, Any]:
    with Session(engine) as session:
        from finance_api.domains.sync.models import SyncRun
        last_run = session.exec(
            select(SyncRun).order_by(SyncRun.started_at.desc()).limit(1)  # type: ignore[attr-defined]
        ).first()
        if not last_run:
            return {"status": "never_synced"}
        return {
            "status": last_run.status,
            "started_at": str(last_run.started_at),
            "completed_at": str(last_run.completed_at) if last_run.completed_at else None,
            "tx_imported": last_run.tx_imported,
            "error": last_run.error,
        }
