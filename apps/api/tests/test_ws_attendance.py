"""WebSocket /ws/attendance — clients receive new punches as they're persisted."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect


def _admin_token(client: TestClient) -> str:
    client.post(
        "/auth/register",
        json={"email": "wsadmin@example.com", "password": "supersecret123", "role": "admin"},
    )
    return client.post(
        "/auth/login",
        json={"email": "wsadmin@example.com", "password": "supersecret123"},
    ).json()["access_token"]


def test_ws_requires_token(client: TestClient) -> None:
    """No token → close with 1008 (policy violation)."""
    with pytest.raises(WebSocketDisconnect) as excinfo:
        with client.websocket_connect("/ws/attendance"):
            pass
    assert excinfo.value.code == 1008


def test_ws_pushes_new_attendance_from_adms(client: TestClient) -> None:
    token = _admin_token(client)

    # Pre-register a device by SN.
    client.get("/iclock/cdata", params={"SN": "WS-1"})

    with client.websocket_connect(f"/ws/attendance?token={token}") as ws:
        # Push a punch via ADMS — the WS should receive it.
        body = "9001\t2026-05-12 09:00:00\t0\t1\t0\t0\n"
        client.post(
            "/iclock/cdata",
            params={"SN": "WS-1", "table": "ATTLOG"},
            content=body,
            headers={"Content-Type": "text/plain"},
        )

        message = ws.receive_json()
        assert message["type"] == "attendance.created"
        assert message["device_user_id"] == "9001"
        assert message["punched_at"].startswith("2026-05-12T09:00:00")
