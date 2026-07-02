"""
Google Calendar OAuth endpoints. Both patients and doctors hit these to
link their own calendar; the `state` param carries their user_id so the
callback knows whose tokens to store (in production, sign/encrypt state
rather than passing the raw UUID).
"""
from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.config import settings
from app.models.user import User
from app.models.google_token import GoogleOAuthToken
from app.services import calendar_service

router = APIRouter(prefix="/api/calendar", tags=["calendar"])


@router.get("/oauth/start")
def oauth_start(current_user: User = Depends(get_current_user)):
    auth_url = calendar_service.build_auth_url(state=str(current_user.id))
    return {"auth_url": auth_url}


@router.get("/oauth/callback")
def oauth_callback(code: str, state: str, db: Session = Depends(get_db)):
    """
    Google redirects here after consent. We exchange the code for tokens and
    store them, then redirect the browser back to the frontend with a
    success flag so the SPA can show a confirmation toast.
    """
    try:
        calendar_service.exchange_code_for_tokens(db, state, code)
    except Exception:  # noqa: BLE001
        return RedirectResponse(url=f"{settings.FRONTEND_BASE_URL}/settings?calendar_linked=false")
    return RedirectResponse(url=f"{settings.FRONTEND_BASE_URL}/settings?calendar_linked=true")


@router.get("/status")
def calendar_status(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    token = db.query(GoogleOAuthToken).filter(GoogleOAuthToken.user_id == current_user.id).first()
    return {"linked": bool(token and token.refresh_token)}
