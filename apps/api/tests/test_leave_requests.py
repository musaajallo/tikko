"""F24 — leave requests: employee submits, lists own.

Approve/reject + team list are deferred to F24-approve.
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


def _unlinked_user(client: TestClient, email: str = "unlinked@example.com") -> dict[str, str]:
    client.post(
        "/auth/register",
        json={"email": email, "password": "supersecret123", "role": "employee"},
    )
    body = client.post(
        "/auth/login",
        json={"email": email, "password": "supersecret123"},
    ).json()
    return {"Authorization": f"Bearer {body['access_token']}"}


def test_submit_leave_request_creates_pending_row(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    employee = _create_employee(client, admin_auth)
    auth = _register_employee_user(client, "ada@example.com", employee["employee_code"])

    response = client.post(
        "/me/leave-requests",
        json={
            "start_date": "2026-06-01",
            "end_date": "2026-06-05",
            "reason": "Family visit",
        },
        headers=auth,
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "pending"
    assert body["start_date"] == "2026-06-01"
    assert body["end_date"] == "2026-06-05"
    assert body["reason"] == "Family visit"
    assert body["employee_id"] == employee["id"]
    assert body["decided_at"] is None
    assert body["decided_by_user_id"] is None
    assert "created_at" in body


def test_submit_leave_request_rejects_end_before_start(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    employee = _create_employee(client, admin_auth)
    auth = _register_employee_user(client, "ada@example.com", employee["employee_code"])

    response = client.post(
        "/me/leave-requests",
        json={
            "start_date": "2026-06-10",
            "end_date": "2026-06-01",
            "reason": "Wrong way",
        },
        headers=auth,
    )
    assert response.status_code == 422


def test_submit_leave_request_403_when_user_unlinked(
    client: TestClient,
) -> None:
    auth = _unlinked_user(client)
    response = client.post(
        "/me/leave-requests",
        json={
            "start_date": "2026-06-01",
            "end_date": "2026-06-05",
            "reason": "x",
        },
        headers=auth,
    )
    assert response.status_code == 403


def test_submit_leave_request_requires_auth(client: TestClient) -> None:
    response = client.post(
        "/me/leave-requests",
        json={
            "start_date": "2026-06-01",
            "end_date": "2026-06-05",
            "reason": "x",
        },
    )
    assert response.status_code == 401


def test_list_my_leave_requests_returns_only_own(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    a = _create_employee(client, admin_auth, code="1042", name="Ada")
    b = _create_employee(client, admin_auth, code="2001", name="Bob")
    auth_a = _register_employee_user(client, "a@example.com", a["employee_code"])
    auth_b = _register_employee_user(client, "b@example.com", b["employee_code"])

    # Ada submits two, Bob submits one.
    client.post(
        "/me/leave-requests",
        json={"start_date": "2026-06-01", "end_date": "2026-06-02", "reason": "x1"},
        headers=auth_a,
    )
    client.post(
        "/me/leave-requests",
        json={"start_date": "2026-07-01", "end_date": "2026-07-02", "reason": "x2"},
        headers=auth_a,
    )
    client.post(
        "/me/leave-requests",
        json={"start_date": "2026-06-01", "end_date": "2026-06-02", "reason": "y1"},
        headers=auth_b,
    )

    response = client.get("/me/leave-requests", headers=auth_a)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    reasons = [item["reason"] for item in body["items"]]
    assert set(reasons) == {"x1", "x2"}


def test_list_my_leave_requests_newest_first(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    employee = _create_employee(client, admin_auth)
    auth = _register_employee_user(client, "ada@example.com", employee["employee_code"])

    client.post(
        "/me/leave-requests",
        json={"start_date": "2026-06-01", "end_date": "2026-06-02", "reason": "first"},
        headers=auth,
    )
    client.post(
        "/me/leave-requests",
        json={"start_date": "2026-07-01", "end_date": "2026-07-02", "reason": "second"},
        headers=auth,
    )

    body = client.get("/me/leave-requests", headers=auth).json()
    # Newest (last submitted) first.
    assert body["items"][0]["reason"] == "second"
    assert body["items"][1]["reason"] == "first"


def test_list_my_leave_requests_403_when_unlinked(client: TestClient) -> None:
    auth = _unlinked_user(client)
    response = client.get("/me/leave-requests", headers=auth)
    assert response.status_code == 403


def test_list_my_leave_requests_requires_auth(client: TestClient) -> None:
    response = client.get("/me/leave-requests")
    assert response.status_code == 401
