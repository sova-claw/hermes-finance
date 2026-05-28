"""Category budget SQLModel."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class CategoryBudget(SQLModel, table=True):
    """Monthly spending limit for a single category."""

    __tablename__ = "category_budgets"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    category: str = Field(unique=True, index=True)
    monthly_limit: float
    currency: str = Field(default="UAH")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
