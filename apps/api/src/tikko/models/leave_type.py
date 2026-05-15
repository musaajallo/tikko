"""LeaveType ORM model — one row per leave category (annual, sick, …).

`days_per_year` is the default allocation a new `LeaveBalance` row gets when
an employee first uses this type. Admins can override per-employee balances
via PATCH /leave-balances/:id without touching the type itself.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from tikko.db import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _new_uuid() -> str:
    return str(uuid.uuid4())


class LeaveType(Base):
    __tablename__ = "leave_types"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    name: Mapped[str] = mapped_column(
        String(120), nullable=False, unique=True, index=True
    )
    days_per_year: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Optional hex colour for UI rendering — "#3b82f6" etc. Stored as plain
    # text rather than a typed colour; validation happens at the schema layer.
    color: Mapped[str | None] = mapped_column(String(16), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )
