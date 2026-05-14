"""F19 — In-process fake pyzk harness.

The fake substitutes for `zk.ZK` inside `tikko.zk.client` so tests can drive
the real `ZKClient` code path end-to-end without `unittest.mock.patch`.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

import tikko.zk.client as zk_client_module
from tikko.zk.client import DeviceInfo, RawPunch, ZKClient, ZKConnectionError
from tikko.zk.fake import FakeDevice, use_fake_devices


def _device(host: str = "10.0.0.50") -> FakeDevice:
    return FakeDevice(
        host=host,
        serial_number="FAKE-001",
        firmware_version="6.60",
        platform="JZ4775_TFT",
        device_name="iClock Fake",
    )


def test_test_connection_returns_device_info_from_fake() -> None:
    with use_fake_devices(_device()):
        info = ZKClient(host="10.0.0.50").test_connection()

    assert info == DeviceInfo(
        serial_number="FAKE-001",
        firmware_version="6.60",
        platform="JZ4775_TFT",
        device_name="iClock Fake",
    )


def test_test_connection_raises_when_host_not_registered() -> None:
    with use_fake_devices():
        with pytest.raises(ZKConnectionError):
            ZKClient(host="10.99.99.99").test_connection()


def test_get_attendance_returns_punches_from_fake() -> None:
    device = _device()
    device.add_punch(
        user_id="1042",
        timestamp=datetime(2026, 5, 14, 8, 0, 0, tzinfo=UTC),
        status=0,
        punch=1,
    )
    device.add_punch(
        user_id="1042",
        timestamp=datetime(2026, 5, 14, 17, 0, 0, tzinfo=UTC),
        status=1,
        punch=1,
    )

    with use_fake_devices(device):
        punches = ZKClient(host="10.0.0.50").get_attendance()

    assert punches == [
        RawPunch(
            user_id="1042",
            timestamp=datetime(2026, 5, 14, 8, 0, 0, tzinfo=UTC),
            status=0,
            punch=1,
        ),
        RawPunch(
            user_id="1042",
            timestamp=datetime(2026, 5, 14, 17, 0, 0, tzinfo=UTC),
            status=1,
            punch=1,
        ),
    ]


def test_add_punch_mid_session_visible_on_next_call() -> None:
    device = _device()

    with use_fake_devices(device):
        client = ZKClient(host="10.0.0.50")
        assert client.get_attendance() == []

        device.add_punch(
            user_id="2001",
            timestamp=datetime(2026, 5, 14, 9, 15, 0, tzinfo=UTC),
            status=0,
            punch=15,
        )

        punches = client.get_attendance()

    assert len(punches) == 1
    assert punches[0].user_id == "2001"


def test_use_fake_devices_restores_real_zk_on_exit() -> None:
    original = zk_client_module.ZK
    with use_fake_devices(_device()):
        assert zk_client_module.ZK is not original
    assert zk_client_module.ZK is original


def test_devices_test_connection_route_uses_fake_zk(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    """End-to-end through FastAPI: register a device, hit /test-connection, no mock.patch."""
    created = client.post(
        "/devices",
        json={"name": "Fake T1", "host": "10.0.0.50", "port": 4370},
        headers=admin_auth,
    ).json()

    with use_fake_devices(_device()):
        response = client.post(
            f"/devices/{created['id']}/test-connection", headers=admin_auth
        )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["serial_number"] == "FAKE-001"
    assert body["firmware_version"] == "6.60"
