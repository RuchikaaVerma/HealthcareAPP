"""
Background jobs, run on a fixed interval via APScheduler (in-process — fine
for a single-instance deployment on Render/Railway; for multi-instance
production, swap for Celery + Redis or a dedicated worker dyno to avoid
duplicate job execution).

Jobs:
1. release_expired_holds — frees up slots abandoned mid-checkout
2. send_due_medication_reminders — emails patients when a dose is due
3. retry_failed_notifications — re-attempts failed emails
"""
import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.core.database import SessionLocal
from app.core.config import settings
from app.models.reminder import ReminderStatus
from app.models.user import User
from app.models.patient import Patient
from app.models.appointment import Appointment
from app.services import slot_service, email_service, reminder_service
from app.models.notification_log import NotificationType

logger = logging.getLogger("scheduler")
scheduler = AsyncIOScheduler()


def job_release_expired_holds():
    db = SessionLocal()
    try:
        count = slot_service.release_expired_holds(db)
        if count:
            logger.info("Released %d expired slot holds", count)
    finally:
        db.close()


async def job_send_due_reminders():
    db = SessionLocal()
    try:
        due = reminder_service.get_due_reminders(db)
        for reminder in due:
            appt = db.query(Appointment).filter(Appointment.id == reminder.appointment_id).first()
            if not appt:
                reminder.status = ReminderStatus.CANCELLED
                continue
            patient = db.query(Patient).filter(Patient.id == appt.patient_id).first()
            patient_user = db.query(User).filter(User.id == patient.user_id).first()
            try:
                await email_service.send_notification(
                    db, patient_user.id, patient_user.email,
                    NotificationType.MEDICATION_REMINDER,
                    subject=f"Reminder: take your {reminder.drug_name}",
                    html_body=email_service.medication_reminder_email(
                        patient_user.full_name, reminder.drug_name, reminder.dosage or ""
                    ),
                    appointment_id=appt.id,
                )
                reminder.status = ReminderStatus.SENT
            except Exception as exc:  # noqa: BLE001
                logger.error("Failed to send medication reminder %s: %s", reminder.id, exc)
                reminder.status = ReminderStatus.FAILED
                reminder.retry_count += 1
        db.commit()
        if due:
            logger.info("Processed %d due medication reminders", len(due))
    finally:
        db.close()


async def job_retry_failed_notifications():
    db = SessionLocal()
    try:
        retried = await email_service.retry_failed_notifications(db)
        if retried:
            logger.info("Retried %d failed notifications", retried)
    finally:
        db.close()


def _run_async_job(coro_fn):
    """APScheduler's asyncio scheduler can schedule coroutine functions directly,
    but we wrap to ensure consistent logging on uncaught exceptions."""
    async def wrapper():
        try:
            await coro_fn()
        except Exception as exc:  # noqa: BLE001
            logger.error("Scheduled job %s raised: %s", coro_fn.__name__, exc)
    return wrapper


def start_scheduler():
    interval = settings.SCHEDULER_INTERVAL_MINUTES
    scheduler.add_job(job_release_expired_holds, "interval", minutes=1, id="release_holds")
    scheduler.add_job(_run_async_job(job_send_due_reminders), "interval", minutes=interval, id="send_reminders")
    scheduler.add_job(_run_async_job(job_retry_failed_notifications), "interval", minutes=interval, id="retry_emails")
    scheduler.start()
    logger.info("Background scheduler started (interval=%s min)", interval)


def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
