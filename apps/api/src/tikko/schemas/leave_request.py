"""Leave request schemas."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

LeaveStatus = Literal["pending", "approved", "rejected"]


class LeaveRequestCreate(BaseModel):
    start_date: date
    end_date: date
    reason: str = Field(..., min_length=1, max_length=500)

    @model_validator(mode="after")
    def _start_before_or_equal_end(self) -> LeaveRequestCreate:
        if self.start_date > self.end_date:
            raise ValueError("start_date must be on or before end_date")
        return self


class LeaveRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    employee_id: str
    # Denormalised for the manager UI so it doesn't need a second /employees
    # round-trip to render names. Populated by the route via a LEFT JOIN; if
    # the employee row was deleted between submission and decision the fields
    # stay null.
    employee_code: str | None = None
    employee_full_name: str | None = None
    start_date: date
    end_date: date
    reason: str
    status: LeaveStatus
    created_at: datetime
    decided_at: datetime | None = None
    decided_by_user_id: str | None = None


class LeaveRequestList(BaseModel):
    items: list[LeaveRequestRead]
    total: int


class LeaveDecisionRequest(BaseModel):
    decision: Literal["approved", "rejected"]
