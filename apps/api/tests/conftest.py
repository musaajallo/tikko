"""Shared pytest fixtures for the tikko-api test suite."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from tikko.main import app


@pytest.fixture
def client() -> TestClient:
    """A synchronous TestClient bound to the FastAPI app."""
    return TestClient(app)
