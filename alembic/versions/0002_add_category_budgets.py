"""add category_budgets table

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-28
"""

import sqlalchemy as sa

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create category_budgets table."""
    op.create_table(
        "category_budgets",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("category", sa.String(), nullable=False, unique=True),
        sa.Column("monthly_limit", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(), nullable=False, server_default="UAH"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_category_budgets_category", "category_budgets", ["category"])


def downgrade() -> None:
    """Drop category_budgets table."""
    op.drop_table("category_budgets")
