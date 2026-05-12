"""Schemas for ZK device protocol responses."""

from __future__ import annotations

from pydantic import BaseModel


class DeviceInfoRead(BaseModel):
    serial_number: str
    firmware_version: str
    platform: str
    device_name: str
