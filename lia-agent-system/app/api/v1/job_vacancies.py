"""
Job Vacancies API endpoints.
Handles conversational job creation and management.
Complete CRUD operations for job vacancies.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request, File, UploadFile, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_, not_
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
import logging
import uuid as uuid_lib

from app.core.database import get_db
from app.services.job_vacancy_service import job_vacancy_service
from app.services.sourcing_pipeline_service import sourcing_pipeline_service
from app.services.teams_service import TeamsService
from app.services.notification_service import NotificationService, NotificationType, NotificationChannel
from app.services.job_status_webhook_service import job_status_webhook_service
from app.services.job_report_service import job_report_service
from app.schemas.job_vacancy_state import JobVacancyState
from app.models.job_vacancy import JobVacancy
from app.models.candidate import VacancyCandidate, Candidate
from app.models.company import CompanyProfile
from app.models.recruitment_stages import CandidateStageHistory
from app.auth.dependencies import (
    get_current_user, 
    get_current_active_user,
    get_current_user_or_demo,
    get_user_company_id
)
from app.auth.models import User, UserRole
from app.services.plan_limits_service import check_active_jobs_limit, check_active_jobs_limit_or_demo
from app.middleware.trial_enforcement import require_active_subscription, require_active_subscription_or_demo
from pydantic import BaseModel, Field, EmailStr

teams_service = TeamsService()
notification_service = NotificationService()

router = APIRouter()
logger = logging.getLogger(__name__)


# =============================================
# HELPER FUNCTIONS
# =============================================

def _generate_lia_metrics(funnel_data: Optional[dict]) -> dict:
    """
    Generate LIA performance metrics based on funnel data.
    These are simulated metrics for visualization purposes.
    In production, these would come from actual LIA interaction logs.
    """
    import random
    
    if not funnel_data:
        return {
            "pipeline_lia": 0,
            "triagens_agendadas": 0,
            "triagens_realizadas": 0,
            "sem_resposta": 0,
            "entrevistas_agendadas": 0
        }
    
    total = funnel_data.get("total", 0)
    screening = funnel_data.get("screening", 0)
    interview = funnel_data.get("interview", 0)
    
    # Generate realistic-looking metrics with some randomness
    # Pipeline LIA: candidates that entered LIA flow (75-95% of total)
    pipeline_base = int(total * random.uniform(0.75, 0.95)) if total > 0 else 0
    
    # Triagens agendadas: scheduling success rate (60-85% of screening)
    triagens_agendadas = int(screening * random.uniform(0.60, 0.85)) if screening > 0 else 0
    
    # Triagens realizadas: completion rate (70-90% of agendadas)
    triagens_realizadas = int(triagens_agendadas * random.uniform(0.70, 0.90)) if triagens_agendadas > 0 else 0
    
    # Sem resposta: non-responsive candidates (10-25% of total)
    sem_resposta = int(total * random.uniform(0.10, 0.25)) if total > 0 else 0
    
    # Entrevistas agendadas: interview scheduling (70-90% of interview stage)
    entrevistas_agendadas = int(interview * random.uniform(0.70, 0.90)) if interview > 0 else 0
    
    return {
        "pipeline_lia": pipeline_base,
        "triagens_agendadas": triagens_agendadas,
        "triagens_realizadas": triagens_realizadas,
        "sem_resposta": sem_resposta,
        "entrevistas_agendadas": entrevistas_agendadas
    }


# =============================================
# SCHEMAS FOR DIRECT CRUD OPERATIONS
# =============================================

class JobVacancyCreate(BaseModel):
    """Schema for creating a job vacancy directly (not via conversation)."""
    title: str = Field(..., min_length=1, max_length=255)
    department: Optional[str] = None
    location: Optional[str] = None
    work_model: Optional[str] = None  # presencial, híbrido, remoto
    employment_type: Optional[str] = None  # CLT, PJ, Temporário
    seniority_level: Optional[str] = None  # Júnior, Pleno, Sênior, Especialista
    description: Optional[str] = None
    requirements: Optional[List[str]] = []
    technical_requirements: Optional[List[dict]] = []
    languages: Optional[List[dict]] = []
    behavioral_competencies: Optional[List[dict]] = []
    salary: Optional[str] = None
    salary_range: Optional[dict] = None
    benefits: Optional[List[str]] = []
    manager: Optional[str] = None
    manager_email: Optional[str] = None
    recruiter: Optional[str] = None
    recruiter_email: Optional[str] = None
    is_confidential: bool = False
    visibility: str = "public"  # public, internal, confidential, hidden
    access_list: Optional[List[str]] = []  # emails/user_ids with access to confidential jobs
    masked_company_name: Optional[str] = None  # for anonymous publication
    exclude_from_sync: bool = False  # exclude from ATS sync
    status: str = "Rascunho"
    priority: str = "média"
    screening_questions: Optional[List[dict]] = []
    interview_stages: Optional[List[dict]] = []
    eligibility_questions: Optional[List[dict]] = []  # Pre-screening eliminatory questions
    disabled_eligibility_question_ids: Optional[List[str]] = []  # CompanyScreeningQuestion IDs disabled for this job
    confidentiality_config: Optional[dict] = None  # LIA confidentiality settings
    is_affirmative: bool = False
    affirmative_criteria_primary: Optional[str] = None
    affirmative_criteria_secondary: Optional[str] = None
    affirmative_description: Optional[str] = None
    affirmative_document_required: bool = False
    affirmative_document_types: Optional[List[str]] = []
    bonus_range: Optional[dict] = None
    conversation_id: Optional[str] = None


class JobVacancyUpdate(BaseModel):
    """Schema for updating a job vacancy."""
    title: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    work_model: Optional[str] = None
    employment_type: Optional[str] = None
    seniority_level: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[List[str]] = None
    technical_requirements: Optional[List[dict]] = None
    languages: Optional[List[dict]] = None
    behavioral_competencies: Optional[List[dict]] = None
    salary: Optional[str] = None
    salary_range: Optional[dict] = None
    bonus_range: Optional[dict] = None
    benefits: Optional[List[str]] = None
    manager: Optional[str] = None
    manager_email: Optional[str] = None
    recruiter: Optional[str] = None
    recruiter_email: Optional[str] = None
    is_confidential: Optional[bool] = None
    visibility: Optional[str] = None
    access_list: Optional[List[str]] = None
    masked_company_name: Optional[str] = None
    exclude_from_sync: Optional[bool] = None
    status: Optional[str] = None
    stage: Optional[str] = None
    priority: Optional[str] = None
    screening_questions: Optional[List[dict]] = None
    interview_stages: Optional[List[dict]] = None
    eligibility_questions: Optional[List[dict]] = None
    disabled_eligibility_question_ids: Optional[List[str]] = None  # CompanyScreeningQuestion IDs disabled for this job
    confidentiality_config: Optional[dict] = None
    is_affirmative: Optional[bool] = None
    affirmative_criteria_primary: Optional[str] = None
    affirmative_criteria_secondary: Optional[str] = None
    affirmative_description: Optional[str] = None
    affirmative_document_required: Optional[bool] = None
    affirmative_document_types: Optional[List[str]] = None
    enriched_jd: Optional[dict] = None


class JobVacancyResponse(BaseModel):
    """Response schema for job vacancy."""
    id: str
    title: str
    department: Optional[str] = None
    location: Optional[str] = None
    work_model: Optional[str] = None
    employment_type: Optional[str] = None
    seniority_level: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[List[str]] = []
    technical_requirements: Optional[List[dict]] = []
    languages: Optional[List[dict]] = []
    behavioral_competencies: Optional[List[dict]] = []
    salary: Optional[str] = None
    salary_range: Optional[dict] = None
    bonus_range: Optional[dict] = None
    benefits: Optional[List[str]] = []
    manager: Optional[str] = None
    manager_email: Optional[str] = None
    recruiter: Optional[str] = None
    recruiter_email: Optional[str] = None
    is_confidential: bool = False
    visibility: str = "public"
    access_list: Optional[List[str]] = []
    masked_company_name: Optional[str] = None
    exclude_from_sync: bool = False
    created_by: Optional[str] = None
    status: str = "Rascunho"
    stage: Optional[str] = None
    priority: str = "média"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    deadline: Optional[str] = None
    funnel_data: Optional[dict] = None
    lia_metrics: Optional[dict] = None
    nps: Optional[int] = None
    budget: Optional[float] = None
    budget_used: Optional[float] = None
    published_linkedin: bool = False
    published_website: bool = False
    next_actions: Optional[List[str]] = []
    urgency_level: Optional[int] = None
    approval_status: Optional[str] = None
    tags: Optional[List[str]] = []
    screening_questions: Optional[List[dict]] = []
    interview_stages: Optional[List[dict]] = []
    eligibility_questions: Optional[List[dict]] = []
    disabled_eligibility_question_ids: Optional[List[str]] = []  # CompanyScreeningQuestion IDs disabled for this job
    confidentiality_config: Optional[dict] = None
    is_affirmative: bool = False
    affirmative_criteria_primary: Optional[str] = None
    affirmative_criteria_secondary: Optional[str] = None
    affirmative_description: Optional[str] = None
    affirmative_document_required: bool = False
    affirmative_document_types: Optional[List[str]] = []
    conversation_id: Optional[str] = None
    screening_config: Optional[dict] = None
    enriched_jd: Optional[dict] = None


class FinalizeJobVacancyRequest(BaseModel):
    """Request to finalize job vacancy creation."""
    conversation_id: str
    job_vacancy_state: JobVacancyState
    created_by: str


class FinalizeJobVacancyResponse(BaseModel):
    """Response after finalizing job vacancy."""
    success: bool
    job_vacancy_id: str
    title: str
    status: str
    message: str


# =============================================
# BULK OPERATIONS SCHEMAS
# =============================================

class BulkActionError(BaseModel):
    """Single error in a bulk action."""
    job_id: str
    error_message: str


class BulkActionResponse(BaseModel):
    """Response for bulk actions."""
    total_requested: int
    successful: int
    failed: int
    errors: List[BulkActionError] = []


class BulkActionRequest(BaseModel):
    """Request for bulk actions with job IDs list."""
    job_ids: List[UUID] = Field(..., min_length=1, max_length=100, description="List of job vacancy UUIDs")


class BulkAssignRecruiterRequest(BaseModel):
    """Request for bulk recruiter assignment."""
    job_ids: List[UUID] = Field(..., min_length=1, max_length=100, description="List of job vacancy UUIDs")
    recruiter_email: str = Field(..., min_length=1, description="New recruiter email")
    recruiter_name: str = Field(..., min_length=1, description="New recruiter name")


class BulkChangeStatusRequest(BaseModel):
    """Request for bulk status change."""
    job_ids: List[UUID] = Field(..., min_length=1, max_length=100, description="List of job vacancy UUIDs")
    new_status: str = Field(..., min_length=1, description="New status to set")


VALID_JOB_STATUSES = ["Rascunho", "Ativa", "Pausada", "Concluída", "Cancelada", "Arquivada"]

ALLOWED_STATUS_TRANSITIONS = {
    "Rascunho": ["Ativa", "Cancelada", "Arquivada"],
    "Ativa": ["Pausada", "Concluída", "Cancelada", "Arquivada"],
    "Pausada": ["Ativa", "Cancelada", "Arquivada"],
    "Concluída": ["Arquivada"],
    "Cancelada": ["Arquivada"],
    "Arquivada": [],
}


@router.post("/job-vacancies/finalize", response_model=FinalizeJobVacancyResponse)
async def finalize_job_vacancy(
    request: FinalizeJobVacancyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Finalize job vacancy creation and persist to database.
    Called when user confirms all data in conversational flow.
    Multi-tenant: Job vacancy is created with the user's company_id.
    """
    try:
        company_id = get_user_company_id(current_user)
        logger.info(f"📝 Finalizing job vacancy: {request.job_vacancy_state.job_title} for company: {company_id}")
        
        if not request.job_vacancy_state.is_ready_for_publication():
            raise HTTPException(
                status_code=400,
                detail="Job vacancy is not ready for publication. Missing required fields."
            )
        
        job_vacancy = await job_vacancy_service.finalize_job_vacancy(
            state=request.job_vacancy_state,
            conversation_id=request.conversation_id,
            created_by=request.created_by,
            company_id=company_id,
            db=db,
            current_user=current_user,
            pipeline_template_id=getattr(request.job_vacancy_state, 'pipeline_template_id', None)
        )
        
        logger.info(f"✅ Job vacancy finalized: {job_vacancy.id} - {job_vacancy.title}")
        
        job_id = str(job_vacancy.id)
        job_title = str(job_vacancy.title)
        job_status = str(job_vacancy.status)
        
        from app.services.job_audit_service import job_audit_service
        await job_audit_service.log_creation(
            job_id=job_id,
            created_by=request.created_by,
            company_id=company_id,
            db=db,
            job_data={"title": job_title, "status": job_status},
        )
        await db.commit()
        
        return FinalizeJobVacancyResponse(
            success=True,
            job_vacancy_id=job_id,
            title=job_title,
            status=job_status,
            message=f"Vaga '{job_title}' criada com sucesso!"
        )
        
    except Exception as e:
        logger.error(f"❌ Error finalizing job vacancy: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================
# JOB VACANCY SEARCH ENDPOINT
# =============================================

class JobVacancySearchItem(BaseModel):
    """Lightweight job vacancy for search results."""
    id: str
    job_id: Optional[str] = None
    title: str
    status: str
    created_at: str
    description_preview: Optional[str] = None


class JobVacancySearchResponse(BaseModel):
    """Response for job vacancy search."""
    items: List[JobVacancySearchItem]
    total_count: int
    has_more: bool


@router.get("/job-vacancies/search", response_model=JobVacancySearchResponse)
async def search_job_vacancies(
    query: str = Query("", min_length=0, description="Search term for title or job_id"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=50, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """
    Search job vacancies by title or job_id.
    Returns lightweight results for autocomplete/selection.
    Multi-tenant: Only returns vacancies from the user's company.
    """
    try:
        company_id = get_user_company_id(current_user)
        offset = (page - 1) * page_size
        
        base_filter = JobVacancy.company_id == company_id
        
        if query and len(query) >= 2:
            search_term = f"%{query}%"
            search_filter = and_(
                base_filter,
                or_(
                    JobVacancy.title.ilike(search_term),
                    JobVacancy.job_id.ilike(search_term)
                )
            )
        else:
            search_filter = base_filter
        
        count_stmt = select(func.count(JobVacancy.id)).where(search_filter)
        count_result = await db.execute(count_stmt)
        total_count = count_result.scalar() or 0
        
        stmt = (
            select(
                JobVacancy.id,
                JobVacancy.job_id,
                JobVacancy.title,
                JobVacancy.status,
                JobVacancy.created_at,
                JobVacancy.description
            )
            .where(search_filter)
            .order_by(JobVacancy.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        
        result = await db.execute(stmt)
        rows = result.all()
        
        items = []
        for row in rows:
            description_preview = None
            if row.description:
                description_preview = row.description[:150] + "..." if len(row.description) > 150 else row.description
            
            items.append(JobVacancySearchItem(
                id=str(row.id),
                job_id=row.job_id,
                title=row.title,
                status=row.status or "Rascunho",
                created_at=row.created_at.isoformat() if row.created_at else "",
                description_preview=description_preview
            ))
        
        return JobVacancySearchResponse(
            items=items,
            total_count=total_count,
            has_more=(offset + len(items)) < total_count
        )
        
    except Exception as e:
        logger.error(f"Error searching job vacancies: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================
# JOB PUBLICATION ENDPOINTS
# =============================================

class JobPublishRequest(BaseModel):
    """Request to publish a job vacancy."""
    trigger_sourcing: bool = True


class JobPublishResponse(BaseModel):
    """Response after publishing a job."""
    success: bool
    job_id: str
    status: str
    message: str
    sourcing_result: Optional[dict] = None


class ConfirmGlobalSearchRequest(BaseModel):
    """Request to confirm global search."""
    credits_to_use: int = 20


class ConfirmGlobalSearchResponse(BaseModel):
    """Response after global search."""
    success: bool
    candidates_found: int
    candidates_added: int
    credits_used: int
    message: str


class SourcingStatusResponse(BaseModel):
    """Sourcing status for a job."""
    job_id: str
    total_candidates: int
    qualified_candidates: int
    pipeline_status: str
    recommended_action: Optional[str] = None


@router.post("/job-vacancies/{job_id}/publish", response_model=JobPublishResponse)
async def publish_job_vacancy(
    job_id: UUID,
    request: JobPublishRequest = JobPublishRequest(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Publish a job vacancy and trigger automated sourcing.
    Changes status to 'Ativa' and runs local database search.
    """
    company_id = get_user_company_id(current_user)
    
    result = await db.execute(
        select(JobVacancy).where(
            and_(JobVacancy.id == job_id, JobVacancy.company_id == company_id)
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")
    
    old_status = job.status
    job.status = "Ativa"
    job.open_date = datetime.utcnow()
    
    from app.services.job_audit_service import job_audit_service
    changed_by = str(current_user.email) if hasattr(current_user, 'email') else str(current_user.id)
    await job_audit_service.log_publication(
        job_id=str(job_id),
        platform="internal",
        changed_by=changed_by,
        company_id=company_id,
        db=db,
        extra_data={"old_status": old_status, "trigger_sourcing": request.trigger_sourcing},
    )
    
    await db.commit()
    
    try:
        from app.services.event_dispatcher import event_dispatcher
        await event_dispatcher.on_job_status_changed(
            job_id=str(job_id),
            company_id=company_id,
            new_status="Ativa",
            previous_status=old_status,
            changed_by=changed_by,
            job_title=job.title
        )
    except Exception as e:
        logger.warning(f"Event dispatch failed for job publish: {e}")
    
    sourcing_result = None
    if request.trigger_sourcing:
        sourcing_result = await sourcing_pipeline_service.run_post_publish_sourcing(
            db=db,
            job_id=str(job_id),
            user_credits=100,
            expand_to_global=False
        )
        
        if sourcing_result.get("local_candidates_added", 0) > 0:
            await notification_service.create_notification(
                db=db,
                user_id=str(current_user.id),
                title="Candidatos Encontrados",
                message=f"LIA encontrou {sourcing_result['local_candidates_added']} candidatos para {job.title}",
                notification_type=NotificationType.INFO,
                channels=[NotificationChannel.APP, NotificationChannel.TEAMS],
                related_job_id=str(job_id),
                action_url=f"/jobs/{job_id}/pipeline",
                action_label="Ver Pipeline"
            )
    
    return JobPublishResponse(
        success=True,
        job_id=str(job_id),
        status=job.status,
        message=f"Vaga '{job.title}' publicada com sucesso!",
        sourcing_result=sourcing_result
    )


@router.post("/job-vacancies/{job_id}/confirm-global-search", response_model=ConfirmGlobalSearchResponse)
async def confirm_global_search(
    job_id: UUID,
    request: ConfirmGlobalSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Confirm global search expansion using Pearch AI.
    Deducts credits from user account.
    """
    company_id = get_user_company_id(current_user)
    
    result = await db.execute(
        select(JobVacancy).where(
            and_(JobVacancy.id == job_id, JobVacancy.company_id == company_id)
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")
    
    search_result = await sourcing_pipeline_service.confirm_global_search(
        db=db,
        job_id=str(job_id),
        user_id=str(current_user.id),
        credits_to_use=request.credits_to_use
    )
    
    if not search_result.get("success"):
        raise HTTPException(
            status_code=500,
            detail=search_result.get("error", "Erro na busca global")
        )
    
    return ConfirmGlobalSearchResponse(
        success=True,
        candidates_found=search_result.get("candidates_found", 0),
        candidates_added=search_result.get("candidates_added", 0),
        credits_used=search_result.get("credits_deducted", 0),
        message=f"Encontrados {search_result.get('candidates_added', 0)} candidatos via Pearch AI"
    )


@router.get("/job-vacancies/{job_id}/sourcing-status", response_model=SourcingStatusResponse)
async def get_sourcing_status(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get current sourcing status for a job."""
    company_id = get_user_company_id(current_user)
    
    result = await db.execute(
        select(JobVacancy).where(
            and_(JobVacancy.id == job_id, JobVacancy.company_id == company_id)
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")
    
    status = await sourcing_pipeline_service.get_job_pipeline_status(
        db=db,
        job_id=str(job_id)
    )
    
    if not status:
        raise HTTPException(status_code=404, detail="Status do pipeline não encontrado")
    
    return SourcingStatusResponse(
        job_id=str(job_id),
        total_candidates=status.total_candidates,
        qualified_candidates=status.qualified_candidates,
        pipeline_status=status.pipeline_status,
        recommended_action=status.recommended_action
    )


# =============================================
# JOB VACANCY METRICS ENDPOINT
# =============================================

class FunnelMetrics(BaseModel):
    """Funnel metrics for candidates in pipeline stages."""
    total: int = 0
    screening: int = 0
    interview: int = 0
    offer: int = 0
    hired: int = 0
    rejected: int = 0


class PerformanceMetrics(BaseModel):
    """Performance metrics for job vacancy."""
    time_to_fill_days: Optional[int] = None
    avg_time_in_stage_days: Optional[float] = None
    conversion_rate: float = 0.0
    source_breakdown: Dict[str, int] = {}


class ActivityMetrics(BaseModel):
    """Activity metrics for job vacancy."""
    views_7d: int = 0
    applications_7d: int = 0
    interviews_scheduled: int = 0
    last_activity: Optional[str] = None


class SLAMetrics(BaseModel):
    """SLA metrics for job vacancy."""
    within_sla: bool = True
    days_remaining: Optional[int] = None
    deadline: Optional[str] = None


class JobVacancyMetricsResponse(BaseModel):
    """Complete metrics response for a job vacancy."""
    job_id: str
    funnel: FunnelMetrics
    performance: PerformanceMetrics
    activity: ActivityMetrics
    sla: SLAMetrics


@router.get("/job-vacancies/{job_vacancy_id}/metrics", response_model=JobVacancyMetricsResponse)
async def get_job_vacancy_metrics(
    job_vacancy_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """
    Get performance metrics for a specific job vacancy.
    
    Returns:
    - Funnel: Candidate counts by pipeline stage
    - Performance: Time metrics, conversion rate, source breakdown
    - Activity: Recent activity stats (views, applications, interviews)
    - SLA: Deadline compliance status
    
    Multi-tenant: Only returns metrics for vacancies from user's company.
    """
    try:
        company_id = get_user_company_id(current_user)
        
        result = await db.execute(
            select(JobVacancy).where(
                and_(
                    JobVacancy.id == job_vacancy_id,
                    JobVacancy.company_id == company_id
                )
            )
        )
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail="Vaga não encontrada")
        
        stage_counts_result = await db.execute(
            select(
                VacancyCandidate.stage,
                func.count(VacancyCandidate.id).label("count")
            )
            .where(VacancyCandidate.vacancy_id == job_vacancy_id)
            .group_by(VacancyCandidate.stage)
        )
        stage_counts = {row.stage: row.count for row in stage_counts_result.all()}
        
        total_count_result = await db.execute(
            select(func.count(VacancyCandidate.id))
            .where(VacancyCandidate.vacancy_id == job_vacancy_id)
        )
        total_candidates = total_count_result.scalar() or 0
        
        source_counts_result = await db.execute(
            select(
                VacancyCandidate.source,
                func.count(VacancyCandidate.id).label("count")
            )
            .where(VacancyCandidate.vacancy_id == job_vacancy_id)
            .group_by(VacancyCandidate.source)
        )
        source_breakdown = {row.source: row.count for row in source_counts_result.all()}
        
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        applications_7d_result = await db.execute(
            select(func.count(VacancyCandidate.id))
            .where(
                and_(
                    VacancyCandidate.vacancy_id == job_vacancy_id,
                    VacancyCandidate.created_at >= seven_days_ago
                )
            )
        )
        applications_7d = applications_7d_result.scalar() or 0
        
        last_activity_result = await db.execute(
            select(func.max(VacancyCandidate.updated_at))
            .where(VacancyCandidate.vacancy_id == job_vacancy_id)
        )
        last_activity = last_activity_result.scalar()
        
        fallback_funnel = job.funnel_data or {}
        
        screening_count = stage_counts.get("screening", 0) + stage_counts.get("triagem", 0) + stage_counts.get("initial", 0)
        interview_count = stage_counts.get("interview", 0) + stage_counts.get("entrevista", 0)
        offer_count = stage_counts.get("offer", 0) + stage_counts.get("proposta", 0)
        hired_count = stage_counts.get("hired", 0) + stage_counts.get("contratado", 0)
        rejected_count = stage_counts.get("rejected", 0) + stage_counts.get("reprovado", 0) + stage_counts.get("recusado", 0)
        
        funnel = FunnelMetrics(
            total=total_candidates if total_candidates > 0 else fallback_funnel.get("total", 0),
            screening=screening_count if screening_count > 0 else fallback_funnel.get("screening", 0),
            interview=interview_count if interview_count > 0 else fallback_funnel.get("interview", 0),
            offer=offer_count if offer_count > 0 else fallback_funnel.get("offer", 0),
            hired=hired_count if hired_count > 0 else fallback_funnel.get("hired", 0),
            rejected=rejected_count if rejected_count > 0 else fallback_funnel.get("rejected", 0)
        )
        
        time_to_fill_days = None
        if job.closed_at and job.open_date:
            time_to_fill_days = (job.closed_at - job.open_date).days
        elif job.closed_at and job.created_at:
            time_to_fill_days = (job.closed_at - job.created_at).days
        
        avg_time_in_stage = None
        if total_candidates > 0 and job.created_at:
            days_open = (datetime.utcnow() - job.created_at).days or 1
            stages_passed = sum([1 for v in [screening_count, interview_count, offer_count, hired_count] if v > 0])
            if stages_passed > 0:
                avg_time_in_stage = round(days_open / (stages_passed * max(total_candidates, 1)), 1)
        
        conversion_rate = 0.0
        if funnel.total > 0:
            conversion_rate = round(funnel.hired / funnel.total, 3)
        
        interviews_scheduled = interview_count
        
        performance = PerformanceMetrics(
            time_to_fill_days=time_to_fill_days,
            avg_time_in_stage_days=avg_time_in_stage,
            conversion_rate=conversion_rate,
            source_breakdown=source_breakdown
        )
        
        views_7d = job.additional_data.get("views_7d", 0) if job.additional_data else 0
        
        activity = ActivityMetrics(
            views_7d=views_7d,
            applications_7d=applications_7d,
            interviews_scheduled=interviews_scheduled,
            last_activity=last_activity.isoformat() if last_activity else None
        )
        
        within_sla = True
        days_remaining = None
        deadline_str = None
        
        if job.deadline:
            deadline_str = job.deadline.strftime("%Y-%m-%d")
            days_remaining = (job.deadline - datetime.utcnow()).days
            within_sla = days_remaining >= 0
        
        sla = SLAMetrics(
            within_sla=within_sla,
            days_remaining=days_remaining,
            deadline=deadline_str
        )
        
        logger.info(f"📊 Retrieved metrics for job vacancy {job_vacancy_id}: {funnel.total} candidates, conversion {conversion_rate}")
        
        return JobVacancyMetricsResponse(
            job_id=str(job_vacancy_id),
            funnel=funnel,
            performance=performance,
            activity=activity,
            sla=sla
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching job vacancy metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================
# JOB VACANCY ANALYTICS ENDPOINT
# =============================================

class FunnelStageItem(BaseModel):
    """Funnel stage with conversion metrics."""
    stage: str
    count: int
    conversion_rate: float
    avg_days: float


class SourceAnalysisItem(BaseModel):
    """Source analysis with conversion metrics."""
    source: str
    count: int
    conversion_rate: float


class DailyApplicationItem(BaseModel):
    """Daily application count."""
    date: str
    count: int


class JobAnalyticsResponse(BaseModel):
    """Detailed analytics response for a job vacancy."""
    vacancy_id: str
    vacancy_title: str
    
    funnel: List[FunnelStageItem]
    total_candidates: int
    total_hired: int
    overall_conversion_rate: float
    
    avg_time_to_hire: float
    avg_time_to_first_response: float
    time_in_stage: Dict[str, float]
    
    sources: List[SourceAnalysisItem]
    top_source: str
    
    daily_applications: List[DailyApplicationItem]
    weekly_trend: float
    
    avg_lia_score: float
    avg_skills_match: float
    top_rejection_reasons: List[str]
    
    company_avg_time_to_hire: float
    company_avg_conversion_rate: float
    position_percentile: int


@router.get("/job-vacancies/{job_id}/analytics", response_model=JobAnalyticsResponse)
async def get_job_analytics(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """
    Returns detailed analytics for a job vacancy including:
    - Funnel analysis (candidates per stage with conversion rates)
    - Time-based metrics (avg time in each stage)
    - Source analysis (where candidates came from)
    - Performance trends (applications over time)
    - Comparison with company averages
    """
    try:
        company_id = get_user_company_id(current_user)
        
        result = await db.execute(
            select(JobVacancy).where(
                and_(JobVacancy.id == job_id, JobVacancy.company_id == company_id)
            )
        )
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail="Vaga não encontrada")
        
        candidates_result = await db.execute(
            select(VacancyCandidate).where(VacancyCandidate.vacancy_id == job_id)
        )
        vacancy_candidates = candidates_result.scalars().all()
        total_candidates = len(vacancy_candidates)
        
        stage_counts: Dict[str, int] = {}
        source_counts: Dict[str, int] = {}
        source_hired_counts: Dict[str, int] = {}
        hired_count = 0
        lia_scores = []
        match_percentages = []
        
        for vc in vacancy_candidates:
            stage = vc.stage or "initial"
            source = vc.source or "unknown"
            
            stage_counts[stage] = stage_counts.get(stage, 0) + 1
            source_counts[source] = source_counts.get(source, 0) + 1
            
            if stage in ["hired", "contratado"]:
                hired_count += 1
                source_hired_counts[source] = source_hired_counts.get(source, 0) + 1
            
            if vc.lia_score is not None:
                lia_scores.append(vc.lia_score)
            if vc.match_percentage is not None:
                match_percentages.append(vc.match_percentage)
        
        stage_order = ["sourcing", "initial", "pending_gate1", "screening", "triagem", "interview", "entrevista", "offer", "proposta", "hired", "contratado", "rejected", "reprovado"]
        funnel_items = []
        cumulative_count = total_candidates
        
        for stage_name in stage_order:
            if stage_name in stage_counts:
                count = stage_counts[stage_name]
                conversion_rate = (count / cumulative_count * 100) if cumulative_count > 0 else 0.0
                funnel_items.append(FunnelStageItem(
                    stage=stage_name,
                    count=count,
                    conversion_rate=round(conversion_rate, 1),
                    avg_days=0.0
                ))
        
        for stage_name, count in stage_counts.items():
            if stage_name not in stage_order:
                conversion_rate = (count / total_candidates * 100) if total_candidates > 0 else 0.0
                funnel_items.append(FunnelStageItem(
                    stage=stage_name,
                    count=count,
                    conversion_rate=round(conversion_rate, 1),
                    avg_days=0.0
                ))
        
        history_result = await db.execute(
            select(CandidateStageHistory)
            .where(CandidateStageHistory.vacancy_id == job_id)
            .order_by(CandidateStageHistory.created_at.asc())
        )
        stage_history = history_result.scalars().all()
        
        time_in_stage: Dict[str, List[float]] = {}
        rejection_reasons: List[str] = []
        first_response_times: List[float] = []
        hire_times: List[float] = []
        
        for history_entry in stage_history:
            if history_entry.time_in_previous_stage_hours is not None and history_entry.from_stage_name:
                stage_name = history_entry.from_stage_name
                hours = history_entry.time_in_previous_stage_hours
                days = hours / 24.0
                if stage_name not in time_in_stage:
                    time_in_stage[stage_name] = []
                time_in_stage[stage_name].append(days)
            
            if history_entry.to_stage_name in ["rejected", "reprovado"] and history_entry.reason:
                rejection_reasons.append(history_entry.reason)
            
            if history_entry.from_stage_name in ["sourcing", "initial", None] and history_entry.to_stage_name not in ["sourcing", "initial"]:
                if history_entry.time_in_previous_stage_hours is not None:
                    first_response_times.append(history_entry.time_in_previous_stage_hours / 24.0)
            
            if history_entry.to_stage_name in ["hired", "contratado"]:
                candidate_history = [h for h in stage_history if h.candidate_id == history_entry.candidate_id]
                total_time = sum(h.time_in_previous_stage_hours or 0 for h in candidate_history)
                hire_times.append(total_time / 24.0)
        
        avg_time_in_stage: Dict[str, float] = {}
        for stage_name, times in time_in_stage.items():
            avg_time_in_stage[stage_name] = round(sum(times) / len(times), 1) if times else 0.0
        
        for funnel_item in funnel_items:
            if funnel_item.stage in avg_time_in_stage:
                funnel_item.avg_days = avg_time_in_stage[funnel_item.stage]
        
        avg_time_to_hire = round(sum(hire_times) / len(hire_times), 1) if hire_times else 0.0
        avg_time_to_first_response = round(sum(first_response_times) / len(first_response_times), 1) if first_response_times else 0.0
        
        sources_list = []
        for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True):
            hired_from_source = source_hired_counts.get(source, 0)
            conversion = (hired_from_source / count * 100) if count > 0 else 0.0
            sources_list.append(SourceAnalysisItem(
                source=source,
                count=count,
                conversion_rate=round(conversion, 1)
            ))
        
        top_source = sources_list[0].source if sources_list else "unknown"
        
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        daily_apps_result = await db.execute(
            select(
                func.date(VacancyCandidate.created_at).label("date"),
                func.count(VacancyCandidate.id).label("count")
            )
            .where(
                and_(
                    VacancyCandidate.vacancy_id == job_id,
                    VacancyCandidate.created_at >= thirty_days_ago
                )
            )
            .group_by(func.date(VacancyCandidate.created_at))
            .order_by(func.date(VacancyCandidate.created_at))
        )
        daily_apps_rows = daily_apps_result.all()
        
        daily_applications = [
            DailyApplicationItem(date=str(row.date), count=row.count)
            for row in daily_apps_rows
        ]
        
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        fourteen_days_ago = datetime.utcnow() - timedelta(days=14)
        
        this_week_result = await db.execute(
            select(func.count(VacancyCandidate.id))
            .where(
                and_(
                    VacancyCandidate.vacancy_id == job_id,
                    VacancyCandidate.created_at >= seven_days_ago
                )
            )
        )
        this_week_count = this_week_result.scalar() or 0
        
        last_week_result = await db.execute(
            select(func.count(VacancyCandidate.id))
            .where(
                and_(
                    VacancyCandidate.vacancy_id == job_id,
                    VacancyCandidate.created_at >= fourteen_days_ago,
                    VacancyCandidate.created_at < seven_days_ago
                )
            )
        )
        last_week_count = last_week_result.scalar() or 0
        
        weekly_trend = 0.0
        if last_week_count > 0:
            weekly_trend = round(((this_week_count - last_week_count) / last_week_count) * 100, 1)
        elif this_week_count > 0:
            weekly_trend = 100.0
        
        avg_lia_score = round(sum(lia_scores) / len(lia_scores), 1) if lia_scores else 0.0
        avg_skills_match = round(sum(match_percentages) / len(match_percentages), 1) if match_percentages else 0.0
        
        reason_counts: Dict[str, int] = {}
        for reason in rejection_reasons:
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
        top_rejection_reasons = sorted(reason_counts.keys(), key=lambda x: reason_counts[x], reverse=True)[:5]
        
        company_jobs_result = await db.execute(
            select(JobVacancy)
            .where(
                and_(
                    JobVacancy.company_id == company_id,
                    JobVacancy.status.in_(["Concluída", "Encerrada"])
                )
            )
        )
        company_jobs = company_jobs_result.scalars().all()
        
        company_hire_times = []
        company_conversion_rates = []
        
        for company_job in company_jobs:
            if company_job.open_date and company_job.closed_at:
                days_to_fill = (company_job.closed_at - company_job.open_date).days
                company_hire_times.append(days_to_fill)
            
            if company_job.funnel_data:
                total = company_job.funnel_data.get("total", 0)
                hired = company_job.funnel_data.get("hired", 0)
                if total > 0:
                    company_conversion_rates.append((hired / total) * 100)
        
        company_avg_time_to_hire = round(sum(company_hire_times) / len(company_hire_times), 1) if company_hire_times else 0.0
        company_avg_conversion_rate = round(sum(company_conversion_rates) / len(company_conversion_rates), 1) if company_conversion_rates else 0.0
        
        overall_conversion_rate = (hired_count / total_candidates * 100) if total_candidates > 0 else 0.0
        
        position_percentile = 50
        if company_conversion_rates and overall_conversion_rate > 0:
            better_than = sum(1 for r in company_conversion_rates if overall_conversion_rate > r)
            position_percentile = int((better_than / len(company_conversion_rates)) * 100)
        
        logger.info(f"📊 Retrieved analytics for job vacancy {job_id}: {total_candidates} candidates, {hired_count} hired")
        
        return JobAnalyticsResponse(
            vacancy_id=str(job_id),
            vacancy_title=job.title,
            funnel=funnel_items,
            total_candidates=total_candidates,
            total_hired=hired_count,
            overall_conversion_rate=round(overall_conversion_rate, 1),
            avg_time_to_hire=avg_time_to_hire,
            avg_time_to_first_response=avg_time_to_first_response,
            time_in_stage=avg_time_in_stage,
            sources=sources_list,
            top_source=top_source,
            daily_applications=daily_applications,
            weekly_trend=weekly_trend,
            avg_lia_score=avg_lia_score,
            avg_skills_match=avg_skills_match,
            top_rejection_reasons=top_rejection_reasons,
            company_avg_time_to_hire=company_avg_time_to_hire,
            company_avg_conversion_rate=company_avg_conversion_rate,
            position_percentile=position_percentile
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching job vacancy analytics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================
# JOB VACANCY AUDIT HISTORY ENDPOINT
# =============================================

class AuditLogItem(BaseModel):
    """Single audit log entry."""
    id: str
    job_vacancy_id: str
    company_id: str
    action: str
    field_changed: Optional[str] = None
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    changed_by: str
    changed_at: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None


class JobVacancyHistoryResponse(BaseModel):
    """Response for job vacancy audit history."""
    items: List[AuditLogItem]
    total: int
    limit: int
    offset: int
    has_more: bool


@router.get("/job-vacancies/{job_id}/history", response_model=JobVacancyHistoryResponse)
async def get_job_vacancy_history(
    job_id: UUID,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """
    Get audit history for a job vacancy.
    Returns all changes with timestamps and who made them.
    Multi-tenant: Only returns history for vacancies from user's company.
    """
    from app.services.job_audit_service import job_audit_service
    
    try:
        company_id = get_user_company_id(current_user)
        offset = (page - 1) * page_size
        
        result = await db.execute(
            select(JobVacancy).where(
                and_(JobVacancy.id == job_id, JobVacancy.company_id == company_id)
            )
        )
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail="Job vacancy not found")
        
        history = await job_audit_service.get_history(
            job_id=str(job_id),
            company_id=company_id,
            db=db,
            limit=page_size,
            offset=offset
        )
        
        items = [
            AuditLogItem(
                id=item["id"],
                job_vacancy_id=item["job_vacancy_id"],
                company_id=item["company_id"],
                action=item["action"],
                field_changed=item.get("field_changed"),
                old_value=item.get("old_value"),
                new_value=item.get("new_value"),
                changed_by=item["changed_by"],
                changed_at=item["changed_at"],
                ip_address=item.get("ip_address"),
                user_agent=item.get("user_agent"),
                extra_data=item.get("extra_data"),
            )
            for item in history["items"]
        ]
        
        return JobVacancyHistoryResponse(
            items=items,
            total=history["total"],
            limit=history["limit"],
            offset=history["offset"],
            has_more=history["has_more"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching job vacancy history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================
# ARCHETYPES ENDPOINT (must be before param routes)
# =============================================

class ArchetypeCandidateResponse(BaseModel):
    """Hired candidate profile for archetype search."""
    id: str
    name: str
    current_title: Optional[str] = None
    years_experience: Optional[int] = None
    skills: Optional[List[str]] = []
    hired_at: Optional[str] = None


class ArchetypeVacancyResponse(BaseModel):
    """Completed vacancy with hired candidate for archetype search."""
    id: str
    title: str
    department: Optional[str] = None
    closed_at: Optional[str] = None
    hired_candidate: Optional[ArchetypeCandidateResponse] = None


class ArchetypesResponse(BaseModel):
    """Response for archetypes endpoint."""
    vacancies: List[ArchetypeVacancyResponse]
    total: int


@router.get("/job-vacancies/archetypes", response_model=ArchetypesResponse)
async def get_archetypes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """
    Get completed job vacancies with hired candidates for archetype search.
    Returns vacancies with status 'Concluída' that have hired candidate data.
    Used for finding similar candidates based on previously successful hires.
    Multi-tenant: Only returns archetypes from user's company.
    """
    try:
        company_id = get_user_company_id(current_user)
        
        result = await db.execute(
            select(JobVacancy)
            .where(JobVacancy.status == "Concluída")
            .where(JobVacancy.company_id == company_id)
            .order_by(JobVacancy.closed_at.desc())
        )
        job_vacancies = result.scalars().all()
        
        archetypes = []
        for jv in job_vacancies:
            hired_data = jv.additional_data.get("hired_candidate") if jv.additional_data else None
            
            if not hired_data:
                tech_skills = []
                if jv.technical_requirements:
                    tech_skills = [tr.get("technology", "") for tr in jv.technical_requirements[:5] if tr.get("technology")]
                
                hired_data = {
                    "id": f"arch_{str(jv.id)[:8]}",
                    "name": f"Contratado - {jv.title}",
                    "current_title": jv.title,
                    "years_experience": 5 if jv.seniority_level in ["Sênior", "Especialista"] else 3 if jv.seniority_level == "Pleno" else 1,
                    "skills": tech_skills or (jv.requirements[:5] if jv.requirements else []),
                    "hired_at": jv.closed_at.isoformat() if jv.closed_at else None
                }
            
            archetype = ArchetypeVacancyResponse(
                id=str(jv.id),
                title=jv.title,
                department=jv.department,
                closed_at=jv.closed_at.isoformat() if jv.closed_at else None,
                hired_candidate=ArchetypeCandidateResponse(**hired_data)
            )
            archetypes.append(archetype)
        
        logger.info(f"✅ Retrieved {len(archetypes)} archetypes (completed vacancies)")
        
        return ArchetypesResponse(
            vacancies=archetypes,
            total=len(archetypes)
        )
        
    except Exception as e:
        logger.error(f"❌ Error fetching archetypes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================
# STATS/OVERVIEW ENDPOINT (must be before param routes)
# =============================================

class MyJobsStats(BaseModel):
    """Métricas para 'Minhas Vagas' (do recrutador logado)."""
    active: int = 0
    completed: int = 0
    time_to_fill_avg: float = 0.0
    candidates_interviewed: int = 0
    conversion_rate: float = 0.0
    candidates_in_funnel: int = 0
    interviews_last_7d: int = 0
    offers_sent: int = 0


class ActiveJobsStats(BaseModel):
    """Métricas para todas as vagas ativas da empresa."""
    total: int = 0
    avg_days_open: float = 0.0
    at_risk: int = 0
    by_urgency: Dict[str, int] = {"alta": 0, "média": 0, "baixa": 0}
    empty_pipeline: int = 0
    deadline_soon: int = 0


class WeeklyTrend(BaseModel):
    """Tendência semanal de contratações."""
    week: str
    hired: int = 0
    opened: int = 0


class AllJobsStats(BaseModel):
    """Métricas globais de todas as vagas (90 dias)."""
    time_to_fill_avg_90d: float = 0.0
    success_rate: float = 0.0
    hired_last_30d: int = 0
    hired_last_90d: int = 0
    within_sla_pct: float = 0.0
    by_department: Dict[str, int] = {}
    trend_weeks: List[WeeklyTrend] = []


class Insight(BaseModel):
    """Insight automático baseado em dados."""
    type: str  # "alert" ou "suggestion"
    message: str
    severity: Optional[str] = None  # "warning", "critical" (para alerts)
    action: Optional[str] = None  # (para suggestions)


class StatsOverviewResponse(BaseModel):
    """Resposta completa do endpoint de métricas agregadas."""
    my_jobs: MyJobsStats
    active_jobs: ActiveJobsStats
    all_jobs: AllJobsStats
    insights: List[Insight] = []


def _calculate_days_between(start_date: Optional[datetime], end_date: Optional[datetime]) -> int:
    """Calculate days between two dates, handling None values."""
    if not start_date or not end_date:
        return 0
    delta = end_date - start_date
    return max(0, delta.days)


def _is_job_at_risk(job: JobVacancy, now: datetime) -> bool:
    """
    Determine if a job is at risk based on:
    - Empty pipeline (funnel_data total = 0 or None)
    - Stalled > 15 days (no update in last 15 days)
    - Deadline < 10 days away
    """
    funnel = job.funnel_data or {}
    total_candidates = funnel.get("total", 0) or 0
    has_empty_pipeline = total_candidates == 0
    
    days_since_update = 0
    if job.updated_at:
        days_since_update = (now - job.updated_at).days
    is_stalled = days_since_update > 15
    
    days_to_deadline = float('inf')
    if job.deadline:
        days_to_deadline = (job.deadline - now).days
    deadline_soon = 0 <= days_to_deadline < 10
    
    return has_empty_pipeline or is_stalled or deadline_soon


def _generate_insights(
    my_jobs_list: List[JobVacancy],
    active_jobs_list: List[JobVacancy],
    completed_jobs_90d: List[JobVacancy],
    stats: Dict[str, Any],
    now: datetime
) -> List[Insight]:
    """Generate automatic insights based on metrics data."""
    insights = []
    
    stalled_jobs = []
    for job in active_jobs_list:
        if job.updated_at and (now - job.updated_at).days > 15:
            stalled_jobs.append(job)
    
    if len(stalled_jobs) > 0:
        job_titles = [j.title for j in stalled_jobs[:3]]
        titles_str = ", ".join(job_titles)
        if len(stalled_jobs) > 3:
            titles_str += f" e mais {len(stalled_jobs) - 3}"
        insights.append(Insight(
            type="alert",
            message=f"{len(stalled_jobs)} vaga(s) parada(s) há mais de 15 dias: {titles_str}",
            severity="warning" if len(stalled_jobs) < 3 else "critical"
        ))
    
    empty_pipeline_jobs = []
    for job in active_jobs_list:
        funnel = job.funnel_data or {}
        if (funnel.get("total", 0) or 0) == 0:
            empty_pipeline_jobs.append(job)
    
    if len(empty_pipeline_jobs) > 0:
        job_titles = [j.title for j in empty_pipeline_jobs[:3]]
        titles_str = ", ".join(job_titles)
        if len(empty_pipeline_jobs) > 3:
            titles_str += f" e mais {len(empty_pipeline_jobs) - 3}"
        insights.append(Insight(
            type="alert",
            message=f"{len(empty_pipeline_jobs)} vaga(s) sem candidatos no pipeline: {titles_str}",
            severity="critical" if len(empty_pipeline_jobs) > 2 else "warning"
        ))
    
    deadline_soon_jobs = []
    for job in active_jobs_list:
        if job.deadline:
            days_to_deadline = (job.deadline - now).days
            if 0 <= days_to_deadline < 10:
                deadline_soon_jobs.append((job, days_to_deadline))
    
    if len(deadline_soon_jobs) > 0:
        details = [f"{j.title} ({d}d)" for j, d in deadline_soon_jobs[:3]]
        details_str = ", ".join(details)
        insights.append(Insight(
            type="alert",
            message=f"{len(deadline_soon_jobs)} vaga(s) com deadline próximo: {details_str}",
            severity="warning"
        ))
    
    if stats.get("conversion_rate", 0) < 10 and len(my_jobs_list) >= 3:
        insights.append(Insight(
            type="suggestion",
            message="Taxa de conversão abaixo de 10%. Considere revisar os critérios de triagem ou a descrição das vagas.",
            action="review_screening_criteria"
        ))
    
    ttf_avg = stats.get("time_to_fill_avg_90d", 0)
    if ttf_avg > 45:
        insights.append(Insight(
            type="suggestion",
            message=f"Tempo médio de preenchimento está em {ttf_avg:.0f} dias. Considere estratégias de sourcing mais ativas.",
            action="improve_sourcing"
        ))
    
    high_priority_count = sum(1 for j in active_jobs_list if j.priority == "alta")
    if high_priority_count >= 5:
        insights.append(Insight(
            type="alert",
            message=f"{high_priority_count} vagas com prioridade alta abertas. Considere priorizar recursos.",
            severity="warning"
        ))
    
    success_rate = stats.get("success_rate", 0)
    if success_rate > 80 and len(completed_jobs_90d) >= 5:
        insights.append(Insight(
            type="suggestion",
            message=f"Excelente taxa de sucesso de {success_rate:.0f}%! Continue monitorando para manter o padrão.",
            action="maintain_standards"
        ))
    
    return insights


@router.get("/job-vacancies/stats/overview", response_model=StatsOverviewResponse)
async def get_job_vacancies_stats_overview(
    recruiter_email: Optional[str] = Query(None, description="Email do recrutador para filtrar 'Minhas Vagas'"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """
    Get aggregated metrics for the job vacancies dashboard.
    
    Multi-tenant: Always filters by company_id from authenticated user.
    
    Parameters:
    - recruiter_email: Optional filter for "My Jobs" section. If not provided,
      uses the current user's email.
    
    Returns aggregated stats including:
    - my_jobs: Metrics for jobs assigned to the recruiter
    - active_jobs: Metrics for all active jobs in the company
    - all_jobs: Historical metrics (90 days)
    - insights: Automatic alerts and suggestions based on data
    """
    try:
        company_id = get_user_company_id(current_user)
        now = datetime.utcnow()
        logger.info(f"📊 Fetching job vacancies stats overview for company: {company_id}")
        
        recruiter_filter_email = recruiter_email or current_user.email
        
        result = await db.execute(
            select(JobVacancy).where(JobVacancy.company_id == company_id)
        )
        all_company_jobs = result.scalars().all()
        
        my_jobs_list = [
            j for j in all_company_jobs 
            if j.recruiter_email and j.recruiter_email.lower() == recruiter_filter_email.lower()
        ]
        
        active_jobs_list = [j for j in all_company_jobs if j.status == "Ativa"]
        
        completed_jobs = [j for j in all_company_jobs if j.status == "Concluída"]
        
        date_90d_ago = now - timedelta(days=90)
        date_30d_ago = now - timedelta(days=30)
        date_7d_ago = now - timedelta(days=7)
        
        completed_jobs_90d = [
            j for j in completed_jobs 
            if j.closed_at and j.closed_at >= date_90d_ago
        ]
        
        completed_jobs_30d = [
            j for j in completed_jobs 
            if j.closed_at and j.closed_at >= date_30d_ago
        ]
        
        my_active = len([j for j in my_jobs_list if j.status == "Ativa"])
        my_completed = len([j for j in my_jobs_list if j.status == "Concluída"])
        
        my_completed_jobs = [j for j in my_jobs_list if j.status == "Concluída" and j.open_date and j.closed_at]
        if my_completed_jobs:
            total_ttf = sum(_calculate_days_between(j.open_date, j.closed_at) for j in my_completed_jobs)
            my_time_to_fill_avg = total_ttf / len(my_completed_jobs)
        else:
            my_time_to_fill_avg = 0.0
        
        my_candidates_interviewed = 0
        my_candidates_in_funnel = 0
        my_offers_sent = 0
        
        for job in my_jobs_list:
            funnel = job.funnel_data or {}
            my_candidates_in_funnel += funnel.get("total", 0) or 0
            my_candidates_interviewed += funnel.get("interview", 0) or funnel.get("entrevista", 0) or 0
            my_offers_sent += funnel.get("offer", 0) or funnel.get("proposta", 0) or 0
        
        my_conversion_rate = 0.0
        if my_candidates_in_funnel > 0:
            hired_count = sum(
                (j.funnel_data or {}).get("hired", 0) or (j.funnel_data or {}).get("contratado", 0) or 0
                for j in my_jobs_list
            )
            my_conversion_rate = (hired_count / my_candidates_in_funnel) * 100
        
        my_interviews_last_7d = 0
        for job in my_jobs_list:
            if job.updated_at and job.updated_at >= date_7d_ago:
                funnel = job.funnel_data or {}
                my_interviews_last_7d += funnel.get("interview", 0) or funnel.get("entrevista", 0) or 0
        
        my_jobs_stats = MyJobsStats(
            active=my_active,
            completed=my_completed,
            time_to_fill_avg=round(my_time_to_fill_avg, 1),
            candidates_interviewed=my_candidates_interviewed,
            conversion_rate=round(my_conversion_rate, 1),
            candidates_in_funnel=my_candidates_in_funnel,
            interviews_last_7d=my_interviews_last_7d,
            offers_sent=my_offers_sent
        )
        
        active_total = len(active_jobs_list)
        
        active_with_open_date = [j for j in active_jobs_list if j.open_date]
        if active_with_open_date:
            total_days_open = sum((now - j.open_date).days for j in active_with_open_date)
            avg_days_open = total_days_open / len(active_with_open_date)
        else:
            avg_days_open = 0.0
        
        at_risk_count = sum(1 for j in active_jobs_list if _is_job_at_risk(j, now))
        
        by_urgency = {"alta": 0, "média": 0, "baixa": 0}
        for job in active_jobs_list:
            priority = (job.priority or "média").lower()
            if priority in by_urgency:
                by_urgency[priority] += 1
            else:
                by_urgency["média"] += 1
        
        empty_pipeline_count = sum(
            1 for j in active_jobs_list 
            if (j.funnel_data or {}).get("total", 0) == 0 or j.funnel_data is None
        )
        
        deadline_soon_count = sum(
            1 for j in active_jobs_list 
            if j.deadline and 0 <= (j.deadline - now).days < 10
        )
        
        active_jobs_stats = ActiveJobsStats(
            total=active_total,
            avg_days_open=round(avg_days_open, 1),
            at_risk=at_risk_count,
            by_urgency=by_urgency,
            empty_pipeline=empty_pipeline_count,
            deadline_soon=deadline_soon_count
        )
        
        completed_with_dates_90d = [
            j for j in completed_jobs_90d 
            if j.open_date and j.closed_at
        ]
        if completed_with_dates_90d:
            total_ttf_90d = sum(_calculate_days_between(j.open_date, j.closed_at) for j in completed_with_dates_90d)
            time_to_fill_avg_90d = total_ttf_90d / len(completed_with_dates_90d)
        else:
            time_to_fill_avg_90d = 0.0
        
        total_jobs_90d = len([
            j for j in all_company_jobs 
            if j.created_at and j.created_at >= date_90d_ago
        ])
        success_rate = (len(completed_jobs_90d) / total_jobs_90d * 100) if total_jobs_90d > 0 else 0.0
        
        hired_last_30d = len(completed_jobs_30d)
        hired_last_90d = len(completed_jobs_90d)
        
        within_sla_count = 0
        for job in completed_jobs_90d:
            if job.deadline and job.closed_at:
                if job.closed_at <= job.deadline:
                    within_sla_count += 1
        within_sla_pct = (within_sla_count / len(completed_jobs_90d) * 100) if completed_jobs_90d else 0.0
        
        by_department: Dict[str, int] = {}
        for job in active_jobs_list:
            dept = job.department or "Não definido"
            by_department[dept] = by_department.get(dept, 0) + 1
        
        trend_weeks: List[WeeklyTrend] = []
        for weeks_ago in range(7, -1, -1):
            week_start = now - timedelta(weeks=weeks_ago + 1)
            week_end = now - timedelta(weeks=weeks_ago)
            week_label = week_start.strftime("%d/%m")
            
            hired_in_week = len([
                j for j in completed_jobs 
                if j.closed_at and week_start <= j.closed_at < week_end
            ])
            opened_in_week = len([
                j for j in all_company_jobs 
                if j.created_at and week_start <= j.created_at < week_end
            ])
            
            trend_weeks.append(WeeklyTrend(
                week=week_label,
                hired=hired_in_week,
                opened=opened_in_week
            ))
        
        all_jobs_stats = AllJobsStats(
            time_to_fill_avg_90d=round(time_to_fill_avg_90d, 1),
            success_rate=round(success_rate, 1),
            hired_last_30d=hired_last_30d,
            hired_last_90d=hired_last_90d,
            within_sla_pct=round(within_sla_pct, 1),
            by_department=by_department,
            trend_weeks=trend_weeks
        )
        
        insights_input_stats = {
            "conversion_rate": my_conversion_rate,
            "time_to_fill_avg_90d": time_to_fill_avg_90d,
            "success_rate": success_rate
        }
        
        insights = _generate_insights(
            my_jobs_list=my_jobs_list,
            active_jobs_list=active_jobs_list,
            completed_jobs_90d=completed_jobs_90d,
            stats=insights_input_stats,
            now=now
        )
        
        logger.info(f"✅ Stats overview generated: {active_total} active jobs, {len(completed_jobs_90d)} completed (90d), {len(insights)} insights")
        
        return StatsOverviewResponse(
            my_jobs=my_jobs_stats,
            active_jobs=active_jobs_stats,
            all_jobs=all_jobs_stats,
            insights=insights
        )
        
    except Exception as e:
        logger.error(f"❌ Error fetching job vacancies stats overview: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/job-vacancies/{job_vacancy_id}")
async def get_job_vacancy(
    job_vacancy_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """
    Get job vacancy by ID.
    Multi-tenant: Only returns vacancy if user has access to that company.
    Uses demo user if not authenticated (for development).
    """
    try:
        from sqlalchemy import select
        
        user_company = get_user_company_id(current_user)
        
        result = await db.execute(
            select(JobVacancy).where(
                JobVacancy.id == job_vacancy_id,
                JobVacancy.company_id == user_company
            )
        )
        job_vacancy = result.scalar_one_or_none()
        
        if not job_vacancy:
            raise HTTPException(status_code=404, detail="Job vacancy not found")
        
        # Visibility access control
        user_email = (current_user.email or "").lower()
        user_id = str(current_user.id) if current_user.id else ""
        is_admin = current_user.role == UserRole.admin if hasattr(current_user, 'role') else False
        jv_visibility = job_vacancy.visibility or "public"
        
        # Check access based on visibility
        can_access = False
        if jv_visibility in ["public", "internal"]:
            can_access = True
        elif is_admin:
            can_access = True
        elif jv_visibility == "confidential":
            jv_created_by = (job_vacancy.created_by or "").lower()
            jv_recruiter_email = (job_vacancy.recruiter_email or "").lower()
            jv_access_list = [x.lower() for x in (job_vacancy.access_list or [])]
            if user_email == jv_created_by or user_email == jv_recruiter_email:
                can_access = True
            elif user_email in jv_access_list or user_id in (job_vacancy.access_list or []):
                can_access = True
        # Hidden: only admin (handled above)
        
        if not can_access:
            raise HTTPException(status_code=403, detail="Você não tem acesso a esta vaga")
        
        # Convert to dict
        return {
            "id": str(job_vacancy.id),
            "title": job_vacancy.title,
            "department": job_vacancy.department,
            "location": job_vacancy.location,
            "work_model": job_vacancy.work_model,
            "seniority_level": job_vacancy.seniority_level,
            "status": job_vacancy.status,
            "is_confidential": job_vacancy.is_confidential,
            "salary_range": job_vacancy.salary_range,
            "technical_requirements": job_vacancy.technical_requirements,
            "languages": job_vacancy.languages,
            "behavioral_competencies": job_vacancy.behavioral_competencies,
            "interview_stages": job_vacancy.interview_stages,
            "screening_questions": job_vacancy.screening_questions,
            "disabled_eligibility_question_ids": job_vacancy.disabled_eligibility_question_ids or [],
            "timeline": job_vacancy.timeline,
            "governance_rules": job_vacancy.governance_rules,
            "whatsapp_template_type": job_vacancy.whatsapp_template_type,
            "screening_config": job_vacancy.screening_config,
            "screening_status": derive_screening_status(job_vacancy.screening_config),
            "enriched_jd": job_vacancy.enriched_jd,
            "created_at": job_vacancy.created_at.isoformat() if hasattr(job_vacancy.created_at, 'isoformat') else None,
            "updated_at": job_vacancy.updated_at.isoformat() if hasattr(job_vacancy.updated_at, 'isoformat') else None,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting job vacancy: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/job-vacancies")
async def list_job_vacancies(
    status: Optional[str] = None,
    visibility: Optional[str] = None,
    skip: int = 0,
    limit: int = 500,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """
    List job vacancies with optional status filter.
    Multi-tenant: Only returns vacancies from user's company.
    Uses demo user if not authenticated (for development).
    
    Visibility rules:
    - public: todos recrutadores da empresa veem
    - internal: só equipe interna vê (não publica em job boards)
    - confidential: só owner + access_list + admin veem
    - hidden: só admin vê
    """
    try:
        from sqlalchemy import select
        
        company_id = get_user_company_id(current_user)
        user_email = current_user.email.lower() if current_user.email else ""
        user_id = str(current_user.id) if current_user.id else ""
        is_admin = current_user.role == UserRole.admin if hasattr(current_user, 'role') else False
        
        query = select(JobVacancy).where(JobVacancy.company_id == company_id)
        
        if status:
            query = query.where(JobVacancy.status == status)
        
        if visibility:
            query = query.where(JobVacancy.visibility == visibility)
        
        query = query.offset(skip).limit(limit).order_by(JobVacancy.created_at.desc())
        
        result = await db.execute(query)
        all_vacancies = result.scalars().all()
        
        # Filter by visibility rules
        job_vacancies = []
        for jv in all_vacancies:
            jv_visibility = jv.visibility or "public"
            
            # Public and internal: everyone in company sees
            if jv_visibility in ["public", "internal"]:
                job_vacancies.append(jv)
                continue
            
            # Admin sees all
            if is_admin:
                job_vacancies.append(jv)
                continue
            
            # Confidential: owner + access_list
            if jv_visibility == "confidential":
                jv_created_by = (jv.created_by or "").lower()
                jv_recruiter_email = (jv.recruiter_email or "").lower()
                jv_access_list = [x.lower() for x in (jv.access_list or [])]
                
                if user_email == jv_created_by or user_email == jv_recruiter_email:
                    job_vacancies.append(jv)
                elif user_email in jv_access_list or user_id in (jv.access_list or []):
                    job_vacancies.append(jv)
                continue
            
            # Hidden: only admin (already handled above)
        
        return {
            "total": len(job_vacancies),
            "skip": skip,
            "limit": limit,
            "items": [
                {
                    "id": str(jv.id),
                    "title": jv.title,
                    "department": jv.department,
                    "location": jv.location,
                    "work_model": jv.work_model,
                    "employment_type": jv.employment_type,
                    "seniority_level": jv.seniority_level,
                    "description": jv.description,
                    "requirements": jv.requirements or [],
                    "technical_requirements": jv.technical_requirements or [],
                    "languages": jv.languages or [],
                    "behavioral_competencies": jv.behavioral_competencies or [],
                    "salary_range": jv.salary_range,
                    "benefits": jv.benefits or [],
                    "manager": jv.manager,
                    "manager_email": jv.manager_email,
                    "recruiter": jv.recruiter,
                    "recruiter_email": jv.recruiter_email,
                    "is_confidential": jv.is_confidential or False,
                    "visibility": jv.visibility or "public",
                    "access_list": jv.access_list or [],
                    "masked_company_name": jv.masked_company_name,
                    "exclude_from_sync": jv.exclude_from_sync or False,
                    "created_by": jv.created_by,
                    "status": jv.status or "Rascunho",
                    "stage": jv.stage,
                    "priority": jv.priority or "média",
                    "created_at": jv.created_at.isoformat() if hasattr(jv.created_at, 'isoformat') else None,
                    "updated_at": jv.updated_at.isoformat() if hasattr(jv.updated_at, 'isoformat') else None,
                    "deadline": jv.deadline.isoformat() if hasattr(jv, 'deadline') and jv.deadline else None,
                    "funnel_data": jv.funnel_data,
                    "lia_metrics": jv.lia_metrics or _generate_lia_metrics(jv.funnel_data),
                    "nps": jv.nps,
                    "budget": jv.budget,
                    "budget_used": jv.budget_used,
                    "published_linkedin": jv.published_linkedin or False,
                    "published_website": jv.published_website or False,
                    "next_actions": jv.next_actions or [],
                    "urgency_level": jv.urgency_level,
                    "approval_status": jv.approval_status,
                    "tags": jv.tags or [],
                    "salary": jv.salary,
                    "screening_questions": jv.screening_questions or [],
                    "interview_stages": jv.interview_stages or [],
                    "conversation_id": str(jv.conversation_id) if jv.conversation_id else None,
                    "screening_config": jv.screening_config,
                    "screening_status": derive_screening_status(jv.screening_config)
                }
                for jv in job_vacancies
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Error listing job vacancies: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================
# DIRECT CRUD ENDPOINTS (não conversacional)
# =============================================

@router.post("/job-vacancies", response_model=JobVacancyResponse)
async def create_job_vacancy(
    job_data: JobVacancyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
    _trial_check: None = Depends(require_active_subscription_or_demo),
    _plan_check: None = Depends(check_active_jobs_limit_or_demo),
):
    """
    Create a new job vacancy directly (not via conversation).
    Useful for quick creation or API integrations.
    Multi-tenant: Job vacancy is created with the user's company_id.
    Uses demo user if not authenticated (for development).
    """
    try:
        company_id = get_user_company_id(current_user)
        logger.info(f"📝 Creating job vacancy: {job_data.title} for company: {company_id}")
        
        job_vacancy = JobVacancy(
            id=uuid_lib.uuid4(),
            title=job_data.title,
            department=job_data.department,
            location=job_data.location,
            work_model=job_data.work_model,
            employment_type=job_data.employment_type,
            seniority_level=job_data.seniority_level,
            description=job_data.description,
            requirements=job_data.requirements or [],
            technical_requirements=job_data.technical_requirements or [],
            languages=job_data.languages or [],
            behavioral_competencies=job_data.behavioral_competencies or [],
            salary=job_data.salary,
            salary_range=job_data.salary_range,
            benefits=job_data.benefits or [],
            manager=job_data.manager,
            manager_email=job_data.manager_email,
            recruiter=job_data.recruiter,
            recruiter_email=job_data.recruiter_email,
            is_confidential=job_data.is_confidential,
            visibility=job_data.visibility,
            access_list=job_data.access_list or [],
            masked_company_name=job_data.masked_company_name,
            exclude_from_sync=job_data.exclude_from_sync,
            status=job_data.status,
            priority=job_data.priority,
            screening_questions=job_data.screening_questions or [],
            interview_stages=job_data.interview_stages or [],
            disabled_eligibility_question_ids=job_data.disabled_eligibility_question_ids or [],
            conversation_id=uuid_lib.UUID(job_data.conversation_id) if job_data.conversation_id else None,
            company_id=company_id,
            created_by=str(current_user.id),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(job_vacancy)
        await db.commit()
        await db.refresh(job_vacancy)
        
        logger.info(f"✅ Job vacancy created: {job_vacancy.id} - {job_vacancy.title}")
        
        return JobVacancyResponse(
            id=str(job_vacancy.id),
            title=job_vacancy.title,
            department=job_vacancy.department,
            location=job_vacancy.location,
            work_model=job_vacancy.work_model,
            employment_type=job_vacancy.employment_type,
            seniority_level=job_vacancy.seniority_level,
            description=job_vacancy.description,
            requirements=job_vacancy.requirements or [],
            technical_requirements=job_vacancy.technical_requirements or [],
            languages=job_vacancy.languages or [],
            behavioral_competencies=job_vacancy.behavioral_competencies or [],
            salary=job_vacancy.salary,
            salary_range=job_vacancy.salary_range,
            benefits=job_vacancy.benefits or [],
            manager=job_vacancy.manager,
            manager_email=job_vacancy.manager_email,
            recruiter=job_vacancy.recruiter,
            recruiter_email=job_vacancy.recruiter_email,
            is_confidential=job_vacancy.is_confidential or False,
            status=job_vacancy.status or "Rascunho",
            priority=job_vacancy.priority or "média",
            created_at=job_vacancy.created_at.isoformat() if job_vacancy.created_at else None,
            updated_at=job_vacancy.updated_at.isoformat() if job_vacancy.updated_at else None,
            screening_questions=job_vacancy.screening_questions or [],
            interview_stages=job_vacancy.interview_stages or [],
            disabled_eligibility_question_ids=job_vacancy.disabled_eligibility_question_ids or [],
            conversation_id=str(job_vacancy.conversation_id) if job_vacancy.conversation_id else None
        )

    except Exception as e:
        logger.error(f"❌ Error creating job vacancy: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/job-vacancies/{job_vacancy_id}", response_model=JobVacancyResponse)
async def update_job_vacancy(
    job_vacancy_id: UUID,
    job_data: JobVacancyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """
    Update an existing job vacancy.
    Only updates fields that are provided (non-None).
    Multi-tenant: Only allows update if user has access to vacancy's company.
    """
    try:
        logger.info(f"📝 Updating job vacancy: {job_vacancy_id}")
        
        user_company = get_user_company_id(current_user)
        
        query = select(JobVacancy).where(
            JobVacancy.id == job_vacancy_id,
            JobVacancy.company_id == user_company
        )
        
        result = await db.execute(query)
        job_vacancy = result.scalar_one_or_none()
        
        if not job_vacancy:
            raise HTTPException(status_code=404, detail="Job vacancy not found")
        
        update_data = job_data.model_dump(exclude_unset=True, exclude_none=True)
        update_data["updated_at"] = datetime.utcnow()
        
        changes = {}
        for field, value in update_data.items():
            if field == "updated_at":
                continue
            if hasattr(job_vacancy, field):
                old_value = getattr(job_vacancy, field)
                if old_value != value:
                    changes[field] = {"old": old_value, "new": value}
                setattr(job_vacancy, field, value)
        
        if changes:
            from app.services.job_audit_service import job_audit_service
            changed_by = str(current_user.email) if hasattr(current_user, 'email') else str(current_user.id)
            await job_audit_service.log_update(
                job_id=str(job_vacancy_id),
                changes=changes,
                changed_by=changed_by,
                company_id=user_company,
                db=db,
            )
        
        await db.commit()
        await db.refresh(job_vacancy)
        
        logger.info(f"✅ Job vacancy updated: {job_vacancy.id} - {job_vacancy.title} ({len(changes)} fields changed)")
        
        return JobVacancyResponse(
            id=str(job_vacancy.id),
            title=job_vacancy.title,
            department=job_vacancy.department,
            location=job_vacancy.location,
            work_model=job_vacancy.work_model,
            employment_type=job_vacancy.employment_type,
            seniority_level=job_vacancy.seniority_level,
            description=job_vacancy.description,
            requirements=job_vacancy.requirements or [],
            technical_requirements=job_vacancy.technical_requirements or [],
            languages=job_vacancy.languages or [],
            behavioral_competencies=job_vacancy.behavioral_competencies or [],
            salary=job_vacancy.salary,
            salary_range=job_vacancy.salary_range,
            benefits=job_vacancy.benefits or [],
            manager=job_vacancy.manager,
            manager_email=job_vacancy.manager_email,
            recruiter=job_vacancy.recruiter,
            recruiter_email=job_vacancy.recruiter_email,
            is_confidential=job_vacancy.is_confidential or False,
            status=job_vacancy.status or "Rascunho",
            priority=job_vacancy.priority or "média",
            created_at=job_vacancy.created_at.isoformat() if job_vacancy.created_at else None,
            updated_at=job_vacancy.updated_at.isoformat() if job_vacancy.updated_at else None,
            screening_questions=job_vacancy.screening_questions or [],
            interview_stages=job_vacancy.interview_stages or [],
            disabled_eligibility_question_ids=job_vacancy.disabled_eligibility_question_ids or [],
            conversation_id=str(job_vacancy.conversation_id) if job_vacancy.conversation_id else None,
            enriched_jd=job_vacancy.enriched_jd
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating job vacancy: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/job-vacancies/{job_vacancy_id}")
async def delete_job_vacancy(
    job_vacancy_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a job vacancy (soft delete - sets status to 'Arquivada').
    Multi-tenant: Only allows delete if user has access to vacancy's company.
    """
    try:
        logger.info(f"🗑️ Deleting job vacancy: {job_vacancy_id}")
        
        user_company = get_user_company_id(current_user)
        
        query = select(JobVacancy).where(
            JobVacancy.id == job_vacancy_id,
            JobVacancy.company_id == user_company
        )
        
        result = await db.execute(query)
        job_vacancy = result.scalar_one_or_none()
        
        if not job_vacancy:
            raise HTTPException(status_code=404, detail="Job vacancy not found")
        
        old_status = job_vacancy.status
        job_vacancy.status = "Arquivada"
        job_vacancy.updated_at = datetime.utcnow()
        
        from app.services.job_audit_service import job_audit_service
        changed_by = str(current_user.email) if hasattr(current_user, 'email') else str(current_user.id)
        await job_audit_service.log_archive(
            job_id=str(job_vacancy_id),
            changed_by=changed_by,
            company_id=user_company,
            db=db,
        )
        
        await db.commit()
        
        logger.info(f"✅ Job vacancy archived: {job_vacancy_id}")
        
        return {
            "success": True,
            "message": f"Vaga '{job_vacancy.title}' arquivada com sucesso",
            "id": str(job_vacancy_id)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting job vacancy: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/job-vacancies/{job_vacancy_id}/status")
async def update_job_vacancy_status(
    job_vacancy_id: UUID,
    status: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update job vacancy status.
    Valid statuses: Rascunho, Ativa, Pausada, Concluída, Arquivada
    Multi-tenant: Only allows update if user has access to vacancy's company.
    """
    try:
        valid_statuses = ["Rascunho", "Ativa", "Pausada", "Concluída", "Arquivada"]
        if status not in valid_statuses:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid status. Valid options: {', '.join(valid_statuses)}"
            )
        
        user_company = get_user_company_id(current_user)
        
        query = select(JobVacancy).where(
            JobVacancy.id == job_vacancy_id,
            JobVacancy.company_id == user_company
        )
        
        result = await db.execute(query)
        job_vacancy = result.scalar_one_or_none()
        
        if not job_vacancy:
            raise HTTPException(status_code=404, detail="Job vacancy not found")
        
        old_status = job_vacancy.status
        job_vacancy.status = status
        job_vacancy.updated_at = datetime.utcnow()
        
        from app.services.job_audit_service import job_audit_service
        changed_by = str(current_user.email) if hasattr(current_user, 'email') else str(current_user.id)
        await job_audit_service.log_status_change(
            job_id=str(job_vacancy_id),
            old_status=old_status,
            new_status=status,
            changed_by=changed_by,
            company_id=user_company,
            db=db,
        )
        
        await db.commit()
        
        logger.info(f"✅ Job vacancy status updated: {job_vacancy_id} ({old_status} → {status})")
        
        try:
            await job_status_webhook_service.dispatch_status_change(
                job_id=str(job_vacancy_id),
                old_status=old_status,
                new_status=status,
                company_id=user_company,
                db=db,
                changed_by=str(current_user.email) if hasattr(current_user, 'email') else str(current_user.id),
                job_title=job_vacancy.title
            )
        except Exception as webhook_error:
            logger.warning(f"Webhook dispatch failed (non-blocking): {webhook_error}")
        
        return {
            "success": True,
            "id": str(job_vacancy_id),
            "old_status": old_status,
            "new_status": status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating job vacancy status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================
# JOB PUBLICATION AND SOURCING ENDPOINTS
# =============================================

class JobPublishRequest(BaseModel):
    """Request to publish a job vacancy."""
    expand_to_global: bool = False
    user_credits: int = 100


class JobPublishResponse(BaseModel):
    """Response after publishing a job vacancy."""
    success: bool
    job_id: str
    job_title: str
    status: str
    sourcing_results: Dict[str, Any]
    message: str


class ConfirmGlobalSearchRequest(BaseModel):
    """Request to confirm global search."""
    credits_to_use: int = 20


class ConfirmGlobalSearchResponse(BaseModel):
    """Response after confirming global search."""
    success: bool
    candidates_found: int
    candidates_added: int
    credits_deducted: int
    message: str
    error: Optional[str] = None


class SourcingStatusResponse(BaseModel):
    """Response for sourcing status."""
    found: bool
    job_id: Optional[str] = None
    job_title: Optional[str] = None
    total_candidates: int = 0
    qualified_candidates: int = 0
    qualified_ratio: float = 0.0
    needs_more_candidates: bool = False
    days_open: int = 0
    pipeline_status: str = "idle"
    recommended_action: Optional[str] = None
    min_candidates_target: int = 10
    error: Optional[str] = None


@router.post("/jobs/{job_id}/publish", response_model=JobPublishResponse)
async def publish_job_vacancy(
    job_id: UUID,
    request: JobPublishRequest = JobPublishRequest(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Publish a job vacancy and trigger initial sourcing pipeline.
    
    This endpoint:
    1. Changes job status to "Ativa"
    2. Triggers local sourcing pipeline
    3. Optionally triggers global search if expand_to_global is True
    4. Creates Teams notification for recruiter approval
    5. Returns initial sourcing results
    
    Multi-tenant: Only allows publish if user has access to vacancy's company.
    """
    try:
        logger.info(f"📢 Publishing job vacancy: {job_id}")
        
        user_company = get_user_company_id(current_user)
        
        query = select(JobVacancy).where(
            JobVacancy.id == job_id,
            JobVacancy.company_id == user_company
        )
        
        result = await db.execute(query)
        job_vacancy = result.scalar_one_or_none()
        
        if not job_vacancy:
            raise HTTPException(status_code=404, detail="Job vacancy not found")
        
        old_status = job_vacancy.status
        job_vacancy.status = "Ativa"
        job_vacancy.open_date = datetime.utcnow()
        job_vacancy.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(job_vacancy)
        
        logger.info(f"✅ Job vacancy status changed: {job_id} ({old_status} → Ativa)")
        
        try:
            await job_status_webhook_service.dispatch_status_change(
                job_id=str(job_id),
                old_status=old_status,
                new_status="Ativa",
                company_id=user_company,
                db=db,
                changed_by=str(current_user.email) if hasattr(current_user, 'email') else str(current_user.id),
                job_title=job_vacancy.title
            )
        except Exception as webhook_error:
            logger.warning(f"Webhook dispatch failed (non-blocking): {webhook_error}")
        
        sourcing_results = await sourcing_pipeline_service.run_post_publish_sourcing(
            db=db,
            job_id=str(job_id),
            user_credits=request.user_credits,
            expand_to_global=request.expand_to_global
        )
        
        total_added = sourcing_results.get("total_candidates_added", 0)
        if total_added > 0:
            await _send_candidates_added_notification(
                db=db,
                user_id=str(current_user.id),
                job_id=str(job_id),
                job_title=job_vacancy.title,
                candidates_added=total_added,
                recruiter_email=job_vacancy.recruiter_email or current_user.email
            )
        
        message = f"Vaga '{job_vacancy.title}' publicada com sucesso!"
        if total_added > 0:
            message += f" LIA adicionou {total_added} candidatos ao pipeline."
        
        if sourcing_results.get("awaiting_global_confirmation"):
            message += " Busca global disponível para expandir o pipeline."
        
        return JobPublishResponse(
            success=True,
            job_id=str(job_id),
            job_title=job_vacancy.title,
            status="Ativa",
            sourcing_results=sourcing_results,
            message=message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error publishing job vacancy: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs/{job_id}/confirm-global-search", response_model=ConfirmGlobalSearchResponse)
async def confirm_global_search(
    job_id: UUID,
    request: ConfirmGlobalSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Confirm global search expansion for a job vacancy.
    
    This endpoint:
    1. Triggers global search via Pearch AI
    2. Adds found candidates to the job pipeline
    3. Deducts credits from user account
    4. Returns global search results
    
    Multi-tenant: Only allows confirm if user has access to vacancy's company.
    """
    try:
        logger.info(f"🌍 Confirming global search for job: {job_id}")
        
        user_company = get_user_company_id(current_user)
        
        query = select(JobVacancy).where(
            JobVacancy.id == job_id,
            JobVacancy.company_id == user_company
        )
        
        result = await db.execute(query)
        job_vacancy = result.scalar_one_or_none()
        
        if not job_vacancy:
            raise HTTPException(status_code=404, detail="Job vacancy not found")
        
        if job_vacancy.status != "Ativa":
            raise HTTPException(
                status_code=400, 
                detail="Job vacancy must be published (status 'Ativa') before global search"
            )
        
        search_result = await sourcing_pipeline_service.confirm_global_search(
            db=db,
            job_id=str(job_id),
            user_id=str(current_user.id),
            credits_to_use=request.credits_to_use
        )
        
        if search_result.get("success") and search_result.get("candidates_added", 0) > 0:
            await _send_candidates_added_notification(
                db=db,
                user_id=str(current_user.id),
                job_id=str(job_id),
                job_title=job_vacancy.title,
                candidates_added=search_result["candidates_added"],
                recruiter_email=job_vacancy.recruiter_email or current_user.email,
                is_global=True
            )
        
        message = ""
        if search_result.get("success"):
            message = f"Busca global concluída! {search_result['candidates_added']} candidatos adicionados ao pipeline."
        else:
            message = f"Busca global falhou: {search_result.get('error', 'Unknown error')}"
        
        return ConfirmGlobalSearchResponse(
            success=search_result.get("success", False),
            candidates_found=search_result.get("candidates_found", 0),
            candidates_added=search_result.get("candidates_added", 0),
            credits_deducted=search_result.get("credits_deducted", 0),
            message=message,
            error=search_result.get("error")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error confirming global search: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}/sourcing-status", response_model=SourcingStatusResponse)
async def get_sourcing_status(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """
    Get current sourcing progress and candidates found for a job.
    
    Returns:
    - Total candidates in pipeline
    - Qualified candidates
    - Pipeline status (healthy, needs_attention, low, critical)
    - Recommended action
    
    Multi-tenant: Only returns status if user has access to vacancy's company.
    """
    try:
        logger.info(f"📊 Getting sourcing status for job: {job_id}")
        
        user_company = get_user_company_id(current_user)
        
        query = select(JobVacancy).where(
            JobVacancy.id == job_id,
            JobVacancy.company_id == user_company
        )
        
        result = await db.execute(query)
        job_vacancy = result.scalar_one_or_none()
        
        if not job_vacancy:
            raise HTTPException(status_code=404, detail="Job vacancy not found")
        
        status = await sourcing_pipeline_service.get_sourcing_status(
            db=db,
            job_id=str(job_id)
        )
        
        if not status.get("found"):
            return SourcingStatusResponse(
                found=False,
                error=status.get("error", "Job not found in pipeline")
            )
        
        return SourcingStatusResponse(
            found=True,
            job_id=status.get("job_id"),
            job_title=status.get("job_title"),
            total_candidates=status.get("total_candidates", 0),
            qualified_candidates=status.get("qualified_candidates", 0),
            qualified_ratio=status.get("qualified_ratio", 0.0),
            needs_more_candidates=status.get("needs_more_candidates", False),
            days_open=status.get("days_open", 0),
            pipeline_status=status.get("pipeline_status", "idle"),
            recommended_action=status.get("recommended_action"),
            min_candidates_target=status.get("min_candidates_target", 10)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting sourcing status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def _send_candidates_added_notification(
    db: AsyncSession,
    user_id: str,
    job_id: str,
    job_title: str,
    candidates_added: int,
    recruiter_email: str,
    is_global: bool = False
) -> None:
    """
    Send notification when candidates are added to pipeline.
    Creates both in-app notification and Teams notification.
    """
    try:
        source_type = "busca global" if is_global else "busca local"
        
        notification_message = f"LIA adicionou {candidates_added} candidatos ao pipeline de {job_title}. Aprove para iniciar triagem."
        
        await notification_service.create_notification(
            user_id=user_id,
            title=f"Candidatos adicionados - {job_title}",
            message=notification_message,
            notification_type=NotificationType.ACTION_REQUIRED,
            category="sourcing",
            source_agent="sourcing_pipeline",
            source_trigger="job_publish",
            related_job_id=job_id,
            action_url=f"/jobs/{job_id}",
            action_label="Ver Pipeline",
            channels=[NotificationChannel.IN_APP.value, NotificationChannel.TEAMS.value, NotificationChannel.EMAIL.value],
            metadata={
                "candidates_added": candidates_added,
                "source_type": source_type,
                "job_title": job_title,
                "recipient_email": recruiter_email,
                "action_url": f"/jobs/{job_id}"
            },
            db=db
        )
        
        teams_message = (
            f"🎯 **Candidatos Adicionados**\n\n"
            f"LIA adicionou **{candidates_added} candidatos** ao pipeline de **{job_title}** via {source_type}.\n\n"
            f"👉 Aprove para iniciar triagem."
        )
        
        await teams_service.send_message(
            text=teams_message,
            title=f"Pipeline Atualizado - {job_title}"
        )
        
        logger.info(f"📬 Notification sent: {candidates_added} candidates added to {job_title}")
        
    except Exception as e:
        logger.warning(f"Failed to send notification: {e}")


# =============================================
# JOB CLONING / DUPLICATION ENDPOINTS
# =============================================

class DuplicateJobRequest(BaseModel):
    """Request schema for duplicating a job vacancy."""
    copies: int = Field(default=1, ge=1, le=10, description="Number of copies to create")
    include_candidates: bool = Field(default=True, description="Whether to include candidates")
    candidate_filter: Optional[str] = Field(default=None, description="Filter candidates: 'all', 'approved', or None")
    candidate_status_override: Optional[str] = Field(default=None, description="Override status for all candidates")
    overrides: Optional[Dict[str, Any]] = Field(default=None, description="Fields to override in cloned jobs")


class CloneFromTemplateRequest(BaseModel):
    """Request schema for creating a job from template."""
    new_title: Optional[str] = Field(default=None, description="Title for the new job")
    overrides: Optional[Dict[str, Any]] = Field(default=None, description="Fields to override")


class FindJobRequest(BaseModel):
    """Request schema for finding a job by ID or title."""
    identifier: str = Field(..., description="Job ID, job_id code, or title to search for")


@router.post("/job-vacancies/{job_id}/duplicate")
async def duplicate_job(
    job_id: UUID,
    request: DuplicateJobRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """
    Duplicate a job vacancy with all its data.
    
    Creates one or more copies of the job, optionally including candidates.
    """
    from app.services.job_clone_service import job_clone_service
    
    company_id = get_user_company_id(current_user)
    
    try:
        logger.info(f"📋 Duplicating job {job_id} with {request.copies} copies, candidates: {request.include_candidates}, filter: {request.candidate_filter}")
        
        result = await job_clone_service.duplicate_job(
            db=db,
            source_job_id=job_id,
            copies=request.copies,
            include_candidates=request.include_candidates,
            candidate_filter=request.candidate_filter,
            candidate_status_override=request.candidate_status_override,
            overrides=request.overrides,
            created_by=current_user.email if hasattr(current_user, 'email') else "demo@wedotalent.com",
            company_id=company_id
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error", "Failed to duplicate job"))
        
        logger.info(f"✅ Created {result['total_jobs_created']} duplicate jobs from {job_id}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error duplicating job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/job-vacancies/{job_id}/clone-from-template")
async def clone_from_template(
    job_id: UUID,
    request: CloneFromTemplateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """
    Create a new job using an existing job as a template.
    
    Does NOT clone candidates - only job data (description, requirements, etc).
    """
    from app.services.job_clone_service import job_clone_service
    
    company_id = get_user_company_id(current_user)
    
    try:
        logger.info(f"📄 Creating job from template {job_id}")
        
        result = await job_clone_service.clone_from_template(
            db=db,
            source_job_id=job_id,
            new_title=request.new_title,
            overrides=request.overrides,
            created_by=current_user.email if hasattr(current_user, 'email') else "demo@wedotalent.com",
            company_id=company_id
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error", "Failed to create from template"))
        
        logger.info(f"✅ Created job from template: {result['created_job']['title']}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating from template: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/job-vacancies/find-by-identifier", response_model=None)
async def find_job_by_identifier(
    request: FindJobRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """
    Find a job by ID, job_id code, or title.
    
    Used by LIA to find jobs when user provides partial information.
    """
    from app.services.job_clone_service import job_clone_service
    
    company_id = get_user_company_id(current_user)
    
    try:
        job = await job_clone_service.get_job_by_id_or_title(
            db=db,
            identifier=request.identifier,
            company_id=company_id
        )
        
        if not job:
            raise HTTPException(status_code=404, detail=f"Vaga não encontrada: {request.identifier}")
        
        summary = await job_clone_service.get_job_summary_for_clone(db, job.id)
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error finding job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/job-vacancies/{job_id}/clone-summary")
async def get_clone_summary(
    job_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a summary of a job for displaying before cloning.
    
    Returns job details and candidate breakdown for preview.
    """
    from app.services.job_clone_service import job_clone_service
    
    try:
        summary = await job_clone_service.get_job_summary_for_clone(db, job_id)
        
        if not summary:
            raise HTTPException(status_code=404, detail=f"Vaga não encontrada: {job_id}")
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting clone summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def derive_screening_status(screening_config: dict) -> str:
    """Derive the screening status from screening_config data."""
    if not screening_config:
        return "not_configured"
    
    status = screening_config.get("status", {})
    
    explicit = status.get("screening_status")
    if explicit:
        return explicit
    
    if status.get("completed_at"):
        return "completed"
    if status.get("paused_at"):
        return "paused"
    if status.get("enabled", False):
        return "active"
    
    has_config = bool(screening_config.get("wsi_skills")) or bool(screening_config.get("settings"))
    if has_config:
        return "not_started"
    
    return "not_configured"


# =============================================
# SCREENING CONFIG ENDPOINTS
# =============================================

class ScreeningConfigStatus(BaseModel):
    """Status of screening automation."""
    enabled: bool = True
    paused_at: Optional[str] = None
    paused_by: Optional[str] = None
    pause_reason: Optional[str] = None
    scheduled_end_date: Optional[str] = None
    last_updated: Optional[str] = None
    screening_status: Optional[str] = "not_configured"  # not_configured, not_started, active, paused, completed

class ScreeningConfigChannel(BaseModel):
    """Configuration for a communication channel."""
    enabled: bool = True
    label: Optional[str] = None

class ScreeningConfigChannels(BaseModel):
    """All communication channels."""
    whatsapp: Optional[ScreeningConfigChannel] = None
    chat_web: Optional[ScreeningConfigChannel] = None
    phone: Optional[ScreeningConfigChannel] = None

class ScreeningConfigSettings(BaseModel):
    """Screening settings."""
    min_score: Optional[int] = 70
    response_timeout_hours: Optional[int] = 48
    max_retries: Optional[int] = 2

class ScreeningConfigMetrics(BaseModel):
    """Screening metrics."""
    screened_count: Optional[int] = 0
    completion_rate: Optional[float] = 0
    average_rating: Optional[float] = 4.2

class ScreeningConfigScheduling(BaseModel):
    """Auto-scheduling configuration."""
    auto_enabled: Optional[bool] = True
    min_score_for_auto: Optional[int] = 75
    calendar_provider: Optional[str] = "Microsoft"
    available_hours: Optional[str] = "9h-18h"
    interview_duration_min: Optional[int] = 45

class ScreeningConfigFeedback(BaseModel):
    """Feedback templates."""
    approved: Optional[str] = "Parabéns! Você foi aprovado na triagem inicial."
    rejected: Optional[str] = "Agradecemos sua participação. Infelizmente não seguiremos com sua candidatura neste momento."

class ScreeningConfigRequest(BaseModel):
    """Full screening configuration schema."""
    status: Optional[ScreeningConfigStatus] = None
    channels: Optional[ScreeningConfigChannels] = None
    settings: Optional[ScreeningConfigSettings] = None
    metrics: Optional[ScreeningConfigMetrics] = None
    scheduling: Optional[ScreeningConfigScheduling] = None
    feedback_templates: Optional[ScreeningConfigFeedback] = None
    wsi_skills: Optional[List[str]] = []

class ScreeningConfigResponse(BaseModel):
    """Response for screening config."""
    job_id: str
    is_default: bool = False
    screening_status: Optional[str] = "not_configured"
    status: Optional[Dict[str, Any]] = None
    channels: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, Any]] = None
    scheduling: Optional[Dict[str, Any]] = None
    feedback_templates: Optional[Dict[str, Any]] = None
    wsi_skills: Optional[List[str]] = []
    updated_at: Optional[str] = None


@router.get("/vagas/{job_id}/screening-config", response_model=ScreeningConfigResponse)
async def get_screening_config(
    job_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get screening configuration for a job vacancy.
    
    Returns the screening settings including channels, thresholds, 
    metrics, and auto-scheduling configuration.
    """
    try:
        result = await db.execute(
            select(JobVacancy).where(JobVacancy.id == job_id)
        )
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(status_code=404, detail=f"Vaga não encontrada: {job_id}")
        
        config = job.screening_config or {}
        
        screening_status = derive_screening_status(config)
        
        return ScreeningConfigResponse(
            job_id=str(job_id),
            is_default=not bool(config),
            screening_status=screening_status,
            status=config.get("status", {"enabled": True, "last_updated": None}),
            channels=config.get("channels", {
                "whatsapp": {"enabled": True, "label": "WhatsApp"},
                "chat_web": {"enabled": True, "label": "Chat Web"},
                "phone": {"enabled": False, "label": "Ligação"}
            }),
            settings=config.get("settings", {"min_score": 70, "response_timeout_hours": 48, "max_retries": 2}),
            metrics=config.get("metrics", {"screened_count": 0, "completion_rate": 0, "average_rating": 4.2}),
            scheduling=config.get("scheduling", {
                "auto_enabled": True,
                "min_score_for_auto": 75,
                "calendar_provider": "Microsoft",
                "available_hours": "9h-18h",
                "interview_duration_min": 45
            }),
            feedback_templates=config.get("feedback_templates", {
                "approved": "Parabéns! Você foi aprovado na triagem inicial.",
                "rejected": "Agradecemos sua participação. Infelizmente não seguiremos com sua candidatura neste momento."
            }),
            wsi_skills=config.get("wsi_skills", []),
            updated_at=config.get("status", {}).get("last_updated")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting screening config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/vagas/{job_id}/screening-config", response_model=ScreeningConfigResponse)
async def update_screening_config(
    job_id: UUID,
    config_data: ScreeningConfigRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """
    Update screening configuration for a job vacancy.
    
    Allows updating channels, settings, scheduling, and other screening parameters.
    """
    try:
        result = await db.execute(
            select(JobVacancy).where(JobVacancy.id == job_id)
        )
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(status_code=404, detail=f"Vaga não encontrada: {job_id}")
        
        # Build new config from request
        new_config = {}
        
        if config_data.status:
            new_config["status"] = config_data.status.model_dump(exclude_none=True)
            new_config["status"]["last_updated"] = datetime.utcnow().isoformat()
        
        if config_data.channels:
            new_config["channels"] = config_data.channels.model_dump(exclude_none=True)
        
        if config_data.settings:
            new_config["settings"] = config_data.settings.model_dump(exclude_none=True)
        
        if config_data.metrics:
            new_config["metrics"] = config_data.metrics.model_dump(exclude_none=True)
        
        if config_data.scheduling:
            new_config["scheduling"] = config_data.scheduling.model_dump(exclude_none=True)
        
        if config_data.feedback_templates:
            new_config["feedback_templates"] = config_data.feedback_templates.model_dump(exclude_none=True)
        
        if config_data.wsi_skills:
            new_config["wsi_skills"] = config_data.wsi_skills
        
        # Merge with existing config
        existing_config = job.screening_config or {}
        merged_config = {**existing_config, **new_config}
        
        # Update job
        job.screening_config = merged_config
        job.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(job)
        
        logger.info(f"✅ Screening config updated for job {job_id}")
        
        return ScreeningConfigResponse(
            job_id=str(job_id),
            is_default=False,
            status=merged_config.get("status"),
            channels=merged_config.get("channels"),
            settings=merged_config.get("settings"),
            metrics=merged_config.get("metrics"),
            scheduling=merged_config.get("scheduling"),
            feedback_templates=merged_config.get("feedback_templates"),
            wsi_skills=merged_config.get("wsi_skills", []),
            updated_at=merged_config.get("status", {}).get("last_updated")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating screening config: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


class ScreeningStatusUpdateRequest(BaseModel):
    """Request to update screening status."""
    screening_status: str  # not_configured, not_started, active, paused, completed
    pause_reason: Optional[str] = None
    scheduled_end_date: Optional[str] = None

VALID_SCREENING_STATUSES = {"not_configured", "not_started", "active", "paused", "completed"}

@router.put("/vagas/{job_id}/screening-status")
async def update_screening_status(
    job_id: UUID,
    request: ScreeningStatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """Update the screening status for a job vacancy."""
    if request.screening_status not in VALID_SCREENING_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid screening status: {request.screening_status}. Valid: {VALID_SCREENING_STATUSES}")
    
    try:
        result = await db.execute(select(JobVacancy).where(JobVacancy.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail=f"Vaga não encontrada: {job_id}")
        
        existing_config = job.screening_config or {}
        existing_status = existing_config.get("status", {})
        
        now = datetime.utcnow().isoformat()
        
        existing_status["screening_status"] = request.screening_status
        existing_status["last_updated"] = now
        
        if request.screening_status == "active":
            existing_status["enabled"] = True
            existing_status["paused_at"] = None
            existing_status["paused_by"] = None
            existing_status["pause_reason"] = None
            if not existing_status.get("activated_at"):
                existing_status["activated_at"] = now
        elif request.screening_status == "paused":
            existing_status["enabled"] = False
            existing_status["paused_at"] = now
            existing_status["paused_by"] = current_user.email if hasattr(current_user, 'email') else "system"
            existing_status["pause_reason"] = request.pause_reason or "Pausado manualmente"
        elif request.screening_status == "completed":
            existing_status["enabled"] = False
            existing_status["completed_at"] = now
        elif request.screening_status == "not_started":
            existing_status["enabled"] = False
            existing_status["paused_at"] = None
        
        if request.scheduled_end_date:
            existing_status["scheduled_end_date"] = request.scheduled_end_date
        
        existing_config["status"] = existing_status
        job.screening_config = existing_config
        job.updated_at = datetime.utcnow()
        
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(job, "screening_config")
        
        await db.commit()
        await db.refresh(job)
        
        logger.info(f"✅ Screening status updated to '{request.screening_status}' for job {job_id}")
        
        return {
            "job_id": str(job_id),
            "screening_status": request.screening_status,
            "status": existing_config.get("status"),
            "updated_at": now
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating screening status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================
# PUBLIC SHARING ENDPOINTS
# =============================================

import secrets
import re


def generate_slug(title: str, company_name: str = "") -> str:
    """Generate a URL-friendly slug from title and company name."""
    base = f"{title}-{company_name}" if company_name else title
    base = base.lower()
    base = re.sub(r'[àáâãäå]', 'a', base)
    base = re.sub(r'[èéêë]', 'e', base)
    base = re.sub(r'[ìíîï]', 'i', base)
    base = re.sub(r'[òóôõö]', 'o', base)
    base = re.sub(r'[ùúûü]', 'u', base)
    base = re.sub(r'[ç]', 'c', base)
    base = re.sub(r'[ñ]', 'n', base)
    base = re.sub(r'[^a-z0-9]+', '-', base)
    base = base.strip('-')
    random_suffix = secrets.token_hex(3)
    return f"{base}-{random_suffix}"[:100]


class GeneratePublicLinkRequest(BaseModel):
    """Request to generate public link."""
    regenerate: bool = False


class GeneratePublicLinkResponse(BaseModel):
    """Response with public link details."""
    success: bool
    public_url: str
    slug: str
    message: str


class ShareLinkResponse(BaseModel):
    """Response with shareable link details for job vacancy."""
    share_link: str
    slug: str
    qr_code_url: Optional[str] = None
    expires_at: Optional[str] = None
    view_count: int = 0


class PublicVacancyResponse(BaseModel):
    """Public vacancy data (no sensitive information)."""
    title: str
    description: Optional[str] = None
    requirements: Optional[List[str]] = []
    benefits: Optional[List[str]] = []
    location: Optional[str] = None
    work_model: Optional[str] = None
    employment_type: Optional[str] = None
    seniority_level: Optional[str] = None
    department: Optional[str] = None
    company_name: Optional[str] = None
    company_description: Optional[str] = None
    company_website: Optional[str] = None
    company_logo: Optional[str] = None
    is_confidential: bool = False
    is_affirmative: bool = False
    technical_requirements: Optional[List[dict]] = []
    languages: Optional[List[dict]] = []
    behavioral_competencies: Optional[List[dict]] = []
    salary_range: Optional[dict] = None
    apply_url: Optional[str] = None


@router.post("/job-vacancies/{vacancy_id}/generate-public-link", response_model=GeneratePublicLinkResponse)
async def generate_public_link(
    vacancy_id: UUID,
    request: GeneratePublicLinkRequest = GeneratePublicLinkRequest(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """
    Generate or retrieve public sharing link for a job vacancy.
    
    This endpoint creates a unique URL-friendly slug that can be used
    to share the job publicly without authentication.
    
    Multi-tenant: Only allows generating links for vacancies in user's company.
    """
    try:
        company_id = get_user_company_id(current_user)
        
        result = await db.execute(
            select(JobVacancy).where(
                and_(JobVacancy.id == vacancy_id, JobVacancy.company_id == company_id)
            )
        )
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(status_code=404, detail="Vaga não encontrada")
        
        if job.visibility == "hidden":
            raise HTTPException(status_code=403, detail="Vagas ocultas não podem ter link público")
        
        if job.public_slug and not request.regenerate:
            return GeneratePublicLinkResponse(
                success=True,
                public_url=f"/vagas/{job.public_slug}",
                slug=job.public_slug,
                message="Link público existente"
            )
        
        company_short = ""
        if job.masked_company_name:
            company_short = job.masked_company_name[:30]
        
        new_slug = generate_slug(job.title, company_short)
        
        existing = await db.execute(
            select(JobVacancy.id).where(JobVacancy.public_slug == new_slug)
        )
        if existing.scalar_one_or_none():
            new_slug = generate_slug(job.title, secrets.token_hex(2))
        
        job.public_slug = new_slug
        job.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(job)
        
        logger.info(f"✅ Generated public link for job {vacancy_id}: /vagas/{new_slug}")
        
        return GeneratePublicLinkResponse(
            success=True,
            public_url=f"/vagas/{new_slug}",
            slug=new_slug,
            message="Link público gerado com sucesso"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error generating public link: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/job-vacancies/{vacancy_id}/share-link", response_model=ShareLinkResponse)
async def get_share_link(
    vacancy_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """
    Get shareable link details for a job vacancy.
    
    Returns structured information about the public sharing link including:
    - share_link: Full URL for sharing (https://app.wedotalent.com/jobs/{slug})
    - slug: The URL-friendly identifier
    - qr_code_url: Endpoint to generate QR code (optional)
    - expires_at: Expiration date if temporary (null for permanent links)
    - view_count: Number of times the public page has been viewed
    
    If no public slug exists, one will be generated automatically.
    Multi-tenant: Only returns data for vacancies in user's company.
    """
    try:
        company_id = get_user_company_id(current_user)
        
        result = await db.execute(
            select(JobVacancy).where(
                and_(JobVacancy.id == vacancy_id, JobVacancy.company_id == company_id)
            )
        )
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(status_code=404, detail="Vaga não encontrada")
        
        if job.visibility == "hidden":
            raise HTTPException(status_code=403, detail="Vagas ocultas não podem ter link público")
        
        if not job.public_slug:
            company_short = ""
            if job.masked_company_name:
                company_short = job.masked_company_name[:30]
            
            new_slug = generate_slug(job.title, company_short)
            
            existing = await db.execute(
                select(JobVacancy.id).where(JobVacancy.public_slug == new_slug)
            )
            if existing.scalar_one_or_none():
                new_slug = generate_slug(job.title, secrets.token_hex(2))
            
            job.public_slug = new_slug
            job.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(job)
            logger.info(f"✅ Generated public slug for job {vacancy_id}: {new_slug}")
        
        share_link = f"https://app.wedotalent.com/jobs/{job.public_slug}"
        qr_code_url = f"/api/v1/job-vacancies/{vacancy_id}/qr-code"
        
        return ShareLinkResponse(
            share_link=share_link,
            slug=job.public_slug,
            qr_code_url=qr_code_url,
            expires_at=None,
            view_count=job.view_count or 0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting share link: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================
# PUBLIC ROUTER (NO AUTHENTICATION)
# =============================================

router_public = APIRouter()


@router_public.get("/p/{slug}", response_model=PublicVacancyResponse)
async def get_public_vacancy(
    slug: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get public vacancy information by slug.
    
    This endpoint is PUBLIC and does not require authentication.
    Returns only non-sensitive job information suitable for external sharing.
    Increments view counter on each access.
    
    Does NOT expose:
    - salary_range if confidential
    - access_list
    - internal workflow data
    - recruiter/manager contact details
    """
    try:
        result = await db.execute(
            select(JobVacancy).where(JobVacancy.public_slug == slug)
        )
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(status_code=404, detail="Vaga não encontrada")
        
        if job.visibility == "hidden" or job.status not in ["Ativa", "Publicada"]:
            raise HTTPException(status_code=404, detail="Vaga não disponível")
        
        job.view_count = (job.view_count or 0) + 1
        await db.commit()
        
        is_confidential = job.is_confidential or job.visibility == "confidential"
        
        company_name = None
        company_description = None
        company_website = None
        company_logo = None
        
        if not is_confidential:
            if job.masked_company_name:
                company_name = job.masked_company_name
        
        tech_reqs = []
        if job.technical_requirements:
            for tr in job.technical_requirements:
                tech_reqs.append({
                    "technology": tr.get("technology"),
                    "level": tr.get("level"),
                    "category": tr.get("category"),
                    "required": tr.get("required", False)
                })
        
        languages = []
        if job.languages:
            for lang in job.languages:
                languages.append({
                    "language": lang.get("language"),
                    "level": lang.get("level"),
                    "required": lang.get("required", False)
                })
        
        competencies = []
        if job.behavioral_competencies:
            for comp in job.behavioral_competencies:
                competencies.append({
                    "competency": comp.get("competency"),
                    "weight": comp.get("weight")
                })
        
        salary_range = None
        if not is_confidential and job.salary_range:
            salary_range = job.salary_range
        
        apply_url = f"https://app.wedotalent.com/vagas/{slug}/apply"
        
        logger.info(f"📖 Public vacancy accessed: {slug} (views: {job.view_count})")
        
        return PublicVacancyResponse(
            title=job.title,
            description=job.description,
            requirements=job.requirements or [],
            benefits=job.benefits or [],
            location=job.location,
            work_model=job.work_model,
            employment_type=job.employment_type,
            seniority_level=job.seniority_level,
            department=job.department,
            company_name=company_name,
            company_description=company_description,
            company_website=company_website,
            company_logo=company_logo,
            is_confidential=is_confidential,
            is_affirmative=job.is_affirmative,
            technical_requirements=tech_reqs,
            languages=languages,
            behavioral_competencies=competencies,
            salary_range=salary_range,
            apply_url=apply_url
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching public vacancy: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


class PublicApplicationResponse(BaseModel):
    status: str
    message: str
    candidate_id: Optional[str] = None
    adherence_score: Optional[float] = None
    next_step: Optional[str] = None


SATURATION_EXCLUDED_STATUSES = ('rejected', 'declined', 'withdrawn')
ADHERENCE_THRESHOLD = 55.0


@router_public.post("/p/{slug}/apply", response_model=PublicApplicationResponse)
async def apply_to_public_vacancy(
    slug: str,
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    lgpd_consent: str = Form(...),
    cv_file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    try:
        if lgpd_consent.lower() not in ("true", "1", "yes", "sim"):
            raise HTTPException(
                status_code=400,
                detail="Consentimento LGPD obrigatório para prosseguir."
            )

        result = await db.execute(
            select(JobVacancy).where(JobVacancy.public_slug == slug)
        )
        job = result.scalar_one_or_none()

        if not job:
            raise HTTPException(status_code=404, detail="Vaga não encontrada")

        if job.visibility == "hidden" or job.status not in ["Ativa", "Publicada", "open", "active", "published"]:
            raise HTTPException(status_code=400, detail="Esta vaga não está aberta para candidaturas")

        cv_content = await cv_file.read()
        parsed_cv = {}
        try:
            from app.services.cv_parser import cv_parser_service
            parsed_cv = await cv_parser_service.parse_cv(
                file_content=cv_content,
                filename=cv_file.filename
            )
        except Exception as e:
            logger.warning(f"CV parsing failed, continuing without parsed data: {e}")

        result = await db.execute(
            select(Candidate).where(Candidate.email == email)
        )
        existing_candidate = result.scalar_one_or_none()

        if existing_candidate:
            candidate = existing_candidate
            candidate.name = name
            candidate.phone = phone or candidate.phone
            candidate.mobile_phone = phone or candidate.mobile_phone
            if parsed_cv.get("skills"):
                existing_skills = candidate.technical_skills or []
                candidate.technical_skills = list(set(existing_skills + parsed_cv.get("skills", [])))
            if parsed_cv.get("experience_years") and not candidate.years_of_experience:
                candidate.years_of_experience = parsed_cv.get("experience_years")
            if parsed_cv.get("current_title") and not candidate.current_title:
                candidate.current_title = parsed_cv.get("current_title")
            candidate.communication_consent = True
            candidate.updated_at = datetime.utcnow()
        else:
            candidate = Candidate(
                id=uuid_lib.uuid4(),
                name=name,
                email=email,
                phone=phone,
                mobile_phone=phone,
                source="web_application",
                status="new",
                technical_skills=parsed_cv.get("skills", []),
                years_of_experience=parsed_cv.get("experience_years"),
                current_title=parsed_cv.get("current_title"),
                current_company=parsed_cv.get("current_company"),
                communication_consent=True
            )
            db.add(candidate)

        await db.flush()

        adherence_score = 70.0
        try:
            from app.services.lia_score_service import LIAScoreService
            lia_svc = LIAScoreService()
            vacancy_requirements = {
                "query": job.title or "",
                "skills": job.required_skills or [],
                "experience_years": getattr(job, "min_experience_years", None),
                "seniority": job.seniority_level,
                "location": getattr(job, "location_city", None) or job.location
            }
            candidate_profile = {
                "skills": candidate.technical_skills or [],
                "experience_years": candidate.years_of_experience,
                "current_title": candidate.current_title,
                "location": candidate.location_city,
                "seniority": candidate.seniority_level
            }
            score_result = lia_svc.calculate_score(
                candidate=candidate_profile,
                search_criteria=vacancy_requirements
            )
            adherence_score = score_result.score
            candidate.lia_score = adherence_score
            candidate.skills_match_percentage = score_result.breakdown.skills_match
            candidate.lia_insights = score_result.to_dict()
        except Exception as e:
            logger.warning(f"Score calculation failed, using default: {e}")

        if adherence_score < ADHERENCE_THRESHOLD:
            await db.commit()
            return PublicApplicationResponse(
                status="low_adherence",
                message="Obrigado pela candidatura! Infelizmente seu perfil não atende aos requisitos mínimos desta vaga no momento. Recomendamos atualizar seu currículo e tentar novamente.",
                candidate_id=str(candidate.id),
                adherence_score=adherence_score,
                next_step="improve_profile"
            )

        existing_vc = await db.execute(
            select(VacancyCandidate).where(
                VacancyCandidate.vacancy_id == job.id,
                VacancyCandidate.candidate_id == candidate.id
            )
        )
        if existing_vc.scalar_one_or_none():
            await db.commit()
            return PublicApplicationResponse(
                status="already_applied",
                message="Você já se candidatou a esta vaga. Acompanhe seu email para atualizações.",
                candidate_id=str(candidate.id),
                adherence_score=adherence_score,
                next_step="wait_for_contact"
            )

        is_saturated = False
        try:
            company = None
            if job.company_id:
                cr = await db.execute(
                    select(CompanyProfile).where(CompanyProfile.id == job.company_id)
                )
                company = cr.scalar_one_or_none()

            threshold_web = 20
            if company and company.additional_data:
                sat_settings = company.additional_data.get("saturation_settings", {})
                threshold_web = sat_settings.get("threshold_web", 20)

            governance = job.governance_rules or {}
            threshold_web = governance.get("threshold_web", threshold_web)

            active_filter = and_(
                VacancyCandidate.vacancy_id == job.id,
                not_(VacancyCandidate.status.in_(SATURATION_EXCLUDED_STATUSES)),
                VacancyCandidate.origin.in_(("web", "whatsapp"))
            )
            count_result = await db.execute(
                select(func.count(VacancyCandidate.id)).where(active_filter)
            )
            organic_count = count_result.scalar() or 0
            is_saturated = organic_count >= threshold_web
        except Exception as e:
            logger.warning(f"Saturation check failed, allowing application: {e}")

        candidate_status = "awaiting_screening" if is_saturated else "applied"

        import secrets as _secrets
        screening_token = _secrets.token_urlsafe(32)

        vacancy_candidate = VacancyCandidate(
            id=uuid_lib.uuid4(),
            vacancy_id=job.id,
            candidate_id=candidate.id,
            company_id=str(job.company_id) if job.company_id else "default",
            source="web_application",
            origin="web",
            lia_score=adherence_score,
            match_percentage=candidate.skills_match_percentage,
            status=candidate_status,
            stage="pending_gate1",
            additional_data={
                "screening_invite_token": screening_token,
                "applied_at": datetime.utcnow().isoformat(),
                "is_saturated_at_apply": is_saturated,
            },
        )
        db.add(vacancy_candidate)

        try:
            await notification_service.create_notification(
                user_id="default_user",
                title="Nova candidatura via formulário web",
                message=f"{name} aplicou para {job.title} com aderência de {adherence_score:.0f}%",
                notification_type=NotificationType.SUCCESS,
                category="new_application",
                related_job_id=str(job.id),
                related_candidate_id=str(candidate.id),
                action_url=f"/candidates/{candidate.id}",
                action_label="Ver Candidato",
                db=db
            )
        except Exception as e:
            logger.warning(f"Notification creation failed: {e}")

        await db.commit()

        if is_saturated:
            return PublicApplicationResponse(
                status="queued",
                message="Obrigado pela candidatura! Seus dados foram registrados. Entraremos em contato em breve quando houver disponibilidade para a próxima etapa.",
                candidate_id=str(candidate.id),
                adherence_score=adherence_score,
                next_step="wait_in_queue"
            )

        return PublicApplicationResponse(
            status="applied",
            message="Candidatura enviada com sucesso! Você receberá um convite para a próxima etapa em breve.",
            candidate_id=str(candidate.id),
            adherence_score=adherence_score,
            next_step="screening"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing public application: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro ao processar candidatura. Tente novamente.")


# =============================================
# JOB VACANCY EXPORT ENDPOINTS (PDF & Excel)
# =============================================

@router.get("/job-vacancies/{job_id}/export/pdf")
async def export_job_vacancy_pdf(
    job_id: UUID,
    report_type: str = Query("analytics", description="Report type: funnel, analytics, or candidates"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Export job vacancy report as PDF.
    
    Report types:
    - funnel: Funnel metrics report with conversion rates and source analysis
    - analytics: Full analytics report with all metrics and charts
    - candidates: List of all candidates with their details
    
    Multi-tenant: Only exports data for vacancies belonging to user's company.
    """
    try:
        company_id = get_user_company_id(current_user)
        
        if report_type == "funnel":
            buffer = await job_report_service.generate_funnel_report(
                job_id=job_id,
                company_id=company_id,
                format="pdf",
                db=db
            )
            filename = f"relatorio_funil_{job_id}.pdf"
        elif report_type == "candidates":
            buffer = await job_report_service.generate_candidate_list_export(
                job_id=job_id,
                company_id=company_id,
                format="pdf",
                db=db
            )
            filename = f"lista_candidatos_{job_id}.pdf"
        else:  # analytics (default)
            buffer = await job_report_service.generate_analytics_report(
                job_id=job_id,
                company_id=company_id,
                format="pdf",
                db=db
            )
            filename = f"relatorio_analitico_{job_id}.pdf"
        
        logger.info(f"📄 PDF report exported for job {job_id} by {current_user.email}")
        
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Error exporting PDF report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/job-vacancies/{job_id}/export/excel")
async def export_job_vacancy_excel(
    job_id: UUID,
    report_type: str = Query("analytics", description="Report type: funnel, analytics, or candidates"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Export job vacancy report as Excel file.
    
    Report types:
    - funnel: Funnel metrics with Summary, Funnel, and Sources sheets
    - analytics: Full analytics with Summary, Funnel, Candidates, and Sources sheets
    - candidates: Candidate list with full details
    
    Multi-tenant: Only exports data for vacancies belonging to user's company.
    """
    try:
        company_id = get_user_company_id(current_user)
        
        if report_type == "funnel":
            buffer = await job_report_service.generate_funnel_report(
                job_id=job_id,
                company_id=company_id,
                format="excel",
                db=db
            )
            filename = f"relatorio_funil_{job_id}.xlsx"
        elif report_type == "candidates":
            buffer = await job_report_service.generate_candidate_list_export(
                job_id=job_id,
                company_id=company_id,
                format="excel",
                db=db
            )
            filename = f"lista_candidatos_{job_id}.xlsx"
        else:  # analytics (default)
            buffer = await job_report_service.generate_analytics_report(
                job_id=job_id,
                company_id=company_id,
                format="excel",
                db=db
            )
            filename = f"relatorio_analitico_{job_id}.xlsx"
        
        logger.info(f"📊 Excel report exported for job {job_id} by {current_user.email}")
        
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Error exporting Excel report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================
# BULK OPERATIONS ENDPOINTS
# =============================================

@router.post("/job-vacancies/bulk/pause", response_model=BulkActionResponse)
async def bulk_pause_job_vacancies(
    request: BulkActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Pause multiple job vacancies.
    Changes status to 'Pausada' for all valid job IDs.
    Only jobs with status 'Ativa' can be paused.
    Multi-tenant: Only affects jobs from the user's company.
    """
    from app.services.job_audit_service import job_audit_service
    
    company_id = get_user_company_id(current_user)
    changed_by = str(current_user.email) if hasattr(current_user, 'email') else str(current_user.id)
    
    successful = 0
    failed = 0
    errors: List[BulkActionError] = []
    
    for job_id in request.job_ids:
        try:
            result = await db.execute(
                select(JobVacancy).where(
                    and_(JobVacancy.id == job_id, JobVacancy.company_id == company_id)
                )
            )
            job = result.scalar_one_or_none()
            
            if not job:
                errors.append(BulkActionError(job_id=str(job_id), error_message="Vaga não encontrada"))
                failed += 1
                continue
            
            if job.status != "Ativa":
                errors.append(BulkActionError(
                    job_id=str(job_id), 
                    error_message=f"Apenas vagas ativas podem ser pausadas. Status atual: {job.status}"
                ))
                failed += 1
                continue
            
            old_status = job.status
            job.status = "Pausada"
            job.updated_at = datetime.utcnow()
            
            await job_audit_service.log_status_change(
                job_id=str(job_id),
                old_status=old_status,
                new_status="Pausada",
                changed_by=changed_by,
                company_id=company_id,
                db=db,
                extra_data={"action": "bulk_pause"}
            )
            
            await job_status_webhook_service.dispatch_status_change(
                job_id=str(job_id),
                old_status=old_status,
                new_status="Pausada",
                company_id=company_id,
                db=db,
                changed_by=changed_by,
                job_title=job.title
            )
            
            try:
                from app.services.event_dispatcher import event_dispatcher
                await event_dispatcher.on_job_status_changed(
                    job_id=str(job_id),
                    company_id=company_id,
                    new_status="Pausada",
                    previous_status=old_status,
                    changed_by=changed_by,
                    job_title=job.title
                )
            except Exception as evt_e:
                logger.warning(f"Event dispatch failed for job pause: {evt_e}")
            
            successful += 1
            
        except Exception as e:
            logger.error(f"Error pausing job {job_id}: {e}")
            errors.append(BulkActionError(job_id=str(job_id), error_message=str(e)))
            failed += 1
    
    await db.commit()
    
    logger.info(f"📋 Bulk pause: {successful} succeeded, {failed} failed for company {company_id}")
    
    return BulkActionResponse(
        total_requested=len(request.job_ids),
        successful=successful,
        failed=failed,
        errors=errors
    )


@router.post("/job-vacancies/bulk/resume", response_model=BulkActionResponse)
async def bulk_resume_job_vacancies(
    request: BulkActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Resume multiple paused job vacancies.
    Changes status from 'Pausada' to 'Ativa'.
    Only jobs with status 'Pausada' can be resumed.
    Multi-tenant: Only affects jobs from the user's company.
    """
    from app.services.job_audit_service import job_audit_service
    
    company_id = get_user_company_id(current_user)
    changed_by = str(current_user.email) if hasattr(current_user, 'email') else str(current_user.id)
    
    successful = 0
    failed = 0
    errors: List[BulkActionError] = []
    
    for job_id in request.job_ids:
        try:
            result = await db.execute(
                select(JobVacancy).where(
                    and_(JobVacancy.id == job_id, JobVacancy.company_id == company_id)
                )
            )
            job = result.scalar_one_or_none()
            
            if not job:
                errors.append(BulkActionError(job_id=str(job_id), error_message="Vaga não encontrada"))
                failed += 1
                continue
            
            if job.status != "Pausada":
                errors.append(BulkActionError(
                    job_id=str(job_id), 
                    error_message=f"Apenas vagas pausadas podem ser retomadas. Status atual: {job.status}"
                ))
                failed += 1
                continue
            
            old_status = job.status
            job.status = "Ativa"
            job.updated_at = datetime.utcnow()
            
            await job_audit_service.log_status_change(
                job_id=str(job_id),
                old_status=old_status,
                new_status="Ativa",
                changed_by=changed_by,
                company_id=company_id,
                db=db,
                extra_data={"action": "bulk_resume"}
            )
            
            await job_status_webhook_service.dispatch_status_change(
                job_id=str(job_id),
                old_status=old_status,
                new_status="Ativa",
                company_id=company_id,
                db=db,
                changed_by=changed_by,
                job_title=job.title
            )
            
            successful += 1
            
        except Exception as e:
            logger.error(f"Error resuming job {job_id}: {e}")
            errors.append(BulkActionError(job_id=str(job_id), error_message=str(e)))
            failed += 1
    
    await db.commit()
    
    logger.info(f"📋 Bulk resume: {successful} succeeded, {failed} failed for company {company_id}")
    
    return BulkActionResponse(
        total_requested=len(request.job_ids),
        successful=successful,
        failed=failed,
        errors=errors
    )


@router.post("/job-vacancies/bulk/archive", response_model=BulkActionResponse)
async def bulk_archive_job_vacancies(
    request: BulkActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Archive multiple job vacancies (soft delete).
    Changes status to 'Arquivada' for all valid job IDs.
    Already archived jobs will be skipped with an error.
    Multi-tenant: Only affects jobs from the user's company.
    """
    from app.services.job_audit_service import job_audit_service
    
    company_id = get_user_company_id(current_user)
    changed_by = str(current_user.email) if hasattr(current_user, 'email') else str(current_user.id)
    
    successful = 0
    failed = 0
    errors: List[BulkActionError] = []
    
    for job_id in request.job_ids:
        try:
            result = await db.execute(
                select(JobVacancy).where(
                    and_(JobVacancy.id == job_id, JobVacancy.company_id == company_id)
                )
            )
            job = result.scalar_one_or_none()
            
            if not job:
                errors.append(BulkActionError(job_id=str(job_id), error_message="Vaga não encontrada"))
                failed += 1
                continue
            
            if job.status == "Arquivada":
                errors.append(BulkActionError(
                    job_id=str(job_id), 
                    error_message="Vaga já está arquivada"
                ))
                failed += 1
                continue
            
            old_status = job.status
            job.status = "Arquivada"
            job.updated_at = datetime.utcnow()
            
            await job_audit_service.log_archive(
                job_id=str(job_id),
                changed_by=changed_by,
                company_id=company_id,
                db=db,
                reason="Arquivamento em lote"
            )
            
            await job_status_webhook_service.dispatch_status_change(
                job_id=str(job_id),
                old_status=old_status,
                new_status="Arquivada",
                company_id=company_id,
                db=db,
                changed_by=changed_by,
                job_title=job.title
            )
            
            successful += 1
            
        except Exception as e:
            logger.error(f"Error archiving job {job_id}: {e}")
            errors.append(BulkActionError(job_id=str(job_id), error_message=str(e)))
            failed += 1
    
    await db.commit()
    
    logger.info(f"📋 Bulk archive: {successful} succeeded, {failed} failed for company {company_id}")
    
    return BulkActionResponse(
        total_requested=len(request.job_ids),
        successful=successful,
        failed=failed,
        errors=errors
    )


@router.post("/job-vacancies/bulk/assign-recruiter", response_model=BulkActionResponse)
async def bulk_assign_recruiter(
    request: BulkAssignRecruiterRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Assign a recruiter to multiple job vacancies.
    Updates recruiter_email and recruiter fields for all valid job IDs.
    Multi-tenant: Only affects jobs from the user's company.
    """
    from app.services.job_audit_service import job_audit_service
    
    company_id = get_user_company_id(current_user)
    changed_by = str(current_user.email) if hasattr(current_user, 'email') else str(current_user.id)
    
    successful = 0
    failed = 0
    errors: List[BulkActionError] = []
    
    for job_id in request.job_ids:
        try:
            result = await db.execute(
                select(JobVacancy).where(
                    and_(JobVacancy.id == job_id, JobVacancy.company_id == company_id)
                )
            )
            job = result.scalar_one_or_none()
            
            if not job:
                errors.append(BulkActionError(job_id=str(job_id), error_message="Vaga não encontrada"))
                failed += 1
                continue
            
            old_recruiter = job.recruiter
            old_recruiter_email = job.recruiter_email
            
            job.recruiter = request.recruiter_name
            job.recruiter_email = request.recruiter_email
            job.updated_at = datetime.utcnow()
            
            changes = {}
            if old_recruiter != request.recruiter_name:
                changes["recruiter"] = {"old": old_recruiter, "new": request.recruiter_name}
            if old_recruiter_email != request.recruiter_email:
                changes["recruiter_email"] = {"old": old_recruiter_email, "new": request.recruiter_email}
            
            if changes:
                await job_audit_service.log_update(
                    job_id=str(job_id),
                    changes=changes,
                    changed_by=changed_by,
                    company_id=company_id,
                    db=db
                )
            
            successful += 1
            
        except Exception as e:
            logger.error(f"Error assigning recruiter to job {job_id}: {e}")
            errors.append(BulkActionError(job_id=str(job_id), error_message=str(e)))
            failed += 1
    
    await db.commit()
    
    logger.info(f"📋 Bulk assign recruiter ({request.recruiter_email}): {successful} succeeded, {failed} failed for company {company_id}")
    
    return BulkActionResponse(
        total_requested=len(request.job_ids),
        successful=successful,
        failed=failed,
        errors=errors
    )


@router.post("/job-vacancies/bulk/change-status", response_model=BulkActionResponse)
async def bulk_change_status(
    request: BulkChangeStatusRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Change status for multiple job vacancies.
    Validates that the status transition is allowed for each job.
    Multi-tenant: Only affects jobs from the user's company.
    
    Valid statuses: Rascunho, Ativa, Pausada, Concluída, Cancelada, Arquivada
    
    Status transitions are validated according to business rules:
    - Rascunho -> Ativa, Cancelada, Arquivada
    - Ativa -> Pausada, Concluída, Cancelada, Arquivada
    - Pausada -> Ativa, Cancelada, Arquivada
    - Concluída -> Arquivada
    - Cancelada -> Arquivada
    - Arquivada -> (none)
    """
    from app.services.job_audit_service import job_audit_service
    
    company_id = get_user_company_id(current_user)
    changed_by = str(current_user.email) if hasattr(current_user, 'email') else str(current_user.id)
    
    if request.new_status not in VALID_JOB_STATUSES:
        raise HTTPException(
            status_code=400, 
            detail=f"Status inválido: '{request.new_status}'. Status válidos: {', '.join(VALID_JOB_STATUSES)}"
        )
    
    successful = 0
    failed = 0
    errors: List[BulkActionError] = []
    
    for job_id in request.job_ids:
        try:
            result = await db.execute(
                select(JobVacancy).where(
                    and_(JobVacancy.id == job_id, JobVacancy.company_id == company_id)
                )
            )
            job = result.scalar_one_or_none()
            
            if not job:
                errors.append(BulkActionError(job_id=str(job_id), error_message="Vaga não encontrada"))
                failed += 1
                continue
            
            old_status = job.status or "Rascunho"
            
            if old_status == request.new_status:
                errors.append(BulkActionError(
                    job_id=str(job_id), 
                    error_message=f"Vaga já está com status '{request.new_status}'"
                ))
                failed += 1
                continue
            
            allowed_transitions = ALLOWED_STATUS_TRANSITIONS.get(old_status, [])
            if request.new_status not in allowed_transitions:
                errors.append(BulkActionError(
                    job_id=str(job_id), 
                    error_message=f"Transição de status não permitida: '{old_status}' -> '{request.new_status}'"
                ))
                failed += 1
                continue
            
            job.status = request.new_status
            job.updated_at = datetime.utcnow()
            
            if request.new_status == "Ativa" and not job.open_date:
                job.open_date = datetime.utcnow()
            elif request.new_status in ["Concluída", "Cancelada", "Arquivada"] and not job.closed_at:
                job.closed_at = datetime.utcnow()
            
            await job_audit_service.log_status_change(
                job_id=str(job_id),
                old_status=old_status,
                new_status=request.new_status,
                changed_by=changed_by,
                company_id=company_id,
                db=db,
                extra_data={"action": "bulk_change_status"}
            )
            
            await job_status_webhook_service.dispatch_status_change(
                job_id=str(job_id),
                old_status=old_status,
                new_status=request.new_status,
                company_id=company_id,
                db=db,
                changed_by=changed_by,
                job_title=job.title
            )
            
            successful += 1
            
        except Exception as e:
            logger.error(f"Error changing status for job {job_id}: {e}")
            errors.append(BulkActionError(job_id=str(job_id), error_message=str(e)))
            failed += 1
    
    await db.commit()
    
    logger.info(f"📋 Bulk change status to '{request.new_status}': {successful} succeeded, {failed} failed for company {company_id}")
    
    return BulkActionResponse(
        total_requested=len(request.job_ids),
        successful=successful,
        failed=failed,
        errors=errors
    )


@router.post("/{vacancy_id}/close")
async def close_vacancy(
    vacancy_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
) -> Dict[str, Any]:
    """
    Close a vacancy after hiring a candidate.
    
    Sends congratulation notification to hired candidate and
    vacancy closed notification to other candidates.
    """
    try:
        company_id = get_user_company_id(current_user)
        data = await request.json()
        
        hired_candidate_id = data.get("hired_candidate_id")
        hired_notification = data.get("hired_notification", {})
        other_notifications = data.get("other_notifications", {})
        
        if not hired_candidate_id:
            raise HTTPException(status_code=400, detail="hired_candidate_id is required")
        
        vacancy_result = await db.execute(
            select(JobVacancy).where(JobVacancy.id == uuid_lib.UUID(vacancy_id))
        )
        vacancy = vacancy_result.scalar_one_or_none()
        
        if not vacancy:
            raise HTTPException(status_code=404, detail="Vacancy not found")
        
        from app.services.communication_service import CommunicationService, MessageType, MessageChannel
        communication_service = CommunicationService()
        
        notifications_sent = {
            "hired": None,
            "others": []
        }
        
        if hired_notification.get("channel") and hired_notification.get("message"):
            try:
                channel_str = hired_notification["channel"]
                channel = MessageChannel.EMAIL if channel_str == "email" else MessageChannel.WHATSAPP
                
                result = await communication_service.send_message(
                    company_id=company_id,
                    candidate_id=hired_candidate_id,
                    candidate_email=hired_notification.get("candidate_email"),
                    candidate_phone=hired_notification.get("candidate_phone"),
                    message_type=MessageType.GENERAL,
                    channel=channel,
                    subject=hired_notification.get("subject", ""),
                    body=hired_notification["message"],
                    job_id=vacancy_id,
                    skip_policy_checks=True,
                    db=db
                )
                notifications_sent["hired"] = {
                    "candidate_id": hired_candidate_id,
                    "channel": channel_str,
                    "success": result.get("success", True)
                }
            except Exception as e:
                logger.error(f"Failed to send hired notification: {e}")
                notifications_sent["hired"] = {"error": str(e)}
        
        other_candidate_ids = other_notifications.get("candidate_ids", [])
        if other_candidate_ids and other_notifications.get("message"):
            channel_str = other_notifications.get("channel", "email")
            channel = MessageChannel.EMAIL if channel_str == "email" else MessageChannel.WHATSAPP
            
            for cand_id in other_candidate_ids:
                try:
                    result = await communication_service.send_message(
                        company_id=company_id,
                        candidate_id=cand_id,
                        candidate_email=other_notifications.get("candidate_emails", {}).get(cand_id),
                        candidate_phone=other_notifications.get("candidate_phones", {}).get(cand_id),
                        message_type=MessageType.PROCESS_CLOSED,
                        channel=channel,
                        subject=other_notifications.get("subject", ""),
                        body=other_notifications["message"],
                        job_id=vacancy_id,
                        skip_policy_checks=True,
                        db=db
                    )
                    notifications_sent["others"].append({
                        "candidate_id": cand_id,
                        "channel": channel_str,
                        "success": result.get("success", True)
                    })
                except Exception as e:
                    logger.error(f"Failed to send vacancy closed notification to {cand_id}: {e}")
                    notifications_sent["others"].append({
                        "candidate_id": cand_id,
                        "error": str(e)
                    })
        
        vacancy.status = "Concluída"
        vacancy.closed_at = datetime.utcnow()
        
        await db.commit()
        
        try:
            from app.services.event_dispatcher import event_dispatcher
            await event_dispatcher.on_job_status_changed(
                job_id=vacancy_id,
                company_id=company_id,
                new_status="Concluída",
                previous_status="Ativa",
                changed_by=str(current_user.id),
                job_title=vacancy.title,
                hired_candidate_id=hired_candidate_id
            )
        except Exception as e:
            logger.warning(f"Event dispatch failed for job close: {e}")
        
        try:
            from app.services.activity_service import ActivityService
            activity_service = ActivityService()
            
            await activity_service.create_activity(
                activity_type="vacancy_closed",
                title=f"Vaga Fechada: {vacancy.title}",
                description=f"Candidato contratado. {len(other_candidate_ids)} candidatos notificados.",
                actor_id="system",
                actor_name="LIA",
                actor_type="system",
                target_id=vacancy_id,
                target_type="vacancy",
                extra_data={
                    "hired_candidate_id": hired_candidate_id,
                    "notified_count": len(other_candidate_ids),
                    "company_id": company_id
                },
                category="recruitment"
            )
        except Exception as e:
            logger.warning(f"Failed to log vacancy closed activity: {e}")
        
        return {
            "success": True,
            "vacancy_id": vacancy_id,
            "status": "Concluída",
            "hired_candidate_id": hired_candidate_id,
            "notifications_sent": notifications_sent
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error closing vacancy: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# =============================================
# D1 — Job Report Data (JSON para modal)
# =============================================

class JobReportFunnelMetrics(BaseModel):
    total_candidates: int
    screening: int
    interview: int
    final: int
    hired: int
    conversion_rate: float
    avg_time_to_hire: float
    cost_per_hire: float


class JobReportChannelItem(BaseModel):
    channel: str
    candidates: int
    hired: int


class JobReportTopCandidate(BaseModel):
    name: str
    score: float
    status: str


class JobReportResponse(BaseModel):
    vacancy_id: str
    vacancy_title: str
    funnel_metrics: JobReportFunnelMetrics
    channel_performance: List[JobReportChannelItem]
    top_candidates: List[JobReportTopCandidate]


@router.get("/jobs/{job_id}/report", response_model=JobReportResponse)
async def get_job_report(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
):
    """
    Retorna dados JSON para o JobReportModal:
    - funnel_metrics: totais e taxas do funil
    - channel_performance: candidatos por fonte/canal
    - top_candidates: top 5 por lia_score
    """
    company_id = get_user_company_id(current_user)

    job_result = await db.execute(
        select(JobVacancy).where(
            and_(JobVacancy.id == job_id, JobVacancy.company_id == company_id)
        )
    )
    job = job_result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")

    vc_result = await db.execute(
        select(VacancyCandidate).where(VacancyCandidate.vacancy_id == job_id)
    )
    vacancy_candidates = vc_result.scalars().all()
    total = len(vacancy_candidates)

    stage_map: Dict[str, int] = {}
    source_map: Dict[str, int] = {}
    source_hired: Dict[str, int] = {}
    hired_count = 0

    for vc in vacancy_candidates:
        stage = (vc.stage or "initial").lower()
        source = vc.source or "unknown"
        stage_map[stage] = stage_map.get(stage, 0) + 1
        source_map[source] = source_map.get(source, 0) + 1
        if stage in ("hired", "contratado"):
            hired_count += 1
            source_hired[source] = source_hired.get(source, 0) + 1

    def _stage_count(*aliases: str) -> int:
        return sum(stage_map.get(a, 0) for a in aliases)

    screening_count = _stage_count("screening", "triagem", "pending_gate1")
    interview_count = _stage_count("interview", "entrevista")
    final_count = _stage_count("final", "offer", "proposta")
    conversion_rate = round(hired_count / total * 100, 1) if total > 0 else 0.0

    # Tempo médio até contratação (dias) via CandidateStageHistory
    avg_time_to_hire = 0.0
    try:
        time_result = await db.execute(
            select(func.avg(CandidateStageHistory.time_in_previous_stage_hours))
            .where(
                and_(
                    CandidateStageHistory.vacancy_id == job_id,
                    CandidateStageHistory.to_stage_name.in_(["hired", "contratado"]),
                )
            )
        )
        avg_hours = time_result.scalar()
        if avg_hours:
            avg_time_to_hire = round(avg_hours / 24, 1)
    except Exception:
        pass

    # Top 5 candidatos por lia_score
    top_vc_result = await db.execute(
        select(VacancyCandidate, Candidate)
        .join(Candidate, VacancyCandidate.candidate_id == Candidate.id)
        .where(
            and_(
                VacancyCandidate.vacancy_id == job_id,
                VacancyCandidate.lia_score.isnot(None),
            )
        )
        .order_by(VacancyCandidate.lia_score.desc())
        .limit(5)
    )
    top_candidates = []
    for vc, cand in top_vc_result.all():
        top_candidates.append(
            JobReportTopCandidate(
                name=cand.name or "Candidato",
                score=float(vc.lia_score or 0),
                status=vc.stage or "initial",
            )
        )

    # Canal/fonte performance
    channel_performance = []
    for source, count in sorted(source_map.items(), key=lambda x: -x[1]):
        channel_performance.append(
            JobReportChannelItem(
                channel=source,
                candidates=count,
                hired=source_hired.get(source, 0),
            )
        )

    return JobReportResponse(
        vacancy_id=str(job_id),
        vacancy_title=job.title,
        funnel_metrics=JobReportFunnelMetrics(
            total_candidates=total,
            screening=screening_count,
            interview=interview_count,
            final=final_count,
            hired=hired_count,
            conversion_rate=conversion_rate,
            avg_time_to_hire=avg_time_to_hire,
            cost_per_hire=0.0,
        ),
        channel_performance=channel_performance,
        top_candidates=top_candidates,
    )
