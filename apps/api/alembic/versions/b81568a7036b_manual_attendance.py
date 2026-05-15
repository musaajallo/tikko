"""attendance_logs source + note columns; device_id nullable; seed manage_attendance

Revision ID: b81568a7036b
Revises: 83c2589798f3
Create Date: 2026-05-15
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'b81568a7036b'
down_revision: str | Sequence[str] | None = '83c2589798f3'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('attendance_logs', schema=None) as batch_op:
        # default at the column level so the backfill of existing rows lands
        # cleanly under the NOT NULL constraint.
        batch_op.add_column(
            sa.Column(
                'source',
                sa.String(length=16),
                nullable=False,
                server_default='device',
            )
        )
        batch_op.add_column(
            sa.Column('note', sa.String(length=255), nullable=True)
        )
        batch_op.alter_column(
            'device_id', existing_type=sa.String(length=36), nullable=True
        )

    role_perms = sa.table(
        "role_permissions",
        sa.column("role", sa.String),
        sa.column("capability", sa.String),
    )
    op.bulk_insert(
        role_perms,
        [
            {"role": "admin", "capability": "manage_attendance"},
            {"role": "manager", "capability": "manage_attendance"},
        ],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        "DELETE FROM role_permissions WHERE capability = 'manage_attendance'"
    )
    with op.batch_alter_table('attendance_logs', schema=None) as batch_op:
        batch_op.alter_column(
            'device_id', existing_type=sa.String(length=36), nullable=False
        )
        batch_op.drop_column('note')
        batch_op.drop_column('source')
