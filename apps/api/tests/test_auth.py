"""Auth: register, login, JWT issuance."""

from __future__ import annotations

import jwt
from fastapi.testclient import TestClient

from tikko.settings import get_settings


def test_register_creates_user_and_returns_safe_fields(client: TestClient) -> None:
    response = client.post(
        "/auth/register",
        json={
            "email": "admin@example.com",
            "password": "supersecret123",
            "role": "admin",
        },
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["email"] == "admin@example.com"
    assert body["role"] == "admin"
    assert isinstance(body["id"], str) and len(body["id"]) == 36
    # Never return the hash or password.
    assert "password" not in body
    assert "password_hash" not in body


def test_register_default_role_is_employee(client: TestClient) -> None:
    response = client.post(
        "/auth/register",
        json={"email": "e@example.com", "password": "supersecret123"},
    )
    assert response.status_code == 201, response.text
    assert response.json()["role"] == "employee"


def test_register_rejects_duplicate_email(client: TestClient) -> None:
    payload = {"email": "dup@example.com", "password": "supersecret123"}
    client.post("/auth/register", json=payload)

    response = client.post("/auth/register", json=payload)
    assert response.status_code == 409


def test_register_rejects_short_password(client: TestClient) -> None:
    response = client.post(
        "/auth/register",
        json={"email": "x@example.com", "password": "short"},
    )
    assert response.status_code == 422


def test_login_returns_tokens_for_valid_credentials(client: TestClient) -> None:
    client.post(
        "/auth/register",
        json={"email": "u@example.com", "password": "supersecret123", "role": "manager"},
    )

    response = client.post(
        "/auth/login",
        json={"email": "u@example.com", "password": "supersecret123"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str) and body["access_token"]
    assert isinstance(body["refresh_token"], str) and body["refresh_token"]


def test_login_token_carries_subject_and_role(client: TestClient) -> None:
    register = client.post(
        "/auth/register",
        json={"email": "claims@example.com", "password": "supersecret123", "role": "manager"},
    ).json()

    login = client.post(
        "/auth/login",
        json={"email": "claims@example.com", "password": "supersecret123"},
    ).json()

    settings = get_settings()
    claims = jwt.decode(login["access_token"], settings.jwt_secret, algorithms=["HS256"])
    assert claims["sub"] == register["id"]
    assert claims["role"] == "manager"
    assert claims["type"] == "access"


def test_login_rejects_wrong_password(client: TestClient) -> None:
    client.post(
        "/auth/register",
        json={"email": "wrong@example.com", "password": "supersecret123"},
    )

    response = client.post(
        "/auth/login",
        json={"email": "wrong@example.com", "password": "nope-not-it"},
    )
    assert response.status_code == 401


def test_login_rejects_unknown_email(client: TestClient) -> None:
    response = client.post(
        "/auth/login",
        json={"email": "ghost@example.com", "password": "supersecret123"},
    )
    assert response.status_code == 401
