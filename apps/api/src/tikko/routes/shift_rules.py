"""Shift rules: CRUD. Per-employee assignment lives on `PATCH /employees/:id`."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import func, select

from tikko.audit import log_audit
from tikko.auth import CurrentUserDep, require_capability
from tikko.db import SessionDep
from tikko.models.employee import Employee
from tikko.models.shift_rule import ShiftRule
from tikko.schemas.shift_rule import (
    ShiftRuleCreate,
    ShiftRuleList,
    ShiftRuleRead,
    ShiftRuleUpdate,
)


def _rule_snapshot(rule: ShiftRule) -> dict[str, object | None]:
    return {
        "id": rule.id,
        "name": rule.name,
        "start_time": rule.start_time.isoformat() if rule.start_time else None,
        "end_time": rule.end_time.isoformat() if rule.end_time else None,
        "late_grace_minutes": rule.late_grace_minutes,
        "early_out_grace_minutes": rule.early_out_grace_minutes,
        "overtime_threshold_minutes": rule.overtime_threshold_minutes,
        "work_days": rule.work_days,
    }

router = APIRouter(prefix="/shift-rules", tags=["shift-rules"])

_manage_shift_rules = require_capability("manage_shift_rules")
_view_shift_rules = require_capability("view_shift_rules")


@router.post(
    "",
    response_model=ShiftRuleRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[_manage_shift_rules],
)
async def create_shift_rule(
    payload: ShiftRuleCreate, session: SessionDep, current: CurrentUserDep
) -> ShiftRule:
    rule = ShiftRule(**payload.model_dump())
    session.add(rule)
    await session.flush()
    await log_audit(
        session,
        actor=current,
        action="create_shift_rule",
        resource_type="shift_rule",
        resource_id=rule.id,
        after=_rule_snapshot(rule),
    )
    return rule


@router.get("", response_model=ShiftRuleList, dependencies=[_view_shift_rules])
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
    "/{rule_id}", response_model=ShiftRuleRead, dependencies=[_view_shift_rules]
)
async def get_shift_rule(rule_id: str, session: SessionDep) -> ShiftRule:
    rule = await session.get(ShiftRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="shift rule not found")
    return rule


@router.patch(
    "/{rule_id}", response_model=ShiftRuleRead, dependencies=[_manage_shift_rules]
)
async def update_shift_rule(
    rule_id: str,
    payload: ShiftRuleUpdate,
    session: SessionDep,
    current: CurrentUserDep,
) -> ShiftRule:
    rule = await session.get(ShiftRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="shift rule not found")

    before = _rule_snapshot(rule)
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(rule, key, value)

    # Re-validate start != end on the merged state. The Pydantic Update model
    # can't enforce this cross-field rule by itself because either side can be
    # absent. F39: equality is the only invalid pair — start > end is valid
    # (overnight shift).
    if rule.start_time == rule.end_time:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start_time and end_time cannot be equal",
        )

    await session.flush()
    await log_audit(
        session,
        actor=current,
        action="update_shift_rule",
        resource_type="shift_rule",
        resource_id=rule.id,
        before=before,
        after=_rule_snapshot(rule),
    )
    return rule


@router.delete(
    "/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[_manage_shift_rules],
)
async def delete_shift_rule(
    rule_id: str, session: SessionDep, current: CurrentUserDep
) -> Response:
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

    before = _rule_snapshot(rule)
    await session.delete(rule)
    await log_audit(
        session,
        actor=current,
        action="delete_shift_rule",
        resource_type="shift_rule",
        resource_id=rule_id,
        before=before,
    )
    await session.flush()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
