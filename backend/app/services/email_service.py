import base64
import logging
from email.message import EmailMessage

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


def _build_message(to_email: str, subject: str, html_body: str) -> str:
    msg = EmailMessage()
    msg["To"] = to_email
    msg["From"] = settings.GMAIL_FROM_EMAIL or "Dra. Acosta"
    msg["Subject"] = subject
    msg.set_content("Este correo requiere soporte HTML.", subtype="plain")
    msg.add_alternative(html_body, subtype="html")
    return msg.as_string()


def _get_access_token() -> str:
    """Obtain Gmail access token from refresh token."""
    url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": settings.GMAIL_CLIENT_ID,
        "client_secret": settings.GMAIL_CLIENT_SECRET,
        "refresh_token": settings.GMAIL_REFRESH_TOKEN,
        "grant_type": "refresh_token",
    }
    with httpx.Client(timeout=30) as client:
        r = client.post(url, data=data)
        r.raise_for_status()
        return r.json()["access_token"]


def send_email_sync(to_email: str, subject: str, html_body: str) -> bool:
    """Send email via Gmail API (sync)."""
    try:
        access_token = _get_access_token()
        raw = base64.urlsafe_b64encode(
            _build_message(to_email, subject, html_body).encode()
        ).decode()

        url = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        body = {"raw": raw}

        with httpx.Client(timeout=30) as client:
            r = client.post(url, headers=headers, json=body)
            r.raise_for_status()
            return True
    except Exception as e:
        logger.exception("Gmail API error: %s", e)
        return False


def send_email_with_attachment(
    to_email: str,
    subject: str,
    html_body: str,
    attachment_bytes: bytes,
    attachment_filename: str,
    attachment_mimetype: str = "application/pdf",
) -> bool:
    """Send email with a file attachment via Gmail API."""
    import mimetypes
    from email.mime.application import MIMEApplication
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    try:
        access_token = _get_access_token()

        msg = MIMEMultipart()
        msg["To"] = to_email
        msg["From"] = settings.GMAIL_FROM_EMAIL or "Dra. Acosta"
        msg["Subject"] = subject

        # Attach HTML body
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        # Attach file
        part = MIMEApplication(attachment_bytes, _subtype="pdf")
        part.add_header(
            "Content-Disposition",
            "attachment",
            filename=attachment_filename,
        )
        msg.attach(part)

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

        url = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        body = {"raw": raw}

        with httpx.Client(timeout=30) as client:
            r = client.post(url, headers=headers, json=body)
            r.raise_for_status()
            return True
    except Exception as e:
        logger.exception("Gmail API attachment error: %s", e)
        return False
