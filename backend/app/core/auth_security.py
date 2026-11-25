"""Authentication cryptography utilities for AI-Pulse."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from pwdlib import PasswordHash


password_hash = PasswordHash.recommended()

ALGORITHM = "HS256"
TOKEN_ISSUER = "ai-pulse"


def hash_password(password: str) -> str:
    """Hash a new password using Argon2."""

    if len(password) < 12:
        raise ValueError("Password must contain at least 12 characters")

    return password_hash.hash(password)


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password against its stored hash."""

    return password_hash.verify(password, stored_hash)


def create_access_token(
    subject: str,
    secret_key: str,
    expires_minutes: int = 30,
    token_version: int = 0,
) -> str:
    """Create a signed, expiring access token."""

    if not subject.strip():
        raise ValueError("Token subject is required")

    if len(secret_key.encode("utf-8")) < 32:
        raise ValueError("JWT secret must contain at least 32 bytes")

    if not 1 <= expires_minutes <= 1440:
        raise ValueError("Invalid token expiration")

    if type(token_version) is not int or token_version < 0:
        raise ValueError("Invalid token version")

    now = datetime.now(timezone.utc)

    payload = {
        "sub": subject,
        "iss": TOKEN_ISSUER,
        "iat": now,
        "exp": now + timedelta(minutes=expires_minutes),
        "jti": str(uuid4()),
        "ver": token_version,
    }

    return jwt.encode(
        payload,
        secret_key,
        algorithm=ALGORITHM,
    )


def decode_access_token(
    token: str,
    secret_key: str,
) -> dict:
    """Validate a signed access token and its expiration."""

    return jwt.decode(
        token,
        secret_key,
        algorithms=[ALGORITHM],
        issuer=TOKEN_ISSUER,
        options={
            "require": ["sub", "iss", "iat", "exp"],
        },
    )
