from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.doctor import Doctor
from app.models.user import User
from app.schemas.doctor import DoctorOut
from app.schemas.appointment import AvailableSlot
from app.services import slot_service

router = APIRouter(prefix="/api/doctors", tags=["doctors"])


def _doctor_to_out(d: Doctor, user: User) -> DoctorOut:
    return DoctorOut(
        id=d.id, full_name=user.full_name, email=user.email,
        specialisation=d.specialisation, bio=d.bio,
        slot_duration_minutes=d.slot_duration_minutes, working_hours=d.working_hours,
    )


@router.get("", response_model=list[DoctorOut])
def search_doctors(specialisation: Optional[str] = Query(None), db: Session = Depends(get_db)):
    query = db.query(Doctor)
    if specialisation:
        query = query.filter(Doctor.specialisation.ilike(f"%{specialisation}%"))
    doctors = query.all()
    return [_doctor_to_out(d, db.query(User).filter(User.id == d.user_id).first()) for d in doctors]


@router.get("/{doctor_id}/slots", response_model=list[AvailableSlot])
def get_slots(doctor_id: str, date: str = Query(..., description="YYYY-MM-DD"), db: Session = Depends(get_db)):
    day = datetime.strptime(date, "%Y-%m-%d").date()
    slots = slot_service.get_available_slots(db, doctor_id, day)
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    duration_minutes = doctor.slot_duration_minutes if doctor else 30
    return [
        AvailableSlot(slot_start=s, slot_end=s + timedelta(minutes=duration_minutes))
        for s in slots
    ]
