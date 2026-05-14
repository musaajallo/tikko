"""F23-link — registering with an `employee_code` links the user to an Employee,
and `GET /auth/me` returns the current user plus the linked employee (or null).
"""

from __future__ import annotations

from fastapi.testclient import TestClient


def _create_employee(
    client: TestClient,
    auth: dict[str, str],
    *,
    code: str = "1042",
    name: str = "Ada Lovelace",
) -> dict:
    return client.post(
        "/employees",
        json={"employee_code": code, "full_name": name},
        headers=auth,
    ).json()


def _register(
    client: TestClient,
    email: str,
    *,
    password: str = "supersecret123",
    role: str = "employee",
    employee_code: str | None = None,
) -> tuple[int, dict]:
    payload: dict[str, object] = {
        "email": email,
        "password": password,
        "role": role,
    }
    if employee_code is not None:
        payload["employee_code"] = employee_code
    response = client.post("/auth/register", json=payload)
    return response.status_code, response.json()


def _login(
    client: TestClient, email: str, password: str = "supersecret123"
) -> dict[str, str]:
    body = client.post(
        "/auth/login", json={"email": email, "password": password}
    ).json()
    return {"Authorization": f"Bearer {body['access_token']}"}


def test_auth_me_returns_user_with_no_linked_employee(
    client: TestClient,
) -> None:
    _register(client, "solo@example.com")
    auth = _login(client, "solo@example.com")

    response = client.get("/auth/me", headers=auth)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["user"]["email"] == "solo@example.com"
    assert body["employee"] is None


def test_register_with_employee_code_links_user(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    employee = _create_employee(client, admin_auth, code="2001", name="Hal")
    _register(client, "hal@example.com", employee_code="2001")
    auth = _login(client, "hal@example.com")

    response = client.get("/auth/me", headers=auth)
    assert response.status_code == 200
    body = response.json()
    assert body["user"]["email"] == "hal@example.com"
    assert body["employee"] is not None
    assert body["employee"]["id"] == employee["id"]
    assert body["employee"]["employee_code"] == "2001"


def test_register_with_unknown_employee_code_404s(client: TestClient) -> None:
    status_code, body = _register(
        client, "ghost@example.com", employee_code="9999"
    )
    assert status_code == 404
    assert "9999" in body.get("detail", "")


def test_auth_me_requires_auth(client: TestClient) -> None:
    response = client.get("/auth/me")
    assert response.status_code == 401
