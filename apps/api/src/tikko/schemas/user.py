"""User and auth schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from tikko.schemas.employee import EmployeeRead

UserRole = Literal["admin", "manager", "employee"]


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=10, max_length=128)
    role: UserRole = "employee"
    # Optional link to an existing Employee by its employee_code; resolved at register.
    employee_code: str | None = None


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    role: UserRole
    employee_id: str | None = None
    created_at: datetime


class LoginPayload(BaseModel):
    email: EmailStr
    password: str
    # Required when the user is an admin with TOTP enabled. Either:
    # - a 6-digit TOTP code from the authenticator app, or
    # - a 10-character recovery code (single-use).
    # The server tries TOTP first, then falls back to recovery-code lookup.
    totp_code: str | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=10, max_length=128)


class UserList(BaseModel):
    items: list[UserRead]
    total: int


class UserRoleUpdate(BaseModel):
    role: UserRole


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"


class AuthMeResponse(BaseModel):
    """`GET /auth/me` — current user + linked employee + flat capability list.

    `capabilities` is the union of every (role, capability) row in the
    `role_permissions` table for this user's role. The frontend uses it to
    gate navigation + UI affordances without hardcoding role↔capability
    mappings on the client.
    """

    user: UserRead
    employee: EmployeeRead | None = None
    capabilities: list[str] = []
