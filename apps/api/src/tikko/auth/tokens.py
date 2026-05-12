"""JWT issuance and verification.

Access tokens are short-lived (default 15 min, from settings); refresh tokens
are long-lived (default 30 days). Both are HS256-signed with `TIKKO_JWT_SECRET`.

Claims carried in every token:
- `sub`     — user id (UUID string)
- `role`    — "admin" | "manager" | "employee"
- `type`    — "access" | "refresh"  (separates the two channels)
- `iat`, `exp` — issued-at / expiry as unix timestamps
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Literal

import jwt

from tikko.settings import get_settings

TokenType = Literal["access", "refresh"]


class TokenError(Exception):
    """Raised when a token is missing, malformed, expired, or wrong-typed."""


def _issue(sub: str, role: str, token_type: TokenType, ttl: timedelta) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": sub,
        "role": role,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + ttl).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def issue_access_token(sub: str, role: str) -> str:
    settings = get_settings()
    return _issue(sub, role, "access", timedelta(minutes=settings.jwt_access_ttl_min))


def issue_refresh_token(sub: str, role: str) -> str:
    settings = get_settings()
    return _issue(sub, role, "refresh", timedelta(days=settings.jwt_refresh_ttl_days))


def decode_token(token: str, expected_type: TokenType = "access") -> dict:
    settings = get_settings()
    try:
        claims = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise TokenError(str(exc)) from exc

    if claims.get("type") != expected_type:
        raise TokenError(
            f"expected {expected_type} token, got {claims.get('type')!r}"
        )
    return claims
