"""
Pydantic schemas for calendar/scheduling operations.
"""
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field
from app.shared.types import WeDoBaseModel


class AvailabilityRequest(WeDoBaseModel):
    """Request to check interviewer availability."""
    interviewer_email: EmailStr
    date: datetime
    duration_minutes: int = Field(default=60, ge=15, le=480)


class TimeSlot(BaseModel):
    """Available time slot."""
    start: datetime
    end: datetime
    duration_minutes: int


class FindMeetingTimeRequest(WeDoBaseModel):
    """Request to find best meeting times."""
    organizer_email: EmailStr
    interviewer_emails: list[EmailStr]
    candidate_email: EmailStr
    duration_minutes: int = Field(default=60, ge=15, le=480)
    preferred_days: list[str] | None = Field(
        default=None,
        description="List of preferred days: Mon, Tue, Wed, Thu, Fri"
    )


class ScheduleInterviewRequest(WeDoBaseModel):
    """Request to schedule an interview."""
    organizer_email: EmailStr
    candidate_name: str = Field(min_length=1, max_length=200)
    candidate_email: EmailStr
    interviewer_emails: list[EmailStr]
    position: str = Field(min_length=1, max_length=200)
    start_time: datetime
    duration_minutes: int = Field(default=60, ge=15, le=480)
    location: str | None = Field(default=None, max_length=200)
    as_teams_meeting: bool = True
    notes: str | None = Field(default=None, max_length=2000)
    company_id: str | None = Field(
        default=None,
        description="Company ID. When set, uses stored per-company delegated OAuth credentials "
                    "for Microsoft Calendar (if available) instead of app-level token.",
    )


class CancelInterviewRequest(WeDoBaseModel):
    """Request to cancel an interview."""
    organizer_email: EmailStr
    event_id: str
    cancellation_message: str | None = Field(default=None, max_length=500)


class RescheduleInterviewRequest(WeDoBaseModel):
    """Request to reschedule an interview."""
    organizer_email: EmailStr
    event_id: str
    new_start_time: datetime
    new_duration_minutes: int | None = Field(default=None, ge=15, le=480)


class CalendarEventResponse(BaseModel):
    """Calendar event response."""
    id: str
    subject: str
    start: datetime
    end: datetime
    location: str | None = None
    is_online_meeting: bool = False
    organizer_email: str
    attendees: list[str]


class MeetingSuggestion(BaseModel):
    """Meeting time suggestion from Graph API."""
    confidence: float
    start_time: datetime
    end_time: datetime
    locations: list[str] | None = None
    suggestion_reason: str | None = None
