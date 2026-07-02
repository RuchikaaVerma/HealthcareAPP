from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime

from app.core.database import get_db
from app.core.deps import require_role
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.models.doctor import Doctor, WorkingHours
from app.schemas.doctor import DoctorCreate, DoctorUpdate, DoctorOut, LeaveCreate, LeaveOut
from app.services import leave_service

router = APIRouter(prefix="/api/admin", tags=["admin"])
require_admin = require_role(UserRole.ADMIN)


@router.post("/doctors", response_model=DoctorOut, status_code=201)
def create_doctor(payload: DoctorCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="An account with this email already exists")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        phone=payload.phone,
        role=UserRole.DOCTOR,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    doctor = Doctor(
        user_id=user.id,
        specialisation=payload.specialisation,
        bio=payload.bio,
        slot_duration_minutes=payload.slot_duration_minutes,
    )
    db.add(doctor)
    db.commit()
    db.refresh(doctor)

    for wh in payload.working_hours:
        db.add(WorkingHours(doctor_id=doctor.id, day_of_week=wh.day_of_week,
                             start_time=wh.start_time, end_time=wh.end_time))
    db.commit()
    db.refresh(doctor)

    return _doctor_to_out(doctor, user)


def _doctor_to_out(doctor: Doctor, user: User) -> DoctorOut:
    return DoctorOut(
        id=doctor.id, full_name=user.full_name, email=user.email,
        specialisation=doctor.specialisation, bio=doctor.bio,
        slot_duration_minutes=doctor.slot_duration_minutes,
        working_hours=doctor.working_hours,
    )


@router.get("/doctors", response_model=list[DoctorOut])
def list_doctors(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    doctors = db.query(Doctor).all()
    return [_doctor_to_out(d, db.query(User).filter(User.id == d.user_id).first()) for d in doctors]


@router.patch("/doctors/{doctor_id}", response_model=DoctorOut)
def update_doctor(doctor_id: UUID, payload: DoctorUpdate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(doctor, field, value)
    db.commit()
    db.refresh(doctor)
    return _doctor_to_out(doctor, db.query(User).filter(User.id == doctor.user_id).first())


@router.post("/doctors/{doctor_id}/leave", status_code=201)
async def add_leave(doctor_id: UUID, payload: LeaveCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    start = datetime.strptime(payload.start_date, "%Y-%m-%d").date()
    end = datetime.strptime(payload.end_date, "%Y-%m-%d").date()
    if end < start:
        raise HTTPException(status_code=400, detail="end_date must be on or after start_date")

    result = await leave_service.create_leave_and_resolve_conflicts(db, doctor_id, start, end, payload.reason or "")
    return result


@router.delete("/doctors/{doctor_id}", status_code=204)
def delete_doctor(doctor_id: UUID, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    from sqlalchemy.exc import IntegrityError
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
        
    user = db.query(User).filter(User.id == doctor.user_id).first()
    if user:
        try:
            db.delete(user)
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=400, 
                detail="Cannot delete this doctor because they have existing patient appointments. Instead, edit their profile to mark them as not accepting new patients."
            )
    return None
