"""Shift rule schemas."""

from __future__ import annotations

from datetime import datetime, time

from pydantic import BaseModel, ConfigDict, Field, model_validator

_WORK_DAYS_PATTERN = r"^[01]{7}$"


class ShiftRuleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    start_time: time
    end_time: time
    late_grace_minutes: int = Field(0, ge=0, le=240)
    early_out_grace_minutes: int = Field(0, ge=0, le=240)
    overtime_threshold_minutes: int = Field(30, ge=0, le=600)
    # 7-char binary string indexed Mon..Sun. "1111100" = Mon-Fri.
    work_days: str = Field("1111100", pattern=_WORK_DAYS_PATTERN)

    @model_validator(mode="after")
    def _start_not_equal_end(self) -> ShiftRuleCreate:
        # F39: allow start_time > end_time to mean an overnight shift. Only
        # equality is meaningless (zero-length window) and gets rejected.
        if self.start_time == self.end_time:
            raise ValueError("start_time and end_time cannot be equal")
        return self


class ShiftRuleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    start_time: time | None = None
    end_time: time | None = None
    late_grace_minutes: int | None = Field(default=None, ge=0, le=240)
    early_out_grace_minutes: int | None = Field(default=None, ge=0, le=240)
    overtime_threshold_minutes: int | None = Field(default=None, ge=0, le=600)
    work_days: str | None = Field(default=None, pattern=_WORK_DAYS_PATTERN)


class ShiftRuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    start_time: time
    end_time: time
    late_grace_minutes: int
    early_out_grace_minutes: int
    overtime_threshold_minutes: int
    work_days: str
    created_at: datetime
    updated_at: datetime


class ShiftRuleList(BaseModel):
    items: list[ShiftRuleRead]
    total: int
