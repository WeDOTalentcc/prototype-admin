"""
Shared imports, constants, helpers, and Pydantic schemas
for the job_vacancies sub-package.
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
from app.domains.job_management.services.job_vacancy_service import job_vacancy_service
from app.services.sourcing_pipeline_service import sourcing_pipeline_service
from app.domains.communication.services.teams_service import TeamsService
from app.services.notification_service import NotificationService, NotificationType, NotificationChannel
from app.domains.job_management.services.job_status_webhook_service import job_status_webhook_service
from app.domains.analytics.services.job_report_service import job_report_service
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

logger = logging.getLogger(__name__)

# =============================================
# CONSTANTS
# =============================================

VALID_JOB_STATUSES = ["Rascunho", "Ativa", "Pausada", "Concluída", "Cancelada", "Arquivada"]

ALLOWED_STATUS_TRANSITIONS = {
    "Rascunho": ["Ativa", "Cancelada", "Arquivada"],
    "Ativa": ["Pausada", "Concluída", "Cancelada", "Arquivada"],
    "Pausada": ["Ativa", "Cancelada", "Arquivada"],
    "Concluída": ["Arquivada"],
    "Cancelada": ["Arquivada"],
    "Arquivada": [],
}

SATURATION_EXCLUDED_STATUSES = ('rejected', 'declined', 'withdrawn')
ADHERENCE_THRESHOLD = 55.0

VALID_SCREENING_STATUSES = {"not_configured", "not_started", "active", "paused", "completed"}

# =============================================
# HELPER FUNCTIONS
# =============================================

def generate_lia_metrics(funnel_data: Optional[dict]) -> dict:
    """Generate LIA performance metrics based on funnel data."""
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

    pipeline_base = int(total * random.uniform(0.75, 0.95)) if total > 0 else 0
    triagens_agendadas = int(screening * random.uniform(0.60, 0.85)) if screening > 0 else 0
    triagens_realizadas = int(triagens_agendadas * random.uniform(0.70, 0.90)) if triagens_agendadas > 0 else 0
    sem_resposta = int(total * random.uniform(0.10, 0.25)) if total > 0 else 0
    entrevistas_agendadas = int(interview * random.uniform(0.70, 0.90)) if interview > 0 else 0

    return {
        "pipeline_lia": pipeline_base,
        "triagens_agendadas": triagens_agendadas,
        "triagens_realizadas": triagens_realizadas,
        "sem_resposta": sem_resposta,
        "entrevistas_agendadas": entrevistas_agendadas
    }


def _calculate_days_between(start_date: Optional[datetime], end_date: Optional[datetime]) -> int:
    """Calculate days between two dates, handling None values."""
    if not start_date or not end_date:
        return 0
    delta = end_date - start_date
    return max(0, delta.days)


def _is_job_at_risk(job: JobVacancy, now: datetime) -> bool:
    """Determine if a job is at risk."""
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


# =============================================
# SHARED PYDANTIC SCHEMAS
# =============================================

class JobVacancyCreate(BaseModel):
    """Schema for creating a job vacancy directly (not via conversation)."""
    title: str = Field(..., min_length=1, max_length=255)
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
    status: str = "Rascunho"
    priority: str = "média"
    screening_questions: Optional[List[dict]] = []
    interview_stages: Optional[List[dict]] = []
    eligibility_questions: Optional[List[dict]] = []
    disabled_eligibility_question_ids: Optional[List[str]] = []
    confidentiality_config: Optional[dict] = None
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
    disabled_eligibility_question_ids: Optional[List[str]] = None
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
    disabled_eligibility_question_ids: Optional[List[str]] = []
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
    conversation_id: str
    job_vacancy_state: JobVacancyState
    created_by: str


class FinalizeJobVacancyResponse(BaseModel):
    success: bool
    job_vacancy_id: str
    title: str
    status: str
    message: str


class BulkActionError(BaseModel):
    job_id: str
    error_message: str


class BulkActionResponse(BaseModel):
    total_requested: int
    successful: int
    failed: int
    errors: List[BulkActionError] = []


class BulkActionRequest(BaseModel):
    job_ids: List[UUID] = Field(..., min_length=1, max_length=100)


class BulkAssignRecruiterRequest(BaseModel):
    job_ids: List[UUID] = Field(..., min_length=1, max_length=100)
    recruiter_email: str = Field(..., min_length=1)
    recruiter_name: str = Field(..., min_length=1)


class BulkChangeStatusRequest(BaseModel):
    job_ids: List[UUID] = Field(..., min_length=1, max_length=100)
    new_status: str = Field(..., min_length=1)
