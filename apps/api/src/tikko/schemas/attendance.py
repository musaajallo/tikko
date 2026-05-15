"""Attendance log response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AttendanceLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    device_id: str | None = None
    device_user_id: str
    punched_at: datetime
    punch_type: int
    verify_mode: int
    source: str = "device"
    note: str | None = None


class AttendanceLogList(BaseModel):
    items: list[AttendanceLogRead]
    total: int


class PollResult(BaseModel):
    polled: int
    new: int


class ManualPunchRequest(BaseModel):
    employee_id: str
    punched_at: datetime
    punch_type: int = 0
    note: str | None = None
