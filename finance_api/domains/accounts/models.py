"""Account domain model."""

import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel


class Account(SQLModel, table=True):
    """Synced Monobank account with current balance."""

    __tablename__ = "accounts"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    monobank_id: str = Field(unique=True, index=True)
    name: str
    currency: str
    account_type: str
    balance: float = 0.0
    synced_at: datetime | None = None
