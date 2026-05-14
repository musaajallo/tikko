"""F28 — `/reports/attendance` (JSON + CSV)."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import patch

from fastapi.testclient import TestClient

from tikko.zk.client import RawPunch


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


def _create_employee_with_rule(
    client: TestClient, admin_auth: dict[str, str], *, code: str = "1042"
) -> dict:
    rule = client.post(
        "/shift-rules",
        json={
            "name": "Standard 9-5",
            "start_time": "09:00:00",
            "end_time": "17:00:00",
        },
        headers=admin_auth,
    ).json()
    employee = client.post(
        "/employees",
        json={"employee_code": code, "full_name": "Ada Lovelace"},
        headers=admin_auth,
    ).json()
    client.patch(
        f"/employees/{employee['id']}",
        json={"shift_rule_id": rule["id"]},
        headers=admin_auth,
    )
    return employee


def _seed_punches(
    client: TestClient,
    admin_auth: dict[str, str],
    code: str,
    punches: list[RawPunch],
) -> None:
    device = client.post(
        "/devices",
        json={"name": "T1", "host": "10.0.0.50", "port": 4370},
        headers=admin_auth,
    ).json()
    with patch(
        "tikko.routes.devices.ZKClient.get_attendance",
        return_value=punches,
    ):
        client.post(f"/devices/{device['id']}/poll", headers=admin_auth)


def test_report_json_returns_daily_breakdown_and_totals(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    employee = _create_employee_with_rule(client, admin_auth)
    _seed_punches(
        client,
        admin_auth,
        "1042",
        [
            RawPunch(
                user_id="1042",
                timestamp=datetime(2026, 5, 14, 9, 0, tzinfo=UTC),
                status=0,
                punch=1,
            ),
            RawPunch(
                user_id="1042",
                timestamp=datetime(2026, 5, 14, 17, 0, tzinfo=UTC),
                status=1,
                punch=1,
            ),
        ],
    )

    response = client.get(
        f"/reports/attendance?employee_id={employee['id']}&month=2026-05",
        headers=admin_auth,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["month"] == "2026-05"
    assert body["employee"]["id"] == employee["id"]
    assert body["employee"]["full_name"] == "Ada Lovelace"
    assert len(body["days"]) == 31
    # Find the worked day:
    [worked] = [d for d in body["days"] if d["worked_minutes"] > 0]
    assert worked["date"] == "2026-05-14"
    assert worked["worked_minutes"] == 480
    # Totals
    assert body["totals"]["days_worked"] == 1
    assert body["totals"]["worked_minutes"] == 480
    assert body["totals"]["late_minutes"] == 0


def test_report_404_when_employee_missing(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    response = client.get(
        "/reports/attendance?employee_id=00000000-0000-0000-0000-000000000000&month=2026-05",
        headers=admin_auth,
    )
    assert response.status_code == 404


def test_report_422_when_employee_has_no_shift_rule(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    employee = client.post(
        "/employees",
        json={"employee_code": "1042", "full_name": "Ada"},
        headers=admin_auth,
    ).json()
    response = client.get(
        f"/reports/attendance?employee_id={employee['id']}&month=2026-05",
        headers=admin_auth,
    )
    assert response.status_code == 422


def test_report_422_when_month_format_bad(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    employee = _create_employee_with_rule(client, admin_auth)
    response = client.get(
        f"/reports/attendance?employee_id={employee['id']}&month=May-2026",
        headers=admin_auth,
    )
    assert response.status_code == 422


def test_report_403_for_employee_role(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    employee = _create_employee_with_rule(client, admin_auth)
    employee_token = _register_and_login(client, "employee", "e@example.com")
    response = client.get(
        f"/reports/attendance?employee_id={employee['id']}&month=2026-05",
        headers=_auth(employee_token),
    )
    assert response.status_code == 403


def test_report_200_for_manager_role(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    employee = _create_employee_with_rule(client, admin_auth)
    manager_token = _register_and_login(client, "manager", "m@example.com")
    response = client.get(
        f"/reports/attendance?employee_id={employee['id']}&month=2026-05",
        headers=_auth(manager_token),
    )
    assert response.status_code == 200


def test_report_requires_auth(client: TestClient) -> None:
    response = client.get(
        "/reports/attendance?employee_id=00000000-0000-0000-0000-000000000000&month=2026-05"
    )
    assert response.status_code == 401


def test_report_csv_has_correct_mime_and_header_row(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    employee = _create_employee_with_rule(client, admin_auth)
    response = client.get(
        f"/reports/attendance.csv?employee_id={employee['id']}&month=2026-05",
        headers=admin_auth,
    )
    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("text/csv")
    body = response.text
    lines = body.strip().splitlines()
    # Header + 31 day rows + 1 totals row = 33
    assert len(lines) == 33
    assert lines[0].startswith(
        "date,is_workday,is_absent,worked_minutes,late_minutes,early_out_minutes,overtime_minutes"
    )
    # First data line is 2026-05-01
    assert lines[1].startswith("2026-05-01,")
    # Last line is totals
    assert lines[-1].startswith("TOTAL,")


def test_report_csv_filename_header_includes_employee_and_month(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    employee = _create_employee_with_rule(client, admin_auth)
    response = client.get(
        f"/reports/attendance.csv?employee_id={employee['id']}&month=2026-05",
        headers=admin_auth,
    )
    cd = response.headers.get("content-disposition", "")
    assert "attachment" in cd
    assert "1042" in cd  # employee code
    assert "2026-05" in cd
