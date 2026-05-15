"""`/permissions` — read + edit the role→capability matrix.

GET returns the full grant table plus the canonical enum lists so the
frontend can render every cell. PATCH toggles a single (role, capability)
grant. Both gated by the `manage_permissions` capability — admin-only by
default but editable like anything else.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import delete, select

from tikko.auth import require_capability
from tikko.db import SessionDep
from tikko.models.role_permission import RolePermission
from tikko.permissions import ALL_CAPABILITIES, ALL_ROLES, Role
from tikko.schemas.permission import PermissionGrantPatch, PermissionsMatrix

router = APIRouter(prefix="/permissions", tags=["permissions"])

_manage_permissions = require_capability("manage_permissions")


@router.get("", response_model=PermissionsMatrix, dependencies=[_manage_permissions])
async def get_permissions(session: SessionDep) -> PermissionsMatrix:
    rows = (
        await session.execute(
            select(RolePermission.role, RolePermission.capability).order_by(
                RolePermission.role, RolePermission.capability
            )
        )
    ).all()

    matrix: dict[Role, list[str]] = {r: [] for r in ALL_ROLES}
    for role, capability in rows:
        if role in matrix:
            matrix[role].append(capability)

    return PermissionsMatrix(
        matrix=matrix,  # type: ignore[arg-type]
        all_roles=list(ALL_ROLES),
        all_capabilities=list(ALL_CAPABILITIES),
    )


@router.patch("", status_code=status.HTTP_204_NO_CONTENT, dependencies=[_manage_permissions])
async def patch_permission(
    payload: PermissionGrantPatch, session: SessionDep
) -> None:
    # Guardrail: refuse to revoke the last grant of `manage_permissions` —
    # without at least one role that can edit the matrix, you'd lock yourself
    # out of the system permanently.
    if (
        payload.capability == "manage_permissions"
        and not payload.granted
    ):
        remaining = await session.scalar(
            select(RolePermission).where(
                RolePermission.capability == "manage_permissions",
                RolePermission.role != payload.role,
            )
        )
        if remaining is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="cannot revoke the last manage_permissions grant",
            )

    if payload.granted:
        # Idempotent: insert if missing.
        existing = await session.get(
            RolePermission, (payload.role, payload.capability)
        )
        if existing is None:
            session.add(
                RolePermission(role=payload.role, capability=payload.capability)
            )
            await session.flush()
    else:
        await session.execute(
            delete(RolePermission).where(
                RolePermission.role == payload.role,
                RolePermission.capability == payload.capability,
            )
        )
        await session.flush()
