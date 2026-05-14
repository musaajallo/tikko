"""`/leave-requests` — manager/admin view of pending and decided leave.

Employees submit + list-their-own under `/me/leave-requests` (see `routes/me.py`).
This module is the admin/manager side: read everyone's, approve/reject.
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select

from tikko.auth import CurrentUserDep, require_role
from tikko.db import SessionDep
from tikko.models.employee import Employee
from tikko.models.leave_request import LeaveRequest
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
) -> LeaveRequestRead:
    """Build the wire shape from a (LeaveRequest, joined employee fields) row."""
    return LeaveRequestRead(
        id=leave.id,
        employee_id=leave.employee_id,
        employee_code=employee_code,
        employee_full_name=employee_full_name,
        start_date=leave.start_date,
        end_date=leave.end_date,
        reason=leave.reason,
        status=leave.status,  # type: ignore[arg-type]
        created_at=leave.created_at,
        decided_at=leave.decided_at,
        decided_by_user_id=leave.decided_by_user_id,
    )

router = APIRouter(prefix="/leave-requests", tags=["leave-requests"])

_admin_or_manager = Depends(require_role("admin", "manager"))


@router.get("", response_model=LeaveRequestList, dependencies=[_admin_or_manager])
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
        select(LeaveRequest, Employee.employee_code, Employee.full_name)
        .outerjoin(Employee, Employee.id == LeaveRequest.employee_id)
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
        items=[_serialize_leave(leave, code, name) for leave, code, name in rows],
        total=total,
    )


@router.patch(
    "/{leave_id}/decision",
    response_model=LeaveRequestRead,
    dependencies=[_admin_or_manager],
)
async def decide_leave_request(
    leave_id: str,
    payload: LeaveDecisionRequest,
    session: SessionDep,
    current: CurrentUserDep,
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
    await session.flush()

    employee = await session.get(Employee, leave.employee_id)
    return _serialize_leave(
        leave,
        employee.employee_code if employee else None,
        employee.full_name if employee else None,
    )
