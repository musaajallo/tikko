"""role_permissions

Revision ID: a64e1b05083a
Revises: 15745463cdad
Create Date: 2026-05-15 02:30:45.970360

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a64e1b05083a'
down_revision: str | Sequence[str] | None = '15745463cdad'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'role_permissions',
        sa.Column('role', sa.String(length=32), nullable=False),
        sa.Column('capability', sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint('role', 'capability'),
    )

    # Seed the default matrix. Inlined as a literal here so this migration
    # stays reproducible — even if tikko.permissions.DEFAULT_MATRIX changes
    # later, this revision represents the system at the moment of adoption.
    seed = [
        # admin gets everything
        ("admin", c)
        for c in (
            "view_devices",
            "manage_devices",
            "poll_devices",
            "view_employees",
            "manage_employees",
            "sync_employees",
            "manage_employee_templates",
            "view_team_leave",
            "decide_leave",
            "view_shift_rules",
            "manage_shift_rules",
            "view_reports",
            "export_reports",
            "manage_users",
            "manage_permissions",
        )
    ] + [
        ("manager", c)
        for c in (
            "view_devices",
            "poll_devices",
            "view_employees",
            "view_team_leave",
            "decide_leave",
            "view_shift_rules",
            "view_reports",
            "export_reports",
        )
    ]
    # employee gets nothing in the matrix; first-person /me/* routes don't
    # check capabilities (they check user.role + linked employee separately).

    role_perms = sa.table(
        "role_permissions",
        sa.column("role", sa.String),
        sa.column("capability", sa.String),
    )
    op.bulk_insert(
        role_perms,
        [{"role": r, "capability": c} for r, c in seed],
    )


def downgrade() -> None:
    op.drop_table('role_permissions')
