"""Account balance endpoints."""

from fastapi import APIRouter

from finance_api.domains.insights.queries import get_account_balances
from finance_api.schemas import AccountBalance

router = APIRouter()


@router.get(
    "",
    response_model=list[AccountBalance],
    summary="List account balances",
    description=(
        "Returns the current balance for every Monobank account that has been synced. "
        "Returns an empty list if no sync has run yet — call `POST /sync` first."
    ),
)
def list_accounts() -> list[dict[str, object]]:
    """Return current balances for all synced accounts."""
    return get_account_balances()
