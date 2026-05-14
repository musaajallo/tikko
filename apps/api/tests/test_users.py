"""`/users` admin endpoints: list + role update."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _register_and_login(client: TestClient, role: str, email: str) -> str:
    client.post(
        "/auth/register",
        json={"email": email, "password": "supersecret123", "role": role},
    )
    return client.post(
        "/auth/login",
        json={"email": email, "password": "supersecret123"},
    ).json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_list_users_returns_all(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    # admin_auth fixture already created an admin. Add two more users.
    _register_and_login(client, "manager", "m@example.com")
    _register_and_login(client, "employee", "e@example.com")

    response = client.get("/users", headers=admin_auth)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["total"] == 3
    emails = {item["email"] for item in body["items"]}
    assert {"m@example.com", "e@example.com"}.issubset(emails)


def test_list_users_403_for_non_admin(client: TestClient) -> None:
    token = _register_and_login(client, "manager", "m@example.com")
    response = client.get("/users", headers=_auth(token))
    assert response.status_code == 403


def test_list_users_401_unauth(client: TestClient) -> None:
    response = client.get("/users")
    assert response.status_code == 401


def test_patch_user_role_promotes_employee_to_manager(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    _register_and_login(client, "employee", "e@example.com")
    listed = client.get("/users", headers=admin_auth).json()
    target = next(u for u in listed["items"] if u["email"] == "e@example.com")

    response = client.patch(
        f"/users/{target['id']}/role",
        json={"role": "manager"},
        headers=admin_auth,
    )
    assert response.status_code == 200, response.text
    assert response.json()["role"] == "manager"


def test_patch_user_role_404_unknown(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    response = client.patch(
        "/users/00000000-0000-0000-0000-000000000000/role",
        json={"role": "manager"},
        headers=admin_auth,
    )
    assert response.status_code == 404


def test_patch_user_role_422_bad_value(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    _register_and_login(client, "employee", "e@example.com")
    target = next(
        u
        for u in client.get("/users", headers=admin_auth).json()["items"]
        if u["email"] == "e@example.com"
    )

    response = client.patch(
        f"/users/{target['id']}/role",
        json={"role": "wizard"},
        headers=admin_auth,
    )
    assert response.status_code == 422


def test_patch_user_role_409_when_demoting_last_admin(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    """Refuse to demote the only admin — would lock everyone out of admin paths."""
    sole_admin = next(
        u
        for u in client.get("/users", headers=admin_auth).json()["items"]
        if u["role"] == "admin"
    )

    response = client.patch(
        f"/users/{sole_admin['id']}/role",
        json={"role": "manager"},
        headers=admin_auth,
    )
    assert response.status_code == 409


def test_patch_user_role_can_demote_admin_when_other_admins_exist(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    _register_and_login(client, "admin", "admin2@example.com")
    listed = client.get("/users", headers=admin_auth).json()
    second_admin = next(u for u in listed["items"] if u["email"] == "admin2@example.com")

    response = client.patch(
        f"/users/{second_admin['id']}/role",
        json={"role": "manager"},
        headers=admin_auth,
    )
    assert response.status_code == 200


def test_patch_user_role_403_for_non_admin(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    _register_and_login(client, "employee", "e@example.com")
    target = next(
        u
        for u in client.get("/users", headers=admin_auth).json()["items"]
        if u["email"] == "e@example.com"
    )

    manager_token = _register_and_login(client, "manager", "m@example.com")
    response = client.patch(
        f"/users/{target['id']}/role",
        json={"role": "manager"},
        headers=_auth(manager_token),
    )
    assert response.status_code == 403
