"""Auth: register and login."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from tikko.auth import (
    hash_password,
    issue_access_token,
    issue_refresh_token,
    verify_password,
)
from tikko.db import SessionDep
from tikko.models.user import User
from tikko.schemas.user import LoginPayload, TokenResponse, UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, session: SessionDep) -> User:
    existing = await session.scalar(select(User).where(User.email == payload.email))
    if existing is not None:
        raise HTTPException(status_code=409, detail="email already registered")

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    session.add(user)
    await session.flush()
    return user


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginPayload, session: SessionDep) -> TokenResponse:
    user = await session.scalar(select(User).where(User.email == payload.email))
    if user is None or not verify_password(payload.password, user.password_hash):
        # One error message for both branches — don't leak which side failed.
        raise HTTPException(status_code=401, detail="invalid credentials")

    return TokenResponse(
        access_token=issue_access_token(user.id, user.role),
        refresh_token=issue_refresh_token(user.id, user.role),
    )
