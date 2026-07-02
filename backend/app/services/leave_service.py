"""
Doctor leave management. The brief specifically calls out:
"When a doctor is marked on leave for a date with existing bookings,
affected patients must be notified" — this is the core requirement
implemented here.
"""
from datetime import date as date_cls
from uuid import UUID
from sqlalchemy import cast, Date
from sqlalchemy.orm import Session

from app.models.leave import Leave
from app.models.appointment import Appointment, AppointmentStatus
from app.services import appointment_service


async def create_leave_and_resolve_conflicts(
    db: Session, doctor_id: UUID, start_date: date_cls, end_date: date_cls, reason: str = ""
) -> dict:
    """
    Creates the Leave row, then finds every HELD/CONFIRMED appointment in the
    affected date range and cancels each one with status CANCELLED_BY_LEAVE,
    triggering the patient notification + calendar cleanup flow. Returns a
    summary so the admin/doctor UI can show "3 appointments were affected
    and patients notified."
    """
    leave = Leave(doctor_id=doctor_id, start_date=start_date, end_date=end_date, reason=reason)
    db.add(leave)
    db.commit()
    db.refresh(leave)

    affected = db.query(Appointment).filter(
        Appointment.doctor_id == doctor_id,
        Appointment.status.in_([AppointmentStatus.HELD, AppointmentStatus.CONFIRMED]),
        cast(Appointment.slot_start, Date) >= start_date,
        cast(Appointment.slot_start, Date) <= end_date,
    ).all()

    cancelled_ids = []
    for appt in affected:
        await appointment_service.cancel_appointment(
            db, appt, AppointmentStatus.CANCELLED_BY_LEAVE,
            reason=f"Doctor on leave: {reason}" if reason else "Doctor on leave",
        )
        cancelled_ids.append(str(appt.id))

    return {
        "leave_id": str(leave.id),
        "affected_appointments": len(affected),
        "cancelled_appointment_ids": cancelled_ids,
    }
