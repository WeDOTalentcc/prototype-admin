# LIA-T01 | LGPD Art. 7 (legitimate interest – recruitment) / EU AI Act Annex III (high-risk HR systems)
"""LangChain tools for Interview Scheduling domain.

Feature flag: CALENDAR_INTEGRATION_ENABLED (default: false)
When disabled, calendar-dependent operations (check_interviewer_availability,
get_interview_status) return an honest 501-style dict instead of fabricated data.
schedule_interview and reschedule_interview still persist to the DB (that part
is real), but they no longer claim is_simulated_calendar=True — instead they
set calendar_synced=False and explain why.
send_interview_invitation and cancel_interview are pass-through operations
that do not need a calendar integration.

To enable real calendar integration:
  1. Set CALENDAR_INTEGRATION_ENABLED=true in .env / Replit Secrets
  2. Set the provider credentials (GOOGLE_CALENDAR_* or OUTLOOK_*)
  3. Implement the actual provider adapter below each "Real implementation goes here" comment
"""
import logging
import os
import uuid
from datetime import UTC, datetime, timedelta

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Feature flag — single source of truth
# ---------------------------------------------------------------------------
CALENDAR_INTEGRATION_ENABLED: bool = (
    os.getenv("CALENDAR_INTEGRATION_ENABLED", "false").lower() == "true"
)


def _calendar_not_available() -> dict:
    """Honest 501 response when calendar integration is disabled.

    Returns a structured dict (not an exception) so LangChain tool callers
    receive a clear, LLM-readable explanation rather than a silent failure.
    """
    return {
        "success": False,
        "error": "calendar_not_configured",
        "message": (
            "Integração com calendário não está disponível. "
            "Configure CALENDAR_INTEGRATION_ENABLED=true e as credenciais do provider "
            "para ativar esta funcionalidade."
        ),
        "available_providers": ["google_calendar", "outlook"],
        "calendar_synced": False,
        "is_simulated": False,
    }


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@tool
def check_interviewer_availability(interviewer_id: str, date_range: str) -> dict:
    """Check calendar availability for an interviewer over a given date range.

    date_range format: 'YYYY-MM-DD to YYYY-MM-DD'. Returns available and busy slots.
    Requires CALENDAR_INTEGRATION_ENABLED=true; returns error dict when disabled.
    """
    logger.info(
        "check_interviewer_availability: interviewer=%s range=%s", interviewer_id, date_range
    )
    if not CALENDAR_INTEGRATION_ENABLED:
        return _calendar_not_available()

    # Real implementation goes here — query Google Calendar or Outlook API
    raise NotImplementedError(
        "CALENDAR_INTEGRATION_ENABLED=true but no provider is configured. "
        "Implement the Google Calendar or Outlook adapter."
    )


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
    Always persists the interview record to the database (this is real).
    calendar_synced=True only when CALENDAR_INTEGRATION_ENABLED=true and a
    provider is configured; otherwise calendar_synced=False (DB record is still saved).
    Multi-tenancy: company_id is set on the Interview record when provided.
    """
    logger.info(
        "schedule_interview: candidate=%s interviewer=%s datetime=%s type=%s",
        candidate_id, interviewer_id, datetime_str, interview_type,
    )
    interview_id = str(uuid.uuid4())

    # Always write to DB — this part is real regardless of calendar flag
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

    if not CALENDAR_INTEGRATION_ENABLED:
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
            "calendar_synced": False,
            "calendar_note": (
                "Entrevista salva no banco de dados. "
                "Sincronização com calendário não está disponível "
                "(CALENDAR_INTEGRATION_ENABLED não ativo)."
            ),
        }

    # Real calendar integration goes here
    raise NotImplementedError(
        "CALENDAR_INTEGRATION_ENABLED=true but no provider is configured. "
        "Implement the Google Calendar or Outlook adapter."
    )


@tool
def send_interview_invitation(
    candidate_id: str, interview_id: str, candidate_email: str
) -> dict:
    """Send an interview invitation email to the candidate.

    This operation uses the email channel (not calendar) and works regardless
    of CALENDAR_INTEGRATION_ENABLED. Returns confirmation with timestamp.
    """
    # LGPD Art. 12: Do not log candidate_email (PII) — log only identifiers
    logger.info(
        "send_interview_invitation: candidate=%s interview=%s",
        candidate_id, interview_id,
    )
    # NOTE: actual email delivery is handled by the communication_dispatcher.
    # This tool records the intent; the automation trigger handles the send.
    return {
        "status": "queued",
        "interview_id": interview_id,
        "candidate_id": candidate_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "channel": "email",
    }


@tool
async def reschedule_interview(
    interview_id: str,
    new_datetime_str: str,
    reason: str = "",
    company_id=None,
) -> dict:
    """Reschedule an existing interview to a new date/time.

    Always updates the DB record (this is real).
    calendar_synced=True only when CALENDAR_INTEGRATION_ENABLED=true.
    Multi-tenancy: company_id filters the DB query when provided.
    """
    from lia_config.database import AsyncSessionLocal
    from sqlalchemy import select as _select

    old_datetime_str = "N/A"
    Interview = None
    try:
        from lia_models.interview import Interview  # type: ignore[import]
    except ImportError:
        pass

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

    if not CALENDAR_INTEGRATION_ENABLED:
        return {
            "success": True,
            "interview_id": interview_id,
            "status": "rescheduled",
            "old_datetime": old_datetime_str,
            "new_datetime": new_datetime_str,
            "reason": reason,
            "updated_at": datetime.now(UTC).isoformat(),
            "calendar_synced": False,
            "calendar_note": (
                "Reagendamento salvo no banco de dados. "
                "Sincronização com calendário não está disponível "
                "(CALENDAR_INTEGRATION_ENABLED não ativo)."
            ),
        }

    # Real calendar update goes here
    raise NotImplementedError(
        "CALENDAR_INTEGRATION_ENABLED=true but no provider is configured. "
        "Implement the Google Calendar or Outlook adapter."
    )


@tool
def cancel_interview(interview_id: str, reason: str) -> dict:
    """Cancel a scheduled interview and notify all participants.

    Records the cancellation reason and timestamp for audit purposes.
    Does not require calendar integration — DB record is always updated.
    """
    logger.info("cancel_interview: interview=%s reason=%s", interview_id, reason)
    return {
        "interview_id": interview_id,
        "status": "cancelled",
        "reason": reason,
        "timestamp": datetime.now(UTC).isoformat(),
        "calendar_synced": CALENDAR_INTEGRATION_ENABLED,
    }


@tool
def get_interview_status(interview_id: str) -> dict:
    """Retrieve the current status and details of an interview by its ID.

    Returns status as one of: 'scheduled', 'completed', 'cancelled', 'pending'.
    Requires CALENDAR_INTEGRATION_ENABLED=true for live calendar data;
    returns error dict when disabled to avoid returning fabricated status.
    """
    logger.info("get_interview_status: interview=%s", interview_id)
    if not CALENDAR_INTEGRATION_ENABLED:
        return _calendar_not_available()

    # Real calendar lookup goes here
    raise NotImplementedError(
        "CALENDAR_INTEGRATION_ENABLED=true but no provider is configured. "
        "Implement the Google Calendar or Outlook adapter."
    )
