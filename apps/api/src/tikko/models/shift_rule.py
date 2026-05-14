"""Shift rule ORM model.

One row per shift definition. Employees opt into a rule via the nullable FK on
`employees.shift_rule_id`; F27 payroll uses the rule to compute late/early/OT
per attendance day.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, time

from sqlalchemy import DateTime, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column

from tikko.db import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _new_uuid() -> str:
    return str(uuid.uuid4())


class ShiftRule(Base):
    __tablename__ = "shift_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    late_grace_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    early_out_grace_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    overtime_threshold_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=30
    )
    # 7-char binary string, indexed Mon..Sun. "1111100" = Mon-Fri.
    work_days: Mapped[str] = mapped_column(String(7), nullable=False, default="1111100")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )
