"""Email sender with a stdout fallback for dev.

If SMTP credentials are not configured, emails are logged to stdout instead of
being sent. This keeps the dev experience friction-free while still exercising
the real code path.
"""

import logging
import smtplib
from email.message import EmailMessage

from app.config import settings

log = logging.getLogger(__name__)


def send_email(to: str, subject: str, body: str) -> None:
    if not settings.smtp_host:
        log.info("[email-dev] to=%s subject=%s\n%s", to, subject, body)
        return

    msg = EmailMessage()
    msg["From"] = settings.smtp_from
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
            if settings.smtp_tls:
                smtp.starttls()
            if settings.smtp_username and settings.smtp_password:
                smtp.login(settings.smtp_username, settings.smtp_password)
            smtp.send_message(msg)
    except Exception:
        # Email is never load-bearing for correctness (the in-app notification
        # still fired). Log the failure and move on rather than failing the
        # request that triggered it.
        log.exception("Failed to send email to %s", to)
