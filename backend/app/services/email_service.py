"""
Email delivery via fastapi-mail (SMTP — works with SendGrid, Mailgun SMTP
relay, Gmail SMTP, etc. — just change MAIL_SERVER/PORT/credentials in .env).

RELIABILITY DESIGN:
Every send first creates a NotificationLog row with status=PENDING, THEN
attempts the SMTP send. If the send succeeds, status -> SENT. If it throws,
status -> FAILED and last_error is recorded, but the row is NOT deleted.
The background scheduler's retry job (see services/scheduler.py) periodically
re-attempts FAILED rows up to EMAIL_MAX_RETRIES, after which it marks them
EXHAUSTED and the failure is visible to admins. This means a transient SMTP
outage never silently drops a booking confirmation or cancellation notice.
"""
import logging
from typing import Optional
from uuid import UUID
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.notification_log import NotificationLog, NotificationType, NotificationStatus

logger = logging.getLogger("email_service")

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)


async def _send_via_smtp(to_email: str, subject: str, html_body: str) -> None:
    fm = FastMail(conf)
    message = MessageSchema(
        subject=subject,
        recipients=[to_email],
        body=html_body,
        subtype=MessageType.html,
    )
    await fm.send_message(message)


async def send_notification(
    db: Session,
    recipient_user_id: UUID,
    recipient_email: str,
    notification_type: NotificationType,
    subject: str,
    html_body: str,
    appointment_id: Optional[UUID] = None,
) -> NotificationLog:
    log = NotificationLog(
        appointment_id=appointment_id,
        recipient_user_id=recipient_user_id,
        recipient_email=recipient_email,
        notification_type=notification_type,
        subject=subject,
        body_preview=html_body[:500],
        status=NotificationStatus.PENDING,
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    try:
        await _send_via_smtp(recipient_email, subject, html_body)
        log.status = NotificationStatus.SENT
        db.commit()
    except Exception as exc:  # noqa: BLE001
        logger.error("Email send failed for %s: %s", recipient_email, exc)
        log.status = NotificationStatus.FAILED
        log.last_error = str(exc)[:1000]
        db.commit()

    return log


async def retry_failed_notifications(db: Session) -> int:
    """Called by the background scheduler. Retries FAILED notifications up to EMAIL_MAX_RETRIES."""
    failed = db.query(NotificationLog).filter(
        NotificationLog.status == NotificationStatus.FAILED,
        NotificationLog.retry_count < settings.EMAIL_MAX_RETRIES,
    ).all()

    retried = 0
    for log in failed:
        log.retry_count += 1
        try:
            await _send_via_smtp(log.recipient_email, log.subject, log.body_preview or "")
            log.status = NotificationStatus.SENT
        except Exception as exc:  # noqa: BLE001
            log.last_error = str(exc)[:1000]
            if log.retry_count >= settings.EMAIL_MAX_RETRIES:
                log.status = NotificationStatus.EXHAUSTED
        retried += 1

    if retried:
        db.commit()
    return retried


# ---------- Email templates (kept simple/inline; swap for Jinja2 if desired) ----------

def booking_confirmation_email(name: str, doctor_name: str, slot_start_str: str) -> str:
    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px;">
      <h2 style="color:#13B8A6;">Appointment Confirmed</h2>
      <p>Hi {name},</p>
      <p>Your appointment with <strong>Dr. {doctor_name}</strong> is confirmed for:</p>
      <p style="font-size:18px;"><strong>{slot_start_str}</strong></p>
      <p>You'll receive a reminder closer to the time. A calendar invite has been sent to your Google Calendar.</p>
    </div>
    """


def cancellation_email(name: str, doctor_name: str, slot_start_str: str, reason: str = "") -> str:
    reason_html = f"<p><em>Reason: {reason}</em></p>" if reason else ""
    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px;">
      <h2 style="color:#FF6B6B;">Appointment Cancelled</h2>
      <p>Hi {name},</p>
      <p>Your appointment with <strong>Dr. {doctor_name}</strong> scheduled for <strong>{slot_start_str}</strong> has been cancelled.</p>
      {reason_html}
      <p>Please book a new slot at your convenience.</p>
    </div>
    """


def leave_conflict_email(name: str, doctor_name: str, slot_start_str: str) -> str:
    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px;">
      <h2 style="color:#FF6B6B;">Your Appointment Needs Rescheduling</h2>
      <p>Hi {name},</p>
      <p>Dr. {doctor_name} is unavailable on <strong>{slot_start_str}</strong> due to unforeseen leave.
      We're sorry for the inconvenience — please rebook a new slot.</p>
    </div>
    """


def medication_reminder_email(name: str, drug_name: str, dosage: str) -> str:
    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px;">
      <h2 style="color:#7C9CFF;">Medication Reminder</h2>
      <p>Hi {name}, it's time to take:</p>
      <p style="font-size:18px;"><strong>{drug_name}</strong> — {dosage}</p>
    </div>
    """
