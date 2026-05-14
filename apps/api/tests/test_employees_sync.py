"""F20-sync — POST /employees/:id/sync drives ZKClient.set_user against the F19 harness.

Per-device connect failures surface as `status: "failed"` entries in the response —
they do **not** turn the whole call into a 5xx, so partial sync is observable to the caller.
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


def test_sync_to_one_device_records_user_on_fake(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    employee = _create_employee(client, admin_auth)
    device = _create_device(client, admin_auth, host="10.0.0.50")
    fake = FakeDevice(host="10.0.0.50")

    with use_fake_devices(fake):
        response = client.post(
            f"/employees/{employee['id']}/sync",
            json={"device_ids": [device["id"]]},
            headers=admin_auth,
        )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["results"] == [
        {"device_id": device["id"], "status": "synced", "error": None}
    ]

    assert "1042" in fake.synced_users
    recorded = fake.synced_users["1042"]
    assert recorded.user_id == "1042"
    assert recorded.uid == 1042
    assert recorded.name == "Ada Lovelace"


def test_sync_to_multiple_devices_all_synced(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    employee = _create_employee(client, admin_auth)
    a = _create_device(client, admin_auth, name="A", host="10.0.0.1")
    b = _create_device(client, admin_auth, name="B", host="10.0.0.2")
    fake_a = FakeDevice(host="10.0.0.1")
    fake_b = FakeDevice(host="10.0.0.2")

    with use_fake_devices(fake_a, fake_b):
        response = client.post(
            f"/employees/{employee['id']}/sync",
            json={"device_ids": [a["id"], b["id"]]},
            headers=admin_auth,
        )

    assert response.status_code == 200
    statuses = {r["device_id"]: r["status"] for r in response.json()["results"]}
    assert statuses == {a["id"]: "synced", b["id"]: "synced"}
    assert "1042" in fake_a.synced_users
    assert "1042" in fake_b.synced_users


def test_sync_preserves_request_device_order(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    employee = _create_employee(client, admin_auth)
    a = _create_device(client, admin_auth, name="A", host="10.0.0.1")
    b = _create_device(client, admin_auth, name="B", host="10.0.0.2")

    with use_fake_devices(FakeDevice(host="10.0.0.1"), FakeDevice(host="10.0.0.2")):
        response = client.post(
            f"/employees/{employee['id']}/sync",
            json={"device_ids": [b["id"], a["id"]]},
            headers=admin_auth,
        )

    assert response.status_code == 200
    ordered = [r["device_id"] for r in response.json()["results"]]
    assert ordered == [b["id"], a["id"]]


def test_sync_reports_failure_when_device_unreachable(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    employee = _create_employee(client, admin_auth)
    device = _create_device(client, admin_auth, host="10.0.0.50")

    # No FakeDevice registered for 10.0.0.50 → FakeZK.connect raises.
    with use_fake_devices():
        response = client.post(
            f"/employees/{employee['id']}/sync",
            json={"device_ids": [device["id"]]},
            headers=admin_auth,
        )

    assert response.status_code == 200, response.text
    entry = response.json()["results"][0]
    assert entry["device_id"] == device["id"]
    assert entry["status"] == "failed"
    assert entry["error"] is not None
    assert "10.0.0.50" in entry["error"]


def test_sync_mixed_success_and_failure(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    employee = _create_employee(client, admin_auth)
    a = _create_device(client, admin_auth, name="A", host="10.0.0.1")
    b = _create_device(client, admin_auth, name="B", host="10.0.0.2")

    # Only A has a fake.
    with use_fake_devices(FakeDevice(host="10.0.0.1")):
        response = client.post(
            f"/employees/{employee['id']}/sync",
            json={"device_ids": [a["id"], b["id"]]},
            headers=admin_auth,
        )

    assert response.status_code == 200
    by_id = {r["device_id"]: r for r in response.json()["results"]}
    assert by_id[a["id"]]["status"] == "synced"
    assert by_id[b["id"]]["status"] == "failed"
    assert by_id[b["id"]]["error"] is not None


def test_sync_404_when_employee_missing(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    device = _create_device(client, admin_auth)
    response = client.post(
        "/employees/00000000-0000-0000-0000-000000000000/sync",
        json={"device_ids": [device["id"]]},
        headers=admin_auth,
    )
    assert response.status_code == 404


def test_sync_400_when_device_id_unknown(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    employee = _create_employee(client, admin_auth)
    response = client.post(
        f"/employees/{employee['id']}/sync",
        json={"device_ids": ["00000000-0000-0000-0000-000000000000"]},
        headers=admin_auth,
    )
    assert response.status_code == 400


def test_sync_422_on_empty_device_ids(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    employee = _create_employee(client, admin_auth)
    response = client.post(
        f"/employees/{employee['id']}/sync",
        json={"device_ids": []},
        headers=admin_auth,
    )
    assert response.status_code == 422


def test_sync_requires_admin_role(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    employee = _create_employee(client, admin_auth)
    device = _create_device(client, admin_auth)
    employee_token = _register_and_login(client, "employee", "e@example.com")

    response = client.post(
        f"/employees/{employee['id']}/sync",
        json={"device_ids": [device["id"]]},
        headers=_auth(employee_token),
    )
    assert response.status_code == 403


def test_sync_requires_auth(client: TestClient) -> None:
    response = client.post(
        "/employees/00000000-0000-0000-0000-000000000000/sync",
        json={"device_ids": []},
    )
    assert response.status_code == 401
