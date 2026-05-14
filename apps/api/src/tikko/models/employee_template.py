"""Fingerprint template ORM model.

One row per (employee, source device, finger). Stored per source device because
templates aren't always portable across firmware/vendor versions — keeping the
provenance lets a later push step pick the right source for a given target.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, LargeBinary, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from tikko.db import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _new_uuid() -> str:
    return str(uuid.uuid4())


class EmployeeTemplate(Base):
    __tablename__ = "employee_templates"
    __table_args__ = (
        UniqueConstraint(
            "employee_id",
            "source_device_id",
            "finger_id",
            name="uq_employee_template_triple",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    employee_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("employees.id"), nullable=False, index=True
    )
    source_device_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("devices.id"), nullable=False, index=True
    )
    finger_id: Mapped[int] = mapped_column(Integer, nullable=False)
    template_data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
