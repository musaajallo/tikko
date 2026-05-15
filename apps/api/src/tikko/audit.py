"""Audit log helper — single seam every mutating route calls into.

The intent is to record state-changing actions so an operator can later answer
"who did what, and when" without trawling commit history or app logs. Routes
hand in a small dict snapshot (not the whole row) so the audit trail stays
human-readable and immune to schema drift.

The helper writes to the same session as the calling route, so an audit row
is committed (or rolled back) atomically with the operation it describes —
exactly the property you want: a transactional audit trail can't lie about
work that didn't happen.
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from tikko.auth import CurrentUser
from tikko.models.audit_event import AuditEvent


def _encode(snapshot: dict[str, Any] | None) -> str | None:
    if snapshot is None:
        return None
    # default=str so datetimes/UUIDs serialise cleanly. Keys are always
    # author-controlled so a non-serialisable key shouldn't happen in practice,
    # but the fallback keeps a stray odd type from blowing up the request.
    return json.dumps(snapshot, default=str, sort_keys=True)


async def log_audit(
    session: AsyncSession,
    *,
    actor: CurrentUser | None,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
) -> None:
    """Append an AuditEvent in the current transaction.

    Args:
        session: the active session for the request.
        actor: the user who performed the action, or None for system events.
        action: a short slug, e.g. "create_employee", "update_role".
        resource_type: a short slug, e.g. "employee", "department", "user".
        resource_id: the row id of the affected resource, when applicable.
        before / after: optional snapshot dicts — leave None when not useful
            (creates have no before; deletes have no after).
    """
    session.add(
        AuditEvent(
            actor_user_id=actor.id if actor is not None else None,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            before_json=_encode(before),
            after_json=_encode(after),
        )
    )
    # Don't flush here — let the surrounding route flush once at the end so
    # the audit row participates in the same transactional boundary.
