"""audit_events + seed view_audit_log

Revision ID: fe86e36e0ac1
Revises: 7764e1168d9e
Create Date: 2026-05-15
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'fe86e36e0ac1'
down_revision: str | Sequence[str] | None = '7764e1168d9e'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'audit_events',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('actor_user_id', sa.String(length=36), nullable=True),
        sa.Column('action', sa.String(length=64), nullable=False),
        sa.Column('resource_type', sa.String(length=32), nullable=False),
        sa.Column('resource_id', sa.String(length=36), nullable=True),
        sa.Column('before_json', sa.Text(), nullable=True),
        sa.Column('after_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ['actor_user_id'], ['users.id'], name='fk_audit_events_actor_user_id'
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_audit_events_actor_user_id'),
        'audit_events',
        ['actor_user_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_audit_events_action'), 'audit_events', ['action'], unique=False
    )
    op.create_index(
        op.f('ix_audit_events_resource_type'),
        'audit_events',
        ['resource_type'],
        unique=False,
    )
    op.create_index(
        op.f('ix_audit_events_resource_id'),
        'audit_events',
        ['resource_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_audit_events_created_at'),
        'audit_events',
        ['created_at'],
        unique=False,
    )

    role_perms = sa.table(
        "role_permissions",
        sa.column("role", sa.String),
        sa.column("capability", sa.String),
    )
    op.bulk_insert(
        role_perms,
        [{"role": "admin", "capability": "view_audit_log"}],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        "DELETE FROM role_permissions WHERE capability = 'view_audit_log'"
    )
    op.drop_index(op.f('ix_audit_events_created_at'), table_name='audit_events')
    op.drop_index(op.f('ix_audit_events_resource_id'), table_name='audit_events')
    op.drop_index(op.f('ix_audit_events_resource_type'), table_name='audit_events')
    op.drop_index(op.f('ix_audit_events_action'), table_name='audit_events')
    op.drop_index(op.f('ix_audit_events_actor_user_id'), table_name='audit_events')
    op.drop_table('audit_events')
