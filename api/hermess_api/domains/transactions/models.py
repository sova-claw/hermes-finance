import uuid
from datetime import date, datetime
from typing import Any, Optional
from sqlmodel import Field, SQLModel
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB


class Transaction(SQLModel, table=True):
    __tablename__ = "transactions"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    account_id: uuid.UUID = Field(foreign_key="accounts.id", index=True)
    monobank_id: str = Field(unique=True, index=True)

    amount: float
    currency: str
    date: date
    description: str
    category: Optional[str] = None
    mcc: Optional[int] = None
    notes: Optional[str] = None
    extra: Optional[dict[str, Any]] = Field(
        default=None, sa_column=Column(JSONB)
    )

    is_pending: bool = False
    cashback_amount: float = 0.0

    created_at: datetime = Field(default_factory=datetime.utcnow)
