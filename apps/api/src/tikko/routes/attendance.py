"""Attendance corrections — admin / manager manual punch entry."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from tikko.audit import log_audit
from tikko.auth import CurrentUserDep, require_capability
from tikko.db import SessionDep
from tikko.models.attendance import AttendanceLog
from tikko.models.employee import Employee
from tikko.schemas.attendance import AttendanceLogRead, ManualPunchRequest

router = APIRouter(prefix="/attendance", tags=["attendance"])

_manage_attendance = require_capability("manage_attendance")


@router.post(
    "/manual",
    response_model=AttendanceLogRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[_manage_attendance],
)
async def create_manual_punch(
    payload: ManualPunchRequest,
    session: SessionDep,
    current: CurrentUserDep,
) -> AttendanceLog:
    """Insert a punch on behalf of an employee.

    Used to correct missed clock-ins / clock-outs without touching device
    hardware. Stored with `source="manual"` so reports can flag the row, and
    `device_id` left null so it doesn't impersonate a terminal.
    """
    employee = await session.get(Employee, payload.employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="employee not found")

    punch = AttendanceLog(
        device_id=None,
        device_user_id=employee.employee_code,
        punched_at=payload.punched_at,
        punch_type=payload.punch_type,
        verify_mode=0,
        source="manual",
        note=payload.note,
    )
    session.add(punch)
    await session.flush()

    await log_audit(
        session,
        actor=current,
        action="create_manual_punch",
        resource_type="attendance",
        resource_id=punch.id,
        after={
            "employee_id": employee.id,
            "employee_code": employee.employee_code,
            "punched_at": punch.punched_at.isoformat(),
            "punch_type": punch.punch_type,
            "note": punch.note,
        },
    )

    return punch
