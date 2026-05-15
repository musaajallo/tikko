"""Department request/response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DepartmentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    parent_id: str | None = None


class DepartmentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    # Nullable on purpose: omit to keep, set to null to detach from parent.
    parent_id: str | None = None


class DepartmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    parent_id: str | None = None
    created_at: datetime
    updated_at: datetime


class DepartmentList(BaseModel):
    items: list[DepartmentRead]
    total: int
