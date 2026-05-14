"""Per-user TOTP secret. One row per User; FK uniqueness keeps it 1:1."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from tikko.db import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class UserTOTP(Base):
    __tablename__ = "user_totp"

    # 1:1 with users — using the FK as the PK keeps "one TOTP record per user"
    # enforced at the schema level without a separate unique constraint.
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), primary_key=True
    )
    # Base32 secret used by `pyotp.TOTP(secret)`. Stored plaintext for MVP;
    # encryption-at-rest is a follow-up (depends on a KMS / wrapper key story).
    secret_b32: Mapped[str] = mapped_column(String(64), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
