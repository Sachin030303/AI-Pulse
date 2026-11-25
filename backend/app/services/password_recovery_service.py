"""Transactional password recovery for AI-Pulse.

Internal service only. Do not expose token issuance through
a public endpoint until email delivery and rate limiting exist.
"""

from datetime import datetime, timezone

from sqlalchemy import select, update

from app.core.auth_security import hash_password
from app.core.password_reset import (
    generate_reset_token,
    hash_reset_token,
    reset_token_expiration,
)
from app.db.session import SessionLocal
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User


class InvalidResetToken(ValueError):
    """Recovery token is invalid, expired, or already consumed."""


def issue_reset_token(user_id: int) -> str:
    """Issue a token for a known, active user.

    Return the secret token only to the trusted caller,
    which will eventually send it through verified email.
    """

    if type(user_id) is not int or user_id < 1:
        raise ValueError("Invalid user ID")

    with SessionLocal.begin() as db:
        user = db.scalar(
            select(User)
            .where(
                User.id == user_id,
                User.is_active.is_(True),
            )
            .with_for_update()
        )

        if user is None:
            raise ValueError("Active user not found")

        now = datetime.now(timezone.utc)

        # Supersede older outstanding tokens.
        db.execute(
            update(PasswordResetToken)
            .where(
                PasswordResetToken.user_id == user_id,
                PasswordResetToken.used_at.is_(None),
            )
            .values(used_at=now)
        )

        raw_token, token_hash = generate_reset_token()

        db.add(
            PasswordResetToken(
                user_id=user_id,
                token_hash=token_hash,
                expires_at=reset_token_expiration(),
            )
        )

    return raw_token


def redeem_reset_token(
    raw_token: str,
    new_password: str,
) -> None:
    """Consume a recovery token and revoke old JWTs atomically."""

    if (
        not isinstance(raw_token, str)
        or not 1 <= len(raw_token) <= 256
    ):
        raise InvalidResetToken("Invalid or expired reset token")

    if (
        not isinstance(new_password, str)
        or not 12 <= len(new_password) <= 128
    ):
        raise ValueError(
            "Password must contain 12 to 128 characters"
        )

    token_hash = hash_reset_token(raw_token)

    with SessionLocal.begin() as db:
        # Find the owner before acquiring locks.
        user_id = db.scalar(
            select(PasswordResetToken.user_id)
            .where(
                PasswordResetToken.token_hash == token_hash
            )
        )

        if user_id is None:
            raise InvalidResetToken("Invalid or expired reset token")

        # Consistent lock order: user, then reset token.
        user = db.scalar(
            select(User)
            .where(User.id == user_id)
            .with_for_update()
        )

        if user is None or not user.is_active:
            raise InvalidResetToken("Invalid or expired reset token")

        reset_record = db.scalar(
            select(PasswordResetToken)
            .where(
                PasswordResetToken.token_hash == token_hash
            )
            .with_for_update()
        )

        now = datetime.now(timezone.utc)

        if (
            reset_record is None
            or reset_record.used_at is not None
            or reset_record.expires_at <= now
        ):
            raise InvalidResetToken("Invalid or expired reset token")

        # Both changes commit or roll back together.
        user.password_hash = hash_password(new_password)
        user.token_version += 1

        # Revoke every outstanding reset token for this user.
        db.execute(
            update(PasswordResetToken)
            .where(
                PasswordResetToken.user_id == user.id,
                PasswordResetToken.used_at.is_(None),
            )
            .values(used_at=now)
        )
