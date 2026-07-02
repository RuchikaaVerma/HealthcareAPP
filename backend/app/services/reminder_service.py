"""
Expands a prescription ("twice daily for 5 days") into individual Reminder
rows with concrete due_at timestamps, and cancels reminders if an
appointment is cancelled after notes were already submitted (edge case).
"""
from datetime import datetime, timedelta
from uuid import UUID
from typing import List
from sqlalchemy.orm import Session

from app.models.reminder import Reminder, ReminderStatus
from app.schemas.appointment import PrescriptionItem


def schedule_reminders_for_prescriptions(
    db: Session, appointment_id: UUID, prescriptions: List[PrescriptionItem], start_from: datetime = None
) -> int:
    """
    Simple even-spacing strategy: for N doses/day, space them across waking
    hours (8:00–22:00) evenly. E.g. frequency_per_day=2 -> 8:00 and 15:00.
    This is intentionally simple and documented so it's easy to swap for a
    more clinical scheduling rule (e.g. with/after meals) later.
    """
    start_from = start_from or datetime.utcnow()
    created = 0
    waking_window_minutes = (22 - 8) * 60

    for item in prescriptions:
        if item.frequency_per_day <= 0:
            continue
        interval = waking_window_minutes / item.frequency_per_day
        for day in range(item.duration_days):
            day_date = (start_from + timedelta(days=day)).date()
            for dose_index in range(item.frequency_per_day):
                minutes_after_8am = int(dose_index * interval)
                due_at = datetime.combine(day_date, datetime.min.time()) + timedelta(hours=8, minutes=minutes_after_8am)
                if due_at <= start_from:
                    continue
                db.add(Reminder(
                    appointment_id=appointment_id,
                    drug_name=item.drug_name,
                    dosage=item.dosage,
                    due_at=due_at,
                    status=ReminderStatus.PENDING,
                ))
                created += 1
    db.commit()
    return created


def cancel_reminders_for_appointment(db: Session, appointment_id: UUID) -> int:
    pending = db.query(Reminder).filter(
        Reminder.appointment_id == appointment_id,
        Reminder.status == ReminderStatus.PENDING,
    ).all()
    for r in pending:
        r.status = ReminderStatus.CANCELLED
    if pending:
        db.commit()
    return len(pending)


def get_due_reminders(db: Session) -> list:
    now = datetime.utcnow()
    return db.query(Reminder).filter(
        Reminder.status == ReminderStatus.PENDING,
        Reminder.due_at <= now,
    ).all()
