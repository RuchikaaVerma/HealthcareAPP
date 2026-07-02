"""Shared mixins for all ORM models."""
import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID


class TimestampMixin:
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


def gen_uuid():
    return uuid.uuid4()


UUID_PK = lambda: Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)  # noqa: E731


def ValuedEnum(enum_class, **kwargs):
    return Enum(enum_class, values_callable=lambda obj: [e.value for e in obj], **kwargs)
