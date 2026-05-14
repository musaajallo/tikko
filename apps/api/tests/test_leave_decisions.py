"""F24-approve — GET /leave-requests + PATCH /:id/decision (admin/manager)."""

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


def _register_employee_user(
    client: TestClient,
    email: str,
    employee_code: str,
) -> dict[str, str]:
    client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "supersecret123",
            "role": "employee",
            "employee_code": employee_code,
        },
    )
    body = client.post(
        "/auth/login",
        json={"email": email, "password": "supersecret123"},
    ).json()
    return {"Authorization": f"Bearer {body['access_token']}"}


def _submit_leave(
    client: TestClient,
    auth: dict[str, str],
    *,
    start: str = "2026-06-01",
    end: str = "2026-06-05",
    reason: str = "Family visit",
) -> dict:
    return client.post(
        "/me/leave-requests",
        json={"start_date": start, "end_date": end, "reason": reason},
        headers=auth,
    ).json()


def test_list_leave_requests_returns_all_for_admin(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    e1 = _create_employee(client, admin_auth, code="1042", name="Ada")
    e2 = _create_employee(client, admin_auth, code="2001", name="Bob")
    auth1 = _register_employee_user(client, "ada@example.com", e1["employee_code"])
    auth2 = _register_employee_user(client, "bob@example.com", e2["employee_code"])
    _submit_leave(client, auth1, reason="ada-1")
    _submit_leave(client, auth2, reason="bob-1")

    response = client.get("/leave-requests", headers=admin_auth)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["total"] == 2
    reasons = {item["reason"] for item in body["items"]}
    assert reasons == {"ada-1", "bob-1"}


def test_list_leave_requests_filters_by_status(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    employee = _create_employee(client, admin_auth)
    auth = _register_employee_user(client, "ada@example.com", employee["employee_code"])
    a = _submit_leave(client, auth, reason="will-decide")
    _submit_leave(client, auth, reason="stays-pending")

    # Approve the first one.
    client.patch(
        f"/leave-requests/{a['id']}/decision",
        json={"decision": "approved"},
        headers=admin_auth,
    )

    pending = client.get("/leave-requests?status=pending", headers=admin_auth).json()
    approved = client.get("/leave-requests?status=approved", headers=admin_auth).json()

    assert pending["total"] == 1
    assert pending["items"][0]["reason"] == "stays-pending"
    assert approved["total"] == 1
    assert approved["items"][0]["reason"] == "will-decide"


def test_list_leave_requests_paginates(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    employee = _create_employee(client, admin_auth)
    auth = _register_employee_user(client, "ada@example.com", employee["employee_code"])
    for i in range(3):
        _submit_leave(
            client,
            auth,
            start=f"2026-0{6 + i}-01",
            end=f"2026-0{6 + i}-02",
            reason=f"r{i}",
        )

    response = client.get(
        "/leave-requests?page=1&page_size=2", headers=admin_auth
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert len(body["items"]) == 2


def test_list_leave_requests_403_for_employee(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    employee_token = _register_and_login(client, "employee", "e@example.com")
    response = client.get("/leave-requests", headers=_auth(employee_token))
    assert response.status_code == 403


def test_list_leave_requests_requires_auth(client: TestClient) -> None:
    response = client.get("/leave-requests")
    assert response.status_code == 401


def test_patch_decision_approves_and_stamps(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    employee = _create_employee(client, admin_auth)
    auth = _register_employee_user(client, "ada@example.com", employee["employee_code"])
    leave = _submit_leave(client, auth)

    response = client.patch(
        f"/leave-requests/{leave['id']}/decision",
        json={"decision": "approved"},
        headers=admin_auth,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "approved"
    assert body["decided_at"] is not None
    assert body["decided_by_user_id"] is not None  # the admin user that decided


def test_patch_decision_rejects(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    employee = _create_employee(client, admin_auth)
    auth = _register_employee_user(client, "ada@example.com", employee["employee_code"])
    leave = _submit_leave(client, auth)

    response = client.patch(
        f"/leave-requests/{leave['id']}/decision",
        json={"decision": "rejected"},
        headers=admin_auth,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "rejected"


def test_patch_decision_409_if_already_decided(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    employee = _create_employee(client, admin_auth)
    auth = _register_employee_user(client, "ada@example.com", employee["employee_code"])
    leave = _submit_leave(client, auth)

    client.patch(
        f"/leave-requests/{leave['id']}/decision",
        json={"decision": "approved"},
        headers=admin_auth,
    )
    response = client.patch(
        f"/leave-requests/{leave['id']}/decision",
        json={"decision": "rejected"},
        headers=admin_auth,
    )
    assert response.status_code == 409


def test_patch_decision_404_unknown_id(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    response = client.patch(
        "/leave-requests/00000000-0000-0000-0000-000000000000/decision",
        json={"decision": "approved"},
        headers=admin_auth,
    )
    assert response.status_code == 404


def test_patch_decision_422_bad_value(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    employee = _create_employee(client, admin_auth)
    auth = _register_employee_user(client, "ada@example.com", employee["employee_code"])
    leave = _submit_leave(client, auth)

    response = client.patch(
        f"/leave-requests/{leave['id']}/decision",
        json={"decision": "maybe"},
        headers=admin_auth,
    )
    assert response.status_code == 422


def test_patch_decision_403_for_employee(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    employee = _create_employee(client, admin_auth)
    auth = _register_employee_user(client, "ada@example.com", employee["employee_code"])
    leave = _submit_leave(client, auth)

    employee_token = _register_and_login(client, "employee", "other@example.com")
    response = client.patch(
        f"/leave-requests/{leave['id']}/decision",
        json={"decision": "approved"},
        headers=_auth(employee_token),
    )
    assert response.status_code == 403


def test_patch_decision_requires_auth(client: TestClient) -> None:
    response = client.patch(
        "/leave-requests/00000000-0000-0000-0000-000000000000/decision",
        json={"decision": "approved"},
    )
    assert response.status_code == 401


def test_manager_can_decide(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    employee = _create_employee(client, admin_auth)
    auth = _register_employee_user(client, "ada@example.com", employee["employee_code"])
    leave = _submit_leave(client, auth)

    manager_token = _register_and_login(client, "manager", "mgr@example.com")
    response = client.patch(
        f"/leave-requests/{leave['id']}/decision",
        json={"decision": "approved"},
        headers=_auth(manager_token),
    )
    assert response.status_code == 200
