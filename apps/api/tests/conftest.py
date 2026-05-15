"""Shared pytest fixtures for the tikko-api test suite.

Each test gets a fresh in-memory SQLite engine; the `get_session` dependency
is overridden so the app reads from that engine instead of the configured
production database.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator, Iterator

import pytest

# Disable the background poller during tests — it would try to connect to
# real devices on every tick. Must be set before tikko.main is imported.
os.environ.setdefault("TIKKO_DISABLE_SCHEDULER", "1")

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# Tell the app's lifespan to create tables on startup (test-only convenience).
# Real environments leave this unset and run `alembic upgrade head` instead.
os.environ.setdefault("TIKKO_CREATE_TABLES_ON_STARTUP", "1")

import tikko.db as db_module
from tikko.db import get_session
from tikko.main import app
from tikko.models import (  # noqa: F401 — register models with Base.metadata
    AttendanceLog,
    AuditEvent,
    Department,
    Device,
    Employee,
    EmployeeTemplate,
    Holiday,
    User,
)


@pytest.fixture
def client() -> Iterator[TestClient]:
    """A TestClient backed by an isolated in-memory SQLite database."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    test_sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

    # Point the module-level cache at the test engine so anything that calls
    # get_engine()/get_sessionmaker() during the request lifecycle stays
    # consistent with the override below.
    db_module._engine = engine
    db_module._sessionmaker = test_sessionmaker

    async def override_get_session() -> AsyncIterator[AsyncSession]:
        async with test_sessionmaker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_session] = override_get_session

    try:
        # TestClient drives the lifespan, which creates tables on the test engine.
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        db_module.reset_engine()


@pytest.fixture
def admin_auth(client: TestClient) -> dict[str, str]:
    """Register a fresh admin user and return an `Authorization: Bearer …` header dict."""
    client.post(
        "/auth/register",
        json={
            "email": "admin-fixture@example.com",
            "password": "supersecret123",
            "role": "admin",
        },
    )
    token = client.post(
        "/auth/login",
        json={"email": "admin-fixture@example.com", "password": "supersecret123"},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
