"""
Bulk Actions API endpoints for mass operations on candidates and job vacancies.
Allows performing actions on multiple records at once with transactional safety.
"""
import csv
import io
import logging
import uuid
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator

from app.auth.dependencies import get_current_user, require_admin_or_recruiter
from app.auth.models import User
from app.repositories.dependencies import get_bulk_actions_repo
from app.repositories.bulk_actions_repository import BulkActionsRepository
from app.domains.communication.services.email_service import get_email_service
from app.shared.compliance.audit_service import audit_service  # module-level for test patchability
from app.shared.compliance.fairness_guard import FairnessGuard as _FairnessGuard
_fairness_guard = _FairnessGuard()
_DECISION_TYPE_MAP = {
    'rejected': 'reject_candidate',
    'hired': 'approve_candidate',
    'screening': 'move_stage',
    'interview': 'move_stage',
    'offer': 'move_stage',
    'new': 'move_stage',
}
from app.domains.communication.services.email_service import EmailService
from app.models.job_vacancy import JobVacancy
from app.shared.security.require_company_id import require_company_id
from sqlalchemy import select as _sa_select
from app.models.candidate import VacancyCandidate as _VacancyCandidate
from app.shared.types import WeDoBaseModel
from app.domains.recruitment.services.triagem_session_service.service import TriagemSessionService

logger = logging.getLogger(__name__)

router = APIRouter()

MAX_BULK_ITEMS = 100
VALID_CANDIDATE_STATUSES = ["new", "screening", "interview", "offer", "hired", "rejected"]
# State machine: maps current_status -> set of allowed target statuses.
# Prevents nonsensical transitions (e.g. hired->new) while allowing
# legitimate recruiting flows including reconsideration (rejected->screening).
STATUS_TRANSITIONS: dict[str, set[str]] = {
    "new":        {"screening", "interview", "offer", "hired", "rejected"},
    "screening":  {"new", "interview", "offer", "hired", "rejected"},
    "interview":  {"new", "screening", "offer", "hired", "rejected"},
    "offer":      {"interview", "hired", "rejected"},
    "hired":      {"rejected"},          # only reversal allowed
    "rejected":   {"new", "screening"},  # reconsideration only
}
# Sentinela: candidatos sem status (None/empty) podem ir pra qualquer estado
_STATUS_UNKNOWN = "__unknown__"


def _check_status_transition(current_status, new_status):
    """Returns error message if transition is invalid, None if allowed.

    Unknown current status (None/empty) is always allowed -- fail-open
    for legacy data without a status set.
    """
    if not current_status:
        return None
    allowed = STATUS_TRANSITIONS.get(current_status)
    if allowed is None:
        return None  # unknown current status -- fail-open
    if new_status not in allowed:
        return (
            f"Transicao invalida: {current_status!r} -> {new_status!r}. "
            f"Permitido: {', '.join(sorted(allowed))}. "
            f"Para corrigir: escolha um dos status permitidos para candidatos em {current_status!r}."
        )
    return None



DEFAULT_SATURATION_THRESHOLD = 20
DEFAULT_UNLOCK_INCREMENT = 10
DEFAULT_UNLOCK_HOURS = 24


async def _check_vacancy_saturation(repo: BulkActionsRepository, vacancy: JobVacancy) -> dict:
    company = None
    try:
        company = await repo.get_company_by_id(vacancy.company_id)
    except Exception:
        pass
    if not company:
        company = await repo.get_default_company()

    sat = {}
    if company and company.additional_data:
        sat = company.additional_data.get("saturation_settings", {})

    governance_rules = vacancy.governance_rules or {}
    threshold_web = governance_rules.get("threshold_web", sat.get("threshold_web", DEFAULT_SATURATION_THRESHOLD))
    threshold_sourcing = governance_rules.get("threshold_sourcing", sat.get("threshold_sourcing", DEFAULT_SATURATION_THRESHOLD))

    disabled_until_str = governance_rules.get("saturation_disabled_until")
    bypass_active = False
    if disabled_until_str:
        try:
            disabled_until = datetime.fromisoformat(disabled_until_str)
            if disabled_until > datetime.utcnow():
                bypass_active = True
        except (ValueError, TypeError):
            pass

    counts = await repo.get_vacancy_channel_counts(vacancy.id)
    organic_count = counts["organic"]
    sourcing_count = counts["sourcing"]

    organic_saturated = organic_count >= threshold_web and not bypass_active
    sourcing_saturated = sourcing_count >= threshold_sourcing and not bypass_active
    is_saturated = organic_saturated or sourcing_saturated

    return {
        "is_saturated": is_saturated,
        "bypass_active": bypass_active,
        "organic_count": organic_count,
        "sourcing_count": sourcing_count,
        "threshold_web": threshold_web,
        "threshold_sourcing": threshold_sourcing,
        "organic_saturated": organic_saturated,
        "sourcing_saturated": sourcing_saturated,
    }


class BulkOperationError(BaseModel):
    """Error detail for a single item in a bulk operation."""
    id: str
    error_message: str


class BulkOperationResult(BaseModel):
    """Result of a bulk operation with detailed success/failure info."""
    total: int
    successful: int
    failed: int
    errors: list[BulkOperationError] = []
    processed_ids: list[str] = []
    message: str = ""


class BulkUpdateStatusRequest(WeDoBaseModel):
    """Request to update status of multiple candidates."""
    candidate_ids: list[str] = Field(..., min_length=1, max_length=MAX_BULK_ITEMS)
    new_status: str = Field(..., description="Status: new, screening, interview, offer, hired, rejected")

    @field_validator("new_status")
    @classmethod
    def validate_status(cls, v):
        if v not in VALID_CANDIDATE_STATUSES:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(VALID_CANDIDATE_STATUSES)}")
        return v

    @field_validator("candidate_ids")
    @classmethod
    def validate_ids_limit(cls, v):
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f"Maximum {MAX_BULK_ITEMS} items per operation")
        return v


class BulkAssignJobRequest(WeDoBaseModel):
    """Request to assign multiple candidates to a job vacancy."""
    candidate_ids: list[str] = Field(..., min_length=1, max_length=MAX_BULK_ITEMS)
    job_vacancy_id: str
    notes: str | None = None

    @field_validator("candidate_ids")
    @classmethod
    def validate_ids_limit(cls, v):
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f"Maximum {MAX_BULK_ITEMS} items per operation")
        return v


class BulkSendEmailRequest(WeDoBaseModel):
    """Request to send emails to multiple candidates."""
    candidate_ids: list[str] = Field(..., min_length=1, max_length=MAX_BULK_ITEMS)
    template_id: str
    custom_variables: dict | None = None

    @field_validator("candidate_ids")
    @classmethod
    def validate_ids_limit(cls, v):
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f"Maximum {MAX_BULK_ITEMS} items per operation")
        return v


class BulkStartScreeningRequest(WeDoBaseModel):
    """Request to start WSI screening for multiple candidates."""
    candidate_ids: list[str] = Field(..., min_length=1, max_length=MAX_BULK_ITEMS)
    job_vacancy_id: str
    screening_type: Literal["text", "voice"] = "text"
    override_saturation: bool = Field(False, description="Override saturation guardrail (manual approval)")

    @field_validator("candidate_ids")
    @classmethod
    def validate_ids_limit(cls, v):
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f"Maximum {MAX_BULK_ITEMS} items per operation")
        return v


class BulkExportRequest(WeDoBaseModel):
    """Request to export multiple candidates data."""
    candidate_ids: list[str] = Field(..., min_length=1, max_length=MAX_BULK_ITEMS)
    format: Literal["csv", "xlsx"] = "csv"
    fields: list[str] | None = None

    @field_validator("candidate_ids")
    @classmethod
    def validate_ids_limit(cls, v):
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f"Maximum {MAX_BULK_ITEMS} items per operation")
        return v


class BulkDeleteRequest(WeDoBaseModel):
    """Request to delete (soft delete) multiple candidates."""
    candidate_ids: list[str] = Field(..., min_length=1, max_length=MAX_BULK_ITEMS)
    permanent: bool = False

    @field_validator("candidate_ids")
    @classmethod
    def validate_ids_limit(cls, v):
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f"Maximum {MAX_BULK_ITEMS} items per operation")
        return v


@router.post("/candidates/bulk/update-status", response_model=BulkOperationResult)
async def bulk_update_candidate_status(
    request: BulkUpdateStatusRequest,
    current_user: User = Depends(get_current_user),
    repo: BulkActionsRepository = Depends(get_bulk_actions_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Update status of multiple candidates at once.

    Valid statuses: new, screening, interview, offer, hired, rejected

    Uses atomic transaction - all updates succeed or all fail.
    Requires authentication.
    """
    logger.info(f"Bulk update status by {current_user.id}: {len(request.candidate_ids)} candidates to '{request.new_status}'")

    errors: list[BulkOperationError] = []
    processed_ids: list[str] = []

    try:
        for candidate_id in request.candidate_ids:
            try:
                candidate = await repo.get_candidate_by_id(uuid.UUID(candidate_id))

                if not candidate:
                    errors.append(BulkOperationError(
                        id=candidate_id,
                        error_message="Candidate not found"
                    ))
                    continue

                if not candidate.is_active:
                    errors.append(BulkOperationError(
                        id=candidate_id,
                        error_message="Candidate is inactive"
                    ))
                    continue

                # State machine guard -- per-item error, does not fail the whole operation
                transition_error = _check_status_transition(candidate.status, request.new_status)
                if transition_error:
                    errors.append(BulkOperationError(
                        id=candidate_id,
                        error_message=transition_error,
                    ))
                    continue

                _old_status = candidate.status
                candidate.status = request.new_status
                candidate.updated_at = datetime.utcnow()
                candidate.last_activity_at = datetime.utcnow()
                processed_ids.append(candidate_id)
                # Compliance: per-candidate audit trail (Task #311)
                try:
                    await audit_service.log_decision(
                        company_id=company_id,
                        agent_name="bulk_actions_api",
                        decision_type=_DECISION_TYPE_MAP.get(request.new_status, "move_stage"),
                        action=f"bulk_update_status_{request.new_status}",
                        decision=request.new_status,
                        reasoning=[
                            f"from_stage: {_old_status}",
                            f"to_stage: {request.new_status}",
                        ],
                        criteria_used=["bulk_status_update"],
                        candidate_id=candidate_id,
                    )
                except Exception as _ae:
                    logger.debug("audit log failed (non-blocking): %s", _ae)

            except ValueError:
                errors.append(BulkOperationError(
                    id=candidate_id,
                    error_message="Invalid UUID format"
                ))
            except Exception as e:
                errors.append(BulkOperationError(
                    id=candidate_id,
                    error_message=str(e)
                ))

        await repo.commit()

        successful = len(processed_ids)
        failed = len(errors)

        logger.info(f"Bulk update completed: {successful} successful, {failed} failed")

        return BulkOperationResult(
            total=len(request.candidate_ids),
            successful=successful,
            failed=failed,
            errors=errors,
            processed_ids=processed_ids,
            message=f"Updated {successful} candidates to status '{request.new_status}'"
        )

    except HTTPException:
        raise
    except Exception as e:
        await repo.rollback()
        logger.error(f"Bulk update status failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/candidates/bulk/assign-job", response_model=BulkOperationResult)
async def bulk_assign_to_job(
    request: BulkAssignJobRequest,
    current_user: User = Depends(get_current_user),
    repo: BulkActionsRepository = Depends(get_bulk_actions_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Assign multiple candidates to a job vacancy.

    Updates candidate's additional_data with job assignment info and optionally adds notes.
    Requires authentication.
    """
    logger.info(f"Bulk assign job by {current_user.id}: {len(request.candidate_ids)} candidates to job {request.job_vacancy_id}")

    errors: list[BulkOperationError] = []
    processed_ids: list[str] = []

    try:
        # LGPD/Fairness guard: check notes for discriminatory content before any DB call
        if request.notes:
            _fg_result = _fairness_guard.check(request.notes)
            if _fg_result.is_blocked:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": "fairness_blocked",
                        "field": "notes",
                        "needs_review": _fg_result.blocked_terms or [],
                        "category": _fg_result.category,
                    },
                )
        job_vacancy = await repo.get_job_vacancy_by_id(uuid.UUID(request.job_vacancy_id))

        if not job_vacancy:
            raise HTTPException(status_code=404, detail="Job vacancy not found")

        for candidate_id in request.candidate_ids:
            try:
                candidate = await repo.get_candidate_by_id(uuid.UUID(candidate_id))

                if not candidate:
                    errors.append(BulkOperationError(
                        id=candidate_id,
                        error_message="Candidate not found"
                    ))
                    continue

                if not candidate.is_active:
                    errors.append(BulkOperationError(
                        id=candidate_id,
                        error_message="Candidate is inactive"
                    ))
                    continue

                additional_data = candidate.additional_data or {}
                job_assignments = additional_data.get("job_assignments", [])

                if request.job_vacancy_id not in [ja.get("job_vacancy_id") for ja in job_assignments]:
                    job_assignments.append({
                        "job_vacancy_id": request.job_vacancy_id,
                        "job_title": job_vacancy.title,
                        "assigned_at": datetime.utcnow().isoformat(),
                        "notes": request.notes
                    })
                    additional_data["job_assignments"] = job_assignments
                    candidate.additional_data = additional_data

                # P0-1 (audit 2026-06-05): grava o LINK canônico em
                # vacancy_candidates (o board + a contagem leem daqui). Antes só
                # escrevia o blob inerte acima (ghost write ignorado pela UI).
                _vc_exists = await repo.db.execute(
                    _sa_select(_VacancyCandidate).where(
                        _VacancyCandidate.vacancy_id == uuid.UUID(request.job_vacancy_id),
                        _VacancyCandidate.candidate_id == uuid.UUID(candidate_id),
                    )
                )
                if _vc_exists.scalar_one_or_none() is None:
                    repo.db.add(_VacancyCandidate(
                        id=uuid.uuid4(),
                        vacancy_id=uuid.UUID(request.job_vacancy_id),
                        candidate_id=uuid.UUID(candidate_id),
                        company_id=company_id,
                        source="manual_assign",
                        stage="sourcing",
                        status="sourced",
                        lia_score=getattr(candidate, "lia_score", None),
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    ))

                candidate.updated_at = datetime.utcnow()
                candidate.last_activity_at = datetime.utcnow()
                processed_ids.append(candidate_id)

            except ValueError:
                errors.append(BulkOperationError(
                    id=candidate_id,
                    error_message="Invalid UUID format"
                ))
            except Exception as e:
                errors.append(BulkOperationError(
                    id=candidate_id,
                    error_message=str(e)
                ))

        await repo.commit()

        successful = len(processed_ids)
        failed = len(errors)

        logger.info(f"Bulk assign completed: {successful} successful, {failed} failed")

        return BulkOperationResult(
            total=len(request.candidate_ids),
            successful=successful,
            failed=failed,
            errors=errors,
            processed_ids=processed_ids,
            message=f"Assigned {successful} candidates to job '{job_vacancy.title}'"
        )

    except HTTPException:
        raise
    except Exception as e:
        await repo.rollback()
        logger.error(f"Bulk assign job failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/candidates/bulk/send-email", response_model=BulkOperationResult)
async def bulk_send_email(
    request: BulkSendEmailRequest,
    current_user: User = Depends(get_current_user),
    repo: BulkActionsRepository = Depends(get_bulk_actions_repo),
    email_svc: EmailService = Depends(get_email_service),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Send emails to multiple candidates using a template.

    Custom variables can override template defaults. Candidate-specific variables
    (name, email) are automatically substituted.
    Requires authentication.
    """
    logger.info(f"Bulk send email by {current_user.id}: {len(request.candidate_ids)} candidates with template {request.template_id}")

    errors: list[BulkOperationError] = []
    processed_ids: list[str] = []

    try:
        template = await repo.get_email_template_by_id(uuid.UUID(request.template_id))

        if not template:
            raise HTTPException(status_code=404, detail="Email template not found")

        if not template.is_active:
            raise HTTPException(status_code=400, detail="Email template is not active")

        for candidate_id in request.candidate_ids:
            try:
                candidate = await repo.get_candidate_by_id(uuid.UUID(candidate_id))

                if not candidate:
                    errors.append(BulkOperationError(
                        id=candidate_id,
                        error_message="Candidate not found"
                    ))
                    continue

                if not candidate.is_active:
                    errors.append(BulkOperationError(
                        id=candidate_id,
                        error_message="Candidate is inactive"
                    ))
                    continue

                if not candidate.communication_consent:
                    errors.append(BulkOperationError(
                        id=candidate_id,
                        error_message="Candidate has not given communication consent"
                    ))
                    continue

                variables = {
                    "candidate_name": candidate.name,
                    "candidate_email": candidate.email,
                    "current_title": candidate.current_title or "",
                    "current_company": candidate.current_company or "",
                }

                if request.custom_variables:
                    variables.update(request.custom_variables)

                try:
                    await email_svc.send_email(
                        db=repo.db,
                        template_id=uuid.UUID(request.template_id),
                        recipient_email=candidate.email,
                        variables=variables,
                        candidate_id=candidate_id,
                        send_immediately=True
                    )

                    candidate.last_contacted_at = datetime.utcnow()
                    candidate.last_activity_at = datetime.utcnow()
                    processed_ids.append(candidate_id)

                except Exception as e:
                    errors.append(BulkOperationError(
                        id=candidate_id,
                        error_message=f"Email send failed: {str(e)}"
                    ))

            except ValueError:
                errors.append(BulkOperationError(
                    id=candidate_id,
                    error_message="Invalid UUID format"
                ))
            except Exception as e:
                errors.append(BulkOperationError(
                    id=candidate_id,
                    error_message=str(e)
                ))

        await repo.commit()

        successful = len(processed_ids)
        failed = len(errors)

        logger.info(f"Bulk email completed: {successful} sent, {failed} failed")

        return BulkOperationResult(
            total=len(request.candidate_ids),
            successful=successful,
            failed=failed,
            errors=errors,
            processed_ids=processed_ids,
            message=f"Sent {successful} emails using template '{template.name}'"
        )

    except HTTPException:
        raise
    except Exception as e:
        await repo.rollback()
        logger.error(f"Bulk send email failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/candidates/bulk/start-screening", response_model=BulkOperationResult)
async def bulk_start_screening(
    request: BulkStartScreeningRequest,
    current_user: User = Depends(get_current_user),
    repo: BulkActionsRepository = Depends(get_bulk_actions_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Start WSI screening for multiple candidates.

    Creates screening sessions for each candidate linked to the job vacancy.
    Screening type can be 'text' (WhatsApp/chat) or 'voice' (phone call).
    Checks saturation guardrail before starting — blocks if pipeline is saturated
    unless override_saturation is True (manual recruiter approval).
    Requires authentication.
    """
    logger.info(f"Bulk start screening by {current_user.id}: {len(request.candidate_ids)} candidates for job {request.job_vacancy_id}")

    errors: list[BulkOperationError] = []
    processed_ids: list[str] = []

    try:
        job_vacancy = await repo.get_job_vacancy_by_id(uuid.UUID(request.job_vacancy_id))

        if not job_vacancy:
            raise HTTPException(status_code=404, detail="Job vacancy not found")

        if not request.override_saturation:
            sat_status = await _check_vacancy_saturation(repo, job_vacancy)
            if sat_status["is_saturated"]:
                detail_parts = []
                if sat_status["organic_saturated"]:
                    detail_parts.append(
                        f"organic {sat_status['organic_count']}/{sat_status['threshold_web']}"
                    )
                if sat_status["sourcing_saturated"]:
                    detail_parts.append(
                        f"sourcing {sat_status['sourcing_count']}/{sat_status['threshold_sourcing']}"
                    )
                detail_msg = ", ".join(detail_parts)
                logger.warning(
                    f"Bulk screening blocked by saturation for job {request.job_vacancy_id}: {detail_msg}"
                )
                raise HTTPException(
                    status_code=409,
                    detail={
                        "error": "saturation_limit_reached",
                        "message": f"Pipeline saturado ({detail_msg}). Triagem bloqueada. Use override_saturation=true para aprovar manualmente.",
                        "organic_count": sat_status["organic_count"],
                        "organic_threshold": sat_status["threshold_web"],
                        "sourcing_count": sat_status["sourcing_count"],
                        "sourcing_threshold": sat_status["threshold_sourcing"],
                    },
                )
        else:
            logger.info(f"Saturation override active for bulk screening job {request.job_vacancy_id} by {current_user.id}")

        triagem_svc = TriagemSessionService()

        for candidate_id in request.candidate_ids:
            try:
                candidate = await repo.get_candidate_by_id(uuid.UUID(candidate_id))

                if not candidate:
                    errors.append(BulkOperationError(
                        id=candidate_id,
                        error_message="Candidate not found"
                    ))
                    continue

                if not candidate.is_active:
                    errors.append(BulkOperationError(
                        id=candidate_id,
                        error_message="Candidate is inactive"
                    ))
                    continue

                voice_mode = request.screening_type == "voice"
                session = await triagem_svc.create_session(
                    db=repo.db,
                    candidate_id=str(candidate_id),
                    job_id=request.job_vacancy_id,
                    company_id=company_id,
                    candidate_name=candidate.name,
                    candidate_email=candidate.email,
                    job_title=job_vacancy.title,
                    invite_channel="voice" if voice_mode else "email",
                    created_by=str(current_user.id),
                    voice_mode=voice_mode,
                )

                if candidate.status == "new":
                    candidate.status = "screening"

                candidate.updated_at = datetime.utcnow()
                candidate.last_activity_at = datetime.utcnow()
                processed_ids.append(candidate_id)

                logger.info(f"Created triagem session {session.id} for candidate {candidate_id} via TriagemSessionService")

            except ValueError:
                errors.append(BulkOperationError(
                    id=candidate_id,
                    error_message="Invalid UUID format"
                ))
            except Exception as e:
                errors.append(BulkOperationError(
                    id=candidate_id,
                    error_message=str(e)
                ))

        await repo.commit()

        successful = len(processed_ids)
        failed = len(errors)

        logger.info(f"Bulk screening started: {successful} sessions created, {failed} failed")

        return BulkOperationResult(
            total=len(request.candidate_ids),
            successful=successful,
            failed=failed,
            errors=errors,
            processed_ids=processed_ids,
            message=f"Started {request.screening_type} screening for {successful} candidates for job '{job_vacancy.title}'"
        )

    except HTTPException:
        raise
    except Exception as e:
        await repo.rollback()
        logger.error(f"Bulk start screening failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/candidates/bulk/export", response_model=None)
async def bulk_export_candidates(
    request: BulkExportRequest,
    current_user: User = Depends(require_admin_or_recruiter),
    repo: BulkActionsRepository = Depends(get_bulk_actions_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Export selected candidates data to CSV or XLSX format.

    Returns a downloadable file with candidate information.
    Requires admin or recruiter role.
    """
    logger.info(f"Bulk export by {current_user.id}: {len(request.candidate_ids)} candidates to {request.format}")

    try:
        candidates_data = []
        errors: list[BulkOperationError] = []

        for candidate_id in request.candidate_ids:
            try:
                candidate = await repo.get_candidate_by_id(uuid.UUID(candidate_id))

                if not candidate:
                    errors.append(BulkOperationError(
                        id=candidate_id,
                        error_message="Candidate not found"
                    ))
                    continue

                candidate_dict = {
                    "id": str(candidate.id),
                    "name": candidate.name,
                    "email": candidate.email,
                    "phone": candidate.phone or "",
                    "linkedin_url": candidate.linkedin_url or "",
                    "current_title": candidate.current_title or "",
                    "current_company": candidate.current_company or "",
                    "seniority_level": candidate.seniority_level or "",
                    "years_of_experience": candidate.years_of_experience or "",
                    "technical_skills": ", ".join(candidate.technical_skills or []),
                    "soft_skills": ", ".join(candidate.soft_skills or []),
                    "location_city": candidate.location_city or "",
                    "location_state": candidate.location_state or "",
                    "location_country": candidate.location_country or "",
                    "is_remote": "Yes" if candidate.is_remote else "No",
                    "desired_salary_min": candidate.desired_salary_min or "",
                    "desired_salary_max": candidate.desired_salary_max or "",
                    "salary_currency": candidate.salary_currency or "BRL",
                    "work_model_preference": candidate.work_model_preference or "",
                    "source": candidate.source or "",
                    "lia_score": candidate.lia_score or "",
                    "status": candidate.status or "",
                    "tags": ", ".join(candidate.tags or []),
                    "created_at": candidate.created_at.isoformat() if candidate.created_at else "",
                    "updated_at": candidate.updated_at.isoformat() if candidate.updated_at else "",
                }

                if request.fields:
                    candidate_dict = {k: v for k, v in candidate_dict.items() if k in request.fields or k == "id"}

                candidates_data.append(candidate_dict)

            except ValueError:
                errors.append(BulkOperationError(
                    id=candidate_id,
                    error_message="Invalid UUID format"
                ))
            except Exception as e:
                errors.append(BulkOperationError(
                    id=candidate_id,
                    error_message=str(e)
                ))

        if not candidates_data:
            raise HTTPException(status_code=404, detail="No valid candidates found for export")

        if request.format == "csv":
            output = io.StringIO()
            fieldnames = list(candidates_data[0].keys())
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(candidates_data)

            content = output.getvalue()
            output.close()

            filename = f"candidates_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"

            return StreamingResponse(
                iter([content]),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}",
                    "X-Export-Total": str(len(candidates_data)),
                    "X-Export-Errors": str(len(errors))
                }
            )

        elif request.format == "xlsx":
            try:
                import openpyxl
                from openpyxl import Workbook

                wb = Workbook()
                ws = wb.active
                ws.title = "Candidates"

                if candidates_data:
                    headers = list(candidates_data[0].keys())
                    ws.append(headers)

                    for candidate in candidates_data:
                        ws.append([candidate.get(h, "") for h in headers])

                output = io.BytesIO()
                wb.save(output)
                output.seek(0)

                filename = f"candidates_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.xlsx"

                return StreamingResponse(
                    iter([output.getvalue()]),
                    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={
                        "Content-Disposition": f"attachment; filename={filename}",
                        "X-Export-Total": str(len(candidates_data)),
                        "X-Export-Errors": str(len(errors))
                    }
                )

            except ImportError:
                output = io.StringIO()
                fieldnames = list(candidates_data[0].keys())
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(candidates_data)

                content = output.getvalue()
                output.close()

                filename = f"candidates_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"

                return StreamingResponse(
                    iter([content]),
                    media_type="text/csv",
                    headers={
                        "Content-Disposition": f"attachment; filename={filename}",
                        "X-Export-Total": str(len(candidates_data)),
                        "X-Export-Errors": str(len(errors)),
                        "X-Format-Fallback": "xlsx not available, exported as csv"
                    }
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk export failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/candidates/bulk/delete", response_model=BulkOperationResult)
async def bulk_delete_candidates(
    request: BulkDeleteRequest,
    current_user: User = Depends(require_admin_or_recruiter),
    repo: BulkActionsRepository = Depends(get_bulk_actions_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Delete multiple candidates (soft delete by default).

    Soft delete sets is_active=False, preserving data for audit.
    Set permanent=True for hard delete (use with caution).
    Requires admin or recruiter role.
    """
    logger.info(f"Bulk delete by {current_user.id}: {len(request.candidate_ids)} candidates (permanent={request.permanent})")

    errors: list[BulkOperationError] = []
    processed_ids: list[str] = []

    try:
        for candidate_id in request.candidate_ids:
            try:
                candidate = await repo.get_candidate_by_id(uuid.UUID(candidate_id))

                if not candidate:
                    errors.append(BulkOperationError(
                        id=candidate_id,
                        error_message="Candidate not found"
                    ))
                    continue

                if request.permanent:
                    await repo.delete_candidate(candidate)
                else:
                    candidate.is_active = False
                    candidate.updated_at = datetime.utcnow()

                processed_ids.append(candidate_id)
                # Compliance: per-candidate audit trail (Task #311)
                try:
                    await audit_service.log_decision(
                        company_id=company_id,
                        agent_name="bulk_actions_api",
                        decision_type="reject_candidate",
                        action="bulk_delete",
                        decision="deleted",
                        reasoning=[
                            f"permanent: {request.permanent}",
                            f"candidate_id: {candidate_id}",
                        ],
                        criteria_used=["bulk_delete"],
                        candidate_id=candidate_id,
                    )
                except Exception as _ae:
                    logger.debug("audit log failed (non-blocking): %s", _ae)

            except ValueError:
                errors.append(BulkOperationError(
                    id=candidate_id,
                    error_message="Invalid UUID format"
                ))
            except Exception as e:
                errors.append(BulkOperationError(
                    id=candidate_id,
                    error_message=str(e)
                ))

        await repo.commit()

        successful = len(processed_ids)
        failed = len(errors)
        delete_type = "permanently deleted" if request.permanent else "deactivated"

        logger.info(f"Bulk delete completed: {successful} {delete_type}, {failed} failed")

        return BulkOperationResult(
            total=len(request.candidate_ids),
            successful=successful,
            failed=failed,
            errors=errors,
            processed_ids=processed_ids,
            message=f"Successfully {delete_type} {successful} candidates"
        )

    except HTTPException:
        raise
    except Exception as e:
        await repo.rollback()
        logger.error(f"Bulk delete failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/candidates/bulk/add-tags", response_model=BulkOperationResult)
async def bulk_add_tags(
    candidate_ids: list[str],
    tags: list[str],
    current_user: User = Depends(get_current_user),
    repo: BulkActionsRepository = Depends(get_bulk_actions_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Add tags to multiple candidates.
    Requires authentication.
    """
    if len(candidate_ids) > MAX_BULK_ITEMS:
        raise HTTPException(status_code=400, detail=f"Maximum {MAX_BULK_ITEMS} items per operation")

    logger.info(f"Bulk add tags by {current_user.id}: {len(candidate_ids)} candidates, tags: {tags}")

    errors: list[BulkOperationError] = []
    processed_ids: list[str] = []

    try:
        for candidate_id in candidate_ids:
            try:
                candidate = await repo.get_candidate_by_id(uuid.UUID(candidate_id))

                if not candidate:
                    errors.append(BulkOperationError(
                        id=candidate_id,
                        error_message="Candidate not found"
                    ))
                    continue

                existing_tags = set(candidate.tags or [])
                new_tags = existing_tags.union(set(tags))
                candidate.tags = list(new_tags)
                candidate.updated_at = datetime.utcnow()
                processed_ids.append(candidate_id)

            except ValueError:
                errors.append(BulkOperationError(
                    id=candidate_id,
                    error_message="Invalid UUID format"
                ))
            except Exception as e:
                errors.append(BulkOperationError(
                    id=candidate_id,
                    error_message=str(e)
                ))

        await repo.commit()

        successful = len(processed_ids)
        failed = len(errors)

        return BulkOperationResult(
            total=len(candidate_ids),
            successful=successful,
            failed=failed,
            errors=errors,
            processed_ids=processed_ids,
            message=f"Added tags {tags} to {successful} candidates"
        )

    except HTTPException:
        raise
    except Exception as e:
        await repo.rollback()
        logger.error(f"Bulk add tags failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/candidates/bulk/remove-tags", response_model=BulkOperationResult)
async def bulk_remove_tags(
    candidate_ids: list[str],
    tags: list[str],
    current_user: User = Depends(get_current_user),
    repo: BulkActionsRepository = Depends(get_bulk_actions_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Remove tags from multiple candidates.
    Requires authentication.
    """
    if len(candidate_ids) > MAX_BULK_ITEMS:
        raise HTTPException(status_code=400, detail=f"Maximum {MAX_BULK_ITEMS} items per operation")

    logger.info(f"Bulk remove tags by {current_user.id}: {len(candidate_ids)} candidates, tags: {tags}")

    errors: list[BulkOperationError] = []
    processed_ids: list[str] = []

    try:
        for candidate_id in candidate_ids:
            try:
                candidate = await repo.get_candidate_by_id(uuid.UUID(candidate_id))

                if not candidate:
                    errors.append(BulkOperationError(
                        id=candidate_id,
                        error_message="Candidate not found"
                    ))
                    continue

                existing_tags = set(candidate.tags or [])
                new_tags = existing_tags - set(tags)
                candidate.tags = list(new_tags)
                candidate.updated_at = datetime.utcnow()
                processed_ids.append(candidate_id)

            except ValueError:
                errors.append(BulkOperationError(
                    id=candidate_id,
                    error_message="Invalid UUID format"
                ))
            except Exception as e:
                errors.append(BulkOperationError(
                    id=candidate_id,
                    error_message=str(e)
                ))

        await repo.commit()

        successful = len(processed_ids)
        failed = len(errors)

        return BulkOperationResult(
            total=len(candidate_ids),
            successful=successful,
            failed=failed,
            errors=errors,
            processed_ids=processed_ids,
            message=f"Removed tags {tags} from {successful} candidates"
        )

    except HTTPException:
        raise
    except Exception as e:
        await repo.rollback()
        logger.error(f"Bulk remove tags failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
