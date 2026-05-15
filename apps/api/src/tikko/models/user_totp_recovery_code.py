"""TOTP recovery codes (F30-recovery).

One row per single-use code. Hashed with SHA-256 — bcrypt is overkill for
high-entropy tokens (10 hex chars = ~40 bits) and would make the per-row
lookup at login slow. Constant-pepper / per-row salt isn't needed because
the inputs aren't user-chosen.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from tikko.db import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _new_uuid() -> str:
    return str(uuid.uuid4())


class UserTOTPRecoveryCode(Base):
    __tablename__ = "user_totp_recovery_codes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    # SHA-256 hex digest of the (normalised) plaintext code.
    code_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
