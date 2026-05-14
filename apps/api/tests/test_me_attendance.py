"""F23-link — /me/attendance + /me/attendance/summary scoped to the logged-in user's linked employee."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import patch

from fastapi.testclient import TestClient

from tikko.zk.client import RawPunch


def _create_employee(
    client: TestClient,
    auth: dict[str, str],
    *,
    code: str,
    name: str = "x",
) -> dict:
    return client.post(
        "/employees",
        json={"employee_code": code, "full_name": name},
        headers=auth,
    ).json()


def _create_device(client: TestClient, auth: dict[str, str]) -> dict:
    return client.post(
        "/devices",
        json={"name": "T1", "host": "10.0.0.50", "port": 4370},
        headers=auth,
    ).json()


def _seed_punches_for(
    client: TestClient,
    admin_auth: dict[str, str],
    device_id: str,
    user_id: str,
    punches: list[RawPunch],
) -> None:
    """Use the existing poll path to seed attendance rows for `user_id`."""
    with patch(
        "tikko.routes.devices.ZKClient.get_attendance", return_value=punches
    ):
        client.post(f"/devices/{device_id}/poll", headers=admin_auth)


def _register_employee_user(
    client: TestClient, email: str, employee_code: str
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


def test_me_attendance_returns_only_linked_employees_punches(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    me = _create_employee(client, admin_auth, code="1042", name="Me")
    _create_employee(client, admin_auth, code="2001", name="Other")
    device = _create_device(client, admin_auth)

    # Punches for both employees on the same device — only "me" rows should appear.
    _seed_punches_for(
        client,
        admin_auth,
        device["id"],
        "1042",
        [
            RawPunch(
                user_id="1042",
                timestamp=datetime(2026, 5, 14, 8, 0, tzinfo=UTC),
                status=0,
                punch=1,
            ),
            RawPunch(
                user_id="2001",
                timestamp=datetime(2026, 5, 14, 8, 5, tzinfo=UTC),
                status=0,
                punch=1,
            ),
        ],
    )

    auth = _register_employee_user(client, "me@example.com", me["employee_code"])
    response = client.get("/me/attendance", headers=auth)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["device_user_id"] == "1042"


def test_me_attendance_403_when_user_not_linked(client: TestClient) -> None:
    client.post(
        "/auth/register",
        json={
            "email": "unlinked@example.com",
            "password": "supersecret123",
            "role": "employee",
        },
    )
    body = client.post(
        "/auth/login",
        json={"email": "unlinked@example.com", "password": "supersecret123"},
    ).json()
    auth = {"Authorization": f"Bearer {body['access_token']}"}

    response = client.get("/me/attendance", headers=auth)
    assert response.status_code == 403


def test_me_attendance_requires_auth(client: TestClient) -> None:
    response = client.get("/me/attendance")
    assert response.status_code == 401


def test_me_attendance_summary_counts_total_and_unique_days(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    me = _create_employee(client, admin_auth, code="3007")
    device = _create_device(client, admin_auth)

    # Three punches in May: two on the 14th, one on the 15th → 3 punches, 2 days.
    _seed_punches_for(
        client,
        admin_auth,
        device["id"],
        "3007",
        [
            RawPunch(
                user_id="3007",
                timestamp=datetime(2026, 5, 14, 8, 0, tzinfo=UTC),
                status=0,
                punch=1,
            ),
            RawPunch(
                user_id="3007",
                timestamp=datetime(2026, 5, 14, 17, 0, tzinfo=UTC),
                status=1,
                punch=1,
            ),
            RawPunch(
                user_id="3007",
                timestamp=datetime(2026, 5, 15, 8, 0, tzinfo=UTC),
                status=0,
                punch=1,
            ),
            # Different month — must not be counted.
            RawPunch(
                user_id="3007",
                timestamp=datetime(2026, 4, 30, 8, 0, tzinfo=UTC),
                status=0,
                punch=1,
            ),
        ],
    )

    auth = _register_employee_user(
        client, "me-3007@example.com", me["employee_code"]
    )
    response = client.get(
        "/me/attendance/summary?month=2026-05", headers=auth
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["month"] == "2026-05"
    assert body["total_punches"] == 3
    assert body["days_present"] == 2


def test_me_attendance_summary_rejects_bad_month_format(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    me = _create_employee(client, admin_auth, code="4001")
    auth = _register_employee_user(client, "me-4001@example.com", me["employee_code"])

    response = client.get("/me/attendance/summary?month=May+2026", headers=auth)
    assert response.status_code == 422


def test_me_attendance_summary_403_when_unlinked(client: TestClient) -> None:
    client.post(
        "/auth/register",
        json={
            "email": "unlinked-sum@example.com",
            "password": "supersecret123",
            "role": "employee",
        },
    )
    body = client.post(
        "/auth/login",
        json={"email": "unlinked-sum@example.com", "password": "supersecret123"},
    ).json()
    auth = {"Authorization": f"Bearer {body['access_token']}"}

    response = client.get("/me/attendance/summary?month=2026-05", headers=auth)
    assert response.status_code == 403
