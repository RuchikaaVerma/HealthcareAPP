import enum
from sqlalchemy import Column, DateTime, ForeignKey, String, Enum, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin, UUID_PK, ValuedEnum


class ReminderStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Reminder(Base, TimestampMixin):
    """
    One row per scheduled medication reminder dose. Generated when a
    prescription is saved (see services/reminder_service.py), which expands
    "twice daily for 5 days" into individual timestamped reminder rows.
    The APScheduler background job polls for PENDING rows whose due time
    has passed and sends the email, marking SENT or FAILED.
    """
    __tablename__ = "reminders"

    id = UUID_PK()
    appointment_id = Column(UUID(as_uuid=True), ForeignKey("appointments.id", ondelete="CASCADE"), nullable=False, index=True)
    drug_name = Column(String(255), nullable=False)
    dosage = Column(String(100), nullable=True)
    due_at = Column(DateTime(timezone=True), nullable=False, index=True)
    status = Column(ValuedEnum(ReminderStatus), nullable=False, default=ReminderStatus.PENDING, index=True)
    retry_count = Column(Integer, default=0)

    appointment = relationship("Appointment", back_populates="reminders")
