"""GET /audit-log — admin-only paginated read of `audit_events`.

Writes happen via `tikko.audit.log_audit` inside the surrounding mutating
route's transaction, not through a dedicated endpoint — audit rows are
side-effects of real actions, never user-submitted.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from tikko.auth import require_capability
from tikko.db import SessionDep
from tikko.models.audit_event import AuditEvent
from tikko.schemas.audit import AuditEventList, AuditEventRead

router = APIRouter(prefix="/audit-log", tags=["audit"])

_view_audit_log = require_capability("view_audit_log")


@router.get("", response_model=AuditEventList, dependencies=[_view_audit_log])
async def list_audit_log(
    session: SessionDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    actor_user_id: str | None = Query(default=None),
    resource_type: str | None = Query(default=None),
    action: str | None = Query(default=None),
    since: datetime | None = Query(default=None),
    until: datetime | None = Query(default=None),
) -> AuditEventList:
    stmt = select(AuditEvent)
    count_stmt = select(func.count()).select_from(AuditEvent)
    if actor_user_id is not None:
        stmt = stmt.where(AuditEvent.actor_user_id == actor_user_id)
        count_stmt = count_stmt.where(AuditEvent.actor_user_id == actor_user_id)
    if resource_type is not None:
        stmt = stmt.where(AuditEvent.resource_type == resource_type)
        count_stmt = count_stmt.where(AuditEvent.resource_type == resource_type)
    if action is not None:
        stmt = stmt.where(AuditEvent.action == action)
        count_stmt = count_stmt.where(AuditEvent.action == action)
    if since is not None:
        stmt = stmt.where(AuditEvent.created_at >= since)
        count_stmt = count_stmt.where(AuditEvent.created_at >= since)
    if until is not None:
        stmt = stmt.where(AuditEvent.created_at < until)
        count_stmt = count_stmt.where(AuditEvent.created_at < until)

    offset = (page - 1) * page_size
    rows = (
        await session.execute(
            stmt.order_by(AuditEvent.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
    ).scalars().all()
    total = await session.scalar(count_stmt)
    return AuditEventList(
        items=[AuditEventRead.model_validate(row) for row in rows],
        total=total or 0,
    )
