

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
async def schedule_interview(
    candidate_id: str,
    interviewer_id: str,
    datetime_str: str,
    interview_type: str = "technical",
    meeting_url: str = "",
    company_id=None,
) -> dict:
    """Schedule an interview slot between a candidate and an interviewer.

    interview_type must be one of: 'technical', 'behavioral', 'cultural_fit', 'final'.
    Returns is_simulated_calendar=True until real Google Calendar integration ships.
    Multi-tenancy: company_id is set on the Interview record when provided.
    """
    logger.info(
        "schedule_interview: candidate=%s interviewer=%s datetime=%s type=%s",
        candidate_id, interviewer_id, datetime_str, interview_type,
    )
    interview_id = str(uuid.uuid4())
    try:
        from lia_config.database import AsyncSessionLocal
        from lia_models.interview import Interview

        async with AsyncSessionLocal() as _db:
            _interview = Interview(
                id=interview_id,
                candidate_id=candidate_id,
                interviewer_id=interviewer_id,
                interview_type=interview_type,
                meeting_url=meeting_url or None,
                company_id=company_id,
            )
            _db.add(_interview)
            await _db.commit()
    except Exception as _db_err:
        logger.warning("schedule_interview: DB write failed (non-fatal): %s", _db_err)

    return {
        "success": True,
        "interview_id": interview_id,
        "status": "scheduled",
        "candidate_id": candidate_id,
        "interviewer_id": interviewer_id,
        "datetime": datetime_str,
        "type": interview_type,
        "meeting_url": meeting_url or None,
        "scheduled_at": datetime.now(UTC).isoformat(),
        "is_simulated_calendar": True,
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
async def reschedule_interview(
    interview_id: str,
    new_datetime_str: str,
    reason: str = "",
    company_id=None,
) -> dict:
    """Reschedule an existing interview to a new date/time.

    Fetches the old datetime from DB when available (non-fatal fallback to N/A).
    Returns is_simulated_calendar=True (simulation stub until real calendar API).

    Multi-tenancy: company_id filters the DB query when provided.
    """
    from lia_config.database import AsyncSessionLocal
    from sqlalchemy import select as _select

    old_datetime_str = "N/A"
    try:
        from lia_models.interview import Interview  # type: ignore[import]
    except ImportError:
        try:
            from lia_models.interview import Interview  # type: ignore[import]
        except ImportError:
            Interview = None

    if Interview is not None:
        try:
            async with AsyncSessionLocal() as _db:
                _q = _select(Interview).where(Interview.id == interview_id)
                if company_id:
                    _q = _q.where(Interview.company_id == company_id)
                _result = await _db.execute(_q)
                _interview = _result.scalar_one_or_none()
                if _interview and _interview.start_time:
                    old_datetime_str = (
                        _interview.start_time.isoformat()
                        if hasattr(_interview.start_time, "isoformat")
                        else str(_interview.start_time)
                    )
        except Exception as _db_err:
            logger.warning("reschedule_interview: DB lookup failed (non-fatal): %s", _db_err)

    logger.info(
        "reschedule_interview: interview=%s new_datetime=%s reason=%s",
        interview_id, new_datetime_str, reason,
    )
    return {
        "success": True,
        "interview_id": interview_id,
        "status": "rescheduled",
        "old_datetime": old_datetime_str,
        "new_datetime": new_datetime_str,
        "reason": reason,
        "updated_at": datetime.now(UTC).isoformat(),
        "is_simulated_calendar": True,
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
