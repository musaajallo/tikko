"""F33 — Department CRUD + employee assignment + hierarchy guards."""

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


def _create_dept(
    client: TestClient,
    auth: dict[str, str],
    name: str = "Engineering",
    parent_id: str | None = None,
) -> dict:
    body: dict = {"name": name}
    if parent_id is not None:
        body["parent_id"] = parent_id
    return client.post("/departments", json=body, headers=auth).json()


def test_post_department_creates_minimal(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    response = client.post(
        "/departments", json={"name": "Engineering"}, headers=admin_auth
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["name"] == "Engineering"
    assert body["parent_id"] is None
    assert isinstance(body["id"], str) and len(body["id"]) == 36


def test_post_department_with_parent(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    parent = _create_dept(client, admin_auth, name="HQ")
    child = client.post(
        "/departments",
        json={"name": "Engineering", "parent_id": parent["id"]},
        headers=admin_auth,
    ).json()
    assert child["parent_id"] == parent["id"]


def test_post_department_404_when_parent_unknown(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    response = client.post(
        "/departments",
        json={
            "name": "Orphan",
            "parent_id": "00000000-0000-0000-0000-000000000000",
        },
        headers=admin_auth,
    )
    assert response.status_code == 404


def test_get_departments_lists_with_total(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    _create_dept(client, admin_auth, name="A")
    _create_dept(client, admin_auth, name="B")
    body = client.get("/departments", headers=admin_auth).json()
    assert body["total"] == 2
    names = {item["name"] for item in body["items"]}
    assert names == {"A", "B"}


def test_patch_department_renames(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    dept = _create_dept(client, admin_auth)
    response = client.patch(
        f"/departments/{dept['id']}",
        json={"name": "Platform"},
        headers=admin_auth,
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Platform"


def test_patch_department_rejects_self_parent(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    dept = _create_dept(client, admin_auth)
    response = client.patch(
        f"/departments/{dept['id']}",
        json={"parent_id": dept["id"]},
        headers=admin_auth,
    )
    assert response.status_code == 422


def test_delete_department_409_when_employees_assigned(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    dept = _create_dept(client, admin_auth)
    employee = client.post(
        "/employees",
        json={"employee_code": "1042", "full_name": "Ada"},
        headers=admin_auth,
    ).json()
    client.patch(
        f"/employees/{employee['id']}",
        json={"department_id": dept["id"]},
        headers=admin_auth,
    )
    response = client.delete(f"/departments/{dept['id']}", headers=admin_auth)
    assert response.status_code == 409


def test_delete_department_409_when_child_exists(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    parent = _create_dept(client, admin_auth, name="HQ")
    _create_dept(client, admin_auth, name="Eng", parent_id=parent["id"])
    response = client.delete(f"/departments/{parent['id']}", headers=admin_auth)
    assert response.status_code == 409


def test_assign_department_via_patch_employee(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    dept = _create_dept(client, admin_auth)
    employee = client.post(
        "/employees",
        json={"employee_code": "1042", "full_name": "Ada"},
        headers=admin_auth,
    ).json()
    assert employee["department_id"] is None

    response = client.patch(
        f"/employees/{employee['id']}",
        json={"department_id": dept["id"]},
        headers=admin_auth,
    )
    assert response.status_code == 200
    assert response.json()["department_id"] == dept["id"]


def test_detach_department_via_patch_employee_with_null(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    dept = _create_dept(client, admin_auth)
    employee = client.post(
        "/employees",
        json={
            "employee_code": "1042",
            "full_name": "Ada",
            "department_id": dept["id"],
        },
        headers=admin_auth,
    ).json()
    assert employee["department_id"] == dept["id"]

    response = client.patch(
        f"/employees/{employee['id']}",
        json={"department_id": None},
        headers=admin_auth,
    )
    assert response.status_code == 200
    assert response.json()["department_id"] is None


def test_assign_unknown_department_404(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    employee = client.post(
        "/employees",
        json={"employee_code": "1042", "full_name": "Ada"},
        headers=admin_auth,
    ).json()
    response = client.patch(
        f"/employees/{employee['id']}",
        json={"department_id": "00000000-0000-0000-0000-000000000000"},
        headers=admin_auth,
    )
    assert response.status_code == 404


def test_post_department_requires_manage_capability(client: TestClient) -> None:
    token = _register_and_login(client, "manager", "m@example.com")
    response = client.post(
        "/departments", json={"name": "X"}, headers=_auth(token)
    )
    # Manager has view_departments but not manage_departments by default.
    assert response.status_code == 403


def test_list_departments_200_for_manager(client: TestClient) -> None:
    token = _register_and_login(client, "manager", "m@example.com")
    response = client.get("/departments", headers=_auth(token))
    assert response.status_code == 200


def test_list_departments_403_for_employee(client: TestClient) -> None:
    token = _register_and_login(client, "employee", "e@example.com")
    response = client.get("/departments", headers=_auth(token))
    assert response.status_code == 403
