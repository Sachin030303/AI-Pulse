"""Secure SMTP delivery for AI-Pulse password reset emails."""

import re
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path
from typing import Literal
from urllib.parse import quote, urlsplit

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class RecoveryEmailSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_prefix="RESET_",
        extra="ignore",
    )

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: SecretStr = SecretStr("")
    SMTP_SECURITY: Literal["starttls", "ssl"] = "starttls"

    FROM_EMAIL: str = ""
    FRONTEND_URL: str = ""


class RecoveryEmailError(RuntimeError):
    """Email configuration or delivery failed."""


def build_reset_link(
    raw_token: str,
    settings: RecoveryEmailSettings,
) -> str:
    """Build a link from trusted configuration, not request headers."""

    if not re.fullmatch(r"[A-Za-z0-9_-]{20,256}", raw_token):
        raise RecoveryEmailError("Invalid recovery token format")

    base_url = settings.FRONTEND_URL.strip()
    parsed = urlsplit(base_url)

    is_https = parsed.scheme == "https"
    is_local_http = (
        parsed.scheme == "http"
        and parsed.hostname in {"localhost", "127.0.0.1"}
    )

    if not (is_https or is_local_http):
        raise RecoveryEmailError(
            "Reset frontend must use HTTPS, except on localhost"
        )

    if (
        not parsed.netloc
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or not parsed.path.strip("/")
    ):
        raise RecoveryEmailError(
            "Invalid password reset frontend URL"
        )

    # A URL fragment is not sent to the web server in HTTP requests.
    # The future frontend will read and clear this fragment.
    return (
        base_url
        + "#token="
        + quote(raw_token, safe="")
    )


def send_password_reset_email(
    recipient: str,
    raw_token: str,
    *,
    settings: RecoveryEmailSettings | None = None,
) -> None:
    """Deliver a password reset link without logging the token."""

    config = settings or RecoveryEmailSettings()

    if not all((
        config.SMTP_HOST,
        config.SMTP_USERNAME,
        config.SMTP_PASSWORD.get_secret_value(),
        config.FROM_EMAIL,
        config.FRONTEND_URL,
    )):
        raise RecoveryEmailError(
            "Password recovery email is not configured"
        )

    if not 1 <= config.SMTP_PORT <= 65535:
        raise RecoveryEmailError("Invalid SMTP port")

    link = build_reset_link(raw_token, config)

    message = EmailMessage()
    message["From"] = config.FROM_EMAIL
    message["To"] = recipient
    message["Subject"] = "AI-Pulse password reset"
    message["Auto-Submitted"] = "auto-generated"

    message.set_content(
        "A password reset was requested for your AI-Pulse account.\n\n"
        "Use the following link to choose a new password:\n\n"
        f"{link}\n\n"
        "This link expires in 15 minutes and can be used once.\n\n"
        "If you did not request this change, ignore this email.\n"
    )

    context = ssl.create_default_context()

    try:
        if config.SMTP_SECURITY == "ssl":
            with smtplib.SMTP_SSL(
                config.SMTP_HOST,
                config.SMTP_PORT,
                timeout=10,
                context=context,
            ) as smtp:
                smtp.login(
                    config.SMTP_USERNAME,
                    config.SMTP_PASSWORD.get_secret_value(),
                )
                smtp.send_message(message)

        else:
            with smtplib.SMTP(
                config.SMTP_HOST,
                config.SMTP_PORT,
                timeout=10,
            ) as smtp:
                smtp.ehlo()
                smtp.starttls(context=context)
                smtp.ehlo()
                smtp.login(
                    config.SMTP_USERNAME,
                    config.SMTP_PASSWORD.get_secret_value(),
                )
                smtp.send_message(message)

    except (smtplib.SMTPException, OSError) as error:
        raise RecoveryEmailError(
            "Password recovery email delivery failed"
        ) from None
