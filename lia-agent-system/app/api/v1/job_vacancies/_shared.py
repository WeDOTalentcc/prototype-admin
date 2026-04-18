"""
Shared imports, constants, helpers, and Pydantic schemas
for the job_vacancies sub-package.
"""
import logging
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.domains.communication.services.teams_service import teams_service
from lia_messaging.notification_service import notification_service
from lia_models.job_vacancy import JobVacancy
from app.schemas.job_vacancy_state import JobVacancyState

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
# PATH PARAMETER CONTRACT (Task #455)
# =============================================
#
# Job vacancy IDs in this API can be either:
#   * UUIDs (local DB primary key)               — "550e8400-e29b-41d4-a716-446655440000"
#   * Decimal integers (Rails bigint, when the
#     RailsAdapter is enabled and the row was
#     authored on the legacy Rails side)         — "12345"
#
# Constraining `{job_vacancy_id}` / `{job_id}` / `{vacancy_id}` path
# parameters to this pattern serves two purposes:
#   1. Collection-scoped sibling routes (e.g. `/job-vacancies/lifecycle-overview`,
#      `/job-vacancies/bulk/pause`, `/job-vacancies/stats/overview`) can never
#      be silently captured by an item handler if router ordering regresses.
#   2. Garbage IDs receive a 422 from FastAPI before the handler runs, instead
#      of a misleading 404 raised by a `UUID("garbage")` ValueError inside the
#      handler.
#
# Routes that already declare the parameter as `UUID` get this for free from
# Pydantic, but `str`-typed parameters (kept that way to accept Rails bigints)
# need this explicit contract.
JOB_ID_PATH_PATTERN = r"^([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}|\d+)$"

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

from fastapi import Depends, HTTPException  # noqa: F401
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: F401

from app.auth.dependencies import (  # noqa: F401  # noqa: F401
    get_current_active_user,
    get_current_user,
    get_current_user_or_demo,
    get_user_company_id,
)
from app.auth.models import User  # noqa: F401  # noqa: F401
from app.core.database import get_db  # noqa: F401


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
    fairness_warnings: list[str] | None = None


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
    fairness_warnings: list[str] | None = None


# =============================================
# FAIRNESS GUARD HELPER (Task #358)
# =============================================
#
# Run FairnessGuard against the user-authored portions of a JobVacancy
# (title, description, requirements, requirement-like dicts) at the moment
# the recruiter creates or updates the row. Hard blocks raise an HTTP 422
# with the offending category/message so the row never lands in the DB;
# soft warnings are returned for the endpoint to attach to the response so
# the recruiter sees them but the save still succeeds.

_REQUIREMENT_DICT_TEXT_KEYS = (
    "technology", "skill", "name", "competency", "competencia",
    "language", "idioma", "description", "descricao",
)


def _stringify_requirement_entries(entries) -> list[str]:
    """Best-effort extract human-readable text from a mixed list of
    strings / dicts (technical_requirements, behavioral_competencies,
    languages, requirements). Unknown shapes fall back to ``str()``.
    """
    out: list[str] = []
    if not entries:
        return out
    for item in entries:
        if item is None:
            continue
        if isinstance(item, str):
            text = item.strip()
            if text:
                out.append(text)
        elif isinstance(item, dict):
            collected = []
            for key in _REQUIREMENT_DICT_TEXT_KEYS:
                val = item.get(key)
                if isinstance(val, str) and val.strip():
                    collected.append(val.strip())
            if collected:
                out.append(" ".join(collected))
            else:
                # Last resort: stringify all string-valued fields
                fallback = " ".join(
                    str(v) for v in item.values()
                    if isinstance(v, str) and v.strip()
                )
                if fallback:
                    out.append(fallback)
        else:
            text = str(item).strip()
            if text:
                out.append(text)
    return out


def _build_jd_fairness_text(
    *,
    title: str | None = None,
    description: str | None = None,
    requirements=None,
    technical_requirements=None,
    behavioral_competencies=None,
    languages=None,
) -> str:
    """Concatenate the user-authored JD fields that recruiters can fill
    with discriminatory language. Order/separator only matter for log
    readability — FairnessGuard scans the full string."""
    parts: list[str] = []
    if title and title.strip():
        parts.append(title.strip())
    if description and description.strip():
        parts.append(description.strip())
    parts.extend(_stringify_requirement_entries(requirements))
    parts.extend(_stringify_requirement_entries(technical_requirements))
    parts.extend(_stringify_requirement_entries(behavioral_competencies))
    parts.extend(_stringify_requirement_entries(languages))
    return "\n".join(parts)


def run_fairness_guard_on_jd(
    *,
    title: str | None = None,
    description: str | None = None,
    requirements=None,
    technical_requirements=None,
    behavioral_competencies=None,
    languages=None,
    context: str = "job_vacancy_save",
) -> list[str]:
    """Run FairnessGuard against the JD fields. Raises HTTPException(422)
    when explicit discriminatory content is detected (Layer 1 block).
    Returns the list of soft warnings (Layer 2 implicit-bias hits) for
    the caller to surface to the recruiter — these never block the save.

    Best-effort: any unexpected error in the guard itself is logged and
    treated as "no warnings" so a guard regression cannot make the JD
    save endpoint unusable.
    """
    text = _build_jd_fairness_text(
        title=title,
        description=description,
        requirements=requirements,
        technical_requirements=technical_requirements,
        behavioral_competencies=behavioral_competencies,
        languages=languages,
    )
    if not text.strip():
        return []

    try:
        from app.shared.compliance.fairness_guard import FairnessGuard
        guard = FairnessGuard()
        result = guard.check(text)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001 — defensive
        logger.warning(
            "[FairnessGuard] JD check skipped (%s): %s", context, exc
        )
        return []

    if result.is_blocked:
        logger.warning(
            "[FairnessGuard] BLOCKED JD save (%s): category=%s terms=%s",
            context, result.category, result.blocked_terms,
        )
        raise HTTPException(
            status_code=422,
            detail={
                "code": "fairness_blocked",
                "category": result.category,
                "message": result.educational_message,
                "blocked_terms": result.blocked_terms,
                "soft_warnings": result.soft_warnings,
            },
        )

    return list(result.soft_warnings or [])


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
