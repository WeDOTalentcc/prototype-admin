"""
Learning Patterns API - Exposes detected patterns, promoted skills, and success profiles.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.recruitment.repositories.learning_patterns_repository import LearningPatternsRepository
from app.domains.automation.services.learning_automation import LearningAutomationService, get_learning_automation_service
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/patterns", tags=["learning-patterns"])

SKILL_PROMOTION_THRESHOLD = 5


@router.get("/{company_id}/detected", response_model=None)
# TODO(phase2): extract to repository — learning pattern storage
async def get_detected_patterns(
    company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    field: str | None = None,
    seniority: str | None = None,
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """List all detected correction patterns for a company."""
    try:
        repo = LearningPatternsRepository(db)
        patterns = await repo.get_correction_patterns(company_id, field=field, seniority=seniority)

        return {
            "company_id": company_id,
            "count": len(patterns),
            "patterns": [
                {
                    "id": str(p.id),
                    "field": p.field,
                    "pattern_type": p.pattern_type,
                    "seniority": p.seniority,
                    "department": p.department,
                    "adjustment_direction": p.adjustment_direction,
                    "adjustment_magnitude": p.adjustment_magnitude,
                    "original_value_pattern": p.original_value_pattern,
                    "corrected_value_pattern": p.corrected_value_pattern,
                    "occurrence_count": p.occurrence_count,
                    "sample_size": p.sample_size,
                    "confidence": p.confidence,
                    "is_active": p.is_active,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                    "updated_at": p.updated_at.isoformat() if p.updated_at else None,
                }
                for p in patterns
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching detected patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{company_id}/skills", response_model=None)
async def get_promoted_skills(
    company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    job_title: str | None = None,
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """List promoted skills for a company (times_confirmed >= threshold)."""
    try:
        repo = LearningPatternsRepository(db)
        skills = await repo.get_promoted_skills(company_id)

        promoted = []
        for s in skills:
            roles = s.roles_associated or []
            if job_title and roles:
                title_lower = job_title.lower()
                if not any(title_lower in r.lower() or r.lower() in title_lower for r in roles):
                    continue

            promoted.append({
                "id": str(s.id),
                "skill_name": s.skill_name,
                "skill_type": s.skill_type,
                "category": s.category,
                "times_confirmed": s.times_confirmed,
                "times_used_in_jobs": s.times_used_in_jobs,
                "times_in_successful_hires": s.times_in_successful_hires,
                "confidence_score": s.confidence_score,
                "roles_associated": s.roles_associated,
                "seniority_levels": s.seniority_levels,
                "is_promoted": s.is_promoted,
            })

        return {
            "company_id": company_id,
            "promotion_threshold": SKILL_PROMOTION_THRESHOLD,
            "count": len(promoted),
            "skills": promoted,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching promoted skills: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{company_id}/success-profiles", response_model=None)
async def get_success_profiles(
    company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    role: str | None = None,
    seniority: str | None = None,
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """List success profiles for a company."""
    try:
        repo = LearningPatternsRepository(db)
        profiles = await repo.get_success_profiles(company_id, role=role, seniority=seniority)

        return {
            "company_id": company_id,
            "count": len(profiles),
            "profiles": [
                {
                    "id": str(p.id),
                    "role_family": p.role_family,
                    "seniority": p.seniority,
                    "department": p.department,
                    "avg_time_to_fill_days": p.avg_time_to_fill_days,
                    "avg_salary": p.avg_salary,
                    "salary_range_min": p.salary_range_min,
                    "salary_range_max": p.salary_range_max,
                    "common_skills": p.common_skills,
                    "common_requirements": p.common_requirements,
                    "preferred_work_model": p.preferred_work_model,
                    "avg_satisfaction_score": p.avg_satisfaction_score,
                    "sample_size": p.sample_size,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                }
                for p in profiles
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching success profiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{company_id}/trigger-detection", response_model=None)
async def trigger_pattern_detection(
    company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    service: LearningAutomationService = Depends(get_learning_automation_service),
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Manually trigger pattern detection for a company."""
    try:
        detection_result = await service.run_pattern_detection(company_id)
        promotion_result = await service.run_skill_promotion(company_id)

        return {
            "company_id": company_id,
            "status": "completed",
            "detection": detection_result,
            "promotion": promotion_result,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering pattern detection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

reorder_collection_before_item(router)
