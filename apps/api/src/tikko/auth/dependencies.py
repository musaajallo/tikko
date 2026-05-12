"""FastAPI auth dependencies — decode the bearer token and enforce roles."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from tikko.auth.tokens import TokenError, decode_token

_bearer = HTTPBearer(auto_error=False)


@dataclass(slots=True)
class CurrentUser:
    """The authenticated identity from the access token. No DB hit per request."""

    id: str
    role: str


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> CurrentUser:
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        claims = decode_token(credentials.credentials, expected_type="access")
    except TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    return CurrentUser(id=claims["sub"], role=claims["role"])


CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]


def require_role(*allowed: str):
    """Factory for role guards: `Depends(require_role("admin", "manager"))`."""

    def _check(user: CurrentUserDep) -> CurrentUser:
        if user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"role '{user.role}' not allowed",
            )
        return user

    return _check
