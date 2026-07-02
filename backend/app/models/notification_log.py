import enum
from sqlalchemy import Column, String, ForeignKey, Enum, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin, UUID_PK, ValuedEnum


class NotificationType(str, enum.Enum):
    BOOKING_CONFIRMATION = "booking_confirmation"
    REMINDER = "reminder"
    CANCELLATION = "cancellation"
    LEAVE_CONFLICT = "leave_conflict"
    MEDICATION_REMINDER = "medication_reminder"
    RESCHEDULE = "reschedule"


class NotificationStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    EXHAUSTED = "exhausted"  # retried max times, gave up


class NotificationLog(Base, TimestampMixin):
    """
    Every outbound email is logged here BEFORE sending. This is what makes
    notification delivery reliable: if the SMTP call throws or times out, the
    row stays PENDING/FAILED with a retry_count, and the background
    scheduler's retry job picks it back up — instead of the email silently
    vanishing if the request crashes mid-send.
    """
    __tablename__ = "notification_logs"

    id = UUID_PK()
    appointment_id = Column(UUID(as_uuid=True), ForeignKey("appointments.id", ondelete="CASCADE"), nullable=True, index=True)
    recipient_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    recipient_email = Column(String(255), nullable=False)
    notification_type = Column(ValuedEnum(NotificationType), nullable=False)
    subject = Column(String(500), nullable=False)
    body_preview = Column(Text, nullable=True)
    status = Column(ValuedEnum(NotificationStatus), nullable=False, default=NotificationStatus.PENDING, index=True)
    retry_count = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)

    appointment = relationship("Appointment", back_populates="notifications")
