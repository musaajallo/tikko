"""Resend integration is a fire-and-forget background task. These tests
patch `tikko.email.send_email` and assert the right events trigger it
with the right arguments.
"""

from __future__ import annotations

import pyotp
from fastapi.testclient import TestClient
from pytest import MonkeyPatch


def _record_sends(monkeypatch: MonkeyPatch) -> list[dict[str, object]]:
    """Replace tikko.email.send_email with a recorder; return the call log.

    The route handlers import `send_email` by name at module load, so we
    patch each call-site's binding rather than the canonical reference.
    """
    sends: list[dict[str, object]] = []

    async def _fake(*, to: str, subject: str, html: str, text: str | None = None) -> None:
        sends.append({"to": to, "subject": subject, "html": html, "text": text})

    import tikko.email as email_mod
    import tikko.routes.auth as auth_route
    import tikko.routes.leave_requests as leave_route
    import tikko.routes.me as me_route
    import tikko.routes.totp as totp_route

    monkeypatch.setattr(email_mod, "send_email", _fake)
    monkeypatch.setattr(auth_route, "send_email", _fake)
    monkeypatch.setattr(totp_route, "send_email", _fake)
    monkeypatch.setattr(me_route, "send_email", _fake)
    monkeypatch.setattr(leave_route, "send_email", _fake)
    return sends


def test_register_sends_welcome_email(
    client: TestClient, monkeypatch: MonkeyPatch
) -> None:
    sends = _record_sends(monkeypatch)
    client.post(
        "/auth/register",
        json={"email": "welcome@example.com", "password": "supersecret123", "role": "employee"},
    )
    welcome = [s for s in sends if s["to"] == "welcome@example.com"]
    assert len(welcome) == 1
    assert "Welcome" in str(welcome[0]["subject"])


def test_change_password_sends_confirmation(
    client: TestClient, monkeypatch: MonkeyPatch
) -> None:
    client.post(
        "/auth/register",
        json={"email": "pw@example.com", "password": "supersecret123", "role": "employee"},
    )
    token = client.post(
        "/auth/login",
        json={"email": "pw@example.com", "password": "supersecret123"},
    ).json()["access_token"]

    sends = _record_sends(monkeypatch)
    client.post(
        "/auth/change-password",
        json={"current_password": "supersecret123", "new_password": "evenbetterpw456"},
        headers={"Authorization": f"Bearer {token}"},
    )
    pw_mails = [s for s in sends if s["to"] == "pw@example.com"]
    assert len(pw_mails) == 1
    assert "password" in str(pw_mails[0]["subject"]).lower()


def test_totp_enable_sends_email(
    client: TestClient, admin_auth: dict[str, str], monkeypatch: MonkeyPatch
) -> None:
    sends = _record_sends(monkeypatch)
    enroll = client.post("/auth/totp/enroll", headers=admin_auth).json()
    code = pyotp.TOTP(enroll["secret"]).now()
    client.post("/auth/totp/verify", json={"code": code}, headers=admin_auth)

    # The admin_auth fixture's email is wired into conftest.py.
    enable_mails = [s for s in sends if "two-factor" in str(s["subject"]).lower()]
    assert len(enable_mails) >= 1
    assert "enabled" in str(enable_mails[0]["subject"]).lower()


def test_leave_submit_emails_decide_capable_users(
    client: TestClient, admin_auth: dict[str, str], monkeypatch: MonkeyPatch
) -> None:
    # Set up an employee linked to a user.
    employee = client.post(
        "/employees",
        json={"employee_code": "9001", "full_name": "Test E"},
        headers=admin_auth,
    ).json()
    client.post(
        "/auth/register",
        json={
            "email": "submitter@example.com",
            "password": "supersecret123",
            "role": "employee",
            "employee_code": employee["employee_code"],
        },
    )
    token = client.post(
        "/auth/login",
        json={"email": "submitter@example.com", "password": "supersecret123"},
    ).json()["access_token"]

    sends = _record_sends(monkeypatch)
    client.post(
        "/me/leave-requests",
        json={
            "start_date": "2026-06-01",
            "end_date": "2026-06-03",
            "reason": "Family",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    # Admin (admin_auth fixture's user) has decide_leave by default → gets the email.
    admin_mails = [s for s in sends if "admin-fixture@example.com" in str(s["to"])]
    assert len(admin_mails) == 1
    assert "Test E" in str(admin_mails[0]["html"])


def test_leave_decided_emails_submitter(
    client: TestClient, admin_auth: dict[str, str], monkeypatch: MonkeyPatch
) -> None:
    employee = client.post(
        "/employees",
        json={"employee_code": "9002", "full_name": "Test D"},
        headers=admin_auth,
    ).json()
    client.post(
        "/auth/register",
        json={
            "email": "deciderly@example.com",
            "password": "supersecret123",
            "role": "employee",
            "employee_code": employee["employee_code"],
        },
    )
    token = client.post(
        "/auth/login",
        json={"email": "deciderly@example.com", "password": "supersecret123"},
    ).json()["access_token"]
    leave = client.post(
        "/me/leave-requests",
        json={
            "start_date": "2026-07-01",
            "end_date": "2026-07-02",
            "reason": "Wedding",
        },
        headers={"Authorization": f"Bearer {token}"},
    ).json()

    sends = _record_sends(monkeypatch)
    client.patch(
        f"/leave-requests/{leave['id']}/decision",
        json={"decision": "approved"},
        headers=admin_auth,
    )
    submitter_mails = [s for s in sends if s["to"] == "deciderly@example.com"]
    assert len(submitter_mails) == 1
    assert "approved" in str(submitter_mails[0]["subject"]).lower()


def test_send_email_noop_without_api_key(monkeypatch: MonkeyPatch) -> None:
    """When TIKKO_RESEND_API_KEY is empty, send_email logs and skips HTTP."""
    import asyncio

    from tikko.email import send_email
    from tikko.settings import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "resend_api_key", "")

    posted: list[object] = []

    def _fail_post(*args: object, **kwargs: object) -> None:
        posted.append((args, kwargs))

    import httpx

    monkeypatch.setattr(httpx.AsyncClient, "post", _fail_post)

    asyncio.run(send_email(to="x@example.com", subject="s", html="<p>h</p>"))
    assert posted == []  # http never called
