"""
Microsoft Graph API endpoints for Teams, Calendar, and Bookings integration.

Provides endpoints for:
- Creating Teams meetings with calendar events
- Testing Microsoft Graph connectivity
- Managing Microsoft Bookings
"""
import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, EmailStr

from app.shared.services.microsoft_graph_service import AttendeeType, MeetingAttendee, microsoft_graph_service
from fastapi import Depends
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item
from app.shared.errors import LIAError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/microsoft", tags=["microsoft-graph"])


class CreateTeamsMeetingRequest(WeDoBaseModel):
    """Request to create a Teams meeting with calendar event."""
    organizer_email: EmailStr
    subject: str
    start_time: datetime
    duration_minutes: int = 60
    attendees: list[dict] | None = None
    body_content: str | None = None
    location: str | None = None
    timezone: str = "America/Sao_Paulo"
    send_invites: bool = True


class TeamsOnlineMeetingResponse(BaseModel):
    """Response for Teams meeting creation."""
    id: str
    join_url: str
    join_web_url: str
    subject: str
    start_time: datetime
    end_time: datetime
    organizer_email: str
    attendees: list[str]
    calendar_event_id: str | None
    dial_in_url: str | None


class ConnectionStatusResponse(BaseModel):
    """Response for connection status check."""
    status: str
    message: str
    configured: bool
    organization: dict | None = None


class BookingsBusinessResponse(BaseModel):
    """Response for Bookings business."""
    id: str
    display_name: str
    business_type: str | None
    public_url: str | None


class CreateBookingsAppointmentRequest(WeDoBaseModel):
    """Request to create a Bookings appointment."""
    business_id: str
    service_id: str
    customer_email: EmailStr
    customer_name: str
    start_time: datetime
    duration_minutes: int = 60
    staff_member_ids: list[str] | None = None
    notes: str | None = None
    timezone: str = "America/Sao_Paulo"


@router.get("/status", response_model=ConnectionStatusResponse)
async def check_connection_status(company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Check Microsoft Graph API connection status.
    
    Returns connection status and organization details if connected.
    """
    result = await microsoft_graph_service.test_connection()
    return ConnectionStatusResponse(**result)


@router.post("/meetings/teams", response_model=TeamsOnlineMeetingResponse)
async def create_teams_meeting(request: CreateTeamsMeetingRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Create a Teams meeting with calendar event.
    
    This creates an Outlook calendar event with a Teams meeting link
    and sends calendar invites to all attendees.
    
    Returns:
        Meeting details including the Teams join URL
    """
    if not microsoft_graph_service.is_configured:
        raise HTTPException(
            status_code=503,
            detail="Microsoft Graph service not configured. Please set AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, and AZURE_TENANT_ID."
        )
    
    try:
        attendees = None
        if request.attendees:
            attendees = [
                MeetingAttendee(
                    email=att.get("email"),
                    name=att.get("name", att.get("email")),
                    type=AttendeeType(att.get("type", "required"))
                )
                for att in request.attendees
            ]
        
        meeting = await microsoft_graph_service.create_teams_meeting_with_calendar_event(
            organizer_email=request.organizer_email,
            subject=request.subject,
            start_time=request.start_time,
            duration_minutes=request.duration_minutes,
            attendees=attendees,
            body_content=request.body_content,
            location=request.location,
            timezone=request.timezone,
            send_invites=request.send_invites
        )
        
        return TeamsOnlineMeetingResponse(
            id=meeting.id,
            join_url=meeting.join_url,
            join_web_url=meeting.join_web_url,
            subject=meeting.subject,
            start_time=meeting.start_time,
            end_time=meeting.end_time,
            organizer_email=meeting.organizer_email,
            attendees=meeting.attendees,
            calendar_event_id=meeting.calendar_event_id,
            dial_in_url=meeting.dial_in_url
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create Teams meeting: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.post("/meetings/standalone", response_model=None)
async def create_standalone_teams_meeting(
    organizer_email: EmailStr,
    subject: str,
    start_time: datetime,
    duration_minutes: int = 60,
    attendee_emails: list[str] | None = None, 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Create a standalone Teams meeting (without calendar event).
    
    Use this for ad-hoc meetings that don't need calendar integration.
    """
    if not microsoft_graph_service.is_configured:
        raise HTTPException(
            status_code=503,
            detail="Microsoft Graph service not configured"
        )
    
    try:
        result = await microsoft_graph_service.create_standalone_teams_meeting(
            organizer_email=organizer_email,
            subject=subject,
            start_time=start_time,
            duration_minutes=duration_minutes,
            attendees=attendee_emails
        )
        
        return {
            "id": result.get("id"),
            "join_url": result.get("joinWebUrl"),
            "subject": result.get("subject"),
            "start_time": result.get("startDateTime"),
            "end_time": result.get("endDateTime")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create standalone meeting: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.get("/calendar/events/{event_id}", response_model=None)
async def get_calendar_event(
    event_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    user_email: EmailStr = Query(..., description="Email of the calendar owner"), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get details of a calendar event.
    """
    if not microsoft_graph_service.is_configured:
        raise HTTPException(status_code=503, detail="Microsoft Graph service not configured")
    
    try:
        event = await microsoft_graph_service.get_calendar_event(
            user_email=user_email,
            event_id=event_id
        )
        
        return {
            "id": event.id,
            "subject": event.subject,
            "start_time": event.start_time,
            "end_time": event.end_time,
            "location": event.location,
            "is_online_meeting": event.is_online_meeting,
            "online_meeting_url": event.online_meeting_url,
            "web_link": event.web_link
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get calendar event: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.delete("/calendar/events/{event_id}", response_model=None)
async def cancel_calendar_event(
    event_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    user_email: EmailStr = Query(..., description="Email of the calendar owner"),
    cancellation_message: str | None = None, 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Cancel a calendar event and notify attendees.
    """
    if not microsoft_graph_service.is_configured:
        raise HTTPException(status_code=503, detail="Microsoft Graph service not configured")
    
    try:
        await microsoft_graph_service.cancel_calendar_event(
            user_email=user_email,
            event_id=event_id,
            comment=cancellation_message
        )
        
        return {"status": "cancelled", "event_id": event_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel event: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.get("/bookings/businesses", response_model=list[dict])
async def list_bookings_businesses(company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    List all Microsoft Bookings businesses.
    """
    if not microsoft_graph_service.is_configured:
        raise HTTPException(status_code=503, detail="Microsoft Graph service not configured")
    
    try:
        businesses = await microsoft_graph_service.get_bookings_businesses()
        return [
            {
                "id": b.get("id"),
                "display_name": b.get("displayName"),
                "business_type": b.get("businessType"),
                "public_url": b.get("publicUrl")
            }
            for b in businesses
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list Bookings businesses: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.get("/bookings/businesses/{business_id}/services", response_model=None)
async def list_bookings_services(business_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)], company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    List services for a Bookings business.
    """
    if not microsoft_graph_service.is_configured:
        raise HTTPException(status_code=503, detail="Microsoft Graph service not configured")
    
    try:
        services = await microsoft_graph_service.get_bookings_services(business_id)
        return [
            {
                "id": s.get("id"),
                "display_name": s.get("displayName"),
                "description": s.get("description"),
                "default_duration": s.get("defaultDuration")
            }
            for s in services
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list Bookings services: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.get("/bookings/businesses/{business_id}/booking-page-url", response_model=None)
async def get_booking_page_url(business_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)], company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get the public booking page URL for a business.
    """
    if not microsoft_graph_service.is_configured:
        raise HTTPException(status_code=503, detail="Microsoft Graph service not configured")
    
    try:
        url = await microsoft_graph_service.get_booking_page_url(business_id)
        return {"booking_page_url": url}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get booking page URL: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.post("/bookings/appointments", response_model=None)
async def create_bookings_appointment(request: CreateBookingsAppointmentRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Create an appointment in Microsoft Bookings.
    """
    if not microsoft_graph_service.is_configured:
        raise HTTPException(status_code=503, detail="Microsoft Graph service not configured")
    
    try:
        result = await microsoft_graph_service.create_bookings_appointment(
            business_id=request.business_id,
            service_id=request.service_id,
            customer_email=request.customer_email,
            customer_name=request.customer_name,
            start_time=request.start_time,
            duration_minutes=request.duration_minutes,
            staff_member_ids=request.staff_member_ids,
            notes=request.notes,
            timezone=request.timezone
        )
        
        return {
            "id": result.get("id"),
            "service_id": result.get("serviceId"),
            "customer_email": result.get("customerEmailAddress"),
            "start_time": result.get("startDateTime", {}).get("dateTime"),
            "end_time": result.get("endDateTime", {}).get("dateTime"),
            "join_web_url": result.get("joinWebUrl")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create Bookings appointment: {e}")
        raise LIAError(message="Erro interno do servidor")

reorder_collection_before_item(router)
