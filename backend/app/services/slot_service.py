"""
Slot computation + concurrency-safe booking.

DOUBLE-BOOKING PREVENTION STRATEGY (see system design doc for full writeup):
1. Available slots are computed on read by taking the doctor's WorkingHours
   template for that weekday, chopping it into slot_duration_minutes pieces,
   then subtracting any slot that overlaps an existing HELD or CONFIRMED
   appointment, and subtracting any slot that falls inside an active Leave.
2. On WRITE (hold_slot), we don't trust that computed list to still be valid
   by the time the request arrives — another patient may have booked the same
   slot a moment earlier. So we rely on a DB-level partial unique index on
   (doctor_id, slot_start) for status IN ('held','confirmed') (created in the
   Alembic migration). We attempt the INSERT inside a transaction; if Postgres
   raises a unique-violation, we catch it and return a 409 Conflict. This is
   correct under true concurrency because Postgres serializes the constraint
   check — no race window, unlike an app-level "check then insert".
3. A HELD row expires after SLOT_HOLD_EXPIRY_SECONDS if the patient never
   confirms (abandons the symptom form). The background scheduler sweeps and
   releases expired holds. This is the "slot hold" mechanism from the brief.
"""
from datetime import datetime, timedelta, date as date_cls, time as time_cls
from typing import List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from app.models.doctor import Doctor, WorkingHours
from app.models.appointment import Appointment, AppointmentStatus
from app.models.leave import Leave
from app.core.config import settings


def _is_on_leave(db: Session, doctor_id: UUID, day: date_cls) -> bool:
    return db.query(Leave).filter(
        Leave.doctor_id == doctor_id,
        Leave.start_date <= day,
        Leave.end_date >= day,
    ).first() is not None


def get_available_slots(db: Session, doctor_id: UUID, day: date_cls) -> List[datetime]:
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    if _is_on_leave(db, doctor_id, day):
        return []

    weekday = day.weekday()  # 0=Monday
    template = db.query(WorkingHours).filter(
        WorkingHours.doctor_id == doctor_id,
        WorkingHours.day_of_week == weekday,
    ).all()
    if not template:
        return []

    duration = timedelta(minutes=doctor.slot_duration_minutes or settings.DEFAULT_SLOT_DURATION_MINUTES)

    # Existing holds/confirmations for the day, used to exclude taken slots
    day_start = datetime.combine(day, time_cls.min)
    day_end = datetime.combine(day, time_cls.max)
    taken = db.query(Appointment.slot_start).filter(
        Appointment.doctor_id == doctor_id,
        Appointment.slot_start >= day_start,
        Appointment.slot_start <= day_end,
        Appointment.status.in_([AppointmentStatus.HELD, AppointmentStatus.CONFIRMED]),
    ).all()
    taken_starts = {t[0].replace(tzinfo=None) for t in taken}

    now = datetime.utcnow()
    slots: List[datetime] = []
    for block in template:
        cursor = datetime.combine(day, block.start_time)
        block_end = datetime.combine(day, block.end_time)
        while cursor + duration <= block_end:
            if cursor not in taken_starts and cursor > now:
                slots.append(cursor)
            cursor += duration
    return slots


def hold_slot(db: Session, doctor_id: UUID, patient_id: UUID, slot_start: datetime) -> Appointment:
    """
    Attempts to atomically reserve a slot. Relies on the DB partial unique
    constraint to be the final word on conflicts — this function does NOT
    assume the slot is free just because get_available_slots said so a moment
    ago (that would reintroduce the race condition).
    """
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    duration = timedelta(minutes=doctor.slot_duration_minutes or settings.DEFAULT_SLOT_DURATION_MINUTES)
    slot_end = slot_start + duration

    if _is_on_leave(db, doctor_id, slot_start.date()):
        raise HTTPException(status_code=409, detail="Doctor is on leave for this date")

    if slot_start <= datetime.utcnow():
        raise HTTPException(status_code=400, detail="Cannot book a slot in the past")

    appointment = Appointment(
        doctor_id=doctor_id,
        patient_id=patient_id,
        slot_start=slot_start,
        slot_end=slot_end,
        status=AppointmentStatus.HELD,
        hold_expires_at=datetime.utcnow() + timedelta(seconds=settings.SLOT_HOLD_EXPIRY_SECONDS),
    )
    db.add(appointment)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This slot was just booked by another patient. Please choose a different slot.",
        )
    db.refresh(appointment)
    return appointment


def confirm_appointment(db: Session, appointment: Appointment) -> Appointment:
    appointment.status = AppointmentStatus.CONFIRMED
    appointment.hold_expires_at = None
    db.commit()
    db.refresh(appointment)
    return appointment


def release_expired_holds(db: Session) -> int:
    """Called by the background scheduler. Returns number of holds released."""
    now = datetime.utcnow()
    expired = db.query(Appointment).filter(
        Appointment.status == AppointmentStatus.HELD,
        Appointment.hold_expires_at < now,
    ).all()
    count = 0
    for appt in expired:
        db.delete(appt)  # held-but-never-confirmed rows are abandoned carts, safe to remove
        count += 1
    if count:
        db.commit()
    return count
