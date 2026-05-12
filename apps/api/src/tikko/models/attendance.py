"""AttendanceLog ORM model — one row per device-reported punch."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from tikko.db import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _new_uuid() -> str:
    return str(uuid.uuid4())


class AttendanceLog(Base):
    __tablename__ = "attendance_logs"
    __table_args__ = (
        # Dedup key: a single physical punch on a device cannot be inserted twice.
        UniqueConstraint(
            "device_id", "device_user_id", "punched_at",
            name="uq_attendance_logs_device_user_time",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    device_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    device_user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    punched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    punch_type: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    verify_mode: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
