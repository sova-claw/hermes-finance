"""purge accounts rows with NULL monobank_id (phantom records from schema repair)

Revision ID: 0005
Revises: 0004
Create Date: 2026-05-29
"""

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Delete accounts that have no monobank_id — they are unreachable by sync."""
    op.execute("DELETE FROM accounts WHERE monobank_id IS NULL")


def downgrade() -> None:
    """No-op — deleted rows cannot be recovered."""
