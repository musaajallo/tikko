"""F26 — ShiftRule CRUD + per-employee assignment."""

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


def _create_rule(
    client: TestClient,
    auth: dict[str, str],
    **overrides: object,
) -> dict:
    payload = {
        "name": "Standard 9-5",
        "start_time": "09:00:00",
        "end_time": "17:00:00",
        "late_grace_minutes": 10,
        "early_out_grace_minutes": 0,
        "overtime_threshold_minutes": 30,
        "work_days": "1111100",
    }
    payload.update(overrides)
    return client.post("/shift-rules", json=payload, headers=auth).json()


def test_post_shift_rule_creates_with_defaults(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    response = client.post(
        "/shift-rules",
        json={
            "name": "Standard 9-5",
            "start_time": "09:00:00",
            "end_time": "17:00:00",
        },
        headers=admin_auth,
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["name"] == "Standard 9-5"
    assert body["start_time"] == "09:00:00"
    assert body["end_time"] == "17:00:00"
    assert body["late_grace_minutes"] == 0
    assert body["early_out_grace_minutes"] == 0
    assert body["overtime_threshold_minutes"] == 30
    assert body["work_days"] == "1111100"
    assert isinstance(body["id"], str) and len(body["id"]) == 36


def test_post_shift_rule_201_for_overnight_shift(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    """F39: end < start is valid — it means the shift spans midnight."""
    response = client.post(
        "/shift-rules",
        json={
            "name": "Night",
            "start_time": "22:00:00",
            "end_time": "06:00:00",
        },
        headers=admin_auth,
    )
    assert response.status_code == 201


def test_post_shift_rule_422_when_start_equals_end(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    response = client.post(
        "/shift-rules",
        json={
            "name": "Zero length",
            "start_time": "09:00:00",
            "end_time": "09:00:00",
        },
        headers=admin_auth,
    )
    assert response.status_code == 422


def test_post_shift_rule_422_when_work_days_malformed(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    response = client.post(
        "/shift-rules",
        json={
            "name": "X",
            "start_time": "09:00:00",
            "end_time": "17:00:00",
            "work_days": "weekdays",
        },
        headers=admin_auth,
    )
    assert response.status_code == 422


def test_post_shift_rule_422_when_negative_grace(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    response = client.post(
        "/shift-rules",
        json={
            "name": "X",
            "start_time": "09:00:00",
            "end_time": "17:00:00",
            "late_grace_minutes": -1,
        },
        headers=admin_auth,
    )
    assert response.status_code == 422


def test_get_shift_rules_lists_with_total(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    _create_rule(client, admin_auth, name="A")
    _create_rule(client, admin_auth, name="B")
    body = client.get("/shift-rules", headers=admin_auth).json()
    assert body["total"] == 2
    names = {item["name"] for item in body["items"]}
    assert names == {"A", "B"}


def test_get_shift_rule_by_id(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    rule = _create_rule(client, admin_auth)
    response = client.get(f"/shift-rules/{rule['id']}", headers=admin_auth)
    assert response.status_code == 200
    assert response.json()["name"] == "Standard 9-5"


def test_get_shift_rule_unknown_404(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    response = client.get(
        "/shift-rules/00000000-0000-0000-0000-000000000000", headers=admin_auth
    )
    assert response.status_code == 404


def test_patch_shift_rule_updates_fields(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    rule = _create_rule(client, admin_auth)
    response = client.patch(
        f"/shift-rules/{rule['id']}",
        json={"name": "Renamed", "start_time": "08:30:00"},
        headers=admin_auth,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Renamed"
    assert body["start_time"] == "08:30:00"
    # untouched
    assert body["end_time"] == "17:00:00"


def test_delete_shift_rule_404_if_unknown(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    response = client.delete(
        "/shift-rules/00000000-0000-0000-0000-000000000000", headers=admin_auth
    )
    assert response.status_code == 404


def test_delete_shift_rule_works_when_unassigned(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    rule = _create_rule(client, admin_auth)
    delete_resp = client.delete(f"/shift-rules/{rule['id']}", headers=admin_auth)
    assert delete_resp.status_code == 204

    get_resp = client.get(f"/shift-rules/{rule['id']}", headers=admin_auth)
    assert get_resp.status_code == 404


def test_delete_shift_rule_409_when_employee_still_assigned(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    rule = _create_rule(client, admin_auth)
    employee = client.post(
        "/employees",
        json={"employee_code": "1042", "full_name": "Ada"},
        headers=admin_auth,
    ).json()
    # Assign the rule to the employee.
    client.patch(
        f"/employees/{employee['id']}",
        json={"shift_rule_id": rule["id"]},
        headers=admin_auth,
    )

    response = client.delete(f"/shift-rules/{rule['id']}", headers=admin_auth)
    assert response.status_code == 409


def test_assign_shift_rule_via_patch_employee(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    rule = _create_rule(client, admin_auth)
    employee = client.post(
        "/employees",
        json={"employee_code": "1042", "full_name": "Ada"},
        headers=admin_auth,
    ).json()
    assert employee["shift_rule_id"] is None

    response = client.patch(
        f"/employees/{employee['id']}",
        json={"shift_rule_id": rule["id"]},
        headers=admin_auth,
    )
    assert response.status_code == 200
    assert response.json()["shift_rule_id"] == rule["id"]


def test_detach_shift_rule_via_patch_employee_with_null(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    rule = _create_rule(client, admin_auth)
    employee = client.post(
        "/employees",
        json={"employee_code": "1042", "full_name": "Ada"},
        headers=admin_auth,
    ).json()
    client.patch(
        f"/employees/{employee['id']}",
        json={"shift_rule_id": rule["id"]},
        headers=admin_auth,
    )

    response = client.patch(
        f"/employees/{employee['id']}",
        json={"shift_rule_id": None},
        headers=admin_auth,
    )
    assert response.status_code == 200
    assert response.json()["shift_rule_id"] is None


def test_assign_unknown_shift_rule_404(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    employee = client.post(
        "/employees",
        json={"employee_code": "1042", "full_name": "Ada"},
        headers=admin_auth,
    ).json()
    response = client.patch(
        f"/employees/{employee['id']}",
        json={"shift_rule_id": "00000000-0000-0000-0000-000000000000"},
        headers=admin_auth,
    )
    assert response.status_code == 404


def test_post_shift_rule_requires_admin(
    client: TestClient,
) -> None:
    token = _register_and_login(client, "employee", "e@example.com")
    response = client.post(
        "/shift-rules",
        json={
            "name": "X",
            "start_time": "09:00:00",
            "end_time": "17:00:00",
        },
        headers=_auth(token),
    )
    assert response.status_code == 403


def test_list_shift_rules_403_for_employee(
    client: TestClient,
) -> None:
    token = _register_and_login(client, "employee", "e@example.com")
    response = client.get("/shift-rules", headers=_auth(token))
    assert response.status_code == 403


def test_list_shift_rules_200_for_manager(
    client: TestClient,
) -> None:
    token = _register_and_login(client, "manager", "m@example.com")
    response = client.get("/shift-rules", headers=_auth(token))
    assert response.status_code == 200
