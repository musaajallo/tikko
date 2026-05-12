"""Auth guards: who can call which /devices endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _register_and_login(client: TestClient, role: str, email: str) -> str:
    client.post(
        "/auth/register",
        json={"email": email, "password": "supersecret123", "role": role},
    )
    body = client.post(
        "/auth/login",
        json={"email": email, "password": "supersecret123"},
    ).json()
    return body["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_health_is_public(client: TestClient) -> None:
    assert client.get("/health").status_code == 200


def test_devices_requires_auth(client: TestClient) -> None:
    response = client.get("/devices")
    assert response.status_code == 401


def test_devices_rejects_bad_token(client: TestClient) -> None:
    response = client.get("/devices", headers={"Authorization": "Bearer not-a-jwt"})
    assert response.status_code == 401


def test_post_devices_requires_admin_role(client: TestClient) -> None:
    employee_token = _register_and_login(client, "employee", "e@example.com")
    response = client.post(
        "/devices",
        json={"name": "X", "host": "10.0.0.1"},
        headers=_auth(employee_token),
    )
    assert response.status_code == 403


def test_admin_can_register_device(client: TestClient) -> None:
    admin_token = _register_and_login(client, "admin", "a@example.com")
    response = client.post(
        "/devices",
        json={"name": "Front gate", "host": "10.0.0.50"},
        headers=_auth(admin_token),
    )
    assert response.status_code == 201


def test_manager_can_list_devices(client: TestClient) -> None:
    admin_token = _register_and_login(client, "admin", "a@example.com")
    client.post(
        "/devices",
        json={"name": "X", "host": "10.0.0.1"},
        headers=_auth(admin_token),
    )

    manager_token = _register_and_login(client, "manager", "m@example.com")
    response = client.get("/devices", headers=_auth(manager_token))
    assert response.status_code == 200
    assert response.json()["total"] >= 1


def test_employee_cannot_test_connection(client: TestClient) -> None:
    admin_token = _register_and_login(client, "admin", "a@example.com")
    device = client.post(
        "/devices",
        json={"name": "X", "host": "10.0.0.1"},
        headers=_auth(admin_token),
    ).json()

    employee_token = _register_and_login(client, "employee", "e@example.com")
    response = client.post(
        f"/devices/{device['id']}/test-connection",
        headers=_auth(employee_token),
    )
    assert response.status_code == 403


def test_employee_can_view_attendance(client: TestClient) -> None:
    admin_token = _register_and_login(client, "admin", "a@example.com")
    device = client.post(
        "/devices",
        json={"name": "X", "host": "10.0.0.1"},
        headers=_auth(admin_token),
    ).json()

    employee_token = _register_and_login(client, "employee", "e@example.com")
    response = client.get(
        f"/devices/{device['id']}/attendance",
        headers=_auth(employee_token),
    )
    assert response.status_code == 200
