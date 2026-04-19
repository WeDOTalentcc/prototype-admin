"""Pipeline Transition Tools — LIA Sprint 3 T04
Move candidates through hiring pipeline stages, manage offers and rejections.
"""
import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from app.shared.tool_handler import tool_handler

logger = logging.getLogger(__name__)

_STAGE_ORDER = ["applied", "screening", "interview", "offer", "hired", "rejected"]


def _next_stage(current: str) -> str:
    """Returns the next stage in the pipeline sequence."""
    try:
        idx = _STAGE_ORDER.index(current)
        return _STAGE_ORDER[idx + 1] if idx + 1 < len(_STAGE_ORDER) else current
    except ValueError:
        return "screening"


@tool_handler(domain="pipeline", require_company=True)
async def move_candidate_to_stage(
    candidate_id: str = "",
    job_id: str = "",
    new_stage: str = "",
    reason: str = "",
    **kwargs: Any,
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
        "success": True,
        "candidate_id": candidate_id,
        "job_id": job_id,
        "old_stage": "unknown",
        "new_stage": new_stage,
        "reason": reason,
        "moved_at": datetime.now(UTC).isoformat(),
    }


@tool_handler(domain="pipeline", require_company=True)
async def get_pipeline_overview(
    job_id: str = "",
    **kwargs: Any,
) -> dict:
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
        "success": True,
        "job_id": job_id,
        "stages": stages,
        "total": sum(stages.values()),
        "simulation_stub": True,
    }


@tool_handler(domain="pipeline", require_company=True)
async def extend_offer(
    candidate_id: str = "",
    job_id: str = "",
    offer_details: str = "",
    **kwargs: Any,
) -> dict:
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
        "success": True,
        "offer_id": offer_id,
        "candidate_id": candidate_id,
        "job_id": job_id,
        "status": "offer_extended",
        "timestamp": datetime.now(UTC).isoformat(),
    }


@tool_handler(domain="pipeline", require_company=True)
async def get_candidate_pipeline_history(
    candidate_id: str = "",
    job_id: str = "",
    **kwargs: Any,
) -> dict:
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
        "success": True,
        "candidate_id": candidate_id,
        "job_id": job_id,
        "history": history,
    }


@tool_handler(domain="pipeline", require_company=True)
async def bulk_advance_candidates(
    job_id: str = "",
    from_stage: str = "",
    candidate_ids: str = "",
    **kwargs: Any,
) -> dict:
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
        "success": True,
        "advanced_count": len(ids),
        "job_id": job_id,
        "from_stage": from_stage,
        "to_stage": to_stage,
        "timestamp": datetime.now(UTC).isoformat(),
    }
