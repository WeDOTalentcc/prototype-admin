"""
Interview Scheduling API endpoints.
Integrated with Microsoft Graph API for Teams meetings and calendar sync.

Provides full CRUD operations for interview management:
- Create interview appointments with automatic Teams meeting links
- Sync with Outlook calendar and send invites
- List/filter interviews
- Update interview details
- Cancel interviews
- Generate ICS calendar files
"""
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, EmailStr

from app.domains.interview_scheduling.dependencies import get_scheduling_repo
from app.domains.interview_scheduling.repositories.scheduling_repository import SchedulingRepository
from app.domains.interview_scheduling.services.scheduling_service import scheduling_service
from app.shared.compliance.audit_service import AuditService, get_audit_service
from app.shared.pii_masking import get_masked_logger
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item
from app.shared.errors import LIAError

logger = get_masked_logger(__name__)

router = APIRouter(prefix="/scheduling", tags=["scheduling"])


class CreateInterviewRequest(WeDoBaseModel):
    """Request to create a new interview."""
    candidate_id: str
    candidate_name: str
    candidate_email: EmailStr
    interviewer_name: str
    interviewer_email: EmailStr
    start_time: datetime
    duration_minutes: int = 60
    interview_type: str = "technical"
    interview_mode: str = "video"
    job_title: str | None = None
    job_vacancy_id: str | None = None
    location: str | None = None
    notes: str | None = None
    additional_interviewers: list[dict[str, str]] | None = None


class UpdateInterviewRequest(WeDoBaseModel):
    """Request to update an interview."""
    start_time: datetime | None = None
    duration_minutes: int | None = None
    interview_type: str | None = None
    interview_mode: str | None = None
    location: str | None = None
    notes: str | None = None
    interviewer_name: str | None = None
    interviewer_email: EmailStr | None = None
    additional_interviewers: list[dict[str, str]] | None = None
    status: str | None = None
    confirmation_status: str | None = None


class InterviewResponse(BaseModel):
    """Response with interview details."""
    id: str
    title: str
    candidate_id: str | None
    candidate_name: str
    candidate_email: str
    interviewer_name: str
    interviewer_email: str
    additional_interviewers: list[dict[str, str]]
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    interview_type: str
    interview_mode: str
    location: str | None
    meeting_url: str | None
    job_title: str | None
    job_vacancy_id: str | None
    status: str
    confirmation_status: str
    notes: str | None
    is_synced_to_calendar: bool | None = False
    created_at: datetime
    updated_at: datetime


class InterviewListResponse(BaseModel):
    """Response for listing interviews."""
    total: int
    items: list[InterviewResponse]
    calendar_status: str = "Funcional - Aguardando Configuração Calendar"


def interview_to_response(interview) -> InterviewResponse:
    """Convert Interview model to response."""
    return InterviewResponse(
        id=str(interview.id),
        title=interview.title,
        candidate_id=str(interview.candidate_id) if interview.candidate_id else None,
        candidate_name=interview.candidate_name,
        candidate_email=interview.candidate_email,
        interviewer_name=interview.interviewer_name,
        interviewer_email=interview.interviewer_email,
        additional_interviewers=interview.additional_interviewers or [],
        start_time=interview.start_time,
        end_time=interview.end_time,
        duration_minutes=interview.duration_minutes,
        interview_type=interview.interview_type,
        interview_mode=interview.interview_mode,
        location=interview.location,
        meeting_url=interview.meeting_url,
        job_title=interview.job_title,
        job_vacancy_id=str(interview.job_vacancy_id) if interview.job_vacancy_id else None,
        status=interview.status,
        confirmation_status=interview.confirmation_status,
        notes=interview.description,
        is_synced_to_calendar=interview.is_synced_to_calendar,
        created_at=interview.created_at,
        updated_at=interview.updated_at
    )


@router.post("/interviews", response_model=InterviewResponse)
async def create_interview(
    request: CreateInterviewRequest,
    repo: SchedulingRepository = Depends(get_scheduling_repo),
    audit_svc: AuditService = Depends(get_audit_service),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Create a new interview appointment.

    Current Status: Funcional - Aguardando Configuração Calendar
    - Interview is saved to database
    - ICS file can be generated for download
    - Calendar sync requires Microsoft Graph or Google Calendar configuration
    """
    try:
        interview = await scheduling_service.create_interview(
            db=repo.db,
            candidate_id=request.candidate_id,
            candidate_name=request.candidate_name,
            candidate_email=request.candidate_email,
            interviewer_name=request.interviewer_name,
            interviewer_email=request.interviewer_email,
            start_time=request.start_time,
            duration_minutes=request.duration_minutes,
            interview_type=request.interview_type,
            interview_mode=request.interview_mode,
            job_title=request.job_title,
            job_vacancy_id=request.job_vacancy_id,
            location=request.location,
            notes=request.notes,
            additional_interviewers=request.additional_interviewers,
            created_by="api"
        )

        try:
            await audit_svc.log_decision(
                company_id=None,
                agent_name="scheduling_module",
                decision_type="schedule_interview",
                action="create_interview",
                decision="scheduled",
                reasoning=[
                    "Interview created via scheduling API",
                    f"Type: {request.interview_type}",
                    f"Scheduled: {request.start_time.isoformat() if request.start_time else 'N/A'}",
                    f"Duration: {request.duration_minutes}min",
                    "Calendar sync: pending",
                ],
                criteria_used=["candidate_availability", "interviewer_availability", "calendar_slot", "interview_type"],
                candidate_id=request.candidate_id,
                job_vacancy_id=request.job_vacancy_id,
                human_review_required=False,
            )
        except Exception as audit_err:
            logger.warning(f"Audit log failed for create_interview: {audit_err}")

        return interview_to_response(interview)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create interview: {e}")
        raise LIAError(message="Erro interno do servidor")


class CreateInterviewWithTeamsRequest(WeDoBaseModel):
    """Request to create an interview with Microsoft Teams meeting."""
    organizer_email: EmailStr
    candidate_id: str
    candidate_name: str
    candidate_email: EmailStr
    start_time: datetime
    duration_minutes: int = 60
    interview_type: str = "technical"
    job_title: str | None = None
    job_vacancy_id: str | None = None
    notes: str | None = None
    additional_attendees: list[dict[str, str]] | None = None
    send_calendar_invites: bool = True
    interviewer_name: str | None = None


class InterviewWithTeamsResponse(BaseModel):
    """Response for interview creation with Teams meeting."""
    interview: InterviewResponse
    teams_metadata: dict[str, Any]


@router.post("/interviews/with-teams", response_model=InterviewWithTeamsResponse)
async def create_interview_with_teams(
    request: CreateInterviewWithTeamsRequest,
    repo: SchedulingRepository = Depends(get_scheduling_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Create an interview with Microsoft Teams meeting.

    This endpoint:
    1. Creates a Teams meeting with auto-generated join link
    2. Sends calendar invites to all attendees via Outlook
    3. Stores the interview in the database

    Requires Microsoft Graph configuration (AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID).
    If not configured, falls back to standard interview creation with ICS file available.

    Returns:
        InterviewWithTeamsResponse containing:
        - interview: Full interview details
        - teams_metadata: Teams meeting info (join URL, status, etc.)
    """
    try:
        interview, teams_metadata = await scheduling_service.create_interview_with_teams(
            db=repo.db,
            organizer_email=request.organizer_email,
            candidate_id=request.candidate_id,
            candidate_name=request.candidate_name,
            candidate_email=request.candidate_email,
            start_time=request.start_time,
            duration_minutes=request.duration_minutes,
            interview_type=request.interview_type,
            job_title=request.job_title,
            job_vacancy_id=request.job_vacancy_id,
            company_id=company_id,
            notes=request.notes,
            additional_attendees=request.additional_attendees,
            send_calendar_invites=request.send_calendar_invites,
            interviewer_name=request.interviewer_name
        )

        return InterviewWithTeamsResponse(
            interview=interview_to_response(interview),
            teams_metadata=teams_metadata
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create interview with Teams: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.get("/interviews", response_model=InterviewListResponse)
async def list_interviews(
    candidate_id: str | None = Query(None, description="Filter by candidate ID"),
    vacancy_id: str | None = Query(None, description="Filter by job vacancy ID"),
    interviewer_email: str | None = Query(None, description="Filter by interviewer email"),
    status: str | None = Query(None, description="Filter by status"),
    from_date: datetime | None = Query(None, description="Filter from this date"),
    to_date: datetime | None = Query(None, description="Filter to this date"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    repo: SchedulingRepository = Depends(get_scheduling_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    List interviews with optional filters.
    """
    try:
        interviews, total = await scheduling_service.list_interviews(
            db=repo.db,
            candidate_id=candidate_id,
            vacancy_id=vacancy_id,
            interviewer_email=interviewer_email,
            status=status,
            from_date=from_date,
            to_date=to_date,
            skip=skip,
            limit=limit
        )

        return InterviewListResponse(
            total=total,
            items=[interview_to_response(i) for i in interviews]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list interviews: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.get("/interviews/{interview_id}", response_model=InterviewResponse)
async def get_interview(
    interview_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    repo: SchedulingRepository = Depends(get_scheduling_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get a specific interview by ID.
    """
    try:
        interview = await scheduling_service.get_interview(repo.db, interview_id)

        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")

        return interview_to_response(interview)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get interview: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.put("/interviews/{interview_id}", response_model=InterviewResponse)
async def update_interview(
    interview_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    request: UpdateInterviewRequest,
    repo: SchedulingRepository = Depends(get_scheduling_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Update an existing interview.

    Only provided fields will be updated.
    """
    try:
        update_data = request.model_dump(exclude_unset=True)

        interview = await scheduling_service.update_interview(
            db=repo.db,
            interview_id=interview_id,
            **update_data
        )

        return interview_to_response(interview)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update interview: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.delete("/interviews/{interview_id}", response_model=None)
async def cancel_interview(
    interview_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    reason: str | None = Query(None, description="Cancellation reason"),
    repo: SchedulingRepository = Depends(get_scheduling_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Cancel an interview.

    The interview is not deleted but marked as cancelled.
    """
    try:
        interview = await scheduling_service.cancel_interview(
            db=repo.db,
            interview_id=interview_id,
            cancellation_reason=reason
        )

        return {
            "success": True,
            "message": "Entrevista cancelada com sucesso",
            "interview_id": str(interview.id),
            "status": interview.status,
            "cancelled_at": interview.cancelled_at.isoformat() if interview.cancelled_at else None
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel interview: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.get("/interviews/{interview_id}/ics", response_model=None)
async def download_interview_ics(
    interview_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    repo: SchedulingRepository = Depends(get_scheduling_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Download ICS calendar file for an interview.

    This allows candidates and interviewers to add the interview to their calendars.
    """
    try:
        interview = await scheduling_service.get_interview(repo.db, interview_id)

        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")

        ics_content = scheduling_service.generate_ics_content(interview)

        filename = f"entrevista_{interview.candidate_name.replace(' ', '_')}_{interview.start_time.strftime('%Y%m%d')}.ics"

        return Response(
            content=ics_content,
            media_type="text/calendar",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate ICS: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.get("/status", response_model=None)
async def get_scheduling_status(company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get the current status of the scheduling system.
    """
    return await scheduling_service.get_calendar_status()


class SendInterviewInviteRequest(WeDoBaseModel):
    """Request to send an interview invite with Bookings link."""
    candidate_id: str
    candidate_email: EmailStr
    candidate_name: str
    job_title: str
    bookings_link: str
    company_name: str | None = None
    recruiter_name: str | None = None
    interviewer_name: str | None = None
    interview_format: str = "video"
    duration_minutes: int = 60


class SendInterviewInviteResponse(BaseModel):
    """Response for interview invite sending."""
    success: bool
    message: str
    email_log_id: str | None = None
    candidate_email: str | None = None
    template_used: str | None = None
    error: str | None = None


@router.post("/interviews/send-invite", response_model=SendInterviewInviteResponse)
async def send_interview_invite(
    request: SendInterviewInviteRequest,
    repo: SchedulingRepository = Depends(get_scheduling_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Send an interview invite email with a Bookings link.

    This endpoint sends an email to the candidate with a link to schedule their interview
    through Microsoft Bookings or similar scheduling service.

    Uses the template with situation='interview_invite' from the database.

    Template Variables:
    - candidato_nome: Candidate name
    - vaga: Job title
    - empresa_nome: Company name
    - recrutador_nome: Recruiter name
    - formato_entrevista: Interview format (video, in_person, phone)
    - duracao_entrevista: Duration in minutes
    - entrevistador_nome: Interviewer name
    - link_calendario: Bookings link for scheduling

    Returns:
        SendInterviewInviteResponse with success status and details
    """
    try:
        result = await scheduling_service.send_interview_invite(
            db=repo.db,
            candidate_id=request.candidate_id,
            candidate_email=request.candidate_email,
            candidate_name=request.candidate_name,
            job_title=request.job_title,
            bookings_link=request.bookings_link,
            company_id=company_id,
            company_name=request.company_name,
            recruiter_name=request.recruiter_name,
            interviewer_name=request.interviewer_name,
            interview_format=request.interview_format,
            duration_minutes=request.duration_minutes
        )

        return SendInterviewInviteResponse(
            success=result.get("success", False),
            message=result.get("message", ""),
            email_log_id=result.get("email_log_id"),
            candidate_email=result.get("candidate_email"),
            template_used=result.get("template_used"),
            error=result.get("error")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send interview invite: {e}")
        raise LIAError(message="Erro interno do servidor")


class SendInterviewConfirmationRequest(WeDoBaseModel):
    """Request to send an interview confirmation with meeting link."""
    candidate_id: str
    candidate_email: EmailStr
    candidate_name: str
    job_title: str
    interview_datetime: datetime
    interview_link: str
    company_name: str | None = None
    recruiter_name: str | None = None
    interviewer_name: str | None = None
    interview_format: str = "video"
    duration_minutes: int = 60


@router.post("/interviews/send-confirmation", response_model=SendInterviewInviteResponse)
async def send_interview_confirmation(
    request: SendInterviewConfirmationRequest,
    repo: SchedulingRepository = Depends(get_scheduling_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Send an interview confirmation email with meeting link.

    This endpoint sends a confirmation email to the candidate with the interview details
    and meeting link (Teams, Zoom, etc.).

    Uses the template with situation='interview_confirmed' from the database.

    Template Variables:
    - candidato_nome: Candidate name
    - vaga: Job title
    - empresa_nome: Company name
    - recrutador_nome: Recruiter name
    - data_entrevista: Interview date
    - horario_entrevista: Interview time
    - duracao_entrevista: Duration in minutes
    - formato_entrevista: Interview format
    - entrevistador_nome: Interviewer name
    - link_entrevista: Meeting link

    Returns:
        SendInterviewInviteResponse with success status and details
    """
    try:
        result = await scheduling_service.send_interview_confirmation(
            db=repo.db,
            candidate_id=request.candidate_id,
            candidate_email=request.candidate_email,
            candidate_name=request.candidate_name,
            job_title=request.job_title,
            interview_datetime=request.interview_datetime,
            interview_link=request.interview_link,
            company_id=company_id,
            company_name=request.company_name,
            recruiter_name=request.recruiter_name,
            interviewer_name=request.interviewer_name,
            interview_format=request.interview_format,
            duration_minutes=request.duration_minutes
        )

        return SendInterviewInviteResponse(
            success=result.get("success", False),
            message=result.get("message", ""),
            email_log_id=result.get("email_log_id"),
            candidate_email=result.get("candidate_email"),
            template_used=result.get("template_used"),
            error=result.get("error")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send interview confirmation: {e}")
        raise LIAError(message="Erro interno do servidor")

reorder_collection_before_item(router)
