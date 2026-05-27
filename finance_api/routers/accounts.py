"""Account balance endpoints."""
from typing import Any

from fastapi import APIRouter

from finance_api.domains.insights.queries import get_account_balances

router = APIRouter()


@router.get("")
def list_accounts() -> list[dict[str, Any]]:
    """Return current balances for all synced accounts."""
    return get_account_balances()
