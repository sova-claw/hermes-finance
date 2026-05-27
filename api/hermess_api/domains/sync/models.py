import uuid
from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class SyncRun(SQLModel, table=True):
    __tablename__ = "sync_runs"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    status: str  # running | completed | failed
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    tx_imported: int = 0
    error: Optional[str] = None
