"""Budget limit endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

from finance_api.domains.budgets.queries import (
    delete_budget,
    list_budgets_vs_spending,
    upsert_budget,
)

router = APIRouter()


class BudgetUpsert(BaseModel):
    """Request body for creating or updating a budget limit."""

    category: str
    monthly_limit: float
    currency: str = "UAH"

    @field_validator("monthly_limit")
    @classmethod
    def limit_must_be_positive(cls, v: float) -> float:
        """Ensure the monthly limit is a positive number."""
        if v <= 0:
            raise ValueError("monthly_limit must be positive")
        return v


@router.get(
    "",
    summary="List budget limits with current-month spending",
    description=(
        "Returns every category budget annotated with how much was spent this month, "
        "how much remains, and whether the limit has been exceeded."
    ),
)
def list_budgets() -> list[dict[str, Any]]:
    """Return all budget limits vs this-month spending."""
    return list_budgets_vs_spending()


@router.post(
    "",
    summary="Create or update a budget limit",
    description=(
        "Upserts a monthly spending limit for a category. "
        "Amounts are in the specified currency (default UAH)."
    ),
)
def set_budget(body: BudgetUpsert) -> dict[str, Any]:
    """Upsert a monthly limit for a category."""
    return upsert_budget(body.category, body.monthly_limit, body.currency)


@router.delete(
    "/{category}",
    summary="Remove a budget limit",
)
def remove_budget(category: str) -> dict[str, bool]:
    """Delete a budget limit. Returns 404 if the category has no limit set."""
    if not delete_budget(category):
        raise HTTPException(
            status_code=404,
            detail=f"No budget found for category '{category}'",
        )
    return {"deleted": True}
