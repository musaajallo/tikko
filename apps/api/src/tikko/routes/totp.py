"""TOTP enrollment + verification + disable + recovery codes.

Admin login enforcement (and recovery-code redemption at login) lives in
`routes/auth.py`.
"""

from __future__ import annotations

import hashlib
import secrets

import pyotp
from fastapi import APIRouter, BackgroundTasks, HTTPException, Response, status
from sqlalchemy import delete

from tikko.auth import CurrentUserDep, verify_password
from tikko.db import SessionDep
from tikko.email import send_email, totp_toggled_email
from tikko.models.user import User
from tikko.models.user_totp import UserTOTP
from tikko.models.user_totp_recovery_code import UserTOTPRecoveryCode
from tikko.schemas.totp import (
    TOTPDisableRequest,
    TOTPEnrollResponse,
    TOTPRecoveryCodesRegenerateRequest,
    TOTPRecoveryCodesResponse,
    TOTPVerifyRequest,
    TOTPVerifyResponse,
)

router = APIRouter(prefix="/auth/totp", tags=["auth"])


_RECOVERY_CODE_COUNT = 10


def _new_recovery_code() -> str:
    """Generate one user-facing recovery code (10 lowercase hex chars)."""
    return secrets.token_hex(5)  # 5 bytes → 10 hex chars


def hash_recovery_code(plaintext: str) -> str:
    """Hash function used for both insert and lookup. Stripped + lowercased."""
    normalised = plaintext.strip().lower().replace("-", "").replace(" ", "")
    return hashlib.sha256(normalised.encode("ascii")).hexdigest()


async def _replace_recovery_codes(
    session: SessionDep, user_id: str
) -> list[str]:
    """Wipe any existing codes for the user and insert a fresh batch.

    Returns the plaintext codes — caller must hand them back to the user once
    and then never again.
    """
    await session.execute(
        delete(UserTOTPRecoveryCode).where(UserTOTPRecoveryCode.user_id == user_id)
    )
    plaintexts = [_new_recovery_code() for _ in range(_RECOVERY_CODE_COUNT)]
    for code in plaintexts:
        session.add(
            UserTOTPRecoveryCode(user_id=user_id, code_hash=hash_recovery_code(code))
        )
    await session.flush()
    return plaintexts

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
    background: BackgroundTasks,
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

    first_time = not record.enabled
    record.enabled = True
    await session.flush()

    # Generate recovery codes only on the first verify of an enrollment cycle.
    # If the user calls /verify again (idempotent OK), they don't get fresh codes.
    if first_time:
        codes = await _replace_recovery_codes(session, current.id)
        # Notify the user that 2FA is now active — important security event.
        user = await session.get(User, current.id)
        if user is not None:
            subject, html = totp_toggled_email(enabled=True)
            background.add_task(
                send_email, to=user.email, subject=subject, html=html
            )
    else:
        codes = []
    return TOTPVerifyResponse(enabled=True, recovery_codes=codes)


@router.post("/disable", status_code=status.HTTP_204_NO_CONTENT)
async def disable_totp(
    payload: TOTPDisableRequest,
    session: SessionDep,
    current: CurrentUserDep,
    background: BackgroundTasks,
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
    # Disable wipes recovery codes too — dangling codes after the TOTP is
    # gone would be confusing at best and risky at worst.
    await session.execute(
        delete(UserTOTPRecoveryCode).where(
            UserTOTPRecoveryCode.user_id == current.id
        )
    )
    await session.flush()

    subject, html = totp_toggled_email(enabled=False)
    background.add_task(send_email, to=user.email, subject=subject, html=html)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/recovery-codes/regenerate", response_model=TOTPRecoveryCodesResponse
)
async def regenerate_recovery_codes(
    payload: TOTPRecoveryCodesRegenerateRequest,
    session: SessionDep,
    current: CurrentUserDep,
) -> TOTPRecoveryCodesResponse:
    user = await session.get(User, current.id)
    if user is None:
        raise HTTPException(status_code=401, detail="user no longer exists")
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="invalid password")

    codes = await _replace_recovery_codes(session, current.id)
    return TOTPRecoveryCodesResponse(recovery_codes=codes)
