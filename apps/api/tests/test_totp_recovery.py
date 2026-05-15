"""F30-recovery — backup codes generated at enroll, redeemable at login, regeneratable."""

from __future__ import annotations

import pyotp
from fastapi.testclient import TestClient


def _register_and_login(
    client: TestClient,
    *,
    role: str = "admin",
    email: str = "u@example.com",
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


def _enroll_and_enable(client: TestClient, token: str) -> tuple[str, list[str]]:
    enroll = client.post("/auth/totp/enroll", headers=_auth(token)).json()
    secret = enroll["secret"]
    verify_body = client.post(
        "/auth/totp/verify",
        json={"code": pyotp.TOTP(secret).now()},
        headers=_auth(token),
    ).json()
    return secret, verify_body["recovery_codes"]


def test_verify_response_includes_ten_recovery_codes(client: TestClient) -> None:
    token = _register_and_login(client)
    enroll = client.post("/auth/totp/enroll", headers=_auth(token)).json()
    response = client.post(
        "/auth/totp/verify",
        json={"code": pyotp.TOTP(enroll["secret"]).now()},
        headers=_auth(token),
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["enabled"] is True
    assert isinstance(body["recovery_codes"], list)
    assert len(body["recovery_codes"]) == 10
    # No duplicates.
    assert len(set(body["recovery_codes"])) == 10


def test_recovery_code_can_be_used_to_login(client: TestClient) -> None:
    token = _register_and_login(client, email="rc1@example.com")
    _secret, codes = _enroll_and_enable(client, token)

    response = client.post(
        "/auth/login",
        json={
            "email": "rc1@example.com",
            "password": "supersecret123",
            "totp_code": codes[0],
        },
    )
    assert response.status_code == 200, response.text
    assert "access_token" in response.json()


def test_recovery_code_is_single_use(client: TestClient) -> None:
    token = _register_and_login(client, email="rc2@example.com")
    _secret, codes = _enroll_and_enable(client, token)

    first = client.post(
        "/auth/login",
        json={
            "email": "rc2@example.com",
            "password": "supersecret123",
            "totp_code": codes[0],
        },
    )
    assert first.status_code == 200

    # Same code, again → rejected.
    second = client.post(
        "/auth/login",
        json={
            "email": "rc2@example.com",
            "password": "supersecret123",
            "totp_code": codes[0],
        },
    )
    assert second.status_code == 401


def test_bad_totp_code_does_not_open_recovery_door(client: TestClient) -> None:
    token = _register_and_login(client, email="rc3@example.com")
    _enroll_and_enable(client, token)

    response = client.post(
        "/auth/login",
        json={
            "email": "rc3@example.com",
            "password": "supersecret123",
            "totp_code": "ffffffffff",  # 10 hex chars but never generated for this user
        },
    )
    assert response.status_code == 401


def test_regenerate_returns_new_codes_and_invalidates_old(client: TestClient) -> None:
    token = _register_and_login(client, email="rc4@example.com")
    _secret, original_codes = _enroll_and_enable(client, token)

    new_body = client.post(
        "/auth/totp/recovery-codes/regenerate",
        json={"password": "supersecret123"},
        headers=_auth(token),
    ).json()
    assert isinstance(new_body["recovery_codes"], list)
    assert len(new_body["recovery_codes"]) == 10
    # No overlap.
    assert set(new_body["recovery_codes"]).isdisjoint(set(original_codes))

    # An old code no longer works.
    rejected = client.post(
        "/auth/login",
        json={
            "email": "rc4@example.com",
            "password": "supersecret123",
            "totp_code": original_codes[0],
        },
    )
    assert rejected.status_code == 401

    # A new code does.
    accepted = client.post(
        "/auth/login",
        json={
            "email": "rc4@example.com",
            "password": "supersecret123",
            "totp_code": new_body["recovery_codes"][0],
        },
    )
    assert accepted.status_code == 200


def test_regenerate_requires_password(client: TestClient) -> None:
    token = _register_and_login(client, email="rc5@example.com")
    _enroll_and_enable(client, token)
    response = client.post(
        "/auth/totp/recovery-codes/regenerate",
        json={"password": "wrong-one"},
        headers=_auth(token),
    )
    assert response.status_code == 401


def test_disable_clears_recovery_codes(client: TestClient) -> None:
    token = _register_and_login(client, email="rc6@example.com")
    _secret, codes = _enroll_and_enable(client, token)

    client.post(
        "/auth/totp/disable",
        json={"password": "supersecret123"},
        headers=_auth(token),
    )

    # TOTP is off, so login doesn't need any code at all.
    bare = client.post(
        "/auth/login",
        json={"email": "rc6@example.com", "password": "supersecret123"},
    )
    assert bare.status_code == 200

    # And if someone re-enrolls and tries an old code, it should still be dead.
    new_token = client.post(
        "/auth/login",
        json={"email": "rc6@example.com", "password": "supersecret123"},
    ).json()["access_token"]
    enroll = client.post("/auth/totp/enroll", headers=_auth(new_token)).json()
    _new_secret = enroll["secret"]
    new_codes = client.post(
        "/auth/totp/verify",
        json={"code": pyotp.TOTP(_new_secret).now()},
        headers=_auth(new_token),
    ).json()["recovery_codes"]
    # Old codes should not appear in the new set.
    assert set(codes).isdisjoint(set(new_codes))
