import uuid
from datetime import datetime, timezone
from sqlmodel import Field, SQLModel


class SyncRun(SQLModel, table=True):
    __tablename__ = "sync_runs"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    status: str  # running | completed | failed
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    tx_imported: int = 0
    error: str | None = None
