"""
User table: holds login credentials and role for ALL account types
(admin, doctor, patient). Doctor/Patient tables hold role-specific profile data
and link back to this table 1:1 via user_id.
"""
import enum
from sqlalchemy import Column, String, Boolean, Enum
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin, UUID_PK, ValuedEnum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    DOCTOR = "doctor"
    PATIENT = "patient"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = UUID_PK()
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(30), nullable=True)
    role = Column(ValuedEnum(UserRole), nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)

    doctor_profile = relationship("Doctor", back_populates="user", uselist=False, cascade="all, delete-orphan")
    patient_profile = relationship("Patient", back_populates="user", uselist=False, cascade="all, delete-orphan")
