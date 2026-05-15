"""role_permissions — which (role, capability) pairs are granted.

Composite PK on (role, capability). Presence = granted; absence = denied.
The seed migration inserts the `DEFAULT_MATRIX`; later edits come through
PATCH /permissions.
"""

from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from tikko.db import Base


class RolePermission(Base):
    __tablename__ = "role_permissions"

    role: Mapped[str] = mapped_column(String(32), primary_key=True)
    capability: Mapped[str] = mapped_column(String(64), primary_key=True)
