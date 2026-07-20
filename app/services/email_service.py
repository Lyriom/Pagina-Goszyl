"""SMTP delivery for validated contact-form submissions."""

from __future__ import annotations

import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr

from email_validator import EmailNotValidError, validate_email

from app.config import settings
from app.contact import ContactSubmission
from app.i18n import Locale, translate


class EmailDeliveryError(RuntimeError):
    """Raised when mail delivery is unavailable or rejected."""


def _normalized_email(value: str) -> str:
    try:
        return validate_email(value, check_deliverability=False).normalized
    except EmailNotValidError as exc:
        raise EmailDeliveryError("Invalid SMTP email configuration") from exc


def _message_body(submission: ContactSubmission, locale: Locale) -> str:
    company = submission.company or "—"
    return "\n".join(
        (
            translate(locale, "email.intro", "Se recibió un nuevo mensaje desde el sitio web de Gozsyl."),
            "",
            f"{translate(locale, 'email.name', 'Nombre')}: {submission.name}",
            f"{translate(locale, 'email.email', 'Correo')}: {submission.email}",
            f"{translate(locale, 'email.company', 'Empresa')}: {company}",
            f"{translate(locale, 'email.language', 'Idioma del sitio')}: {locale.upper()}",
            "",
            f"{translate(locale, 'email.message', 'Mensaje')}:",
            submission.message,
        )
    )


def send_contact_email(submission: ContactSubmission, locale: Locale) -> None:
    """Send one plain-text message; visitor input is never used as a recipient."""
    if not settings.SMTP_HOST:
        raise EmailDeliveryError("SMTP is not configured")

    recipient = _normalized_email(settings.CONTACT_RECIPIENT_EMAIL)
    sender = _normalized_email(settings.SMTP_FROM_EMAIL)
    reply_to = _normalized_email(str(submission.email))

    message = EmailMessage()
    message["Subject"] = translate(
        locale,
        "email.subject",
        "[Gozsyl] Nuevo mensaje del sitio web",
    )
    message["From"] = formataddr(("Gozsyl Website", sender))
    message["To"] = recipient
    message["Reply-To"] = reply_to
    message.set_content(_message_body(submission, locale))

    password = (
        settings.SMTP_PASSWORD.get_secret_value()
        if settings.SMTP_PASSWORD is not None
        else None
    )
    if settings.SMTP_USERNAME and not password:
        raise EmailDeliveryError("SMTP password is not configured")

    try:
        if settings.SMTP_SECURITY == "ssl":
            client: smtplib.SMTP = smtplib.SMTP_SSL(
                settings.SMTP_HOST,
                settings.SMTP_PORT,
                timeout=settings.SMTP_TIMEOUT_SECONDS,
                context=ssl.create_default_context(),
            )
        else:
            client = smtplib.SMTP(
                settings.SMTP_HOST,
                settings.SMTP_PORT,
                timeout=settings.SMTP_TIMEOUT_SECONDS,
            )

        with client:
            client.ehlo()
            if settings.SMTP_SECURITY == "starttls":
                client.starttls(context=ssl.create_default_context())
                client.ehlo()
            if settings.SMTP_USERNAME and password:
                client.login(settings.SMTP_USERNAME, password)
            client.send_message(message)
    except (OSError, ValueError, smtplib.SMTPException) as exc:
        raise EmailDeliveryError("SMTP delivery failed") from exc
