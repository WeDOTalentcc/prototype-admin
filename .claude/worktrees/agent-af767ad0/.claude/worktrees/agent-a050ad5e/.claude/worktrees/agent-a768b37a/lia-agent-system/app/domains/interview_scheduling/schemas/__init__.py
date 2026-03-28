"""Interview & Scheduling Domain - Schema definitions."""
from app.domains.interview_scheduling.schemas.calendar import (
    AvailabilityRequest,
    TimeSlot,
    FindMeetingTimeRequest,
    ScheduleInterviewRequest,
    CancelInterviewRequest,
    RescheduleInterviewRequest,
    CalendarEventResponse,
    MeetingSuggestion,
)
from app.domains.interview_scheduling.schemas.interview_scheduling_state import (
    InterviewParticipant,
    InterviewSchedulingState,
)

__all__ = [
    "AvailabilityRequest",
    "TimeSlot",
    "FindMeetingTimeRequest",
    "ScheduleInterviewRequest",
    "CancelInterviewRequest",
    "RescheduleInterviewRequest",
    "CalendarEventResponse",
    "MeetingSuggestion",
    "InterviewParticipant",
    "InterviewSchedulingState",
]
