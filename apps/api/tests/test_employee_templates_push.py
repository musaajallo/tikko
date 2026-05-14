"""F21-push — POST /employees/:id/templates/push.

Reads stored templates from `employee_templates`, picks the latest per finger,
and writes them to each target device via `set_user` + `save_user_templates`.
Per-device failures surface as `status: "failed"` entries, mirroring F20-sync.
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
    name: str,
    host: str,
) -> dict:
    return client.post(
        "/devices",
        json={"name": name, "host": host, "port": 4370},
        headers=auth,
    ).json()


def _pull_from(
    client: TestClient,
    auth: dict[str, str],
    employee_id: str,
    device_id: str,
) -> None:
    response = client.post(
        f"/employees/{employee_id}/templates/pull?from_device_id={device_id}",
        headers=auth,
    )
    assert response.status_code == 200, response.text


def test_push_writes_templates_to_target_device(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    employee = _create_employee(client, admin_auth)
    source = _create_device(client, admin_auth, name="src", host="10.0.0.1")
    target = _create_device(client, admin_auth, name="tgt", host="10.0.0.2")

    # Seed source with two enrolled fingers, pull them so they're stored in the DB.
    source_fake = FakeDevice(host="10.0.0.1")
    source_fake.set_user_template("1042", 0, b"finger-zero")
    source_fake.set_user_template("1042", 1, b"finger-one")
    with use_fake_devices(source_fake):
        _pull_from(client, admin_auth, employee["id"], source["id"])

    # Push to the target — fresh fake with no templates yet.
    target_fake = FakeDevice(host="10.0.0.2")
    with use_fake_devices(target_fake):
        response = client.post(
            f"/employees/{employee['id']}/templates/push",
            json={"device_ids": [target["id"]]},
            headers=admin_auth,
        )

    assert response.status_code == 200, response.text
    body = response.json()
    [entry] = body["results"]
    assert entry["device_id"] == target["id"]
    assert entry["status"] == "pushed"
    assert entry["fingers_pushed"] == 2
    assert entry["error"] is None

    # set_user must have run too (push ensures the user record exists first).
    assert "1042" in target_fake.synced_users
    # And both fingers should now be readable from the target fake.
    assert target_fake.templates["1042"] == {0: b"finger-zero", 1: b"finger-one"}


def test_push_to_multiple_devices(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    employee = _create_employee(client, admin_auth)
    source = _create_device(client, admin_auth, name="src", host="10.0.0.1")
    a = _create_device(client, admin_auth, name="A", host="10.0.0.2")
    b = _create_device(client, admin_auth, name="B", host="10.0.0.3")

    source_fake = FakeDevice(host="10.0.0.1")
    source_fake.set_user_template("1042", 3, b"finger-three")
    with use_fake_devices(source_fake):
        _pull_from(client, admin_auth, employee["id"], source["id"])

    fake_a = FakeDevice(host="10.0.0.2")
    fake_b = FakeDevice(host="10.0.0.3")
    with use_fake_devices(fake_a, fake_b):
        response = client.post(
            f"/employees/{employee['id']}/templates/push",
            json={"device_ids": [a["id"], b["id"]]},
            headers=admin_auth,
        )

    assert response.status_code == 200
    statuses = {r["device_id"]: r["status"] for r in response.json()["results"]}
    assert statuses == {a["id"]: "pushed", b["id"]: "pushed"}
    assert fake_a.templates["1042"][3] == b"finger-three"
    assert fake_b.templates["1042"][3] == b"finger-three"


def test_push_picks_latest_template_per_finger(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    """If two source devices have finger 0, push the most recently captured one."""
    employee = _create_employee(client, admin_auth)
    src_a = _create_device(client, admin_auth, name="srcA", host="10.0.0.1")
    src_b = _create_device(client, admin_auth, name="srcB", host="10.0.0.2")
    target = _create_device(client, admin_auth, name="tgt", host="10.0.0.3")

    # Pull from A first (older).
    fake_a = FakeDevice(host="10.0.0.1")
    fake_a.set_user_template("1042", 0, b"older-from-A")
    with use_fake_devices(fake_a):
        _pull_from(client, admin_auth, employee["id"], src_a["id"])

    # Then pull from B (newer captured_at).
    fake_b = FakeDevice(host="10.0.0.2")
    fake_b.set_user_template("1042", 0, b"newer-from-B")
    with use_fake_devices(fake_b):
        _pull_from(client, admin_auth, employee["id"], src_b["id"])

    target_fake = FakeDevice(host="10.0.0.3")
    with use_fake_devices(target_fake):
        client.post(
            f"/employees/{employee['id']}/templates/push",
            json={"device_ids": [target["id"]]},
            headers=admin_auth,
        )

    assert target_fake.templates["1042"][0] == b"newer-from-B"


def test_push_with_no_stored_templates_returns_zero(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    employee = _create_employee(client, admin_auth)
    target = _create_device(client, admin_auth, name="tgt", host="10.0.0.2")
    target_fake = FakeDevice(host="10.0.0.2")

    with use_fake_devices(target_fake):
        response = client.post(
            f"/employees/{employee['id']}/templates/push",
            json={"device_ids": [target["id"]]},
            headers=admin_auth,
        )
    assert response.status_code == 200
    [entry] = response.json()["results"]
    assert entry["status"] == "pushed"
    assert entry["fingers_pushed"] == 0


def test_push_reports_failure_when_target_unreachable(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    employee = _create_employee(client, admin_auth)
    source = _create_device(client, admin_auth, name="src", host="10.0.0.1")
    target = _create_device(client, admin_auth, name="tgt", host="10.0.0.2")

    source_fake = FakeDevice(host="10.0.0.1")
    source_fake.set_user_template("1042", 0, b"finger")
    with use_fake_devices(source_fake):
        _pull_from(client, admin_auth, employee["id"], source["id"])

    # No fake for 10.0.0.2 → push to target fails.
    with use_fake_devices():
        response = client.post(
            f"/employees/{employee['id']}/templates/push",
            json={"device_ids": [target["id"]]},
            headers=admin_auth,
        )
    assert response.status_code == 200, response.text
    [entry] = response.json()["results"]
    assert entry["status"] == "failed"
    assert entry["error"] is not None


def test_push_mixed_success_and_failure(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    employee = _create_employee(client, admin_auth)
    source = _create_device(client, admin_auth, name="src", host="10.0.0.1")
    a = _create_device(client, admin_auth, name="A", host="10.0.0.2")
    b = _create_device(client, admin_auth, name="B", host="10.0.0.3")

    source_fake = FakeDevice(host="10.0.0.1")
    source_fake.set_user_template("1042", 0, b"finger")
    with use_fake_devices(source_fake):
        _pull_from(client, admin_auth, employee["id"], source["id"])

    # Only A registered.
    with use_fake_devices(FakeDevice(host="10.0.0.2")):
        response = client.post(
            f"/employees/{employee['id']}/templates/push",
            json={"device_ids": [a["id"], b["id"]]},
            headers=admin_auth,
        )
    assert response.status_code == 200
    by_id = {r["device_id"]: r for r in response.json()["results"]}
    assert by_id[a["id"]]["status"] == "pushed"
    assert by_id[b["id"]]["status"] == "failed"


def test_push_404_when_employee_missing(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    device = _create_device(client, admin_auth, name="t", host="10.0.0.1")
    response = client.post(
        "/employees/00000000-0000-0000-0000-000000000000/templates/push",
        json={"device_ids": [device["id"]]},
        headers=admin_auth,
    )
    assert response.status_code == 404


def test_push_400_when_device_id_unknown(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    employee = _create_employee(client, admin_auth)
    response = client.post(
        f"/employees/{employee['id']}/templates/push",
        json={"device_ids": ["00000000-0000-0000-0000-000000000000"]},
        headers=admin_auth,
    )
    assert response.status_code == 400


def test_push_422_on_empty_device_ids(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    employee = _create_employee(client, admin_auth)
    response = client.post(
        f"/employees/{employee['id']}/templates/push",
        json={"device_ids": []},
        headers=admin_auth,
    )
    assert response.status_code == 422


def test_push_requires_admin_role(
    client: TestClient, admin_auth: dict[str, str]
) -> None:
    employee = _create_employee(client, admin_auth)
    device = _create_device(client, admin_auth, name="t", host="10.0.0.1")
    employee_token = _register_and_login(client, "employee", "e@example.com")
    response = client.post(
        f"/employees/{employee['id']}/templates/push",
        json={"device_ids": [device["id"]]},
        headers=_auth(employee_token),
    )
    assert response.status_code == 403


def test_push_requires_auth(client: TestClient) -> None:
    response = client.post(
        "/employees/00000000-0000-0000-0000-000000000000/templates/push",
        json={"device_ids": []},
    )
    assert response.status_code == 401
