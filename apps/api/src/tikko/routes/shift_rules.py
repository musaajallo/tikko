"""Shift rules: CRUD. Per-employee assignment lives on `PATCH /employees/:id`."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select

from tikko.auth import require_role
from tikko.db import SessionDep
from tikko.models.employee import Employee
from tikko.models.shift_rule import ShiftRule
from tikko.schemas.shift_rule import (
    ShiftRuleCreate,
    ShiftRuleList,
    ShiftRuleRead,
    ShiftRuleUpdate,
)

router = APIRouter(prefix="/shift-rules", tags=["shift-rules"])

_admin_only = Depends(require_role("admin"))
_admin_or_manager = Depends(require_role("admin", "manager"))


@router.post(
    "",
    response_model=ShiftRuleRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[_admin_only],
)
async def create_shift_rule(
    payload: ShiftRuleCreate, session: SessionDep
) -> ShiftRule:
    rule = ShiftRule(**payload.model_dump())
    session.add(rule)
    await session.flush()
    return rule


@router.get("", response_model=ShiftRuleList, dependencies=[_admin_or_manager])
async def list_shift_rules(
    session: SessionDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
) -> ShiftRuleList:
    offset = (page - 1) * page_size
    items = (
        await session.execute(
            select(ShiftRule)
            .order_by(ShiftRule.created_at)
            .offset(offset)
            .limit(page_size)
        )
    ).scalars().all()
    total = await session.scalar(select(func.count()).select_from(ShiftRule))
    return ShiftRuleList(
        items=[ShiftRuleRead.model_validate(item) for item in items],
        total=total or 0,
    )


@router.get(
    "/{rule_id}", response_model=ShiftRuleRead, dependencies=[_admin_or_manager]
)
async def get_shift_rule(rule_id: str, session: SessionDep) -> ShiftRule:
    rule = await session.get(ShiftRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="shift rule not found")
    return rule


@router.patch(
    "/{rule_id}", response_model=ShiftRuleRead, dependencies=[_admin_only]
)
async def update_shift_rule(
    rule_id: str, payload: ShiftRuleUpdate, session: SessionDep
) -> ShiftRule:
    rule = await session.get(ShiftRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="shift rule not found")

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(rule, key, value)

    # Re-validate start<end on the merged state. The Pydantic Update model
    # can't enforce this cross-field rule by itself because either side can be
    # absent.
    if rule.start_time >= rule.end_time:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start_time must be before end_time",
        )

    await session.flush()
    return rule


@router.delete(
    "/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[_admin_only],
)
async def delete_shift_rule(rule_id: str, session: SessionDep) -> Response:
    rule = await session.get(ShiftRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="shift rule not found")

    # Refuse to delete a rule that's still in use. The operator must re-assign
    # affected employees first — ON DELETE SET NULL would silently break
    # assignments without warning.
    assigned_count = await session.scalar(
        select(func.count())
        .select_from(Employee)
        .where(Employee.shift_rule_id == rule_id)
    )
    if assigned_count:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{assigned_count} employee(s) still assigned to this shift rule",
        )

    await session.delete(rule)
    await session.flush()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
