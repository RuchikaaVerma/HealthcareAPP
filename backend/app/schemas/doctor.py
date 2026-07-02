from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from uuid import UUID
from datetime import time


class WorkingHoursIn(BaseModel):
    day_of_week: int = Field(ge=0, le=6, description="0=Monday ... 6=Sunday")
    start_time: time
    end_time: time


class WorkingHoursOut(WorkingHoursIn):
    id: UUID

    class Config:
        from_attributes = True


class DoctorCreate(BaseModel):
    """Used by admin to create a doctor account + profile in one call."""
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str
    phone: Optional[str] = None
    specialisation: str
    bio: Optional[str] = None
    slot_duration_minutes: int = 30
    working_hours: List[WorkingHoursIn] = []


class DoctorUpdate(BaseModel):
    specialisation: Optional[str] = None
    bio: Optional[str] = None
    slot_duration_minutes: Optional[int] = None
    is_accepting_patients: Optional[bool] = None


class DoctorOut(BaseModel):
    id: UUID
    full_name: str
    email: EmailStr
    specialisation: str
    bio: Optional[str] = None
    slot_duration_minutes: int
    working_hours: List[WorkingHoursOut] = []

    class Config:
        from_attributes = True


class LeaveCreate(BaseModel):
    start_date: str  # YYYY-MM-DD
    end_date: str
    reason: Optional[str] = None


class LeaveOut(BaseModel):
    id: UUID
    start_date: str
    end_date: str
    reason: Optional[str] = None

    class Config:
        from_attributes = True
