"""Reset the explicitly identified local AI-Pulse administrator."""

import logging
from getpass import getpass

from sqlalchemy import select

from app.core.auth_security import hash_password
from app.db.session import SessionLocal
from app.models.user import User


ADMIN_ID = 3
ADMIN_EMAIL = "sunnykhubchandani030303@gmail.com"

logging.getLogger("sqlalchemy.engine").setLevel(logging.ERROR)


def main():
    print("\n=== LOCAL ADMIN PASSWORD RESET ===")
    print("Target administrator ID:", ADMIN_ID)

    confirmation = input(
        "Type RESET to authorize this password change: "
    ).strip()

    if confirmation != "RESET":
        raise SystemExit("Cancelled. No changes made.")

    password = getpass("New administrator password: ")
    repeated = getpass("Confirm new password: ")

    if password != repeated:
        raise SystemExit("Passwords do not match")

    if not 12 <= len(password) <= 128:
        raise SystemExit(
            "Password must contain 12 to 128 characters"
        )

    new_hash = hash_password(password)

    with SessionLocal() as db:
        db.get_bind().echo = False

        admin = db.scalar(
            select(User).where(
                User.id == ADMIN_ID,
                User.email == ADMIN_EMAIL,
                User.role == "admin",
                User.is_active.is_(True),
            )
        )

        if admin is None:
            raise SystemExit(
                "Active administrator not found. No changes made."
            )

        admin.password_hash = new_hash
        db.commit()

    print("\nPASS: Administrator password updated")
    print("Account ID:", ADMIN_ID)
    print("Role: admin")
    print("No other account was modified")


if __name__ == "__main__":
    main()
