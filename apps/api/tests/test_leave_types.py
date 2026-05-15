"""F37 — leave types + balances + balance consumption on approve."""

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


def _create_type(
    client: TestClient,
    auth: dict[str, str],
    name: str = "Annual",
    days: int = 20,
) -> dict:
    return client.post(
        "/leave-types",
        json={"name": name, "days_per_year": days},
        headers=auth,
    ).json()


def test_post_leave_type_creates(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    response = client.post(
        "/leave-types",
        json={"name": "Annual", "days_per_year": 20, "color": "#3b82f6"},
        headers=admin_auth,
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["name"] == "Annual"
    assert body["days_per_year"] == 20


def test_post_leave_type_409_on_duplicate_name(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    _create_type(client, admin_auth)
    second = client.post(
        "/leave-types",
        json={"name": "Annual", "days_per_year": 25},
        headers=admin_auth,
    )
    assert second.status_code == 409


def test_list_leave_types(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    _create_type(client, admin_auth, name="Annual")
    _create_type(client, admin_auth, name="Sick", days=10)
    body = client.get("/leave-types", headers=admin_auth).json()
    assert body["total"] == 2
    assert {it["name"] for it in body["items"]} == {"Annual", "Sick"}


def test_post_leave_type_requires_manage_capability(client: TestClient) -> None:
    token = _register_and_login(client, "manager", "m@example.com")
    response = client.post(
        "/leave-types",
        json={"name": "Annual", "days_per_year": 20},
        headers=_auth(token),
    )
    assert response.status_code == 403


def test_list_leave_types_200_for_manager(client: TestClient) -> None:
    token = _register_and_login(client, "manager", "m@example.com")
    response = client.get("/leave-types", headers=_auth(token))
    assert response.status_code == 200


def test_delete_leave_type_409_when_referenced(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    lt = _create_type(client, admin_auth)
    # Create employee + linked user, then submit a leave request that uses this type.
    employee = client.post(
        "/employees",
        json={"employee_code": "1042", "full_name": "Ada"},
        headers=admin_auth,
    ).json()
    client.post(
        "/auth/register",
        json={
            "email": "ada@example.com",
            "password": "supersecret123",
            "role": "employee",
            "employee_code": employee["employee_code"],
        },
    )
    token = client.post(
        "/auth/login",
        json={"email": "ada@example.com", "password": "supersecret123"},
    ).json()["access_token"]
    client.post(
        "/me/leave-requests",
        json={
            "start_date": "2026-06-01",
            "end_date": "2026-06-05",
            "reason": "trip",
            "leave_type_id": lt["id"],
        },
        headers=_auth(token),
    )

    response = client.delete(f"/leave-types/{lt['id']}", headers=admin_auth)
    assert response.status_code == 409


def test_approve_consumes_balance(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    lt = _create_type(client, admin_auth, days=20)
    # Build employee + user link.
    employee = client.post(
        "/employees",
        json={"employee_code": "1042", "full_name": "Ada"},
        headers=admin_auth,
    ).json()
    client.post(
        "/auth/register",
        json={
            "email": "ada@example.com",
            "password": "supersecret123",
            "role": "employee",
            "employee_code": employee["employee_code"],
        },
    )
    ada_token = client.post(
        "/auth/login",
        json={"email": "ada@example.com", "password": "supersecret123"},
    ).json()["access_token"]

    submitted = client.post(
        "/me/leave-requests",
        json={
            "start_date": "2026-06-01",
            "end_date": "2026-06-05",  # 5 days inclusive
            "reason": "trip",
            "leave_type_id": lt["id"],
        },
        headers=_auth(ada_token),
    ).json()
    assert submitted["leave_type_id"] == lt["id"]
    assert submitted["leave_type_name"] == "Annual"

    decided = client.patch(
        f"/leave-requests/{submitted['id']}/decision",
        json={"decision": "approved"},
        headers=admin_auth,
    )
    assert decided.status_code == 200

    balances = client.get(
        f"/leave-balances?employee_id={employee['id']}&year=2026",
        headers=admin_auth,
    ).json()
    assert balances["total"] == 1
    bal = balances["items"][0]
    assert bal["leave_type_id"] == lt["id"]
    assert bal["allocated_days"] == 20
    assert bal["used_days"] == 5


def test_reject_does_not_consume_balance(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    lt = _create_type(client, admin_auth)
    employee = client.post(
        "/employees",
        json={"employee_code": "1042", "full_name": "Ada"},
        headers=admin_auth,
    ).json()
    client.post(
        "/auth/register",
        json={
            "email": "ada@example.com",
            "password": "supersecret123",
            "role": "employee",
            "employee_code": employee["employee_code"],
        },
    )
    ada_token = client.post(
        "/auth/login",
        json={"email": "ada@example.com", "password": "supersecret123"},
    ).json()["access_token"]
    submitted = client.post(
        "/me/leave-requests",
        json={
            "start_date": "2026-06-01",
            "end_date": "2026-06-05",
            "reason": "trip",
            "leave_type_id": lt["id"],
        },
        headers=_auth(ada_token),
    ).json()
    client.patch(
        f"/leave-requests/{submitted['id']}/decision",
        json={"decision": "rejected"},
        headers=admin_auth,
    )
    balances = client.get(
        f"/leave-balances?employee_id={employee['id']}&year=2026",
        headers=admin_auth,
    ).json()
    assert balances["total"] == 0


def test_admin_can_adjust_allocated_days(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    lt = _create_type(client, admin_auth, days=20)
    employee = client.post(
        "/employees",
        json={"employee_code": "1042", "full_name": "Ada"},
        headers=admin_auth,
    ).json()
    bal = client.post(
        f"/leave-balances?employee_id={employee['id']}&leave_type_id={lt['id']}&year=2026",
        headers=admin_auth,
    ).json()
    assert bal["allocated_days"] == 20

    response = client.patch(
        f"/leave-balances/{bal['id']}",
        json={"allocated_days": 25},
        headers=admin_auth,
    )
    assert response.status_code == 200
    assert response.json()["allocated_days"] == 25


def test_submit_with_unknown_leave_type_id_returns_404(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    employee = client.post(
        "/employees",
        json={"employee_code": "1042", "full_name": "Ada"},
        headers=admin_auth,
    ).json()
    client.post(
        "/auth/register",
        json={
            "email": "ada@example.com",
            "password": "supersecret123",
            "role": "employee",
            "employee_code": employee["employee_code"],
        },
    )
    ada_token = client.post(
        "/auth/login",
        json={"email": "ada@example.com", "password": "supersecret123"},
    ).json()["access_token"]
    response = client.post(
        "/me/leave-requests",
        json={
            "start_date": "2026-06-01",
            "end_date": "2026-06-05",
            "reason": "trip",
            "leave_type_id": "00000000-0000-0000-0000-000000000000",
        },
        headers=_auth(ada_token),
    )
    assert response.status_code == 404
