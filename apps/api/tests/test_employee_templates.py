"""F21 — pull fingerprint templates off a device + list stored templates.

Push to other devices is deferred to F21-push, so these tests only cover the
read path (device → DB) and the list path (DB → JSON metadata).
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from tikko.zk.fake import FakeDevice, use_fake_devices


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


def _create_device(
    client: TestClient,
    auth: dict[str, str],
    *,
    name: str = "T1",
    host: str = "10.0.0.50",
) -> dict:
    return client.post(
        "/devices",
        json={"name": name, "host": host, "port": 4370},
        headers=auth,
    ).json()


def test_pull_stores_each_finger_returned_by_the_device(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    employee = _create_employee(client, admin_auth)
    device = _create_device(client, admin_auth, host="10.0.0.50")
    fake = FakeDevice(host="10.0.0.50")
    fake.set_user_template("1042", 0, b"\x00finger-zero")
    fake.set_user_template("1042", 1, b"\x01finger-one")

    with use_fake_devices(fake):
        response = client.post(
            f"/employees/{employee['id']}/templates/pull"
            f"?from_device_id={device['id']}",
            headers=admin_auth,
        )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["stored"] == 2
    assert sorted(body["fingers"]) == [0, 1]


def test_pull_then_list_returns_stored_metadata(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    employee = _create_employee(client, admin_auth)
    device = _create_device(client, admin_auth)
    fake = FakeDevice(host="10.0.0.50")
    fake.set_user_template("1042", 3, b"\x03three")

    with use_fake_devices(fake):
        client.post(
            f"/employees/{employee['id']}/templates/pull"
            f"?from_device_id={device['id']}",
            headers=admin_auth,
        )

    response = client.get(
        f"/employees/{employee['id']}/templates", headers=admin_auth
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    [item] = body["items"]
    assert item["employee_id"] == employee["id"]
    assert item["source_device_id"] == device["id"]
    assert item["finger_id"] == 3
    assert "captured_at" in item
    # The blob is intentionally omitted from list responses.
    assert "template_data" not in item


def test_pull_replaces_previous_rows_for_same_source_device(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    employee = _create_employee(client, admin_auth)
    device = _create_device(client, admin_auth)

    # First pull captures fingers 0+1.
    fake = FakeDevice(host="10.0.0.50")
    fake.set_user_template("1042", 0, b"old-0")
    fake.set_user_template("1042", 1, b"old-1")
    with use_fake_devices(fake):
        client.post(
            f"/employees/{employee['id']}/templates/pull"
            f"?from_device_id={device['id']}",
            headers=admin_auth,
        )

    # Second pull: only finger 2 — should fully replace the first set.
    fake2 = FakeDevice(host="10.0.0.50")
    fake2.set_user_template("1042", 2, b"new-2")
    with use_fake_devices(fake2):
        response = client.post(
            f"/employees/{employee['id']}/templates/pull"
            f"?from_device_id={device['id']}",
            headers=admin_auth,
        )
    assert response.status_code == 200
    assert response.json()["fingers"] == [2]

    listed = client.get(
        f"/employees/{employee['id']}/templates", headers=admin_auth
    ).json()
    assert listed["total"] == 1
    assert listed["items"][0]["finger_id"] == 2


def test_pull_with_no_templates_stored_returns_zero(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    employee = _create_employee(client, admin_auth)
    device = _create_device(client, admin_auth)
    fake = FakeDevice(host="10.0.0.50")  # no templates

    with use_fake_devices(fake):
        response = client.post(
            f"/employees/{employee['id']}/templates/pull"
            f"?from_device_id={device['id']}",
            headers=admin_auth,
        )
    assert response.status_code == 200
    body = response.json()
    assert body["stored"] == 0
    assert body["fingers"] == []


def test_pull_404_when_employee_missing(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    device = _create_device(client, admin_auth)
    response = client.post(
        "/employees/00000000-0000-0000-0000-000000000000/templates/pull"
        f"?from_device_id={device['id']}",
        headers=admin_auth,
    )
    assert response.status_code == 404


def test_pull_404_when_from_device_missing(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    employee = _create_employee(client, admin_auth)
    response = client.post(
        f"/employees/{employee['id']}/templates/pull"
        "?from_device_id=00000000-0000-0000-0000-000000000000",
        headers=admin_auth,
    )
    assert response.status_code == 404


def test_pull_503_when_device_unreachable(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    employee = _create_employee(client, admin_auth)
    device = _create_device(client, admin_auth, host="10.0.0.50")
    with use_fake_devices():  # no fake for 10.0.0.50
        response = client.post(
            f"/employees/{employee['id']}/templates/pull"
            f"?from_device_id={device['id']}",
            headers=admin_auth,
        )
    assert response.status_code == 503


def test_list_404_when_employee_missing(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    response = client.get(
        "/employees/00000000-0000-0000-0000-000000000000/templates",
        headers=admin_auth,
    )
    assert response.status_code == 404


def test_list_empty_when_no_templates(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    employee = _create_employee(client, admin_auth)
    response = client.get(
        f"/employees/{employee['id']}/templates", headers=admin_auth
    )
    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0}


def test_pull_requires_admin_role(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    employee = _create_employee(client, admin_auth)
    device = _create_device(client, admin_auth)
    employee_token = _register_and_login(client, "employee", "e@example.com")
    response = client.post(
        f"/employees/{employee['id']}/templates/pull"
        f"?from_device_id={device['id']}",
        headers=_auth(employee_token),
    )
    assert response.status_code == 403


def test_list_403_for_employee_role(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    employee = _create_employee(client, admin_auth)
    employee_token = _register_and_login(client, "employee", "e@example.com")
    response = client.get(
        f"/employees/{employee['id']}/templates",
        headers=_auth(employee_token),
    )
    assert response.status_code == 403


def test_list_200_for_manager_role(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    employee = _create_employee(client, admin_auth)
    manager_token = _register_and_login(client, "manager", "m@example.com")
    response = client.get(
        f"/employees/{employee['id']}/templates",
        headers=_auth(manager_token),
    )
    assert response.status_code == 200
