"""Password hashing via bcrypt.

Wrapped so callers don't import bcrypt directly and the algorithm choice
stays in one place if we ever migrate to argon2.
"""

from __future__ import annotations

import bcrypt


def hash_password(plain: str) -> str:
    """Return a UTF-8 string suitable for storing in the `users.password_hash` column."""
    salted = bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt())
    return salted.decode("utf-8")


def verify_password(plain: str, stored_hash: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), stored_hash.encode("utf-8"))
    except ValueError:
        # Stored hash is malformed — treat as a verification failure.
        return False
