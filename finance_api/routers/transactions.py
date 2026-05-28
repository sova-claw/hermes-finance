"""Transaction and spending analytics endpoints."""
from typing import Literal

from fastapi import APIRouter, Query

from finance_api.domains.insights import queries
from finance_api.schemas import MonthlyTrend, TransactionItem

router = APIRouter()

Period = Literal["this_month", "last_month", "last_7d", "last_30d", "last_90d"]


@router.get(
    "",
    response_model=list[TransactionItem],
    summary="List recent transactions",
    description="Returns the most recent transactions ordered by date descending.",
)
def list_transactions(
    limit: int = Query(default=20, ge=1, le=100, description="Maximum number of transactions to return"),
) -> list[dict]:
    """Return the most recent transactions."""
    return queries.get_recent_transactions(limit)


@router.get(
    "/spending",
    response_model=dict[str, float],
    summary="Spending by category",
    description=(
        "Returns total spending grouped by MCC-derived category for the given period. "
        "Keys are category names (e.g. 'Food & Drink', 'Groceries', 'Transportation'). "
        "Values are absolute amounts in the account's currency."
    ),
)
def spending_by_category(
    period: Period = Query(default="this_month", description="Time window to analyse"),
) -> dict[str, float]:
    """Return spending totals grouped by category."""
    return queries.get_spending_by_category(period)


@router.get(
    "/trend",
    response_model=list[MonthlyTrend],
    summary="Monthly income vs expense trend",
    description=(
        "Returns month-by-month income and expense totals. "
        "Useful for plotting a bar or line chart of financial trends."
    ),
)
def monthly_trend(
    months: int = Query(default=3, ge=1, le=24, description="Number of calendar months to include"),
) -> list[dict]:
    """Return month-by-month income and expense totals."""
    return queries.get_monthly_trend(months)
