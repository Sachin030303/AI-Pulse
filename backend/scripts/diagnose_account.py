"""Diagnose the existing AI-Pulse administrator account."""

from getpass import getpass

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.user import User
from app.core.auth_security import verify_password


def main():
    print("\n=== AI-PULSE ACCOUNT DIAGNOSTIC ===")

    email = input("AI-Pulse account email: ").strip().lower()
    password = getpass("AI-Pulse password (hidden): ")

    with SessionLocal() as db:
        user = db.scalar(
            select(User).where(User.email == email)
        )

        if user is None:
            print("FAIL: Account not found")
            return

        print("PASS: Account found")
        print("Role:", user.role)
        print("Active:", user.is_active)

        try:
            matches = verify_password(
                password,
                user.password_hash,
            )
            print("Password matches:", matches)

        except Exception as error:
            print(
                "Password verification error:",
                type(error).__name__,
            )

    print("\nACCOUNT DIAGNOSTIC COMPLETE")


if __name__ == "__main__":
    main()
