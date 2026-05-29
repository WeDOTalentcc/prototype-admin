"""
Sourcing Pipeline API - Endpoints for automated candidate sourcing.
"""
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.sourcing.services.sourcing_pipeline_service import sourcing_pipeline_service
from app.api.v1._path_patterns import (
    DUAL_ID_PATH_PATTERN,
    reorder_collection_before_item,
)
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel

router = APIRouter(prefix="/pipeline", tags=["sourcing-pipeline"])


class PipelineConfigRequest(WeDoBaseModel):
    """Request model for updating pipeline configuration."""
    min_candidates_per_job: int | None = Field(None, ge=1, le=100)
    min_qualified_ratio: float | None = Field(None, ge=0.0, le=1.0)
    auto_expand_to_global: bool | None = None
    search_limit_local: int | None = Field(None, ge=1, le=500)
    search_limit_global: int | None = Field(None, ge=1, le=100)
    days_before_low_volume_alert: int | None = Field(None, ge=1, le=30)
    auto_create_tasks: bool | None = None
    auto_create_alerts: bool | None = None


class PipelineConfigResponse(BaseModel):
    """Response model for pipeline configuration."""
    min_candidates_per_job: int
    min_qualified_ratio: float
    auto_expand_to_global: bool
    search_limit_local: int
    search_limit_global: int
    days_before_low_volume_alert: int
    auto_create_tasks: bool
    auto_create_alerts: bool


class JobPipelineStatusResponse(BaseModel):
    """Response model for job pipeline status."""
    job_id: str
    job_title: str
    total_candidates: int
    qualified_candidates: int
    qualified_ratio: float
    needs_more_candidates: bool
    days_open: int
    last_sourcing_run: datetime | None = None
    pipeline_status: str
    recommended_action: str | None = None


class PipelineRunResponse(BaseModel):
    """Response model for a single pipeline run."""
    job_id: str
    success: bool
    candidates_found_local: int
    candidates_found_global: int
    candidates_added: int
    tasks_created: list[str]
    alerts_created: list[str]
    error_message: str | None = None
    expanded_to_global: bool
    duration_seconds: float


class PipelineRunAllResponse(BaseModel):
    """Response model for running pipeline on all jobs."""
    success: bool
    jobs_processed: int
    jobs_succeeded: int = 0
    jobs_failed: int = 0
    total_candidates_added: int
    total_tasks_created: int = 0
    total_alerts_created: int = 0
    duration_seconds: float
    message: str | None = None
    results: list[dict] | None = None


class RunPipelineRequest(WeDoBaseModel):
    """Request model for running pipeline on a job."""
    force_global_search: bool = False


@router.get("/config", response_model=PipelineConfigResponse)
async def get_pipeline_config(company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get current pipeline configuration."""
    config = sourcing_pipeline_service.get_config()
    return config


@router.put("/config", response_model=PipelineConfigResponse)
async def update_pipeline_config(config_update: PipelineConfigRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Update pipeline configuration.
    
    Only provided fields will be updated.
    """
    update_dict = {k: v for k, v in config_update.model_dump().items() if v is not None}
    
    if not update_dict:
        return sourcing_pipeline_service.get_config()
    
    sourcing_pipeline_service.update_config(**update_dict)
    return sourcing_pipeline_service.get_config()


@router.get("/status/{job_id}", response_model=JobPipelineStatusResponse)
async def get_job_pipeline_status(
    job_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get the pipeline status for a specific job.
    
    Returns information about candidate volume, qualified ratio,
    and recommended actions.
    """
    status = await sourcing_pipeline_service.get_job_pipeline_status(db, job_id)
    
    if not status:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    return {
        "job_id": status.job_id,
        "job_title": status.job_title,
        "total_candidates": status.total_candidates,
        "qualified_candidates": status.qualified_candidates,
        "qualified_ratio": status.qualified_ratio,
        "needs_more_candidates": status.needs_more_candidates,
        "days_open": status.days_open,
        "last_sourcing_run": status.last_sourcing_run,
        "pipeline_status": status.pipeline_status,
        "recommended_action": status.recommended_action
    }


@router.get("/jobs-needing-candidates", response_model=list[JobPipelineStatusResponse])
async def get_jobs_needing_candidates(
    limit: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get all open jobs that need more candidates.
    
    Jobs are returned sorted by urgency (lowest qualified ratio first,
    then by days open).
    """
    jobs = await sourcing_pipeline_service.get_jobs_needing_candidates(db, limit=limit)
    
    return [
        {
            "job_id": j.job_id,
            "job_title": j.job_title,
            "total_candidates": j.total_candidates,
            "qualified_candidates": j.qualified_candidates,
            "qualified_ratio": j.qualified_ratio,
            "needs_more_candidates": j.needs_more_candidates,
            "days_open": j.days_open,
            "last_sourcing_run": j.last_sourcing_run,
            "pipeline_status": j.pipeline_status,
            "recommended_action": j.recommended_action
        }
        for j in jobs
    ]


@router.post("/run/{job_id}", response_model=PipelineRunResponse)
async def run_pipeline_for_job(
    job_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    request: RunPipelineRequest | None = None,
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Run the sourcing pipeline for a specific job.
    
    This will:
    1. Search local database for matching candidates
    2. Optionally expand to Pearch AI global search if configured
    3. Add found candidates to the job pipeline
    4. Create follow-up tasks and alerts as needed
    
    The operation is idempotent and safe to run multiple times.
    """
    force_global = request.force_global_search if request else False
    
    result = await sourcing_pipeline_service.run_pipeline_for_job(
        db, 
        job_id, 
        force_global_search=force_global
    )
    
    if not result.success and result.error_message and "not found" in result.error_message.lower():
        raise HTTPException(status_code=404, detail=result.error_message)
    
    return {
        "job_id": result.job_id,
        "success": result.success,
        "candidates_found_local": result.candidates_found_local,
        "candidates_found_global": result.candidates_found_global,
        "candidates_added": result.candidates_added,
        "tasks_created": result.tasks_created,
        "alerts_created": result.alerts_created,
        "error_message": result.error_message,
        "expanded_to_global": result.expanded_to_global,
        "duration_seconds": result.duration_seconds
    }


@router.post("/run-all", response_model=PipelineRunAllResponse)
async def run_pipeline_for_all_jobs(
    max_jobs: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Run the sourcing pipeline for all jobs that need more candidates.
    
    This will process up to max_jobs jobs that need candidates,
    sorted by urgency.
    """
    result = await sourcing_pipeline_service.run_pipeline_for_all_jobs(db, max_jobs=max_jobs)
    
    return result


@router.get("/summary", response_model=None)
async def get_pipeline_summary(db: AsyncSession = Depends(get_db), company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get a summary of the sourcing pipeline status.
    
    Returns counts and statistics about jobs and candidates.
    """
    jobs_needing = await sourcing_pipeline_service.get_jobs_needing_candidates(db, limit=100)
    config = sourcing_pipeline_service.get_config()
    
    critical_count = sum(1 for j in jobs_needing if j.pipeline_status == "critical")
    low_count = sum(1 for j in jobs_needing if j.pipeline_status == "low")
    needs_attention_count = sum(1 for j in jobs_needing if j.pipeline_status == "needs_attention")
    
    return {
        "total_jobs_needing_candidates": len(jobs_needing),
        "critical_jobs": critical_count,
        "low_volume_jobs": low_count,
        "needs_attention_jobs": needs_attention_count,
        "config": config,
        "top_priority_jobs": [
            {
                "job_id": j.job_id,
                "job_title": j.job_title,
                "total_candidates": j.total_candidates,
                "pipeline_status": j.pipeline_status,
                "recommended_action": j.recommended_action
            }
            for j in jobs_needing[:5]
        ]
    }


# Task #455/#458 blindagem: garante que rotas collection-scoped sejam
# registradas ANTES das item-scoped ({job_id}), evitando shadowing.
# Roda uma vez ao fim do modulo apos todas as rotas declaradas.
reorder_collection_before_item(router)
