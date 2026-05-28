"""Health check endpoint."""

import structlog
from fastapi import APIRouter

from finance_api.domains.insights.queries import get_sync_health
from finance_api.schemas import HealthResponse, SyncStatus

log = structlog.get_logger(__name__)
router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description=(
        "Always returns HTTP 200. The `sync` field shows last sync status "
        "— use this to verify the DB is reachable."
    ),
    tags=["health"],
)
def health() -> HealthResponse:
    """Returns service health. Always 200 — sync field shows DB status."""
    try:
        sync_data = get_sync_health()
        sync = SyncStatus(**sync_data)
    except Exception as exc:
        log.warning("health_db_error", error=str(exc))
        sync = SyncStatus(status="db_unavailable")
    return HealthResponse(status="ok", sync=sync)
