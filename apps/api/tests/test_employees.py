"""Employees API — CRUD (F20 part 1; sync deferred to F20-sync).

Auth model mirrors `/devices`:
- POST / PATCH / DELETE — admin
- GET (list + one) — admin or manager
"""

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


def test_post_employee_creates_and_defaults_status_to_active(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    response = client.post(
        "/employees",
        json={"employee_code": "1042", "full_name": "Ada Lovelace"},
        headers=admin_auth,
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["employee_code"] == "1042"
    assert body["full_name"] == "Ada Lovelace"
    assert body["status"] == "active"
    assert isinstance(body["id"], str) and len(body["id"]) == 36
    assert "created_at" in body


def test_post_employee_rejects_non_numeric_code(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    response = client.post(
        "/employees",
        json={"employee_code": "ABC-1", "full_name": "x"},
        headers=admin_auth,
    )
    assert response.status_code == 422


def test_post_employee_rejects_duplicate_code(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    _create_employee(client, admin_auth, code="1042")
    response = client.post(
        "/employees",
        json={"employee_code": "1042", "full_name": "Other"},
        headers=admin_auth,
    )
    assert response.status_code == 409


def test_get_employees_lists_with_total_and_items(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    _create_employee(client, admin_auth, code="1", name="A")
    _create_employee(client, admin_auth, code="2", name="B")

    response = client.get("/employees", headers=admin_auth)

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    codes = {item["employee_code"] for item in body["items"]}
    assert codes == {"1", "2"}


def test_get_employees_pagination(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    for i in range(3):
        _create_employee(client, admin_auth, code=str(100 + i), name=f"E{i}")

    response = client.get(
        "/employees?page=1&page_size=2", headers=admin_auth
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert len(body["items"]) == 2


def test_get_employee_by_id_returns_one(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    created = _create_employee(client, admin_auth)
    response = client.get(f"/employees/{created['id']}", headers=admin_auth)
    assert response.status_code == 200
    assert response.json()["employee_code"] == "1042"


def test_get_employee_by_unknown_id_returns_404(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    response = client.get(
        "/employees/00000000-0000-0000-0000-000000000000", headers=admin_auth
    )
    assert response.status_code == 404


def test_patch_employee_updates_full_name(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    created = _create_employee(client, admin_auth)
    response = client.patch(
        f"/employees/{created['id']}",
        json={"full_name": "Ada L. Byron"},
        headers=admin_auth,
    )
    assert response.status_code == 200, response.text
    assert response.json()["full_name"] == "Ada L. Byron"


def test_patch_employee_updates_status(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    created = _create_employee(client, admin_auth)
    response = client.patch(
        f"/employees/{created['id']}",
        json={"status": "terminated"},
        headers=admin_auth,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "terminated"


def test_patch_employee_rejects_unknown_status(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    created = _create_employee(client, admin_auth)
    response = client.patch(
        f"/employees/{created['id']}",
        json={"status": "ghosted"},
        headers=admin_auth,
    )
    assert response.status_code == 422


def test_patch_employee_unknown_returns_404(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    response = client.patch(
        "/employees/00000000-0000-0000-0000-000000000000",
        json={"full_name": "X"},
        headers=admin_auth,
    )
    assert response.status_code == 404


def test_delete_employee_removes_row(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    created = _create_employee(client, admin_auth)
    delete_resp = client.delete(
        f"/employees/{created['id']}", headers=admin_auth
    )
    assert delete_resp.status_code == 204

    get_resp = client.get(f"/employees/{created['id']}", headers=admin_auth)
    assert get_resp.status_code == 404


def test_delete_employee_unknown_returns_404(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    response = client.delete(
        "/employees/00000000-0000-0000-0000-000000000000", headers=admin_auth
    )
    assert response.status_code == 404


def test_employees_requires_auth(client: TestClient) -> None:
    response = client.get("/employees")
    assert response.status_code == 401


def test_post_employees_requires_admin_role(client: TestClient) -> None:
    token = _register_and_login(client, "employee", "e@example.com")
    response = client.post(
        "/employees",
        json={"employee_code": "1", "full_name": "X"},
        headers=_auth(token),
    )
    assert response.status_code == 403


def test_manager_can_list_employees(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    _create_employee(client, admin_auth)
    manager_token = _register_and_login(client, "manager", "m@example.com")
    response = client.get("/employees", headers=_auth(manager_token))
    assert response.status_code == 200
    assert response.json()["total"] == 1
