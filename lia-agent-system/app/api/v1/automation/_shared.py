"""
Automation API endpoints.

Provides endpoints for:
- Checking automation triggers
- Getting trigger configurations
- Enabling/disabling triggers
- AI-powered stage transition suggestions
- Executing specific automation actions
"""
import logging
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.cv_screening.services.cv_scoring_service import CVScoringService
from app.services.audit_service import audit_service
from app.domains.automation.services.automation_service import automation_service  # noqa: F401
from app.domains.automation.services.automation_trigger_service import automation_trigger_service  # noqa: F401
from app.domains.communication.services.communication_service import communication_service  # noqa: F401

logger = logging.getLogger(__name__)

_cv_scoring_service = None
_wsi_service = None

def get_cv_scoring_service():
    """Lazy load CVScoringService."""
    global _cv_scoring_service
    if _cv_scoring_service is None:
        _cv_scoring_service = CVScoringService()
    return _cv_scoring_service


def get_wsi_service():
    """Lazy load WSIService for conversational screening."""
    global _wsi_service
    if _wsi_service is None:
        from app.domains.cv_screening.services.wsi_service import WSIService
        _wsi_service = WSIService()
    return _wsi_service


# router is created in each sub-module and aggregated in __init__.py

_email_service = None
_whatsapp_service = None
_activity_service = None
_scheduling_service = None
_calendar_service = None


def get_email_service():
    """Lazy load EmailService."""
    global _email_service
    if _email_service is None:
        from app.domains.communication.services.email_service import EmailService
        _email_service = EmailService()
    return _email_service


def get_whatsapp_service():
    """Lazy load WhatsAppService."""
    global _whatsapp_service
    if _whatsapp_service is None:
        from app.domains.communication.services.whatsapp_service import WhatsAppService
        _whatsapp_service = WhatsAppService()
    return _whatsapp_service


def get_activity_service():
    """Lazy load ActivityService."""
    global _activity_service
    if _activity_service is None:
        from app.services.activity_service import ActivityService
        _activity_service = ActivityService()
    return _activity_service


def get_scheduling_service():
    """Lazy load SchedulingService."""
    global _scheduling_service
    if _scheduling_service is None:
        from app.domains.interview_scheduling.services.scheduling_service import SchedulingService
        _scheduling_service = SchedulingService()
    return _scheduling_service


def get_calendar_service():
    """Lazy load CalendarService."""
    global _calendar_service
    if _calendar_service is None:
        from app.domains.interview_scheduling.services.calendar_service import CalendarService
        _calendar_service = CalendarService()
    return _calendar_service


_ats_sync_service = None


def get_ats_sync_service():
    """Lazy load ATSSyncService."""
    global _ats_sync_service
    if _ats_sync_service is None:
        from app.domains.ats_integration.services.ats_sync_service import ATSSyncService
        _ats_sync_service = ATSSyncService()
    return _ats_sync_service


ATS_STAGE_MAPPING = {
    "gupy": {
        "Novo": "applied",
        "Triagem": "screening",
        "Triagem CV": "cv_screening",
        "Triagem WSI": "screening",
        "Entrevista": "interview",
        "Entrevista Técnica": "technical_interview",
        "Entrevista Comportamental": "behavioral_interview",
        "Entrevista Final": "final_interview",
        "Proposta": "offer",
        "Contratado": "hired",
        "Reprovado": "rejected",
        "Desistente": "withdrawn",
        "Em Análise": "under_review",
    },
    "pandape": {
        "Novo": "novo",
        "Triagem": "triagem",
        "Triagem CV": "triagem_cv",
        "Triagem WSI": "triagem_comportamental",
        "Entrevista": "entrevista",
        "Entrevista Técnica": "entrevista_tecnica",
        "Entrevista Comportamental": "entrevista_comportamental",
        "Entrevista Final": "entrevista_final",
        "Proposta": "proposta",
        "Contratado": "contratado",
        "Reprovado": "reprovado",
        "Desistente": "desistente",
        "Em Análise": "em_analise",
    },
}


def map_lia_stage_to_ats(lia_stage: str, ats_platform: str, company_id: str | None = None) -> tuple:
    """
    Map LIA stage name to ATS-specific stage identifier.
    
    Args:
        lia_stage: LIA internal stage name (e.g., "Triagem", "Entrevista")
        ats_platform: Target ATS platform (gupy, pandape, merge)
        company_id: Optional company ID for audit logging
        
    Returns:
        Tuple of (ats_stage, is_mapped) where:
        - ats_stage: ATS-specific stage identifier or safe default (lowercase with underscores)
        - is_mapped: True if explicit mapping exists, False if using fallback
    """
    platform_mapping = ATS_STAGE_MAPPING.get(ats_platform.lower(), {})
    mapped_stage = platform_mapping.get(lia_stage)
    
    if mapped_stage:
        return mapped_stage, True
    
    safe_default = lia_stage.lower().replace(" ", "_")
    logger.warning(
        f"⚠️ [ATS_STAGE_MAPPING] No mapping found for stage '{lia_stage}' "
        f"on platform '{ats_platform}'. Using safe default: '{safe_default}'"
    )
    
    return safe_default, False


async def notify_unmapped_stage(
    company_id: str,
    lia_stage: str,
    ats_platform: str,
    candidate_id: str | None = None,
    vacancy_id: str | None = None
) -> None:
    """
    Create notification and audit log for unmapped ATS stage.
    
    This alerts recruiters about potential ATS sync issues when
    a LIA stage doesn't have an explicit mapping to the target ATS.
    """
    try:
        activity_service = get_activity_service()
        await activity_service.create_activity(
            activity_type="ats_unmapped_stage_warning",
            title=f"Etapa não mapeada para {ats_platform.upper()}",
            description=(
                f"A etapa '{lia_stage}' não possui mapeamento configurado para o ATS {ats_platform}. "
                f"Foi utilizado o valor padrão '{lia_stage.lower().replace(' ', '_')}'. "
                f"Considere configurar o mapeamento para evitar inconsistências."
            ),
            actor_id="system",
            actor_name="LIA Automation",
            actor_type="system",
            target_id=candidate_id or "system",
            target_type="candidate" if candidate_id else "system",
            extra_data={
                "vacancy_id": vacancy_id,
                "company_id": company_id,
                "ats_platform": ats_platform,
                "lia_stage": lia_stage,
                "fallback_stage": lia_stage.lower().replace(" ", "_"),
                "warning_type": "unmapped_stage"
            },
            category="ats_sync"
        )
        
        await audit_service.log_decision(
            company_id=company_id,
            agent_name="ats_integrator",
            decision_type="ats_sync",
            action="stage_mapping_fallback",
            decision="fallback_used",
            score=None,
            confidence=0.5,
            reasoning=[
                f"No explicit mapping found for stage '{lia_stage}' on {ats_platform}",
                f"Using fallback: '{lia_stage.lower().replace(' ', '_')}'",
                "Recruiter notified about potential sync inconsistency"
            ],
            criteria_used=["lia_stage", "ats_platform", "mapping_availability"],
            candidate_id=candidate_id,
            job_vacancy_id=vacancy_id,
            human_review_required=True
        )
        
        logger.info(f"🔔 [ATS_STAGE_MAPPING] Notification created for unmapped stage '{lia_stage}'")
    except Exception as e:
        logger.error(f"❌ [ATS_STAGE_MAPPING] Failed to create notification: {e}")



from sqlalchemy import select


async def validate_multi_tenancy(
    db: AsyncSession,
    candidate_id: str,
    vacancy_id: str,
    company_id: str
) -> tuple[bool, str]:
    """
    Validate that candidate and vacancy belong to the specified company.
    Returns (is_valid, error_message).
    
    Uses VacancyCandidate for candidate company validation since the main
    Candidate model may not have direct company_id.
    """
    from app.models.candidate import VacancyCandidate
    from app.models.job_vacancy import JobVacancy
    
    vacancy_result = await db.execute(
        select(JobVacancy).where(
            JobVacancy.id == vacancy_id,
            JobVacancy.company_id == company_id
        )
    )
    if not vacancy_result.scalar_one_or_none():
        return False, "Vacancy not found or belongs to different company"
    
    vacancy_candidate_result = await db.execute(
        select(VacancyCandidate).where(
            VacancyCandidate.candidate_id == candidate_id,
            VacancyCandidate.vacancy_id == vacancy_id,
            VacancyCandidate.company_id == company_id
        )
    )
    if not vacancy_candidate_result.scalar_one_or_none():
        return False, "Candidate not found or not associated with this vacancy/company"
    
    return True, ""


class UpdateTriggerRequest(BaseModel):
    """Request model for updating a trigger."""
    enabled: bool


class ExecuteActionRequest(BaseModel):
    """Request model for executing a specific automation action."""
    action_type: Literal['email', 'whatsapp', 'triagem_wsi', 'agendar_entrevista', 'apenas_mover'] = Field(
        ..., description="Type of action to execute"
    )
    candidate_id: str = Field(..., description="ID of the candidate")
    vacancy_id: str = Field(..., description="ID of the vacancy")
    company_id: str = Field(..., description="Company ID for multi-tenancy")
    channel: Literal['email', 'whatsapp'] | None = Field(
        None, description="Communication channel (for triagem_wsi)"
    )
    template_id: str | None = Field(None, description="Template ID to use")
    subject: str | None = Field(None, description="Email subject (for email actions)")
    message: str | None = Field(None, description="Custom message content")
    metadata: dict[str, Any] | None = Field(default=None, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "action_type": "email",
                "candidate_id": "cand_123",
                "vacancy_id": "vac_456",
                "company_id": "comp_789",
                "channel": "email",
                "subject": "Próximos passos - Processo Seletivo",
                "message": "Olá, você foi aprovado para a próxima etapa!"
            }
        }


class InterviewScheduledRequest(BaseModel):
    """Request model for interview scheduled trigger."""
    candidate_id: str = Field(..., description="ID of the candidate")
    vacancy_id: str = Field(..., description="ID of the vacancy")
    company_id: str = Field(..., description="Company ID for multi-tenancy")
    interview_datetime: datetime = Field(..., description="Interview date and time")
    interview_link: str | None = Field(None, description="Video call link for the interview")
    interviewer_name: str | None = Field("Equipe", description="Name of the interviewer")
    interviewer_email: str | None = Field(None, description="Email of the interviewer")
    interview_type: str = Field("behavioral", description="Type: technical, behavioral, cultural")
    duration_minutes: int = Field(60, description="Interview duration in minutes")
    notes: str | None = Field(None, description="Additional notes for the interview")
    candidate_name: str | None = Field(None, description="Name of the candidate")
    candidate_email: str | None = Field(None, description="Email of the candidate")
    candidate_phone: str | None = Field(None, description="Phone number of the candidate")
    job_title: str | None = Field(None, description="Title of the job vacancy")
    organizer_email: str | None = Field(None, description="Email of the meeting organizer (recruiter)")

    class Config:
        json_schema_extra = {
            "example": {
                "candidate_id": "cand_123",
                "vacancy_id": "vac_456",
                "company_id": "comp_789",
                "interview_datetime": "2026-01-25T10:00:00",
                "interview_link": "https://meet.google.com/abc-defg-hij",
                "interviewer_name": "Maria Silva",
                "interviewer_email": "maria.silva@empresa.com",
                "interview_type": "technical",
                "duration_minutes": 60,
                "candidate_name": "João Santos",
                "candidate_email": "joao.santos@email.com",
                "job_title": "Desenvolvedor Senior"
            }
        }


class InterviewCompletedRequest(BaseModel):
    """Request model for interview completed trigger."""
    candidate_id: str = Field(..., description="ID of the candidate")
    vacancy_id: str = Field(..., description="ID of the vacancy")
    company_id: str = Field(..., description="Company ID for multi-tenancy")
    interview_id: str = Field(..., description="ID of the completed interview")
    interview_type: str = Field("behavioral", description="Type: technical, behavioral, cultural")
    interviewer_notes: str | None = Field(None, description="Notes from the interviewer")
    competency_ratings: dict[str, float] | None = Field(None, description="Ratings per competency (1-5)")
    overall_impression: str | None = Field(None, description="Overall impression from interviewer")
    transcript: str | None = Field(None, description="Interview transcript if recorded")
    candidate_name: str | None = Field(None, description="Name of the candidate")
    job_title: str | None = Field(None, description="Title of the job vacancy")
    interviewer_name: str | None = Field(None, description="Name of the interviewer")

    class Config:
        json_schema_extra = {
            "example": {
                "candidate_id": "cand_123",
                "vacancy_id": "vac_456",
                "company_id": "comp_789",
                "interview_id": "int_101",
                "interview_type": "technical",
                "interviewer_notes": "Candidato demonstrou conhecimento sólido em Python e arquitetura.",
                "competency_ratings": {
                    "technical_skills": 4.5,
                    "problem_solving": 4.0,
                    "communication": 3.5,
                    "teamwork": 4.0
                },
                "overall_impression": "Candidato forte, recomendo para próxima etapa.",
                "candidate_name": "João Santos",
                "job_title": "Desenvolvedor Senior",
                "interviewer_name": "Maria Silva"
            }
        }


class CandidateInactiveRequest(BaseModel):
    """Request model for candidate inactive trigger."""
    candidate_id: str = Field(..., description="ID of the candidate")
    vacancy_id: str = Field(..., description="ID of the vacancy")
    company_id: str = Field(..., description="Company ID for multi-tenancy")
    days_inactive: int = Field(7, description="Number of days the candidate has been inactive")
    last_activity_date: datetime | None = Field(None, description="Date of last activity")
    current_stage: str | None = Field(None, description="Current pipeline stage: Triagem, Entrevista, Proposta")
    candidate_name: str | None = Field(None, description="Name of the candidate")
    candidate_email: str | None = Field(None, description="Email of the candidate")
    candidate_phone: str | None = Field(None, description="Phone number of the candidate")
    job_title: str | None = Field(None, description="Title of the job vacancy")

    class Config:
        json_schema_extra = {
            "example": {
                "candidate_id": "cand_123",
                "vacancy_id": "vac_456",
                "company_id": "comp_789",
                "days_inactive": 7,
                "last_activity_date": "2026-01-12T10:30:00",
                "current_stage": "Triagem",
                "candidate_name": "João Santos",
                "candidate_email": "joao.santos@email.com",
                "candidate_phone": "+5511999999999",
                "job_title": "Desenvolvedor Senior"
            }
        }


class ATSSyncRequest(BaseModel):
    """Request model for ATS synchronization trigger."""
    candidate_id: str = Field(..., description="ID of the candidate in LIA")
    vacancy_id: str = Field(..., description="ID of the vacancy in LIA")
    company_id: str = Field(..., description="Company ID for multi-tenancy")
    new_stage: str = Field(..., description="New stage name in LIA (e.g., Triagem, Entrevista)")
    previous_stage: str | None = Field(None, description="Previous stage name in LIA")
    ats_platform: str = Field("gupy", description="Target ATS platform: gupy, pandape, merge")
    ats_candidate_id: str | None = Field(None, description="External ATS candidate ID (if known)")
    ats_vacancy_id: str | None = Field(None, description="External ATS vacancy/job ID (if known)")
    sync_direction: str = Field("outbound", description="Sync direction: outbound (LIA→ATS) or inbound (ATS→LIA)")
    candidate_name: str | None = Field(None, description="Name of the candidate")
    candidate_email: str | None = Field(None, description="Email of the candidate")
    job_title: str | None = Field(None, description="Title of the job vacancy")
    sync_reason: str | None = Field(None, description="Reason for the sync (e.g., stage_change, manual_sync)")

    class Config:
        json_schema_extra = {
            "example": {
                "candidate_id": "cand_123",
                "vacancy_id": "vac_456",
                "company_id": "comp_789",
                "new_stage": "Entrevista",
                "previous_stage": "Triagem",
                "ats_platform": "gupy",
                "ats_candidate_id": "gupy_app_789",
                "ats_vacancy_id": "gupy_job_456",
                "sync_direction": "outbound",
                "candidate_name": "João Santos",
                "candidate_email": "joao.santos@email.com",
                "job_title": "Desenvolvedor Senior",
                "sync_reason": "stage_change"
            }
        }




# --- Additional Pydantic models used by event_handlers and triggers ---

class ScreenCandidateRequest(BaseModel):
    """Request model for screening a candidate against a vacancy."""
    candidate_id: str = Field(..., description="ID of the candidate to screen")
    vacancy_id: str = Field(..., description="ID of the job vacancy")
    company_id: str = Field(..., description="Company ID for multi-tenancy")

    class Config:
        json_schema_extra = {
            "example": {
                "candidate_id": "cand_123",
                "vacancy_id": "vac_456",
                "company_id": "comp_789"
            }
        }



class TriggerEventRequest(BaseModel):
    """Request model for triggering an automation event."""
    event_type: str = Field(..., description="Type of event to trigger (e.g., job_created, screening_completed)")
    entity_id: str = Field(..., description="ID of the related entity (job, candidate, etc)")
    company_id: str = Field(..., description="Company ID for multi-tenancy")
    entity_type: str = Field(default="job", description="Type of entity (job, candidate, interview)")
    metadata: dict[str, Any] | None = Field(default=None, description="Additional event context data")

    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "job_created",
                "entity_id": "job_123",
                "company_id": "comp_456",
                "entity_type": "job",
                "metadata": {
                    "job_title": "Desenvolvedor Backend Senior",
                    "created_by": "user_789"
                }
            }
        }



class ScreeningCompletedRequest(BaseModel):
    """Request model for conversational screening completed trigger."""
    candidate_id: str = Field(..., description="ID of the candidate who completed screening")
    vacancy_id: str = Field(..., description="ID of the job vacancy")
    company_id: str = Field(..., description="Company ID for multi-tenancy")
    screening_type: Literal['voice', 'chat', 'whatsapp'] = Field(
        ..., description="Type of conversational screening completed"
    )
    transcript: str | None = Field(None, description="Full conversation transcript")
    responses: list[dict[str, Any]] | None = Field(
        default=None, 
        description="Structured responses from the screening conversation"
    )
    competency_weights: dict[str, float] | None = Field(
        default=None,
        description="Optional custom competency weights for WSI calculation"
    )
    metadata: dict[str, Any] | None = Field(default=None, description="Additional screening metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "candidate_id": "cand_123",
                "vacancy_id": "vac_456",
                "company_id": "comp_789",
                "screening_type": "whatsapp",
                "transcript": "Candidato: Olá, estou interessado...\nLIA: Conte sobre sua experiência...",
                "responses": [
                    {"question_id": "q1", "competency": "Python", "response": "Tenho 5 anos de experiência..."},
                    {"question_id": "q2", "competency": "Liderança", "response": "Liderei uma equipe de 8 pessoas..."}
                ],
                "metadata": {
                    "duration_seconds": 420,
                    "questions_answered": 6
                }
            }
        }


# WSI Pass/Fail threshold constants — aligned with canonical WSI_CUTOFFS
# from wsi_deterministic_scorer.py (Spec §10.3)
WSI_PASS_THRESHOLD = 3.75  # approved_auto ≥ 3.75/5 (= 7.5/10)
WSI_REVIEW_THRESHOLD = 3.0  # review_min ≥ 3.0/5 (= 6.0/10)

class BulkSuggestionRequest(BaseModel):
    """Request model for bulk suggestion operations."""
    suggestion_ids: list[str] = Field(..., description="List of suggestion IDs to process")
    company_id: str = Field(..., description="Company ID for multi-tenancy validation")
    reviewer_id: str | None = Field(None, description="ID of the user reviewing suggestions")
    reason: str | None = Field(None, description="Reason for rejection (bulk reject only)")



class CandidateNoShowRequest(BaseModel):
    """Request model for candidate no-show trigger."""
    candidate_id: str = Field(..., description="ID of the candidate who didn't show")
    vacancy_id: str = Field(..., description="ID of the vacancy")
    company_id: str = Field(..., description="Company ID for multi-tenancy")
    interview_id: str = Field(..., description="ID of the missed interview")
    interview_datetime: datetime = Field(..., description="Interview date and time that was missed")
    interview_type: str = Field("technical", description="Type: technical, behavioral, cultural")
    no_show_count: int = Field(1, description="How many times candidate didn't show")
    candidate_name: str | None = Field(None, description="Name of the candidate")
    candidate_email: str | None = Field(None, description="Email of the candidate")
    candidate_phone: str | None = Field(None, description="Phone number of the candidate")
    job_title: str | None = Field(None, description="Title of the job vacancy")
    interviewer_name: str | None = Field(None, description="Name of the interviewer")

    class Config:
        json_schema_extra = {
            "example": {
                "candidate_id": "cand_123",
                "vacancy_id": "vac_456",
                "company_id": "comp_789",
                "interview_id": "int_101",
                "interview_datetime": "2026-01-19T10:00:00",
                "interview_type": "technical",
                "no_show_count": 1,
                "candidate_name": "João Santos",
                "candidate_email": "joao.santos@email.com",
                "candidate_phone": "+5511999999999",
                "job_title": "Desenvolvedor Senior",
                "interviewer_name": "Maria Silva"
            }
        }



class OfferSentPayload(BaseModel):
    """Request model for offer sent trigger."""
    candidate_id: str = Field(..., description="ID of the candidate")
    vacancy_id: str = Field(..., description="ID of the vacancy")
    company_id: str = Field(..., description="Company ID for multi-tenancy")
    offer_details: dict[str, Any] | None = Field(None, description="Details of the offer")
    salary_offered: float | None = Field(None, description="Salary amount offered")
    start_date: str | None = Field(None, description="Proposed start date")
    response_deadline: str | None = Field(None, description="Date by which candidate should respond")
    candidate_name: str | None = Field(None, description="Name of the candidate")
    candidate_email: str | None = Field(None, description="Email of the candidate")
    job_title: str | None = Field(None, description="Title of the job vacancy")

    class Config:
        json_schema_extra = {
            "example": {
                "candidate_id": "cand_123",
                "vacancy_id": "vac_456",
                "company_id": "comp_789",
                "offer_details": {"position": "Senior Developer", "benefits": ["health", "dental"]},
                "salary_offered": 15000.00,
                "start_date": "2026-02-01",
                "response_deadline": "2026-01-25",
                "candidate_name": "João Santos",
                "candidate_email": "joao.santos@email.com",
                "job_title": "Desenvolvedor Senior"
            }
        }



class CandidateHiredPayload(BaseModel):
    """Request model for candidate hired trigger."""
    candidate_id: str = Field(..., description="ID of the candidate")
    vacancy_id: str = Field(..., description="ID of the vacancy")
    company_id: str = Field(..., description="Company ID for multi-tenancy")
    hire_date: str | None = Field(None, description="Official hire date")
    final_salary: float | None = Field(None, description="Final agreed salary")
    department: str | None = Field(None, description="Department the candidate will join")
    manager_id: str | None = Field(None, description="ID of the direct manager")
    candidate_name: str | None = Field(None, description="Name of the candidate")
    candidate_email: str | None = Field(None, description="Email of the candidate")
    job_title: str | None = Field(None, description="Title of the job vacancy")

    class Config:
        json_schema_extra = {
            "example": {
                "candidate_id": "cand_123",
                "vacancy_id": "vac_456",
                "company_id": "comp_789",
                "hire_date": "2026-02-01",
                "final_salary": 16000.00,
                "department": "Engineering",
                "manager_id": "user_789",
                "candidate_name": "João Santos",
                "candidate_email": "joao.santos@email.com",
                "job_title": "Desenvolvedor Senior"
            }
        }



class CandidateRejectedPayload(BaseModel):
    """Request model for candidate rejected trigger."""
    candidate_id: str = Field(..., description="ID of the candidate")
    vacancy_id: str = Field(..., description="ID of the vacancy")
    company_id: str = Field(..., description="Company ID for multi-tenancy")
    rejection_reason: str | None = Field(None, description="Reason for rejection")
    rejection_stage: str | None = Field(None, description="Stage at which rejected")
    add_to_talent_pool: bool = Field(True, description="Whether to add to talent pool")
    send_feedback: bool = Field(True, description="Whether to send feedback email")
    candidate_name: str | None = Field(None, description="Name of the candidate")
    candidate_email: str | None = Field(None, description="Email of the candidate")
    job_title: str | None = Field(None, description="Title of the job vacancy")
    reviewer_id: str | None = Field(None, description="ID do usuário humano que autorizou a rejeição (obrigatório — LGPD art. 20 / EU AI Act art. 14)")

    class Config:
        json_schema_extra = {
            "example": {
                "candidate_id": "cand_123",
                "vacancy_id": "vac_456",
                "company_id": "comp_789",
                "rejection_reason": "Outro candidato apresentou maior aderência técnica",
                "rejection_stage": "Entrevista Técnica",
                "add_to_talent_pool": True,
                "send_feedback": True,
                "candidate_name": "Maria Silva",
                "candidate_email": "maria.silva@email.com",
                "job_title": "Desenvolvedor Senior"
            }
        }



class RejectSuggestionRequest(BaseModel):
    """Request model for rejecting an AI suggestion."""
    reason: str | None = Field(None, description="Reason for rejecting the suggestion")



