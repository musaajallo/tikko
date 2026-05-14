"""Employee request/response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

EmployeeStatus = Literal["active", "inactive", "terminated"]

# Constraining to digits keeps `employee_code` interchangeable with the ZK
# device-side `uid` (a small int), so F20-sync can pass `int(employee_code)`
# directly to `pyzk.set_user(uid=…, user_id=…)` without a separate mapping.
_CODE_PATTERN = r"^\d+$"


class EmployeeCreate(BaseModel):
    employee_code: str = Field(..., min_length=1, max_length=32, pattern=_CODE_PATTERN)
    full_name: str = Field(..., min_length=1, max_length=255)
    status: EmployeeStatus = "active"


class EmployeeUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    status: EmployeeStatus | None = None


class EmployeeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    employee_code: str
    full_name: str
    status: EmployeeStatus
    created_at: datetime
    updated_at: datetime


class EmployeeList(BaseModel):
    items: list[EmployeeRead]
    total: int


class EmployeeSyncRequest(BaseModel):
    device_ids: list[str] = Field(..., min_length=1)


class EmployeeSyncEntry(BaseModel):
    device_id: str
    status: Literal["synced", "failed"]
    error: str | None = None


class EmployeeSyncResult(BaseModel):
    results: list[EmployeeSyncEntry]


class TemplateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    employee_id: str
    source_device_id: str
    finger_id: int
    captured_at: datetime


class TemplateList(BaseModel):
    items: list[TemplateRead]
    total: int


class TemplatePullResult(BaseModel):
    stored: int
    fingers: list[int]


class TemplatePushRequest(BaseModel):
    device_ids: list[str] = Field(..., min_length=1)


class TemplatePushEntry(BaseModel):
    device_id: str
    status: Literal["pushed", "failed"]
    fingers_pushed: int = 0
    error: str | None = None


class TemplatePushResult(BaseModel):
    results: list[TemplatePushEntry]
