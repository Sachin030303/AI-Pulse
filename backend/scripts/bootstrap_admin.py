"""One-time local administrator account bootstrap."""

from getpass import getpass

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.auth_config import get_jwt_secret
from app.core.auth_security import hash_password
from app.db.session import SessionLocal
from app.models.user import User
from app.schemas.auth import UserRegisterRequest


def main() -> None:
    # Refuse bootstrap if JWT configuration is missing.
    get_jwt_secret()

    with SessionLocal() as db:
        existing_admin = db.scalar(
            select(User.id).where(User.role == "admin")
        )

        if existing_admin is not None:
            raise SystemExit(
                "An administrator already exists. Bootstrap disabled."
            )

    print("\n=== AI-PULSE ADMINISTRATOR SETUP ===")
    print("Credentials are entered locally and are not displayed.")

    email = input("Administrator email: ").strip()
    password = getpass("Administrator password: ")
    confirmation = getpass("Confirm password: ")

    if password != confirmation:
        raise SystemExit("Passwords do not match")

    try:
        validated = UserRegisterRequest(
            email=email,
            password=password,
        )
    except ValueError as error:
        raise SystemExit(
            "Invalid administrator email or password"
        ) from error

    normalized_email = str(validated.email).casefold()

    with SessionLocal() as db:
        existing_admin = db.scalar(
            select(User.id).where(User.role == "admin")
        )

        if existing_admin is not None:
            raise SystemExit("Administrator already configured")

        existing_email = db.scalar(
            select(User.id).where(User.email == normalized_email)
        )

        if existing_email is not None:
            raise SystemExit(
                "This email already belongs to an account. "
                "No existing account was modified."
            )

        admin = User(
            email=normalized_email,
            password_hash=hash_password(validated.password),
            role="admin",
            is_active=True,
        )

        try:
            db.add(admin)
            db.flush()

            admin_id = admin.id
            db.commit()

        except IntegrityError:
            db.rollback()
            raise SystemExit(
                "Account creation conflict. No account was created."
            )

    print("\nADMINISTRATOR ACCOUNT CREATED")
    print("User ID:", admin_id)
    print("Role: admin")
    print("Password stored as Argon2 hash")


if __name__ == "__main__":
    main()
