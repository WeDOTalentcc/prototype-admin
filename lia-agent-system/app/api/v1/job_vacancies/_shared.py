"""
Shared imports, constants, helpers, and Pydantic schemas
for the job_vacancies sub-package.
"""

__all__ = [
    # constants
    "VALID_JOB_STATUSES",
    "ALLOWED_STATUS_TRANSITIONS",
    "SATURATION_EXCLUDED_STATUSES",
    "ADHERENCE_THRESHOLD",
    "VALID_SCREENING_STATUSES",
    "VALID_PRIORITIES",
    "URGENCY_LEVELS",
    "WORK_MODEL_OPTIONS",
    "EMPLOYMENT_TYPE_OPTIONS",
    "SENIORITY_OPTIONS",
    # helpers
    "_calculate_days_between",
    "_is_job_at_risk",
    "derive_screening_status",
    "generate_slug",
    # schemas
    "JobVacancyCreate",
    "JobVacancyUpdate",
    "JobVacancyResponse",
    "FinalizeJobVacancyRequest",
    "FinalizeJobVacancyResponse",
    "BulkActionError",
    "BulkActionResponse",
    "BulkActionRequest",
    "BulkAssignRecruiterRequest",
    "BulkChangeStatusRequest",
    # re-exported deps
    "get_current_active_user",
    "get_current_user",
    "get_current_user_or_demo",
    "get_user_company_id",
    "User",
    "get_db",
    "AsyncSession",
    "Depends",
    "HTTPException",
    "JobVacancy",
    "JobVacancyState",
    "teams_service",
    "notification_service",
    "BaseModel",
    "Field",
    "logger",
]

import logging
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.domains.communication.services.teams_service import teams_service
from libs.messaging.lia_messaging.notification_service import notification_service
from app.models.job_vacancy import JobVacancy
from app.schemas.job_vacancy_state import JobVacancyState
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN

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

# --- Dropdown option vocabularies (FastAPI canonical — Rails fora do fluxo) ---
# Onda 1 (audit 2026-06-06): fonte única para GET /job-vacancies/options.
# Valores são as strings canônicas PT que o formulário FE persiste
# (ver plataforma-lia/src/components/jobs/job-edit-tab + helpers/vacancy_vocab.py).
VALID_PRIORITIES = ["alta", "média", "baixa"]

URGENCY_LEVELS = [
    {"id": 1, "name": "1 — Muito baixa"},
    {"id": 2, "name": "2 — Baixa"},
    {"id": 3, "name": "3 — Média"},
    {"id": 4, "name": "4 — Alta"},
    {"id": 5, "name": "5 — Crítica"},
]

WORK_MODEL_OPTIONS = ["remoto", "híbrido", "presencial"]

EMPLOYMENT_TYPE_OPTIONS = ["CLT", "PJ", "Estágio", "Freelancer", "Temporário"]

SENIORITY_OPTIONS = [
    "Estágio", "Júnior", "Pleno", "Sênior",
    "Especialista", "Coordenador", "Gerente", "Diretor",
]

# =============================================
# HELPER FUNCTIONS
# =============================================

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

    # P1-3 (audit 2026-06-05): a forma do wizard/grafo grava screening_questions
    # (sem wsi_skills/settings). Sem isto, vaga configurada pelo chat aparece
    # como "Configurar" (not_configured). derive_screening_status é o produtor
    # único do sinal — fix aqui conserta lista + detalhe + preview de uma vez.
    has_config = (
        bool(screening_config.get("wsi_skills"))
        or bool(screening_config.get("settings"))
        or bool(screening_config.get("screening_questions"))
    )
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
from app.shared.types import WeDoBaseModel


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



# ── Stakeholder validation (T10) ──────────────────────────────────────────

import re as _re_mod

_EMAIL_RE = _re_mod.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
_VALID_STAKEHOLDER_ROLES = {
    # roles novos (canonical)
    "ta_lead", "area_manager", "area_director", "technical_interviewer",
    # roles legados mantidos como alias (backward compat)
    "hr_bp", "dept_head", "committee_member", "interviewer", "other",
}


def _validate_stakeholders_list(v: list[dict] | None) -> list[dict] | None:
    if v is None:
        return v
    if not isinstance(v, list):
        raise ValueError("stakeholders deve ser uma lista")
    if len(v) > 20:
        raise ValueError("Maximo de 20 stakeholders por vaga")
    validated = []
    for i, item in enumerate(v):
        if not isinstance(item, dict):
            raise ValueError(f"stakeholders[{i}] deve ser um objeto")
        name = item.get("name")
        email = item.get("email")
        role = item.get("role", "other")
        if not name or not isinstance(name, str) or len(name.strip()) < 2:
            raise ValueError(f"stakeholders[{i}].name e obrigatorio (min 2 chars)")
        if not email or not isinstance(email, str) or not _EMAIL_RE.match(email.strip()):
            raise ValueError(f"stakeholders[{i}].email invalido: {email!r}")
        if role and role not in _VALID_STAKEHOLDER_ROLES:
            raise ValueError(
                f"stakeholders[{i}].role invalido: {role!r}. "
                f"Aceitos: {sorted(_VALID_STAKEHOLDER_ROLES)}"
            )
        validated.append({
            "name": name.strip(),
            "email": email.strip().lower(),
            "role": role or "other",
        })
    return validated

class JobVacancyCreate(WeDoBaseModel):
    """Schema for creating a job vacancy directly (not via conversation)."""
    title: str = Field(..., min_length=1, max_length=255)
    department: str | None = None
    location: str | None = None
    work_model: str | None = None
    employment_type: str | None = None
    seniority_level: str | None = None
    description: str | None = None
    # T-1166 — responsibilities (job duties) MUST be persisted separately from
    # requirements. Frontend reads `job.responsibilities` (see
    # SCMSectionContent.tsx) under the "RESPONSABILIDADES" label. Collapsing
    # both into `requirements` is the bug fixed by migration 132.
    responsibilities: list[str] | None = []
    requirements: list[str] | None = []
    technical_requirements: list[dict] | None = []
    languages: list[dict] | None = []
    behavioral_competencies: list[dict] | None = []
    salary: str | None = None
    salary_range: dict | None = None
    benefits: list[str | dict] | None = []
    variable_compensation: list[str | dict] | None = []
    manager: str | None = None
    manager_email: str | None = None
    recruiter: str | None = None
    recruiter_email: str | None = None
    stakeholders: list[dict] | None = None
    is_confidential: bool = False
    visibility: str = "public"
    access_list: list[str] | None = []
    masked_company_name: str | None = None
    exclude_from_sync: bool = False
    status: str = "Rascunho"
    # Phase 4H — source + wizard_stage tracking
    source: str = "wizard"  # 'wizard' | 'ats_import' | 'ats_external' | 'manual'
    wizard_stage: str | None = None  # current LangGraph node when source='wizard'
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

    @field_validator("stakeholders", mode="before")
    @classmethod
    def _validate_stakeholders(cls, v):
        return _validate_stakeholders_list(v)


class JobVacancyUpdate(WeDoBaseModel):
    """Schema for updating a job vacancy."""
    title: str | None = None
    department: str | None = None
    location: str | None = None
    work_model: str | None = None
    employment_type: str | None = None
    seniority_level: str | None = None
    description: str | None = None
    # T-1166 — see JobVacancyCreate.
    responsibilities: list[str] | None = None
    requirements: list[str] | None = None
    technical_requirements: list[dict] | None = None
    languages: list[dict] | None = None
    behavioral_competencies: list[dict] | None = None
    salary: str | None = None
    salary_range: dict | None = None
    bonus_range: dict | None = None
    benefits: list[str | dict] | None = None
    variable_compensation: list[str | dict] | None = None
    manager: str | None = None
    manager_email: str | None = None
    recruiter: str | None = None
    recruiter_email: str | None = None
    stakeholders: list[dict] | None = None
    is_confidential: bool | None = None
    visibility: str | None = None
    access_list: list[str] | None = None
    masked_company_name: str | None = None
    exclude_from_sync: bool | None = None
    status: str | None = None
    stage: str | None = None
    # Phase 4H — source + wizard_stage tracking (mostly read-only, but allow patch)
    source: str | None = None
    wizard_stage: str | None = None
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
    city: str | None = None
    # Onda 1 (audit 2026-06-06): prazos da vaga + urgência são features REAIS
    # (prazos alimentam job_alert_service/notifications; urgência é exibida/filtrável).
    # As colunas já existem no model; o setattr-loop genérico do update persiste.
    urgency_level: int | None = None
    open_date: datetime | None = None
    deadline: datetime | None = None
    deadline_screening: datetime | None = None
    deadline_shortlist: datetime | None = None
    deadline_closing: datetime | None = None

    # GAP-05-004: Optimistic locking control field.
    # When provided, the update is rejected (HTTP 409) if the DB updated_at
    # has changed since the client last read the vacancy.  Not a DB column;
    # the endpoint pops it before persisting.
    expected_updated_at: datetime | None = None

    @field_validator("stakeholders", mode="before")
    @classmethod
    def _validate_stakeholders(cls, v):
        return _validate_stakeholders_list(v)


class JobVacancyResponse(BaseModel):
    """Response schema for job vacancy."""
    id: str
    title: str
    department: str | None = None
    location: str | None = None
    city: str | None = None
    work_model: str | None = None
    employment_type: str | None = None
    seniority_level: str | None = None
    description: str | None = None
    # T-1166 — see JobVacancyCreate.
    responsibilities: list[str] | None = []
    requirements: list[str] | None = []
    technical_requirements: list[dict] | None = []
    languages: list[dict] | None = []
    behavioral_competencies: list[dict] | None = []

    # Auditoria 2026-05-22 (P0 — HTTP 500 em GET /job-vacancies):
    # Vaga seed antiga (Sprint O.2 Validation, id 74f462e9-...) tinha
    # technical_requirements no formato legacy {"python": true} (dict)
    # em vez do canonical [{"technology": "python"}] (list of dicts).
    # Pydantic 2 ResponseValidationError quebrava TODO list() porque
    # uma row no resultado nao matchava o schema. O dado foi normalizado
    # diretamente no banco (1 row UPDATE), mas adicionamos este validator
    # defense-in-depth para que qualquer dado legado/futuro corrompido
    # nao quebre o endpoint inteiro novamente.
    @field_validator(
        "technical_requirements",
        "languages",
        "behavioral_competencies",
        mode="before",
    )
    @classmethod
    def _normalize_list_of_dicts(cls, v):
        """Coerce legacy/corrupt shapes to list[dict] canonical.

        Aceita:
          - None / "" / [] → []
          - list[dict] → passthrough
          - dict {"skill": true, ...} → [{"technology": "skill"}, ...] (legacy)
          - lista de strings → [{"technology": s}, ...] (heuristica)
        """
        if v is None or v == "" or v == []:
            return []
        if isinstance(v, list):
            # Normalize string items embedded in list
            out = []
            for item in v:
                if isinstance(item, dict):
                    out.append(item)
                elif isinstance(item, str):
                    out.append({"technology": item})
                # silently drop other types — defense-in-depth
            return out
        if isinstance(v, dict):
            # Legacy: {"python": True, "react": False} → [{"technology": "python"}]
            return [{"technology": k} for k, val in v.items() if val]
        return []
    salary: str | None = None
    salary_range: dict | None = None
    bonus_range: dict | None = None
    benefits: list[str | dict] | None = []
    variable_compensation: list[str | dict] | None = []
    manager: str | None = None
    manager_email: str | None = None
    recruiter: str | None = None
    recruiter_email: str | None = None
    stakeholders: list[dict] | None = []
    is_confidential: bool = False
    visibility: str = "public"
    access_list: list[str] | None = []
    masked_company_name: str | None = None
    exclude_from_sync: bool = False
    created_by: str | None = None
    status: str = "Rascunho"
    # Phase 4H — source + wizard_stage tracking
    source: str = "wizard"
    wizard_stage: str | None = None
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


class FinalizeJobVacancyRequest(WeDoBaseModel):
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


class BulkActionRequest(WeDoBaseModel):
    job_ids: list[UUID] = Field(..., min_length=1, max_length=100)


class BulkAssignRecruiterRequest(WeDoBaseModel):
    job_ids: list[UUID] = Field(..., min_length=1, max_length=100)
    recruiter_email: str = Field(..., min_length=1)
    recruiter_name: str = Field(..., min_length=1)


class BulkChangeStatusRequest(WeDoBaseModel):
    job_ids: list[UUID] = Field(..., min_length=1, max_length=100)
    new_status: str = Field(..., min_length=1)



# ---------------------------------------------------------------------------
# JD fairness helpers (Task #358)
# ---------------------------------------------------------------------------

def _build_jd_fairness_text(
    *,
    title: str = "",
    description: str = "",
    requirements: "list[str] | None" = None,
    technical_requirements: "list[dict] | None" = None,
    behavioral_competencies: "list[dict] | None" = None,
    languages: "list[dict] | None" = None,
) -> str:
    """Build a concatenated text blob from JD fields for fairness analysis.

    Combines title, description, plain requirement strings, plus the
    key text fields extracted from structured dicts so the FairnessGuard
    can scan the entire posting in a single pass.

    Args:
        title: Job title string.
        description: Free-text job description.
        requirements: List of plain-text requirement strings.
        technical_requirements: List of dicts with a "technology" or "name" key.
        behavioral_competencies: List of dicts with a "competency" key.
        languages: List of dicts with a "language" key.

    Returns:
        Space-joined string of all non-empty parts.
    """
    parts: list[str] = []
    if title:
        parts.append(title)
    if description:
        parts.append(description)
    for req in (requirements or []):
        if req:
            parts.append(str(req))
    for tr in (technical_requirements or []):
        val = tr.get("technology") or tr.get("name", "")
        if val:
            parts.append(str(val))
    for bc in (behavioral_competencies or []):
        val = bc.get("competency", "")
        if val:
            parts.append(str(val))
    for lang in (languages or []):
        val = lang.get("language", "")
        if val:
            parts.append(str(val))
    return " ".join(parts)


def run_fairness_guard_on_jd(
    *,
    title: str = "",
    description: str = "",
    requirements: "list[str] | None" = None,
    technical_requirements: "list[dict] | None" = None,
    behavioral_competencies: "list[dict] | None" = None,
    languages: "list[dict] | None" = None,
) -> "list[str]":
    """Run the FairnessGuard over all JD text fields.

    Returns a (possibly empty) list of soft-warning strings when the JD
    passes but contains implicit-bias language.

    Raises:
        HTTPException(422): when the JD contains explicitly discriminatory
            content (``result.is_blocked`` is True).  The detail payload
            conforms to the frontend contract::

                {
                    "code": "fairness_blocked",
                    "category": "<category>",
                    "message": "<educational_message>",
                    "blocked_terms": [...],
                }
    """
    from fastapi import HTTPException as _HTTPException
    from app.shared.compliance.fairness_guard import FairnessGuard

    text = _build_jd_fairness_text(
        title=title,
        description=description,
        requirements=requirements,
        technical_requirements=technical_requirements,
        behavioral_competencies=behavioral_competencies,
        languages=languages,
    )

    try:
        guard = FairnessGuard()
        result = guard.check(text)
    except Exception:
        # FairnessGuard regression must never block a save.
        return []

    if result.is_blocked:
        raise _HTTPException(
            status_code=422,
            detail={
                "code": "fairness_blocked",
                "category": result.category,
                "message": result.educational_message or "Conteúdo discriminatório detectado.",
                "blocked_terms": result.blocked_terms,
            },
        )

    return list(result.soft_warnings or [])
# Backward-compat alias: job-vacancy handlers historically imported
# JOB_ID_PATH_PATTERN from here. It IS the canonical dual-ID pattern.
JOB_ID_PATH_PATTERN = DUAL_ID_PATH_PATTERN


# ─── Faixa salarial herdada da empresa (read-time enrichment, audit 2026-06-06) ─
# Paulo: a faixa salarial da vaga deve ser HERDADA da empresa (Configuracoes ->
# Faixas Salariais por Nivel) em TODO lugar (lista, detalhe), nao so quando o
# recrutador edita+salva. Resolve a banda por nivel + departamento + contrato e
# preenche salary_range das vagas SEM faixa explicita. Enriquecimento em tempo
# de LEITURA — nunca commitado (GET nao da commit). Faixa explicita sempre vence.
def _salary_range_is_empty(sr) -> bool:
    if not sr or not isinstance(sr, dict):
        return True
    if sr.get("undisclosed"):  # "A combinar" explicito — nao herda da empresa
        return False
    return not sr.get("min") and not sr.get("max")


def _band_to_salary_range(band) -> dict:
    return {
        "min": band.min,
        "max": band.max,
        "currency": band.currency or "BRL",
        "source": "company_salary_band",
        "inherited": True,
    }


async def resolve_inherited_salary_ranges(db, company_id, vacancies) -> None:
    """Preenche salary_range das vagas SEM faixa explicita com a banda cadastrada
    da empresa, casada por nivel + departamento + contrato. UMA leitura das
    bandas (sem N+1). Mutacao in-memory read-time (sem commit). Audit 2026-06-06."""
    if not company_id or company_id in ("default", "unknown"):
        return
    needing = [
        v for v in vacancies
        if _salary_range_is_empty(getattr(v, "salary_range", None))
        and getattr(v, "seniority_level", None)
    ]
    if not needing:
        return
    from app.domains.company.repositories.salary_band_repository import (
        SalaryBandRepository,
    )

    repo = SalaryBandRepository(db)
    try:
        bands = await repo.list_for_company(company_id, active_only=True)
    except Exception:  # fail-open — sem banda, faixa fica como esta
        return
    if not bands:
        return
    for v in needing:
        band = repo.match_from_bands(
            bands,
            seniority_level=v.seniority_level,
            department=getattr(v, "department", None),
            contract_type=getattr(v, "employment_type", None),
        )
        if band and band.min is not None:
            v.salary_range = _band_to_salary_range(band)


__all__.append("resolve_inherited_salary_ranges")


def _benefit_to_inherited_dict(b) -> dict:
    return {
        "id": str(b.id),
        "name": b.name,
        "category": b.category,
        "description": getattr(b, "description", None),
        "icon": getattr(b, "icon", None),
        "value": getattr(b, "value", None),
        "value_type": getattr(b, "value_type", None),
        "is_mandatory": bool(getattr(b, "is_mandatory", False)),
        "inherited": True,
        "source": "company_benefit",
    }


async def resolve_inherited_benefits(db, company_id, vacancies) -> None:
    """Preenche benefits das vagas SEM beneficios explicitos com os beneficios
    da empresa casados por nivel + departamento + contrato (+ os is_mandatory).
    Mutacao in-memory read-time (sem commit). Fail-open. Audit 2026-06-06 (FASE 1).
    Espelha resolve_inherited_salary_ranges; wirado so no detalhe (sem N+1)."""
    if not company_id or company_id in ("default", "unknown"):
        return
    needing = [v for v in vacancies if not (getattr(v, "benefits", None) or [])]
    if not needing:
        return
    from app.domains.company.repositories.company_benefit_repository import (
        CompanyBenefitRepository,
    )

    repo = CompanyBenefitRepository(db)
    for v in needing:
        try:
            pairs = await repo.list_matching(
                str(company_id),
                seniority_level=getattr(v, "seniority_level", None),
                department=getattr(v, "department", None),
                contract_type=getattr(v, "employment_type", None),
            )
        except Exception:  # noqa: BLE001 — fail-open por vaga
            continue
        inherited = [
            _benefit_to_inherited_dict(b)
            for (b, matches) in pairs
            if matches or getattr(b, "is_mandatory", False)
        ]
        if inherited:
            v.benefits = inherited


__all__.append("resolve_inherited_benefits")

# ─── Vacancy salary PII gate (audit 2026-06-06) ──────────────────────────────

async def load_role_pii_defaults(db, company_id: str) -> dict:
    from app.domains.hiring_policy.repositories.hiring_policy_repository import HiringPolicyRepository
    try:
        policy = await HiringPolicyRepository(db).get_by_company(company_id)
        return (getattr(policy, "pii_visibility_defaults", None) or {}) if policy else {}
    except Exception:  # fail-open — visibility check should never block reads
        return {}


def apply_vacancy_salary_visibility(vacancy_dict: dict, current_user, role_defaults=None) -> dict:
    """Mask vacancy salary fields when vacancy_salary visibility is hidden.

    Mutates and returns the dict. Adds vacancy_salary_masked flag.
    Default: visible (True). Fail-open to avoid breaking reads.
    """
    from app.shared.rbac.pii_field_resolver import resolve_field_visibility
    visible = resolve_field_visibility(current_user, role_defaults or {}, "vacancy_salary", default=True)
    if visible:
        vacancy_dict["vacancy_salary_masked"] = False
        return vacancy_dict
    for key in ("salary", "salary_range", "salary_min", "salary_max"):
        if key in vacancy_dict:
            vacancy_dict[key] = None
    vacancy_dict["vacancy_salary_masked"] = True
    return vacancy_dict


__all__.append("load_role_pii_defaults")
__all__.append("apply_vacancy_salary_visibility")

