"""Email sending via Resend (https://resend.com).

A single `send_email` function that POSTs to Resend's REST API. When the
`TIKKO_RESEND_API_KEY` setting is empty (the dev default) the function logs
the intended send and skips the network call - so local dev never spams real
inboxes.

Callers should hand this to FastAPI's `BackgroundTasks`:
    background.add_task(send_email, to=..., subject=..., html=...)

so a slow Resend response can't block the HTTP request.
"""

from __future__ import annotations

import logging
from typing import Final

import httpx

logger = logging.getLogger(__name__)

_RESEND_URL: Final = "https://api.resend.com/emails"


async def send_email(
    *,
    to: str,
    subject: str,
    html: str,
    text: str | None = None,
) -> None:
    """Send one email. No-op when no Resend API key is configured."""
    # Local import: settings is the seam tests patch.
    from tikko.settings import get_settings

    settings = get_settings()
    if not settings.resend_api_key:
        logger.info(
            "email.skipped (no TIKKO_RESEND_API_KEY)",
            extra={"to": to, "subject": subject},
        )
        return

    payload: dict[str, object] = {
        "from": settings.from_email,
        "to": [to],
        "subject": subject,
        "html": html,
    }
    if text is not None:
        payload["text"] = text

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                _RESEND_URL,
                headers={"Authorization": f"Bearer {settings.resend_api_key}"},
                json=payload,
            )
            response.raise_for_status()
    except httpx.HTTPError as exc:  # network, 4xx, 5xx
        logger.warning(
            "email.failed",
            extra={"to": to, "subject": subject, "error": str(exc)},
        )


# ---------------------------------------------------------------------------
# Pre-baked templates. Plain HTML so we don't need a templating engine; if the
# list grows past a handful, swap to jinja2 + a `templates/` dir.
# ---------------------------------------------------------------------------


def welcome_email(*, email: str, role: str) -> tuple[str, str]:
    subject = "Welcome to tikko"
    html = f"""
      <p>Hi,</p>
      <p>Your tikko account has been created with the role <strong>{role}</strong>.</p>
      <p>Sign in at <a href="https://tikko.local">tikko</a>.</p>
    """
    return subject, html.strip()


def password_changed_email(*, email: str) -> tuple[str, str]:
    subject = "Your tikko password was changed"
    html = """
      <p>Your tikko password was just changed.</p>
      <p>If this wasn't you, sign in to revoke sessions and reset your password.</p>
    """
    return subject, html.strip()


def totp_toggled_email(*, enabled: bool) -> tuple[str, str]:
    state = "enabled" if enabled else "disabled"
    subject = f"Two-factor authentication {state}"
    html = f"""
      <p>Two-factor authentication on your tikko account is now <strong>{state}</strong>.</p>
      <p>If this wasn't you, change your password immediately.</p>
    """
    return subject, html.strip()


def leave_submitted_email(
    *, employee_name: str, start_date: str, end_date: str, reason: str
) -> tuple[str, str]:
    subject = f"Leave request from {employee_name}"
    html = f"""
      <p><strong>{employee_name}</strong> has requested leave.</p>
      <ul>
        <li>Dates: {start_date} to {end_date}</li>
        <li>Reason: {reason}</li>
      </ul>
      <p>Review and decide in <a href="https://tikko.local/leave-requests">tikko</a>.</p>
    """
    return subject, html.strip()


def leave_decided_email(
    *, decision: str, start_date: str, end_date: str
) -> tuple[str, str]:
    decision_label = decision.upper()
    subject = f"Your leave request was {decision}"
    html = f"""
      <p>Your leave request for <strong>{start_date} to {end_date}</strong> has been
      <strong>{decision_label}</strong>.</p>
    """
    return subject, html.strip()
