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
    # Required only when the user is an admin with TOTP enabled. Six digits.
    totp_code: str | None = Field(default=None, pattern=r"^\d{6}$")


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=10, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"


class AuthMeResponse(BaseModel):
    """`GET /auth/me` returns the current user plus the linked Employee (or null)."""

    user: UserRead
    employee: EmployeeRead | None = None
