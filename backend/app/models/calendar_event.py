from sqlalchemy import Column, String, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base
from app.models.base import TimestampMixin, UUID_PK, ValuedEnum


class CalendarOwnerType(str, enum.Enum):
    PATIENT = "patient"
    DOCTOR = "doctor"


class CalendarEvent(Base, TimestampMixin):
    """
    Tracks the Google Calendar event ID created for an appointment, per
    owner (patient and doctor each get their own event on their own
    calendar). Storing the event_id lets us update/delete the correct
    event on reschedule or cancellation instead of guessing.
    """
    __tablename__ = "calendar_events"

    id = UUID_PK()
    appointment_id = Column(UUID(as_uuid=True), ForeignKey("appointments.id", ondelete="CASCADE"), nullable=False, index=True)
    owner_type = Column(ValuedEnum(CalendarOwnerType), nullable=False)
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    google_event_id = Column(String(255), nullable=True)
    sync_failed = Column(String(10), default="false")

    appointment = relationship("Appointment", back_populates="calendar_events")
