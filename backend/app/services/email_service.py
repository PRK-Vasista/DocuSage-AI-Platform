# This is Copyright of DocuSage 2026 Owner Rohith Kumar Vasista P.

"""
Minimal outbound email helper using the Python standard library only.
"""

import logging
import smtplib
from email.message import EmailMessage

from ..core.config import app_settings
from ..core.exceptions import DocuSageError

logger = logging.getLogger("services.email")


class EmailDeliveryError(DocuSageError):
    """Raised when an email cannot be sent."""

    def __init__(self, message: str = "Failed to send email."):
        super().__init__(message, status_code=503)


def send_email(*, to_address: str, subject: str, body: str) -> None:
    """
    Send a plain-text email via configured SMTP settings.

    Args:
        to_address: Recipient email.
        subject: Subject line.
        body: Plain-text body.

    Raises:
        EmailDeliveryError: When SMTP is not configured or sending fails.
    """
    if not app_settings.smtp_configured:
        raise EmailDeliveryError("Email is not configured (SMTP_HOST is empty).")

    from_address = (app_settings.SMTP_FROM or app_settings.SMTP_USER or "").strip()
    if not from_address:
        raise EmailDeliveryError("SMTP_FROM (or SMTP_USER) must be set to send email.")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = from_address
    message["To"] = to_address
    message.set_content(body)

    try:
        with smtplib.SMTP(app_settings.SMTP_HOST, app_settings.SMTP_PORT, timeout=30) as smtp:
            if app_settings.SMTP_USE_TLS:
                smtp.starttls()
            if app_settings.SMTP_USER:
                smtp.login(app_settings.SMTP_USER, app_settings.SMTP_PASSWORD)
            smtp.send_message(message)
        logger.info("Email sent to %s subject=%s", to_address, subject)
    except Exception as exc:  # noqa: BLE001
        logger.error("SMTP send failed: %s", exc)
        raise EmailDeliveryError("Failed to send email via SMTP.") from exc
