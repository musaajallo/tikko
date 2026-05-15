"""Holiday request/response schemas."""

from __future__ import annotations

from datetime import date as date_t
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class HolidayCreate(BaseModel):
    date: date_t
    name: str = Field(..., min_length=1, max_length=120)


class HolidayUpdate(BaseModel):
    date: date_t | None = None
    name: str | None = Field(default=None, min_length=1, max_length=120)


class HolidayRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    date: date_t
    name: str
    created_at: datetime
    updated_at: datetime


class HolidayList(BaseModel):
    items: list[HolidayRead]
    total: int
