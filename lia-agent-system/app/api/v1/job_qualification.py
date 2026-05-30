"""
Job Qualification Classification API (WDT-009)
Endpoints for classifying job vacancies and managing qualification levels.
"""
import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.job_management.services.job_qualification_service import job_qualification_service
from app.models.job_vacancy import JobVacancy
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

# RAILS-DEPRECATED: This endpoint manages Rails-owned entities (candidates/jobs/applies/users).
# Direct DB calls will be replaced by RailsAdapter after ats-api-rails handoff.
# See: app/domains/integrations_hub/services/rails_adapter.py

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs/qualification", tags=["job-qualification"])


class ClassifyJobRequest(WeDoBaseModel):
    title: str = Field(..., min_length=1)
    department: str | None = None
    seniority_level: str | None = None
    description: str | None = None
    requirements: list | None = None
    salary_range: dict[str, Any] | None = None
    work_model: str | None = None
    employment_type: str | None = None


class ClassifyJobResponse(BaseModel):
    level: str
    confidence: float
    reasoning: str


class JobQualificationResponse(BaseModel):
    job_id: str
    qualification_level: str | None = None
    qualification_confidence: float | None = None
    qualification_reasoning: str | None = None
    qualification_override: bool = False
    classified: bool = False


class OverrideQualificationRequest(WeDoBaseModel):
    level: str = Field(..., pattern="^(alta|media|baixa)$")
    reason: str | None = None


@router.post("/classify", response_model=ClassifyJobResponse)
async def classify_job(body: ClassifyJobRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Classify a job vacancy qualification level using AI (without saving)."""
    result = await job_qualification_service.classify(
        title=body.title,
        department=body.department,
        seniority_level=body.seniority_level,
        description=body.description,
        requirements=body.requirements,
        salary_range=body.salary_range,
        work_model=body.work_model,
        employment_type=body.employment_type,
    )
    return ClassifyJobResponse(**result)


@router.post("/{job_id}/classify", response_model=JobQualificationResponse)
async def classify_and_save(job_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)], db: AsyncSession = Depends(get_db), company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Classify a job vacancy and save the result to the database."""
    result = await db.execute(select(JobVacancy).where(JobVacancy.id == job_id, JobVacancy.company_id == company_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job vacancy not found")
    
    if job.qualification_override:
        return JobQualificationResponse(
            job_id=str(job.id),
            qualification_level=job.qualification_level,
            qualification_confidence=job.qualification_confidence,
            qualification_reasoning=job.qualification_reasoning,
            qualification_override=True,
            classified=True,
        )
    
    classification = await job_qualification_service.classify(
        title=job.title,
        department=job.department,
        seniority_level=job.seniority_level,
        description=job.description,
        requirements=job.requirements,
        salary_range=job.salary_range,
        work_model=job.work_model,
        employment_type=job.employment_type,
    )
    
    job.qualification_level = classification["level"]
    job.qualification_confidence = classification["confidence"]
    job.qualification_reasoning = classification["reasoning"]
    job.qualification_classified_at = datetime.utcnow()
    await db.flush()
    
    return JobQualificationResponse(
        job_id=str(job.id),
        qualification_level=classification["level"],
        qualification_confidence=classification["confidence"],
        qualification_reasoning=classification["reasoning"],
        qualification_override=False,
        classified=True,
    )


@router.get("/{job_id}", response_model=JobQualificationResponse)
async def get_qualification(job_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)], db: AsyncSession = Depends(get_db), company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get the current qualification level of a job vacancy."""
    result = await db.execute(select(JobVacancy).where(JobVacancy.id == job_id, JobVacancy.company_id == company_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job vacancy not found")
    
    return JobQualificationResponse(
        job_id=str(job.id),
        qualification_level=job.qualification_level,
        qualification_confidence=job.qualification_confidence,
        qualification_reasoning=job.qualification_reasoning,
        qualification_override=job.qualification_override or False,
        classified=job.qualification_level is not None,
    )


@router.put("/{job_id}/override", response_model=JobQualificationResponse)
async def override_qualification(job_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)], body: OverrideQualificationRequest, db: AsyncSession = Depends(get_db), company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Manually override the qualification level of a job vacancy."""
    result = await db.execute(select(JobVacancy).where(JobVacancy.id == job_id, JobVacancy.company_id == company_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job vacancy not found")
    
    job.qualification_level = body.level
    job.qualification_override = True
    job.qualification_reasoning = body.reason or f"Override manual para '{body.level}'"
    job.qualification_confidence = 1.0
    job.qualification_classified_at = datetime.utcnow()
    await db.flush()
    
    return JobQualificationResponse(
        job_id=str(job.id),
        qualification_level=body.level,
        qualification_confidence=1.0,
        qualification_reasoning=job.qualification_reasoning,
        qualification_override=True,
        classified=True,
    )

reorder_collection_before_item(router)
