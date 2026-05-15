"""Schemas for the permissions endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field

from tikko.permissions import Capability, Role


class PermissionsMatrix(BaseModel):
    """`role` → list of granted capabilities."""

    matrix: dict[Role, list[Capability]]
    # The canonical list of capabilities + roles, so the frontend can render
    # every cell of the table even when a role has zero grants.
    all_roles: list[Role]
    all_capabilities: list[Capability]


class PermissionGrantPatch(BaseModel):
    role: Role
    capability: Capability
    granted: bool = Field(..., description="true → grant; false → revoke")
