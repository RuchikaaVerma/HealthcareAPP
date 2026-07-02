"""
Centralized application configuration.
All environment variables are loaded once here and imported elsewhere
as `from app.core.config import settings`.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    APP_NAME: str = "Healthcare Appointment Manager"
    APP_ENV: str = "development"
    APP_BASE_URL: str = "http://localhost:8000"
    FRONTEND_BASE_URL: str = "http://localhost:3000"
    SECRET_KEY: str = "change_me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/healthcare_db"

    # Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"
    LLM_MAX_RETRIES: int = 2
    LLM_TIMEOUT_SECONDS: int = 20

    # Email
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = "no-reply@example.com"
    MAIL_FROM_NAME: str = "Clinic"
    MAIL_SERVER: str = "smtp.sendgrid.net"
    MAIL_PORT: int = 587
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    EMAIL_MAX_RETRIES: int = 3

    # Google Calendar
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/calendar/oauth/callback"
    GOOGLE_SCOPES: str = "https://www.googleapis.com/auth/calendar.events"

    # Scheduler
    SCHEDULER_INTERVAL_MINUTES: int = 5

    # Slots
    DEFAULT_SLOT_DURATION_MINUTES: int = 30
    SLOT_HOLD_EXPIRY_SECONDS: int = 120

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def google_scopes_list(self) -> List[str]:
        return [s.strip() for s in self.GOOGLE_SCOPES.split(",") if s.strip()]


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
