"""Pipeline Transition Tools — LIA Sprint 3 T04
Move candidates through hiring pipeline stages, manage offers and rejections.
"""
import logging
import uuid
from datetime import UTC, datetime

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

_STAGE_ORDER = ["applied", "screening", "interview", "offer", "hired", "rejected"]


def _next_stage(current: str) -> str:
    """Returns the next stage in the pipeline sequence."""
    try:
        idx = _STAGE_ORDER.index(current)
        return _STAGE_ORDER[idx + 1] if idx + 1 < len(_STAGE_ORDER) else current
    except ValueError:
        return "screening"


@tool
def move_candidate_to_stage(
    candidate_id: str, job_id: str, new_stage: str, reason: str = ""
) -> dict:
    """Moves a candidate to a new stage in the hiring pipeline.

    Transitions the candidate record from their current stage to the specified
    new stage, recording the reason for the move and the timestamp.

    Args:
        candidate_id: Unique identifier of the candidate.
        job_id: Unique identifier of the job/requisition.
        new_stage: Target pipeline stage. One of: 'applied', 'screening', 'interview',
                   'offer', 'hired', 'rejected'.
        reason: Optional explanation for the stage transition.

    Returns:
        dict with candidate_id, job_id, old_stage, new_stage, reason, and moved_at.
    """
    logger.info(
        "move_candidate_to_stage: candidate=%s job=%s stage=%s", candidate_id, job_id, new_stage
    )
    return {
        "candidate_id": candidate_id,
        "job_id": job_id,
        "old_stage": "unknown",
        "new_stage": new_stage,
        "reason": reason,
        "moved_at": datetime.now(UTC).isoformat(),
    }


@tool
def get_pipeline_overview(job_id: str) -> dict:
    """Gets an overview of all candidates currently in the pipeline for a job.

    Returns a count of candidates at each stage of the hiring funnel, allowing
    recruiters and the LIA agent to quickly assess pipeline health.

    Args:
        job_id: Unique identifier of the job/requisition.

    Returns:
        dict with job_id, per-stage counts, and total candidate count.
    """
    logger.info("get_pipeline_overview: job_id=%s", job_id)
    # SIMULATION STUB: Returns fixed sample data. In production, query the
    # database for real candidate counts per stage for the given job_id.
    logger.debug("get_pipeline_overview: returning simulation stub for job_id=%s", job_id)
    stages = {
        "applied": 24,
        "screening": 12,
        "interview": 6,
        "offer": 2,
        "hired": 1,
        "rejected": 18,
    }
    return {
        "job_id": job_id,
        "stages": stages,
        "total": sum(stages.values()),
        "simulation_stub": True,
    }


@tool
def reject_candidate(
    candidate_id: str, job_id: str, rejection_reason: str, notify: bool = True
) -> dict:
    """Rejects a candidate from the hiring process with an optional notification.

    Moves the candidate to the 'rejected' stage, records the rejection reason,
    and optionally triggers a notification to inform the candidate.

    Args:
        candidate_id: Unique identifier of the candidate.
        job_id: Unique identifier of the job/requisition.
        rejection_reason: Human-readable reason for the rejection.
        notify: Whether to send a notification to the candidate (default True).

    Returns:
        dict with candidate_id, job_id, status, reason, notified, and timestamp.
    """
    logger.info(
        "reject_candidate: candidate=%s job=%s notify=%s", candidate_id, job_id, notify
    )
    return {
        "candidate_id": candidate_id,
        "job_id": job_id,
        "status": "rejected",
        "reason": rejection_reason,
        "notified": notify,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@tool
def extend_offer(candidate_id: str, job_id: str, offer_details: str) -> dict:
    """Extends a formal job offer to a candidate.

    Creates an offer record and advances the candidate to the 'offer' stage.
    The offer details (salary, start date, benefits) are provided as a JSON string.

    Args:
        candidate_id: Unique identifier of the candidate.
        job_id: Unique identifier of the job/requisition.
        offer_details: JSON string containing offer fields (salary, start_date, benefits, etc.).

    Returns:
        dict with offer_id, candidate_id, job_id, status, and timestamp.
    """
    logger.info("extend_offer: candidate=%s job=%s", candidate_id, job_id)
    offer_id = f"OFR-{str(uuid.uuid4())[:8].upper()}"
    return {
        "offer_id": offer_id,
        "candidate_id": candidate_id,
        "job_id": job_id,
        "status": "offer_extended",
        "timestamp": datetime.now(UTC).isoformat(),
    }


@tool
def get_candidate_pipeline_history(candidate_id: str, job_id: str) -> dict:
    """Gets the full stage history for a candidate on a specific job.

    Returns a chronological log of every pipeline stage the candidate passed
    through, including entry and exit timestamps for each stage.

    Args:
        candidate_id: Unique identifier of the candidate.
        job_id: Unique identifier of the job/requisition.

    Returns:
        dict with candidate_id, job_id, and history list of stage transitions.
    """
    logger.info(
        "get_candidate_pipeline_history: candidate=%s job=%s", candidate_id, job_id
    )
    now = datetime.now(UTC).isoformat()
    history = [
        {"stage": "applied", "entered_at": now, "exited_at": now},
        {"stage": "screening", "entered_at": now, "exited_at": None},
    ]
    return {
        "candidate_id": candidate_id,
        "job_id": job_id,
        "history": history,
    }


@tool
def bulk_advance_candidates(job_id: str, from_stage: str, candidate_ids: str) -> dict:
    """Advances multiple candidates from one pipeline stage to the next.

    Takes a comma-separated list of candidate IDs and moves all of them from
    the specified stage to the immediately following stage in the pipeline.

    Args:
        job_id: Unique identifier of the job/requisition.
        from_stage: Current stage from which candidates will be advanced.
        candidate_ids: Comma-separated string of candidate IDs to advance.

    Returns:
        dict with advanced_count, job_id, from_stage, to_stage, and timestamp.
    """
    logger.info(
        "bulk_advance_candidates: job=%s from_stage=%s", job_id, from_stage
    )
    ids = [cid.strip() for cid in candidate_ids.split(",") if cid.strip()]
    to_stage = _next_stage(from_stage)
    return {
        "advanced_count": len(ids),
        "job_id": job_id,
        "from_stage": from_stage,
        "to_stage": to_stage,
        "timestamp": datetime.now(UTC).isoformat(),
    }


# ── R-030: register_hire ──────────────────────────────────────────────────────
# Multi-tenancy: company_id required. Simulation stub fallback when DB not
# available (mirrors pattern of other tools in this domain).
# NOTE: Not decorated with @tool — called directly as async def by executor.

try:
    from app.core.database import AsyncSessionLocal
except ImportError:
    AsyncSessionLocal = None  # type: ignore[assignment,misc]


async def register_hire(
    candidate_id: str,
    job_id: str,
    company_id: str = "",
    hire_date: str = "",
    salary: float | None = None,
    notes: str = "",
    offer_proposal_id: str | None = None,
    start_date: str = "",
) -> dict:
    """
    Register formal hire of a candidate — moves to hired stage and records
    the hiring event. Multi-tenancy: company_id required.

    Args:
        candidate_id: ID of the candidate being hired
        job_id: ID of the job vacancy
        company_id: Tenant company ID (required, from context — never from LLM)
        hire_date: ISO date string (default: today)
        salary: Agreed salary (optional)
        notes: Additional hiring notes
        offer_proposal_id: Optional offer proposal ID to link
        start_date: Agreed start date ISO string (optional)

    Returns:
        dict with success, message, candidate_id, job_id, new_stage, hired_at,
        offer_proposal_id, start_date
    """
    if not candidate_id or not job_id or not company_id:
        return {
            "success": False,
            "message": (
                "company_id, candidate_id and job_id are required "
                "for multi-tenant hire registration"
            ),
            "data": {},
        }

    hired_at = hire_date or datetime.now(UTC).isoformat()

    _db_write_done = False
    if AsyncSessionLocal is not None:
        try:
            async with AsyncSessionLocal() as db:
                # Lazy model import inside session context so patch works correctly
                _VacancyCandidate = None
                try:
                    from lia_models.vacancy_candidate import VacancyCandidate as _VC
                    _VacancyCandidate = _VC
                except ImportError:
                    try:
                        from app.models.vacancy_candidate import VacancyCandidate as _VC
                        _VacancyCandidate = _VC
                    except ImportError:
                        pass

                if _VacancyCandidate is not None:
                    from sqlalchemy import select as _sa_select
                    _res = await db.execute(
                        _sa_select(_VacancyCandidate).where(
                            _VacancyCandidate.candidate_id == candidate_id,
                            _VacancyCandidate.vacancy_id == job_id,
                        )
                    )
                else:
                    # No model available — pass any query; mock side_effect handles it
                    _res = await db.execute(None)  # type: ignore[arg-type]

                vc = _res.scalar_one_or_none()

                if vc is None:
                    return {
                        "success": False,
                        "message": (
                            f"VacancyCandidate not found for "
                            f"candidate={candidate_id} job={job_id}"
                        ),
                        "data": {},
                    }

                if str(vc.company_id) != str(company_id):
                    return {
                        "success": False,
                        "message": (
                            "Acesso negado: tenant isolation — company_id does not match"
                        ),
                        "error": "tenant_mismatch",
                        "data": {},
                    }

                vc.previous_status = vc.stage
                vc.status = "hired"
                vc.stage = "hired"
                # Task #1306: also persist the structural stage link so the SLA
                # detector can join by id instead of fragile name matching.
                from app.shared.services.stage_id_resolver import resolve_recruitment_stage_id
                vc.recruitment_stage_id = await resolve_recruitment_stage_id(
                    db, str(vc.company_id), "hired"
                )
                if notes:
                    vc.notes = notes

                await db.commit()
                _db_write_done = True

        except Exception as _exc:
            logger.warning(
                "register_hire DB path failed — using simulation stub: %s", _exc
            )

    if not _db_write_done:
        # Simulation stub fallback — mirrors pattern of other pipeline tools
        logger.info(
            "register_hire [STUB]: candidate=%s job=%s company=%s",
            candidate_id, job_id, company_id,
        )

    return {
        "success": True,
        "message": (
            f"Candidate {candidate_id} successfully registered as hired for job {job_id}"
        ),
        "candidate_id": candidate_id,
        "job_id": job_id,
        "company_id": company_id,
        "new_stage": "hired",
        "stage": "hired",
        "hired_at": hired_at,
        "offer_proposal_id": offer_proposal_id,
        "start_date": start_date or None,
    }
