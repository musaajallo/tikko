"""Background poller for ZK devices.

Two pieces:

1. `devices_due_for_poll` — pure function. Given a snapshot of Device rows
   plus a clock and a default interval, returns which ones to poll right now.
   Easy to unit-test.

2. `run_poll_loop` — the actual asyncio task started on FastAPI lifespan.
   It selects enabled devices, calls the existing `_insert_punches_dedup`
   path, broadcasts new punches, and stamps `last_polled_at`. We never
   raise out of this loop — a single dead device shouldn't kill the worker.
"""

from __future__ import annotations

import asyncio
from collections.abc import Iterable, Sequence
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

import structlog
from sqlalchemy import select

from tikko.db import get_sessionmaker
from tikko.models.device import Device
from tikko.realtime import get_broadcaster
from tikko.settings import get_settings
from tikko.zk.client import RawPunch, ZKClient, ZKConnectionError

log = structlog.get_logger("scheduler")


class _DueShape(Protocol):
    id: Any
    enabled: bool
    poll_interval_sec: int | None
    last_polled_at: datetime | None


def devices_due_for_poll(
    devices: Iterable[_DueShape],
    *,
    now: datetime,
    default_interval: int,
) -> list[_DueShape]:
    due: list[_DueShape] = []
    for d in devices:
        if not d.enabled:
            continue
        if d.last_polled_at is None:
            due.append(d)
            continue
        interval = d.poll_interval_sec or default_interval
        if d.last_polled_at + timedelta(seconds=interval) <= now:
            due.append(d)
    return due


async def _poll_one(device: Device, punches: Sequence[RawPunch]) -> int:
    """Insert punches for one device, returning the number actually new."""
    from sqlalchemy.dialects.sqlite import insert as sqlite_insert

    from tikko.models.attendance import AttendanceLog

    sm = get_sessionmaker()
    async with sm() as session:
        rows = [
            {
                "device_id": device.id,
                "device_user_id": p.user_id,
                "punched_at": p.timestamp,
                "punch_type": p.status,
                "verify_mode": p.punch,
            }
            for p in punches
        ]
        new = 0
        if rows:
            stmt = sqlite_insert(AttendanceLog).values(rows)
            stmt = stmt.on_conflict_do_nothing(
                index_elements=["device_id", "device_user_id", "punched_at"]
            )
            result = await session.execute(stmt)
            new = result.rowcount or 0
        # Stamp the device so we don't re-poll for another interval.
        await session.execute(
            select(Device).where(Device.id == device.id)
        )
        device_row = await session.get(Device, device.id)
        if device_row is not None:
            device_row.last_polled_at = datetime.now(UTC)
        await session.commit()
        return new


async def _tick(default_interval: int, connect_timeout: int) -> None:
    sm = get_sessionmaker()
    async with sm() as session:
        rows = (await session.execute(select(Device))).scalars().all()

    now = datetime.now(UTC)
    due = devices_due_for_poll(rows, now=now, default_interval=default_interval)

    for device in due:
        client = ZKClient(host=device.host, port=device.port, timeout=connect_timeout)
        try:
            punches = await asyncio.to_thread(client.get_attendance)
        except ZKConnectionError as exc:
            log.warning("device_poll_failed", device_id=device.id, error=str(exc))
            # Still stamp last_polled_at so we don't hammer a dead device.
            sm2 = get_sessionmaker()
            async with sm2() as session:
                d = await session.get(Device, device.id)
                if d is not None:
                    d.last_polled_at = datetime.now(UTC)
                    await session.commit()
            continue

        try:
            new = await _poll_one(device, punches)
        except Exception as exc:
            log.exception("device_persist_failed", device_id=device.id, error=str(exc))
            continue

        if new:
            broadcaster = get_broadcaster()
            for p in punches:
                await broadcaster.publish(
                    {
                        "type": "attendance.created",
                        "device_id": device.id,
                        "device_user_id": p.user_id,
                        "punched_at": p.timestamp.isoformat(),
                        "punch_type": p.status,
                        "verify_mode": p.punch,
                    }
                )


async def run_poll_loop(tick_seconds: int = 5) -> None:
    """Run forever. Wake every `tick_seconds`, poll any overdue device."""
    settings = get_settings()
    while True:
        try:
            await _tick(
                default_interval=settings.default_poll_interval_sec,
                connect_timeout=settings.zk_connect_timeout_sec,
            )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            log.exception("scheduler_tick_failed", error=str(exc))
        await asyncio.sleep(tick_seconds)
