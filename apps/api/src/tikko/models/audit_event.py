"""AuditEvent ORM model — append-only log of system mutations.

Each row records who did what to which resource, with optional before/after
JSON snapshots. Routes that change state call `tikko.audit.log_audit` to
append; reads go through `GET /audit-log` (admin-only).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from tikko.db import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _new_uuid() -> str:
    return str(uuid.uuid4())


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    # Nullable for system-originated events (background jobs, future ADMS
    # actions). When set, it's the user who performed the action — not the
    # subject of the action.
    actor_user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    resource_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, index=True
    )
    # JSON-encoded as text so the column type works on SQLite + Postgres alike.
    # Always rendered from a small, hand-picked snapshot — never the whole row.
    before_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    after_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, index=True
    )
