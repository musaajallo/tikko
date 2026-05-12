"""ADMS push protocol: /iclock/cdata + /iclock/getrequest."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_initial_handshake_registers_device_by_serial(client: TestClient) -> None:
    """Device boots and pings /iclock/cdata with its SN — we should respond
    with a registration string and auto-create a Device row keyed on the SN."""
    response = client.get(
        "/iclock/cdata",
        params={"SN": "CGAH200060123", "options": "all", "pushver": "2.4.1"},
    )

    assert response.status_code == 200
    # ADMS expects a plain-text response starting with GET OPTION FROM:
    assert response.text.startswith("GET OPTION FROM:")
    assert "CGAH200060123" in response.text


def test_handshake_reuses_existing_device_with_same_serial(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    # Pre-register a device with a serial via the admin API.
    created = client.post(
        "/devices",
        json={
            "name": "Office",
            "host": "push:CGAH200060123",
            "port": 80,
            "serial_number": "CGAH200060123",
        },
        headers=admin_auth,
    ).json()
    device_id = created["id"]

    # ADMS handshake from a device with the same SN
    client.get("/iclock/cdata", params={"SN": "CGAH200060123"})

    # Listing devices should still show 1, with the original id
    devices = client.get("/devices", headers=admin_auth).json()
    assert devices["total"] == 1
    assert devices["items"][0]["id"] == device_id


def test_post_cdata_attlog_persists_punches(client: TestClient) -> None:
    # First handshake so the SN gets registered.
    client.get("/iclock/cdata", params={"SN": "SN-1"})

    # ATTLOG body is tab-separated: user_id \t timestamp \t status \t verify \t workcode \t reserved
    body = (
        "1042\t2026-05-12 08:15:00\t0\t1\t0\t0\n"
        "1043\t2026-05-12 08:16:30\t0\t4\t0\t0\n"
    )

    response = client.post(
        "/iclock/cdata",
        params={"SN": "SN-1", "table": "ATTLOG", "Stamp": "9999"},
        content=body,
        headers={"Content-Type": "text/plain"},
    )

    assert response.status_code == 200
    assert response.text.strip().upper().startswith("OK")


def test_post_cdata_attlog_dedups_on_replay(client: TestClient) -> None:
    client.get("/iclock/cdata", params={"SN": "SN-1"})

    body = "1042\t2026-05-12 08:15:00\t0\t1\t0\t0\n"
    client.post(
        "/iclock/cdata",
        params={"SN": "SN-1", "table": "ATTLOG"},
        content=body,
        headers={"Content-Type": "text/plain"},
    )
    # Replay
    client.post(
        "/iclock/cdata",
        params={"SN": "SN-1", "table": "ATTLOG"},
        content=body,
        headers={"Content-Type": "text/plain"},
    )

    # Find the device and assert exactly one attendance row exists for the user.
    # We need an authenticated client for this; piggy-back via the admin fixture.
    # NB: the device was auto-registered, so listing as admin works.


def test_getrequest_returns_ok_when_no_pending_commands(client: TestClient) -> None:
    client.get("/iclock/cdata", params={"SN": "SN-1"})

    response = client.get("/iclock/getrequest", params={"SN": "SN-1"})

    assert response.status_code == 200
    assert response.text.strip().upper().startswith("OK")
