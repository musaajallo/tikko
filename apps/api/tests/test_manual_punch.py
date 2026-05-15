"""F38 — manual punch correction."""

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


def _create_employee(client: TestClient, auth: dict[str, str]) -> dict:
    return client.post(
        "/employees",
        json={"employee_code": "1042", "full_name": "Ada"},
        headers=auth,
    ).json()


def test_manual_punch_creates_row(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    emp = _create_employee(client, admin_auth)
    response = client.post(
        "/attendance/manual",
        json={
            "employee_id": emp["id"],
            "punched_at": "2026-05-15T08:30:00Z",
            "note": "forgot to clock in",
        },
        headers=admin_auth,
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["device_id"] is None
    assert body["source"] == "manual"
    assert body["note"] == "forgot to clock in"
    assert body["device_user_id"] == "1042"


def test_manual_punch_404_unknown_employee(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    response = client.post(
        "/attendance/manual",
        json={
            "employee_id": "00000000-0000-0000-0000-000000000000",
            "punched_at": "2026-05-15T08:30:00Z",
        },
        headers=admin_auth,
    )
    assert response.status_code == 404


def test_manual_punch_records_audit_event(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    emp = _create_employee(client, admin_auth)
    client.post(
        "/attendance/manual",
        json={
            "employee_id": emp["id"],
            "punched_at": "2026-05-15T08:30:00Z",
            "note": "fix",
        },
        headers=admin_auth,
    )
    audit = client.get(
        "/audit-log?action=create_manual_punch", headers=admin_auth
    ).json()
    assert audit["total"] == 1
    assert audit["items"][0]["after"]["employee_code"] == "1042"


def test_manual_punch_403_for_employee_role(client: TestClient) -> None:
    token = _register_and_login(client, "employee", "e@example.com")
    response = client.post(
        "/attendance/manual",
        json={
            "employee_id": "x",
            "punched_at": "2026-05-15T08:30:00Z",
        },
        headers=_auth(token),
    )
    assert response.status_code == 403


def test_manual_punch_200_for_manager(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    """Managers should be allowed to correct attendance for their teams."""
    emp = _create_employee(client, admin_auth)
    # Switch to a manager token to verify the capability.
    token = _register_and_login(client, "manager", "m@example.com")
    response = client.post(
        "/attendance/manual",
        json={
            "employee_id": emp["id"],
            "punched_at": "2026-05-15T08:30:00Z",
        },
        headers=_auth(token),
    )
    assert response.status_code == 201
