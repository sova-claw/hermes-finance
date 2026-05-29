"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-05-27
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def _add_missing_columns(conn: sa.engine.Connection, table: str, cols: list) -> None:
    """Add any columns that are missing from an existing table."""
    existing = {c["name"] for c in sa.inspect(conn).get_columns(table)}
    for col in cols:
        if col.name not in existing:
            op.add_column(table, col)


def upgrade() -> None:
    conn = op.get_bind()
    tables = sa.inspect(conn).get_table_names()

    if "accounts" in tables:
        # Table predates alembic — add any missing columns and exit.
        _add_missing_columns(conn, "accounts", [
            sa.Column("monobank_id", sa.String()),
            sa.Column("name", sa.String()),
            sa.Column("currency", sa.String()),
            sa.Column("account_type", sa.String()),
            sa.Column("balance", sa.Float(), server_default="0"),
            sa.Column("synced_at", sa.DateTime()),
        ])
        return

    op.create_table(
        "accounts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("monobank_id", sa.String(), nullable=False, unique=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("currency", sa.String(), nullable=False),
        sa.Column("account_type", sa.String(), nullable=False),
        sa.Column("balance", sa.Float(), nullable=False, server_default="0"),
        sa.Column("synced_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_accounts_monobank_id", "accounts", ["monobank_id"])

    op.create_table(
        "transactions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "account_id",
            sa.Uuid(),
            sa.ForeignKey("accounts.id"),
            nullable=False,
        ),
        sa.Column("monobank_id", sa.String(), nullable=False, unique=True),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=True),
        sa.Column("mcc", sa.Integer(), nullable=True),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("extra", JSONB(), nullable=True),
        sa.Column("is_pending", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("cashback_amount", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_transactions_account_id", "transactions", ["account_id"])
    op.create_index("ix_transactions_monobank_id", "transactions", ["monobank_id"])
    op.create_index("ix_transactions_date", "transactions", ["date"])

    op.create_table(
        "sync_runs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("tx_imported", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("transactions")
    op.drop_table("accounts")
    op.drop_table("sync_runs")
