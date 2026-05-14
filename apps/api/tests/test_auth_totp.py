"""F30 — TOTP enrollment + verification + admin login enforcement.

Recovery codes are out of scope — that's F30-recovery.
"""

from __future__ import annotations

import pyotp
from fastapi.testclient import TestClient


def _register_and_login(
    client: TestClient,
    *,
    role: str = "admin",
    email: str = "admin2@example.com",
) -> str:
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


def test_enroll_returns_secret_and_otpauth_uri(client: TestClient) -> None:
    token = _register_and_login(client)
    response = client.post("/auth/totp/enroll", headers=_auth(token))
    assert response.status_code == 200, response.text
    body = response.json()
    assert "secret" in body
    assert len(body["secret"]) >= 16  # base32, typically 32 chars
    assert body["otpauth_uri"].startswith("otpauth://totp/")
    # `enabled` should still be false until /verify confirms.
    assert body["enabled"] is False


def test_verify_with_correct_code_enables_totp(client: TestClient) -> None:
    token = _register_and_login(client)
    enroll = client.post("/auth/totp/enroll", headers=_auth(token)).json()

    code = pyotp.TOTP(enroll["secret"]).now()
    response = client.post(
        "/auth/totp/verify",
        json={"code": code},
        headers=_auth(token),
    )
    assert response.status_code == 200, response.text
    assert response.json()["enabled"] is True


def test_verify_with_wrong_code_returns_422(client: TestClient) -> None:
    token = _register_and_login(client)
    client.post("/auth/totp/enroll", headers=_auth(token))
    response = client.post(
        "/auth/totp/verify",
        json={"code": "000000"},
        headers=_auth(token),
    )
    assert response.status_code == 422


def test_verify_without_prior_enroll_returns_404(client: TestClient) -> None:
    token = _register_and_login(client)
    response = client.post(
        "/auth/totp/verify",
        json={"code": "123456"},
        headers=_auth(token),
    )
    assert response.status_code == 404


def test_admin_login_requires_totp_code_when_enabled(client: TestClient) -> None:
    token = _register_and_login(client, email="admin-totp@example.com")
    enroll = client.post("/auth/totp/enroll", headers=_auth(token)).json()
    code = pyotp.TOTP(enroll["secret"]).now()
    client.post(
        "/auth/totp/verify",
        json={"code": code},
        headers=_auth(token),
    )

    # Login without TOTP code — should be denied.
    bare = client.post(
        "/auth/login",
        json={"email": "admin-totp@example.com", "password": "supersecret123"},
    )
    assert bare.status_code == 401
    assert "totp" in bare.json().get("detail", "").lower()


def test_admin_login_succeeds_with_correct_totp_code(client: TestClient) -> None:
    token = _register_and_login(client, email="admin-totp2@example.com")
    enroll = client.post("/auth/totp/enroll", headers=_auth(token)).json()
    secret = enroll["secret"]
    client.post(
        "/auth/totp/verify",
        json={"code": pyotp.TOTP(secret).now()},
        headers=_auth(token),
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "admin-totp2@example.com",
            "password": "supersecret123",
            "totp_code": pyotp.TOTP(secret).now(),
        },
    )
    assert response.status_code == 200, response.text
    assert "access_token" in response.json()


def test_admin_login_with_bad_totp_code_returns_401(client: TestClient) -> None:
    token = _register_and_login(client, email="admin-totp3@example.com")
    enroll = client.post("/auth/totp/enroll", headers=_auth(token)).json()
    client.post(
        "/auth/totp/verify",
        json={"code": pyotp.TOTP(enroll["secret"]).now()},
        headers=_auth(token),
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "admin-totp3@example.com",
            "password": "supersecret123",
            "totp_code": "000000",
        },
    )
    assert response.status_code == 401


def test_employee_login_does_not_require_totp_even_if_enrolled(
    client: TestClient,
) -> None:
    """TOTP is required only for admins. An employee with TOTP enrolled can still log in
    with email + password alone."""
    token = _register_and_login(client, role="employee", email="emp-totp@example.com")
    enroll = client.post("/auth/totp/enroll", headers=_auth(token)).json()
    client.post(
        "/auth/totp/verify",
        json={"code": pyotp.TOTP(enroll["secret"]).now()},
        headers=_auth(token),
    )

    response = client.post(
        "/auth/login",
        json={"email": "emp-totp@example.com", "password": "supersecret123"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_admin_without_enrolled_totp_logs_in_normally(client: TestClient) -> None:
    _register_and_login(client, email="bare-admin@example.com")
    response = client.post(
        "/auth/login",
        json={"email": "bare-admin@example.com", "password": "supersecret123"},
    )
    assert response.status_code == 200


def test_disable_requires_password(client: TestClient) -> None:
    token = _register_and_login(client, email="disable-totp@example.com")
    enroll = client.post("/auth/totp/enroll", headers=_auth(token)).json()
    client.post(
        "/auth/totp/verify",
        json={"code": pyotp.TOTP(enroll["secret"]).now()},
        headers=_auth(token),
    )

    # Wrong password → 401.
    bad = client.post(
        "/auth/totp/disable",
        json={"password": "wrong-password"},
        headers=_auth(token),
    )
    assert bad.status_code == 401

    # Right password → 204.
    ok = client.post(
        "/auth/totp/disable",
        json={"password": "supersecret123"},
        headers=_auth(token),
    )
    assert ok.status_code == 204

    # Login no longer demands the code.
    response = client.post(
        "/auth/login",
        json={"email": "disable-totp@example.com", "password": "supersecret123"},
    )
    assert response.status_code == 200


def test_enroll_requires_auth(client: TestClient) -> None:
    response = client.post("/auth/totp/enroll")
    assert response.status_code == 401


def test_verify_requires_auth(client: TestClient) -> None:
    response = client.post("/auth/totp/verify", json={"code": "123456"})
    assert response.status_code == 401
