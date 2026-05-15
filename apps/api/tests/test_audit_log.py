"""F34 — Audit log."""

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


def test_list_audit_log_starts_empty(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    body = client.get("/audit-log", headers=admin_auth).json()
    assert body == {"items": [], "total": 0}


def test_create_employee_records_audit_event(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    response = client.post(
        "/employees",
        json={"employee_code": "1042", "full_name": "Ada"},
        headers=admin_auth,
    )
    assert response.status_code == 201

    body = client.get("/audit-log", headers=admin_auth).json()
    assert body["total"] == 1
    event = body["items"][0]
    assert event["action"] == "create_employee"
    assert event["resource_type"] == "employee"
    assert event["after"]["employee_code"] == "1042"
    assert event["after"]["full_name"] == "Ada"
    assert event["before"] is None


def test_update_employee_records_before_and_after(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    emp = client.post(
        "/employees",
        json={"employee_code": "1042", "full_name": "Ada"},
        headers=admin_auth,
    ).json()
    client.patch(
        f"/employees/{emp['id']}",
        json={"full_name": "Ada Lovelace"},
        headers=admin_auth,
    )

    items = (
        client.get(
            "/audit-log?action=update_employee", headers=admin_auth
        ).json()["items"]
    )
    assert len(items) == 1
    event = items[0]
    assert event["before"]["full_name"] == "Ada"
    assert event["after"]["full_name"] == "Ada Lovelace"


def test_delete_department_records_before_only(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    dept = client.post(
        "/departments", json={"name": "Engineering"}, headers=admin_auth
    ).json()
    client.delete(f"/departments/{dept['id']}", headers=admin_auth)

    items = (
        client.get(
            "/audit-log?action=delete_department", headers=admin_auth
        ).json()["items"]
    )
    assert len(items) == 1
    event = items[0]
    assert event["before"]["name"] == "Engineering"
    assert event["after"] is None
    assert event["resource_id"] == dept["id"]


def test_filter_audit_log_by_resource_type(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    client.post(
        "/employees",
        json={"employee_code": "1042", "full_name": "Ada"},
        headers=admin_auth,
    )
    client.post("/departments", json={"name": "Eng"}, headers=admin_auth)

    employees_only = client.get(
        "/audit-log?resource_type=employee", headers=admin_auth
    ).json()
    assert employees_only["total"] == 1
    assert employees_only["items"][0]["resource_type"] == "employee"


def test_list_audit_log_requires_capability(client: TestClient) -> None:
    token = _register_and_login(client, "manager", "m@example.com")
    response = client.get("/audit-log", headers=_auth(token))
    assert response.status_code == 403


def test_failed_role_demotion_does_not_log(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    """An admin whose role can't change shouldn't leave an audit row behind.

    The lockout guard rejects the call with 409, so no DB state changes — and
    the audit log must reflect that rejection by recording nothing.
    """
    # The only admin in this test is the admin_auth fixture user. Try to
    # demote them and expect 409.
    users = client.get("/users", headers=admin_auth).json()["items"]
    admin_user = next(u for u in users if u["role"] == "admin")
    response = client.patch(
        f"/users/{admin_user['id']}/role",
        json={"role": "employee"},
        headers=admin_auth,
    )
    assert response.status_code == 409
    role_events = client.get(
        "/audit-log?action=update_user_role", headers=admin_auth
    ).json()
    assert role_events["total"] == 0
