"""`/leave-requests` — manager/admin view of pending and decided leave.

Employees submit + list-their-own under `/me/leave-requests` (see `routes/me.py`).
This module is the admin/manager side: read everyone's, approve/reject.
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status
from sqlalchemy import func, select

from tikko.auth import CurrentUserDep, require_capability
from tikko.db import SessionDep
from tikko.email import leave_decided_email, send_email
from tikko.models.employee import Employee
from tikko.models.leave_balance import LeaveBalance
from tikko.models.leave_request import LeaveRequest
from tikko.models.leave_type import LeaveType
from tikko.models.user import User
from tikko.schemas.leave_request import (
    LeaveDecisionRequest,
    LeaveRequestList,
    LeaveRequestRead,
    LeaveStatus,
)


def _serialize_leave(
    leave: LeaveRequest,
    employee_code: str | None,
    employee_full_name: str | None,
    leave_type_name: str | None = None,
) -> LeaveRequestRead:
    """Build the wire shape from a (LeaveRequest, joined employee fields) row."""
    return LeaveRequestRead(
        id=leave.id,
        employee_id=leave.employee_id,
        employee_code=employee_code,
        employee_full_name=employee_full_name,
        leave_type_id=leave.leave_type_id,
        leave_type_name=leave_type_name,
        start_date=leave.start_date,
        end_date=leave.end_date,
        reason=leave.reason,
        status=leave.status,  # type: ignore[arg-type]
        created_at=leave.created_at,
        decided_at=leave.decided_at,
        decided_by_user_id=leave.decided_by_user_id,
    )

router = APIRouter(prefix="/leave-requests", tags=["leave-requests"])

_view_team_leave = require_capability("view_team_leave")
_decide_leave = require_capability("decide_leave")


@router.get("", response_model=LeaveRequestList, dependencies=[_view_team_leave])
async def list_leave_requests(
    session: SessionDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    status: LeaveStatus | None = Query(  # noqa: B008 — fastapi marker, same as other routes
        None,
        description="Filter by request status. Omit to return every request.",
    ),
) -> LeaveRequestList:
    base = (
        select(
            LeaveRequest,
            Employee.employee_code,
            Employee.full_name,
            LeaveType.name,
        )
        .outerjoin(Employee, Employee.id == LeaveRequest.employee_id)
        .outerjoin(LeaveType, LeaveType.id == LeaveRequest.leave_type_id)
    )
    count_base = select(func.count()).select_from(LeaveRequest)
    if status is not None:
        base = base.where(LeaveRequest.status == status)
        count_base = count_base.where(LeaveRequest.status == status)

    offset = (page - 1) * page_size
    rows = (
        await session.execute(
            base.order_by(LeaveRequest.created_at.desc()).offset(offset).limit(page_size)
        )
    ).all()
    total = (await session.scalar(count_base)) or 0

    return LeaveRequestList(
        items=[
            _serialize_leave(leave, code, name, type_name)
            for leave, code, name, type_name in rows
        ],
        total=total,
    )


@router.patch(
    "/{leave_id}/decision",
    response_model=LeaveRequestRead,
    dependencies=[_decide_leave],
)
async def decide_leave_request(
    leave_id: str,
    payload: LeaveDecisionRequest,
    session: SessionDep,
    current: CurrentUserDep,
    background: BackgroundTasks,
) -> LeaveRequestRead:
    leave = await session.get(LeaveRequest, leave_id)
    if leave is None:
        raise HTTPException(status_code=404, detail="leave request not found")
    if leave.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"already {leave.status}",
        )

    leave.status = payload.decision
    leave.decided_at = datetime.now(UTC)
    leave.decided_by_user_id = current.id

    # Consume balance on approve. Only when the request carries a leave_type_id —
    # legacy rows submitted before F37 don't have one and we don't infer it.
    if payload.decision == "approved" and leave.leave_type_id is not None:
        days = (leave.end_date - leave.start_date).days + 1
        year = leave.start_date.year
        balance = await session.scalar(
            select(LeaveBalance).where(
                LeaveBalance.employee_id == leave.employee_id,
                LeaveBalance.leave_type_id == leave.leave_type_id,
                LeaveBalance.year == year,
            )
        )
        if balance is None:
            # Auto-create with the type's default allocation. Operators can
            # adjust afterwards via PATCH /leave-balances/:id.
            leave_type = await session.get(LeaveType, leave.leave_type_id)
            allocated = leave_type.days_per_year if leave_type is not None else 0
            balance = LeaveBalance(
                employee_id=leave.employee_id,
                leave_type_id=leave.leave_type_id,
                year=year,
                allocated_days=allocated,
                used_days=days,
            )
            session.add(balance)
        else:
            balance.used_days += days

    await session.flush()

    employee = await session.get(Employee, leave.employee_id)

    # Notify the user who submitted the request (if their account exists +
    # they're the one linked to this employee).
    if employee is not None:
        submitter_email = await session.scalar(
            select(User.email).where(User.employee_id == employee.id)
        )
        if submitter_email:
            subject, html = leave_decided_email(
                decision=payload.decision,
                start_date=leave.start_date.isoformat(),
                end_date=leave.end_date.isoformat(),
            )
            background.add_task(
                send_email, to=submitter_email, subject=subject, html=html
            )

    leave_type_name: str | None = None
    if leave.leave_type_id is not None:
        leave_type = await session.get(LeaveType, leave.leave_type_id)
        leave_type_name = leave_type.name if leave_type else None
    return _serialize_leave(
        leave,
        employee.employee_code if employee else None,
        employee.full_name if employee else None,
        leave_type_name=leave_type_name,
    )
