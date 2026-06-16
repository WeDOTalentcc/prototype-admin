"""
Pydantic schemas for calendar/scheduling operations.
"""
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field
from app.shared.types import WeDoBaseModel


# Sprint F.3 #25 canonical-fix: AvailabilityRequest moved to schemas/calendar.py
from app.schemas.calendar import AvailabilityRequest  # noqa: F401  (re-export for backward compat)


# Sprint F.3 #25 canonical-fix: TimeSlot moved to schemas/calendar.py
from app.schemas.calendar import TimeSlot  # noqa: F401  (re-export for backward compat)


# Sprint F.3 #25 canonical-fix: FindMeetingTimeRequest moved to schemas/calendar.py
from app.schemas.calendar import FindMeetingTimeRequest  # noqa: F401  (re-export for backward compat)


# DUPLICATE_OF_INTENT: app/schemas/calendar.py — re-export pattern, fields verified identical (Sprint Q.1 triagem I bucket)
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


# Sprint F.3 #25 canonical-fix: CancelInterviewRequest moved to schemas/calendar.py
from app.schemas.calendar import CancelInterviewRequest  # noqa: F401  (re-export for backward compat)


# DUPLICATE_OF_INTENT: app/schemas/calendar.py — re-export pattern, fields verified identical (Sprint Q.1 triagem I bucket)
class RescheduleInterviewRequest(WeDoBaseModel):
    """Request to reschedule an interview."""
    organizer_email: EmailStr
    event_id: str
    new_start_time: datetime
    new_duration_minutes: int | None = Field(default=None, ge=15, le=480)


# Sprint F.3 #25 canonical-fix: CalendarEventResponse moved to schemas/calendar.py
from app.schemas.calendar import CalendarEventResponse  # noqa: F401  (re-export for backward compat)


# Sprint F.3 #25 canonical-fix: MeetingSuggestion moved to schemas/calendar.py
from app.schemas.calendar import MeetingSuggestion  # noqa: F401  (re-export for backward compat)
