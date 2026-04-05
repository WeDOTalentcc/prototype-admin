"""
Bulk Actions API endpoints for mass operations on candidates and job vacancies.
Allows performing actions on multiple records at once with transactional safety.
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import Optional, List, Literal
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
import logging
import uuid
import io
import csv

from sqlalchemy import func, and_, not_

from app.models.candidate import Candidate, VacancyCandidate
from app.models.job_vacancy import JobVacancy
from app.models.email_template import EmailTemplate
from app.models.company import CompanyProfile
from app.domains.communication.services.email_service import email_service
from app.core.database import get_db
from app.auth.dependencies import get_current_user, require_admin_or_recruiter
from app.auth.models import User, UserRole

logger = logging.getLogger(__name__)

router = APIRouter()

MAX_BULK_ITEMS = 100
VALID_CANDIDATE_STATUSES = ["new", "screening", "interview", "offer", "hired", "rejected"]

EXCLUDED_STATUSES = ('rejected', 'declined', 'withdrawn')
ORGANIC_ORIGINS = ('web', 'whatsapp')
SOURCING_ORIGINS = ('sourcing', 'ats')
DEFAULT_SATURATION_THRESHOLD = 20
DEFAULT_UNLOCK_INCREMENT = 10
DEFAULT_UNLOCK_HOURS = 24


async def _check_vacancy_saturation(db: AsyncSession, vacancy: JobVacancy) -> dict:
    from datetime import timedelta
    company = None
    try:
        result = await db.execute(
            select(CompanyProfile).where(CompanyProfile.id == vacancy.company_id)
        )
        company = result.scalar_one_or_none()
    except Exception:
        pass
    if not company:
        result2 = await db.execute(
            select(CompanyProfile).where(CompanyProfile.is_default == True).limit(1)
        )
        company = result2.scalar_one_or_none()

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

    active_filter = and_(
        VacancyCandidate.vacancy_id == vacancy.id,
        not_(VacancyCandidate.status.in_(EXCLUDED_STATUSES)),
    )

    channel_result = await db.execute(
        select(
            func.count(VacancyCandidate.id).filter(
                VacancyCandidate.origin.in_(ORGANIC_ORIGINS) | VacancyCandidate.origin.is_(None)
            ).label("organic"),
            func.count(VacancyCandidate.id).filter(
                VacancyCandidate.origin.in_(SOURCING_ORIGINS)
            ).label("sourcing"),
        ).where(active_filter)
    )
    row = channel_result.one()
    organic_count = row.organic or 0
    sourcing_count = row.sourcing or 0

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
    errors: List[BulkOperationError] = []
    processed_ids: List[str] = []
    message: str = ""


class BulkUpdateStatusRequest(BaseModel):
    """Request to update status of multiple candidates."""
    candidate_ids: List[str] = Field(..., min_length=1, max_length=MAX_BULK_ITEMS)
    new_status: str = Field(..., description="Status: new, screening, interview, offer, hired, rejected")
    
    @field_validator('new_status')
    @classmethod
    def validate_status(cls, v):
        if v not in VALID_CANDIDATE_STATUSES:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(VALID_CANDIDATE_STATUSES)}")
        return v
    
    @field_validator('candidate_ids')
    @classmethod
    def validate_ids_limit(cls, v):
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f"Maximum {MAX_BULK_ITEMS} items per operation")
        return v


class BulkAssignJobRequest(BaseModel):
    """Request to assign multiple candidates to a job vacancy."""
    candidate_ids: List[str] = Field(..., min_length=1, max_length=MAX_BULK_ITEMS)
    job_vacancy_id: str
    notes: Optional[str] = None
    
    @field_validator('candidate_ids')
    @classmethod
    def validate_ids_limit(cls, v):
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f"Maximum {MAX_BULK_ITEMS} items per operation")
        return v


class BulkSendEmailRequest(BaseModel):
    """Request to send emails to multiple candidates."""
    candidate_ids: List[str] = Field(..., min_length=1, max_length=MAX_BULK_ITEMS)
    template_id: str
    custom_variables: Optional[dict] = None
    
    @field_validator('candidate_ids')
    @classmethod
    def validate_ids_limit(cls, v):
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f"Maximum {MAX_BULK_ITEMS} items per operation")
        return v


class BulkStartScreeningRequest(BaseModel):
    """Request to start WSI screening for multiple candidates."""
    candidate_ids: List[str] = Field(..., min_length=1, max_length=MAX_BULK_ITEMS)
    job_vacancy_id: str
    screening_type: Literal["text", "voice"] = "text"
    override_saturation: bool = Field(False, description="Override saturation guardrail (manual approval)")
    
    @field_validator('candidate_ids')
    @classmethod
    def validate_ids_limit(cls, v):
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f"Maximum {MAX_BULK_ITEMS} items per operation")
        return v


class BulkExportRequest(BaseModel):
    """Request to export multiple candidates data."""
    candidate_ids: List[str] = Field(..., min_length=1, max_length=MAX_BULK_ITEMS)
    format: Literal["csv", "xlsx"] = "csv"
    fields: Optional[List[str]] = None
    
    @field_validator('candidate_ids')
    @classmethod
    def validate_ids_limit(cls, v):
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f"Maximum {MAX_BULK_ITEMS} items per operation")
        return v


class BulkDeleteRequest(BaseModel):
    """Request to delete (soft delete) multiple candidates."""
    candidate_ids: List[str] = Field(..., min_length=1, max_length=MAX_BULK_ITEMS)
    permanent: bool = False
    
    @field_validator('candidate_ids')
    @classmethod
    def validate_ids_limit(cls, v):
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f"Maximum {MAX_BULK_ITEMS} items per operation")
        return v


@router.post("/candidates/bulk/update-status", response_model=BulkOperationResult)
async def bulk_update_candidate_status(
    request: BulkUpdateStatusRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update status of multiple candidates at once.
    
    Valid statuses: new, screening, interview, offer, hired, rejected
    
    Uses atomic transaction - all updates succeed or all fail.
    Requires authentication.
    """
    logger.info(f"Bulk update status by {current_user.email}: {len(request.candidate_ids)} candidates to '{request.new_status}'")
    
    errors: List[BulkOperationError] = []
    processed_ids: List[str] = []
    
    try:
        for candidate_id in request.candidate_ids:
            try:
                result = await db.execute(
                    select(Candidate).where(Candidate.id == uuid.UUID(candidate_id))
                )
                candidate = result.scalar_one_or_none()
                
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
                
                candidate.status = request.new_status
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
        
        await db.commit()
        
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
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Bulk update status failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/candidates/bulk/assign-job", response_model=BulkOperationResult)
async def bulk_assign_to_job(
    request: BulkAssignJobRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Assign multiple candidates to a job vacancy.
    
    Updates candidate's additional_data with job assignment info and optionally adds notes.
    Requires authentication.
    """
    logger.info(f"Bulk assign job by {current_user.email}: {len(request.candidate_ids)} candidates to job {request.job_vacancy_id}")
    
    errors: List[BulkOperationError] = []
    processed_ids: List[str] = []
    
    try:
        result = await db.execute(
            select(JobVacancy).where(JobVacancy.id == uuid.UUID(request.job_vacancy_id))
        )
        job_vacancy = result.scalar_one_or_none()
        
        if not job_vacancy:
            raise HTTPException(status_code=404, detail="Job vacancy not found")
        
        for candidate_id in request.candidate_ids:
            try:
                result = await db.execute(
                    select(Candidate).where(Candidate.id == uuid.UUID(candidate_id))
                )
                candidate = result.scalar_one_or_none()
                
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
        
        await db.commit()
        
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
        await db.rollback()
        logger.error(f"Bulk assign job failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/candidates/bulk/send-email", response_model=BulkOperationResult)
async def bulk_send_email(
    request: BulkSendEmailRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Send emails to multiple candidates using a template.
    
    Custom variables can override template defaults. Candidate-specific variables
    (name, email) are automatically substituted.
    Requires authentication.
    """
    logger.info(f"Bulk send email by {current_user.email}: {len(request.candidate_ids)} candidates with template {request.template_id}")
    
    errors: List[BulkOperationError] = []
    processed_ids: List[str] = []
    
    try:
        result = await db.execute(
            select(EmailTemplate).where(EmailTemplate.id == uuid.UUID(request.template_id))
        )
        template = result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(status_code=404, detail="Email template not found")
        
        if not template.is_active:
            raise HTTPException(status_code=400, detail="Email template is not active")
        
        for candidate_id in request.candidate_ids:
            try:
                result = await db.execute(
                    select(Candidate).where(Candidate.id == uuid.UUID(candidate_id))
                )
                candidate = result.scalar_one_or_none()
                
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
                    await email_service.send_email(
                        db=db,
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
        
        await db.commit()
        
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
        await db.rollback()
        logger.error(f"Bulk send email failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/candidates/bulk/start-screening", response_model=BulkOperationResult)
async def bulk_start_screening(
    request: BulkStartScreeningRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Start WSI screening for multiple candidates.
    
    Creates screening sessions for each candidate linked to the job vacancy.
    Screening type can be 'text' (WhatsApp/chat) or 'voice' (phone call).
    Checks saturation guardrail before starting — blocks if pipeline is saturated
    unless override_saturation is True (manual recruiter approval).
    Requires authentication.
    """
    logger.info(f"Bulk start screening by {current_user.email}: {len(request.candidate_ids)} candidates for job {request.job_vacancy_id}")
    
    errors: List[BulkOperationError] = []
    processed_ids: List[str] = []
    
    try:
        result = await db.execute(
            select(JobVacancy).where(JobVacancy.id == uuid.UUID(request.job_vacancy_id))
        )
        job_vacancy = result.scalar_one_or_none()
        
        if not job_vacancy:
            raise HTTPException(status_code=404, detail="Job vacancy not found")
        
        if not request.override_saturation:
            sat_status = await _check_vacancy_saturation(db, job_vacancy)
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
            logger.info(f"Saturation override active for bulk screening job {request.job_vacancy_id} by {current_user.email}")
        
        for candidate_id in request.candidate_ids:
            try:
                result = await db.execute(
                    select(Candidate).where(Candidate.id == uuid.UUID(candidate_id))
                )
                candidate = result.scalar_one_or_none()
                
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
                screening_sessions = additional_data.get("screening_sessions", [])
                
                screening_session = {
                    "session_id": str(uuid.uuid4()),
                    "job_vacancy_id": request.job_vacancy_id,
                    "job_title": job_vacancy.title,
                    "screening_type": request.screening_type,
                    "status": "pending",
                    "created_at": datetime.utcnow().isoformat()
                }
                screening_sessions.append(screening_session)
                additional_data["screening_sessions"] = screening_sessions
                candidate.additional_data = additional_data
                
                if candidate.status == "new":
                    candidate.status = "screening"
                
                candidate.updated_at = datetime.utcnow()
                candidate.last_activity_at = datetime.utcnow()
                processed_ids.append(candidate_id)
                
                logger.info(f"Created screening session {screening_session['session_id']} for candidate {candidate_id}")
                
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
        
        await db.commit()
        
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
        await db.rollback()
        logger.error(f"Bulk start screening failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/candidates/bulk/export")
async def bulk_export_candidates(
    request: BulkExportRequest,
    current_user: User = Depends(require_admin_or_recruiter),
    db: AsyncSession = Depends(get_db)
):
    """
    Export selected candidates data to CSV or XLSX format.
    
    Returns a downloadable file with candidate information.
    Requires admin or recruiter role.
    """
    logger.info(f"Bulk export by {current_user.email}: {len(request.candidate_ids)} candidates to {request.format}")
    
    try:
        candidates_data = []
        errors: List[BulkOperationError] = []
        
        for candidate_id in request.candidate_ids:
            try:
                result = await db.execute(
                    select(Candidate).where(Candidate.id == uuid.UUID(candidate_id))
                )
                candidate = result.scalar_one_or_none()
                
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
    db: AsyncSession = Depends(get_db)
):
    """
    Delete multiple candidates (soft delete by default).
    
    Soft delete sets is_active=False, preserving data for audit.
    Set permanent=True for hard delete (use with caution).
    Requires admin or recruiter role.
    """
    logger.info(f"Bulk delete by {current_user.email}: {len(request.candidate_ids)} candidates (permanent={request.permanent})")
    
    errors: List[BulkOperationError] = []
    processed_ids: List[str] = []
    
    try:
        for candidate_id in request.candidate_ids:
            try:
                result = await db.execute(
                    select(Candidate).where(Candidate.id == uuid.UUID(candidate_id))
                )
                candidate = result.scalar_one_or_none()
                
                if not candidate:
                    errors.append(BulkOperationError(
                        id=candidate_id,
                        error_message="Candidate not found"
                    ))
                    continue
                
                if request.permanent:
                    await db.delete(candidate)
                else:
                    candidate.is_active = False
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
        
        await db.commit()
        
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
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Bulk delete failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/candidates/bulk/add-tags", response_model=BulkOperationResult)
async def bulk_add_tags(
    candidate_ids: List[str],
    tags: List[str],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Add tags to multiple candidates.
    Requires authentication.
    """
    if len(candidate_ids) > MAX_BULK_ITEMS:
        raise HTTPException(status_code=400, detail=f"Maximum {MAX_BULK_ITEMS} items per operation")
    
    logger.info(f"Bulk add tags by {current_user.email}: {len(candidate_ids)} candidates, tags: {tags}")
    
    errors: List[BulkOperationError] = []
    processed_ids: List[str] = []
    
    try:
        for candidate_id in candidate_ids:
            try:
                result = await db.execute(
                    select(Candidate).where(Candidate.id == uuid.UUID(candidate_id))
                )
                candidate = result.scalar_one_or_none()
                
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
        
        await db.commit()
        
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
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Bulk add tags failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/candidates/bulk/remove-tags", response_model=BulkOperationResult)
async def bulk_remove_tags(
    candidate_ids: List[str],
    tags: List[str],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Remove tags from multiple candidates.
    Requires authentication.
    """
    if len(candidate_ids) > MAX_BULK_ITEMS:
        raise HTTPException(status_code=400, detail=f"Maximum {MAX_BULK_ITEMS} items per operation")
    
    logger.info(f"Bulk remove tags by {current_user.email}: {len(candidate_ids)} candidates, tags: {tags}")
    
    errors: List[BulkOperationError] = []
    processed_ids: List[str] = []
    
    try:
        for candidate_id in candidate_ids:
            try:
                result = await db.execute(
                    select(Candidate).where(Candidate.id == uuid.UUID(candidate_id))
                )
                candidate = result.scalar_one_or_none()
                
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
        
        await db.commit()
        
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
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Bulk remove tags failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
