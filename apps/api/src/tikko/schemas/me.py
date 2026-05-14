"""Schemas for `/me/*` — the logged-in user's own attendance."""

from __future__ import annotations

import re

from pydantic import BaseModel, field_validator

_MONTH_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


class AttendanceMonthQuery(BaseModel):
    """A `YYYY-MM` query param wrapper, validated at the route boundary."""

    month: str

    @field_validator("month")
    @classmethod
    def _valid_month(cls, value: str) -> str:
        if not _MONTH_PATTERN.match(value):
            raise ValueError("month must be YYYY-MM")
        return value


class AttendanceSummary(BaseModel):
    month: str
    total_punches: int
    days_present: int
