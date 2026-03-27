"""
Pydantic schemas for calendar/scheduling operations.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime


class AvailabilityRequest(BaseModel):
    """Request to check interviewer availability."""
    interviewer_email: EmailStr
    date: datetime
    duration_minutes: int = Field(default=60, ge=15, le=480)


class TimeSlot(BaseModel):
    """Available time slot."""
    start: datetime
    end: datetime
    duration_minutes: int


class FindMeetingTimeRequest(BaseModel):
    """Request to find best meeting times."""
    organizer_email: EmailStr
    interviewer_emails: List[EmailStr]
    candidate_email: EmailStr
    duration_minutes: int = Field(default=60, ge=15, le=480)
    preferred_days: Optional[List[str]] = Field(
        default=None,
        description="List of preferred days: Mon, Tue, Wed, Thu, Fri"
    )


class ScheduleInterviewRequest(BaseModel):
    """Request to schedule an interview."""
    organizer_email: EmailStr
    candidate_name: str = Field(min_length=1, max_length=200)
    candidate_email: EmailStr
    interviewer_emails: List[EmailStr]
    position: str = Field(min_length=1, max_length=200)
    start_time: datetime
    duration_minutes: int = Field(default=60, ge=15, le=480)
    location: Optional[str] = Field(default=None, max_length=200)
    as_teams_meeting: bool = True
    notes: Optional[str] = Field(default=None, max_length=2000)


class CancelInterviewRequest(BaseModel):
    """Request to cancel an interview."""
    organizer_email: EmailStr
    event_id: str
    cancellation_message: Optional[str] = Field(default=None, max_length=500)


class RescheduleInterviewRequest(BaseModel):
    """Request to reschedule an interview."""
    organizer_email: EmailStr
    event_id: str
    new_start_time: datetime
    new_duration_minutes: Optional[int] = Field(default=None, ge=15, le=480)


class CalendarEventResponse(BaseModel):
    """Calendar event response."""
    id: str
    subject: str
    start: datetime
    end: datetime
    location: Optional[str] = None
    is_online_meeting: bool = False
    organizer_email: str
    attendees: List[str]


class MeetingSuggestion(BaseModel):
    """Meeting time suggestion from Graph API."""
    confidence: float
    start_time: datetime
    end_time: datetime
    locations: Optional[List[str]] = None
    suggestion_reason: Optional[str] = None
