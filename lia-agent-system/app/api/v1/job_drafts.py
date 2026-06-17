"""
Job Drafts API endpoints.
CRUD operations for job drafts in the wizard flow.
"""
import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import assert_resource_ownership, get_current_user_or_demo
from app.auth.models import User
from app.core.database import get_db, get_tenant_db
from app.models.job_draft import DraftFieldHistory, JobDraft, JobDraftStatus
from app.models.job_vacancy import JobVacancy
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel

router = APIRouter()
logger = logging.getLogger(__name__)


class JobDraftCreate(WeDoBaseModel):
    """Schema for creating a new job draft."""
    raw_input: str = Field(..., min_length=1, description="Raw job description text")
    conversation_id: str | None = None


class JobDraftUpdate(WeDoBaseModel):
    """Schema for partial update of a job draft."""
    job_title: str | None = None
    department: str | None = None
    seniority: str | None = None
    location: str | None = None
    work_model: str | None = None
    hybrid_days: int | None = None
    employment_type: str | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    currency: str | None = None
    country: str | None = None
    pj_rate: float | None = None
    skills: list[str] | None = None
    benefits: list[str] | None = None
    languages: list[str] | None = None
    behavioral_competencies: list[dict] | None = None
    screening_questions: list[dict] | None = None
    pipeline_stages: list[dict] | None = None
    generated_jd: str | None = None
    current_step: str | None = None
    status: str | None = None


class JobDraftFieldHistoryResponse(BaseModel):
    """Schema for field history entry."""
    id: str
    field_name: str
    old_value: dict | None = None
    new_value: dict | None = None
    change_type: str
    confidence_at_change: float | None = None
    source: str | None = None
    reason: str | None = None
    created_at: str
    created_by: str | None = None


class JobDraftResponse(BaseModel):
    """Response schema for job draft."""
    id: str
    company_id: str
    recruiter_id: str
    conversation_id: str | None = None
    status: str
    current_step: str | None = None
    raw_input: str | None = None
    imported_jd: str | None = None
    job_title: str | None = None
    department: str | None = None
    seniority: str | None = None
    location: str | None = None
    work_model: str | None = None
    hybrid_days: int | None = None
    employment_type: str | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    currency: str | None = None
    country: str | None = None
    pj_rate: float | None = None
    skills: list[str] | None = []
    benefits: list[str] | None = []
    languages: list[str] | None = []
    behavioral_competencies: list[dict] | None = []
    screening_questions: list[dict] | None = []
    pipeline_stages: list[dict] | None = []
    generated_jd: str | None = None
    inferred_fields: dict | None = {}
    confirmed_fields: dict | None = {}
    company_defaults_used: dict | None = {}
    confidence_map: dict | None = {}
    insights: list[dict] | None = []
    warnings: list[dict] | None = []
    estimated_ttf: int | None = None
    job_complexity: str | None = None
    published_job_id: str | None = None
    created_at: str
    updated_at: str
    structured_at: str | None = None
    reviewed_at: str | None = None
    published_at: str | None = None


class JobDraftListResponse(BaseModel):
    """Response schema for listing job drafts."""
    drafts: list[JobDraftResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class PublishDraftRequest(WeDoBaseModel):
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
    status: str | None = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    """
    List all job drafts for the user's company with pagination and optional status filter.
    """
    # company_id vem do Depends(require_company_id) - JWT canonical
    # (shadow assignment com get_user_company_id removido 2026-05-22, P1 cleanup)
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
    
    # TENANT-EXEMPT: conditions[0] is JobDraft.company_id == company_id (declared above at L198); AST sensor cannot trace dynamic conditions builder
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
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Get a specific job draft with all details.
    """
    result = await db.execute(
        select(JobDraft).where(JobDraft.id == draft_id, JobDraft.company_id == company_id)
    )
    draft = result.scalar_one_or_none()
    
    if not draft:
        raise HTTPException(status_code=404, detail="Job draft not found")
    
    assert_resource_ownership(draft, current_user, "job draft")
    
    return _draft_to_response(draft)


@router.get("/job-drafts/{draft_id}/history", response_model=list[JobDraftFieldHistoryResponse])
async def get_job_draft_history(
    draft_id: UUID,
    field_name: str | None = Query(None, description="Filter by field name"),
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Get the field change history for a job draft.
    """
    result = await db.execute(
        select(JobDraft).where(JobDraft.id == draft_id, JobDraft.company_id == company_id)
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
    db: AsyncSession = Depends(get_tenant_db), 
company_id: str = Depends(require_company_id)):
    """
    Create a new job draft from raw input text.
    """
    # company_id vem do Depends(require_company_id) - JWT canonical
    # (shadow assignment com get_user_company_id removido 2026-05-22, P1 cleanup)
    draft = JobDraft(
        company_id=company_id,
        recruiter_id=str(current_user.id),
        raw_input=data.raw_input,
        conversation_id=UUID(data.conversation_id) if data.conversation_id else None,
        status=JobDraftStatus.DRAFT,
        current_step="input"
    )
    
    db.add(draft)
    await db.flush()
    await db.refresh(draft)
    
    logger.info(f"Created job draft {draft.id} for company {company_id}")
    
    return _draft_to_response(draft)


@router.patch("/job-drafts/{draft_id}", response_model=JobDraftResponse)
async def update_job_draft(
    draft_id: UUID,
    data: JobDraftUpdate,
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_tenant_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Partially update a job draft's fields.
    """
    result = await db.execute(
        select(JobDraft).where(JobDraft.id == draft_id, JobDraft.company_id == company_id)
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
    
    await db.flush()
    await db.refresh(draft)
    
    logger.info(f"Updated job draft {draft_id}")
    
    return _draft_to_response(draft)


@router.delete("/job-drafts/{draft_id}", status_code=204, response_model=None)
async def delete_job_draft(
    draft_id: UUID,
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_tenant_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Soft delete a job draft by setting its status to CANCELLED.
    """
    result = await db.execute(
        select(JobDraft).where(JobDraft.id == draft_id, JobDraft.company_id == company_id)
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
    
    
    logger.info(f"Soft deleted (cancelled) job draft {draft_id}")
    
    return None


@router.post("/job-drafts/{draft_id}/publish", response_model=PublishDraftResponse)
async def publish_job_draft(
    draft_id: UUID,
    data: PublishDraftRequest | None = None,
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_tenant_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Publish a draft to create a JobVacancy.
    """
    result = await db.execute(
        select(JobDraft).where(JobDraft.id == draft_id, JobDraft.company_id == company_id)
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
        # T-1166 — responsibilities flows through when the wizard stored it on
        # the draft (column may not exist yet on JobDraft for legacy drafts —
        # getattr falls back to []). Empty list is the safe default; previous
        # behaviour silently lost responsibilities by never populating the col.
        responsibilities=list(getattr(draft, "responsibilities", None) or []),
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
    
    await db.flush()
    await db.refresh(job_vacancy)
    
    logger.info(f"Published job draft {draft_id} as job vacancy {job_vacancy.id}")
    
    try:
        from app.shared.services.event_dispatcher import event_dispatcher

# RAILS-DEPRECATED: This endpoint manages Rails-owned entities (candidates/jobs/applies/users).
# See: app/domains/integrations_hub/services/rails_adapter.py
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
