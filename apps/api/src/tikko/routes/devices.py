"""Devices: register, list, retrieve, test-connection, poll attendance."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from tikko.db import SessionDep
from tikko.models.attendance import AttendanceLog
from tikko.models.device import Device
from tikko.schemas.attendance import AttendanceLogList, AttendanceLogRead, PollResult
from tikko.schemas.device import DeviceCreate, DeviceList, DeviceRead
from tikko.schemas.zk import DeviceInfoRead
from tikko.settings import get_settings
from tikko.zk.client import RawPunch, ZKClient, ZKConnectionError

router = APIRouter(prefix="/devices", tags=["devices"])


async def _insert_punches_dedup(
    session: AsyncSession, device_id: str, punches: list[RawPunch]
) -> int:
    """Bulk-insert punches, skipping rows that violate the unique (device, user, time) key.

    Uses the SQLite dialect's `INSERT OR IGNORE` semantics, which is also the
    natural fit for Postgres via `ON CONFLICT DO NOTHING` (kept simple for now —
    the SQLite dialect's `prefix_with` works on both via SQLAlchemy's
    `insert(...).on_conflict_do_nothing()` upgrade path in a later feature).
    """
    if not punches:
        return 0

    rows = [
        {
            "device_id": device_id,
            "device_user_id": p.user_id,
            "punched_at": p.timestamp,
            "punch_type": p.status,
            "verify_mode": p.punch,
        }
        for p in punches
    ]

    stmt = sqlite_insert(AttendanceLog).values(rows)
    stmt = stmt.on_conflict_do_nothing(
        index_elements=["device_id", "device_user_id", "punched_at"]
    )
    result = await session.execute(stmt)
    return result.rowcount or 0


@router.post("", response_model=DeviceRead, status_code=status.HTTP_201_CREATED)
async def create_device(payload: DeviceCreate, session: SessionDep) -> Device:
    device = Device(
        name=payload.name,
        host=payload.host,
        port=payload.port,
        location=payload.location,
    )
    session.add(device)
    await session.flush()
    return device


@router.get("", response_model=DeviceList)
async def list_devices(session: SessionDep) -> DeviceList:
    result = await session.execute(select(Device).order_by(Device.created_at))
    items = result.scalars().all()
    total = await session.scalar(select(func.count()).select_from(Device))
    return DeviceList(
        items=[DeviceRead.model_validate(d) for d in items],
        total=total or 0,
    )


@router.get("/{device_id}", response_model=DeviceRead)
async def get_device(device_id: str, session: SessionDep) -> Device:
    device = await session.get(Device, device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="device not found")
    return device


@router.post("/{device_id}/test-connection", response_model=DeviceInfoRead)
async def test_device_connection(device_id: str, session: SessionDep) -> DeviceInfoRead:
    device = await session.get(Device, device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="device not found")

    settings = get_settings()
    zk_client = ZKClient(
        host=device.host,
        port=device.port,
        timeout=settings.zk_connect_timeout_sec,
    )

    try:
        info = await asyncio.to_thread(zk_client.test_connection)
    except ZKConnectionError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    return DeviceInfoRead(
        serial_number=info.serial_number,
        firmware_version=info.firmware_version,
        platform=info.platform,
        device_name=info.device_name,
    )


@router.post("/{device_id}/poll", response_model=PollResult)
async def poll_device(device_id: str, session: SessionDep) -> PollResult:
    device = await session.get(Device, device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="device not found")

    settings = get_settings()
    zk_client = ZKClient(
        host=device.host,
        port=device.port,
        timeout=settings.zk_connect_timeout_sec,
    )

    try:
        punches = await asyncio.to_thread(zk_client.get_attendance)
    except ZKConnectionError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc

    new_count = await _insert_punches_dedup(session, device.id, punches)
    await session.flush()
    return PollResult(polled=len(punches), new=new_count)


@router.get("/{device_id}/attendance", response_model=AttendanceLogList)
async def list_attendance(
    device_id: str,
    session: SessionDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
) -> AttendanceLogList:
    device = await session.get(Device, device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="device not found")

    offset = (page - 1) * page_size
    stmt = (
        select(AttendanceLog)
        .where(AttendanceLog.device_id == device_id)
        .order_by(AttendanceLog.punched_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await session.execute(stmt)
    items = result.scalars().all()

    total = await session.scalar(
        select(func.count())
        .select_from(AttendanceLog)
        .where(AttendanceLog.device_id == device_id)
    )

    return AttendanceLogList(
        items=[AttendanceLogRead.model_validate(item) for item in items],
        total=total or 0,
    )
