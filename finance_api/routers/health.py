"""Health check endpoint."""

from typing import Any

import structlog
from fastapi import APIRouter

from finance_api.domains.insights.queries import get_sync_health

log = structlog.get_logger(__name__)
router = APIRouter()


@router.get(
    "/health",
    summary="Health check",
    description=(
        "Always returns HTTP 200. The `sync` field shows last sync status "
        "— use this to verify the DB is reachable."
    ),
    tags=["health"],
)
def health() -> dict[str, Any]:
    """Returns service health. Always 200 — sync field shows DB status."""
    try:
        sync = get_sync_health()
    except Exception as exc:
        log.warning("health_db_error", error=str(exc))
        sync = {"status": "db_unavailable"}
    return {"status": "ok", "sync": sync}
