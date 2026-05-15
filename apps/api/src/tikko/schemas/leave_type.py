"""Leave type + balance schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LeaveTypeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    days_per_year: int = Field(default=0, ge=0, le=365)
    color: str | None = Field(default=None, max_length=16)


class LeaveTypeUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    days_per_year: int | None = Field(default=None, ge=0, le=365)
    color: str | None = Field(default=None, max_length=16)


class LeaveTypeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    days_per_year: int
    color: str | None = None
    created_at: datetime
    updated_at: datetime


class LeaveTypeList(BaseModel):
    items: list[LeaveTypeRead]
    total: int


class LeaveBalanceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    employee_id: str
    leave_type_id: str
    year: int
    allocated_days: int
    used_days: int
    created_at: datetime
    updated_at: datetime


class LeaveBalanceList(BaseModel):
    items: list[LeaveBalanceRead]
    total: int


class LeaveBalanceUpdate(BaseModel):
    """Operator adjusts the allocation; used_days stays system-managed."""

    allocated_days: int = Field(..., ge=0, le=365)
