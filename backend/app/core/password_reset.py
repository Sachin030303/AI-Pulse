"""Generate secure password recovery tokens."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone


RESET_TOKEN_LIFETIME_MINUTES = 15


def generate_reset_token() -> tuple[str, str]:
    """Return the raw token and the hash to store in the database."""

    raw_token = secrets.token_urlsafe(32)
    token_hash = hash_reset_token(raw_token)

    return raw_token, token_hash


def hash_reset_token(token: str) -> str:
    """Compute a non-reversible lookup hash of a random token."""

    if not isinstance(token, str) or not token:
        raise ValueError("Invalid password reset token")

    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


def reset_token_expiration() -> datetime:
    """Return the timezone-aware expiration timestamp."""

    return datetime.now(timezone.utc) + timedelta(
        minutes=RESET_TOKEN_LIFETIME_MINUTES
    )
