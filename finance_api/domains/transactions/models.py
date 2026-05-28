"""Transaction domain model."""

import uuid
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class Transaction(SQLModel, table=True):
    """Imported bank transaction with MCC-derived category."""

    __tablename__ = "transactions"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    account_id: uuid.UUID = Field(foreign_key="accounts.id", index=True)
    monobank_id: str = Field(unique=True, index=True)

    amount: float
    currency: str
    date: date
    description: str
    category: str | None = None
    mcc: int | None = None
    notes: str | None = None
    extra: dict[str, Any] | None = Field(default=None, sa_column=Column(JSONB))

    is_pending: bool = False
    cashback_amount: float = 0.0

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
