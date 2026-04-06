"""
Interview Scheduling API endpoints.
"""
import json
import uuid
from datetime import datetime, timedelta

from anthropic import AsyncAnthropic
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.interview_scheduling.services.calendar_service import calendar_service
from app.models.candidate import Candidate
from app.models.interview import Interview, InterviewFeedback
from app.models.job_vacancy import JobVacancy
from app.services.activity_service import activity_service
from app.shared.compliance.audit_service import audit_service
from app.shared.pii_masking import get_masked_logger

logger = get_masked_logger(__name__)

router = APIRouter()


# Pydantic schemas for request/response
class ScheduleInterviewRequest(BaseModel):
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
    start_time: datetime
    duration_minutes: int = 60
    location: str | None = None
    as_teams_meeting: bool = True
    notes: str | None = None


class CheckAvailabilityRequest(BaseModel):
    interviewer_email: EmailStr
    date: datetime
    duration_minutes: int = 60


class RescheduleInterviewRequest(BaseModel):
    new_start_time: datetime
    new_duration_minutes: int | None = None


class InterviewFeedbackRequest(BaseModel):
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


@router.post("/interviews/schedule", response_model=dict)
async def schedule_interview(
    request: ScheduleInterviewRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Schedule a new interview with automatic Microsoft Calendar integration.
    """
    try:
        # Validate candidate contact info if candidate_id is provided
        if request.candidate_id:
            try:
                candidate_uuid = uuid.UUID(request.candidate_id)
                result = await db.execute(
                    select(Candidate).where(Candidate.id == candidate_uuid)
                )
                candidate = result.scalar_one_or_none()
                
                if candidate:
                    has_valid_email = candidate.email and '@' in candidate.email
                    has_valid_phone = candidate.phone and len(candidate.phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')) >= 8
                    
                    if not has_valid_email and not has_valid_phone:
                        raise HTTPException(
                            status_code=400,
                            detail={
                                "error": "missing_contact_info",
                                "message": "Candidato não possui email ou telefone válido. É necessário ter pelo menos um contato para agendar entrevista.",
                                "candidate_name": candidate.name,
                                "email": candidate.email,
                                "phone": candidate.phone
                            }
                        )
            except ValueError:
                logger.warning(f"Invalid candidate_id format: {request.candidate_id}")
        
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
            notes=request.notes
        )
        
        # Create database record
        interview = Interview(
            title=f"Entrevista: {request.candidate_name} - {request.job_title}",
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
            graph_event_id=calendar_event.get("id"),
            graph_organizer_email=request.interviewer_email,
            is_synced_to_calendar=True,
            last_synced_at=datetime.utcnow(),
            status="scheduled",
            created_by="system"
        )
        
        # Extract meeting URL from calendar event
        if request.as_teams_meeting and calendar_event.get("onlineMeeting"):
            interview.meeting_url = calendar_event["onlineMeeting"].get("joinUrl")
            interview.meeting_platform = "teams"
        
        db.add(interview)
        await db.commit()
        await db.refresh(interview)
        
        logger.info(f"✅ Interview scheduled: {interview.id}")

        try:
            audit_company_id = None
            if request.job_vacancy_id:
                vac_result = await db.execute(
                    select(JobVacancy.company_id).where(JobVacancy.id == uuid.UUID(request.job_vacancy_id))
                )
                vac_row = vac_result.scalar_one_or_none()
                if vac_row:
                    audit_company_id = str(vac_row)
            if audit_company_id:
                await audit_service.log_decision(
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
                    criteria_used=["candidate_contact_info", "interviewer_availability", "calendar_sync", "interview_mode"],
                    candidate_id=request.candidate_id,
                    job_vacancy_id=request.job_vacancy_id,
                    human_review_required=False,
                )
            else:
                logger.warning("Skipping audit log for schedule_interview: no company_id resolvable from vacancy")
        except Exception as audit_err:
            logger.warning(f"Audit log failed for schedule_interview: {audit_err}")

        return {
            "success": True,
            "interview_id": str(interview.id),
            "calendar_event_id": calendar_event.get("id"),
            "meeting_url": interview.meeting_url,
            "start_time": interview.start_time.isoformat(),
            "end_time": interview.end_time.isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to schedule interview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/interviews", response_model=list[dict])
async def list_interviews(
    status: str | None = Query(None, description="Filter by status"),
    candidate_email: str | None = Query(None, description="Filter by candidate email"),
    interviewer_email: str | None = Query(None, description="Filter by interviewer email"),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    List interviews with optional filters.
    """
    try:
        from sqlalchemy.orm import aliased
        jv = aliased(JobVacancy)
        query = select(Interview, jv.job_id, jv.manager).outerjoin(jv, Interview.job_vacancy_id == jv.id)
        
        filters = []
        if status:
            filters.append(Interview.status == status)
        if candidate_email:
            filters.append(Interview.candidate_email == candidate_email)
        if interviewer_email:
            filters.append(Interview.interviewer_email == interviewer_email)
        
        if filters:
            query = query.where(and_(*filters))
        
        query = query.order_by(Interview.start_time.desc()).limit(limit)
        
        result = await db.execute(query)
        rows = result.all()
        
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
        
    except Exception as e:
        logger.error(f"❌ Failed to list interviews: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/interviews/{interview_id}/cancel", response_model=dict)
async def cancel_interview(
    interview_id: str,
    cancellation_message: str | None = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Cancel a scheduled interview.
    """
    try:
        result = await db.execute(
            select(Interview).where(Interview.id == interview_id)
        )
        interview = result.scalar_one_or_none()
        
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")
        
        # Cancel in calendar if synced
        if interview.graph_event_id and interview.graph_organizer_email:
            await calendar_service.cancel_interview(
                organizer_email=interview.graph_organizer_email,
                event_id=interview.graph_event_id,
                cancellation_message=cancellation_message
            )
        
        # Update database
        interview.status = "cancelled"
        interview.cancelled_at = datetime.utcnow()
        interview.cancellation_reason = cancellation_message
        
        await db.commit()
        
        logger.info(f"✅ Interview cancelled: {interview_id}")
        
        return {"success": True, "message": "Interview cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to cancel interview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class CompleteInterviewRequest(BaseModel):
    outcome: str | None = None
    feedback: dict | None = None
    company_id: str | None = None


@router.post("/interviews/{interview_id}/complete", response_model=dict)
async def complete_interview(
    interview_id: str,
    request: CompleteInterviewRequest,
    db: AsyncSession = Depends(get_db)
):
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
            db=db,
            interview_id=interview_id,
            outcome=request.outcome,
            feedback=request.feedback,
            company_id=request.company_id,
            dispatch_event=True
        )
        
        logger.info(f"✅ Interview completed: {interview_id}")
        
        return {
            "success": True,
            "interview_id": str(interview.id),
            "status": interview.status,
            "outcome": request.outcome,
            "completed_at": interview.completed_at.isoformat() if interview.completed_at else None
        }
        
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error(f"❌ Failed to complete interview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/interviews/{interview_id}/reschedule", response_model=dict)
async def reschedule_interview(
    interview_id: str,
    request: RescheduleInterviewRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Reschedule an existing interview.
    """
    try:
        result = await db.execute(
            select(Interview).where(Interview.id == interview_id)
        )
        interview = result.scalar_one_or_none()
        
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")
        
        # Reschedule in calendar if synced
        if interview.graph_event_id and interview.graph_organizer_email:
            await calendar_service.reschedule_interview(
                organizer_email=interview.graph_organizer_email,
                event_id=interview.graph_event_id,
                new_start_time=request.new_start_time,
                new_duration_minutes=request.new_duration_minutes
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
        
        await db.commit()
        
        logger.info(f"✅ Interview rescheduled: {interview_id} from {old_start} to {request.new_start_time}")
        
        return {
            "success": True,
            "message": "Interview rescheduled successfully",
            "new_start_time": interview.start_time.isoformat(),
            "new_end_time": interview.end_time.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to reschedule interview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/interviews/check-availability", response_model=dict)
async def check_availability(request: CheckAvailabilityRequest):
    """
    Check interviewer availability for a specific date.
    """
    try:
        available_slots = await calendar_service.check_interviewer_availability(
            interviewer_email=request.interviewer_email,
            date=request.date,
            duration_minutes=request.duration_minutes
        )
        
        return {
            "interviewer_email": request.interviewer_email,
            "date": request.date.isoformat(),
            "duration_minutes": request.duration_minutes,
            "available_slots": available_slots,
            "total_slots": len(available_slots)
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to check availability: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/interviews/{interview_id}/feedback", response_model=dict)
async def submit_interview_feedback(
    interview_id: str,
    feedback: InterviewFeedbackRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Submit feedback for a completed interview.
    """
    try:
        # Verify interview exists
        result = await db.execute(
            select(Interview).where(Interview.id == interview_id)
        )
        interview = result.scalar_one_or_none()
        
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
            next_steps_suggested=feedback.next_steps_suggested
        )
        
        db.add(feedback_record)
        
        # Update interview status
        if interview.status == "scheduled":
            interview.status = "completed"
        
        await db.commit()
        
        logger.info(f"✅ Feedback submitted for interview {interview_id}")
        
        return {
            "success": True,
            "feedback_id": str(feedback_record.id),
            "message": "Feedback submitted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to submit feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================
# AI-FIRST SCHEDULING ENDPOINTS
# =============================================

class GenerateEmailTemplateRequest(BaseModel):
    candidate_name: str
    candidate_email: EmailStr
    job_title: str
    interview_type: str = "técnica"
    user_name: str | None = "Consultor"


class ScheduleFromPromptRequest(BaseModel):
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
async def generate_email_template(request: GenerateEmailTemplateRequest):
    """
    Generate interview invitation email template using LIA.
    AI-first approach for email generation.
    """
    try:
        anthropic = AsyncAnthropic()
        
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
        
        response = await anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        email_body = response.content[0].text
        
        # Generate subject
        subject = f"Convite para Entrevista {request.interview_type.capitalize()} - {request.job_title}"
        
        logger.info(f"✅ Email template generated for {request.candidate_name}")
        
        return {
            "success": True,
            "subject": subject,
            "body": email_body,
            "to": request.candidate_email,
            "candidate_name": request.candidate_name
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to generate email template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/interviews/schedule-from-prompt", response_model=dict)
async def schedule_from_prompt(
    request: ScheduleFromPromptRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Schedule interview using natural language prompt.
    Parses: "Agendar para amanhã às 14h comigo"
    """
    try:
        anthropic = AsyncAnthropic()
        
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
        
        response = await anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            messages=[{"role": "user", "content": parse_prompt}]
        )
        
        extracted_text = response.content[0].text
        
        # Clean JSON
        if "```json" in extracted_text:
            extracted_text = extracted_text.split("```json")[1].split("```")[0]
        elif "```" in extracted_text:
            extracted_text = extracted_text.split("```")[1].split("```")[0]
        
        try:
            extracted = json.loads(extracted_text.strip())
        except json.JSONDecodeError:
            logger.error(f"❌ Failed to parse LLM JSON output: {extracted_text}")
            raise HTTPException(
                status_code=400,
                detail="Não foi possível entender o prompt. Por favor, tente novamente com data e hora mais claras (ex: 'amanhã às 14h')."
            )
        
        # Validate required fields
        if not extracted.get("date") or not extracted.get("time"):
            raise HTTPException(
                status_code=400,
                detail="Não foi possível identificar a data ou hora. Por favor, especifique quando deseja agendar (ex: 'amanhã às 14h')."
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
                    detail="Não é possível agendar entrevistas no passado. Por favor, escolha uma data futura."
                )
        except ValueError:
            logger.error(f"❌ Invalid datetime format: date={extracted.get('date')}, time={extracted.get('time')}")
            raise HTTPException(
                status_code=400,
                detail="Formato de data/hora inválido. Por favor, use formatos como 'amanhã às 14h' ou 'próxima segunda 10h'."
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
                notes=extracted.get("notes")
            )
        except Exception as calendar_error:
            logger.error(f"❌ Calendar service failed: {calendar_error}")
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao criar evento no calendário: {str(calendar_error)}"
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
            created_by=request.user_name
        )
        
        # Extract meeting URL
        if calendar_event.get("onlineMeeting"):
            interview.meeting_url = calendar_event["onlineMeeting"].get("joinUrl")
            interview.meeting_platform = "teams"
        
        db.add(interview)
        await db.commit()
        await db.refresh(interview)
        
        # Create activity feed entry if candidate_id provided
        if request.candidate_id:
            await activity_service.create_activity(
                db=db,
                activity_type="interview_scheduled",
                title=f"Entrevista {request.interview_type} agendada",
                description=f"Entrevista agendada para {start_time.strftime('%d/%m/%Y às %H:%M')} com {interviewer_name}",
                candidate_id=request.candidate_id,
                job_vacancy_id=request.job_vacancy_id,
                metadata={
                    "interview_id": str(interview.id),
                    "meeting_url": interview.meeting_url,
                    "interviewer": interviewer_name
                }
            )
        
        logger.info(f"✅ Interview scheduled from prompt for {request.candidate_name}")
        
        return {
            "success": True,
            "interview_id": str(interview.id),
            "meeting_url": interview.meeting_url,
            "start_time": start_time.isoformat(),
            "end_time": interview.end_time.isoformat(),
            "interviewer": interviewer_name,
            "parsed_data": extracted
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions with their original status codes
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error scheduling from prompt: {e}")
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
    scope: str = Query(..., description="Shortlist scope: shortlisted_by_you, shortlisted_org_this_project, shortlisted_org_all_projects"),
    user_email: str | None = Query(None, description="User email for 'shortlisted_by_you' scope"),
    company_id: str | None = Query(None, description="Company ID for org-level scopes"),
    project_id: str | None = Query(None, description="Project/Vacancy ID for project-specific scopes"),
    since_date: str | None = Query(None, description="Filter interviews since this date (ISO format)"),
    db: AsyncSession = Depends(get_db)
):
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
        from app.models.job_vacancy import JobVacancy
        
        valid_statuses = ['scheduled', 'confirmed', 'completed', 'rescheduled']
        
        query = select(Interview.candidate_id).distinct()
        filters = [Interview.status.in_(valid_statuses)]
        
        if since_date:
            try:
                since_datetime = datetime.fromisoformat(since_date.replace('Z', '+00:00'))
                filters.append(Interview.created_at >= since_datetime)
            except ValueError:
                pass
        
        if scope == "shortlisted_by_you":
            if not user_email:
                return {"candidate_ids": [], "count": 0}
            filters.append(Interview.interviewer_email == user_email)
            
        elif scope == "shortlisted_org_this_project":
            if not project_id or not is_valid_uuid(project_id):
                return {"candidate_ids": [], "count": 0}
            filters.append(Interview.job_vacancy_id == project_id)
            
        elif scope == "shortlisted_org_all_projects":
            if company_id:
                vacancy_subquery = select(JobVacancy.id).where(JobVacancy.company_id == company_id)
                filters.append(Interview.job_vacancy_id.in_(vacancy_subquery))
        else:
            return {"candidate_ids": [], "count": 0}
        
        query = query.where(and_(*filters))
        
        result = await db.execute(query)
        candidate_ids = [str(row[0]) for row in result.fetchall() if row[0] is not None]
        
        logger.info(f"✅ Found {len(candidate_ids)} shortlisted candidates for scope: {scope}")
        
        return {
            "candidate_ids": candidate_ids,
            "count": len(candidate_ids)
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get shortlisted candidates: {e}")
        raise HTTPException(status_code=500, detail=str(e))
