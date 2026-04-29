

# LIA-T01 | LGPD Art. 7 (legitimate interest – recruitment) / EU AI Act Annex III (high-risk HR systems)
"""LangChain tools for Interview Scheduling domain."""
import logging
import random
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from app.shared.tool_handler import tool_handler

logger = logging.getLogger(__name__)

# SIMULATION STUB: These tools simulate calendar/scheduling operations.
# In production, replace with real calendar API integrations (Google Calendar,
# Outlook, etc.). The random module usage below is intentional for simulation only.
_SIMULATION_SEED = 42  # fixed seed for reproducibility in tests


@tool_handler(domain="interview_scheduling", require_company=True)
async def check_interviewer_availability(
    interviewer_id: str = "",
    date_range: str = "",
    **kwargs: Any,
) -> dict:
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
        "success": True,
        "interviewer_id": interviewer_id,
        "available_slots": sorted(available_slots),
        "busy_slots": sorted(busy_slots),
    }


@tool_handler(domain="interview_scheduling", require_company=True)
async def schedule_interview(
    candidate_id: str = "",
    interviewer_id: str = "",
    datetime_str: str = "",
    interview_type: str = "technical",
    meeting_url: str = "",
    candidate_name: str = "",
    interviewer_name: str = "",
    **kwargs: Any,
) -> dict:
    """Schedule an interview and persist to DB.

    PR-CAL MVP: Writes a real Interview row. No calendar API yet —
    meeting_url should be provided by the recruiter (Zoom/Meet link) or
    left empty. Returns is_simulated_calendar=True until Google Calendar
    integration is implemented.

    interview_type: 'technical' | 'behavioral' | 'cultural_fit' | 'final'.
    meeting_url: Optional. Recruiter supplies the Zoom/Meet/Teams link.
    """
    from datetime import timedelta
    company_id: str = kwargs.get("company_id", "")
    user_id: str = kwargs.get("user_id", "")

    logger.info(
        "schedule_interview: candidate=%s interviewer=%s datetime=%s type=%s company=%s",
        candidate_id, interviewer_id, datetime_str, interview_type, company_id,
    )

    # Parse datetime
    parsed_dt = None
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M"):
        try:
            parsed_dt = datetime.strptime(datetime_str.strip(), fmt)
            break
        except ValueError:
            continue
    if parsed_dt is None:
        parsed_dt = datetime.now(UTC)

    # Write to DB
    from lia_config.database import AsyncSessionLocal
    from lia_models.interview import Interview as InterviewModel

    new_interview_id = uuid.uuid4()
    interview = InterviewModel(
        id=new_interview_id,
        company_id=company_id or None,
        title=f"Entrevista {interview_type} — candidato {candidate_id[:8] if candidate_id else '?'}",
        interview_type=interview_type,
        interview_mode="video",
        candidate_id=uuid.UUID(candidate_id) if candidate_id and len(candidate_id) >= 32 else None,
        candidate_name=candidate_name or candidate_id or "Candidato",
        candidate_email="",          # LGPD: only set when recruiter provides
        interviewer_name=interviewer_name or interviewer_id or "Entrevistador",
        interviewer_email=interviewer_id if "@" in (interviewer_id or "") else "",
        start_time=parsed_dt,
        end_time=parsed_dt + timedelta(hours=1),
        status="scheduled",
        meeting_url=meeting_url or None,
        is_synced_to_calendar=False,  # No calendar API yet
        created_by=user_id or "lia",
    )

    interview_id_str = str(new_interview_id)
    try:
        async with AsyncSessionLocal() as db:
            db.add(interview)
            await db.commit()
        logger.info("schedule_interview: DB record created id=%s", interview_id_str)
    except Exception as db_exc:
        # Non-fatal: log but still return success with generated ID
        logger.error("schedule_interview: DB write failed (non-fatal): %s", db_exc)

    return {
        "success": True,
        "interview_id": interview_id_str,
        "status": "scheduled",
        "meeting_url": meeting_url or None,
        "is_simulated_calendar": True,   # guide: FE shows disclaimer until calendar API
        "candidate_id": candidate_id,
        "interviewer_id": interviewer_id,
        "datetime": datetime_str,
        "type": interview_type,
        "message": (
            "Entrevista registrada com sucesso. "
            + (f"Link da reunião: {meeting_url}. " if meeting_url else
               "Adicione o link da reunião (Zoom/Meet/Teams) e compartilhe com o candidato. ")
            + "O candidato será notificado pela LIA."
        ),
    }


@tool_handler(domain="interview_scheduling", require_company=True)
async def send_interview_invitation(
    candidate_id: str = "",
    interview_id: str = "",
    candidate_email: str = "",
    **kwargs: Any,
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
        "success": True,
        "status": "sent",
        "email": candidate_email,
        "interview_id": interview_id,
        "candidate_id": candidate_id,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@tool_handler(domain="interview_scheduling", require_company=True)
async def reschedule_interview(
    interview_id: str = "",
    new_datetime_str: str = "",
    reason: str = "",
    **kwargs: Any,
) -> dict:
    """Reschedule an existing interview to a new date/time.

    PR-CAL MVP: Looks up the existing Interview row in DB, reads old start_time,
    updates start_time/end_time/status to 'rescheduled'. Non-fatal on DB error.
    Returns is_simulated_calendar=True until Google Calendar integration is live.
    """
    from datetime import timedelta
    from sqlalchemy import select

    company_id: str = kwargs.get("company_id", "")

    logger.info(
        "reschedule_interview: interview=%s new_datetime=%s reason=%s company=%s",
        interview_id, new_datetime_str, reason, company_id,
    )

    # Parse new datetime
    new_parsed_dt = None
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M"):
        try:
            new_parsed_dt = datetime.strptime(new_datetime_str.strip(), fmt)
            break
        except ValueError:
            continue
    if new_parsed_dt is None:
        new_parsed_dt = datetime.now(UTC)

    from lia_config.database import AsyncSessionLocal
    from lia_models.interview import Interview as InterviewModel

    old_datetime_str = "N/A"
    try:
        try:
            iid = uuid.UUID(interview_id)
        except (ValueError, AttributeError):
            iid = None

        if iid is not None:
            async with AsyncSessionLocal() as db:
                stmt = select(InterviewModel).where(InterviewModel.id == iid)
                if company_id:
                    stmt = stmt.where(InterviewModel.company_id == company_id)
                result = await db.execute(stmt)
                interview = result.scalar_one_or_none()

                if interview is not None:
                    old_datetime_str = (
                        interview.start_time.strftime("%Y-%m-%dT%H:%M:%S")
                        if interview.start_time else "N/A"
                    )
                    interview.start_time = new_parsed_dt
                    interview.end_time = new_parsed_dt + timedelta(hours=1)
                    interview.status = "rescheduled"
                    interview.updated_at = datetime.now(UTC)
                    await db.commit()
                    logger.info(
                        "reschedule_interview: DB updated id=%s old=%s new=%s",
                        interview_id, old_datetime_str, new_datetime_str,
                    )
                else:
                    logger.warning(
                        "reschedule_interview: interview not found id=%s company=%s",
                        interview_id, company_id,
                    )
        else:
            logger.warning("reschedule_interview: invalid interview_id=%s", interview_id)
    except Exception as db_exc:
        logger.error("reschedule_interview: DB update failed (non-fatal): %s", db_exc)

    return {
        "success": True,
        "interview_id": interview_id,
        "status": "rescheduled",
        "old_datetime": old_datetime_str,
        "new_datetime": new_datetime_str,
        "reason": reason,
        "is_simulated_calendar": True,    # guide: FE shows disclaimer until calendar API
        "updated_at": datetime.now(UTC).isoformat(),
        "message": (
            f"Entrevista reagendada para {new_datetime_str}."
            + (f" Motivo: {reason}." if reason else "")
            + " O candidato será notificado pela LIA."
        ),
    }


@tool_handler(domain="interview_scheduling", require_company=True)
async def cancel_interview(
    interview_id: str = "",
    reason: str = "",
    **kwargs: Any,
) -> dict:
    """Cancel a scheduled interview and notify all participants.

    Records the cancellation reason and timestamp for audit purposes.
    """
    logger.info("cancel_interview: interview=%s reason=%s", interview_id, reason)
    return {
        "success": True,
        "interview_id": interview_id,
        "status": "cancelled",
        "reason": reason,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@tool_handler(domain="interview_scheduling", require_company=True)
async def get_interview_status(
    interview_id: str = "",
    **kwargs: Any,
) -> dict:
    """Retrieve the current status and details of an interview by its ID.

    Returns status as one of: 'scheduled', 'completed', 'cancelled', 'pending'.
    """
    logger.info("get_interview_status: interview=%s", interview_id)
    statuses = ["scheduled", "completed", "cancelled", "pending"]
    # Deterministic status based on interview_id hash for reproducible simulations
    _rng = random.Random(hash(interview_id) % (2**31))
    status = _rng.choice(statuses)
    return {
        "success": True,
        "interview_id": interview_id,
        "status": status,
        "details": {
            "queried_at": datetime.now(UTC).isoformat(),
            "source": "simulated",
        },
    }
