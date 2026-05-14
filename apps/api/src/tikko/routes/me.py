"""`/me/*` — the logged-in user's own attendance and monthly summary.

These routes require the User to have a linked Employee (`User.employee_id`).
If they don't, the route returns 403 — admins/managers without an enrolled
identity simply don't have "own attendance" to look at.
"""

from __future__ import annotations

import calendar
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from tikko.auth import CurrentUserDep
from tikko.db import SessionDep
from tikko.models.attendance import AttendanceLog
from tikko.models.employee import Employee
from tikko.models.leave_request import LeaveRequest
from tikko.models.user import User
from tikko.schemas.attendance import AttendanceLogList, AttendanceLogRead
from tikko.schemas.leave_request import (
    LeaveRequestCreate,
    LeaveRequestList,
    LeaveRequestRead,
)
from tikko.schemas.me import AttendanceSummary

router = APIRouter(prefix="/me", tags=["me"])

_MONTH_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"


async def _linked_employee(
    session: SessionDep, current: CurrentUserDep
) -> Employee:
    """Resolve the current user's linked employee or 403 if unlinked."""
    user = await session.get(User, current.id)
    if user is None or user.employee_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="this user is not linked to an employee",
        )
    employee = await session.get(Employee, user.employee_id)
    if employee is None:
        # FK row vanished — treat as unlinked.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="this user is not linked to an employee",
        )
    return employee


@router.get("/attendance", response_model=AttendanceLogList)
async def list_my_attendance(
    session: SessionDep,
    current: CurrentUserDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
) -> AttendanceLogList:
    employee = await _linked_employee(session, current)

    offset = (page - 1) * page_size
    stmt = (
        select(AttendanceLog)
        .where(AttendanceLog.device_user_id == employee.employee_code)
        .order_by(AttendanceLog.punched_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    items = (await session.execute(stmt)).scalars().all()

    total = await session.scalar(
        select(func.count())
        .select_from(AttendanceLog)
        .where(AttendanceLog.device_user_id == employee.employee_code)
    )
    return AttendanceLogList(
        items=[AttendanceLogRead.model_validate(item) for item in items],
        total=total or 0,
    )


@router.get("/attendance/summary", response_model=AttendanceSummary)
async def my_attendance_summary(
    session: SessionDep,
    current: CurrentUserDep,
    month: str = Query(..., pattern=_MONTH_PATTERN, description="YYYY-MM"),
) -> AttendanceSummary:
    employee = await _linked_employee(session, current)

    year_str, month_str = month.split("-")
    year, month_num = int(year_str), int(month_str)
    start = datetime(year, month_num, 1, tzinfo=UTC)
    _, last_day = calendar.monthrange(year, month_num)
    # End is the first instant of the next day after the last day of the month.
    end = datetime(year, month_num, last_day, 23, 59, 59, 999_999, tzinfo=UTC)

    base = select(AttendanceLog).where(
        AttendanceLog.device_user_id == employee.employee_code,
        AttendanceLog.punched_at >= start,
        AttendanceLog.punched_at <= end,
    )
    total = (
        await session.scalar(select(func.count()).select_from(base.subquery()))
    ) or 0

    days_present = (
        await session.scalar(
            select(func.count(func.distinct(func.date(AttendanceLog.punched_at))))
            .where(
                AttendanceLog.device_user_id == employee.employee_code,
                AttendanceLog.punched_at >= start,
                AttendanceLog.punched_at <= end,
            )
        )
    ) or 0

    return AttendanceSummary(
        month=month, total_punches=total, days_present=days_present
    )


@router.post(
    "/leave-requests",
    response_model=LeaveRequestRead,
    status_code=status.HTTP_201_CREATED,
)
async def submit_leave_request(
    payload: LeaveRequestCreate,
    session: SessionDep,
    current: CurrentUserDep,
) -> LeaveRequest:
    employee = await _linked_employee(session, current)
    leave = LeaveRequest(
        employee_id=employee.id,
        start_date=payload.start_date,
        end_date=payload.end_date,
        reason=payload.reason,
        status="pending",
    )
    session.add(leave)
    await session.flush()
    return leave


@router.get("/leave-requests", response_model=LeaveRequestList)
async def list_my_leave_requests(
    session: SessionDep,
    current: CurrentUserDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
) -> LeaveRequestList:
    employee = await _linked_employee(session, current)
    offset = (page - 1) * page_size
    stmt = (
        select(LeaveRequest)
        .where(LeaveRequest.employee_id == employee.id)
        .order_by(LeaveRequest.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    items = (await session.execute(stmt)).scalars().all()
    total = (
        await session.scalar(
            select(func.count())
            .select_from(LeaveRequest)
            .where(LeaveRequest.employee_id == employee.id)
        )
    ) or 0
    return LeaveRequestList(
        items=[LeaveRequestRead.model_validate(item) for item in items],
        total=total,
    )
