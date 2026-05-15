"""F36 — bulk employee import via CSV upload."""

from __future__ import annotations

import io

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


def _post_csv(client: TestClient, auth: dict[str, str], csv_text: str) -> dict:
    return client.post(
        "/employees/import",
        files={"file": ("import.csv", io.BytesIO(csv_text.encode()), "text/csv")},
        headers=auth,
    ).json()


def test_import_happy_path_creates_rows(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    csv_text = (
        "employee_code,full_name\n"
        "1001,Ada Lovelace\n"
        "1002,Grace Hopper\n"
    )
    body = _post_csv(client, admin_auth, csv_text)
    assert body["created"] == 2
    assert body["skipped"] == 0
    assert body["failed"] == 0
    assert all(r["status"] == "created" for r in body["rows"])


def test_import_skips_existing_codes(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    client.post(
        "/employees",
        json={"employee_code": "1001", "full_name": "Ada"},
        headers=admin_auth,
    )
    body = _post_csv(
        client,
        admin_auth,
        "employee_code,full_name\n1001,Ada Lovelace\n1002,Grace Hopper\n",
    )
    assert body["created"] == 1
    assert body["skipped"] == 1
    statuses = {r["status"] for r in body["rows"]}
    assert statuses == {"skipped", "created"}


def test_import_422_when_required_column_missing(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    response = client.post(
        "/employees/import",
        files={
            "file": (
                "bad.csv",
                io.BytesIO(b"full_name\nAda\n"),
                "text/csv",
            )
        },
        headers=admin_auth,
    )
    assert response.status_code == 422
    assert "employee_code" in response.text


def test_import_marks_bad_rows_failed(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    csv_text = (
        "employee_code,full_name\n"
        "1001,Ada\n"
        "ABC,Bad Code\n"          # not all digits
        ",Missing Code\n"          # blank code
        "1002,\n"                 # blank name
    )
    body = _post_csv(client, admin_auth, csv_text)
    assert body["created"] == 1
    assert body["failed"] == 3


def test_import_resolves_department_by_name(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    dept = client.post(
        "/departments", json={"name": "Engineering"}, headers=admin_auth
    ).json()

    body = _post_csv(
        client,
        admin_auth,
        "employee_code,full_name,department_name\n"
        "1001,Ada Lovelace,engineering\n",
    )
    assert body["created"] == 1
    emp_id = body["rows"][0]["employee_id"]
    emp = client.get(f"/employees/{emp_id}", headers=admin_auth).json()
    assert emp["department_id"] == dept["id"]


def test_import_fails_row_when_department_name_unknown(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    body = _post_csv(
        client,
        admin_auth,
        "employee_code,full_name,department_name\n"
        "1001,Ada Lovelace,Nonexistent\n",
    )
    assert body["created"] == 0
    assert body["failed"] == 1
    assert "Nonexistent" in body["rows"][0]["error"]


def test_import_requires_manage_employees(client: TestClient) -> None:
    token = _register_and_login(client, "manager", "m@example.com")
    response = client.post(
        "/employees/import",
        files={
            "file": (
                "x.csv",
                io.BytesIO(b"employee_code,full_name\n1,a\n"),
                "text/csv",
            )
        },
        headers=_auth(token),
    )
    assert response.status_code == 403


def test_import_audits_each_created_row(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    _post_csv(
        client,
        admin_auth,
        "employee_code,full_name\n1001,Ada\n1002,Grace\n",
    )
    audit = client.get(
        "/audit-log?action=create_employee&resource_type=employee",
        headers=admin_auth,
    ).json()
    assert audit["total"] == 2
