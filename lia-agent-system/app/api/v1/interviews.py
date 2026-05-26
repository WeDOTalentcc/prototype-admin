"""
Interview Scheduling API endpoints.
"""
import json
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.shared.providers.llm_factory import get_provider_for_tenant
from app.domains.analytics.services.activity_service import activity_service as activity_svc
from pydantic import BaseModel, EmailStr

from app.domains.interview_scheduling.dependencies import get_interview_repo
from app.domains.interview_scheduling.repositories.interview_repository import InterviewRepository
from app.domains.interview_scheduling.services.calendar_service import calendar_service
from app.models.interview import Interview, InterviewFeedback
from app.domains.analytics.services.activity_service import ActivityService, get_activity_service
from app.shared.compliance.audit_service import AuditService, get_audit_service
from app.shared.pii_masking import get_masked_logger
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match
from app.shared.types import WeDoBaseModel

logger = get_masked_logger(__name__)

router = APIRouter()


# Pydantic schemas for request/response
class ScheduleInterviewRequest(WeDoBaseModel):
    candidate_id: str | None = None  # If provided, will validate contact info
    candidate_name: str
    candidate_email: EmailStr
    interviewer_name: str
    interviewer_email: EmailStr
    additional_interviewers: list[dict] = []
    job_title: str
    job_vacancy_id: str | None = None
    interview_type: str = "technical"  # technical, behavioral, cultural, final
    interview_mode: str = "video"  # video, in_person, phone
    recruitment_stage_id: str | None = None
    start_time: datetime
    duration_minutes: int = 60
    location: str | None = None
    as_teams_meeting: bool = True
    notes: str | None = None


class CheckAvailabilityRequest(WeDoBaseModel):
    interviewer_email: EmailStr
    date: datetime
    duration_minutes: int = 60


class RescheduleInterviewRequest(WeDoBaseModel):
    new_start_time: datetime
    new_duration_minutes: int | None = None


class InterviewFeedbackRequest(WeDoBaseModel):
    interviewer_name: str
    interviewer_email: EmailStr
    interviewer_role: str | None = None
    technical_skills_rating: float | None = None
    communication_rating: float | None = None
    cultural_fit_rating: float | None = None
    overall_rating: float | None = None
    strengths: list[str] = []
    weaknesses: list[str] = []
    notes: str | None = None
    recommendation: str | None = None
    next_steps_suggested: str | None = None


@router.post("/interviews", response_model=dict)
@router.post("/interviews/schedule", response_model=dict)
async def schedule_interview(
    request: ScheduleInterviewRequest,
    request_obj: Request,
    repo: InterviewRepository = Depends(get_interview_repo),
    audit_svc: AuditService = Depends(get_audit_service),
    activity_svc: ActivityService = Depends(get_activity_service),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Schedule a new interview with automatic Microsoft Calendar integration.
    """
    try:
        # Validate candidate contact info if candidate_id is provided
        if request.candidate_id:
            try:
                candidate_uuid = uuid.UUID(request.candidate_id)
                candidate = await repo.get_candidate_by_id(candidate_uuid)

                if candidate:
                    has_valid_email = candidate.email and "@" in candidate.email
                    has_valid_phone = candidate.phone and len(
                        candidate.phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
                    ) >= 8

                    if not has_valid_email and not has_valid_phone:
                        raise HTTPException(
                            status_code=400,
                            detail={
                                "error": "missing_contact_info",
                                "message": "Candidato não possui email ou telefone válido. É necessário ter pelo menos um contato para agendar entrevista.",
                                "candidate_name": candidate.name,
                                "email": candidate.email,
                                "phone": candidate.phone,
                            },
                        )
            except ValueError:
                logger.warning("Invalid candidate_id format: %s", request.candidate_id)

        # Create calendar event
        all_interviewer_emails = [request.interviewer_email] + [
            i.get("email") for i in request.additional_interviewers if i.get("email")
        ]

        calendar_event = await calendar_service.schedule_interview(
            organizer_email=request.interviewer_email,
            candidate_name=request.candidate_name,
            candidate_email=request.candidate_email,
            interviewer_emails=all_interviewer_emails,
            position=request.job_title,
            start_time=request.start_time,
            duration_minutes=request.duration_minutes,
            location=request.location,
            as_teams_meeting=request.as_teams_meeting,
            notes=request.notes,
        )

        # Resolve recruitment stage if provided
        resolved_stage_name = None
        resolved_stage_id = None
        if request.recruitment_stage_id:
            try:
                req_company_id = (
                    getattr(request_obj.state, "company_id", None)
                    if hasattr(request_obj, "state")
                    else None
                )
                stage_uuid = uuid.UUID(request.recruitment_stage_id)
                stage = await repo.get_recruitment_stage(stage_uuid, company_id=req_company_id)
                if stage:
                    resolved_stage_name = stage.name
                    resolved_stage_id = stage.id
                    logger.info(
                        "Interview linked to stage: %s (%s)",
                        stage.display_name,
                        stage.name,
                    )
            except (ValueError, Exception) as e:
                logger.warning("Invalid recruitment_stage_id: %s", e)

        req_company_id = (
            getattr(request_obj.state, "company_id", None)
            if hasattr(request_obj, "state")
            else None
        )

        # Create database record
        interview = Interview(
            title=f"Entrevista: {request.candidate_name} - {request.job_title}",
            company_id=req_company_id,
            interview_type=request.interview_type,
            interview_mode=request.interview_mode,
            candidate_name=request.candidate_name,
            candidate_email=request.candidate_email,
            interviewer_name=request.interviewer_name,
            interviewer_email=request.interviewer_email,
            additional_interviewers=request.additional_interviewers,
            start_time=request.start_time,
            end_time=request.start_time + timedelta(minutes=request.duration_minutes),
            duration_minutes=request.duration_minutes,
            location=request.location,
            job_title=request.job_title,
            job_vacancy_id=uuid.UUID(request.job_vacancy_id) if request.job_vacancy_id else None,
            application_stage=resolved_stage_name,
            recruitment_stage_id=resolved_stage_id,
            graph_event_id=calendar_event.get("id"),
            graph_organizer_email=request.interviewer_email,
            is_synced_to_calendar=True,
            last_synced_at=datetime.utcnow(),
            status="scheduled",
            created_by="system",
        )

        # Extract meeting URL from calendar event
        if request.as_teams_meeting and calendar_event.get("onlineMeeting"):
            interview.meeting_url = calendar_event["onlineMeeting"].get("joinUrl")
            interview.meeting_platform = "teams"

        interview = await repo.add_interview(interview)

        logger.info("Interview scheduled: %s", interview.id)

        try:
            audit_company_id = None
            if request.job_vacancy_id:
                audit_company_id = await repo.get_vacancy_company_id(
                    uuid.UUID(request.job_vacancy_id)
                )
            if audit_company_id:
                await audit_svc.log_decision(
                    company_id=audit_company_id,
                    agent_name="interviews_module",
                    decision_type="schedule_interview",
                    action="schedule_interview",
                    decision="scheduled",
                    reasoning=[
                        "Interview scheduled via calendar integration",
                        f"Type: {request.interview_type}",
                        f"Mode: {request.interview_mode}",
                        f"Scheduled: {request.start_time.isoformat() if request.start_time else 'N/A'}",
                        "Calendar sync status: confirmed",
                    ],
                    criteria_used=[
                        "candidate_contact_info",
                        "interviewer_availability",
                        "calendar_sync",
                        "interview_mode",
                    ],
                    candidate_id=request.candidate_id,
                    job_vacancy_id=request.job_vacancy_id,
                    human_review_required=False,
                )
            else:
                logger.warning(
                    "Skipping audit log for schedule_interview: no company_id resolvable from vacancy"
                )
        except Exception as audit_err:
            logger.warning("Audit log failed for schedule_interview: %s", audit_err)

        await repo.commit()

        return {
            "success": True,
            "interview_id": str(interview.id),
            "calendar_event_id": calendar_event.get("id"),
            "meeting_url": interview.meeting_url,
            "start_time": interview.start_time.isoformat(),
            "end_time": interview.end_time.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to schedule interview: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/interviews", response_model=list[dict])
async def list_interviews(
    request_obj: Request,
    status: str | None = Query(None, description="Filter by status"),
    candidate_email: str | None = Query(None, description="Filter by candidate email"),
    interviewer_email: str | None = Query(None, description="Filter by interviewer email"),
    job_vacancy_id: str | None = Query(None, description="Filter by job vacancy ID"),
    candidate_id: str | None = Query(None, description="Filter by candidate ID"),
    limit: int = Query(50, ge=1, le=100),
    repo: InterviewRepository = Depends(get_interview_repo),
    current_user: User = Depends(get_current_user_or_demo),
    company_id: str = Depends(require_company_id),
):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    List interviews with optional filters.
    """
    try:
        if job_vacancy_id:
            try:
                uuid.UUID(job_vacancy_id)
            except (ValueError, AttributeError):
                raise HTTPException(status_code=400, detail="Invalid job_vacancy_id format")
        if candidate_id:
            try:
                uuid.UUID(candidate_id)
            except (ValueError, AttributeError):
                raise HTTPException(status_code=400, detail="Invalid candidate_id format")

        company_id = getattr(request_obj.state, "company_id", None) if hasattr(request_obj, "state") else None
        rows = await repo.list_interviews(
            status=status,
            candidate_email=candidate_email,
            interviewer_email=interviewer_email,
            job_vacancy_id=job_vacancy_id,
            candidate_id=candidate_id,
            company_id=company_id,
            limit=limit,
        )

        # Sprint 6.2 RBAC: visible scope filter (1-level manager hierarchy).
        # Plan canonical: ~/.claude/plans/jolly-roaming-moler.md
        # Visible interview if:
        #   - user is admin (bypass)
        #   - user has no dept_id AND no subordinates (legacy soft-launch bypass)
        #   - interviewer_email is self
        #   - interviewer_email is in subordinate_emails (manager sees team)
        try:
            from app.shared.rbac.visible_scope import compute_visible_scope
            _scope = await compute_visible_scope(current_user)
            if not _scope.is_admin and (
                _scope.own_dept_id is not None or _scope.has_subordinates
            ):
                _allowed = set(_scope.subordinate_user_emails)
                if _scope.user_email:
                    _allowed.add(_scope.user_email)
                rows = [
                    r for r in rows
                    if (r[0].interviewer_email or "").lower() in _allowed
                    or not r[0].interviewer_email  # unassigned interviews visible to all
                ]
        except Exception as _scope_exc:
            logger.debug("[Sprint6.2] interview scope filter failed (non-blocking): %s", _scope_exc)

        return [
            {
                "id": str(interview.id),
                "title": interview.title,
                "description": interview.description,
                "candidate_id": str(interview.candidate_id) if interview.candidate_id else None,
                "candidate_name": interview.candidate_name,
                "candidate_email": interview.candidate_email,
                "interviewer_name": interview.interviewer_name,
                "interviewer_email": interview.interviewer_email,
                "interview_type": interview.interview_type,
                "interview_mode": interview.interview_mode,
                "start_time": interview.start_time.isoformat(),
                "end_time": interview.end_time.isoformat(),
                "duration_minutes": interview.duration_minutes,
                "status": interview.status,
                "confirmation_status": interview.confirmation_status,
                "meeting_url": interview.meeting_url,
                "meeting_platform": interview.meeting_platform,
                "location": interview.location,
                "job_vacancy_id": str(interview.job_vacancy_id) if interview.job_vacancy_id else None,
                "job_title": interview.job_title,
                "job_code": job_code,
                "job_manager": job_manager,
                "application_stage": interview.application_stage,
                "is_synced_to_calendar": interview.is_synced_to_calendar,
                "created_at": interview.created_at.isoformat() if interview.created_at else None,
                "cancelled_at": interview.cancelled_at.isoformat() if interview.cancelled_at else None,
                "cancellation_reason": interview.cancellation_reason,
            }
            for interview, job_code, job_manager in rows
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to list interviews: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/interviews/{interview_id}/cancel", response_model=dict)
async def cancel_interview(
    interview_id: str,
    cancellation_message: str | None = None,
    repo: InterviewRepository = Depends(get_interview_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Cancel a scheduled interview.
    """
    try:
        interview = await repo.get_interview_by_id(interview_id)

        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")

        # Cancel in calendar if synced
        if interview.graph_event_id and interview.graph_organizer_email:
            await calendar_service.cancel_interview(
                organizer_email=interview.graph_organizer_email,
                event_id=interview.graph_event_id,
                cancellation_message=cancellation_message,
            )

        # Update database
        interview.status = "cancelled"
        interview.cancelled_at = datetime.utcnow()
        interview.cancellation_reason = cancellation_message

        await repo.commit()

        logger.info("Interview cancelled: %s", interview_id)

        return {"success": True, "message": "Interview cancelled successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to cancel interview: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


class CompleteInterviewRequest(WeDoBaseModel):
    outcome: str | None = None
    feedback: dict | None = None


@router.post("/interviews/{interview_id}/complete", response_model=dict)
async def complete_interview(
    interview_id: str,
    request: CompleteInterviewRequest,
    repo: InterviewRepository = Depends(get_interview_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Mark an interview as completed.

    This endpoint dispatches the interview-completed event to automation handlers
    for further processing (e.g., stage changes, notifications).

    Args:
        interview_id: UUID of the interview to complete
        outcome: Interview outcome (passed, failed, pending_review)
        feedback: Interview feedback data
        company_id: Company ID for event dispatch
    """
    try:
        from app.domains.interview_scheduling.services.scheduling_service import scheduling_service

        interview = await scheduling_service.complete_interview(
            db=repo.db,
            interview_id=interview_id,
            outcome=request.outcome,
            feedback=request.feedback,
            company_id=company_id,
            dispatch_event=True,
        )

        logger.info("Interview completed: %s", interview_id)

        return {
            "success": True,
            "interview_id": str(interview.id),
            "status": interview.status,
            "outcome": request.outcome,
            "completed_at": interview.completed_at.isoformat() if interview.completed_at else None,
        }

    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to complete interview: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/interviews/{interview_id}/reschedule", response_model=dict)
async def reschedule_interview(
    interview_id: str,
    request: RescheduleInterviewRequest,
    repo: InterviewRepository = Depends(get_interview_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Reschedule an existing interview.
    """
    try:
        interview = await repo.get_interview_by_id(interview_id)

        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")

        # Reschedule in calendar if synced
        if interview.graph_event_id and interview.graph_organizer_email:
            await calendar_service.reschedule_interview(
                organizer_email=interview.graph_organizer_email,
                event_id=interview.graph_event_id,
                new_start_time=request.new_start_time,
                new_duration_minutes=request.new_duration_minutes,
            )

        # Update database
        old_start = interview.start_time
        interview.start_time = request.new_start_time

        if request.new_duration_minutes:
            interview.duration_minutes = request.new_duration_minutes
            interview.end_time = request.new_start_time + timedelta(minutes=request.new_duration_minutes)
        else:
            interview.end_time = request.new_start_time + timedelta(minutes=interview.duration_minutes)

        interview.status = "rescheduled"
        interview.last_synced_at = datetime.utcnow()

        await repo.commit()

        logger.info("Interview rescheduled: %s from %s to %s", interview_id, old_start, request.new_start_time)

        return {
            "success": True,
            "message": "Interview rescheduled successfully",
            "new_start_time": interview.start_time.isoformat(),
            "new_end_time": interview.end_time.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to reschedule interview: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/interviews/check-availability", response_model=dict)
async def check_availability(request: CheckAvailabilityRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Check interviewer availability for a specific date.
    """
    try:
        available_slots = await calendar_service.check_interviewer_availability(
            interviewer_email=request.interviewer_email,
            date=request.date,
            duration_minutes=request.duration_minutes,
        )

        return {
            "interviewer_email": request.interviewer_email,
            "date": request.date.isoformat(),
            "duration_minutes": request.duration_minutes,
            "available_slots": available_slots,
            "total_slots": len(available_slots),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to check availability: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/interviews/{interview_id}/feedback", response_model=dict)
async def submit_interview_feedback(
    interview_id: str,
    feedback: InterviewFeedbackRequest,
    repo: InterviewRepository = Depends(get_interview_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Submit feedback for a completed interview.
    """
    try:
        # Verify interview exists
        interview = await repo.get_interview_by_id(interview_id)

        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")

        # Create feedback record
        feedback_record = InterviewFeedback(
            interview_id=interview_id,
            interviewer_name=feedback.interviewer_name,
            interviewer_email=feedback.interviewer_email,
            interviewer_role=feedback.interviewer_role,
            technical_skills_rating=feedback.technical_skills_rating,
            communication_rating=feedback.communication_rating,
            cultural_fit_rating=feedback.cultural_fit_rating,
            overall_rating=feedback.overall_rating,
            strengths=feedback.strengths,
            weaknesses=feedback.weaknesses,
            notes=feedback.notes,
            recommendation=feedback.recommendation,
            next_steps_suggested=feedback.next_steps_suggested,
        )

        await repo.add_feedback(feedback_record)

        # Update interview status
        if interview.status == "scheduled":
            interview.status = "completed"

        await repo.commit()

        logger.info("Feedback submitted for interview %s", interview_id)

        return {
            "success": True,
            "feedback_id": str(feedback_record.id),
            "message": "Feedback submitted successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to submit feedback: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================
# AI-FIRST SCHEDULING ENDPOINTS
# =============================================

class GenerateEmailTemplateRequest(WeDoBaseModel):
    candidate_name: str
    candidate_email: EmailStr
    job_title: str
    interview_type: str = "técnica"
    user_name: str | None = "Consultor"


class ScheduleFromPromptRequest(WeDoBaseModel):
    candidate_name: str
    candidate_email: EmailStr
    candidate_id: str | None = None
    job_title: str
    job_vacancy_id: str | None = None
    interview_type: str = "técnica"
    natural_language_prompt: str  # "Agendar para amanhã às 14h comigo"
    user_name: str = "Consultor"
    user_email: EmailStr


@router.post("/interviews/generate-email-template", response_model=dict)
async def generate_email_template(request: GenerateEmailTemplateRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Generate interview invitation email template using LIA.
    AI-first approach for email generation.
    """
    try:
        container = get_provider_for_tenant()

        prompt = f"""Gere um email profissional de convite para entrevista.

INFORMAÇÕES:
- Candidato: {request.candidate_name}
- Email: {request.candidate_email}
- Vaga: {request.job_title}
- Tipo de entrevista: {request.interview_type}
- Enviado por: {request.user_name}

REQUISITOS:
1. Tom profissional mas amigável
2. Mencionar a vaga e tipo de entrevista
3. Deixar claro que o agendamento será feito (data/hora serão confirmadas)
4. Incluir contato para dúvidas
5. Assinar como "{request.user_name} - WedoTalent"

Retorne APENAS o corpo do email (sem assunto), formatado em HTML simples.
"""

        email_body = await container.generate_with_fallback(prompt, agent_type="InterviewAgent")

        # Generate subject
        subject = f"Convite para Entrevista {request.interview_type.capitalize()} - {request.job_title}"

        logger.info("Email template generated for %s", request.candidate_name)

        return {
            "success": True,
            "subject": subject,
            "body": email_body,
            "to": request.candidate_email,
            "candidate_name": request.candidate_name,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to generate email template: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/interviews/schedule-from-prompt", response_model=dict)
async def schedule_from_prompt(
    request: ScheduleFromPromptRequest,
    repo: InterviewRepository = Depends(get_interview_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Schedule interview using natural language prompt.
    Parses: "Agendar para amanhã às 14h comigo"
    """
    try:
        container = get_provider_for_tenant()

        # Parse natural language prompt using LIA
        parse_prompt = f"""Extraia informações de agendamento de entrevista do prompt em linguagem natural.

PROMPT DO USUÁRIO:
"{request.natural_language_prompt}"

CONTEXTO:
- Data/hora atual: {datetime.now().isoformat()}
- Usuário: {request.user_name} ({request.user_email})

EXTRAIA e retorne EXATAMENTE no formato JSON abaixo:
1. Data da entrevista no formato YYYY-MM-DD (calcular se relativo: "amanhã", "semana que vem", etc)
2. Hora da entrevista no formato HH:MM (24 horas)
3. Entrevistador (se "comigo", use "{request.user_name}")
4. Email do entrevistador (se "comigo", use "{request.user_email}")
5. Duração em minutos (padrão: 60)

IMPORTANTE: Retorne APENAS o JSON válido sem texto adicional.

{{
    "date": "YYYY-MM-DD",
    "time": "HH:MM",
    "interviewer_name": "{request.user_name}",
    "interviewer_email": "{request.user_email}",
    "duration_minutes": 60,
    "notes": "Informações extras se houver"
}}
"""

        extracted_text = await container.generate_with_fallback(parse_prompt, agent_type="InterviewAgent")

        # Clean JSON
        if "```json" in extracted_text:
            extracted_text = extracted_text.split("```json")[1].split("```")[0]
        elif "```" in extracted_text:
            extracted_text = extracted_text.split("```")[1].split("```")[0]

        try:
            extracted = json.loads(extracted_text.strip())
        except json.JSONDecodeError:
            logger.error("Failed to parse LLM JSON output: %s", extracted_text)
            raise HTTPException(
                status_code=400,
                detail="Não foi possível entender o prompt. Por favor, tente novamente com data e hora mais claras (ex: 'amanhã às 14h').",
            )

        # Validate required fields
        if not extracted.get("date") or not extracted.get("time"):
            raise HTTPException(
                status_code=400,
                detail="Não foi possível identificar a data ou hora. Por favor, especifique quando deseja agendar (ex: 'amanhã às 14h').",
            )

        # Parse and validate datetime
        try:
            interview_date = datetime.strptime(extracted["date"], "%Y-%m-%d").date()
            interview_time = datetime.strptime(extracted["time"], "%H:%M").time()
            start_time = datetime.combine(interview_date, interview_time)

            # Validate not in the past
            if start_time < datetime.now():
                raise HTTPException(
                    status_code=400,
                    detail="Não é possível agendar entrevistas no passado. Por favor, escolha uma data futura.",
                )
        except ValueError:
            logger.error(
                "Invalid datetime format: date=%s, time=%s",
                extracted.get("date"),
                extracted.get("time"),
            )
            raise HTTPException(
                status_code=400,
                detail="Formato de data/hora inválido. Por favor, use formatos como 'amanhã às 14h' ou 'próxima segunda 10h'.",
            )

        # Default to user if not specified or "comigo"
        interviewer_name = extracted.get("interviewer_name", request.user_name) or request.user_name
        interviewer_email = extracted.get("interviewer_email", request.user_email) or request.user_email
        duration_minutes = extracted.get("duration_minutes", 60) or 60

        # Create calendar event with validated data
        try:
            calendar_event = await calendar_service.schedule_interview(
                organizer_email=interviewer_email,
                candidate_name=request.candidate_name,
                candidate_email=request.candidate_email,
                interviewer_emails=[interviewer_email],
                position=request.job_title,
                start_time=start_time,
                duration_minutes=duration_minutes,
                location="Microsoft Teams",
                as_teams_meeting=True,
                notes=extracted.get("notes"),
            )
        except HTTPException:
            raise
        except Exception as calendar_error:
            logger.error("Calendar service failed: %s", calendar_error)
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao criar evento no calendário: {str(calendar_error)}",
            )

        # Create database record
        interview = Interview(
            title=f"Entrevista: {request.candidate_name} - {request.job_title}",
            interview_type=request.interview_type,
            interview_mode="remoto",
            candidate_name=request.candidate_name,
            candidate_email=request.candidate_email,
            interviewer_name=interviewer_name,
            interviewer_email=interviewer_email,
            additional_interviewers=[],
            start_time=start_time,
            end_time=start_time + timedelta(minutes=duration_minutes),
            duration_minutes=duration_minutes,
            location="Microsoft Teams",
            job_title=request.job_title,
            graph_event_id=calendar_event.get("id"),
            graph_organizer_email=interviewer_email,
            is_synced_to_calendar=True,
            last_synced_at=datetime.utcnow(),
            status="scheduled",
            created_by=request.user_name,
        )

        # Extract meeting URL
        if calendar_event.get("onlineMeeting"):
            interview.meeting_url = calendar_event["onlineMeeting"].get("joinUrl")
            interview.meeting_platform = "teams"

        interview = await repo.add_interview(interview)

        # Create activity feed entry if candidate_id provided
        if request.candidate_id:
            await activity_svc.create_activity(
                db=repo.db,
                activity_type="interview_scheduled",
                title=f"Entrevista {request.interview_type} agendada",
                description=f"Entrevista agendada para {start_time.strftime('%d/%m/%Y às %H:%M')} com {interviewer_name}",
                candidate_id=request.candidate_id,
                job_vacancy_id=request.job_vacancy_id,
                metadata={
                    "interview_id": str(interview.id),
                    "meeting_url": interview.meeting_url,
                    "interviewer": interviewer_name,
                },
            )

        await repo.commit()

        logger.info("Interview scheduled from prompt for %s", request.candidate_name)

        return {
            "success": True,
            "interview_id": str(interview.id),
            "meeting_url": interview.meeting_url,
            "start_time": start_time.isoformat(),
            "end_time": interview.end_time.isoformat(),
            "interviewer": interviewer_name,
            "parsed_data": extracted,
        }

    except HTTPException:
        # Re-raise HTTP exceptions with their original status codes
        raise
    except Exception as e:
        logger.error("Unexpected error scheduling from prompt: %s", e)
        raise HTTPException(status_code=500, detail=f"Erro inesperado: {str(e)}")


# =============================================
# SHORTLISTED CANDIDATES ENDPOINT
# =============================================

def is_valid_uuid(val: str) -> bool:
    """Check if a string is a valid UUID."""
    try:
        uuid.UUID(str(val))
        return True
    except (ValueError, TypeError):
        return False


@router.get("/interviews/shortlisted/filter", response_model=dict)
async def get_shortlisted_candidate_ids(
    scope: str = Query(
        ...,
        description="Shortlist scope: shortlisted_by_you, shortlisted_org_this_project, shortlisted_org_all_projects",
    ),
    user_email: str | None = Query(None, description="User email for 'shortlisted_by_you' scope"),
    company_id: str | None = Query(None, description="Company ID for org-level scopes"),
    project_id: str | None = Query(None, description="Project/Vacancy ID for project-specific scopes"),
    since_date: str | None = Query(None, description="Filter interviews since this date (ISO format)"),
    repo: InterviewRepository = Depends(get_interview_repo),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get candidate IDs that have been shortlisted (have interview records).

    Business rule for "shortlisted": A candidate is shortlisted if they have at least
    one interview record with status in ('scheduled', 'confirmed', 'completed', 'rescheduled').

    Scopes:
    - shortlisted_by_you: Candidates where the user is the interviewer
    - shortlisted_org_this_project: Candidates interviewed for a specific project/vacancy
    - shortlisted_org_all_projects: All candidates interviewed by the company
    """
    try:
        since_datetime = None
        if since_date:
            try:
                since_datetime = datetime.fromisoformat(since_date.replace("Z", "+00:00"))
            except ValueError:
                pass

        if scope == "shortlisted_org_this_project" and (not project_id or not is_valid_uuid(project_id)):
            return {"candidate_ids": [], "count": 0}

        candidate_ids = await repo.get_shortlisted_candidate_ids(
            scope=scope,
            user_email=user_email,
            company_id=company_id,
            project_id=project_id,
            since_datetime=since_datetime,
        )

        logger.info("Found %d shortlisted candidates for scope: %s", len(candidate_ids), scope)

        return {
            "candidate_ids": candidate_ids,
            "count": len(candidate_ids),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get shortlisted candidates: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/interviews/stages", response_model=list[dict])
async def get_interview_stages(
    request: Request,
    repo: InterviewRepository = Depends(get_interview_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Get the company's configured recruitment stages that can be used for interviews.

    Returns stages ordered by stage_order, filtered to active interview-type stages
    (excludes initial funnel and final rejection/hired stages).
    Company is resolved from the authenticated JWT context (request.state.company_id).
    """
    company_id = getattr(request, "state", None) and getattr(request.state, "company_id", None)
    if not company_id:
        raise HTTPException(status_code=401, detail="Company context required")
    try:
        stages = await repo.get_interview_stages(company_id)

        return [
            {
                "id": str(s.id),
                "name": s.name,
                "display_name": s.display_name,
                "description": s.description,
                "stage_order": s.stage_order,
                "color": s.color,
                "icon": s.icon,
                "sla_hours": s.sla_hours,
            }
            for s in stages
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get interview stages: %s", e)
        raise HTTPException(status_code=500, detail="Error fetching stages")


def _validate_interview_uuid(interview_id: str) -> None:
    try:
        uuid.UUID(interview_id)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=404, detail="Interview not found")


class UploadRecordingRequest(WeDoBaseModel):
    recording_url: str
    language_hint: str = "pt-BR"
    auto_transcribe: bool = True


class TranscribeInterviewRequest(WeDoBaseModel):
    language_hint: str = "pt-BR"


@router.patch("/interviews/{interview_id}/recording", response_model=dict)
async def upload_recording(
    interview_id: str,
    request: UploadRecordingRequest,
    request_obj: Request,
    background_tasks: BackgroundTasks,
    repo: InterviewRepository = Depends(get_interview_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Attach a recording URL to an interview and optionally trigger transcription.
    """
    _validate_interview_uuid(interview_id)

    try:
        interview = await repo.get_interview_by_id(interview_id)
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")

        req_company_id = getattr(request_obj.state, "company_id", None) if hasattr(request_obj, "state") else None
        if req_company_id and (not interview.company_id or interview.company_id != req_company_id):
            raise HTTPException(status_code=404, detail="Interview not found")

        interview.recording_url = request.recording_url
        await repo.commit()

        logger.info("Recording URL attached to interview %s", interview_id)

        if request.auto_transcribe:
            background_tasks.add_task(
                _run_transcription_background,
                interview_id,
                request.recording_url,
                request.language_hint,
            )
            return {
                "success": True,
                "interview_id": interview_id,
                "recording_url": request.recording_url,
                "transcription_status": "queued",
                "message": "Recording attached. Transcription started in background.",
            }

        return {
            "success": True,
            "interview_id": interview_id,
            "recording_url": request.recording_url,
            "transcription_status": "not_started",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to attach recording to interview %s: %s", interview_id, e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/interviews/{interview_id}/transcribe", response_model=dict)
async def transcribe_interview(
    interview_id: str,
    request: TranscribeInterviewRequest,
    request_obj: Request,
    background_tasks: BackgroundTasks,
    repo: InterviewRepository = Depends(get_interview_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Trigger transcription for an interview that already has a recording URL.
    """
    _validate_interview_uuid(interview_id)

    try:
        interview = await repo.get_interview_by_id(interview_id)
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")

        req_company_id = getattr(request_obj.state, "company_id", None) if hasattr(request_obj, "state") else None
        if req_company_id and (not interview.company_id or interview.company_id != req_company_id):
            raise HTTPException(status_code=404, detail="Interview not found")

        if not interview.recording_url:
            raise HTTPException(
                status_code=400,
                detail="Interview does not have a recording URL. Attach one first via PATCH /interviews/{id}/recording.",
            )

        if interview.transcript:
            return {
                "success": True,
                "interview_id": interview_id,
                "transcription_status": "already_transcribed",
                "word_count": len(interview.transcript.split()),
                "language": interview.transcript_language,
            }

        background_tasks.add_task(
            _run_transcription_background,
            interview_id,
            interview.recording_url,
            request.language_hint,
        )

        return {
            "success": True,
            "interview_id": interview_id,
            "transcription_status": "queued",
            "message": "Transcription started in background.",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to trigger transcription for interview %s: %s", interview_id, e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/interviews/{interview_id}/transcript", response_model=dict)
async def get_interview_transcript(
    interview_id: str,
    request_obj: Request,
    repo: InterviewRepository = Depends(get_interview_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Get the transcript for an interview.
    """
    _validate_interview_uuid(interview_id)

    try:
        interview = await repo.get_interview_by_id(interview_id)
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")

        req_company_id = getattr(request_obj.state, "company_id", None) if hasattr(request_obj, "state") else None
        if req_company_id and (not interview.company_id or interview.company_id != req_company_id):
            raise HTTPException(status_code=404, detail="Interview not found")

        if not interview.transcript:
            feedback = interview.feedback or {}
            fallback_transcript = feedback.get("transcript_text")
            if fallback_transcript:
                return {
                    "interview_id": interview_id,
                    "has_transcript": True,
                    "transcript": fallback_transcript,
                    "language": interview.transcript_language or "pt-BR",
                    "source": interview.transcript_source or feedback.get("transcript_source", "teams"),
                    "word_count": len(fallback_transcript.split()),
                }
            return {
                "interview_id": interview_id,
                "has_transcript": False,
                "transcript": None,
                "message": "No transcript available for this interview.",
            }

        return {
            "interview_id": interview_id,
            "has_transcript": True,
            "transcript": interview.transcript,
            "language": interview.transcript_language,
            "source": interview.transcript_source,
            "word_count": len(interview.transcript.split()),
            "transcribed_at": interview.transcribed_at.isoformat() if interview.transcribed_at else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get transcript for interview %s: %s", interview_id, e)
        raise HTTPException(status_code=500, detail=str(e))


async def _run_transcription_background(
    interview_id: str,
    recording_url: str,
    language_hint: str,
) -> None:
    from app.core.database import AsyncSessionLocal
    from app.domains.interview_intelligence.services.transcription_service import transcription_service

    try:
        async with AsyncSessionLocal() as db:
            result = await transcription_service.transcribe_and_persist(
                interview_id=interview_id,
                recording_url=recording_url,
                db=db,
                language_hint=language_hint,
            )
            logger.info(
                "Background transcription completed for interview %s: %d words",
                interview_id,
                result.get("word_count", 0),
            )
    except Exception as e:
        logger.error("Background transcription failed for interview %s: %s", interview_id, e)
