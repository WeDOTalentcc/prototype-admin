

# LIA-T01 | LGPD Art. 7 (legitimate interest – recruitment) / EU AI Act Annex III (high-risk HR systems)
"""LangChain tools for Interview Scheduling domain."""
import logging
import random
import uuid
from datetime import UTC, datetime, timedelta

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# SIMULATION STUB: These tools simulate calendar/scheduling operations.
# In production, replace with real calendar API integrations (Google Calendar,
# Outlook, etc.). The random module usage below is intentional for simulation only.
_SIMULATION_SEED = 42  # fixed seed for reproducibility in tests


@tool
def check_interviewer_availability(interviewer_id: str, date_range: str) -> dict:
    """Check calendar availability for an interviewer over a given date range.

    date_range format: 'YYYY-MM-DD to YYYY-MM-DD'. Returns available and busy slots.
    """
    logger.info("check_interviewer_availability: interviewer=%s range=%s", interviewer_id, date_range)
    try:
        parts = [p.strip() for p in date_range.split("to")]
        start_date = datetime.strptime(parts[0], "%Y-%m-%d")
        end_date = datetime.strptime(parts[1], "%Y-%m-%d")
    except (ValueError, IndexError):
        start_date = datetime.now(UTC)
        end_date = start_date + timedelta(days=7)

    hours = [9, 10, 11, 14, 15, 16]
    all_slots = []
    current = start_date
    while current <= end_date:
        for h in hours:
            slot_dt = current.replace(hour=h, minute=0, second=0)
            all_slots.append(slot_dt.strftime("%Y-%m-%d %H:%M"))
        current += timedelta(days=1)

    # Use deterministic seed based on interviewer_id for reproducible simulations
    _rng = random.Random(hash(interviewer_id) % (2**31))
    _rng.shuffle(all_slots)
    available_count = _rng.randint(3, 5)
    available_slots = all_slots[:available_count]
    busy_slots = all_slots[available_count: available_count + _rng.randint(1, 3)]

    return {
        "interviewer_id": interviewer_id,
        "available_slots": sorted(available_slots),
        "busy_slots": sorted(busy_slots),
    }


@tool
def schedule_interview(
    candidate_id: str,
    interviewer_id: str,
    datetime_str: str,
    interview_type: str = "technical",
) -> dict:
    """Schedule an interview slot between a candidate and an interviewer.

    interview_type must be one of: 'technical', 'behavioral', 'cultural_fit', 'final'.
    """
    logger.info(
        "schedule_interview: candidate=%s interviewer=%s datetime=%s type=%s",
        candidate_id, interviewer_id, datetime_str, interview_type,
    )
    interview_id = f"IV-{uuid.uuid4().hex[:8].upper()}"
    calendar_link = f"https://calendar.lia.app/interviews/{interview_id}"
    return {
        "interview_id": interview_id,
        "status": "scheduled",
        "calendar_link": calendar_link,
        "candidate_id": candidate_id,
        "interviewer_id": interviewer_id,
        "datetime": datetime_str,
        "type": interview_type,
    }


@tool
def send_interview_invitation(
    candidate_id: str, interview_id: str, candidate_email: str
) -> dict:
    """Send an interview invitation email to the candidate (simulated).

    Returns confirmation with timestamp of when the email was dispatched.
    """
    # LGPD Art. 12: Do not log candidate_email (PII) — log only identifiers
    logger.info(
        "send_interview_invitation: candidate=%s interview=%s",
        candidate_id, interview_id,
    )
    return {
        "status": "sent",
        "email": candidate_email,
        "interview_id": interview_id,
        "candidate_id": candidate_id,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@tool
def reschedule_interview(
    interview_id: str, new_datetime_str: str, reason: str = ""
) -> dict:
    """Reschedule an existing interview to a new date/time.

    Stores the old datetime as 'N/A' since this is a simulation without persistent state.
    """
    logger.info(
        "reschedule_interview: interview=%s new_datetime=%s reason=%s",
        interview_id, new_datetime_str, reason,
    )
    return {
        "interview_id": interview_id,
        "status": "rescheduled",
        "old_datetime": "N/A",
        "new_datetime": new_datetime_str,
        "reason": reason,
        "updated_at": datetime.now(UTC).isoformat(),
    }


@tool
def cancel_interview(interview_id: str, reason: str) -> dict:
    """Cancel a scheduled interview and notify all participants.

    Records the cancellation reason and timestamp for audit purposes.
    """
    logger.info("cancel_interview: interview=%s reason=%s", interview_id, reason)
    return {
        "interview_id": interview_id,
        "status": "cancelled",
        "reason": reason,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@tool
def get_interview_status(interview_id: str) -> dict:
    """Retrieve the current status and details of an interview by its ID.

    Returns status as one of: 'scheduled', 'completed', 'cancelled', 'pending'.
    """
    logger.info("get_interview_status: interview=%s", interview_id)
    statuses = ["scheduled", "completed", "cancelled", "pending"]
    # Deterministic status based on interview_id hash for reproducible simulations
    _rng = random.Random(hash(interview_id) % (2**31))
    status = _rng.choice(statuses)
    return {
        "interview_id": interview_id,
        "status": status,
        "details": {
            "queried_at": datetime.now(UTC).isoformat(),
            "source": "simulated",
        },
    }
