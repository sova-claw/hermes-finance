"""Sync control endpoints."""

import threading

from fastapi import APIRouter

from finance_api.domains.insights.queries import get_sync_health
from finance_api.domains.sync.monobank import run_sync
from finance_api.schemas import SyncStatus, SyncTriggered

router = APIRouter()


@router.post(
    "",
    response_model=SyncTriggered,
    summary="Trigger Monobank sync",
    description=(
        "Starts a full Monobank sync in the background and returns immediately. "
        "If a sync is already running, the new request is ignored (the lock in "
        "`run_sync` handles deduplication). Poll `GET /sync/status` to track "
        "progress."
    ),
)
def trigger_sync() -> dict[str, str]:
    """Trigger a Monobank sync in the background."""
    threading.Thread(target=run_sync, daemon=True).start()
    return {"status": "started"}


@router.get(
    "/status",
    response_model=SyncStatus,
    summary="Last sync status",
    description=(
        "Returns the status of the most recent sync run. "
        "Returns `status: never_synced` with zero/null fields if no sync has run yet."
    ),
)
def sync_status() -> SyncStatus:
    """Return the status of the last sync run."""
    return SyncStatus(**get_sync_health())
