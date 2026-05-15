"""Capability-based route guard.

Reads the (role, capability) grants from `role_permissions` and lets the
request through iff the user's role has the capability. `require_role(...)`
is gone; every protected route now declares the capability it needs.

The DB lookup is one indexed point-query per request. If this ever shows up
in profiles we can cache per-role grants in memory and invalidate on
PATCH /permissions, but at MVP scale it's not worth the complexity.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy import select

from tikko.auth.dependencies import CurrentUserDep
from tikko.db import SessionDep
from tikko.models.role_permission import RolePermission
from tikko.permissions import Capability


def require_capability(name: Capability):
    """Factory for capability-checking dependencies.

    Use as: `dependencies=[require_capability("manage_devices")]` on routes.
    """

    async def _check(
        session: SessionDep,
        user: CurrentUserDep,
    ) -> None:
        granted = await session.scalar(
            select(RolePermission).where(
                RolePermission.role == user.role,
                RolePermission.capability == name,
            )
        )
        if granted is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"missing capability: {name}",
            )

    return Depends(_check)


async def capabilities_for_role(
    session: SessionDep, role: str
) -> list[str]:
    """Return the ordered list of capabilities granted to `role`."""
    rows = (
        await session.execute(
            select(RolePermission.capability)
            .where(RolePermission.role == role)
            .order_by(RolePermission.capability)
        )
    ).all()
    return [r[0] for r in rows]


CapabilityDep = Annotated[None, Depends(require_capability)]
