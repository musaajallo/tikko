"""FastAPI application entrypoint."""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from tikko import __version__
from tikko.db import Base, get_engine, get_sessionmaker
from tikko.models import (  # noqa: F401 — register metadata
    AttendanceLog,
    AuditEvent,
    Department,
    Device,
    Employee,
    EmployeeTemplate,
    Holiday,
    LeaveRequest,
    ShiftRule,
    User,
    UserTOTP,
)
from tikko.routes.audit import router as audit_router
from tikko.routes.auth import router as auth_router
from tikko.routes.departments import router as departments_router
from tikko.routes.devices import router as devices_router
from tikko.routes.employees import router as employees_router
from tikko.routes.holidays import router as holidays_router
from tikko.routes.iclock import router as iclock_router
from tikko.routes.leave_requests import router as leave_requests_router
from tikko.routes.me import router as me_router
from tikko.routes.permissions import router as permissions_router
from tikko.routes.reports import router as reports_router
from tikko.routes.shift_rules import router as shift_rules_router
from tikko.routes.stats import router as stats_router
from tikko.routes.totp import router as totp_router
from tikko.routes.users import router as users_router
from tikko.routes.ws import router as ws_router
from tikko.scheduler import run_poll_loop
from tikko.settings import get_settings


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Run the device-polling worker until shutdown.

    Schema is managed by Alembic — run `uv run alembic upgrade head` before
    starting the app in any new environment. Tests set
    `TIKKO_CREATE_TABLES_ON_STARTUP=1` to skip migrations and build the schema
    in-memory via `Base.metadata.create_all` for speed.
    """
    # Fail-fast at startup if the deploy mode contradicts the config. LAN mode
    # is permissive (no-op); cloud mode raises on default-secret, sqlite DB,
    # or default-localhost CORS.
    get_settings().validate_for_deployment()

    if os.getenv("TIKKO_CREATE_TABLES_ON_STARTUP") == "1":
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Tests skip migrations, so they also skip the role_permissions seed
        # that the alembic migration installs. Re-seed here from the in-code
        # DEFAULT_MATRIX so every test session has a working RBAC table.
        from sqlalchemy import select as _select

        from tikko.models.role_permission import RolePermission
        from tikko.permissions import DEFAULT_MATRIX

        async with get_sessionmaker()() as session:
            existing = await session.scalar(
                _select(RolePermission).limit(1)
            )
            if existing is None:
                for role, caps in DEFAULT_MATRIX.items():
                    for cap in caps:
                        session.add(RolePermission(role=role, capability=cap))
                await session.commit()

    # Skip the background loop in test runs so tests don't poll real devices.
    poller_task: asyncio.Task[None] | None = None
    if os.getenv("TIKKO_DISABLE_SCHEDULER") != "1":
        poller_task = asyncio.create_task(run_poll_loop(), name="tikko-poller")

    try:
        yield
    finally:
        if poller_task is not None:
            poller_task.cancel()
            try:
                await poller_task
            except asyncio.CancelledError:
                pass


app = FastAPI(title="tikko-api", version=__version__, lifespan=lifespan)

_settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "tikko-api", "version": __version__}


app.include_router(auth_router)
app.include_router(totp_router)
app.include_router(users_router)
app.include_router(audit_router)
app.include_router(departments_router)
app.include_router(devices_router)
app.include_router(employees_router)
app.include_router(holidays_router)
app.include_router(me_router)
app.include_router(permissions_router)
app.include_router(leave_requests_router)
app.include_router(shift_rules_router)
app.include_router(reports_router)
app.include_router(stats_router)
app.include_router(iclock_router)
app.include_router(ws_router)
