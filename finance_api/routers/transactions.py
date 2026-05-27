"""Transaction and spending analytics endpoints."""
from typing import Any, Literal

from fastapi import APIRouter, Query

from finance_api.domains.insights import queries

router = APIRouter()

Period = Literal["this_month", "last_month", "last_7d", "last_30d", "last_90d"]


@router.get("")
def list_transactions(limit: int = Query(default=20, ge=1, le=100)) -> list[dict[str, Any]]:
    """Return the most recent transactions."""
    return queries.get_recent_transactions(limit)


@router.get("/spending")
def spending_by_category(period: Period = Query(default="this_month")) -> dict[str, float]:
    """Return spending totals grouped by category for the given period."""
    return queries.get_spending_by_category(period)


@router.get("/trend")
def monthly_trend(months: int = Query(default=3, ge=1, le=24)) -> list[dict[str, Any]]:
    """Return month-by-month income and expense totals."""
    return queries.get_monthly_trend(months)
