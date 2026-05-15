"""holidays table + view_holidays / manage_holidays seed

Revision ID: 83c2589798f3
Revises: fe86e36e0ac1
Create Date: 2026-05-15
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '83c2589798f3'
down_revision: str | Sequence[str] | None = 'fe86e36e0ac1'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'holidays',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('date', name='uq_holidays_date'),
    )
    op.create_index(op.f('ix_holidays_date'), 'holidays', ['date'], unique=False)

    role_perms = sa.table(
        "role_permissions",
        sa.column("role", sa.String),
        sa.column("capability", sa.String),
    )
    op.bulk_insert(
        role_perms,
        [
            {"role": "admin", "capability": "view_holidays"},
            {"role": "admin", "capability": "manage_holidays"},
            {"role": "manager", "capability": "view_holidays"},
        ],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        "DELETE FROM role_permissions "
        "WHERE capability IN ('view_holidays', 'manage_holidays')"
    )
    op.drop_index(op.f('ix_holidays_date'), table_name='holidays')
    op.drop_table('holidays')
