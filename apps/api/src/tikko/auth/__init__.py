"""Auth utilities — password hashing, JWT issue/verify, FastAPI deps."""

from tikko.auth.capabilities import capabilities_for_role, require_capability
from tikko.auth.dependencies import (
    CurrentUser,
    CurrentUserDep,
    get_current_user,
    require_role,
)
from tikko.auth.hashing import hash_password, verify_password
from tikko.auth.tokens import (
    TokenError,
    decode_token,
    issue_access_token,
    issue_refresh_token,
)

__all__ = [
    "CurrentUser",
    "CurrentUserDep",
    "TokenError",
    "capabilities_for_role",
    "decode_token",
    "get_current_user",
    "hash_password",
    "issue_access_token",
    "issue_refresh_token",
    "require_capability",
    "require_role",
    "verify_password",
]
