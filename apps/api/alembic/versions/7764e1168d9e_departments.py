"""departments + employee.department_id + seed dept capabilities

Revision ID: 7764e1168d9e
Revises: a64e1b05083a
Create Date: 2026-05-15
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '7764e1168d9e'
down_revision: str | Sequence[str] | None = 'a64e1b05083a'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'departments',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('parent_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ['parent_id'], ['departments.id'], name='fk_departments_parent_id'
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_departments_parent_id'), 'departments', ['parent_id'], unique=False
    )

    # employees.department_id (nullable FK)
    with op.batch_alter_table('employees', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('department_id', sa.String(length=36), nullable=True)
        )
        batch_op.create_index(
            batch_op.f('ix_employees_department_id'),
            ['department_id'],
            unique=False,
        )
        # SQLite batch mode needs a named FK constraint (see F26 done.md note).
        batch_op.create_foreign_key(
            'fk_employees_department_id',
            'departments',
            ['department_id'],
            ['id'],
        )

    # Seed the new capabilities into role_permissions. Admin gets both, manager
    # gets the view side. Inlined as literals so this revision stays
    # reproducible even if DEFAULT_MATRIX changes later.
    role_perms = sa.table(
        "role_permissions",
        sa.column("role", sa.String),
        sa.column("capability", sa.String),
    )
    op.bulk_insert(
        role_perms,
        [
            {"role": "admin", "capability": "view_departments"},
            {"role": "admin", "capability": "manage_departments"},
            {"role": "manager", "capability": "view_departments"},
        ],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        "DELETE FROM role_permissions "
        "WHERE capability IN ('view_departments', 'manage_departments')"
    )
    with op.batch_alter_table('employees', schema=None) as batch_op:
        batch_op.drop_constraint('fk_employees_department_id', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_employees_department_id'))
        batch_op.drop_column('department_id')

    op.drop_index(op.f('ix_departments_parent_id'), table_name='departments')
    op.drop_table('departments')
