"""`POST /auth/change-password` — verify current, update to new."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _register_and_login(
    client: TestClient,
    *,
    email: str = "user@example.com",
    password: str = "supersecret123",
    role: str = "employee",
) -> dict[str, str]:
    client.post(
        "/auth/register",
        json={"email": email, "password": password, "role": role},
    )
    body = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    ).json()
    return {"Authorization": f"Bearer {body['access_token']}"}


def test_change_password_happy_path(client: TestClient) -> None:
    auth = _register_and_login(client)
    response = client.post(
        "/auth/change-password",
        json={
            "current_password": "supersecret123",
            "new_password": "evenbetterpassword456",
        },
        headers=auth,
    )
    assert response.status_code == 204, response.text

    # New password works.
    new_login = client.post(
        "/auth/login",
        json={"email": "user@example.com", "password": "evenbetterpassword456"},
    )
    assert new_login.status_code == 200

    # Old password no longer works.
    old_login = client.post(
        "/auth/login",
        json={"email": "user@example.com", "password": "supersecret123"},
    )
    assert old_login.status_code == 401


def test_change_password_wrong_current_returns_401(client: TestClient) -> None:
    auth = _register_and_login(client)
    response = client.post(
        "/auth/change-password",
        json={
            "current_password": "wrong-one",
            "new_password": "evenbetterpassword456",
        },
        headers=auth,
    )
    assert response.status_code == 401


def test_change_password_new_too_short_returns_422(client: TestClient) -> None:
    auth = _register_and_login(client)
    response = client.post(
        "/auth/change-password",
        json={
            "current_password": "supersecret123",
            "new_password": "short",
        },
        headers=auth,
    )
    assert response.status_code == 422


def test_change_password_requires_auth(client: TestClient) -> None:
    response = client.post(
        "/auth/change-password",
        json={
            "current_password": "supersecret123",
            "new_password": "evenbetterpassword456",
        },
    )
    assert response.status_code == 401
