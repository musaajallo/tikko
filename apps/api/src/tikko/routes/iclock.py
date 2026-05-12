"""ADMS push-protocol endpoints (/iclock/*).

These are unauthenticated by design — ZKTeco devices use SN identity, not
HTTP auth. In a hostile network you'd front this with an allowlist or a
shared secret on the path. (TODO when the deploy-mode work lands in F31.)
"""

from __future__ import annotations

from fastapi import APIRouter, Query, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from tikko.adms import parse_attlog
from tikko.db import SessionDep
from tikko.models.attendance import AttendanceLog
from tikko.models.device import Device

router = APIRouter(prefix="/iclock", tags=["iclock"])


async def _resolve_or_register_device(session: SessionDep, serial: str) -> Device:
    """Look up a device by serial_number; stub-create one if unknown."""
    device = await session.scalar(select(Device).where(Device.serial_number == serial))
    if device is not None:
        return device
    device = Device(
        name=f"Pending {serial}",
        host=f"push:{serial}",
        port=80,
        serial_number=serial,
    )
    session.add(device)
    await session.flush()
    return device


@router.get("/cdata", response_class=PlainTextResponse)
async def cdata_handshake(
    session: SessionDep,
    SN: str = Query(..., min_length=1),
) -> str:
    """Initial handshake. Device asks for its config; we register it if new
    and answer with a baseline server-options block."""
    device = await _resolve_or_register_device(session, SN)
    # Standard ADMS response. Stamps are bookkeeping markers the device echoes
    # back on subsequent uploads — using "0" tells it to send everything.
    return "\n".join(
        [
            f"GET OPTION FROM: {device.serial_number}",
            "ATTLOGStamp=0",
            "OPERLOGStamp=0",
            "PhotoStamp=0",
            "ErrorDelay=30",
            "Delay=10",
            "TransTimes=00:00;14:00",
            "TransInterval=1",
            "TransFlag=TransData AttLog OpLog",
            "TimeZone=0",
            "Realtime=1",
            "Encrypt=None",
        ]
    )


@router.post("/cdata", response_class=PlainTextResponse)
async def cdata_upload(
    request: Request,
    session: SessionDep,
    SN: str = Query(..., min_length=1),
    table: str = Query("ATTLOG"),
) -> str:
    body_bytes = await request.body()
    body = body_bytes.decode("utf-8", errors="replace")
    device = await _resolve_or_register_device(session, SN)

    if table.upper() != "ATTLOG":
        # We don't model operator logs / fingerprint uploads yet — ack so the
        # device clears its buffer, but no-op on the data.
        return "OK"

    punches = parse_attlog(body)
    if not punches:
        return "OK: 0"

    rows = [
        {
            "device_id": device.id,
            "device_user_id": p.user_id,
            "punched_at": p.timestamp,
            "punch_type": p.status,
            "verify_mode": p.verify,
        }
        for p in punches
    ]
    stmt = sqlite_insert(AttendanceLog).values(rows)
    stmt = stmt.on_conflict_do_nothing(
        index_elements=["device_id", "device_user_id", "punched_at"]
    )
    result = await session.execute(stmt)
    await session.flush()
    inserted = result.rowcount or 0
    return f"OK: {inserted}"


@router.get("/getrequest", response_class=PlainTextResponse)
async def get_request(
    SN: str = Query(..., min_length=1),
) -> str:
    """Devices long-poll this endpoint for queued commands. We have no
    command queue yet — always respond OK."""
    _ = SN  # acknowledged
    return "OK"
