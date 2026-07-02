"""
Google Calendar integration via OAuth 2.0.

Flow:
1. User (patient or doctor) hits GET /api/calendar/oauth/start -> redirected
   to Google's consent screen.
2. Google redirects back to GOOGLE_REDIRECT_URI with a `code`.
3. We exchange the code for access + refresh tokens and store them in
   GoogleOAuthToken, keyed by user_id.
4. On booking/reschedule/cancellation, calendar_service creates/updates/
   deletes an event on each linked user's calendar using their stored
   refresh token (silently minted into a fresh access token as needed).

If a user has never connected Google Calendar, calendar sync is skipped
gracefully — the appointment and email flows are NOT blocked by missing
calendar credentials (graceful degradation, same philosophy as LLM failures).
"""
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.google_token import GoogleOAuthToken

logger = logging.getLogger("calendar_service")

CLIENT_CONFIG = {
    "web": {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
}


def build_auth_url(state: str) -> str:
    flow = Flow.from_client_config(CLIENT_CONFIG, scopes=settings.google_scopes_list)
    flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=state,
    )
    return auth_url


def exchange_code_for_tokens(db: Session, user_id: UUID, code: str) -> GoogleOAuthToken:
    flow = Flow.from_client_config(CLIENT_CONFIG, scopes=settings.google_scopes_list)
    flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
    flow.fetch_token(code=code)
    creds = flow.credentials

    token_row = db.query(GoogleOAuthToken).filter(GoogleOAuthToken.user_id == user_id).first()
    if not token_row:
        token_row = GoogleOAuthToken(user_id=user_id)
        db.add(token_row)

    token_row.access_token = creds.token
    token_row.refresh_token = creds.refresh_token or token_row.refresh_token
    token_row.token_expiry = creds.expiry
    token_row.scope = " ".join(creds.scopes or [])
    db.commit()
    db.refresh(token_row)
    return token_row


def _get_credentials(db: Session, user_id: UUID) -> Optional[Credentials]:
    token_row = db.query(GoogleOAuthToken).filter(GoogleOAuthToken.user_id == user_id).first()
    if not token_row or not token_row.refresh_token:
        return None

    creds = Credentials(
        token=token_row.access_token,
        refresh_token=token_row.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=settings.google_scopes_list,
    )
    if creds.expired:
        try:
            creds.refresh(GoogleRequest())
            token_row.access_token = creds.token
            token_row.token_expiry = creds.expiry
            db.commit()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to refresh Google token for user %s: %s", user_id, exc)
            return None
    return creds


def create_event(db: Session, user_id: UUID, summary: str, description: str,
                  start: datetime, end: datetime) -> Optional[str]:
    """Returns the created google_event_id, or None if the user has no calendar linked or the API call failed."""
    creds = _get_credentials(db, user_id)
    if not creds:
        return None
    try:
        service = build("calendar", "v3", credentials=creds)
        event = service.events().insert(
            calendarId="primary",
            body={
                "summary": summary,
                "description": description,
                "start": {"dateTime": start.isoformat()},
                "end": {"dateTime": end.isoformat()},
                "reminders": {"useDefault": True},
            },
        ).execute()
        return event.get("id")
    except HttpError as exc:
        logger.error("Google Calendar create_event failed for user %s: %s", user_id, exc)
        return None


def update_event(db: Session, user_id: UUID, google_event_id: str, summary: str,
                  description: str, start: datetime, end: datetime) -> bool:
    creds = _get_credentials(db, user_id)
    if not creds:
        return False
    try:
        service = build("calendar", "v3", credentials=creds)
        service.events().patch(
            calendarId="primary",
            eventId=google_event_id,
            body={
                "summary": summary,
                "description": description,
                "start": {"dateTime": start.isoformat()},
                "end": {"dateTime": end.isoformat()},
            },
        ).execute()
        return True
    except HttpError as exc:
        logger.error("Google Calendar update_event failed for user %s: %s", user_id, exc)
        return False


def delete_event(db: Session, user_id: UUID, google_event_id: str) -> bool:
    creds = _get_credentials(db, user_id)
    if not creds:
        return False
    try:
        service = build("calendar", "v3", credentials=creds)
        service.events().delete(calendarId="primary", eventId=google_event_id).execute()
        return True
    except HttpError as exc:
        logger.error("Google Calendar delete_event failed for user %s: %s", user_id, exc)
        return False
