"""
Shared imports, constants, helpers, and Pydantic schemas
for the job_vacancies sub-package.
"""
from fastapi import status
import logging
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.domains.communication.services.teams_service import TeamsService
from app.models.job_vacancy import JobVacancy
from app.schemas.job_vacancy_state import JobVacancyState
from app.services.notification_service import NotificationService

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

def generate_lia_metrics(funnel_data: dict | None) -> dict:
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


def _calculate_days_between(start_date: datetime | None, end_date: datetime | None) -> int:
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


import re
import secrets
from app.core.database import get_db  # noqa: F401
from app.auth.dependencies import get_current_active_user, get_current_user, get_user_company_id  # noqa: F401
from app.auth.models import User  # noqa: F401
from app.auth.dependencies import get_current_user_or_demo, get_current_user  # noqa: F401
from app.auth.models import User  # noqa: F401
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: F401
from fastapi import Depends, HTTPException  # noqa: F401


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
    department: str | None = None
    location: str | None = None
    work_model: str | None = None
    employment_type: str | None = None
    seniority_level: str | None = None
    description: str | None = None
    requirements: list[str] | None = []
    technical_requirements: list[dict] | None = []
    languages: list[dict] | None = []
    behavioral_competencies: list[dict] | None = []
    salary: str | None = None
    salary_range: dict | None = None
    benefits: list[str] | None = []
    manager: str | None = None
    manager_email: str | None = None
    recruiter: str | None = None
    recruiter_email: str | None = None
    is_confidential: bool = False
    visibility: str = "public"
    access_list: list[str] | None = []
    masked_company_name: str | None = None
    exclude_from_sync: bool = False
    status: str = "Rascunho"
    priority: str = "média"
    screening_questions: list[dict] | None = []
    interview_stages: list[dict] | None = []
    eligibility_questions: list[dict] | None = []
    disabled_eligibility_question_ids: list[str] | None = []
    confidentiality_config: dict | None = None
    is_affirmative: bool = False
    affirmative_criteria_primary: str | None = None
    affirmative_criteria_secondary: str | None = None
    affirmative_description: str | None = None
    affirmative_document_required: bool = False
    affirmative_document_types: list[str] | None = []
    bonus_range: dict | None = None
    conversation_id: str | None = None


class JobVacancyUpdate(BaseModel):
    """Schema for updating a job vacancy."""
    title: str | None = None
    department: str | None = None
    location: str | None = None
    work_model: str | None = None
    employment_type: str | None = None
    seniority_level: str | None = None
    description: str | None = None
    requirements: list[str] | None = None
    technical_requirements: list[dict] | None = None
    languages: list[dict] | None = None
    behavioral_competencies: list[dict] | None = None
    salary: str | None = None
    salary_range: dict | None = None
    bonus_range: dict | None = None
    benefits: list[str] | None = None
    manager: str | None = None
    manager_email: str | None = None
    recruiter: str | None = None
    recruiter_email: str | None = None
    is_confidential: bool | None = None
    visibility: str | None = None
    access_list: list[str] | None = None
    masked_company_name: str | None = None
    exclude_from_sync: bool | None = None
    status: str | None = None
    stage: str | None = None
    priority: str | None = None
    screening_questions: list[dict] | None = None
    interview_stages: list[dict] | None = None
    eligibility_questions: list[dict] | None = None
    disabled_eligibility_question_ids: list[str] | None = None
    confidentiality_config: dict | None = None
    is_affirmative: bool | None = None
    affirmative_criteria_primary: str | None = None
    affirmative_criteria_secondary: str | None = None
    affirmative_description: str | None = None
    affirmative_document_required: bool | None = None
    affirmative_document_types: list[str] | None = None
    enriched_jd: dict | None = None


class JobVacancyResponse(BaseModel):
    """Response schema for job vacancy."""
    id: str
    title: str
    department: str | None = None
    location: str | None = None
    work_model: str | None = None
    employment_type: str | None = None
    seniority_level: str | None = None
    description: str | None = None
    requirements: list[str] | None = []
    technical_requirements: list[dict] | None = []
    languages: list[dict] | None = []
    behavioral_competencies: list[dict] | None = []
    salary: str | None = None
    salary_range: dict | None = None
    bonus_range: dict | None = None
    benefits: list[str] | None = []
    manager: str | None = None
    manager_email: str | None = None
    recruiter: str | None = None
    recruiter_email: str | None = None
    is_confidential: bool = False
    visibility: str = "public"
    access_list: list[str] | None = []
    masked_company_name: str | None = None
    exclude_from_sync: bool = False
    created_by: str | None = None
    status: str = "Rascunho"
    stage: str | None = None
    priority: str = "média"
    created_at: str | None = None
    updated_at: str | None = None
    deadline: str | None = None
    funnel_data: dict | None = None
    lia_metrics: dict | None = None
    nps: int | None = None
    budget: float | None = None
    budget_used: float | None = None
    published_linkedin: bool = False
    published_website: bool = False
    next_actions: list[str] | None = []
    urgency_level: int | None = None
    approval_status: str | None = None
    tags: list[str] | None = []
    screening_questions: list[dict] | None = []
    interview_stages: list[dict] | None = []
    eligibility_questions: list[dict] | None = []
    disabled_eligibility_question_ids: list[str] | None = []
    confidentiality_config: dict | None = None
    is_affirmative: bool = False
    affirmative_criteria_primary: str | None = None
    affirmative_criteria_secondary: str | None = None
    affirmative_description: str | None = None
    affirmative_document_required: bool = False
    affirmative_document_types: list[str] | None = []
    conversation_id: str | None = None
    screening_config: dict | None = None
    enriched_jd: dict | None = None


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
    errors: list[BulkActionError] = []


class BulkActionRequest(BaseModel):
    job_ids: list[UUID] = Field(..., min_length=1, max_length=100)


class BulkAssignRecruiterRequest(BaseModel):
    job_ids: list[UUID] = Field(..., min_length=1, max_length=100)
    recruiter_email: str = Field(..., min_length=1)
    recruiter_name: str = Field(..., min_length=1)


class BulkChangeStatusRequest(BaseModel):
    job_ids: list[UUID] = Field(..., min_length=1, max_length=100)
    new_status: str = Field(..., min_length=1)
