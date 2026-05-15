"""`/permissions` + `require_capability` + /auth/me capabilities."""

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


def test_auth_me_includes_admin_capabilities(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    body = client.get("/auth/me", headers=admin_auth).json()
    caps = set(body["capabilities"])
    # Sanity: admin should have at least these out of the box.
    assert {"manage_devices", "manage_employees", "manage_permissions"} <= caps


def test_auth_me_employee_has_no_capabilities_by_default(
    client: TestClient,
) -> None:
    token = _register_and_login(client, "employee", "e@example.com")
    body = client.get("/auth/me", headers=_auth(token)).json()
    assert body["capabilities"] == []


def test_get_permissions_returns_full_matrix(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    body = client.get("/permissions", headers=admin_auth).json()
    assert "admin" in body["matrix"]
    assert "manager" in body["matrix"]
    assert "employee" in body["matrix"]
    assert "manage_devices" in body["all_capabilities"]
    # The seed grants admin every capability.
    assert set(body["all_capabilities"]) <= set(body["matrix"]["admin"])


def test_get_permissions_403_without_manage_permissions(
    client: TestClient,
) -> None:
    token = _register_and_login(client, "manager", "m@example.com")
    response = client.get("/permissions", headers=_auth(token))
    assert response.status_code == 403


def test_patch_permission_grants_a_capability(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    # Manager currently can't manage_devices; grant it.
    response = client.patch(
        "/permissions",
        json={
            "role": "manager",
            "capability": "manage_devices",
            "granted": True,
        },
        headers=admin_auth,
    )
    assert response.status_code == 204

    after = client.get("/permissions", headers=admin_auth).json()
    assert "manage_devices" in after["matrix"]["manager"]

    # The newly-granted capability should also let a manager hit /devices POST.
    mgr_token = _register_and_login(client, "manager", "m@example.com")
    create_response = client.post(
        "/devices",
        json={"name": "Front gate", "host": "10.0.0.50"},
        headers=_auth(mgr_token),
    )
    assert create_response.status_code == 201, create_response.text


def test_patch_permission_revokes_a_capability(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    # Revoke admin's view_employees and confirm a follow-up call now 403s.
    response = client.patch(
        "/permissions",
        json={
            "role": "admin",
            "capability": "view_employees",
            "granted": False,
        },
        headers=admin_auth,
    )
    assert response.status_code == 204

    employees = client.get("/employees", headers=admin_auth)
    assert employees.status_code == 403


def test_patch_permission_idempotent_grant(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    # admin already has manage_devices from the seed.
    response = client.patch(
        "/permissions",
        json={
            "role": "admin",
            "capability": "manage_devices",
            "granted": True,
        },
        headers=admin_auth,
    )
    assert response.status_code == 204


def test_cannot_revoke_last_manage_permissions(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    # Only admin has manage_permissions by default — revoking it would lock
    # the system out of editing the matrix.
    response = client.patch(
        "/permissions",
        json={
            "role": "admin",
            "capability": "manage_permissions",
            "granted": False,
        },
        headers=admin_auth,
    )
    assert response.status_code == 409


def test_patch_permission_422_on_unknown_role_or_capability(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    bad_role = client.patch(
        "/permissions",
        json={
            "role": "superuser",
            "capability": "manage_devices",
            "granted": True,
        },
        headers=admin_auth,
    )
    assert bad_role.status_code == 422

    bad_cap = client.patch(
        "/permissions",
        json={
            "role": "manager",
            "capability": "rule_the_world",
            "granted": True,
        },
        headers=admin_auth,
    )
    assert bad_cap.status_code == 422
