"""POST /devices/{id}/test-connection — connect to a real device via pyzk."""

from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from tikko.zk.client import DeviceInfo, ZKConnectionError


def _create_device(client: TestClient) -> dict:
    return client.post(
        "/devices",
        json={"name": "T1", "host": "10.0.0.50", "port": 4370},
    ).json()


def test_test_connection_returns_device_info(client: TestClient) -> None:
    device = _create_device(client)

    fake_info = DeviceInfo(
        serial_number="ZK-12345",
        firmware_version="6.60",
        platform="JZ4775_TFT",
        device_name="iClock 580",
    )

    with patch("tikko.routes.devices.ZKClient.test_connection", return_value=fake_info):
        response = client.post(f"/devices/{device['id']}/test-connection")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["serial_number"] == "ZK-12345"
    assert body["firmware_version"] == "6.60"
    assert body["platform"] == "JZ4775_TFT"
    assert body["device_name"] == "iClock 580"


def test_test_connection_404_on_unknown_device(client: TestClient) -> None:
    response = client.post(
        "/devices/00000000-0000-0000-0000-000000000000/test-connection"
    )
    assert response.status_code == 404


def test_test_connection_503_when_device_unreachable(client: TestClient) -> None:
    device = _create_device(client)

    with patch(
        "tikko.routes.devices.ZKClient.test_connection",
        side_effect=ZKConnectionError("connect timeout"),
    ):
        response = client.post(f"/devices/{device['id']}/test-connection")

    assert response.status_code == 503
    assert "connect timeout" in response.json()["detail"]
