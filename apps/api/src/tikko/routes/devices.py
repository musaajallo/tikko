"""Devices: register, list, retrieve."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from tikko.db import SessionDep
from tikko.models.device import Device
from tikko.schemas.device import DeviceCreate, DeviceList, DeviceRead

router = APIRouter(prefix="/devices", tags=["devices"])


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
