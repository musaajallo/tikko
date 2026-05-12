"""Smoke test: the API responds on /health with a structured status payload."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "tikko-api"
    # Version should be a non-empty string, e.g. "0.0.0".
    assert isinstance(body["version"], str) and body["version"]


def test_health_is_unauthenticated(client: TestClient) -> None:
    """/health must be reachable without auth so liveness probes work."""
    response = client.get("/health")
    assert response.status_code == 200
