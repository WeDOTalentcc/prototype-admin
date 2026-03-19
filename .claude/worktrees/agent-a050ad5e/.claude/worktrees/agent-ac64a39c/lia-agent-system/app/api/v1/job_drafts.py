"""
Job Drafts API endpoints.
CRUD operations for job drafts in the wizard flow.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional, List
from uuid import UUID
from datetime import datetime
import logging

from app.core.database import get_db
from app.models.job_draft import JobDraft, JobDraftStatus, DraftFieldHistory, ChangeType
from app.models.job_vacancy import JobVacancy
from app.auth.dependencies import (
    get_current_user_or_demo,
    get_user_company_id,
    assert_resource_ownership
)
from app.auth.models import User
from pydantic import BaseModel, Field

router = APIRouter()
logger = logging.getLogger(__name__)


class JobDraftCreate(BaseModel):
    """Schema for creating a new job draft."""
    raw_input: str = Field(..., min_length=1, description="Raw job description text")
    conversation_id: Optional[str] = None


class JobDraftUpdate(BaseModel):
    """Schema for partial update of a job draft."""
    job_title: Optional[str] = None
    department: Optional[str] = None
    seniority: Optional[str] = None
    location: Optional[str] = None
    work_model: Optional[str] = None
    hybrid_days: Optional[int] = None
    employment_type: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    currency: Optional[str] = None
    country: Optional[str] = None
    pj_rate: Optional[float] = None
    skills: Optional[List[str]] = None
    benefits: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    behavioral_competencies: Optional[List[dict]] = None
    screening_questions: Optional[List[dict]] = None
    pipeline_stages: Optional[List[dict]] = None
    generated_jd: Optional[str] = None
    current_step: Optional[str] = None
    status: Optional[str] = None


class JobDraftFieldHistoryResponse(BaseModel):
    """Schema for field history entry."""
    id: str
    field_name: str
    old_value: Optional[dict] = None
    new_value: Optional[dict] = None
    change_type: str
    confidence_at_change: Optional[float] = None
    source: Optional[str] = None
    reason: Optional[str] = None
    created_at: str
    created_by: Optional[str] = None


class JobDraftResponse(BaseModel):
    """Response schema for job draft."""
    id: str
    company_id: str
    recruiter_id: str
    conversation_id: Optional[str] = None
    status: str
    current_step: Optional[str] = None
    raw_input: Optional[str] = None
    imported_jd: Optional[str] = None
    job_title: Optional[str] = None
    department: Optional[str] = None
    seniority: Optional[str] = None
    location: Optional[str] = None
    work_model: Optional[str] = None
    hybrid_days: Optional[int] = None
    employment_type: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    currency: Optional[str] = None
    country: Optional[str] = None
    pj_rate: Optional[float] = None
    skills: Optional[List[str]] = []
    benefits: Optional[List[str]] = []
    languages: Optional[List[str]] = []
    behavioral_competencies: Optional[List[dict]] = []
    screening_questions: Optional[List[dict]] = []
    pipeline_stages: Optional[List[dict]] = []
    generated_jd: Optional[str] = None
    inferred_fields: Optional[dict] = {}
    confirmed_fields: Optional[dict] = {}
    company_defaults_used: Optional[dict] = {}
    confidence_map: Optional[dict] = {}
    insights: Optional[List[dict]] = []
    warnings: Optional[List[dict]] = []
    estimated_ttf: Optional[int] = None
    job_complexity: Optional[str] = None
    published_job_id: Optional[str] = None
    created_at: str
    updated_at: str
    structured_at: Optional[str] = None
    reviewed_at: Optional[str] = None
    published_at: Optional[str] = None


class JobDraftListResponse(BaseModel):
    """Response schema for listing job drafts."""
    drafts: List[JobDraftResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class PublishDraftRequest(BaseModel):
    """Request schema for publishing a draft."""
    status: str = "Rascunho"
    priority: str = "média"


class PublishDraftResponse(BaseModel):
    """Response schema for published job vacancy."""
    draft_id: str
    job_vacancy_id: str
    message: str


def _draft_to_response(draft: JobDraft) -> JobDraftResponse:
    """Convert JobDraft model to response schema."""
    return JobDraftResponse(
        id=str(draft.id),
        company_id=draft.company_id,
        recruiter_id=draft.recruiter_id,
        conversation_id=str(draft.conversation_id) if draft.conversation_id else None,
        status=draft.status.value if draft.status else "draft",
        current_step=draft.current_step,
        raw_input=draft.raw_input,
        imported_jd=draft.imported_jd,
        job_title=draft.job_title,
        department=draft.department,
        seniority=draft.seniority,
        location=draft.location,
        work_model=draft.work_model,
        hybrid_days=draft.hybrid_days,
        employment_type=draft.employment_type,
        salary_min=draft.salary_min,
        salary_max=draft.salary_max,
        currency=draft.currency,
        country=draft.country,
        pj_rate=draft.pj_rate,
        skills=draft.skills or [],
        benefits=draft.benefits or [],
        languages=draft.languages or [],
        behavioral_competencies=draft.behavioral_competencies or [],
        screening_questions=draft.screening_questions or [],
        pipeline_stages=draft.pipeline_stages or [],
        generated_jd=draft.generated_jd,
        inferred_fields=draft.inferred_fields or {},
        confirmed_fields=draft.confirmed_fields or {},
        company_defaults_used=draft.company_defaults_used or {},
        confidence_map=draft.confidence_map or {},
        insights=draft.insights or [],
        warnings=draft.warnings or [],
        estimated_ttf=draft.estimated_ttf,
        job_complexity=draft.job_complexity,
        published_job_id=str(draft.published_job_id) if draft.published_job_id else None,
        created_at=draft.created_at.isoformat() if draft.created_at else "",
        updated_at=draft.updated_at.isoformat() if draft.updated_at else "",
        structured_at=draft.structured_at.isoformat() if draft.structured_at else None,
        reviewed_at=draft.reviewed_at.isoformat() if draft.reviewed_at else None,
        published_at=draft.published_at.isoformat() if draft.published_at else None,
    )


@router.get("/job-drafts", response_model=JobDraftListResponse)
async def list_job_drafts(
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db)
):
    """
    List all job drafts for the user's company with pagination and optional status filter.
    """
    company_id = get_user_company_id(current_user)
    
    conditions = [JobDraft.company_id == company_id]
    
    if status:
        try:
            status_enum = JobDraftStatus(status.lower())
            conditions.append(JobDraft.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Valid values: {', '.join([s.value for s in JobDraftStatus])}"
            )
    
    count_query = select(func.count(JobDraft.id)).where(and_(*conditions))
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0
    
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    offset = (page - 1) * page_size
    
    query = (
        select(JobDraft)
        .where(and_(*conditions))
        .order_by(JobDraft.updated_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    
    result = await db.execute(query)
    drafts = result.scalars().all()
    
    return JobDraftListResponse(
        drafts=[_draft_to_response(d) for d in drafts],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/job-drafts/{draft_id}", response_model=JobDraftResponse)
async def get_job_draft(
    draft_id: UUID,
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific job draft with all details.
    """
    result = await db.execute(
        select(JobDraft).where(JobDraft.id == draft_id)
    )
    draft = result.scalar_one_or_none()
    
    if not draft:
        raise HTTPException(status_code=404, detail="Job draft not found")
    
    assert_resource_ownership(draft, current_user, "job draft")
    
    return _draft_to_response(draft)


@router.get("/job-drafts/{draft_id}/history", response_model=List[JobDraftFieldHistoryResponse])
async def get_job_draft_history(
    draft_id: UUID,
    field_name: Optional[str] = Query(None, description="Filter by field name"),
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the field change history for a job draft.
    """
    result = await db.execute(
        select(JobDraft).where(JobDraft.id == draft_id)
    )
    draft = result.scalar_one_or_none()
    
    if not draft:
        raise HTTPException(status_code=404, detail="Job draft not found")
    
    assert_resource_ownership(draft, current_user, "job draft")
    
    conditions = [DraftFieldHistory.draft_id == draft_id]
    if field_name:
        conditions.append(DraftFieldHistory.field_name == field_name)
    
    history_query = (
        select(DraftFieldHistory)
        .where(and_(*conditions))
        .order_by(DraftFieldHistory.created_at.desc())
    )
    
    history_result = await db.execute(history_query)
    history_entries = history_result.scalars().all()
    
    return [
        JobDraftFieldHistoryResponse(
            id=str(h.id),
            field_name=h.field_name,
            old_value=h.old_value,
            new_value=h.new_value,
            change_type=h.change_type.value if h.change_type else "edited",
            confidence_at_change=h.confidence_at_change,
            source=h.source,
            reason=h.reason,
            created_at=h.created_at.isoformat() if h.created_at else "",
            created_by=h.created_by
        )
        for h in history_entries
    ]


@router.post("/job-drafts", response_model=JobDraftResponse, status_code=201)
async def create_job_draft(
    data: JobDraftCreate,
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new job draft from raw input text.
    """
    company_id = get_user_company_id(current_user)
    
    draft = JobDraft(
        company_id=company_id,
        recruiter_id=str(current_user.id),
        raw_input=data.raw_input,
        conversation_id=UUID(data.conversation_id) if data.conversation_id else None,
        status=JobDraftStatus.DRAFT,
        current_step="input"
    )
    
    db.add(draft)
    await db.commit()
    await db.refresh(draft)
    
    logger.info(f"Created job draft {draft.id} for company {company_id}")
    
    return _draft_to_response(draft)


@router.patch("/job-drafts/{draft_id}", response_model=JobDraftResponse)
async def update_job_draft(
    draft_id: UUID,
    data: JobDraftUpdate,
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db)
):
    """
    Partially update a job draft's fields.
    """
    result = await db.execute(
        select(JobDraft).where(JobDraft.id == draft_id)
    )
    draft = result.scalar_one_or_none()
    
    if not draft:
        raise HTTPException(status_code=404, detail="Job draft not found")
    
    assert_resource_ownership(draft, current_user, "job draft")
    
    if draft.status == JobDraftStatus.PUBLISHED:
        raise HTTPException(
            status_code=400,
            detail="Cannot update a published draft"
        )
    
    if draft.status == JobDraftStatus.CANCELLED:
        raise HTTPException(
            status_code=400,
            detail="Cannot update a cancelled draft"
        )
    
    update_data = data.model_dump(exclude_unset=True)
    
    if "status" in update_data:
        status_value = update_data.pop("status")
        try:
            new_status = JobDraftStatus(status_value.lower())
            if new_status == JobDraftStatus.STRUCTURED:
                draft.mark_structured()
            elif new_status == JobDraftStatus.REVIEWED:
                draft.mark_reviewed()
            elif new_status == JobDraftStatus.CONFIRMED:
                draft.mark_confirmed()
            elif new_status == JobDraftStatus.CANCELLED:
                draft.mark_cancelled()
            else:
                draft.status = new_status
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Valid values: {', '.join([s.value for s in JobDraftStatus])}"
            )
    
    for field, value in update_data.items():
        if hasattr(draft, field):
            old_value = getattr(draft, field)
            setattr(draft, field, value)
            
            if old_value != value:
                history_entry = DraftFieldHistory.create_edited(
                    draft_id=draft.id,
                    field_name=field,
                    old_value=old_value if not isinstance(old_value, (list, dict)) else old_value,
                    new_value=value if not isinstance(value, (list, dict)) else value,
                    created_by=str(current_user.id)
                )
                db.add(history_entry)
    
    draft.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(draft)
    
    logger.info(f"Updated job draft {draft_id}")
    
    return _draft_to_response(draft)


@router.delete("/job-drafts/{draft_id}", status_code=204)
async def delete_job_draft(
    draft_id: UUID,
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete a job draft by setting its status to CANCELLED.
    """
    result = await db.execute(
        select(JobDraft).where(JobDraft.id == draft_id)
    )
    draft = result.scalar_one_or_none()
    
    if not draft:
        raise HTTPException(status_code=404, detail="Job draft not found")
    
    assert_resource_ownership(draft, current_user, "job draft")
    
    if draft.status == JobDraftStatus.PUBLISHED:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete a published draft"
        )
    
    draft.mark_cancelled()
    
    await db.commit()
    
    logger.info(f"Soft deleted (cancelled) job draft {draft_id}")
    
    return None


@router.post("/job-drafts/{draft_id}/publish", response_model=PublishDraftResponse)
async def publish_job_draft(
    draft_id: UUID,
    data: Optional[PublishDraftRequest] = None,
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db)
):
    """
    Publish a draft to create a JobVacancy.
    """
    result = await db.execute(
        select(JobDraft).where(JobDraft.id == draft_id)
    )
    draft = result.scalar_one_or_none()
    
    if not draft:
        raise HTTPException(status_code=404, detail="Job draft not found")
    
    assert_resource_ownership(draft, current_user, "job draft")
    
    if draft.status == JobDraftStatus.PUBLISHED:
        raise HTTPException(
            status_code=400,
            detail="Draft is already published"
        )
    
    if draft.status == JobDraftStatus.CANCELLED:
        raise HTTPException(
            status_code=400,
            detail="Cannot publish a cancelled draft"
        )
    
    if not draft.job_title:
        raise HTTPException(
            status_code=400,
            detail="Cannot publish draft without a job title"
        )
    
    publish_data = data or PublishDraftRequest()
    
    salary_range = None
    if draft.salary_min or draft.salary_max:
        salary_range = {
            "min": draft.salary_min,
            "max": draft.salary_max,
            "currency": draft.currency or "BRL"
        }
    
    job_vacancy = JobVacancy(
        company_id=draft.company_id,
        title=draft.job_title,
        department=draft.department,
        location=draft.location,
        work_model=draft.work_model,
        employment_type=draft.employment_type,
        seniority_level=draft.seniority,
        description=draft.generated_jd or draft.raw_input,
        requirements=draft.skills or [],
        technical_requirements=[],
        languages=[{"language": lang, "level": "fluent"} for lang in (draft.languages or [])],
        behavioral_competencies=draft.behavioral_competencies or [],
        salary_range=salary_range,
        benefits=draft.benefits or [],
        screening_questions=draft.screening_questions or [],
        interview_stages=draft.pipeline_stages or [],
        status=publish_data.status,
        priority=publish_data.priority,
        created_by=str(current_user.id)
    )
    
    db.add(job_vacancy)
    await db.flush()
    
    draft.mark_published(job_vacancy.id)
    
    await db.commit()
    await db.refresh(job_vacancy)
    
    logger.info(f"Published job draft {draft_id} as job vacancy {job_vacancy.id}")
    
    try:
        from app.services.event_dispatcher import event_dispatcher
        await event_dispatcher.on_job_status_changed(
            job_id=str(job_vacancy.id),
            company_id=str(draft.company_id) if draft.company_id else "",
            new_status=publish_data.status or "Ativa",
            previous_status="Rascunho",
            changed_by=str(current_user.id),
            job_title=draft.job_title
        )
    except Exception as e:
        logger.warning(f"Event dispatch failed for draft publish: {e}")
    
    return PublishDraftResponse(
        draft_id=str(draft_id),
        job_vacancy_id=str(job_vacancy.id),
        message="Draft successfully published as job vacancy"
    )
