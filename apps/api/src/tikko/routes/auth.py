"""Auth: register, login, /auth/me."""

from __future__ import annotations

import pyotp
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from tikko.auth import (
    CurrentUserDep,
    hash_password,
    issue_access_token,
    issue_refresh_token,
    verify_password,
)
from tikko.db import SessionDep
from tikko.models.employee import Employee
from tikko.models.user import User
from tikko.models.user_totp import UserTOTP
from tikko.schemas.employee import EmployeeRead
from tikko.schemas.user import (
    AuthMeResponse,
    LoginPayload,
    TokenResponse,
    UserCreate,
    UserRead,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, session: SessionDep) -> User:
    existing = await session.scalar(select(User).where(User.email == payload.email))
    if existing is not None:
        raise HTTPException(status_code=409, detail="email already registered")

    employee_id: str | None = None
    if payload.employee_code is not None:
        employee = await session.scalar(
            select(Employee).where(Employee.employee_code == payload.employee_code)
        )
        if employee is None:
            raise HTTPException(
                status_code=404,
                detail=f"employee_code {payload.employee_code!r} not found",
            )
        employee_id = employee.id

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
        employee_id=employee_id,
    )
    session.add(user)
    await session.flush()
    return user


@router.get("/me", response_model=AuthMeResponse)
async def get_me(
    session: SessionDep,
    current: CurrentUserDep,
) -> AuthMeResponse:
    user = await session.get(User, current.id)
    if user is None:
        # JWT was valid but the row vanished — treat as unauthenticated.
        raise HTTPException(status_code=401, detail="user no longer exists")

    employee_payload: EmployeeRead | None = None
    if user.employee_id is not None:
        employee = await session.get(Employee, user.employee_id)
        if employee is not None:
            employee_payload = EmployeeRead.model_validate(employee)

    return AuthMeResponse(
        user=UserRead.model_validate(user),
        employee=employee_payload,
    )


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginPayload, session: SessionDep) -> TokenResponse:
    user = await session.scalar(select(User).where(User.email == payload.email))
    if user is None or not verify_password(payload.password, user.password_hash):
        # One error message for both branches — don't leak which side failed.
        raise HTTPException(status_code=401, detail="invalid credentials")

    # Admin accounts gate on TOTP if enrolled + enabled. Non-admins can enrol
    # but their login isn't blocked (per the F30 description: "TOTP for admin role").
    if user.role == "admin":
        totp = await session.get(UserTOTP, user.id)
        if totp is not None and totp.enabled:
            if payload.totp_code is None:
                raise HTTPException(status_code=401, detail="totp_required")
            # Same 1-step drift window as /auth/totp/verify keeps the door open
            # when the client clock is slightly off.
            if not pyotp.TOTP(totp.secret_b32).verify(
                payload.totp_code, valid_window=1
            ):
                raise HTTPException(status_code=401, detail="invalid totp code")

    return TokenResponse(
        access_token=issue_access_token(user.id, user.role),
        refresh_token=issue_refresh_token(user.id, user.role),
    )
