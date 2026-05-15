"""Capability constants + the default role→capability matrix.

The full list of capabilities is closed — it's a `Literal` type so a typo at a
route guard fails typecheck instead of silently never matching. The default
matrix is what migrations seed and what the system falls back to if a
`role_permissions` row is missing.

Mutating the matrix at runtime: see `PATCH /permissions` + the
`role_permissions` table. The route guards always consult the DB, so toggles
take effect on the next request.
"""

from __future__ import annotations

from typing import Final, Literal, cast, get_args

Capability = Literal[
    # Devices
    "view_devices",
    "manage_devices",
    "poll_devices",
    # Employees
    "view_employees",
    "manage_employees",
    "sync_employees",
    "manage_employee_templates",
    # Departments (F33)
    "view_departments",
    "manage_departments",
    # Holidays (F35)
    "view_holidays",
    "manage_holidays",
    # Attendance corrections (F38)
    "manage_attendance",
    # Leave types + balances (F37)
    "view_leave_types",
    "manage_leave_types",
    "view_leave_balances",
    "manage_leave_balances",
    # Leave (third-person manager view)
    "view_team_leave",
    "decide_leave",
    # Shift rules
    "view_shift_rules",
    "manage_shift_rules",
    # Reports
    "view_reports",
    "export_reports",
    # Users + permissions
    "manage_users",
    "manage_permissions",
    # Audit log (F34)
    "view_audit_log",
]

ALL_CAPABILITIES: Final[tuple[Capability, ...]] = cast(
    tuple[Capability, ...], get_args(Capability)
)

Role = Literal["admin", "manager", "employee"]
ALL_ROLES: Final[tuple[Role, ...]] = cast(tuple[Role, ...], get_args(Role))


# Default grants, used by the seed migration. Source of truth for "what each
# role can do out of the box" — when this changes, generate a new migration
# that diffs the matrix.
DEFAULT_MATRIX: Final[dict[Role, frozenset[Capability]]] = {
    "admin": frozenset(ALL_CAPABILITIES),
    "manager": frozenset(
        {
            "view_devices",
            "poll_devices",
            "view_employees",
            "view_departments",
            "view_holidays",
            "manage_attendance",
            "view_leave_types",
            "view_leave_balances",
            "view_team_leave",
            "decide_leave",
            "view_shift_rules",
            "view_reports",
            "export_reports",
        }
    ),
    "employee": frozenset(),
}
