"""Audit log response schemas."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator


def _decode_json(value: Any) -> Any:
    """Map AuditEvent.before_json / after_json (str | None) → parsed JSON."""
    if value is None or isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


class AuditEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    actor_user_id: str | None = None
    action: str
    resource_type: str
    resource_id: str | None = None
    # `before` and `after` derive from ORM columns `before_json` / `after_json`
    # (Text). We do the mapping + decode in one model_validator below so the
    # wire format presents parsed JSON under clean names.
    before: Any | None = None
    after: Any | None = None
    created_at: datetime

    @model_validator(mode="before")
    @classmethod
    def _map_columns(cls, data: Any) -> Any:
        # When data is the ORM object, pull the *_json attrs into before/after.
        # When data is already a dict (e.g. coming back from JSON), leave it.
        if isinstance(data, dict):
            if "before_json" in data and "before" not in data:
                data["before"] = _decode_json(data.pop("before_json"))
            if "after_json" in data and "after" not in data:
                data["after"] = _decode_json(data.pop("after_json"))
            return data
        # ORM object path: copy attrs into a dict so all fields populate.
        if hasattr(data, "__dict__"):
            return {
                "id": data.id,
                "actor_user_id": data.actor_user_id,
                "action": data.action,
                "resource_type": data.resource_type,
                "resource_id": data.resource_id,
                "before": _decode_json(data.before_json),
                "after": _decode_json(data.after_json),
                "created_at": data.created_at,
            }
        return data


class AuditEventList(BaseModel):
    items: list[AuditEventRead]
    total: int
