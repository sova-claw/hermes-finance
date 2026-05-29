"""fix accounts schema — add columns missing from pre-migration accounts table

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-29
"""

import sqlalchemy as sa

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

_TABLE = "accounts"


def _existing_columns(conn: sa.engine.Connection) -> set[str]:
    return {c["name"] for c in sa.inspect(conn).get_columns(_TABLE)}


def _existing_indexes(conn: sa.engine.Connection) -> set[str]:
    return {i["name"] for i in sa.inspect(conn).get_indexes(_TABLE)}


def upgrade() -> None:
    """Idempotently add columns that predate alembic tracking."""
    conn = op.get_bind()
    cols = _existing_columns(conn)
    indexes = _existing_indexes(conn)

    if "monobank_id" not in cols:
        op.add_column(_TABLE, sa.Column("monobank_id", sa.String(), nullable=True))

    if "balance" not in cols:
        op.add_column(
            _TABLE,
            sa.Column("balance", sa.Float(), nullable=False, server_default="0"),
        )

    if "synced_at" not in cols:
        op.add_column(_TABLE, sa.Column("synced_at", sa.DateTime(), nullable=True))

    if "ix_accounts_monobank_id" not in indexes:
        op.create_index("ix_accounts_monobank_id", _TABLE, ["monobank_id"], unique=True)


def downgrade() -> None:
    """No-op — column additions from a schema repair are not reverted."""
