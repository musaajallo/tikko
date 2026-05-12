"""Devices API — register, list, retrieve."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_post_devices_creates_a_device(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    payload = {
        "name": "Front gate",
        "host": "192.168.1.50",
        "port": 4370,
        "location": "HQ entrance",
    }
    response = client.post("/devices", json=payload, headers=admin_auth)

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["name"] == "Front gate"
    assert body["host"] == "192.168.1.50"
    assert body["port"] == 4370
    assert body["location"] == "HQ entrance"
    assert isinstance(body["id"], str) and len(body["id"]) == 36
    assert "created_at" in body


def test_post_devices_defaults_port_to_4370(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    response = client.post(
        "/devices",
        json={"name": "Back door", "host": "10.0.0.20"},
        headers=admin_auth,
    )
    assert response.status_code == 201, response.text
    assert response.json()["port"] == 4370


def test_post_devices_rejects_missing_host(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    response = client.post("/devices", json={"name": "No host"}, headers=admin_auth)
    assert response.status_code == 422


def test_get_devices_lists_devices(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    client.post("/devices", json={"name": "A", "host": "10.0.0.1"}, headers=admin_auth)
    client.post("/devices", json={"name": "B", "host": "10.0.0.2"}, headers=admin_auth)

    response = client.get("/devices", headers=admin_auth)

    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 2
    names = {item["name"] for item in body["items"]}
    assert {"A", "B"}.issubset(names)


def test_get_device_by_id(client: TestClient, admin_auth: dict[str, str]) -> None:
    created = client.post(
        "/devices",
        json={"name": "Lookup target", "host": "10.0.0.99"},
        headers=admin_auth,
    ).json()

    response = client.get(f"/devices/{created['id']}", headers=admin_auth)

    assert response.status_code == 200
    assert response.json()["name"] == "Lookup target"


def test_get_device_by_unknown_id_returns_404(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    response = client.get(
        "/devices/00000000-0000-0000-0000-000000000000", headers=admin_auth
    )
    assert response.status_code == 404
