"""Analytics queries over transactions and accounts."""
from datetime import date, timedelta
from typing import Any
from uuid import UUID

from sqlmodel import Session, func, select

from finance_api.core.db.engine import engine
from finance_api.domains.accounts.models import Account
from finance_api.domains.sync.models import SyncRun
from finance_api.domains.transactions.models import Transaction


def _period_dates(period: str) -> tuple[date, date]:
    today = date.today()
    if period == "this_month":
        return today.replace(day=1), today
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
    return today.replace(day=1), today


def _month_range(year: int, month: int) -> tuple[date, date]:
    first = date(year, month, 1)
    if month == 12:
        last = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last = date(year, month + 1, 1) - timedelta(days=1)
    return first, last


def _months_ago(n: int) -> tuple[int, int]:
    """Return (year, month) for n months before the current month."""
    today = date.today()
    month = today.month - n
    year = today.year
    while month <= 0:
        month += 12
        year -= 1
    return year, month


def get_account_balances() -> list[dict[str, Any]]:
    """Return current balances for all synced accounts."""
    with Session(engine) as session:
        accounts = session.exec(select(Account)).all()
        return [
            {"name": a.name, "currency": a.currency, "balance": a.balance, "type": a.account_type}
            for a in accounts
        ]


def get_spending_by_category(
    period: str = "this_month",
    account_id: UUID | None = None,
    exclude_uncategorized: bool = False,
) -> dict[str, float]:
    """Return total spending grouped by category for the given period."""
    start, end = _period_dates(period)
    with Session(engine) as session:
        q = (
            select(Transaction.category, func.sum(Transaction.amount))
            .where(Transaction.date >= start)
            .where(Transaction.date <= end)
            .where(Transaction.amount < 0)
            .where(Transaction.is_pending == False)  # noqa: E712
        )
        if account_id:
            q = q.where(Transaction.account_id == account_id)
        if exclude_uncategorized:
            q = q.where(Transaction.category.is_not(None))  # type: ignore[attr-defined]
        q = q.group_by(Transaction.category)
        rows = session.exec(q).all()
        return {
            (cat or "Uncategorized"): round(abs(total), 2)
            for cat, total in rows
        }


def get_monthly_trend(
    months: int = 3,
    account_id: UUID | None = None,
) -> list[dict[str, Any]]:
    """Return month-by-month income and expense totals."""
    result = []
    for i in range(months - 1, -1, -1):
        year, month = _months_ago(i)
        first, last = _month_range(year, month)

        with Session(engine) as session:
            def _sum(condition: Any) -> float:
                base = (
                    select(func.sum(Transaction.amount))
                    .where(Transaction.date >= first)
                    .where(Transaction.date <= last)
                    .where(Transaction.is_pending == False)  # noqa: E712
                    .where(condition)
                )
                if account_id:
                    base = base.where(Transaction.account_id == account_id)
                return session.exec(base).first() or 0

            income = _sum(Transaction.amount > 0)
            expenses = _sum(Transaction.amount < 0)

        result.append({
            "month": first.strftime("%b %Y"),
            "income": round(income, 2),
            "expenses": round(abs(expenses), 2),
        })
    return result


def get_recent_transactions(
    limit: int = 20,
    account_id: UUID | None = None,
) -> list[dict[str, Any]]:
    """Return the most recent transactions, optionally filtered by account."""
    with Session(engine) as session:
        q = (
            select(Transaction)
            .order_by(Transaction.date.desc(), Transaction.created_at.desc())  # type: ignore[attr-defined]
            .limit(limit)
        )
        if account_id:
            q = q.where(Transaction.account_id == account_id)
        txs = session.exec(q).all()
        return [
            {
                "date": t.date.isoformat(),
                "description": t.description,
                "amount": t.amount,
                "currency": t.currency,
                "category": t.category,
            }
            for t in txs
        ]


def get_sync_health() -> dict[str, Any]:
    """Return the status of the most recent sync run."""
    with Session(engine) as session:
        last_run = session.exec(
            select(SyncRun).order_by(SyncRun.started_at.desc()).limit(1)  # type: ignore[attr-defined]
        ).first()
        if not last_run:
            return {"status": "never_synced"}
        return {
            "status": last_run.status,
            "started_at": last_run.started_at.isoformat() if last_run.started_at else None,
            "completed_at": last_run.completed_at.isoformat() if last_run.completed_at else None,
            "tx_imported": last_run.tx_imported,
            "error": last_run.error,
        }
