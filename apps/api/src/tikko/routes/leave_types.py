"""Leave types: CRUD with audit hooks.

Per-employee balances live under `/leave-balances`. The two are deliberately
separate URLs because their lifecycles diverge — the type catalog is a small,
mostly-static dataset; balances explode by employee × year.
"""

from __future__ import annotations

from datetime import date as date_t

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from tikko.audit import log_audit
from tikko.auth import CurrentUserDep, require_capability
from tikko.db import SessionDep
from tikko.models.employee import Employee
from tikko.models.leave_balance import LeaveBalance
from tikko.models.leave_request import LeaveRequest
from tikko.models.leave_type import LeaveType
from tikko.schemas.leave_type import (
    LeaveBalanceList,
    LeaveBalanceRead,
    LeaveBalanceUpdate,
    LeaveTypeCreate,
    LeaveTypeList,
    LeaveTypeRead,
    LeaveTypeUpdate,
)

router = APIRouter(tags=["leave-types"])

_manage_types = require_capability("manage_leave_types")
_view_types = require_capability("view_leave_types")
_manage_balances = require_capability("manage_leave_balances")
_view_balances = require_capability("view_leave_balances")


def _type_snapshot(lt: LeaveType) -> dict[str, object | None]:
    return {
        "id": lt.id,
        "name": lt.name,
        "days_per_year": lt.days_per_year,
        "color": lt.color,
    }


def _balance_snapshot(b: LeaveBalance) -> dict[str, object]:
    return {
        "id": b.id,
        "employee_id": b.employee_id,
        "leave_type_id": b.leave_type_id,
        "year": b.year,
        "allocated_days": b.allocated_days,
        "used_days": b.used_days,
    }


@router.post(
    "/leave-types",
    response_model=LeaveTypeRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[_manage_types],
)
async def create_leave_type(
    payload: LeaveTypeCreate, session: SessionDep, current: CurrentUserDep
) -> LeaveType:
    lt = LeaveType(
        name=payload.name,
        days_per_year=payload.days_per_year,
        color=payload.color,
    )
    session.add(lt)
    try:
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"leave type {payload.name!r} already exists",
        ) from exc
    await log_audit(
        session,
        actor=current,
        action="create_leave_type",
        resource_type="leave_type",
        resource_id=lt.id,
        after=_type_snapshot(lt),
    )
    return lt


@router.get(
    "/leave-types", response_model=LeaveTypeList, dependencies=[_view_types]
)
async def list_leave_types(
    session: SessionDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
) -> LeaveTypeList:
    offset = (page - 1) * page_size
    items = (
        await session.execute(
            select(LeaveType).order_by(LeaveType.name).offset(offset).limit(page_size)
        )
    ).scalars().all()
    total = await session.scalar(select(func.count()).select_from(LeaveType))
    return LeaveTypeList(
        items=[LeaveTypeRead.model_validate(item) for item in items],
        total=total or 0,
    )


@router.patch(
    "/leave-types/{type_id}",
    response_model=LeaveTypeRead,
    dependencies=[_manage_types],
)
async def update_leave_type(
    type_id: str,
    payload: LeaveTypeUpdate,
    session: SessionDep,
    current: CurrentUserDep,
) -> LeaveType:
    lt = await session.get(LeaveType, type_id)
    if lt is None:
        raise HTTPException(status_code=404, detail="leave type not found")

    before = _type_snapshot(lt)
    if payload.name is not None:
        lt.name = payload.name
    if payload.days_per_year is not None:
        lt.days_per_year = payload.days_per_year
    if "color" in payload.model_fields_set:
        lt.color = payload.color
    try:
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="another leave type already has that name",
        ) from exc

    after = _type_snapshot(lt)
    if before != after:
        await log_audit(
            session,
            actor=current,
            action="update_leave_type",
            resource_type="leave_type",
            resource_id=lt.id,
            before=before,
            after=after,
        )
    return lt


@router.delete(
    "/leave-types/{type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[_manage_types],
)
async def delete_leave_type(
    type_id: str, session: SessionDep, current: CurrentUserDep
) -> Response:
    lt = await session.get(LeaveType, type_id)
    if lt is None:
        raise HTTPException(status_code=404, detail="leave type not found")

    # Refuse to delete when in-flight requests or balances still reference the
    # type — the foreign keys would either fail at the DB or leave dangling
    # rows depending on dialect. Either way, surface it as a 409.
    requests = await session.scalar(
        select(func.count())
        .select_from(LeaveRequest)
        .where(LeaveRequest.leave_type_id == type_id)
    )
    if requests:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{requests} leave request(s) still reference this type",
        )
    balances = await session.scalar(
        select(func.count())
        .select_from(LeaveBalance)
        .where(LeaveBalance.leave_type_id == type_id)
    )
    if balances:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{balances} balance row(s) still reference this type",
        )

    before = _type_snapshot(lt)
    await session.delete(lt)
    await log_audit(
        session,
        actor=current,
        action="delete_leave_type",
        resource_type="leave_type",
        resource_id=type_id,
        before=before,
    )
    await session.flush()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Balances
# ---------------------------------------------------------------------------


@router.get(
    "/leave-balances",
    response_model=LeaveBalanceList,
    dependencies=[_view_balances],
)
async def list_leave_balances(
    session: SessionDep,
    employee_id: str | None = Query(default=None),
    year: int | None = Query(default=None),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
) -> LeaveBalanceList:
    stmt = select(LeaveBalance)
    count_stmt = select(func.count()).select_from(LeaveBalance)
    if employee_id is not None:
        stmt = stmt.where(LeaveBalance.employee_id == employee_id)
        count_stmt = count_stmt.where(LeaveBalance.employee_id == employee_id)
    if year is not None:
        stmt = stmt.where(LeaveBalance.year == year)
        count_stmt = count_stmt.where(LeaveBalance.year == year)

    offset = (page - 1) * page_size
    items = (
        await session.execute(
            stmt.order_by(LeaveBalance.year.desc(), LeaveBalance.leave_type_id)
            .offset(offset)
            .limit(page_size)
        )
    ).scalars().all()
    total = await session.scalar(count_stmt)
    return LeaveBalanceList(
        items=[LeaveBalanceRead.model_validate(b) for b in items],
        total=total or 0,
    )


@router.patch(
    "/leave-balances/{balance_id}",
    response_model=LeaveBalanceRead,
    dependencies=[_manage_balances],
)
async def update_leave_balance(
    balance_id: str,
    payload: LeaveBalanceUpdate,
    session: SessionDep,
    current: CurrentUserDep,
) -> LeaveBalance:
    """Adjust allocated_days. used_days is system-managed and not editable."""
    balance = await session.get(LeaveBalance, balance_id)
    if balance is None:
        raise HTTPException(status_code=404, detail="leave balance not found")

    before = _balance_snapshot(balance)
    balance.allocated_days = payload.allocated_days
    await session.flush()
    after = _balance_snapshot(balance)
    if before != after:
        await log_audit(
            session,
            actor=current,
            action="update_leave_balance",
            resource_type="leave_balance",
            resource_id=balance.id,
            before=before,
            after=after,
        )
    return balance


@router.post(
    "/leave-balances",
    response_model=LeaveBalanceRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[_manage_balances],
)
async def create_leave_balance(
    session: SessionDep,
    current: CurrentUserDep,
    employee_id: str = Query(...),
    leave_type_id: str = Query(...),
    year: int = Query(..., ge=2000, le=2100),
    allocated_days: int | None = Query(default=None, ge=0, le=365),
) -> LeaveBalance:
    """Explicit row create — used to grant a balance ahead of any approval.

    If `allocated_days` is omitted, the type's `days_per_year` is used as the
    default so a single click sets up a sensible starting allocation.
    """
    employee = await session.get(Employee, employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="employee not found")
    lt = await session.get(LeaveType, leave_type_id)
    if lt is None:
        raise HTTPException(status_code=404, detail="leave type not found")

    if allocated_days is None:
        allocated_days = lt.days_per_year

    balance = LeaveBalance(
        employee_id=employee_id,
        leave_type_id=leave_type_id,
        year=year,
        allocated_days=allocated_days,
        used_days=0,
    )
    session.add(balance)
    try:
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="a balance already exists for that employee / type / year",
        ) from exc
    await log_audit(
        session,
        actor=current,
        action="create_leave_balance",
        resource_type="leave_balance",
        resource_id=balance.id,
        after=_balance_snapshot(balance),
    )
    return balance
