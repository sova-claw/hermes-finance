from fastapi import APIRouter
from finance_api.domains.insights.queries import get_sync_health

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "sync": get_sync_health()}
