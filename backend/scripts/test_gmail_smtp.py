"""Test Gmail SMTP connectivity for AI-Pulse."""

import smtplib
import ssl
from email.message import EmailMessage

from app.services.password_reset_email import RecoveryEmailSettings


def main():
    config = RecoveryEmailSettings()

    if config.SMTP_HOST != "smtp.gmail.com":
        raise SystemExit("Gmail SMTP host is not configured")

    if not config.SMTP_USERNAME:
        raise SystemExit("SMTP username is missing")

    if not config.SMTP_PASSWORD.get_secret_value():
        raise SystemExit("Gmail App Password is missing")

    if config.FROM_EMAIL.casefold() != config.SMTP_USERNAME.casefold():
        raise SystemExit(
            "For this test, sender and Gmail username must match"
        )

    recipient = config.SMTP_USERNAME

    print("\n=== AI-PULSE GMAIL SMTP TEST ===")
    print("Recipient:", recipient)
    print("This will send exactly one test email.")

    confirmation = input("Type SEND to continue: ").strip()

    if confirmation != "SEND":
        raise SystemExit("Test cancelled. No email sent.")

    message = EmailMessage()
    message["From"] = config.FROM_EMAIL
    message["To"] = recipient
    message["Subject"] = "AI-Pulse SMTP Test"
    message.set_content(
        "Hello!\n\n"
        "Your AI-Pulse backend successfully submitted "
        "an email through Gmail SMTP.\n\n"
        "This is a connectivity test, not a password reset."
    )

    context = ssl.create_default_context()

    try:
        if (
            config.SMTP_PORT == 465
            and config.SMTP_SECURITY == "ssl"
        ):
            with smtplib.SMTP_SSL(
                config.SMTP_HOST,
                config.SMTP_PORT,
                timeout=15,
                context=context,
            ) as smtp:
                smtp.login(
                    config.SMTP_USERNAME,
                    config.SMTP_PASSWORD.get_secret_value(),
                )
                smtp.send_message(message)

        elif (
            config.SMTP_PORT == 587
            and config.SMTP_SECURITY == "starttls"
        ):
            with smtplib.SMTP(
                config.SMTP_HOST,
                config.SMTP_PORT,
                timeout=15,
            ) as smtp:
                smtp.ehlo()
                smtp.starttls(context=context)
                smtp.ehlo()
                smtp.login(
                    config.SMTP_USERNAME,
                    config.SMTP_PASSWORD.get_secret_value(),
                )
                smtp.send_message(message)

        else:
            raise SystemExit(
                "SMTP port and security settings do not match"
            )

    except smtplib.SMTPAuthenticationError:
        raise SystemExit(
            "FAIL: Gmail rejected authentication. "
            "Check your Google App Password."
        ) from None

    except (smtplib.SMTPException, OSError) as error:
        raise SystemExit(
            "FAIL: SMTP operation failed: "
            + type(error).__name__
        ) from None

    print("PASS: Gmail SMTP authentication")
    print("PASS: Test email submitted successfully")
    print("\nAI-PULSE SMTP TEST PASSED")


if __name__ == "__main__":
    main()
