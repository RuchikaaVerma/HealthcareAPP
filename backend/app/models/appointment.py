"""
Appointment is the core transactional entity.

Concurrency-safety design (see system design doc for full rationale):
- A UNIQUE constraint on (doctor_id, slot_start) for rows where status is
  HELD or CONFIRMED prevents two confirmed/held bookings from ever
  occupying the same slot, even under simultaneous requests. Postgres
  enforces this atomically at the DB level — the real source of truth,
  not just an application-level check.
- New bookings are created as HELD first (a short-lived hold), then
  promoted to CONFIRMED only after symptom form + confirmation succeed.
  Expired holds are released by the background scheduler.
- CANCELLED/CANCELLED_BY_LEAVE rows are excluded from the unique index
  (via a partial index — see migration) so a cancelled slot can be rebooked.
"""
import enum
from sqlalchemy import Column, String, ForeignKey, DateTime, Text, Enum, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin, UUID_PK, ValuedEnum


class AppointmentStatus(str, enum.Enum):
    HELD = "held"                          # temporary hold while patient fills symptom form
    CONFIRMED = "confirmed"                # booking finalized
    CANCELLED_BY_PATIENT = "cancelled_by_patient"
    CANCELLED_BY_DOCTOR = "cancelled_by_doctor"
    CANCELLED_BY_LEAVE = "cancelled_by_leave"   # auto-cancelled because doctor went on leave
    COMPLETED = "completed"
    NO_SHOW = "no_show"


class UrgencyLevel(str, enum.Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class Appointment(Base, TimestampMixin):
    __tablename__ = "appointments"

    id = UUID_PK()
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("doctors.id", ondelete="RESTRICT"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False, index=True)

    slot_start = Column(DateTime(timezone=True), nullable=False, index=True)
    slot_end = Column(DateTime(timezone=True), nullable=False)
    status = Column(ValuedEnum(AppointmentStatus), nullable=False, default=AppointmentStatus.HELD, index=True)
    hold_expires_at = Column(DateTime(timezone=True), nullable=True)  # null once CONFIRMED

    # Pre-visit (patient-submitted symptom form + LLM output)
    symptoms_text = Column(Text, nullable=True)
    ai_urgency_level = Column(ValuedEnum(UrgencyLevel), nullable=True)
    ai_chief_complaint = Column(Text, nullable=True)
    ai_suggested_questions = Column(Text, nullable=True)  # JSON-encoded list of 3 strings
    ai_pre_visit_raw = Column(Text, nullable=True)         # raw LLM response, for audit/debug
    ai_pre_visit_failed = Column(Integer, default=0)        # 0/1 flag — true if LLM failed and fallback used

    # Post-visit (doctor notes + LLM patient-friendly summary)
    doctor_notes = Column(Text, nullable=True)
    prescription_text = Column(Text, nullable=True)  # JSON-encoded list of {drug, dosage, frequency, duration}
    ai_post_visit_summary = Column(Text, nullable=True)
    ai_post_visit_failed = Column(Integer, default=0)

    cancellation_reason = Column(String(500), nullable=True)

    doctor = relationship("Doctor", back_populates="appointments")
    patient = relationship("Patient", back_populates="appointments")
    calendar_events = relationship("CalendarEvent", back_populates="appointment", cascade="all, delete-orphan")
    reminders = relationship("Reminder", back_populates="appointment", cascade="all, delete-orphan")
    notifications = relationship("NotificationLog", back_populates="appointment", cascade="all, delete-orphan")
