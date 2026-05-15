"""leave_types + leave_balances + leave_requests.leave_type_id + seed caps

Revision ID: ca280c92f92f
Revises: b81568a7036b
Create Date: 2026-05-15
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'ca280c92f92f'
down_revision: str | Sequence[str] | None = 'b81568a7036b'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'leave_types',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('days_per_year', sa.Integer(), nullable=False),
        sa.Column('color', sa.String(length=16), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uq_leave_types_name'),
    )
    op.create_index(
        op.f('ix_leave_types_name'), 'leave_types', ['name'], unique=False
    )

    op.create_table(
        'leave_balances',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('employee_id', sa.String(length=36), nullable=False),
        sa.Column('leave_type_id', sa.String(length=36), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('allocated_days', sa.Integer(), nullable=False),
        sa.Column('used_days', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ['employee_id'], ['employees.id'],
            name='fk_leave_balances_employee_id',
        ),
        sa.ForeignKeyConstraint(
            ['leave_type_id'], ['leave_types.id'],
            name='fk_leave_balances_leave_type_id',
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'employee_id', 'leave_type_id', 'year',
            name='uq_leave_balances_employee_type_year',
        ),
    )
    op.create_index(
        op.f('ix_leave_balances_employee_id'),
        'leave_balances',
        ['employee_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_leave_balances_leave_type_id'),
        'leave_balances',
        ['leave_type_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_leave_balances_year'), 'leave_balances', ['year'], unique=False
    )

    with op.batch_alter_table('leave_requests', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('leave_type_id', sa.String(length=36), nullable=True)
        )
        batch_op.create_index(
            batch_op.f('ix_leave_requests_leave_type_id'),
            ['leave_type_id'],
            unique=False,
        )
        batch_op.create_foreign_key(
            'fk_leave_requests_leave_type_id',
            'leave_types',
            ['leave_type_id'],
            ['id'],
        )

    role_perms = sa.table(
        "role_permissions",
        sa.column("role", sa.String),
        sa.column("capability", sa.String),
    )
    op.bulk_insert(
        role_perms,
        [
            {"role": "admin", "capability": "view_leave_types"},
            {"role": "admin", "capability": "manage_leave_types"},
            {"role": "admin", "capability": "view_leave_balances"},
            {"role": "admin", "capability": "manage_leave_balances"},
            {"role": "manager", "capability": "view_leave_types"},
            {"role": "manager", "capability": "view_leave_balances"},
        ],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        "DELETE FROM role_permissions WHERE capability IN ("
        "'view_leave_types','manage_leave_types',"
        "'view_leave_balances','manage_leave_balances')"
    )
    with op.batch_alter_table('leave_requests', schema=None) as batch_op:
        batch_op.drop_constraint(
            'fk_leave_requests_leave_type_id', type_='foreignkey'
        )
        batch_op.drop_index(batch_op.f('ix_leave_requests_leave_type_id'))
        batch_op.drop_column('leave_type_id')

    op.drop_index(op.f('ix_leave_balances_year'), table_name='leave_balances')
    op.drop_index(
        op.f('ix_leave_balances_leave_type_id'), table_name='leave_balances'
    )
    op.drop_index(
        op.f('ix_leave_balances_employee_id'), table_name='leave_balances'
    )
    op.drop_table('leave_balances')

    op.drop_index(op.f('ix_leave_types_name'), table_name='leave_types')
    op.drop_table('leave_types')
