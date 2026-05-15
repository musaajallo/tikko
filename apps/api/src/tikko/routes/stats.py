"""Aggregate stats for the dashboard cards."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import func, select

from tikko.auth import require_capability
from tikko.db import SessionDep
from tikko.models.attendance import AttendanceLog
from tikko.models.device import Device

router = APIRouter(prefix="/stats", tags=["stats"])


class Stats(BaseModel):
    devices: int
    devices_enabled: int
    devices_online: int  # polled recently (within the online_cutoff window)
    punches_today: int
    punches_24h: int


@router.get(
    "",
    response_model=Stats,
    # Stats is the device-overview KPI strip — gate on view_devices, since it
    # surfaces device counts more than anything else.
    dependencies=[require_capability("view_devices")],
)
async def get_stats(session: SessionDep) -> Stats:
    now = datetime.now(UTC)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = now - timedelta(hours=24)
    online_cutoff = now - timedelta(seconds=300)  # generous default

    total_devices = (
        await session.scalar(select(func.count()).select_from(Device))
    ) or 0
    enabled_devices = (
        await session.scalar(
            select(func.count()).select_from(Device).where(Device.enabled.is_(True))
        )
    ) or 0
    online_devices = (
        await session.scalar(
            select(func.count())
            .select_from(Device)
            .where(Device.enabled.is_(True))
            .where(Device.last_polled_at.is_not(None))
            .where(Device.last_polled_at >= online_cutoff)
        )
    ) or 0
    today = (
        await session.scalar(
            select(func.count())
            .select_from(AttendanceLog)
            .where(AttendanceLog.punched_at >= today_start)
        )
    ) or 0
    last24 = (
        await session.scalar(
            select(func.count())
            .select_from(AttendanceLog)
            .where(AttendanceLog.punched_at >= yesterday)
        )
    ) or 0

    return Stats(
        devices=total_devices,
        devices_enabled=enabled_devices,
        devices_online=online_devices,
        punches_today=today,
        punches_24h=last24,
    )
