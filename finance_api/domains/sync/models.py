"""Sync run tracking model."""

import uuid
from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class SyncRun(SQLModel, table=True):
    """Tracks status and details of a single Monobank sync run."""

    __tablename__ = "sync_runs"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    status: str  # running | completed | failed
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    tx_imported: int = 0
    error: str | None = None
