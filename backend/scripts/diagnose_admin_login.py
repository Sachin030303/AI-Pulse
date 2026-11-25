"""Diagnose local administrator credentials safely."""

import logging
from getpass import getpass

import httpx
from sqlalchemy import select

from app.core.auth_security import verify_password
from app.db.session import SessionLocal
from app.models.user import User


ADMIN_ID = 3
ADMIN_EMAIL = "sunnykhubchandani030303@gmail.com"

logging.getLogger("sqlalchemy.engine").setLevel(logging.ERROR)


def main():
    print("\n=== AI-PULSE ADMIN LOGIN DIAGNOSTIC ===")

    with SessionLocal() as db:
        db.get_bind().echo = False

        admin = db.scalar(
            select(User).where(
                User.id == ADMIN_ID,
                User.email == ADMIN_EMAIL,
            )
        )

        if admin is None:
            print("FAIL: Administrator not found in local database")
            return

        print("PASS: Administrator account found")
        print("Role:", admin.role)
        print("Active:", admin.is_active)

        if admin.role != "admin" or not admin.is_active:
            print("FAIL: Account role or active status is invalid")
            return

        password = getpass("Enter current administrator password: ")

        password_matches = verify_password(
            password,
            admin.password_hash,
        )

    print(
        "Local password verification:",
        "PASS" if password_matches else "FAIL",
    )

    if not password_matches:
        print(
            "\nDIAGNOSIS: Password does not match "
            "the stored administrator password."
        )
        print("Use Step 209B to reset it locally.")
        return

    with httpx.Client(
        base_url="http://127.0.0.1:8000",
        timeout=30,
    ) as client:

        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": ADMIN_EMAIL,
                "password": password,
            },
        )

        print("Live API login status:", response.status_code)

        if response.status_code == 200:
            print("PASS: Live administrator login verified")
        else:
            print(
                "FAIL: Local password is correct, but "
                "the running API rejected the login."
            )
            print(
                "Check whether Uvicorn is connected "
                "to the same PostgreSQL database."
            )


if __name__ == "__main__":
    main()
