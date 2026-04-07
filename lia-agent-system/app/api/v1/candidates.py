"""
Candidates API endpoints - 2-tier search architecture:
1. Local search (proprietary PostgreSQL database) - FREE
2. Global search (Pearch AI 190M+ profiles) - PAID (credits required)
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
from app.services.calibration_service import CalibrationService
from app.services.consent_checker_service import ConsentCheckerService
from app.shared.compliance.audit_service import AuditService, get_audit_service
from app.shared.compliance.fairness_guard_middleware import check_rejection_reason
from app.shared.pii_masking import get_masked_logger

logger = get_masked_logger(__name__)


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
    Uses stage ranking to determine direction of movement.
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


class ScreeningDecisionRequest(BaseModel):
    """Request model for screening decision endpoint."""
    job_id: str | None = None
    decision: str  # "approved" or "rejected"
    reason: str | None = None
    reviewer_id: str | None = Field(None, description="ID do usuário que tomou a decisão (obrigatório para rejeições)")

router = APIRouter()


def normalize_array_field(value) -> list:
    """
    Normalize PostgreSQL array fields that may come as string or list of chars.
    Handles cases where ARRAY(String) returns a stringified PostgreSQL array format.
    """
    if value is None:
        return []

    # If it's already a proper list with real items (not single chars from iteration)
    if isinstance(value, list):
        # Check if it looks like a PostgreSQL array was iterated as chars: ['{', '"', 'S', 'o', 'f', 't', ...]
        if len(value) > 0 and all(isinstance(v, str) and len(v) == 1 for v in value[:10]):
            # Reconstruct the string and parse it
            array_str = ''.join(value)
            return parse_pg_array_string(array_str)
        return value

    # If it's a string, try to parse it
    if isinstance(value, str):
        return parse_pg_array_string(value)

    return []


def extract_company_info_from_work_history(work_history: list) -> dict:
    """
    Extract company_industries and company_size from the most recent experience.
    Returns dict with company_industries (list) and company_size (str or None).
    """
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
    """
    Parse a PostgreSQL array string format like {"Software Development","Cloud Computing"}
    into a Python list.
    """
    if not array_str:
        return []

    array_str = array_str.strip()

    # Handle PostgreSQL array format: {"item1","item2","item3"}
    if array_str.startswith('{') and array_str.endswith('}'):
        # Remove the outer braces
        inner = array_str[1:-1]
        if not inner:
            return []

        # Parse the comma-separated quoted values
        items = []
        current_item = ""
        in_quotes = False

        for char in inner:
            if char == '"' and not in_quotes:
                in_quotes = True
            elif char == '"' and in_quotes:
                in_quotes = False
            elif char == ',' and not in_quotes:
                if current_item:
                    items.append(current_item.strip())
                current_item = ""
            else:
                current_item += char

        # Don't forget the last item
        if current_item:
            items.append(current_item.strip())

        return items

    # Try JSON format
    try:
        import json
        parsed = json.loads(array_str)
        if isinstance(parsed, list):
            return parsed
    except Exception:
        pass

    # Try comma-separated
    if ',' in array_str:
        return [item.strip() for item in array_str.split(',') if item.strip()]

    # Single item
    if array_str:
        return [array_str]

    return []


# ==================== CRUD ENDPOINTS ====================

@router.get("", response_model=None)
async def list_candidates(
    search: str | None = None,
    status: str | None = None,
    source: str | None = None,
    ids: str | None = None,
    skip: int = 0,
    limit: int = 50,
    candidate_repo: CandidateRepository = Depends(get_candidate_repo),
):
    """
    List all candidates from the proprietary database.
    search: Optional text search in name, current_title, current_company, and technical_skills
    ids: Optional comma-separated list of candidate UUIDs to filter by
    """
    try:
        id_list: list[str] | None = None
        if ids:
            import re
            uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
            id_list = [i.strip() for i in ids.split(",") if i.strip() and uuid_pattern.match(i.strip())]
            if not id_list:
                id_list = None

        candidates = await candidate_repo.list_candidates(
            search=search,
            status=status,
            source=source,
            ids=id_list,
            skip=skip,
            limit=limit,
        )

        return {
            "total": len(candidates),
            "skip": skip,
            "limit": limit,
            "items": [
                {
                    "id": str(c.id),
                    "name": c.name,
                    "email": c.email,
                    "secondary_email": c.secondary_email,
                    "phone": c.phone,
                    "mobile_phone": c.mobile_phone,
                    "secondary_phone": c.secondary_phone,
                    "linkedin_url": c.linkedin_url,
                    "github_url": c.github_url,
                    "portfolio_url": c.portfolio_url,
                    "avatar_url": c.avatar_url,
                    "date_of_birth": str(c.date_of_birth) if c.date_of_birth else None,
                    "gender": c.gender,
                    "nationality": c.nationality,
                    "marital_status": c.marital_status,
                    "cpf": c.cpf,
                    "current_title": c.current_title,
                    "current_company": c.current_company,
                    "seniority_level": c.seniority_level,
                    "years_of_experience": c.years_of_experience,
                    "self_introduction": c.self_introduction,
                    "technical_skills": c.technical_skills or [],
                    "soft_skills": c.soft_skills or [],
                    "languages": c.languages or {},
                    "certifications": c.certifications or [],
                    "interests": c.interests or [],
                    "location_city": c.location_city,
                    "location_state": c.location_state,
                    "location_country": c.location_country,
                    "address_street": c.address_street,
                    "address_number": c.address_number,
                    "address_district": c.address_district,
                    "address_zip": c.address_zip,
                    "address_complement": c.address_complement,
                    "is_remote": c.is_remote,
                    "willing_to_relocate": c.willing_to_relocate,
                    "mobility": c.mobility,
                    "work_model_preference": c.work_model_preference,
                    "contract_type_preference": c.contract_type_preference,
                    "current_salary": c.current_salary,
                    "desired_salary_min": c.desired_salary_min,
                    "desired_salary_max": c.desired_salary_max,
                    "salary_currency": c.salary_currency,
                    "salary_expectation_clt": c.salary_expectation_clt,
                    "salary_expectation_pj": c.salary_expectation_pj,
                    "salary_expectation_freelance": c.salary_expectation_freelance,
                    "resume_url": c.resume_url,
                    "source": c.source,
                    "ats_source_name": c.ats_source_name,
                    "ats_candidate_id": c.ats_candidate_id,
                    "pearch_profile_id": c.pearch_profile_id,
                    "is_open_to_work": c.is_open_to_work,
                    "is_decision_maker": c.is_decision_maker,
                    "is_top_universities": c.is_top_universities,
                    "is_hiring": c.is_hiring,
                    "headline": c.headline,
                    "expertise": normalize_array_field(c.expertise),
                    "linkedin_followers_count": c.linkedin_followers_count,
                    "linkedin_connections_count": c.linkedin_connections_count,
                    "pearch_insights": c.pearch_insights or {},
                    "outreach_message": c.outreach_message,
                    "best_personal_email": c.best_personal_email,
                    "best_business_email": c.best_business_email,
                    "personal_emails": c.personal_emails or [],
                    "business_emails": c.business_emails or [],
                    "phone_types": c.phone_types or {},
                    "estimated_age": c.estimated_age,
                    "middle_name": c.middle_name,
                    "company_followers_count": c.company_followers_count,
                    "company_keywords": c.company_keywords or [],
                    "lia_score": c.lia_score,
                    "lia_insights": c.lia_insights or {},
                    "skills_match_percentage": c.skills_match_percentage,
                    "status": c.status,
                    "is_active": c.is_active,
                    "is_blacklisted": c.is_blacklisted,
                    "blacklist_reason": c.blacklist_reason,
                    "preferred_contact_method": c.preferred_contact_method,
                    "best_time_to_contact": c.best_time_to_contact,
                    "communication_consent": c.communication_consent,
                    "completed_register": c.completed_register,
                    "accept_terms": c.accept_terms,
                    "work_history": c.work_history or [],
                    **extract_company_info_from_work_history(c.work_history or []),
                    "tags": c.tags or [],
                    "notes": c.notes,
                    "additional_data": c.additional_data or {},
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                    "updated_at": c.updated_at.isoformat() if c.updated_at else None,
                    "last_contacted_at": c.last_contacted_at.isoformat() if c.last_contacted_at else None,
                    "last_activity_at": c.last_activity_at.isoformat() if c.last_activity_at else None
                }
                for c in candidates
            ]
        }

    except Exception as e:
        logger.error(f"Error listing candidates: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{candidate_id}", response_model=None)
async def get_candidate(
    candidate_id: str,
    candidate_repo: CandidateRepository = Depends(get_candidate_repo),
):
    """
    Get a specific candidate by ID.
    """
    try:
        candidate = await candidate_repo.get_by_id_str(candidate_id)

        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")

        return {
            "id": str(candidate.id),
            "name": candidate.name,
            "email": candidate.email,
            "secondary_email": candidate.secondary_email,
            "phone": candidate.phone,
            "mobile_phone": candidate.mobile_phone,
            "secondary_phone": candidate.secondary_phone,
            "linkedin_url": candidate.linkedin_url,
            "github_url": candidate.github_url,
            "portfolio_url": candidate.portfolio_url,
            "avatar_url": candidate.avatar_url,
            # Personal Information
            "date_of_birth": str(candidate.date_of_birth) if candidate.date_of_birth else None,
            "gender": candidate.gender,
            "nationality": candidate.nationality,
            "marital_status": candidate.marital_status,
            "cpf": candidate.cpf,
            # Professional
            "current_title": candidate.current_title,
            "current_company": candidate.current_company,
            "seniority_level": candidate.seniority_level,
            "years_of_experience": candidate.years_of_experience,
            "self_introduction": candidate.self_introduction,
            # Skills & Competencies
            "technical_skills": candidate.technical_skills or [],
            "soft_skills": candidate.soft_skills or [],
            "languages": candidate.languages or {},
            "certifications": candidate.certifications or [],
            "interests": candidate.interests or [],
            # Location
            "location_city": candidate.location_city,
            "location_state": candidate.location_state,
            "location_country": candidate.location_country,
            "address_street": candidate.address_street,
            "address_number": candidate.address_number,
            "address_district": candidate.address_district,
            "address_zip": candidate.address_zip,
            "address_complement": candidate.address_complement,
            # Work Preferences
            "is_remote": candidate.is_remote,
            "willing_to_relocate": candidate.willing_to_relocate,
            "mobility": candidate.mobility,
            "work_model_preference": candidate.work_model_preference,
            "contract_type_preference": candidate.contract_type_preference,
            # Salary
            "current_salary": candidate.current_salary,
            "desired_salary_min": candidate.desired_salary_min,
            "desired_salary_max": candidate.desired_salary_max,
            "salary_currency": candidate.salary_currency,
            "salary_expectation_clt": candidate.salary_expectation_clt,
            "salary_expectation_pj": candidate.salary_expectation_pj,
            "salary_expectation_freelance": candidate.salary_expectation_freelance,
            # Documents
            "resume_url": candidate.resume_url,
            "resume_text": candidate.resume_text,
            "cover_letter": candidate.cover_letter,
            # Source & Integration
            "source": candidate.source,
            "ats_source_name": candidate.ats_source_name,
            "ats_candidate_id": candidate.ats_candidate_id,
            "pearch_profile_id": candidate.pearch_profile_id,
            # Pearch / Global Search Data
            "is_open_to_work": candidate.is_open_to_work,
            "is_decision_maker": candidate.is_decision_maker,
            "is_top_universities": candidate.is_top_universities,
            "is_hiring": candidate.is_hiring,
            "headline": candidate.headline,
            "expertise": normalize_array_field(candidate.expertise),
            "linkedin_followers_count": candidate.linkedin_followers_count,
            "linkedin_connections_count": candidate.linkedin_connections_count,
            "pearch_insights": candidate.pearch_insights or {},
            "outreach_message": candidate.outreach_message,
            "best_personal_email": candidate.best_personal_email,
            "best_business_email": candidate.best_business_email,
            "personal_emails": candidate.personal_emails or [],
            "business_emails": candidate.business_emails or [],
            "phone_types": candidate.phone_types or {},
            "estimated_age": candidate.estimated_age,
            "middle_name": candidate.middle_name,
            "company_followers_count": candidate.company_followers_count,
            "company_keywords": candidate.company_keywords or [],
            # AI / LIA Insights
            "lia_score": candidate.lia_score,
            "lia_insights": candidate.lia_insights or {},
            "skills_match_percentage": candidate.skills_match_percentage,
            # Status
            "status": candidate.status,
            "is_active": candidate.is_active,
            "is_blacklisted": candidate.is_blacklisted,
            "blacklist_reason": candidate.blacklist_reason,
            # Communication
            "preferred_contact_method": candidate.preferred_contact_method,
            "best_time_to_contact": candidate.best_time_to_contact,
            "communication_consent": candidate.communication_consent,
            # Registration
            "completed_register": candidate.completed_register,
            "accept_terms": candidate.accept_terms,
            # Work History
            "work_history": candidate.work_history or [],
            # Flattened company info from most recent experience
            **extract_company_info_from_work_history(candidate.work_history or []),
            # Additional
            "tags": candidate.tags or [],
            "notes": candidate.notes,
            "additional_data": candidate.additional_data or {},
            # Timestamps
            "created_at": candidate.created_at.isoformat() if candidate.created_at else None,
            "updated_at": candidate.updated_at.isoformat() if candidate.updated_at else None,
            "last_contacted_at": candidate.last_contacted_at.isoformat() if candidate.last_contacted_at else None,
            "last_activity_at": candidate.last_activity_at.isoformat() if candidate.last_activity_at else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting candidate: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def _background_enrich_candidate(candidate_id: uuid.UUID, linkedin_url: str):
    """Background task to enrich candidate from LinkedIn."""
    from app.core.database import AsyncSessionLocal
    from app.services.candidate_enrichment_service import CandidateEnrichmentService

    try:
        async with AsyncSessionLocal() as db:
            enrichment_service = CandidateEnrichmentService()
            result = await enrichment_service.enrich_candidate(
                db=db,
                candidate_id=candidate_id,
                linkedin_url=linkedin_url,
                include_experiences=True,
                include_education=True,
                include_email_discovery=True
            )
            if result.get("success"):
                logger.info(f"Background enrichment completed for candidate {candidate_id}: {len(result.get('fields_updated', []))} fields updated")
            else:
                logger.warning(f"Background enrichment failed for candidate {candidate_id}: {result.get('error')}")
    except Exception as e:
        logger.error(f"Background enrichment error for candidate {candidate_id}: {e}")


@router.post("", response_model=None)
async def create_candidate(
    candidate_data: CandidateCreate,
    background_tasks: BackgroundTasks,
    candidate_repo: CandidateRepository = Depends(get_candidate_repo),
):
    """
    Create a new candidate.
    If auto_enrich=True and linkedin_url is provided, enrichment runs in background.
    """
    try:
        logger.info(f"Creating candidate: {candidate_data.name}")

        candidate = Candidate(
            id=uuid.uuid4(),
            name=candidate_data.name,
            email=candidate_data.email,
            phone=candidate_data.phone,
            linkedin_url=candidate_data.linkedin_url,
            github_url=candidate_data.github_url,
            portfolio_url=candidate_data.portfolio_url,
            current_title=candidate_data.current_title,
            current_company=candidate_data.current_company,
            seniority_level=candidate_data.seniority_level,
            years_of_experience=candidate_data.years_of_experience,
            technical_skills=candidate_data.technical_skills or [],
            soft_skills=candidate_data.soft_skills or [],
            languages=candidate_data.languages or {},
            certifications=candidate_data.certifications or [],
            location_city=candidate_data.location_city,
            location_state=candidate_data.location_state,
            location_country=candidate_data.location_country,
            is_remote=candidate_data.is_remote,
            willing_to_relocate=candidate_data.willing_to_relocate,
            desired_salary_min=candidate_data.desired_salary_min,
            desired_salary_max=candidate_data.desired_salary_max,
            salary_currency=candidate_data.salary_currency or "BRL",
            work_model_preference=candidate_data.work_model_preference,
            contract_type_preference=candidate_data.contract_type_preference,
            source=candidate_data.source or "manual",
            notes=candidate_data.notes,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        candidate = await candidate_repo.create(candidate)

        logger.info(f"Candidate created: {candidate.id}")

        enrichment_scheduled = False
        if candidate_data.auto_enrich and candidate_data.linkedin_url:
            background_tasks.add_task(
                _background_enrich_candidate,
                candidate.id,
                candidate_data.linkedin_url
            )
            enrichment_scheduled = True
            logger.info(f"Background enrichment scheduled for candidate {candidate.id}")

        return {
            "id": str(candidate.id),
            "name": candidate.name,
            "email": candidate.email,
            "phone": candidate.phone,
            "current_title": candidate.current_title,
            "current_company": candidate.current_company,
            "seniority_level": candidate.seniority_level,
            "location_city": candidate.location_city,
            "source": candidate.source,
            "status": candidate.status,
            "created_at": candidate.created_at.isoformat() if candidate.created_at else None,
            "message": "Candidate created successfully",
            "enrichment_scheduled": enrichment_scheduled
        }

    except Exception as e:
        logger.error(f"Error creating candidate: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{candidate_id}", response_model=None)
async def update_candidate(
    candidate_id: str,
    candidate_data: CandidateUpdate,
    candidate_repo: CandidateRepository = Depends(get_candidate_repo),
):
    """
    Update an existing candidate.
    """
    try:
        candidate = await candidate_repo.get_by_id_str(candidate_id)

        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")

        update_data = candidate_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(candidate, field):
                setattr(candidate, field, value)

        candidate.updated_at = datetime.utcnow()

        candidate = await candidate_repo.update(candidate)

        logger.info(f"Candidate updated: {candidate_id}")

        return {
            "id": str(candidate.id),
            "name": candidate.name,
            "email": candidate.email,
            "status": candidate.status,
            "updated_at": candidate.updated_at.isoformat() if candidate.updated_at else None,
            "message": "Candidate updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating candidate: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{candidate_id}/stage", response_model=None)
async def update_candidate_stage(
    candidate_id: str,
    stage_data: CandidateStageUpdate,
    candidate_repo: CandidateRepository = Depends(get_candidate_repo),
    vc_repo: VacancyCandidateRepository = Depends(get_vacancy_candidate_repo),
    audit_svc: AuditService = Depends(get_audit_service),
    activity_svc: ActivityService = Depends(get_activity_service),
):
    """
    Update candidate pipeline stage (used when moving candidates in Kanban).
    This is a lightweight endpoint for stage transitions.

    The stage is stored in VacancyCandidate (the relationship between candidate and job).
    If job_vacancy_id is provided, updates that specific relationship.
    Otherwise, updates the most recent VacancyCandidate for this candidate.
    """
    try:
        # First verify candidate exists
        candidate = await candidate_repo.get_by_id_str(candidate_id)

        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")

        # Find the VacancyCandidate to update
        vacancy_candidate = await vc_repo.get_for_candidate_and_job(
            candidate_id=candidate_id,
            job_vacancy_id=str(stage_data.job_vacancy_id) if stage_data.job_vacancy_id else None,
        )

        if not vacancy_candidate:
            # No VacancyCandidate found - update candidate status instead as fallback
            # Human Review Gate applies here too
            if get_stage_rank(stage_data.stage) == -1 and not stage_data.user_id:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": "human_review_required",
                        "message": (
                            "Rejeição de candidato requer identificação do revisor humano (user_id). "
                            "Rejeições automatizadas sem revisão humana não são permitidas."
                        ),
                        "compliance": ["LGPD art. 20", "EU AI Act art. 14"],
                    },
                )
            previous_stage = candidate.status or "unknown"
            candidate.status = stage_data.stage
            candidate.updated_at = datetime.utcnow()

            candidate = await candidate_repo.update(candidate)

            logger.info(f"Candidate {candidate_id} status updated (no vacancy): {previous_stage} -> {stage_data.stage}")

            return {
                "id": str(candidate.id),
                "name": candidate.name,
                "stage": stage_data.stage,
                "previous_stage": previous_stage,
                "sub_status": stage_data.sub_status,
                "updated_at": candidate.updated_at.isoformat() if candidate.updated_at else None,
                "message": "Candidate status updated successfully (no vacancy association)"
            }

        # Human Review Gate — block automated rejection without a human reviewer
        # Compliance: LGPD art. 20, EU AI Act art. 14
        is_rejection = get_stage_rank(stage_data.stage) == -1
        if is_rejection and not stage_data.user_id:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "human_review_required",
                    "message": (
                        "Rejeição de candidato requer identificação do revisor humano (user_id). "
                        "Rejeições automatizadas sem revisão humana não são permitidas."
                    ),
                    "compliance": ["LGPD art. 20", "EU AI Act art. 14"],
                },
            )

        # G2: FairnessGuard — check rejection sub_status for discriminatory bias
        if is_rejection and stage_data.sub_status:
            fg_rejection = check_rejection_reason(
                reason=stage_data.sub_status,
                candidate_name=candidate.name or "",
                company_id=str(vacancy_candidate.company_id) if hasattr(vacancy_candidate, "company_id") else "",
            )
            if fg_rejection.is_blocked:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": "fairness_blocked",
                        "message": fg_rejection.blocked_result.educational_message if fg_rejection.blocked_result else "Viés detectado no motivo da rejeição.",
                        "category": fg_rejection.blocked_result.category if fg_rejection.blocked_result else None,
                        "compliance": ["Lei 9.029/95", "CLT Art. 373-A"],
                    },
                )

        # Update stage in VacancyCandidate
        previous_stage = vacancy_candidate.stage or "unknown"
        lia_score_at_transition = vacancy_candidate.lia_score
        vacancy_candidate.stage = stage_data.stage

        # Record human reviewer when rejecting
        if is_rejection:
            vacancy_candidate.rejected_by_human = True
            vacancy_candidate.human_reviewer_id = stage_data.user_id

        # Update sub_status if provided
        if stage_data.sub_status:
            vacancy_candidate.status = stage_data.sub_status

        vacancy_candidate.updated_at = datetime.utcnow()

        vacancy_candidate = await vc_repo.update(vacancy_candidate)

        logger.info(f"Candidate {candidate_id} stage updated for vacancy {vacancy_candidate.vacancy_id}: {previous_stage} -> {stage_data.stage}")

        # Record implicit feedback for calibration learning loop
        feedback_action = determine_feedback_action(previous_stage, stage_data.stage)
        if feedback_action != "neutral":
            try:
                calibration_service = CalibrationService(candidate_repo.db)
                await calibration_service.record_implicit_feedback(
                    candidate_id=candidate_id,
                    job_id=str(vacancy_candidate.vacancy_id),
                    user_id=stage_data.user_id or "system",
                    action=feedback_action,
                    stage_from=previous_stage,
                    stage_to=stage_data.stage,
                    lia_score=lia_score_at_transition,
                    lia_ranking=None,
                    context={
                        "sub_status": stage_data.sub_status,
                        "candidate_name": candidate.name,
                        "transition_type": "kanban_move"
                    }
                )
                logger.info(f"Implicit feedback recorded: {feedback_action} for candidate {candidate_id} (LIA score: {lia_score_at_transition})")

                # Connect DB calibration to in-memory scoring calibration so future
                # evaluations for this job reflect recruiter approval/rejection patterns.
                if lia_score_at_transition is not None:
                    from uuid import uuid4

                    from app.domains.cv_screening.services.rubric_evaluation_service import calibration_feedback
                    adjusted_score: float
                    if feedback_action == "advance":
                        adjusted_score = min(99.0, lia_score_at_transition + 10.0)
                        recruiter_decision = "approved"
                    else:
                        adjusted_score = max(0.0, lia_score_at_transition - 15.0)
                        recruiter_decision = "rejected"
                    calibration_feedback.record_feedback(
                        evaluation_id=str(uuid4()),
                        candidate_id=candidate_id,
                        job_id=str(vacancy_candidate.vacancy_id),
                        original_score=lia_score_at_transition,
                        recruiter_adjusted_score=adjusted_score,
                        recruiter_decision=recruiter_decision,
                    )
                    logger.info(
                        f"Scoring calibration updated for job {vacancy_candidate.vacancy_id}: "
                        f"{recruiter_decision} (score {lia_score_at_transition:.1f} → {adjusted_score:.1f})"
                    )

                # D6-G2: ML Feedback Loop — registra sinal de decisão do recrutador
                try:
                    import asyncio as _asyncio

                    from app.services.ml_feedback_service import ml_feedback_service as _ml_fb
                    _decision_map = {"advance": "hire", "reject": "reject"}
                    _ml_decision = _decision_map.get(feedback_action)
                    if _ml_decision:
                        _company_id = str(getattr(vacancy_candidate, "company_id", "") or "")
                        _job_id = str(vacancy_candidate.vacancy_id)
                        _asyncio.create_task(
                            _ml_fb.record_decision(
                                db=candidate_repo.db,
                                company_id=_company_id,
                                job_id=_job_id,
                                candidate_id=candidate_id,
                                lia_score=float(lia_score_at_transition or 0),
                                decision=_ml_decision,
                            )
                        )
                except Exception as _ml_err:
                    logger.debug("[D6-G2] ml_feedback record_decision skipped: %s", _ml_err)

            except Exception as calibration_error:
                logger.warning(f"Failed to record implicit feedback: {calibration_error}")

        return {
            "id": str(candidate.id),
            "name": candidate.name,
            "stage": vacancy_candidate.stage,
            "previous_stage": previous_stage,
            "sub_status": vacancy_candidate.status,
            "vacancy_id": vacancy_candidate.vacancy_id,
            "updated_at": vacancy_candidate.updated_at.isoformat() if vacancy_candidate.updated_at else None,
            "message": "Candidate stage updated successfully",
            "feedback_recorded": feedback_action if feedback_action != "neutral" else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating candidate stage: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{candidate_id}", response_model=None)
async def delete_candidate(
    candidate_id: str,
    candidate_repo: CandidateRepository = Depends(get_candidate_repo),
):
    """
    Soft delete (deactivate) a candidate.
    """
    try:
        candidate = await candidate_repo.get_by_id_str(candidate_id)

        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")

        await candidate_repo.soft_delete(candidate)

        logger.info(f"Candidate deactivated: {candidate_id}")

        return {"message": "Candidate deactivated successfully", "id": candidate_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting candidate: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ENRICHMENT (APIFY LINKEDIN SCRAPER) ====================

class EnrichmentRequest(BaseModel):
    linkedin_url: str | None = None
    include_experiences: bool = True
    include_education: bool = True
    include_email_discovery: bool = True


@router.post("/{candidate_id}/enrich", response_model=None)
async def enrich_candidate(
    candidate_id: str,
    request: EnrichmentRequest = EnrichmentRequest(),
    candidate_repo: CandidateRepository = Depends(get_candidate_repo),
):
    """
    Enrich candidate data from LinkedIn using Apify scrapers.

    This endpoint scrapes the candidate's LinkedIn profile and fills in missing data:
    - Basic info: name, avatar, headline, current title/company
    - Location: city, state, country
    - Skills: technical skills, languages, certifications
    - Social: followers count, connections count, open to work status
    - Contact: emails (personal, business), phone discovery
    - Experience: work history records
    - Education: education records

    Requires APIFY_API_KEY to be configured.
    """
    try:
        from app.services.candidate_enrichment_service import candidate_enrichment_service

        result = await candidate_enrichment_service.enrich_candidate(
            db=candidate_repo.db,
            candidate_id=uuid.UUID(candidate_id),
            linkedin_url=request.linkedin_url,
            include_experiences=request.include_experiences,
            include_education=request.include_education,
            include_email_discovery=request.include_email_discovery
        )

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "Enrichment failed"))

        logger.info(f"Candidate enriched: {candidate_id} - {len(result.get('fields_updated', []))} fields updated")

        return {
            "success": True,
            "candidate_id": candidate_id,
            "fields_updated": result.get("fields_updated", []),
            "experiences_added": result.get("experiences_added", 0),
            "education_added": result.get("education_added", 0),
            "source": result.get("source", "apify"),
            "message": f"Enrichment completed: {len(result.get('fields_updated', []))} fields updated"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enriching candidate: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== LOCAL SEARCH (PROPRIETARY DATABASE - FREE) ====================

@router.post("/search/local", response_model=CandidateSearchResponse)
async def search_candidates_local(
    request: CandidateSearchRequest,
    current_user: User = Depends(get_current_user_or_demo),
    candidate_repo: CandidateRepository = Depends(get_candidate_repo),
    audit_svc: AuditService = Depends(get_audit_service),
):
    """
    Search candidates in proprietary PostgreSQL database (FREE - no credits consumed).

    This is ALWAYS the first search tier. Only suggest global search if local results
    are insufficient.
    """
    start_time = datetime.utcnow()
    filters = request.filters

    try:
        candidates_db, total_count = await candidate_repo.search_local(filters)

        # Convert to response schema
        candidates = [CandidateResponse.model_validate(c) for c in candidates_db]

        # Record search
        search_duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        search_record = CandidateSearch(
            id=uuid.uuid4(),
            user_id=str(current_user.id),
            conversation_id=request.conversation_id,
            search_query=filters.query or "structured_search",
            search_filters=filters.model_dump(),
            local_results_count=len(candidates),
            global_results_count=0,
            total_results=total_count or 0,
            used_global_search=False,
            credits_consumed=0,
            search_source="local",
            search_duration_ms=search_duration_ms,
            created_at=datetime.utcnow()
        )
        search_record = await candidate_repo.record_search(search_record)

        logger.info(f"Local search completed: {len(candidates)} results in {search_duration_ms}ms")

        try:
            _company = getattr(current_user, "company_id", None)
            active_filters = [k for k, v in (filters.model_dump() or {}).items() if v]
            await audit_svc.log_decision(
                company_id=str(_company) if _company else None,
                agent_name="candidate_search",
                decision_type="search_candidates",
                action="local_search",
                decision="executed",
                reasoning=[
                    f"Local search returned {len(candidates)} results",
                    f"Duration: {search_duration_ms}ms",
                    f"Active filters: {len(active_filters)}",
                    f"Total matches: {total_count or 0}",
                ],
                criteria_used=active_filters or ["no_filters"],
                score=float(len(candidates)),
                confidence=1.0,
                human_review_required=False,
            )
        except Exception as audit_err:
            logger.warning(f"Audit log failed for local_search: {audit_err}")

        return CandidateSearchResponse(
            candidates=candidates,
            total_count=total_count or 0,
            local_count=len(candidates),
            global_count=0,
            search_id=uuid.UUID(str(search_record.id)),
            credits_consumed=0
        )

    except Exception as e:
        logger.error(f"Local search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Local search failed: {str(e)}")


# ==================== GLOBAL SEARCH (PEARCH AI - PAID) ====================

@router.post("/search", response_model=PearchSearchResponse)
async def search_candidates(
    request: PearchSearchRequest,
    audit_svc: AuditService = Depends(get_audit_service),
    pearch_svc: PearchService = Depends(get_pearch_service),
):
    """
    Search for candidates using natural language query.
    """
    try:
        _search_type = getattr(request, "search_type", None) or getattr(request, "type", "fast")
        _limit = getattr(request, "limit", 10)
        _timeout = getattr(request, "timeout", 60)
        import time as _time
        _gs_start = _time.monotonic()
        result = await pearch_svc.search_candidates(
            query=request.query,
            search_type=str(_search_type),
            limit=_limit,
            timeout=_timeout
        )
        _gs_duration_ms = round((_time.monotonic() - _gs_start) * 1000, 1)
        try:
            _result_count = len(getattr(result, "candidates", [])) if result else 0
            await audit_svc.log_decision(
                company_id=None,
                agent_name="candidate_search",
                decision_type="search_candidates",
                action="global_search",
                decision="executed",
                reasoning=[
                    f"Global search ({_search_type}) executed",
                    f"Results returned: {_result_count}",
                    f"Duration: {_gs_duration_ms}ms",
                    f"Query length: {len(request.query)} chars",
                    f"Limit: {_limit}",
                    f"Timeout: {_timeout}s",
                ],
                criteria_used=["query", "search_type", "limit", "timeout"],
                score=float(_result_count),
                human_review_required=False,
            )
        except Exception as audit_err:
            logger.warning(f"Audit log failed for global_search: {audit_err}")
        return result
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Candidate search failed: {e}")
        raise HTTPException(status_code=500, detail="Candidate search failed")


@router.get("/search", response_model=PearchSearchResponse)
async def search_candidates_get(
    query: str = Query(..., description="Natural language search query"),
    search_type: str = Query("fast", description="Search type: 'fast' or 'deep'"),
    limit: int = Query(10, ge=1, le=100, description="Number of results"),
    timeout: int = Query(60, ge=10, le=1800, description="Timeout in seconds")
,
    pearch_svc: PearchService = Depends(get_pearch_service),
):
    """
    Search for candidates using GET request (convenient for testing).
    """
    try:
        return await pearch_svc.search_candidates(
            query=query,
            search_type=search_type,
            limit=limit,
            timeout=timeout
        )
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Candidate search failed: {e}")
        raise HTTPException(status_code=500, detail="Candidate search failed")


@router.post("/search/by-job-description", response_model=PearchSearchResponse)
async def search_by_job_description(
    job_description: str,
    location: str | None = None,
    limit: int = Query(20, ge=1, le=100)
,
    pearch_svc: PearchService = Depends(get_pearch_service),
):
    """
    Search candidates by pasting a full job description.
    """
    try:
        return await pearch_svc.search_by_job_description(
            job_description=job_description,
            location=location,
            limit=limit
        )
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Job description search failed: {e}")
        raise HTTPException(status_code=500, detail="Job description search failed")


@router.get("/health", response_model=None)
async def health_check():
    """
    Check if Pearch AI integration is properly configured.
    """
    import os
    api_key_configured = bool(os.getenv("PEARCH_API_KEY"))

    return {
        "service": "Pearch AI Candidate Search",
        "status": "configured" if api_key_configured else "not_configured",
        "api_key_set": api_key_configured,
        "message": "Ready to search 190M+ candidate profiles" if api_key_configured else "PEARCH_API_KEY not configured"
    }


# ==================== VIEWED CANDIDATES ENDPOINTS ====================

class ViewedCandidateCreate(BaseModel):
    source: str | None = None


class ViewedCandidateResponse(BaseModel):
    id: str
    candidate_id: str
    user_id: str
    viewed_at: str
    source: str | None = None


@router.post("/{candidate_id}/viewed", response_model=None)
async def mark_candidate_viewed(
    candidate_id: str,
    body: ViewedCandidateCreate = None,
    candidate_repo: CandidateRepository = Depends(get_candidate_repo),
):
    """
    Mark a candidate as viewed by the current user.
    Uses upsert to update viewed_at if already exists.
    """
    try:
        user_id = "default_user"
        source = body.source if body else None

        viewed, created = await candidate_repo.upsert_viewed(
            candidate_id=candidate_id,
            user_id=user_id,
            source=source,
        )

        if not created:
            return {
                "id": str(viewed.id),
                "candidate_id": viewed.candidate_id,
                "user_id": viewed.user_id,
                "viewed_at": viewed.viewed_at.isoformat() if viewed.viewed_at else None,
                "source": viewed.source,
                "message": "Viewed timestamp updated"
            }
        else:
            return {
                "id": str(viewed.id),
                "candidate_id": viewed.candidate_id,
                "user_id": viewed.user_id,
                "viewed_at": viewed.viewed_at.isoformat() if viewed.viewed_at else None,
                "source": viewed.source,
                "message": "Candidate marked as viewed"
            }

    except Exception as e:
        logger.error(f"Error marking candidate as viewed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/viewed/list", response_model=None)
async def list_viewed_candidates(
    skip: int = 0,
    limit: int = 100,
    candidate_repo: CandidateRepository = Depends(get_candidate_repo),
):
    """
    List all candidates viewed by the current user.
    Returns candidate IDs with view timestamps, ordered by most recently viewed.
    """
    try:
        user_id = "default_user"

        viewed_list, total = await candidate_repo.list_viewed(
            user_id=user_id, skip=skip, limit=limit
        )

        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "items": [
                {
                    "id": str(v.id),
                    "candidate_id": v.candidate_id,
                    "user_id": v.user_id,
                    "viewed_at": v.viewed_at.isoformat() if v.viewed_at else None,
                    "source": v.source
                }
                for v in viewed_list
            ],
            "candidate_ids": [v.candidate_id for v in viewed_list]
        }

    except Exception as e:
        logger.error(f"Error listing viewed candidates: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{candidate_id}/viewed", response_model=None)
async def unmark_candidate_viewed(
    candidate_id: str,
    candidate_repo: CandidateRepository = Depends(get_candidate_repo),
):
    """
    Remove viewed status from a candidate for the current user.
    """
    try:
        user_id = "default_user"

        deleted = await candidate_repo.delete_viewed(
            candidate_id=candidate_id, user_id=user_id
        )

        if not deleted:
            raise HTTPException(status_code=404, detail="Viewed record not found")

        return {"message": "Viewed status removed", "candidate_id": candidate_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unmarking candidate as viewed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== FAVORITES ENDPOINTS ====================

class FavoriteCreate(BaseModel):
    note: str | None = None
    is_pinned: bool = False
    source: str | None = None


class FavoriteUpdate(BaseModel):
    note: str | None = None
    is_pinned: bool | None = None


@router.post("/{candidate_id}/favorite", response_model=None)
async def toggle_favorite(
    candidate_id: str,
    body: FavoriteCreate = None,
    current_user: User = Depends(get_current_user_or_demo),
    favorites_repo: CandidateFavoritesRepository = Depends(get_candidate_favorites_repo),
):
    """
    Toggle favorite status for a candidate.
    If already favorited, removes it. If not, adds it.
    """
    try:
        user_id = str(current_user.id)
        if not current_user.company_id:
            raise HTTPException(status_code=400, detail="company_id is required but not set for current user")
        company_id = current_user.company_id

        existing = await favorites_repo.get(candidate_id=candidate_id, user_id=user_id)

        if existing:
            await favorites_repo.remove(existing)

            return {
                "action": "removed",
                "candidate_id": candidate_id,
                "is_favorite": False,
                "message": "Candidate removed from favorites"
            }
        else:
            favorite = CandidateFavorite(
                id=uuid.uuid4(),
                candidate_id=candidate_id,
                user_id=user_id,
                company_id=company_id,
                note=body.note if body else None,
                is_pinned=body.is_pinned if body else False,
                source=body.source if body else None
            )
            favorite = await favorites_repo.add(favorite)

            return {
                "action": "added",
                "id": str(favorite.id),
                "candidate_id": favorite.candidate_id,
                "user_id": favorite.user_id,
                "note": favorite.note,
                "is_pinned": favorite.is_pinned,
                "is_favorite": True,
                "created_at": favorite.created_at.isoformat() if favorite.created_at else None,
                "message": "Candidate added to favorites"
            }

    except Exception as e:
        logger.error(f"Error toggling favorite: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{candidate_id}/favorite", response_model=None)
async def update_favorite(
    candidate_id: str,
    body: FavoriteUpdate,
    favorites_repo: CandidateFavoritesRepository = Depends(get_candidate_favorites_repo),
):
    """
    Update favorite note or pinned status.
    """
    try:
        user_id = "default_user"

        favorite = await favorites_repo.get(candidate_id=candidate_id, user_id=user_id)

        if not favorite:
            raise HTTPException(status_code=404, detail="Favorite not found")

        if body.note is not None:
            favorite.note = body.note
        if body.is_pinned is not None:
            favorite.is_pinned = body.is_pinned

        favorite = await favorites_repo.update(favorite)

        return {
            "id": str(favorite.id),
            "candidate_id": favorite.candidate_id,
            "note": favorite.note,
            "is_pinned": favorite.is_pinned,
            "updated_at": favorite.updated_at.isoformat() if favorite.updated_at else None,
            "message": "Favorite updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating favorite: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/favorites/list", response_model=None)
async def list_favorites(
    skip: int = 0,
    limit: int = 100,
    favorites_repo: CandidateFavoritesRepository = Depends(get_candidate_favorites_repo),
):
    """
    List all favorited candidates for the current user.
    Returns favorites ordered by most recently added, with pinned items first.
    """
    try:
        user_id = "default_user"

        favorites_list, total = await favorites_repo.list_for_user(
            user_id=user_id, skip=skip, limit=limit
        )

        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "items": [
                {
                    "id": str(f.id),
                    "candidate_id": f.candidate_id,
                    "user_id": f.user_id,
                    "note": f.note,
                    "is_pinned": f.is_pinned,
                    "source": f.source,
                    "created_at": f.created_at.isoformat() if f.created_at else None,
                    "updated_at": f.updated_at.isoformat() if f.updated_at else None
                }
                for f in favorites_list
            ],
            "candidate_ids": [f.candidate_id for f in favorites_list]
        }

    except Exception as e:
        logger.error(f"Error listing favorites: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{candidate_id}/favorite", response_model=None)
async def remove_favorite(
    candidate_id: str,
    favorites_repo: CandidateFavoritesRepository = Depends(get_candidate_favorites_repo),
):
    """
    Remove a candidate from favorites.
    """
    try:
        user_id = "default_user"

        favorite = await favorites_repo.get(candidate_id=candidate_id, user_id=user_id)

        if not favorite:
            raise HTTPException(status_code=404, detail="Favorite not found")

        await favorites_repo.remove(favorite)

        return {"message": "Removed from favorites", "candidate_id": candidate_id, "is_favorite": False}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing favorite: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== HIDDEN CANDIDATES ENDPOINTS ====================

class HiddenCreate(BaseModel):
    reason: str | None = None
    source: str | None = None


@router.post("/{candidate_id}/hide", response_model=None)
async def toggle_hidden(
    candidate_id: str,
    body: HiddenCreate = None,
    current_user: User = Depends(get_current_user_or_demo),
    hidden_repo: CandidateHiddenRepository = Depends(get_candidate_hidden_repo),
):
    """
    Toggle hidden status for a candidate.
    If already hidden, shows it. If visible, hides it.
    """
    try:
        user_id = str(current_user.id)
        if not current_user.company_id:
            raise HTTPException(status_code=400, detail="company_id is required but not set for current user")
        company_id = current_user.company_id

        existing = await hidden_repo.get(candidate_id=candidate_id, user_id=user_id)

        if existing:
            await hidden_repo.remove(existing)

            return {
                "action": "shown",
                "candidate_id": candidate_id,
                "is_hidden": False,
                "message": "Candidate is now visible"
            }
        else:
            hidden = CandidateHidden(
                id=uuid.uuid4(),
                candidate_id=candidate_id,
                user_id=user_id,
                company_id=company_id,
                reason=body.reason if body else None,
                source=body.source if body else None
            )
            hidden = await hidden_repo.add(hidden)

            return {
                "action": "hidden",
                "id": str(hidden.id),
                "candidate_id": hidden.candidate_id,
                "user_id": hidden.user_id,
                "reason": hidden.reason,
                "is_hidden": True,
                "created_at": hidden.created_at.isoformat() if hidden.created_at else None,
                "message": "Candidate hidden"
            }

    except Exception as e:
        logger.error(f"Error toggling hidden: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hidden/list", response_model=None)
async def list_hidden(
    skip: int = 0,
    limit: int = 100,
    hidden_repo: CandidateHiddenRepository = Depends(get_candidate_hidden_repo),
):
    """
    List all hidden candidates for the current user.
    """
    try:
        user_id = "default_user"

        hidden_list, total = await hidden_repo.list_for_user(
            user_id=user_id, skip=skip, limit=limit
        )

        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "items": [
                {
                    "id": str(h.id),
                    "candidate_id": h.candidate_id,
                    "user_id": h.user_id,
                    "reason": h.reason,
                    "source": h.source,
                    "created_at": h.created_at.isoformat() if h.created_at else None
                }
                for h in hidden_list
            ],
            "candidate_ids": [h.candidate_id for h in hidden_list]
        }

    except Exception as e:
        logger.error(f"Error listing hidden candidates: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{candidate_id}/hide", response_model=None)
async def remove_hidden(
    candidate_id: str,
    hidden_repo: CandidateHiddenRepository = Depends(get_candidate_hidden_repo),
):
    """
    Remove a candidate from the hidden list (make visible).
    """
    try:
        user_id = "default_user"

        hidden = await hidden_repo.get(candidate_id=candidate_id, user_id=user_id)

        if not hidden:
            raise HTTPException(status_code=404, detail="Hidden record not found")

        await hidden_repo.remove(hidden)

        return {"message": "Candidate is now visible", "candidate_id": candidate_id, "is_hidden": False}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing hidden status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{candidate_id}/screening-decision", response_model=None)
async def screening_decision(
    candidate_id: str,
    request: ScreeningDecisionRequest,
    candidate_repo: CandidateRepository = Depends(get_candidate_repo),
    vc_repo: VacancyCandidateRepository = Depends(get_vacancy_candidate_repo),
):
    """
    Record screening decision for a candidate (approve or reject).

    - If approved: moves to "Entrevista" stage
    - If rejected: moves to "Reprovado Triagem" stage
    - Creates activity record for audit trail
    """
    try:
        if request.decision not in ["approved", "rejected"]:
            raise HTTPException(
                status_code=400,
                detail="Decision must be 'approved' or 'rejected'"
            )

        # Human Review Gate — block automated rejection without a human reviewer
        if request.decision == "rejected" and not request.reviewer_id:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "human_review_required",
                    "message": (
                        "Rejeição na triagem requer identificação do revisor humano (reviewer_id). "
                        "Rejeições automatizadas sem revisão humana não são permitidas."
                    ),
                    "compliance": ["LGPD art. 20", "EU AI Act art. 14"],
                },
            )

        # G2: FairnessGuard — check rejection reason for discriminatory bias
        if request.decision == "rejected" and request.reason:
            fg_rejection = check_rejection_reason(
                reason=request.reason,
                company_id=request.job_id or "",
            )
            if fg_rejection.is_blocked:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": "fairness_blocked",
                        "message": fg_rejection.blocked_result.educational_message if fg_rejection.blocked_result else "Viés detectado no motivo da rejeição.",
                        "category": fg_rejection.blocked_result.category if fg_rejection.blocked_result else None,
                        "compliance": ["Lei 9.029/95", "CLT Art. 373-A"],
                    },
                )

        candidate = await candidate_repo.get_by_id_str(candidate_id)

        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")

        # Validate contact info before approving (required for screening)
        if request.decision == "approved":
            has_valid_email = candidate.email and '@' in candidate.email
            has_valid_phone = candidate.phone and len(candidate.phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')) >= 8

            if not has_valid_email and not has_valid_phone:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "missing_contact_info",
                        "message": "Candidato não possui email ou telefone válido. É necessário ter pelo menos um contato para prosseguir com a triagem.",
                        "candidate_name": candidate.name,
                        "email": candidate.email,
                        "phone": candidate.phone
                    }
                )

        # First, get the current stage of the candidate in the vacancy
        current_stage = None
        vacancy_candidate = None
        if request.job_id:
            vacancy_candidate = await vc_repo.get_for_candidate_and_job(
                candidate_id=candidate_id,
                job_vacancy_id=request.job_id,
            )

        # Get current stage
        if vacancy_candidate:
            current_stage = vacancy_candidate.stage

        is_awaiting_screening = (
            vacancy_candidate
            and vacancy_candidate.status == "awaiting_screening"
            and request.decision == "approved"
        )

        if is_awaiting_screening:
            try:
                from app.domains.automation.services.automation_handlers import handle_recruiter_override_approve
                override_result = await handle_recruiter_override_approve(
                    db=candidate_repo.db,
                    candidate_id=str(candidate_id),
                    vacancy_id=str(vacancy_candidate.vacancy_id),
                    company_id=vacancy_candidate.company_id,
                )
                return {
                    "success": True,
                    "message": f"Candidato {candidate.name} priorizado da fila de espera",
                    "candidate_id": str(candidate_id),
                    "candidate_name": candidate.name,
                    "decision": "approved",
                    "new_stage": "screening",
                    "new_status": "screening",
                    "override": True,
                    "override_result": override_result,
                }
            except Exception as override_error:
                logger.error(f"Override approve failed: {override_error}", exc_info=True)

        early_stages = ["Novo", "Pipeline", "Funil", "Aplicado", "novo", "pipeline", "funil", "aplicado", "new", "applied"]
        screening_stages = ["Triagem", "triagem", "screening", "Screening"]

        if request.decision == "approved":
            if current_stage and current_stage.lower() in [s.lower() for s in early_stages]:
                new_stage = "Triagem"
                activity_description = "Candidato aprovado e movido para Triagem"
            elif current_stage and current_stage.lower() in [s.lower() for s in screening_stages]:
                new_stage = "Entrevista"
                activity_description = "Candidato aprovado na triagem e movido para Entrevista"
            else:
                new_stage = "Triagem"
                activity_description = "Candidato aprovado e movido para Triagem"

            new_status = "approved_screening"
            activity_type = "screening_approved"
            activity_title = f"Candidato Aprovado - {candidate.name}"
        else:
            new_stage = "Reprovado Triagem"
            new_status = "rejected_screening"
            activity_type = "screening_rejected"
            activity_title = f"Triagem Reprovada - {candidate.name}"
            activity_description = "Candidato reprovado na triagem"
            if request.reason:
                activity_description += f". Motivo: {request.reason}"

        # Update vacancy candidate if found
        if vacancy_candidate:
            vacancy_candidate.stage = new_stage
            vacancy_candidate.status = new_status
            vacancy_candidate.updated_at = datetime.utcnow()
            if request.reason:
                vacancy_candidate.notes = (vacancy_candidate.notes or "") + f"\n[Triagem] {request.reason}"
            # Record human reviewer for audit trail (guard already enforced above)
            if request.decision == "rejected":
                vacancy_candidate.rejected_by_human = True
                vacancy_candidate.human_reviewer_id = request.reviewer_id
            await vc_repo.update(vacancy_candidate)

        candidate.status = new_status
        await candidate_repo.update(candidate)

        try:
            await activity_svc.create_activity(
                activity_type=activity_type,
                title=activity_title,
                description=activity_description,
                summary=activity_description,
                actor_id="system",
                actor_name="LIA",
                actor_type="ai",
                target_id=str(candidate_id),
                target_name=candidate.name,
                target_type="candidate",
                extra_data={
                    "decision": request.decision,
                    "job_id": request.job_id,
                    "reason": request.reason,
                    "new_stage": new_stage,
                    "previous_status": candidate.status,
                },
                priority="normal",
                category="screening",
                action_url=f"/funil-de-talentos/candidato/{candidate_id}",
                action_label="Ver Candidato",
            )
        except Exception as activity_error:
            logger.warning(f"Failed to create activity: {activity_error}")

        logger.info(f"Screening decision recorded: {candidate.name} -> {request.decision}")

        try:
            _vc_company = getattr(vacancy_candidate, "company_id", None) if vacancy_candidate else None
            _vc_score = getattr(vacancy_candidate, "wsi_score", None) if vacancy_candidate else None
            _vc_ranking = getattr(vacancy_candidate, "ranking_position", None) if vacancy_candidate else None
            await audit_svc.log_decision(
                company_id=str(_vc_company) if _vc_company else None,
                agent_name="screening_module",
                decision_type="approved" if request.decision == "approved" else "rejected",
                action="screening_decision",
                decision=request.decision,
                reasoning=[
                    f"Screening decision: {request.decision}",
                    f"Stage transition: {new_stage}",
                    f"WSI score: {_vc_score}" if _vc_score else "WSI score: N/A",
                    f"Ranking: {_vc_ranking}" if _vc_ranking else "Ranking: N/A",
                    "Recruiter rationale: provided" if getattr(request, "reason", None) else "Recruiter rationale: none",
                ],
                criteria_used=["screening_evaluation", "recruiter_review", "wsi_score", "ranking_position"],
                candidate_id=str(candidate_id),
                job_vacancy_id=request.job_id,
                score=float(_vc_score) if _vc_score else None,
                human_review_required=request.decision == "rejected",
            )
        except Exception as audit_err:
            logger.warning(f"Audit log failed for screening_decision: {audit_err}")

        if request.decision == "rejected" and vacancy_candidate and request.job_id:
            try:
                from app.domains.automation.services.stage_automation_engine import (

# RAILS-DEPRECATED: This endpoint manages Rails-owned entities (candidates/jobs/applies/users).
# Direct DB calls will be replaced by RailsAdapter after ats-api-rails handoff.
# See: app/domains/integrations_hub/services/rails_adapter.py
                    AutomationEvent,
                    StageAutomationEngine,
                    TriggerType,
                )
                engine = StageAutomationEngine()
                slot_event = AutomationEvent(
                    trigger_type=TriggerType.SLOT_OPENED,
                    candidate_id=str(candidate_id),
                    vacancy_id=str(request.job_id),
                    company_id=vacancy_candidate.company_id,
                    payload={"slots_available": 1, "reason": "candidate_rejected"},
                    source="screening_decision",
                )
                await engine.process_event(slot_event, candidate_repo.db, auto_execute=True)
            except Exception as slot_error:
                logger.warning(f"Failed to process screening queue after rejection: {slot_error}")

        return {
            "success": True,
            "message": f"Candidate {request.decision} successfully",
            "candidate_id": str(candidate_id),
            "candidate_name": candidate.name,
            "decision": request.decision,
            "new_stage": new_stage,
            "new_status": new_status,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording screening decision: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== LGPD CONSENT ENDPOINTS ====================

class ConsentCreateRequest(BaseModel):
    consent_type: str
    consent_given: bool
    consent_source: str = "api"
    consent_text: str | None = None
    ip_address: str | None = None


@router.get("/{candidate_id}/consents", response_model=None)
async def get_candidate_consents(
    candidate_id: uuid.UUID,
    x_company_id: str | None = Header(None),
    candidate_repo: CandidateRepository = Depends(get_candidate_repo),
):
    """Lista todos os consentimentos LGPD de um candidato."""
    company_id = x_company_id or "admin_company"
    svc = ConsentCheckerService(candidate_repo.db)
    consents = await svc.get_candidate_consents(str(candidate_id), company_id)
    return {"candidate_id": str(candidate_id), "consents": consents}


@router.post("/{candidate_id}/consents", response_model=None)
async def create_or_update_candidate_consent(
    candidate_id: uuid.UUID,
    request: ConsentCreateRequest,
    x_company_id: str | None = Header(None),
    candidate_repo: CandidateRepository = Depends(get_candidate_repo),
):
    """Registra ou atualiza consentimento LGPD de um candidato por finalidade."""
    company_id = x_company_id or "admin_company"
    svc = ConsentCheckerService(candidate_repo.db)
    consent = await svc.register_consent(
        candidate_id=str(candidate_id),
        company_id=company_id,
        consent_type=request.consent_type,
        consent_given=request.consent_given,
        consent_source=request.consent_source,
        consent_text=request.consent_text,
        ip_address=request.ip_address,
    )
    await candidate_repo.db.commit()
    return consent.to_dict()


@router.delete("/{candidate_id}/consents/{consent_type}", status_code=200, response_model=None)
async def revoke_candidate_consent(
    candidate_id: uuid.UUID,
    consent_type: str,
    x_company_id: str | None = Header(None),
    candidate_repo: CandidateRepository = Depends(get_candidate_repo),
):
    """Revoga consentimento LGPD de um candidato para uma finalidade específica."""
    company_id = x_company_id or "admin_company"
    svc = ConsentCheckerService(candidate_repo.db)
    consent = await svc.register_consent(
        candidate_id=str(candidate_id),
        company_id=company_id,
        consent_type=consent_type,
        consent_given=False,
        consent_source="candidate_request",
    )
    await candidate_repo.db.commit()
    return {"success": True, "message": f"Consentimento '{consent_type}' revogado", "consent": consent.to_dict()}


# ==================== COMMUNICATION PREFERENCES ENDPOINTS ====================

class CommunicationPreferencesUpdate(BaseModel):
    preferred_channels: list[str] | None = None  # ["email", "whatsapp", "sms"]
    channel_opt_out: list[str] | None = None      # ["marketing_email", "whatsapp"]


@router.get("/{candidate_id}/communication-preferences", response_model=None)
async def get_communication_preferences(
    candidate_id: uuid.UUID,
    candidate_repo: CandidateRepository = Depends(get_candidate_repo),
    current_user: User = Depends(get_current_user_or_demo),
):
    """Retorna preferências de canal de comunicação do candidato."""
    candidate = await candidate_repo.get_by_id(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidato não encontrado")

    return {
        "candidate_id": str(candidate_id),
        "preferred_channels": candidate.preferred_channels or ["email"],
        "channel_opt_out": candidate.channel_opt_out or [],
        "preferred_contact_method": candidate.preferred_contact_method,
    }


@router.put("/{candidate_id}/communication-preferences", response_model=None)
async def update_communication_preferences(
    candidate_id: uuid.UUID,
    request: CommunicationPreferencesUpdate,
    candidate_repo: CandidateRepository = Depends(get_candidate_repo),
    current_user: User = Depends(get_current_user_or_demo),
):
    """Atualiza preferências de canal de comunicação do candidato."""
    candidate = await candidate_repo.get_by_id(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidato não encontrado")

    if request.preferred_channels is not None:
        candidate.preferred_channels = request.preferred_channels
    if request.channel_opt_out is not None:
        candidate.channel_opt_out = request.channel_opt_out

    candidate.updated_at = datetime.utcnow()
    candidate = await candidate_repo.update(candidate)

    return {
        "success": True,
        "candidate_id": str(candidate_id),
        "preferred_channels": candidate.preferred_channels,
        "channel_opt_out": candidate.channel_opt_out,
    }
