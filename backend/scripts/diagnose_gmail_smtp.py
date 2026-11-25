"""Diagnose Gmail SMTP connection without sending emails."""

import smtplib
import ssl
from contextlib import suppress

from app.services.password_reset_email import RecoveryEmailSettings


config = RecoveryEmailSettings()

smtp = None
stage = "Connection"

print("\n=== AI-PULSE GMAIL DIAGNOSTIC ===")

try:
    stage = "Connection and server greeting"
    smtp = smtplib.SMTP(
        config.SMTP_HOST,
        config.SMTP_PORT,
        timeout=20,
    )
    print("PASS: Connected to Gmail SMTP")

    stage = "EHLO"
    code, _ = smtp.ehlo()
    assert code == 250
    print("PASS: SMTP EHLO accepted")

    stage = "STARTTLS"
    if not smtp.has_extn("starttls"):
        raise RuntimeError("STARTTLS not advertised")

    smtp.starttls(context=ssl.create_default_context())
    print("PASS: STARTTLS connection established")

    stage = "EHLO after STARTTLS"
    code, _ = smtp.ehlo()
    assert code == 250
    print("PASS: Encrypted SMTP session established")

    print("\nNetwork and TLS checks passed.")
    answer = input(
        "Type LOGIN to test Gmail authentication: "
    ).strip()

    if answer == "LOGIN":
        stage = "Gmail authentication"
        smtp.login(
            config.SMTP_USERNAME,
            config.SMTP_PASSWORD.get_secret_value(),
        )
        print("PASS: Gmail authentication successful")
    else:
        print("Authentication test skipped")

except smtplib.SMTPAuthenticationError:
    print("FAIL: Gmail authentication rejected")
    print("Check your Google App Password")

except (
    smtplib.SMTPException,
    ssl.SSLError,
    OSError,
    RuntimeError,
    AssertionError,
) as error:
    print("FAIL at stage:", stage)
    print("Error type:", type(error).__name__)

finally:
    if smtp is not None:
        with suppress(Exception):
            smtp.quit()

print("\nSMTP DIAGNOSTIC COMPLETE")
