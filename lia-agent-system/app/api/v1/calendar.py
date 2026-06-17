"""
Calendar/Interview scheduling API endpoints.

Provedores suportados:
- Microsoft Graph (padrão, /calendar/*)
- Google Calendar (opcional, /calendar/google/*)
  Requer ENABLE_GOOGLE_CALENDAR=True e credenciais configuradas por empresa.
"""
import hashlib
import hmac
import logging
from urllib.parse import urlencode
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.domains.interview_scheduling.repositories.calendar_credentials_repository import CalendarCredentialsRepository
from app.domains.interview_scheduling.services.calendar_service import calendar_service
from app.schemas.calendar import (
    AvailabilityRequest,
    CancelInterviewRequest,
    FindMeetingTimeRequest,
    RescheduleInterviewRequest,
    ScheduleInterviewRequest,
    TimeSlot,
)
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match
from app.shared.errors import LIAError, LIAInternalError
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/calendar", tags=["calendar"])


# TODO(phase2): extract to repository — calendar slot/booking DB calls
def check_graph_configured():
    """Dependency to check if Microsoft Graph is configured."""
    if not settings.AZURE_CLIENT_ID or not settings.AZURE_CLIENT_SECRET or not settings.AZURE_TENANT_ID:
        raise HTTPException(
            status_code=503,
            detail="Microsoft Graph API not configured. Set AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, and AZURE_TENANT_ID."
        )


class CalendarHealthResponse(BaseModel):
    status: str
    service: str
    graph_configured: bool


@router.get("/health", response_model=CalendarHealthResponse)
async def calendar_health(company_id: str = Depends(require_company_id)):
    # multi-tenancy: public endpoint (health) — no tenant data
    """Health check for calendar integration."""
    is_configured = (
        settings.AZURE_CLIENT_ID is not None and
        settings.AZURE_CLIENT_SECRET is not None and
        settings.AZURE_TENANT_ID is not None
    )
    
    return {
        "status": "healthy",
        "service": "calendar-api",
        "graph_configured": is_configured
    }


@router.post("/availability", response_model=list[TimeSlot], dependencies=[Depends(check_graph_configured)])
async def check_availability(request: AvailabilityRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Check interviewer availability for a specific date.
    Returns available time slots.
    """
    try:
        slots = await calendar_service.check_interviewer_availability(
            interviewer_email=request.interviewer_email,
            date=request.date,
            duration_minutes=request.duration_minutes
        )
        
        return [
            TimeSlot(
                start=datetime.fromisoformat(slot["start"]),
                end=datetime.fromisoformat(slot["end"]),
                duration_minutes=slot["duration_minutes"]
            )
            for slot in slots
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking availability: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.post("/find-meeting-times", response_model=list[dict], dependencies=[Depends(check_graph_configured)])
async def find_meeting_times(request: FindMeetingTimeRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Find best meeting times for interview using Microsoft Graph findMeetingTimes API.
    Returns suggested meeting times sorted by confidence.
    """
    try:
        suggestions = await calendar_service.find_best_interview_time(
            organizer_email=request.organizer_email,
            interviewer_emails=request.interviewer_emails,
            candidate_email=request.candidate_email,
            duration_minutes=request.duration_minutes,
            preferred_days=request.preferred_days
        )
        
        return suggestions
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding meeting times: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.post("/schedule-interview", response_model=dict)
async def schedule_interview(
    http_request: Request,
    body: ScheduleInterviewRequest,
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Schedule an interview appointment.
    Creates calendar event and sends invitations to all attendees.

    Provider selection (Google / Microsoft delegated / Microsoft app-level) is handled
    inside CalendarService._get_client() based on stored per-company credentials.
    The Microsoft Graph config check is NOT enforced here so that Google-only companies
    can schedule interviews without Azure credentials being set.

    company_id in request body is optional. When provided it is validated against
    the authenticated user's tenant (request.state.company_id). Falls back to
    JWT company_id when body company_id is absent.
    """
    # Derive authoritative company_id from JWT (set by AuthEnforcementMiddleware)
    jwt_company_id: str | None = getattr(http_request.state, "company_id", None) or None
    caller_role: str = getattr(http_request.state, "user_role", "") or ""

    # Validate body company_id against JWT tenant (strict for non-admins)
    if body.company_id:
        _assert_company_access(http_request, body.company_id)
        effective_company_id = body.company_id
    else:
        # Fail closed: non-platform roles must have a company context
        if caller_role not in ("super_admin", "platform_admin") and not jwt_company_id:
            raise HTTPException(
                status_code=403,
                detail="Forbidden — no company context in authentication token.",
            )
        effective_company_id = jwt_company_id

    try:
        event = await calendar_service.schedule_interview(
            organizer_email=body.organizer_email,
            candidate_name=body.candidate_name,
            candidate_email=body.candidate_email,
            interviewer_emails=body.interviewer_emails,
            position=body.position,
            start_time=body.start_time,
            duration_minutes=body.duration_minutes,
            location=body.location,
            as_teams_meeting=body.as_teams_meeting,
            notes=body.notes,
            company_id=effective_company_id,
            db=db,
        )
        
        return {
            "status": "scheduled",
            "event": event
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scheduling interview: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


class CancelInterviewResponse(BaseModel):
    status: str
    event_id: str


@router.post("/cancel-interview", dependencies=[Depends(check_graph_configured)], response_model=CancelInterviewResponse)
async def cancel_interview(request: CancelInterviewRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Cancel a scheduled interview.
    Sends cancellation notification to all attendees.
    """
    try:
        success = await calendar_service.cancel_interview(
            organizer_email=request.organizer_email,
            event_id=request.event_id,
            cancellation_message=request.cancellation_message
        )
        
        if not success:
            raise LIAError(message="Failed to cancel interview")
        
        return {"status": "cancelled", "event_id": request.event_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling interview: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.post("/reschedule-interview", response_model=dict, dependencies=[Depends(check_graph_configured)])
async def reschedule_interview(request: RescheduleInterviewRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Reschedule an existing interview to a new time.
    Sends update notification to all attendees.
    """
    try:
        updated_event = await calendar_service.reschedule_interview(
            organizer_email=request.organizer_email,
            event_id=request.event_id,
            new_start_time=request.new_start_time,
            new_duration_minutes=request.new_duration_minutes
        )
        
        return {
            "status": "rescheduled",
            "event": updated_event
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rescheduling interview: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


# ---------------------------------------------------------------------------
# Google Calendar endpoints
# ---------------------------------------------------------------------------

def check_google_calendar_configured():
    """Dependency: check if Google Calendar integration is enabled."""
    if not settings.ENABLE_GOOGLE_CALENDAR:
        raise HTTPException(
            status_code=503,
            detail="Google Calendar integration is disabled. Set ENABLE_GOOGLE_CALENDAR=True.",
        )


class GoogleScheduleInterviewRequest(WeDoBaseModel):
    attendees: list[str] = Field(..., description="Attendee email addresses")
    organizer_email: str = Field(..., description="Organizer / calendar owner email")
    start_time: datetime = Field(..., description="Interview start time (UTC)")
    duration_minutes: int = Field(default=60, ge=15, le=480)
    summary: str = Field(..., description="Event title")
    description: str = Field(default="", description="Event description / notes")
    create_meet_link: bool = Field(default=True, description="Create Google Meet link")


class GoogleCancelInterviewRequest(WeDoBaseModel):
    event_id: str = Field(..., description="Google Calendar event ID")
    calendar_id: str = Field(default="primary", description="Calendar ID or organizer email")


class GoogleAvailabilityRequest(WeDoBaseModel):
    organizer_email: str
    attendees: list[str]
    duration_minutes: int = Field(default=60, ge=15, le=480)
    start: datetime
    end: datetime


class GoogleCalendarHealthResponse(BaseModel):
    status: str
    service: str
    enabled: bool
    service_account_configured: bool
    oauth_client_configured: bool


@router.get("/google/health", response_model=GoogleCalendarHealthResponse)
async def google_calendar_health(company_id: str = Depends(require_company_id)):
    # multi-tenancy: public endpoint (health) — no tenant data
    """Health check for Google Calendar integration."""
    return {
        "status": "healthy",
        "service": "google-calendar-api",
        "enabled": settings.ENABLE_GOOGLE_CALENDAR,
        "service_account_configured": settings.GOOGLE_CALENDAR_SERVICE_ACCOUNT_JSON is not None,
        "oauth_client_configured": (
            settings.GOOGLE_CALENDAR_CLIENT_ID is not None
            and settings.GOOGLE_CALENDAR_CLIENT_SECRET is not None
        ),
    }


class GoogleAvailabilitySlotsResponse(BaseModel):
    slots: list[dict]


@router.post("/google/availability", dependencies=[Depends(check_google_calendar_configured)], response_model=GoogleAvailabilitySlotsResponse)
async def google_check_availability(request: GoogleAvailabilityRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Check attendee availability using Google Calendar freebusy API.
    Returns list of available time slots.
    """
    try:
        from app.shared.services.google_calendar_client import GoogleCalendarClient
        client = GoogleCalendarClient()
        slots = await client.get_available_slots(
            organizer_email=request.organizer_email,
            attendees=request.attendees,
            duration_minutes=request.duration_minutes,
            start=request.start,
            end=request.end,
        )
        return {"slots": [s.to_dict() for s in slots]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error checking Google Calendar availability: %s", e, exc_info=True)
        raise LIAError(message="Erro interno do servidor")


class GoogleScheduleInterviewResponse(BaseModel):
    status: str
    event: dict


@router.post("/google/schedule-interview", dependencies=[Depends(check_google_calendar_configured)], response_model=GoogleScheduleInterviewResponse)
async def google_schedule_interview(request: GoogleScheduleInterviewRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Create a Google Calendar event for an interview with optional Google Meet link.
    """
    try:
        from app.shared.services.google_calendar_client import GoogleCalendarClient
        client = GoogleCalendarClient()
        event = await client.create_calendar_event(
            attendees=request.attendees,
            start_time=request.start_time,
            duration_minutes=request.duration_minutes,
            summary=request.summary,
            description=request.description,
            create_meet_link=request.create_meet_link,
            organizer_email=request.organizer_email,
        )
        return {"status": "scheduled", "event": event}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error scheduling Google Calendar interview: %s", e, exc_info=True)
        raise LIAError(message="Erro interno do servidor")


class GoogleCancelInterviewResponse(BaseModel):
    status: str
    event_id: str


@router.post("/google/cancel-interview", dependencies=[Depends(check_google_calendar_configured)], response_model=GoogleCancelInterviewResponse)
async def google_cancel_interview(request: GoogleCancelInterviewRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Cancel a Google Calendar event and notify attendees.
    """
    try:
        from app.shared.services.google_calendar_client import GoogleCalendarClient
        client = GoogleCalendarClient()
        success = await client.delete_calendar_event(
            event_id=request.event_id,
            calendar_id=request.calendar_id,
        )
        if not success:
            raise LIAError(message="Failed to cancel Google Calendar event.")
        return {"status": "cancelled", "event_id": request.event_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error cancelling Google Calendar interview: %s", e, exc_info=True)
        raise LIAError(message="Erro interno do servidor")


# ---------------------------------------------------------------------------
# OAuth 2.0 flow for Google Calendar (company-level)
# ---------------------------------------------------------------------------

class GoogleOAuthAuthUrlResponse(BaseModel):
    auth_url: str
    state: str


@router.get("/google/auth-url", dependencies=[Depends(check_google_calendar_configured)], response_model=GoogleOAuthAuthUrlResponse)
async def google_oauth_auth_url(
    request: Request,
    company_id: str = Query(..., description="Company ID"),
    _gate: str = Depends(require_company_id_strict_match("query.company_id")),
):
    # multi-tenancy: gated via require_company_id_strict_match (JWT vs query.company_id) — 403 on mismatch (Task #1143)
    """
    Generate Google OAuth authorization URL.
    Frontend redirects the user (admin) to this URL to grant calendar access.
    Caller must belong to the same company (tenant-scoped).
    """
    _assert_company_access(request, company_id)
    if not settings.GOOGLE_CALENDAR_CLIENT_ID or not settings.GOOGLE_CALENDAR_OAUTH_REDIRECT_URI:
        raise HTTPException(
            status_code=503,
            detail="Google Calendar OAuth not configured. Set GOOGLE_CALENDAR_CLIENT_ID and GOOGLE_CALENDAR_OAUTH_REDIRECT_URI.",
        )
    try:
        from google_auth_oauthlib.flow import Flow  # type: ignore[union-attr]
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.GOOGLE_CALENDAR_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CALENDAR_CLIENT_SECRET,
                    "redirect_uris": [settings.GOOGLE_CALENDAR_OAUTH_REDIRECT_URI],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=["https://www.googleapis.com/auth/calendar"],
        )
        flow.redirect_uri = settings.GOOGLE_CALENDAR_OAUTH_REDIRECT_URI
        # CSRF protection: HMAC-sign the company_id so the callback can verify it
        sig = hmac.new(
            settings.SECRET_KEY.encode(), company_id.encode(), hashlib.sha256
        ).hexdigest()
        csrf_state = f"{company_id}:{sig}"
        auth_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            state=csrf_state,
            prompt="consent",
        )
        return {"auth_url": auth_url, "state": csrf_state}
    except ImportError:
        raise LIAInternalError("google-auth-oauthlib is required for OAuth flow. pip install google-auth-oauthlib")


class GoogleOAuthCallbackResponse(BaseModel):
    status: str
    company_id: str
    provider: str


@router.get("/google/callback", dependencies=[Depends(check_google_calendar_configured)], response_model=GoogleOAuthCallbackResponse)
async def google_oauth_callback(
    code: str = Query(...),
    state: str = Query(..., description="company_id passed as OAuth state"),
):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Handle Google OAuth callback. Exchanges code for tokens and stores
    encrypted credentials in company_calendar_credentials.
    """
    if not settings.GOOGLE_CALENDAR_CLIENT_ID or not settings.GOOGLE_CALENDAR_OAUTH_REDIRECT_URI:
        raise HTTPException(status_code=503, detail="Google Calendar OAuth not fully configured.")

    # Verify HMAC-signed state to prevent CSRF
    parts = state.split(":", 1)
    if len(parts) != 2:
        raise HTTPException(status_code=400, detail="OAuth state inválido")
    company_id_str, provided_sig = parts
    expected_sig = hmac.new(
        settings.SECRET_KEY.encode(), company_id_str.encode(), hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(provided_sig, expected_sig):
        raise HTTPException(status_code=400, detail="OAuth state inválido — possível CSRF")

    try:
        import json
        import uuid

        from google_auth_oauthlib.flow import Flow  # type: ignore[union-attr]

        from app.core.database import AsyncSessionLocal
        from app.models.company_calendar_credentials import CompanyCalendarCredentials
        from app.shared.encryption import encrypt_value

        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.GOOGLE_CALENDAR_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CALENDAR_CLIENT_SECRET,
                    "redirect_uris": [settings.GOOGLE_CALENDAR_OAUTH_REDIRECT_URI],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=["https://www.googleapis.com/auth/calendar"],
            state=state,
        )
        flow.redirect_uri = settings.GOOGLE_CALENDAR_OAUTH_REDIRECT_URI
        flow.fetch_token(code=code)

        creds = flow.credentials
        token_data = json.dumps({
            "access_token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": list(creds.scopes or []),
            "expiry": creds.expiry.isoformat() if creds.expiry else None,
        })

        async with AsyncSessionLocal() as db:
            repo = CalendarCredentialsRepository(db)
            await repo.upsert_credentials(
                company_id=uuid.UUID(company_id_str),
                provider="google",
                encrypted_credentials=encrypt_value(token_data),
                is_active=True,
                timezone=settings.GOOGLE_CALENDAR_DEFAULT_TIMEZONE,
            )
            await db.commit()

        return {"status": "connected", "company_id": company_id_str, "provider": "google"}

    except ImportError:
        raise LIAError(message="google-auth-oauthlib required. pip install google-auth-oauthlib")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error in Google OAuth callback: %s", e, exc_info=True)
        raise LIAError(message="Erro interno do servidor")


# ---------------------------------------------------------------------------
# Microsoft Calendar delegated OAuth 2.0 (per-company user-level access)
# ---------------------------------------------------------------------------

def check_microsoft_oauth_configured():
    """Dependency: check if Microsoft delegated OAuth is configured."""
    if not all([settings.AZURE_CLIENT_ID, settings.AZURE_CLIENT_SECRET, settings.AZURE_TENANT_ID]):
        raise HTTPException(
            status_code=503,
            detail="Microsoft Calendar OAuth not configured. Set AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID.",
        )
    if not settings.MICROSOFT_CALENDAR_OAUTH_REDIRECT_URI:
        raise HTTPException(
            status_code=503,
            detail="MICROSOFT_CALENDAR_OAUTH_REDIRECT_URI not set.",
        )


class MicrosoftOAuthAuthUrlResponse(BaseModel):
    auth_url: str
    state: str


def _assert_company_access(request: Request, company_id: str) -> None:
    """
    Validate that the authenticated caller's company matches the requested company_id.

    - Super-admins and platform_admins may manage any tenant.
    - All other roles must have a company_id in their JWT and it must match.
    - Fails closed: if caller_company_id is absent (token lacks company context), raises 403
      to prevent unauthenticated or misconfigured tokens from bypassing tenant isolation.

    Raises 403 if access is denied.
    """
    caller_company_id: str | None = getattr(request.state, "company_id", None) or None
    caller_role: str = getattr(request.state, "user_role", "") or ""

    # Platform-level roles bypass tenant isolation
    if caller_role in ("super_admin", "platform_admin"):
        return

    # Fail closed: require an authenticated company context
    if not caller_company_id:
        raise HTTPException(
            status_code=403,
            detail="Forbidden — no company context in authentication token.",
        )

    if str(caller_company_id) != str(company_id):
        raise HTTPException(
            status_code=403,
            detail="Forbidden — company_id does not match your authenticated tenant.",
        )


@router.get("/microsoft/auth-url", dependencies=[Depends(check_microsoft_oauth_configured)], response_model=MicrosoftOAuthAuthUrlResponse)
async def microsoft_oauth_auth_url(
    request: Request,
    company_id: str = Query(..., description="Company ID"),
    _gate: str = Depends(require_company_id_strict_match("query.company_id")),
):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Generate Microsoft OAuth authorization URL for delegated calendar access.
    Frontend redirects the company admin to this URL to grant calendar permissions.
    Uses MSAL authorization code flow with offline_access + Calendars.ReadWrite scopes.
    """
    _assert_company_access(request, company_id)
    # HMAC-signed state for CSRF protection (mirrors Google pattern)
    sig = hmac.new(
        settings.SECRET_KEY.encode(), company_id.encode(), hashlib.sha256
    ).hexdigest()
    csrf_state = f"{company_id}:{sig}"

    scopes = "offline_access Calendars.ReadWrite"
    tenant = settings.AZURE_TENANT_ID
    params = urlencode({
        "client_id": settings.AZURE_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": settings.MICROSOFT_CALENDAR_OAUTH_REDIRECT_URI,
        "response_mode": "query",
        "scope": scopes,
        "state": csrf_state,
        "prompt": "consent",
    })
    auth_url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize?{params}"
    return {"auth_url": auth_url, "state": csrf_state}


class MicrosoftOAuthCallbackResponse(BaseModel):
    status: str
    company_id: str
    provider: str


@router.get("/microsoft/callback", response_model=MicrosoftOAuthCallbackResponse)
async def microsoft_oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Handle Microsoft OAuth callback. Exchanges authorization code for tokens
    and stores encrypted credentials in company_calendar_credentials.
    """
    if not all([settings.AZURE_CLIENT_ID, settings.AZURE_CLIENT_SECRET,
                settings.AZURE_TENANT_ID, settings.MICROSOFT_CALENDAR_OAUTH_REDIRECT_URI]):
        raise HTTPException(status_code=503, detail="Microsoft Calendar OAuth not fully configured.")

    # Verify HMAC-signed state (CSRF protection)
    parts = state.split(":", 1)
    if len(parts) != 2:
        raise HTTPException(status_code=400, detail="OAuth state inválido")
    company_id_str, provided_sig = parts
    expected_sig = hmac.new(
        settings.SECRET_KEY.encode(), company_id_str.encode(), hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(provided_sig, expected_sig):
        raise HTTPException(status_code=400, detail="OAuth state inválido — possível CSRF")

    try:
        import json
        import uuid

        import httpx as _httpx

        from app.core.database import AsyncSessionLocal
        from app.shared.encryption import encrypt_value

        token_url = f"https://login.microsoftonline.com/{settings.AZURE_TENANT_ID}/oauth2/v2.0/token"
        data = {
            "client_id": settings.AZURE_CLIENT_ID,
            "client_secret": settings.AZURE_CLIENT_SECRET,
            "code": code,
            "redirect_uri": settings.MICROSOFT_CALENDAR_OAUTH_REDIRECT_URI,
            "grant_type": "authorization_code",
            "scope": "offline_access Calendars.ReadWrite",
        }

        async with _httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(token_url, data=data)

        if resp.status_code != 200:
            logger.error("Microsoft token exchange failed: %s — %s", resp.status_code, resp.text[:500])
            raise HTTPException(status_code=502, detail=f"Microsoft token exchange failed: {resp.status_code}")

        token_data_raw = resp.json()
        token_data = json.dumps({
            "access_token": token_data_raw.get("access_token"),
            "refresh_token": token_data_raw.get("refresh_token"),
            "token_type": token_data_raw.get("token_type"),
            "expires_in": token_data_raw.get("expires_in"),
            "scope": token_data_raw.get("scope"),
            "client_id": settings.AZURE_CLIENT_ID,
            "tenant_id": settings.AZURE_TENANT_ID,
        })

        async with AsyncSessionLocal() as db:
            repo = CalendarCredentialsRepository(db)
            await repo.upsert_credentials(
                company_id=uuid.UUID(company_id_str),
                provider="microsoft",
                encrypted_credentials=encrypt_value(token_data),
                is_active=True,
                timezone=settings.MICROSOFT_CALENDAR_DEFAULT_TIMEZONE,
            )
            await db.commit()

        return {"status": "connected", "company_id": company_id_str, "provider": "microsoft"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error in Microsoft OAuth callback: %s", e, exc_info=True)
        raise LIAError(message="Erro interno do servidor")


class MicrosoftOAuthStatusResponse(BaseModel):
    company_id: str
    provider: str
    connected: bool
    is_active: bool | None
    timezone: str | None
    message: str


@router.get("/microsoft/oauth-status", response_model=MicrosoftOAuthStatusResponse)
async def microsoft_oauth_status(
    request: Request,
    company_id: str = Query(..., description="Company ID"),
    _gate: str = Depends(require_company_id_strict_match("query.company_id")),
):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Return Microsoft Calendar OAuth connection status for a company.
    Queries company_calendar_credentials without making external calls.
    Caller must belong to the same company (tenant-scoped).
    """
    _assert_company_access(request, company_id)
    try:
        import uuid
        from app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            repo = CalendarCredentialsRepository(db)
            creds = await repo.get_credentials(uuid.UUID(company_id), "microsoft")
    except HTTPException:
        raise
    except Exception as e:
        raise LIAError(message="Erro interno do servidor")

    if creds and creds.is_active:
        return {
            "company_id": company_id,
            "provider": "microsoft",
            "connected": True,
            "is_active": creds.is_active,
            "timezone": creds.timezone,
            "message": "Microsoft Calendar OAuth credentials stored and active.",
        }
    return {
        "company_id": company_id,
        "provider": "microsoft",
        "connected": False,
        "is_active": getattr(creds, "is_active", None),
        "timezone": getattr(creds, "timezone", None),
        "message": (
            "Microsoft Calendar not connected for this company. "
            "Complete the OAuth flow via GET /api/v1/calendar/microsoft/auth-url."
        ),
    }


class GoogleOAuthStatusResponse(BaseModel):
    company_id: str
    provider: str
    connected: bool
    is_active: bool | None
    timezone: str | None
    message: str


@router.get("/google/oauth-status", dependencies=[Depends(check_google_calendar_configured)], response_model=GoogleOAuthStatusResponse)
async def google_oauth_status(
    request: Request,
    company_id: str = Query(..., description="Company ID"),
    _gate: str = Depends(require_company_id_strict_match("query.company_id")),
):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Return the current Google Calendar OAuth connection status for a company.
    Caller must belong to the same company (tenant-scoped).

    Queries the encrypted credentials store (company_calendar_credentials).
    Does NOT refresh tokens or make external calls.
    """
    _assert_company_access(request, company_id)
    try:
        import uuid
        from app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            repo = CalendarCredentialsRepository(db)
            creds = await repo.get_credentials(uuid.UUID(company_id), "google")
    except HTTPException:
        raise
    except Exception as e:
        raise LIAError(message="Erro interno do servidor")

    if creds and creds.is_active:
        return {
            "company_id": company_id,
            "provider": "google",
            "connected": True,
            "is_active": creds.is_active,
            "timezone": creds.timezone,
            "message": "Google Calendar OAuth credentials stored and active.",
        }
    return {
        "company_id": company_id,
        "provider": "google",
        "connected": False,
        "is_active": getattr(creds, "is_active", None),
        "timezone": getattr(creds, "timezone", None),
        "message": (
            "Google Calendar not connected for this company. "
            "Complete the OAuth flow via GET /api/v1/calendar/google/auth-url."
        ),
    }
