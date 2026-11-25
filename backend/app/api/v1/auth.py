"""AI-Pulse user authentication endpoints."""

import jwt
import logging
from hashlib import sha256

from fastapi import (
    BackgroundTasks,
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
)
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth_config import get_jwt_secret
from app.core.auth_security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.db.session import SessionLocal
from app.models.user import User
from app.core.recovery_rate_limit import allow_attempt
from app.services.password_recovery_service import issue_reset_token
from app.services.password_reset_email import (
    RecoveryEmailError,
    RecoveryEmailSettings,
    build_reset_link,
    send_password_reset_email,
)

from app.schemas.password_recovery import (
    ForgotPasswordRequest,
    PasswordResetRequest,
    PasswordResetResponse,
)
from app.services.password_recovery_service import (
    InvalidResetToken,
    redeem_reset_token,
)

from app.schemas.auth import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)


router = APIRouter()
bearer = HTTPBearer(auto_error=False)

# Use a precomputed hash to reduce login timing differences
# between existing and nonexistent accounts.
DUMMY_HASH = hash_password("UnusedDummyPassword123!")


def get_db():
    with SessionLocal() as db:
        yield db


def unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:

    if credentials is None:
        raise unauthorized()

    try:
        payload = decode_access_token(
            credentials.credentials,
            get_jwt_secret(),
        )
        subject = payload.get("sub")

        if (
            not isinstance(subject, str)
            or not subject.isdecimal()
            or int(subject) < 1
        ):
            raise unauthorized()

    except jwt.InvalidTokenError:
        raise unauthorized()

    user = db.get(User, int(subject))

    if user is None or not user.is_active:
        raise unauthorized()

    presented_version = payload.get("ver", 0)
    if (
        type(presented_version) is not int
        or presented_version != user.token_version
    ):
        raise unauthorized()

    return user


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: UserRegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    # Temporary local-development restriction.
    if request.client is None or request.client.host not in (
        "127.0.0.1",
        "::1",
    ):
        raise HTTPException(
            status_code=403,
            detail="Registration is restricted to local development",
        )

    email = str(payload.email).strip().casefold()

    existing = db.scalar(
        select(User.id).where(User.email == email)
    )

    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="Email already registered",
        )

    user = User(
        email=email,
        password_hash=hash_password(payload.password),
        role="user",
        is_active=True,
    )

    try:
        db.add(user)
        db.flush()
        db.refresh(user)

        response = UserResponse.model_validate(user)

        db.commit()

    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Email already registered",
        ) from error

    except Exception:
        db.rollback()
        raise

    return response


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    payload: UserLoginRequest,
    db: Session = Depends(get_db),
):
    email = str(payload.email).strip().casefold()

    user = db.scalar(
        select(User).where(User.email == email)
    )

    stored_hash = (
        user.password_hash
        if user is not None
        else DUMMY_HASH
    )

    password_valid = verify_password(
        payload.password,
        stored_hash,
    )

    if (
        user is None
        or not password_valid
        or not user.is_active
    ):
        raise unauthorized()

    token = create_access_token(
        subject=str(user.id),
        secret_key=get_jwt_secret(),
        expires_minutes=30,
        token_version=user.token_version,
    )

    return TokenResponse(access_token=token)


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: User = Depends(get_current_user),
):
    return current_user



@router.post(
    "/reset-password",
    response_model=PasswordResetResponse,
)
def reset_password(payload: PasswordResetRequest):
    """Reset an account using a verified recovery token."""

    raw_token = payload.token.get_secret_value()
    new_password = payload.new_password.get_secret_value()

    if not 12 <= len(new_password) <= 128:
        raise HTTPException(
            status_code=422,
            detail="Password must contain 12 to 128 characters",
        )

    try:
        redeem_reset_token(raw_token, new_password)

    except InvalidResetToken:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired reset token",
        ) from None

    return PasswordResetResponse(
        message="Password reset successful. Please sign in again."
    )



RECOVERY_RESPONSE = (
    "If an account exists for this email, "
    "password reset instructions will be sent."
)

recovery_logger = logging.getLogger(__name__)


def _recovery_email_ready(config: RecoveryEmailSettings) -> bool:
    if not all((
        config.SMTP_HOST,
        config.SMTP_USERNAME,
        config.SMTP_PASSWORD.get_secret_value(),
        config.FROM_EMAIL,
        config.FRONTEND_URL,
    )):
        return False

    if not 1 <= config.SMTP_PORT <= 65535:
        return False

    try:
        build_reset_link("A" * 32, config)
    except RecoveryEmailError:
        return False

    return True


def _deliver_password_recovery(
    email: str,
    config: RecoveryEmailSettings,
) -> None:
    """Send a reset link after the HTTP response is generated."""

    try:
        with SessionLocal() as db:
            user_id = db.scalar(
                select(User.id).where(
                    User.email == email,
                    User.is_active.is_(True),
                )
            )

        if user_id is None:
            return

        raw_token = issue_reset_token(user_id)

        send_password_reset_email(
            email,
            raw_token,
            settings=config,
        )

    except Exception:
        # Never include credentials, tokens or recipient in logs.
        recovery_logger.error(
            "Password recovery background operation failed"
        )


@router.post(
    "/forgot-password",
    response_model=PasswordResetResponse,
    status_code=202,
)
def forgot_password(
    payload: ForgotPasswordRequest,
    request: Request,
    background_tasks: BackgroundTasks,
):
    """Request password recovery without disclosing account existence."""

    try:
        config = RecoveryEmailSettings()
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Password recovery temporarily unavailable",
        ) from None

    if not _recovery_email_ready(config):
        raise HTTPException(
            status_code=503,
            detail="Password recovery temporarily unavailable",
        )

    email = str(payload.email).strip().casefold()
    client_ip = (
        request.client.host
        if request.client is not None
        else "unknown"
    )

    ip_allowed = allow_attempt(
        f"forgot:ip:{client_ip}",
        limit=6,
    )

    email_key = sha256(email.encode("utf-8")).hexdigest()

    email_allowed = (
        allow_attempt(f"forgot:email:{email_key}", limit=3)
        if ip_allowed
        else False
    )

    # Rate limiting does not disclose whether an account exists.
    if ip_allowed and email_allowed:
        background_tasks.add_task(
            _deliver_password_recovery,
            email,
            config,
        )

    return PasswordResetResponse(message=RECOVERY_RESPONSE)
