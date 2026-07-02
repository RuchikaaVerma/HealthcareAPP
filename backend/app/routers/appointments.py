import json
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_role, get_current_user
from app.models.user import User, UserRole
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.appointment import Appointment, AppointmentStatus
from app.schemas.appointment import (
    AppointmentHoldRequest, AppointmentHoldOut, SymptomFormSubmit, AppointmentOut,
    CancelAppointmentRequest, PostVisitSubmit,
)
from app.services import slot_service, llm_service, appointment_service, reminder_service

router = APIRouter(prefix="/api/appointments", tags=["appointments"])

require_patient = require_role(UserRole.PATIENT)
require_doctor = require_role(UserRole.DOCTOR)


def _get_patient_or_404(db: Session, user: User) -> Patient:
    patient = db.query(Patient).filter(Patient.user_id == user.id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    return patient


def _get_doctor_or_404(db: Session, user: User) -> Doctor:
    doctor = db.query(Doctor).filter(Doctor.user_id == user.id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor profile not found")
    return doctor


@router.post("/hold", response_model=AppointmentHoldOut, status_code=201)
def hold_appointment(payload: AppointmentHoldRequest, db: Session = Depends(get_db), user: User = Depends(require_patient)):
    """
    Step 1 of booking: reserve the slot (HELD status) while the patient
    fills the symptom form. This is the "slot hold mechanism" — it prevents
    two patients from both seeing a slot as available and racing to confirm
    it, since the DB unique constraint blocks any second HELD/CONFIRMED row.
    """
    patient = _get_patient_or_404(db, user)
    appointment = slot_service.hold_slot(db, payload.doctor_id, patient.id, payload.slot_start)
    return appointment


@router.post("/confirm", response_model=AppointmentOut)
async def confirm_appointment(payload: SymptomFormSubmit, db: Session = Depends(get_db), user: User = Depends(require_patient)):
    """
    Step 2 of booking: patient submits symptoms, LLM generates the pre-visit
    summary, the hold is promoted to CONFIRMED, and calendar/email sync runs.
    """
    patient = _get_patient_or_404(db, user)
    appointment = db.query(Appointment).filter(
        Appointment.id == payload.appointment_id,
        Appointment.patient_id == patient.id,
    ).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Held appointment not found")
    if appointment.status != AppointmentStatus.HELD:
        raise HTTPException(status_code=400, detail="This appointment is not in a holdable state (it may have expired)")

    ai_result = llm_service.generate_pre_visit_summary(payload.symptoms_text)

    appointment.symptoms_text = payload.symptoms_text
    appointment.ai_urgency_level = ai_result["urgency_level"]
    appointment.ai_chief_complaint = ai_result["chief_complaint"]
    appointment.ai_suggested_questions = json.dumps(ai_result["suggested_questions"])
    appointment.ai_pre_visit_raw = ai_result.get("raw")
    appointment.ai_pre_visit_failed = 1 if ai_result["failed"] else 0
    appointment.status = AppointmentStatus.CONFIRMED
    appointment.hold_expires_at = None
    db.commit()
    db.refresh(appointment)

    await appointment_service.finalize_booking(db, appointment)
    db.refresh(appointment)
    return appointment


@router.get("/me", response_model=list[AppointmentOut])
def my_appointments(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role == UserRole.PATIENT:
        patient = _get_patient_or_404(db, user)
        return db.query(Appointment).filter(Appointment.patient_id == patient.id).order_by(Appointment.slot_start.desc()).all()
    elif user.role == UserRole.DOCTOR:
        doctor = _get_doctor_or_404(db, user)
        return db.query(Appointment).filter(Appointment.doctor_id == doctor.id).order_by(Appointment.slot_start.desc()).all()
    raise HTTPException(status_code=403, detail="Admins do not have a personal appointment list")


@router.get("/{appointment_id}", response_model=AppointmentOut)
def get_appointment(appointment_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    # authorization: must be the owning patient, the assigned doctor, or an admin
    if user.role == UserRole.PATIENT:
        patient = _get_patient_or_404(db, user)
        if appointment.patient_id != patient.id:
            raise HTTPException(status_code=403, detail="Not your appointment")
    elif user.role == UserRole.DOCTOR:
        doctor = _get_doctor_or_404(db, user)
        if appointment.doctor_id != doctor.id:
            raise HTTPException(status_code=403, detail="Not your appointment")
    return appointment


@router.post("/{appointment_id}/cancel", response_model=AppointmentOut)
async def cancel(appointment_id: UUID, payload: CancelAppointmentRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if user.role == UserRole.PATIENT:
        patient = _get_patient_or_404(db, user)
        if appointment.patient_id != patient.id:
            raise HTTPException(status_code=403, detail="Not your appointment")
        new_status = AppointmentStatus.CANCELLED_BY_PATIENT
    elif user.role == UserRole.DOCTOR:
        doctor = _get_doctor_or_404(db, user)
        if appointment.doctor_id != doctor.id:
            raise HTTPException(status_code=403, detail="Not your appointment")
        new_status = AppointmentStatus.CANCELLED_BY_DOCTOR
    else:
        new_status = AppointmentStatus.CANCELLED_BY_DOCTOR  # admin override

    await appointment_service.cancel_appointment(db, appointment, new_status, payload.reason or "")
    db.refresh(appointment)
    return appointment


@router.post("/post-visit", response_model=AppointmentOut)
def submit_post_visit(payload: PostVisitSubmit, db: Session = Depends(get_db), user: User = Depends(require_doctor)):
    """Doctor submits notes + prescription; LLM generates patient-friendly summary; reminders are scheduled."""
    doctor = _get_doctor_or_404(db, user)
    appointment = db.query(Appointment).filter(
        Appointment.id == payload.appointment_id,
        Appointment.doctor_id == doctor.id,
    ).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    prescriptions_dicts = [p.model_dump() for p in payload.prescriptions]
    ai_result = llm_service.generate_post_visit_summary(payload.doctor_notes, prescriptions_dicts)

    appointment.doctor_notes = payload.doctor_notes
    appointment.prescription_text = json.dumps(prescriptions_dicts)
    appointment.ai_post_visit_summary = json.dumps({
        "summary": ai_result["summary"],
        "medication_schedule": ai_result["medication_schedule"],
        "follow_up_steps": ai_result["follow_up_steps"],
    })
    appointment.ai_post_visit_failed = 1 if ai_result["failed"] else 0
    appointment.status = AppointmentStatus.COMPLETED
    db.commit()
    db.refresh(appointment)

    reminder_service.schedule_reminders_for_prescriptions(db, appointment.id, payload.prescriptions)

    return appointment
