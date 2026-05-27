"""Sync control endpoints."""
import threading
from typing import Any

from fastapi import APIRouter

from finance_api.domains.insights.queries import get_sync_health
from finance_api.domains.sync.monobank import run_sync

router = APIRouter()


@router.post("")
def trigger_sync() -> dict[str, str]:
    """Trigger a Monobank sync in the background. Returns immediately."""
    threading.Thread(target=run_sync, daemon=True).start()
    return {"status": "started"}


@router.get("/status")
def sync_status() -> dict[str, Any]:
    """Return the status of the last sync run."""
    return get_sync_health()
