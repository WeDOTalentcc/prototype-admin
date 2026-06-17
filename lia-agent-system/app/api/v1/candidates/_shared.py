"""
Shared imports, constants, helpers, and Pydantic models for all candidates sub-modules.
"""
import uuid
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.domains.candidates.dependencies import (
    get_candidate_favorites_repo,
    get_candidate_hidden_repo,
    get_candidate_repo,
    get_vacancy_candidate_repo,
)
from app.domains.candidates.repositories.candidate_favorites_repository import (
    CandidateFavoritesRepository,
    CandidateHiddenRepository,
)
from app.domains.candidates.repositories.candidate_repository import CandidateRepository
from app.domains.candidates.repositories.vacancy_candidate_repository import VacancyCandidateRepository
from app.domains.sourcing.services.pearch_service import PearchService, get_pearch_service, pearch_service
from app.models.candidate import (
    Candidate,
    CandidateFavorite,
    CandidateHidden,
    CandidateSearch,
)
from app.models.pearch import PearchSearchRequest, PearchSearchResponse
from app.schemas.candidate import (
    CandidateCreate,
    CandidateResponse,
    CandidateSearchRequest,
    CandidateSearchResponse,
    CandidateStageUpdate,
    CandidateUpdate,
)
from app.domains.analytics.services.activity_service import ActivityService, get_activity_service
from app.domains.analytics.services.calibration_service import CalibrationService  # R-055: direct canonical (shim deleted)
from app.shared.services.consent_checker_service import ConsentCheckerService
from app.shared.compliance.audit_service import AuditService, get_audit_service
from app.shared.compliance.fairness_guard_middleware import check_rejection_reason
from app.shared.pii_masking import get_masked_logger
from app.shared.types import WeDoBaseModel

logger = get_masked_logger(__name__)

# ---------------------------------------------------------------------------
# Stage ordering constants
# ---------------------------------------------------------------------------
STAGE_PROGRESSION_ORDER = {
    "sourcing": 0, "funil": 0, "funnel": 0, "sourced": 0, "novo": 0, "new": 0,
    "triagem": 1, "screening": 1, "cv aprovado": 1, "cv review": 1, "pre-triagem": 1,
    "entrevista rh": 2, "interview_hr": 2, "entrevista inicial": 2,
    "entrevista técnica": 3, "technical interview": 3, "entrevista tecnica": 3, "technical": 3,
    "entrevista final": 4, "final interview": 4, "entrevista gestor": 4, "manager interview": 4,
    "proposta": 5, "offer": 5, "oferta": 5, "proposta enviada": 5,
    "aceito": 6, "accepted": 6, "contratado": 6, "hired": 6, "admitido": 6, "contratação": 6
}

REJECTION_STAGES = {
    "reprovado", "rejected", "descartado", "discarded", "não aprovado",
    "recusado", "declined", "dropout", "desistiu", "cancelado", "arquivado"
}

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def get_stage_rank(stage: str) -> int:
    """
    Get numeric rank for a stage.
    Higher = further in pipeline.
    -1 = rejection stage
    -2 = unknown stage (treat transitions as neutral)
    """
    stage_lower = stage.lower().strip() if stage else ""
    if not stage_lower or stage_lower == "unknown":
        return -2
    if any(rej in stage_lower for rej in REJECTION_STAGES):
        return -1
    for key, rank in STAGE_PROGRESSION_ORDER.items():
        if key in stage_lower or stage_lower in key:
            return rank
    return -2


def determine_feedback_action(stage_from: str, stage_to: str) -> str:
    """
    Determine if a stage transition is an advancement or rejection.
    Returns: 'advance', 'reject', or 'neutral'
    """
    stage_to_lower = (stage_to or "").lower().strip()
    if any(rej in stage_to_lower for rej in REJECTION_STAGES):
        return "reject"
    from_rank = get_stage_rank(stage_from)
    to_rank = get_stage_rank(stage_to)
    if to_rank == -1:
        return "reject"
    if from_rank == -2 or to_rank == -2:
        return "neutral"
    if to_rank > from_rank:
        return "advance"
    if to_rank < from_rank:
        return "neutral"
    return "neutral"


def normalize_array_field(value) -> list:
    """Normalize PostgreSQL array fields that may come as string or list of chars."""
    if value is None:
        return []
    if isinstance(value, list):
        if len(value) > 0 and all(isinstance(v, str) and len(v) == 1 for v in value[:10]):
            array_str = "".join(value)
            return parse_pg_array_string(array_str)
        return value
    if isinstance(value, str):
        return parse_pg_array_string(value)
    return []


def extract_company_info_from_work_history(work_history: list) -> dict:
    """Extract company_industries and company_size from the most recent experience."""
    company_industries = []
    company_size = None
    if not work_history or not isinstance(work_history, list):
        return {"company_industries": company_industries, "company_size": company_size}
    for exp in work_history:
        if not isinstance(exp, dict):
            continue
        exp_industries = exp.get("industries", [])
        if exp_industries and isinstance(exp_industries, list) and not company_industries:
            company_industries = exp_industries
        exp_size = exp.get("company_size") or exp.get("company_size_range")
        if exp_size and not company_size:
            company_size = exp_size
        if company_industries and company_size:
            break
    return {"company_industries": company_industries, "company_size": company_size}


def parse_pg_array_string(array_str: str) -> list:
    """Parse a PostgreSQL array string format like {"item1","item2"} into a Python list."""
    if not array_str:
        return []
    array_str = array_str.strip()
    if array_str.startswith("{") and array_str.endswith("}"):
        inner = array_str[1:-1]
        if not inner:
            return []
        items = []
        current_item = ""
        in_quotes = False
        for char in inner:
            if char == '"' and not in_quotes:
                in_quotes = True
            elif char == '"' and in_quotes:
                in_quotes = False
            elif char == "," and not in_quotes:
                if current_item:
                    items.append(current_item.strip())
                current_item = ""
            else:
                current_item += char
        if current_item:
            items.append(current_item.strip())
        return items
    try:
        import json
        parsed = json.loads(array_str)
        if isinstance(parsed, list):
            return parsed
    except Exception:
        pass
    if "," in array_str:
        return [item.strip() for item in array_str.split(",") if item.strip()]
    if array_str:
        return [array_str]
    return []


# ---------------------------------------------------------------------------
# Shared Pydantic request models
# ---------------------------------------------------------------------------

class ScreeningDecisionRequest(WeDoBaseModel):
    """Request model for screening decision endpoint."""
    job_id: str | None = None
    decision: str  # "approved" or "rejected"
    reason: str | None = None
    reviewer_id: str | None = Field(None, description="ID do usuário que tomou a decisão (obrigatório para rejeições)")
