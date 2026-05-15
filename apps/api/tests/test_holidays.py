"""F35 — Holiday CRUD + payroll engine integration."""

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


def test_post_holiday_creates(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    response = client.post(
        "/holidays",
        json={"date": "2026-12-25", "name": "Christmas Day"},
        headers=admin_auth,
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["date"] == "2026-12-25"
    assert body["name"] == "Christmas Day"


def test_post_holiday_409_on_duplicate_date(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    client.post(
        "/holidays",
        json={"date": "2026-12-25", "name": "Christmas Day"},
        headers=admin_auth,
    )
    second = client.post(
        "/holidays",
        json={"date": "2026-12-25", "name": "Christmas (alt)"},
        headers=admin_auth,
    )
    assert second.status_code == 409


def test_list_holidays_filters_by_year(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    client.post(
        "/holidays",
        json={"date": "2026-01-01", "name": "New Year"},
        headers=admin_auth,
    )
    client.post(
        "/holidays",
        json={"date": "2027-01-01", "name": "New Year"},
        headers=admin_auth,
    )

    only_2026 = client.get("/holidays?year=2026", headers=admin_auth).json()
    assert only_2026["total"] == 1
    assert only_2026["items"][0]["date"] == "2026-01-01"


def test_patch_holiday_updates(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    h = client.post(
        "/holidays",
        json={"date": "2026-05-01", "name": "Labour Day"},
        headers=admin_auth,
    ).json()
    response = client.patch(
        f"/holidays/{h['id']}",
        json={"name": "Workers' Day"},
        headers=admin_auth,
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Workers' Day"


def test_delete_holiday(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    h = client.post(
        "/holidays",
        json={"date": "2026-12-31", "name": "Year end"},
        headers=admin_auth,
    ).json()
    response = client.delete(f"/holidays/{h['id']}", headers=admin_auth)
    assert response.status_code == 204
    again = client.get(f"/holidays/{h['id']}", headers=admin_auth)
    # No GET-by-id endpoint, so just confirm the list no longer carries it.
    assert again.status_code == 404 or h["id"] not in [
        item["id"]
        for item in client.get("/holidays", headers=admin_auth).json()["items"]
    ]


def test_post_holiday_requires_manage_capability(client: TestClient) -> None:
    token = _register_and_login(client, "manager", "m@example.com")
    response = client.post(
        "/holidays",
        json={"date": "2026-12-25", "name": "X"},
        headers=_auth(token),
    )
    assert response.status_code == 403


def test_list_holidays_403_for_employee(client: TestClient) -> None:
    token = _register_and_login(client, "employee", "e@example.com")
    response = client.get("/holidays", headers=_auth(token))
    assert response.status_code == 403


def test_holiday_records_audit_event(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    client.post(
        "/holidays",
        json={"date": "2026-12-25", "name": "Christmas"},
        headers=admin_auth,
    )
    items = client.get(
        "/audit-log?action=create_holiday", headers=admin_auth
    ).json()["items"]
    assert len(items) == 1
    assert items[0]["after"]["date"] == "2026-12-25"
