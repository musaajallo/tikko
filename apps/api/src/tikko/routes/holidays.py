"""Holidays: CRUD with date-uniqueness + audit hooks.

Holidays feed F35's payroll engine integration — `reports.py` loads the set
of dates that fall inside the reported month and hands them to `compute_month`
so late/early/absent are skipped on those days.
"""

from __future__ import annotations

from datetime import date as date_t

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from tikko.audit import log_audit
from tikko.auth import CurrentUserDep, require_capability
from tikko.db import SessionDep
from tikko.models.holiday import Holiday
from tikko.schemas.holiday import (
    HolidayCreate,
    HolidayList,
    HolidayRead,
    HolidayUpdate,
)

router = APIRouter(prefix="/holidays", tags=["holidays"])

_manage_holidays = require_capability("manage_holidays")
_view_holidays = require_capability("view_holidays")


def _snapshot(holiday: Holiday) -> dict[str, object]:
    return {
        "id": holiday.id,
        "date": holiday.date.isoformat(),
        "name": holiday.name,
    }


@router.post(
    "",
    response_model=HolidayRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[_manage_holidays],
)
async def create_holiday(
    payload: HolidayCreate, session: SessionDep, current: CurrentUserDep
) -> Holiday:
    holiday = Holiday(date=payload.date, name=payload.name)
    session.add(holiday)
    try:
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"a holiday already exists on {payload.date.isoformat()}",
        ) from exc
    await log_audit(
        session,
        actor=current,
        action="create_holiday",
        resource_type="holiday",
        resource_id=holiday.id,
        after=_snapshot(holiday),
    )
    return holiday


@router.get("", response_model=HolidayList, dependencies=[_view_holidays])
async def list_holidays(
    session: SessionDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(200, ge=1, le=1000),
    year: int | None = Query(default=None, description="Filter to a calendar year"),
) -> HolidayList:
    stmt = select(Holiday)
    count_stmt = select(func.count()).select_from(Holiday)
    if year is not None:
        start = date_t(year, 1, 1)
        end = date_t(year + 1, 1, 1)
        stmt = stmt.where(Holiday.date >= start, Holiday.date < end)
        count_stmt = count_stmt.where(Holiday.date >= start, Holiday.date < end)

    offset = (page - 1) * page_size
    items = (
        await session.execute(
            stmt.order_by(Holiday.date).offset(offset).limit(page_size)
        )
    ).scalars().all()
    total = await session.scalar(count_stmt)
    return HolidayList(
        items=[HolidayRead.model_validate(h) for h in items],
        total=total or 0,
    )


@router.patch(
    "/{holiday_id}",
    response_model=HolidayRead,
    dependencies=[_manage_holidays],
)
async def update_holiday(
    holiday_id: str,
    payload: HolidayUpdate,
    session: SessionDep,
    current: CurrentUserDep,
) -> Holiday:
    holiday = await session.get(Holiday, holiday_id)
    if holiday is None:
        raise HTTPException(status_code=404, detail="holiday not found")

    before = _snapshot(holiday)
    if payload.date is not None:
        holiday.date = payload.date
    if payload.name is not None:
        holiday.name = payload.name

    try:
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="another holiday is already on that date",
        ) from exc

    after = _snapshot(holiday)
    if before != after:
        await log_audit(
            session,
            actor=current,
            action="update_holiday",
            resource_type="holiday",
            resource_id=holiday.id,
            before=before,
            after=after,
        )
    return holiday


@router.delete(
    "/{holiday_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[_manage_holidays],
)
async def delete_holiday(
    holiday_id: str, session: SessionDep, current: CurrentUserDep
) -> Response:
    holiday = await session.get(Holiday, holiday_id)
    if holiday is None:
        raise HTTPException(status_code=404, detail="holiday not found")

    before = _snapshot(holiday)
    await session.delete(holiday)
    await log_audit(
        session,
        actor=current,
        action="delete_holiday",
        resource_type="holiday",
        resource_id=holiday_id,
        before=before,
    )
    await session.flush()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
