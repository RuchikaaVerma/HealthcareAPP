from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
from app.models.base import TimestampMixin, UUID_PK


class GoogleOAuthToken(Base, TimestampMixin):
    """
    Stores Google OAuth 2.0 tokens per user so the backend can create/update/
    delete calendar events on their behalf without re-prompting consent each
    time. access_token is short-lived; refresh_token is used to mint new
    access tokens silently (see services/calendar_service.py).

    NOTE: In a real production deployment, encrypt these at rest (e.g. via
    pgcrypto or an application-level Fernet key) rather than storing plaintext.
    """
    __tablename__ = "google_oauth_tokens"

    id = UUID_PK()
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    access_token = Column(String(2048), nullable=False)
    refresh_token = Column(String(2048), nullable=True)
    token_expiry = Column(DateTime(timezone=True), nullable=True)
    scope = Column(String(500), nullable=True)
