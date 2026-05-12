"""Device request/response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DeviceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    host: str = Field(..., min_length=1, max_length=255)
    port: int = Field(default=4370, ge=1, le=65535)
    location: str | None = Field(default=None, max_length=255)


class DeviceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    host: str
    port: int
    location: str | None
    created_at: datetime


class DeviceList(BaseModel):
    items: list[DeviceRead]
    total: int
