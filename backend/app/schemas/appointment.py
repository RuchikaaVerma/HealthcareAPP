from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from app.models.appointment import AppointmentStatus, UrgencyLevel


class SlotQuery(BaseModel):
    doctor_id: UUID
    date: str  # YYYY-MM-DD — returns available slots for this single day


class AvailableSlot(BaseModel):
    slot_start: datetime
    slot_end: datetime


class AppointmentHoldRequest(BaseModel):
    doctor_id: UUID
    slot_start: datetime


class AppointmentHoldOut(BaseModel):
    id: UUID
    doctor_id: UUID
    slot_start: datetime
    slot_end: datetime
    status: AppointmentStatus
    hold_expires_at: Optional[datetime]

    class Config:
        from_attributes = True


class SymptomFormSubmit(BaseModel):
    appointment_id: UUID
    symptoms_text: str = Field(min_length=5, max_length=3000)


class AppointmentOut(BaseModel):
    id: UUID
    doctor_id: UUID
    patient_id: UUID
    slot_start: datetime
    slot_end: datetime
    status: AppointmentStatus
    symptoms_text: Optional[str] = None
    ai_urgency_level: Optional[UrgencyLevel] = None
    ai_chief_complaint: Optional[str] = None
    ai_suggested_questions: Optional[str] = None  # JSON string, frontend parses
    ai_pre_visit_failed: Optional[int] = 0
    doctor_notes: Optional[str] = None
    prescription_text: Optional[str] = None
    ai_post_visit_summary: Optional[str] = None
    ai_post_visit_failed: Optional[int] = 0
    cancellation_reason: Optional[str] = None

    class Config:
        from_attributes = True


class CancelAppointmentRequest(BaseModel):
    reason: Optional[str] = None


class PrescriptionItem(BaseModel):
    drug_name: str
    dosage: str
    frequency_per_day: int = Field(ge=1, le=6)
    duration_days: int = Field(ge=1, le=90)
    instructions: Optional[str] = None


class PostVisitSubmit(BaseModel):
    appointment_id: UUID
    doctor_notes: str = Field(min_length=5, max_length=5000)
    prescriptions: List[PrescriptionItem] = []
