"""
Doctor profile + weekly working-hours configuration.
Admin manages these. WorkingHours defines the recurring weekly availability
template; actual bookable slots are computed dynamically from this template
minus existing appointments and leave days (see services/slot_service.py).
"""
from sqlalchemy import Column, String, Integer, ForeignKey, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin, UUID_PK


class Doctor(Base, TimestampMixin):
    __tablename__ = "doctors"

    id = UUID_PK()
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    specialisation = Column(String(150), nullable=False, index=True)
    bio = Column(String(1000), nullable=True)
    slot_duration_minutes = Column(Integer, nullable=False, default=30)
    is_accepting_patients = Column(String(10), default="true")  # admin can pause intake without deleting profile

    user = relationship("User", back_populates="doctor_profile")
    working_hours = relationship("WorkingHours", back_populates="doctor", cascade="all, delete-orphan")
    leaves = relationship("Leave", back_populates="doctor", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="doctor")


class WorkingHours(Base, TimestampMixin):
    """One row per weekday the doctor is available. day_of_week: 0=Monday ... 6=Sunday."""
    __tablename__ = "working_hours"

    id = UUID_PK()
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False, index=True)
    day_of_week = Column(Integer, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

    doctor = relationship("Doctor", back_populates="working_hours")
