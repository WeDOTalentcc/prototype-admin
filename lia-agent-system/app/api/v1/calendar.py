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
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.config import settings
from app.domains.interview_scheduling.services.calendar_service import calendar_service
from app.schemas.calendar import (
    AvailabilityRequest,
    CancelInterviewRequest,
    FindMeetingTimeRequest,
    RescheduleInterviewRequest,
    ScheduleInterviewRequest,
    TimeSlot,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/calendar", tags=["calendar"])


def check_graph_configured():
    """Dependency to check if Microsoft Graph is configured."""
    if not settings.AZURE_CLIENT_ID or not settings.AZURE_CLIENT_SECRET or not settings.AZURE_TENANT_ID:
        raise HTTPException(
            status_code=503,
            detail="Microsoft Graph API not configured. Set AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, and AZURE_TENANT_ID."
        )


@router.get("/health", response_model=None)
async def calendar_health():
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
async def check_availability(request: AvailabilityRequest):
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
        
    except Exception as e:
        logger.error(f"Error checking availability: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/find-meeting-times", response_model=list[dict], dependencies=[Depends(check_graph_configured)])
async def find_meeting_times(request: FindMeetingTimeRequest):
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
        
    except Exception as e:
        logger.error(f"Error finding meeting times: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schedule-interview", response_model=dict, dependencies=[Depends(check_graph_configured)])
async def schedule_interview(request: ScheduleInterviewRequest):
    """
    Schedule an interview appointment.
    Creates calendar event and sends invitations to all attendees.
    """
    try:
        event = await calendar_service.schedule_interview(
            organizer_email=request.organizer_email,
            candidate_name=request.candidate_name,
            candidate_email=request.candidate_email,
            interviewer_emails=request.interviewer_emails,
            position=request.position,
            start_time=request.start_time,
            duration_minutes=request.duration_minutes,
            location=request.location,
            as_teams_meeting=request.as_teams_meeting,
            notes=request.notes
        )
        
        return {
            "status": "scheduled",
            "event": event
        }
        
    except Exception as e:
        logger.error(f"Error scheduling interview: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cancel-interview", dependencies=[Depends(check_graph_configured)], response_model=None)
async def cancel_interview(request: CancelInterviewRequest):
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
            raise HTTPException(status_code=500, detail="Failed to cancel interview")
        
        return {"status": "cancelled", "event_id": request.event_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling interview: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reschedule-interview", response_model=dict, dependencies=[Depends(check_graph_configured)])
async def reschedule_interview(request: RescheduleInterviewRequest):
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
        
    except Exception as e:
        logger.error(f"Error rescheduling interview: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


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


class GoogleScheduleInterviewRequest(BaseModel):
    company_id: str = Field(..., description="Company ID (tenant)")
    attendees: list[str] = Field(..., description="Attendee email addresses")
    organizer_email: str = Field(..., description="Organizer / calendar owner email")
    start_time: datetime = Field(..., description="Interview start time (UTC)")
    duration_minutes: int = Field(default=60, ge=15, le=480)
    summary: str = Field(..., description="Event title")
    description: str = Field(default="", description="Event description / notes")
    create_meet_link: bool = Field(default=True, description="Create Google Meet link")


class GoogleCancelInterviewRequest(BaseModel):
    company_id: str
    event_id: str = Field(..., description="Google Calendar event ID")
    calendar_id: str = Field(default="primary", description="Calendar ID or organizer email")


class GoogleAvailabilityRequest(BaseModel):
    company_id: str
    organizer_email: str
    attendees: list[str]
    duration_minutes: int = Field(default=60, ge=15, le=480)
    start: datetime
    end: datetime


@router.get("/google/health", response_model=None)
async def google_calendar_health():
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


@router.post("/google/availability", dependencies=[Depends(check_google_calendar_configured)], response_model=None)
async def google_check_availability(request: GoogleAvailabilityRequest):
    """
    Check attendee availability using Google Calendar freebusy API.
    Returns list of available time slots.
    """
    try:
        from app.services.google_calendar_client import GoogleCalendarClient
        client = GoogleCalendarClient()
        slots = await client.get_available_slots(
            organizer_email=request.organizer_email,
            attendees=request.attendees,
            duration_minutes=request.duration_minutes,
            start=request.start,
            end=request.end,
        )
        return {"slots": [s.to_dict() for s in slots]}
    except Exception as e:
        logger.error("Error checking Google Calendar availability: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/google/schedule-interview", dependencies=[Depends(check_google_calendar_configured)], response_model=None)
async def google_schedule_interview(request: GoogleScheduleInterviewRequest):
    """
    Create a Google Calendar event for an interview with optional Google Meet link.
    """
    try:
        from app.services.google_calendar_client import GoogleCalendarClient
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
    except Exception as e:
        logger.error("Error scheduling Google Calendar interview: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/google/cancel-interview", dependencies=[Depends(check_google_calendar_configured)], response_model=None)
async def google_cancel_interview(request: GoogleCancelInterviewRequest):
    """
    Cancel a Google Calendar event and notify attendees.
    """
    try:
        from app.services.google_calendar_client import GoogleCalendarClient
        client = GoogleCalendarClient()
        success = await client.delete_calendar_event(
            event_id=request.event_id,
            calendar_id=request.calendar_id,
        )
        if not success:
            raise HTTPException(status_code=500, detail="Failed to cancel Google Calendar event.")
        return {"status": "cancelled", "event_id": request.event_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error cancelling Google Calendar interview: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# OAuth 2.0 flow for Google Calendar (company-level)
# ---------------------------------------------------------------------------

@router.get("/google/auth-url", dependencies=[Depends(check_google_calendar_configured)], response_model=None)
async def google_oauth_auth_url(company_id: str = Query(..., description="Company ID")):
    """
    Generate Google OAuth authorization URL.
    Frontend redirects the user (admin) to this URL to grant calendar access.
    """
    if not settings.GOOGLE_CALENDAR_CLIENT_ID or not settings.GOOGLE_CALENDAR_OAUTH_REDIRECT_URI:
        raise HTTPException(
            status_code=503,
            detail="Google Calendar OAuth not configured. Set GOOGLE_CALENDAR_CLIENT_ID and GOOGLE_CALENDAR_OAUTH_REDIRECT_URI.",
        )
    try:
        from google_auth_oauthlib.flow import Flow  # type: ignore
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
        raise HTTPException(
            status_code=500,
            detail="google-auth-oauthlib is required for OAuth flow. pip install google-auth-oauthlib",
        )


@router.get("/google/callback", dependencies=[Depends(check_google_calendar_configured)], response_model=None)
async def google_oauth_callback(
    code: str = Query(...),
    state: str = Query(..., description="company_id passed as OAuth state"),
):
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

        from google_auth_oauthlib.flow import Flow  # type: ignore

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
            existing = await db.execute(
                __import__("sqlalchemy", fromlist=["select"]).select(CompanyCalendarCredentials).where(
                    CompanyCalendarCredentials.company_id == uuid.UUID(company_id_str),
                    CompanyCalendarCredentials.provider == "google",
                )
            )
            record = existing.scalar_one_or_none()

            if record:
                record.encrypted_credentials = encrypt_value(token_data)
                record.is_active = True
            else:
                record = CompanyCalendarCredentials(
                    id=uuid.uuid4(),
                    company_id=uuid.UUID(company_id_str),
                    provider="google",
                    encrypted_credentials=encrypt_value(token_data),
                    is_active=True,
                    timezone=settings.GOOGLE_CALENDAR_DEFAULT_TIMEZONE,
                )
                db.add(record)
            await db.commit()

        return {"status": "connected", "company_id": company_id_str, "provider": "google"}

    except ImportError:
        raise HTTPException(status_code=500, detail="google-auth-oauthlib required. pip install google-auth-oauthlib")
    except Exception as e:
        logger.error("Error in Google OAuth callback: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
