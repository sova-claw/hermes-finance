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
    description="Returns the most recent transactions ordered by date descending. Filter by account_id to scope to one account.",
)
def list_transactions(
    limit: int = Query(default=20, ge=1, le=100, description="Maximum number of transactions to return"),
    account_id: UUID | None = Query(default=None, description="Filter to a specific account (use monobank account UUID)"),
) -> list[dict]:
    return queries.get_recent_transactions(limit=limit, account_id=account_id)


@router.get(
    "/spending",
    response_model=dict[str, float],
    summary="Spending by category",
    description=(
        "Returns total spending grouped by MCC-derived category. "
        "Use `exclude_uncategorized=true` to hide bank transfers and internal movements "
        "that have no MCC code."
    ),
)
def spending_by_category(
    period: Period = Query(default="this_month", description="Time window to analyse"),
    account_id: UUID | None = Query(default=None, description="Scope to a single account"),
    exclude_uncategorized: bool = Query(default=False, description="Exclude transactions with no MCC category (bank transfers)"),
) -> dict[str, float]:
    return queries.get_spending_by_category(
        period=period, account_id=account_id, exclude_uncategorized=exclude_uncategorized
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
    months: int = Query(default=3, ge=1, le=24, description="Number of calendar months to include"),
    account_id: UUID | None = Query(default=None, description="Scope to a single account"),
) -> list[dict]:
    return queries.get_monthly_trend(months=months, account_id=account_id)
