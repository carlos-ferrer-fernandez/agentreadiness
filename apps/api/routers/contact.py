"""
Contact form endpoint — sends support emails via SMTP.
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/contact", tags=["contact"])


class ContactRequest(BaseModel):
    name: str
    email: str
    subject: str
    message: str


@router.post("")
async def send_contact_message(request: ContactRequest):
    """Send a contact form submission via SMTP."""
    settings = get_settings()

    if not settings.smtp_user or not settings.smtp_password:
        logger.error("SMTP not configured — SMTP_USER and SMTP_PASSWORD required")
        raise HTTPException(
            status_code=503,
            detail="Contact form is temporarily unavailable. Please email us directly at carlos@groundocs.com",
        )

    # Build the email
    msg = MIMEMultipart()
    msg["From"] = settings.smtp_user
    msg["To"] = settings.contact_email
    msg["Reply-To"] = request.email
    msg["Subject"] = f"[GrounDocs Support] {request.subject}"

    body = f"""New support message from groundocs.com

From: {request.name} <{request.email}>
Subject: {request.subject}

{request.message}

---
Reply directly to this email to respond to {request.name}.
"""
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port) as server:
            server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)

        logger.info(f"Contact email sent from {request.email}: {request.subject}")
        return {"success": True, "message": "Message sent! We'll get back to you soon."}

    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP authentication failed")
        raise HTTPException(status_code=503, detail="Email service error. Please email us directly at carlos@groundocs.com")
    except Exception as e:
        logger.error(f"Failed to send contact email: {e}")
        raise HTTPException(status_code=503, detail="Failed to send message. Please email us directly at carlos@groundocs.com")
