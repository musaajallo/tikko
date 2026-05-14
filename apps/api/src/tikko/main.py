"""FastAPI application entrypoint."""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from tikko import __version__
from tikko.db import Base, get_engine
from tikko.models import (  # noqa: F401 — register metadata
    AttendanceLog,
    Device,
    Employee,
    EmployeeTemplate,
    User,
)
from tikko.routes.auth import router as auth_router
from tikko.routes.devices import router as devices_router
from tikko.routes.employees import router as employees_router
from tikko.routes.iclock import router as iclock_router
from tikko.routes.me import router as me_router
from tikko.routes.stats import router as stats_router
from tikko.routes.ws import router as ws_router
from tikko.scheduler import run_poll_loop
from tikko.settings import get_settings


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Create tables on startup, then run the device-polling worker until
    shutdown. Replaced by Alembic migrations in a later feature."""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

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
app.include_router(devices_router)
app.include_router(employees_router)
app.include_router(me_router)
app.include_router(stats_router)
app.include_router(iclock_router)
app.include_router(ws_router)
