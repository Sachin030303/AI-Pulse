"""AI-Pulse password recovery integration test."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select, update

from app.core.auth_config import get_jwt_secret
from app.core.auth_security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.core.password_reset import hash_reset_token
from app.db.session import SessionLocal
from app.main import app
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User
from app.schemas.auth import UserResponse
from app.services.password_recovery_service import (
    InvalidResetToken,
    issue_reset_token,
    redeem_reset_token,
)


original_password = "TemporaryTestPassword2026!"
new_password = "UpdatedTestPassword2026!"

# Use a domain accepted by EmailStr validation.
# No email will be sent during these tests.
email = f"recovery-test-{uuid4().hex}@example.com"

user_id = None


def must_reject(token):
    try:
        redeem_reset_token(token, new_password)
    except InvalidResetToken:
        return

    raise AssertionError("Invalid reset token was accepted")


def request_profile(token):
    with TestClient(app) as client:
        return client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )


try:
    # 1. Create and validate disposable account.
    with SessionLocal.begin() as db:
        user = User(
            email=email,
            password_hash=hash_password(original_password),
            role="user",
            is_active=True,
            token_version=0,
        )

        db.add(user)
        db.flush()
        db.refresh(user)

        # Catch response schema problems immediately.
        UserResponse.model_validate(user)

        user_id = user.id

    print("PASS: Disposable user created")
    print("PASS: User response schema valid")

    # 2. Verify original JWT.
    old_jwt = create_access_token(
        subject=str(user_id),
        secret_key=get_jwt_secret(),
        token_version=0,
    )

    assert request_profile(old_jwt).status_code == 200

    print("PASS: Original JWT accepted")

    # 3. Issue two tokens. First should become invalid.
    first_token = issue_reset_token(user_id)
    second_token = issue_reset_token(user_id)

    assert first_token != second_token

    must_reject(first_token)

    print("PASS: Previous recovery token invalidated")

    # 4. Verify only token hash is stored.
    with SessionLocal() as db:
        record = db.scalar(
            select(PasswordResetToken).where(
                PasswordResetToken.token_hash
                == hash_reset_token(second_token)
            )
        )

        assert record is not None
        assert record.token_hash != second_token
        assert record.used_at is None

    print("PASS: Only token hash stored")

    # 5. Redeem the current token.
    redeem_reset_token(second_token, new_password)

    with SessionLocal() as db:
        user = db.get(User, user_id)

        assert verify_password(
            new_password,
            user.password_hash,
        )

        assert not verify_password(
            original_password,
            user.password_hash,
        )

        assert user.token_version == 1

    print("PASS: Password updated")
    print("PASS: JWT token version incremented")

    # 6. Token must not be reusable.
    must_reject(second_token)

    print("PASS: Used recovery token rejected")

    # 7. Old JWT must no longer work.
    assert request_profile(old_jwt).status_code == 401

    new_jwt = create_access_token(
        subject=str(user_id),
        secret_key=get_jwt_secret(),
        token_version=1,
    )

    assert request_profile(new_jwt).status_code == 200

    print("PASS: Old JWT revoked")
    print("PASS: New JWT accepted")

    # 8. Expired recovery tokens must be rejected.
    expired_token = issue_reset_token(user_id)

    with SessionLocal.begin() as db:
        db.execute(
            update(PasswordResetToken)
            .where(
                PasswordResetToken.token_hash
                == hash_reset_token(expired_token)
            )
            .values(
                expires_at=(
                    datetime.now(timezone.utc)
                    - timedelta(seconds=1)
                )
            )
        )

    must_reject(expired_token)

    print("PASS: Expired recovery token rejected")

    # 9. An invalid recovery must not change credentials.
    with SessionLocal() as db:
        user = db.get(User, user_id)

        assert user.token_version == 1
        assert verify_password(
            new_password,
            user.password_hash,
        )

    print("PASS: Invalid recovery preserved credentials")

    print("\nALL PASSWORD RECOVERY TESTS PASSED")

finally:
    if user_id is not None:
        with SessionLocal.begin() as db:
            user = db.get(User, user_id)

            if user is not None:
                db.delete(user)

        print("PASS: Disposable user cleaned up")
