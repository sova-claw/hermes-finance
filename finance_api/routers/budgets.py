"""Budget limit endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

from finance_api.domains.budgets.queries import (
    delete_budget,
    list_budgets_vs_spending,
    upsert_budget,
)
from finance_api.domains.transactions.categories import ALL as VALID_CATEGORIES
from finance_api.schemas import BudgetItem, BudgetSet

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

    @field_validator("category")
    @classmethod
    def category_must_be_known(cls, v: str) -> str:
        """Reject categories that don't exist in the canonical category list."""
        if v not in VALID_CATEGORIES:
            raise ValueError(
                f"Unknown category '{v}'. Valid categories: {sorted(VALID_CATEGORIES)}"
            )
        return v


@router.get(
    "",
    response_model=list[BudgetItem],
    summary="List budget limits with current-month spending",
    description=(
        "Returns every category budget annotated with how much was spent this month, "
        "how much remains, and whether the limit has been exceeded. "
        "Budgets that are exceeded appear first."
    ),
)
def list_budgets() -> list[BudgetItem]:
    """Return all budget limits vs this-month spending."""
    return list_budgets_vs_spending()


@router.post(
    "",
    response_model=BudgetSet,
    summary="Create or update a budget limit",
    description=(
        "Upserts a monthly spending limit for a category. "
        "Category must be one of the canonical category names (see `categories.ALL`). "
        "Amounts are in the specified currency (default UAH)."
    ),
)
def set_budget(body: BudgetUpsert) -> BudgetSet:
    """Upsert a monthly limit for a category."""
    return upsert_budget(body.category, body.monthly_limit, body.currency)


@router.delete(
    "/{category}",
    response_model=dict[str, bool],
    summary="Remove a budget limit",
    description=(
        "Deletes the spending limit for a category. Returns 404 if none is set."
    ),
)
def remove_budget(category: str) -> dict[str, bool]:
    """Delete a budget limit. Returns 404 if the category has no limit set."""
    if not delete_budget(category):
        raise HTTPException(
            status_code=404,
            detail=f"No budget found for category '{category}'",
        )
    return {"deleted": True}
