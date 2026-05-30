"""
Job Embeddings API - Endpoints for semantic job search.

Provides:
- Create/update job embeddings
- Find similar jobs (semantic search)
- Fast Track suggestions
- Batch processing
"""
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.domains.job_management.services.job_embedding_service import job_embedding_service
from fastapi import Depends
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match
from app.shared.types import WeDoBaseModel
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

router = APIRouter(prefix="/job-embeddings", tags=["Job Embeddings"])
logger = logging.getLogger(__name__)


class CreateEmbeddingRequest(WeDoBaseModel):
    """Request to create/update job embedding."""
    job_id: str
    job_title: str
    department: str | None = None
    seniority: str | None = None
    location: str | None = None
    work_model: str | None = None
    skills: list[str] | None = Field(default_factory=list)
    behavioral_competencies: list[str] | None = Field(default_factory=list)
    description: str | None = None
    outcome_status: str | None = None
    time_to_fill_days: int | None = None
    is_template: bool = False
    draft_id: str | None = None


class SimilarJobsRequest(WeDoBaseModel):
    """Request to find similar jobs."""
    job_title: str
    department: str | None = None
    seniority: str | None = None
    location: str | None = None
    skills: list[str] | None = Field(default_factory=list)
    behavioral: list[str] | None = Field(default_factory=list)
    description: str | None = None
    limit: int = 5
    min_similarity: float = 0.5
    exclude_job_ids: list[str] | None = Field(default_factory=list)


class FastTrackRequest(WeDoBaseModel):
    """Request for Fast Track suggestions."""
    job_title: str
    department: str | None = None
    limit: int = 3


class BatchProcessRequest(WeDoBaseModel):
    """Request for batch embedding processing."""
    job_ids: list[str] | None = Field(default_factory=list)
    limit: int = 100


@router.post("/create", response_model=None)
async def create_embedding(request: CreateEmbeddingRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Create or update embedding for a job vacancy.
    """
    try:
        result = await job_embedding_service.create_or_update_job_embedding(
            company_id=company_id,
            job_id=request.job_id,
            job_title=request.job_title,
            department=request.department,
            seniority=request.seniority,
            location=request.location,
            work_model=request.work_model,
            skills=request.skills,
            behavioral=request.behavioral_competencies,
            description=request.description,
            outcome_status=request.outcome_status,
            time_to_fill_days=request.time_to_fill_days,
            is_template=request.is_template,
            draft_id=request.draft_id
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating embedding: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/similar", response_model=None)
async def find_similar_jobs(request: SimilarJobsRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Find semantically similar jobs using vector search.
    """
    try:
        similar_jobs = await job_embedding_service.find_similar_jobs(
            company_id=company_id,
            job_title=request.job_title,
            department=request.department,
            seniority=request.seniority,
            location=request.location,
            skills=request.skills,
            behavioral=request.behavioral,
            description=request.description,
            limit=request.limit,
            min_similarity=request.min_similarity,
            exclude_job_ids=request.exclude_job_ids
        )
        
        return {
            "success": True,
            "similar_jobs": similar_jobs,
            "count": len(similar_jobs)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding similar jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fast-track", response_model=None)
async def get_fast_track_suggestions(request: FastTrackRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Get Fast Track suggestions for quick job creation.
    
    Returns semantically similar jobs with complete data for copy:
    - Basic info (title, department, location, work_model)
    - Technical skills and behavioral competencies
    - Salary range and benefits
    - WSI/screening questions
    - Description and responsibilities
    """
    try:
        suggestions = await job_embedding_service.get_fast_track_full_suggestions(
            company_id=company_id,
            job_title=request.job_title,
            department=request.department,
            limit=request.limit
        )
        
        return {
            "success": True,
            "suggestions": suggestions,
            "count": len(suggestions),
            "message": f"Found {len(suggestions)} Fast Track options" if suggestions else "No similar jobs found yet"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Fast Track suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class FullJobDataRequest(WeDoBaseModel):
    """Request for full job data."""
    job_id: str


@router.post("/full-job-data", response_model=None)
async def get_full_job_data(request: FullJobDataRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Get complete job data for Fast Track copy.
    
    Returns all fields needed to copy a job:
    - Basic info
    - Skills and competencies
    - Salary and benefits
    - WSI questions
    - Description
    """
    try:
        job_data = await job_embedding_service.get_full_job_data(
            company_id=company_id,
            job_id=request.job_id
        )
        
        if not job_data:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return {
            "success": True,
            "job_data": job_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting full job data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-process", response_model=None)
async def batch_process_embeddings(request: BatchProcessRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Process embeddings for multiple jobs in batch.
    
    Useful for generating embeddings for existing jobs.
    """
    try:
        result = await job_embedding_service.batch_process_jobs(
            company_id=company_id,
            job_ids=request.job_ids if request.job_ids else None,
            limit=request.limit
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error batch processing embeddings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/{company_id}", response_model=None)
async def get_embedding_stats(company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)], _company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get embedding statistics for a company.
    """
    try:
        stats = await job_embedding_service.get_embedding_stats(company_id)
        return {
            "success": True,
            **stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting embedding stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class FastTrackUsageRequest(WeDoBaseModel):
    """Request to record Fast Track usage."""
    source_job_id: str
    new_job_id: str
    modified_fields: list[str] = Field(default_factory=list)
    was_published: bool = False


class OutcomeUpdateRequest(WeDoBaseModel):
    """Request to update job outcome."""
    job_id: str
    outcome_status: str
    time_to_fill_days: int | None = None
    hire_quality_score: float | None = None


@router.post("/fast-track/record-usage", response_model=None)
async def record_fast_track_usage(request: FastTrackUsageRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Record when Fast Track is used to create a job.
    
    This feeds the learning loop to improve future suggestions.
    """
    try:
        result = await job_embedding_service.record_fast_track_usage(
            company_id=company_id,
            source_job_id=request.source_job_id,
            new_job_id=request.new_job_id,
            modified_fields=request.modified_fields,
            was_published=request.was_published
        )
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording Fast Track usage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/outcome", response_model=None)
async def update_job_outcome(request: OutcomeUpdateRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Update job embedding with outcome data.
    
    Outcomes improve future Fast Track suggestions by:
    - Boosting successful jobs in similarity rankings
    - Learning from time-to-fill patterns
    - Incorporating hire quality scores
    """
    try:
        result = await job_embedding_service.update_embedding_from_outcome(
            company_id=company_id,
            job_id=request.job_id,
            outcome_status=request.outcome_status,
            time_to_fill_days=request.time_to_fill_days,
            hire_quality_score=request.hire_quality_score
        )
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating job outcome: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fast-track/insights/{company_id}", response_model=None)
async def get_fast_track_insights(company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)], _company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get Fast Track usage insights for a company.
    
    Returns:
    - Total Fast Track uses
    - Success rate
    - Most used templates
    - Most modified fields
    - Improvement suggestions
    """
    try:
        insights = await job_embedding_service.get_fast_track_insights(company_id)
        return insights
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Fast Track insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))

reorder_collection_before_item(router)
