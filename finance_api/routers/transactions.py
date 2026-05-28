"""Transaction and spending analytics endpoints."""

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Query

from finance_api.domains.insights import queries
from finance_api.schemas import MonthlyTrend, TransactionItem

router = APIRouter()

Period = Literal["this_month", "last_month", "last_7d", "last_30d", "last_90d"]


@router.get(
    "",
    response_model=list[TransactionItem],
    summary="List recent transactions",
    description=(
        "Returns transactions ordered by date descending. "
        "Use `period` to scope to a time window (e.g. `last_7d`, `this_month`). "
        "Without `period`, returns the most recent `limit` transactions. "
        "Filter by `account_id` to scope to one account."
    ),
)
def list_transactions(
    limit: int = Query(
        default=20,
        ge=1,
        le=200,
        description="Maximum number of transactions to return",
    ),
    period: Period | None = Query(
        default=None,
        description="Optional time window — returns transactions in period up to limit",
    ),
    account_id: UUID | None = Query(
        default=None,
        description="Filter to a specific account (use account_id from GET /accounts)",
    ),
) -> list[dict[str, object]]:
    """Return transactions, optionally scoped to a period and account."""
    return queries.get_recent_transactions(
        limit=limit, period=period, account_id=account_id
    )


@router.get(
    "/spending",
    response_model=dict[str, float],
    summary="Spending by category",
    description=(
        "Returns total spending grouped by MCC-derived category. "
        "Use `exclude_uncategorized=true` to hide bank transfers and "
        "internal movements that have no MCC code."
    ),
)
def spending_by_category(
    period: Period = Query(
        default="this_month",
        description="Time window to analyse",
    ),
    account_id: UUID | None = Query(
        default=None,
        description="Scope to a single account",
    ),
    exclude_uncategorized: bool = Query(
        default=False,
        description=("Exclude transactions with no MCC category (bank transfers)"),
    ),
) -> dict[str, float]:
    """Return total spending grouped by category."""
    return queries.get_spending_by_category(
        period=period,
        account_id=account_id,
        exclude_uncategorized=exclude_uncategorized,
    )


@router.get(
    "/trend",
    response_model=list[MonthlyTrend],
    summary="Monthly income vs expense trend",
    description=(
        "Returns month-by-month income and expense totals. "
        "Month boundaries are exact calendar months, not 30-day windows."
    ),
)
def monthly_trend(
    months: int = Query(
        default=3,
        ge=1,
        le=24,
        description="Number of calendar months to include",
    ),
    account_id: UUID | None = Query(
        default=None,
        description="Scope to a single account",
    ),
) -> list[dict[str, object]]:
    """Return month-by-month income and expense totals."""
    return queries.get_monthly_trend(months=months, account_id=account_id)
