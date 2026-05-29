"""fix accounts schema — add missing columns if table predates migration

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-29
"""

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add any columns that are missing from an old accounts table."""
    op.execute(
        "ALTER TABLE accounts ADD COLUMN IF NOT EXISTS monobank_id VARCHAR"
    )
    op.execute(
        "ALTER TABLE accounts ADD COLUMN IF NOT EXISTS balance FLOAT NOT NULL DEFAULT 0"
    )
    op.execute(
        "ALTER TABLE accounts ADD COLUMN IF NOT EXISTS synced_at TIMESTAMP"
    )
    # Ensure unique index exists
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_accounts_monobank_id"
        " ON accounts (monobank_id)"
    )


def downgrade() -> None:
    """No-op — we don't drop columns on downgrade."""
