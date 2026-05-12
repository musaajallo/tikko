"""Attendance log: poll a device, list its logs, dedup on repeated polls."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import patch

from fastapi.testclient import TestClient

from tikko.zk.client import RawPunch


def _create_device(client: TestClient) -> dict:
    return client.post(
        "/devices",
        json={"name": "T1", "host": "10.0.0.50", "port": 4370},
    ).json()


def _punches(count: int = 3) -> list[RawPunch]:
    return [
        RawPunch(
            user_id="1042",
            timestamp=datetime(2026, 5, 12, 8, i, 0, tzinfo=UTC),
            status=0,
            punch=i,
        )
        for i in range(count)
    ]


def test_poll_persists_new_punches_and_reports_count(client: TestClient) -> None:
    device = _create_device(client)

    with patch(
        "tikko.routes.devices.ZKClient.get_attendance",
        return_value=_punches(3),
    ):
        response = client.post(f"/devices/{device['id']}/poll")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["polled"] == 3
    assert body["new"] == 3


def test_poll_is_idempotent_no_dedup_inserts(client: TestClient) -> None:
    device = _create_device(client)

    with patch(
        "tikko.routes.devices.ZKClient.get_attendance",
        return_value=_punches(3),
    ):
        first = client.post(f"/devices/{device['id']}/poll").json()
        second = client.post(f"/devices/{device['id']}/poll").json()

    assert first["new"] == 3
    assert second["polled"] == 3
    assert second["new"] == 0


def test_poll_404_unknown_device(client: TestClient) -> None:
    response = client.post(
        "/devices/00000000-0000-0000-0000-000000000000/poll"
    )
    assert response.status_code == 404


def test_get_attendance_lists_punches(client: TestClient) -> None:
    device = _create_device(client)

    with patch(
        "tikko.routes.devices.ZKClient.get_attendance",
        return_value=_punches(2),
    ):
        client.post(f"/devices/{device['id']}/poll")

    response = client.get(f"/devices/{device['id']}/attendance")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert len(body["items"]) == 2
    assert all(item["device_user_id"] == "1042" for item in body["items"])
