"""Secure local password reset for an existing AI-Pulse admin."""

from getpass import getpass

from sqlalchemy import select

from app.core.auth_security import hash_password, verify_password
from app.db.session import SessionLocal
from app.models.user import User


def main():
    print("\n=== AI-PULSE ADMIN PASSWORD RESET ===")

    email = input("Administrator email: ").strip().lower()

    with SessionLocal() as db:
        user = db.scalar(
            select(User).where(User.email == email)
        )

        if user is None or user.role != "admin":
            raise SystemExit("Administrator account not found")

        if not user.is_active:
            raise SystemExit("Administrator account is inactive")

    print("PASS: Existing administrator verified")

    confirmation = input(
        "Type RESET to change the password: "
    ).strip()

    if confirmation != "RESET":
        raise SystemExit("Cancelled. No changes made.")

    password = getpass("New AI-Pulse password: ")
    repeat = getpass("Confirm new password: ")

    if password != repeat:
        raise SystemExit("FAIL: Passwords do not match")

    if not 12 <= len(password) <= 128:
        raise SystemExit(
            "Password must contain 12 to 128 characters"
        )

    password_hash = hash_password(password)

    if not verify_password(password, password_hash):
        raise SystemExit("FAIL: Password hashing verification")

    with SessionLocal.begin() as db:
        user = db.scalar(
            select(User)
            .where(
                User.email == email,
                User.role == "admin",
                User.is_active.is_(True),
            )
            .with_for_update()
        )

        if user is None:
            raise SystemExit("Administrator unavailable")

        user.password_hash = password_hash
        user.token_version = (user.token_version or 0) + 1

    print("\nPASS: Administrator password updated")
    print("PASS: Previous JWT access tokens invalidated")
    print("PASS: Existing project data preserved")
    print("\nAI-PULSE PASSWORD RESET COMPLETE")


if __name__ == "__main__":
    main()
