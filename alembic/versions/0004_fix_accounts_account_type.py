"""fix accounts schema — ensure all columns from 0001 schema are present

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-29
"""

import sqlalchemy as sa

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

_TABLE = "accounts"

# All columns the accounts table must have (from migration 0001)
_REQUIRED_COLUMNS: list[tuple[str, sa.types.TypeEngine, dict]] = [
    ("monobank_id", sa.String(), {}),
    ("name", sa.String(), {}),
    ("currency", sa.String(), {}),
    ("account_type", sa.String(), {}),
    ("balance", sa.Float(), {"server_default": "0", "nullable": False}),
    ("synced_at", sa.DateTime(), {"nullable": True}),
]


def upgrade() -> None:
    """Idempotently add any columns still missing from the accounts table."""
    conn = op.get_bind()
    existing = {c["name"] for c in sa.inspect(conn).get_columns(_TABLE)}
    for col_name, col_type, kwargs in _REQUIRED_COLUMNS:
        if col_name not in existing:
            op.add_column(_TABLE, sa.Column(col_name, col_type, **kwargs))


def downgrade() -> None:
    """No-op."""
