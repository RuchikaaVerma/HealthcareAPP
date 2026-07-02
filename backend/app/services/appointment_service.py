"""
High-level orchestration for the appointment lifecycle. Routes call into
here rather than touching email/calendar services directly, so the
"create calendar events + send emails on booking" behavior lives in one
place and stays consistent across booking, rescheduling, and cancellation.
"""
import json
import logging
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.appointment import Appointment, AppointmentStatus
from app.models.calendar_event import CalendarEvent, CalendarOwnerType
from app.models.notification_log import NotificationType
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.user import User
from app.services import calendar_service, email_service, reminder_service

logger = logging.getLogger("appointment_service")


async def finalize_booking(db: Session, appointment: Appointment) -> Appointment:
    """
    Called after symptom form is submitted and the hold is promoted to
    CONFIRMED. Creates calendar events for both patient and doctor (best
    effort — failures don't block booking) and sends confirmation emails.
    """
    doctor = db.query(Doctor).filter(Doctor.id == appointment.doctor_id).first()
    patient = db.query(Patient).filter(Patient.id == appointment.patient_id).first()
    doctor_user = db.query(User).filter(User.id == doctor.user_id).first()
    patient_user = db.query(User).filter(User.id == patient.user_id).first()

    slot_str = appointment.slot_start.strftime("%A, %d %B %Y at %I:%M %p")

    # --- Calendar sync (best effort, never raises) ---
    for owner_type, owner_user, summary in [
        (CalendarOwnerType.PATIENT, patient_user, f"Appointment with Dr. {doctor_user.full_name}"),
        (CalendarOwnerType.DOCTOR, doctor_user, f"Appointment with {patient_user.full_name}"),
    ]:
        event_id = calendar_service.create_event(
            db, owner_user.id, summary,
            description="Booked via Healthcare Appointment Manager",
            start=appointment.slot_start, end=appointment.slot_end,
        )
        db.add(CalendarEvent(
            appointment_id=appointment.id,
            owner_type=owner_type,
            owner_user_id=owner_user.id,
            google_event_id=event_id,
            sync_failed="false" if event_id else "true",
        ))
    db.commit()

    # --- Email notifications (logged + retryable, never raises) ---
    await email_service.send_notification(
        db, patient_user.id, patient_user.email,
        NotificationType.BOOKING_CONFIRMATION,
        subject="Your appointment is confirmed",
        html_body=email_service.booking_confirmation_email(patient_user.full_name, doctor_user.full_name, slot_str),
        appointment_id=appointment.id,
    )
    await email_service.send_notification(
        db, doctor_user.id, doctor_user.email,
        NotificationType.BOOKING_CONFIRMATION,
        subject="New appointment booked",
        html_body=email_service.booking_confirmation_email(doctor_user.full_name, patient_user.full_name, slot_str),
        appointment_id=appointment.id,
    )

    return appointment


async def cancel_appointment(db: Session, appointment: Appointment, status: AppointmentStatus, reason: str = "") -> Appointment:
    """Cancels an appointment, deletes calendar events, sends cancellation emails, cancels pending reminders."""
    appointment.status = status
    appointment.cancellation_reason = reason
    db.commit()

    doctor = db.query(Doctor).filter(Doctor.id == appointment.doctor_id).first()
    patient = db.query(Patient).filter(Patient.id == appointment.patient_id).first()
    doctor_user = db.query(User).filter(User.id == doctor.user_id).first()
    patient_user = db.query(User).filter(User.id == patient.user_id).first()
    slot_str = appointment.slot_start.strftime("%A, %d %B %Y at %I:%M %p")

    # Delete calendar events (best effort)
    events = db.query(CalendarEvent).filter(CalendarEvent.appointment_id == appointment.id).all()
    for event in events:
        if event.google_event_id:
            calendar_service.delete_event(db, event.owner_user_id, event.google_event_id)

    reminder_service.cancel_reminders_for_appointment(db, appointment.id)

    notif_type = (
        NotificationType.LEAVE_CONFLICT
        if status == AppointmentStatus.CANCELLED_BY_LEAVE
        else NotificationType.CANCELLATION
    )
    email_fn = (
        email_service.leave_conflict_email
        if status == AppointmentStatus.CANCELLED_BY_LEAVE
        else email_service.cancellation_email
    )

    await email_service.send_notification(
        db, patient_user.id, patient_user.email, notif_type,
        subject="Appointment update" if status == AppointmentStatus.CANCELLED_BY_LEAVE else "Appointment cancelled",
        html_body=(
            email_fn(patient_user.full_name, doctor_user.full_name, slot_str)
            if status == AppointmentStatus.CANCELLED_BY_LEAVE
            else email_fn(patient_user.full_name, doctor_user.full_name, slot_str, reason)
        ),
        appointment_id=appointment.id,
    )
    return appointment
