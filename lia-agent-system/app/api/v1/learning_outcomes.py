"""
Learning Outcomes API - Endpoints for job outcome tracking and analysis.

Provides:
- Manual outcome recording
- Outcome listing per company (paginated)
- Summary statistics (fill rate, avg TTF, avg candidates)
- Pattern detection from historical outcomes
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.recruitment.repositories.learning_outcome_repository import LearningOutcomeRepository
from app.domains.job_management.services.outcome_tracker import outcome_tracker
from app.models.feedback_learning import JobOutcome, JobOutcomeType
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match
from app.shared.types import WeDoBaseModel
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

router = APIRouter(prefix="/learning-outcomes", tags=["Learning Outcomes"])
logger = logging.getLogger(__name__)


def get_learning_outcome_repo(db: AsyncSession = Depends(get_db)) -> LearningOutcomeRepository:
    return LearningOutcomeRepository(db)


class OutcomeRecordRequest(WeDoBaseModel):
    job_id: str
    reason: str = Field(..., description="Close reason: filled, cancelled, expired, reposted")
    hired_candidate_id: str | None = None


class OutcomeResponse(BaseModel):
    id: str
    company_id: str
    job_id: str
    outcome: str
    time_to_fill_days: int | None = None
    role: str | None = None
    seniority: str | None = None
    department: str | None = None
    location: str | None = None
    candidate_count_total: int | None = None
    candidate_count_screened: int | None = None
    candidate_count_interviewed: int | None = None
    candidate_count_offered: int | None = None
    salary_initial_min: float | None = None
    salary_initial_max: float | None = None
    created_at: str | None = None


class OutcomeStatsResponse(BaseModel):
    total_outcomes: int = 0
    filled_count: int = 0
    cancelled_count: int = 0
    expired_count: int = 0
    fill_rate: float = 0.0
    avg_time_to_fill_days: float | None = None
    avg_candidates_total: float | None = None
    avg_candidates_screened: float | None = None
    avg_candidates_interviewed: float | None = None


class OutcomePatternResponse(BaseModel):
    role: str | None = None
    seniority: str | None = None
    department: str | None = None
    sample_size: int = 0
    avg_time_to_fill: float | None = None
    avg_candidates: float | None = None
    fill_rate: float = 0.0


@router.post("/outcomes/record", response_model=None)
async def record_outcome(request: OutcomeRecordRequest, db: AsyncSession = Depends(get_db), company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    try:
        result = await outcome_tracker.record_job_close(
            job_id=request.job_id,
            company_id=company_id,
            reason=request.reason,
            hired_candidate_id=request.hired_candidate_id,
            db=db,
        )
        if not result:
            raise HTTPException(status_code=404, detail="Job not found or outcome recording failed")
        return {
            "success": True,
            "outcome_id": str(result.id),
            "outcome": result.outcome.value if result.outcome else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to record outcome: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/outcomes/{company_id}", response_model=list[OutcomeResponse])
async def list_outcomes(
    company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    outcome_type: str | None = Query(default=None),
    repo: LearningOutcomeRepository = Depends(get_learning_outcome_repo),
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    try:
        ot = None
        if outcome_type:
            try:
                ot = JobOutcomeType(outcome_type)
            except ValueError:
                pass
        outcomes = await repo.list_paginated(
            company_id=company_id,
            outcome_type=ot,
            limit=limit,
            offset=offset,
        )
        return [
            OutcomeResponse(
                id=str(o.id),
                company_id=o.company_id,
                job_id=str(o.job_id),
                outcome=o.outcome.value if o.outcome else "",
                time_to_fill_days=o.time_to_fill_days,
                role=o.role,
                seniority=o.seniority,
                department=o.department,
                location=o.location,
                candidate_count_total=o.candidate_count_total,
                candidate_count_screened=o.candidate_count_screened,
                candidate_count_interviewed=o.candidate_count_interviewed,
                candidate_count_offered=o.candidate_count_offered,
                salary_initial_min=o.salary_initial_min,
                salary_initial_max=o.salary_initial_max,
                created_at=o.created_at.isoformat() if o.created_at else None,
            )
            for o in outcomes
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list outcomes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/outcomes/{company_id}/stats", response_model=OutcomeStatsResponse)
async def get_outcome_stats(
    company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    repo: LearningOutcomeRepository = Depends(get_learning_outcome_repo),
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    try:
        stats = await repo.get_stats(company_id)
        total = stats["total"]
        filled = stats["filled"]
        cancelled = stats["cancelled"]
        expired = stats["expired"]
        avg_row = stats["avg_row"]

        return OutcomeStatsResponse(
            total_outcomes=total,
            filled_count=filled,
            cancelled_count=cancelled,
            expired_count=expired,
            fill_rate=round(filled / total, 4) if total > 0 else 0.0,
            avg_time_to_fill_days=round(float(avg_row[0]), 1) if avg_row and avg_row[0] else None,
            avg_candidates_total=round(float(avg_row[1]), 1) if avg_row and avg_row[1] else None,
            avg_candidates_screened=round(float(avg_row[2]), 1) if avg_row and avg_row[2] else None,
            avg_candidates_interviewed=round(float(avg_row[3]), 1) if avg_row and avg_row[3] else None,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get outcome stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/outcomes/{company_id}/patterns", response_model=list[OutcomePatternResponse])
async def get_outcome_patterns(
    company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    group_by: str = Query(default="role", pattern="^(role|seniority|department)$"),
    repo: LearningOutcomeRepository = Depends(get_learning_outcome_repo),
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    try:
        rows = await repo.get_patterns(company_id=company_id, group_by=group_by)

        patterns = []
        for row in rows:
            group_value, sample_size, avg_ttf, avg_cands, filled_count = row
            pattern = OutcomePatternResponse(
                sample_size=sample_size,
                avg_time_to_fill=round(float(avg_ttf), 1) if avg_ttf else None,
                avg_candidates=round(float(avg_cands), 1) if avg_cands else None,
                fill_rate=round(filled_count / sample_size, 4) if sample_size > 0 else 0.0,
            )
            setattr(pattern, group_by, group_value)
            patterns.append(pattern)

        return patterns
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get outcome patterns: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

reorder_collection_before_item(router)
