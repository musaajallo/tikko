"""TOTP enrollment + verification + disable (admin login enforcement is in `routes/auth.py`)."""

from __future__ import annotations

import pyotp
from fastapi import APIRouter, HTTPException, Response, status

from tikko.auth import CurrentUserDep, verify_password
from tikko.db import SessionDep
from tikko.models.user import User
from tikko.models.user_totp import UserTOTP
from tikko.schemas.totp import (
    TOTPDisableRequest,
    TOTPEnrollResponse,
    TOTPVerifyRequest,
    TOTPVerifyResponse,
)

router = APIRouter(prefix="/auth/totp", tags=["auth"])

_ISSUER = "tikko"


@router.post("/enroll", response_model=TOTPEnrollResponse)
async def enroll_totp(
    session: SessionDep, current: CurrentUserDep
) -> TOTPEnrollResponse:
    user = await session.get(User, current.id)
    if user is None:
        # JWT outlived the row — same as the /auth/me edge case.
        raise HTTPException(status_code=401, detail="user no longer exists")

    existing = await session.get(UserTOTP, current.id)
    if existing is None:
        # Fresh secret, not yet enabled.
        secret = pyotp.random_base32()
        record = UserTOTP(user_id=current.id, secret_b32=secret, enabled=False)
        session.add(record)
        await session.flush()
    elif not existing.enabled:
        # Re-enrolling before verifying — rotate the secret so the old QR is dead.
        existing.secret_b32 = pyotp.random_base32()
        await session.flush()
        record = existing
    else:
        # Already enabled — refuse, force the operator through disable+re-enroll.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="TOTP already enabled; disable first before re-enrolling",
        )

    otpauth_uri = pyotp.TOTP(record.secret_b32).provisioning_uri(
        name=user.email, issuer_name=_ISSUER
    )
    return TOTPEnrollResponse(
        secret=record.secret_b32,
        otpauth_uri=otpauth_uri,
        enabled=record.enabled,
    )


@router.post("/verify", response_model=TOTPVerifyResponse)
async def verify_totp(
    payload: TOTPVerifyRequest,
    session: SessionDep,
    current: CurrentUserDep,
) -> TOTPVerifyResponse:
    record = await session.get(UserTOTP, current.id)
    if record is None:
        raise HTTPException(
            status_code=404, detail="TOTP not enrolled — call /auth/totp/enroll first"
        )

    # `valid_window=1` accepts the previous + next 30s step so a small clock
    # drift between server and authenticator app doesn't lock the user out.
    if not pyotp.TOTP(record.secret_b32).verify(payload.code, valid_window=1):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="invalid TOTP code",
        )

    record.enabled = True
    await session.flush()
    return TOTPVerifyResponse(enabled=True)


@router.post("/disable", status_code=status.HTTP_204_NO_CONTENT)
async def disable_totp(
    payload: TOTPDisableRequest,
    session: SessionDep,
    current: CurrentUserDep,
) -> Response:
    user = await session.get(User, current.id)
    if user is None:
        raise HTTPException(status_code=401, detail="user no longer exists")
    # Re-auth: disabling 2FA is destructive enough to demand the password again.
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="invalid password")

    record = await session.get(UserTOTP, current.id)
    if record is not None:
        await session.delete(record)
        await session.flush()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
