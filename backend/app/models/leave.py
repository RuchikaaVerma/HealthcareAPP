from sqlalchemy import Column, Date, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin, UUID_PK


class Leave(Base, TimestampMixin):
    """
    A date range during which a doctor is unavailable.
    When created, the service layer (see services/leave_service.py) finds all
    CONFIRMED/HELD appointments in this range, cancels them with status
    CANCELLED_BY_LEAVE, and triggers patient notification + calendar cleanup.
    """
    __tablename__ = "leaves"

    id = UUID_PK()
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False, index=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    reason = Column(String(500), nullable=True)

    doctor = relationship("Doctor", back_populates="leaves")
