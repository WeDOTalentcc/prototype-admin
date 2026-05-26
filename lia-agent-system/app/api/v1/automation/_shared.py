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

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.automation.services.automation_service import AutomationService, automation_service, get_automation_service  # noqa: F401
from app.domains.automation.services.automation_trigger_service import automation_trigger_service  # noqa: F401
from app.domains.communication.services.communication_service import CommunicationService, communication_service, get_communication_service  # noqa: F401
from app.shared.services.audit_service import audit_service

logger = logging.getLogger(__name__)

def get_cv_scoring_service():
    """Return canonical CVScoringService singleton."""
    from app.domains.cv_screening.services.cv_scoring_service import cv_scoring_service
    return cv_scoring_service


def get_wsi_service():
    """Return canonical WSIService singleton."""
    from app.domains.cv_screening.services.wsi_service import wsi_service
    return wsi_service


# router is created in each sub-module and aggregated in __init__.py


def get_email_service():
    """Return canonical EmailService singleton."""
    from app.domains.communication.services.email_service import get_email_service as _canon_factory
    return _canon_factory()


def get_whatsapp_service():
    """Return canonical WhatsAppService singleton."""
    from app.domains.communication.services.whatsapp_service import whatsapp_service
    return whatsapp_service


def get_activity_service():
    """Return canonical ActivityService singleton."""
    from app.domains.analytics.services.activity_service import activity_service
    return activity_service


def get_scheduling_service():
    """Return canonical SchedulingService singleton."""
    from app.domains.interview_scheduling.services.scheduling_service import scheduling_service
    return scheduling_service


def get_calendar_service():
    """Return canonical CalendarService singleton."""
    from app.domains.interview_scheduling.services.calendar_service import calendar_service
    return calendar_service


def get_ats_sync_service():
    """Return canonical ATSSyncService singleton."""
    from app.domains.ats_integration.services.ats_sync_service import ats_sync_service
    return ats_sync_service


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
from app.shared.types import WeDoBaseModel


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

# RAILS-DEPRECATED: This endpoint manages Rails-owned entities (candidates/jobs/applies/users).
# Direct DB calls will be replaced by RailsAdapter after ats-api-rails handoff.
# See: app/domains/integrations_hub/services/rails_adapter.py
    
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


class UpdateTriggerRequest(WeDoBaseModel):
    """Request model for updating a trigger."""
    enabled: bool


class ExecuteActionRequest(WeDoBaseModel):
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


class InterviewScheduledRequest(WeDoBaseModel):
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


class InterviewCompletedRequest(WeDoBaseModel):
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


class CandidateInactiveRequest(WeDoBaseModel):
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


class ATSSyncRequest(WeDoBaseModel):
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

class ScreenCandidateRequest(WeDoBaseModel):
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



class TriggerEventRequest(WeDoBaseModel):
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



class ScreeningCompletedRequest(WeDoBaseModel):
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

class BulkSuggestionRequest(WeDoBaseModel):
    """Request model for bulk suggestion operations."""
    suggestion_ids: list[str] = Field(..., description="List of suggestion IDs to process")
    company_id: str = Field(..., description="Company ID for multi-tenancy validation")
    reviewer_id: str | None = Field(None, description="ID of the user reviewing suggestions")
    reason: str | None = Field(None, description="Reason for rejection (bulk reject only)")



class CandidateNoShowRequest(WeDoBaseModel):
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



class OfferSentPayload(WeDoBaseModel):
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



class CandidateHiredPayload(WeDoBaseModel):
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



class CandidateRejectedPayload(WeDoBaseModel):
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



class RejectSuggestionRequest(WeDoBaseModel):
    """Request model for rejecting an AI suggestion."""
    reason: str | None = Field(None, description="Reason for rejecting the suggestion")


class TriggerMetadata(BaseModel):
    """Common metadata returned by all trigger handlers."""
    candidate_id: str
    vacancy_id: str
    processed_at: str


class ScreeningWsiDetails(BaseModel):
    technical_wsi: float
    behavioral_wsi: float
    classification: str
    percentile: float | None = None


class ScreeningCandidateFeedback(BaseModel):
    decision: str
    main_message: str
    technical_strengths: list[str] | None = []
    development_opportunities: list[str] | None = []
    next_steps: list[str] | None = []


class ResponseMetadata(BaseModel):
    """Typed metadata envelope shared by all event-handler responses.

    Core fields are explicitly typed; handler-specific supplementary fields
    (e.g. screening_type, rejection_stage) are preserved via extra='allow'
    so the model is a concrete schema rather than an opaque dict while still
    accommodating per-trigger contextual data.
    """
    model_config = ConfigDict(extra='allow')

    trigger_id: str | None = None
    processed_at: str | None = None
    pipeline_version: str | None = None
    company_id: str | None = None
    candidate_id: str | None = None
    vacancy_id: str | None = None
    duration_ms: int | None = None


class ATSResponseData(BaseModel):
    """Typed wrapper for ATS platform response data in ATSSyncResponse.

    Replaces the opaque `dict | None` field with a structured model so that
    API consumers receive a documented contract rather than an arbitrary blob.
    """
    model_config = ConfigDict(extra='forbid')

    external_id: str | None = None
    ats_status: str | None = None
    ats_stage: str | None = None
    synced_at: str | None = None
    error_code: str | None = None
    raw_message: str | None = None


class ScreeningCompletedResponse(BaseModel):
    """Response for POST /handle-trigger/screening-completed."""
    success: bool
    trigger: str
    wsi_score: float
    wsi_details: ScreeningWsiDetails
    recommendation: str
    passed: bool
    communication_sent: bool
    notification_created: bool
    suggested_next_stage: str | None = None
    confidence: float
    candidate_feedback: ScreeningCandidateFeedback
    metadata: ResponseMetadata


class InterviewScheduledResponse(BaseModel):
    """Response for POST /handle-trigger/interview-scheduled."""
    success: bool
    trigger: str
    email_sent: bool
    whatsapp_sent: bool
    calendar_event_created: bool
    notification_created: bool
    interview_id: str | None = None
    calendar_event_id: str | None = None
    metadata: ResponseMetadata


class ParecerDetails(BaseModel):
    id: str | None = None
    summary: str | None = None
    strengths: list[str] | None = []
    development_areas: list[str] | None = []
    recommendation: str | None = None
    average_rating: float | None = None


class InterviewCompletedResponse(BaseModel):
    """Response for POST /handle-trigger/interview-completed."""
    success: bool
    trigger: str
    parecer: ParecerDetails
    suggested_next_stage: str | None = None
    confidence: float
    notification_created: bool
    metadata: ResponseMetadata


class CommunicationFailure(BaseModel):
    """Typed record for a single communication channel failure."""
    channel: str
    error: str


class CandidateInactiveResponse(BaseModel):
    """Response for POST /handle-trigger/candidate-inactive."""
    success: bool
    partial_success: bool | None = None
    trigger: str
    days_inactive: int | None = None
    follow_up_sent: bool
    follow_up_type: str | None = None
    email_sent: bool
    whatsapp_sent: bool
    notification_created: bool
    communication_failures: list[CommunicationFailure] | None = None
    metadata: ResponseMetadata


class NoShowDetails(BaseModel):
    email_sent: bool
    whatsapp_sent: bool
    recommendation: str | None = None
    confidence_score: float | None = None


class CandidateNoShowResponse(BaseModel):
    """Response for POST /handle-trigger/candidate-no-show."""
    success: bool
    trigger: str
    no_show_count: int | None = None
    action_taken: str | None = None
    communication_sent: bool
    suggestion_created: bool
    notification_created: bool
    details: NoShowDetails
    metadata: ResponseMetadata


class ATSStageMappingDetails(BaseModel):
    lia_stage: str
    ats_stage: str


class ATSSyncResponse(BaseModel):
    """Response for POST /handle-trigger/ats-sync."""
    success: bool
    trigger: str
    ats_platform: str
    sync_status: str
    sync_direction: str
    stage_mapping: ATSStageMappingDetails
    ats_response: ATSResponseData | None = None
    error: str | None = None
    metadata: ResponseMetadata


class OfferSentDetails(BaseModel):
    email_sent: bool
    notification_created: bool
    ats_synced: bool


class OfferSentResponse(BaseModel):
    """Response for POST /handle-trigger/offer-sent."""
    success: bool
    trigger: str
    actions: list[str] | None = []
    details: OfferSentDetails
    metadata: ResponseMetadata


class CandidateHiredDetails(BaseModel):
    email_sent: bool
    stage_updated: bool
    notification_created: bool
    ats_synced: bool


class CandidateHiredResponse(BaseModel):
    """Response for POST /handle-trigger/candidate-hired."""
    success: bool
    trigger: str
    actions: list[str] | None = []
    details: CandidateHiredDetails
    metadata: ResponseMetadata


class CandidateRejectedDetails(BaseModel):
    email_sent: bool
    stage_updated: bool
    added_to_talent_pool: bool
    ats_synced: bool


class CandidateRejectedResponse(BaseModel):
    """Response for POST /handle-trigger/candidate-rejected."""
    success: bool
    trigger: str
    actions: list[str] | None = []
    details: CandidateRejectedDetails
    metadata: ResponseMetadata





# ---------------------------------------------------------------------------
# Helper: log_automation_execution
# ---------------------------------------------------------------------------

async def log_automation_execution(
    db,
    *,
    trigger_event: str,
    trigger_data: dict,
    candidate_id: str,
    vacancy_id: str,
    company_id: str,
    action_executed: str,
    action_result: dict,
    status: str = "success",
    execution_time_ms: int = 0,
) -> None:
    """Create an AutomationExecutionLog entry with error handling.

    Absorbs the identical try/except + db.add() pattern that was repeated
    across every event handler.
    """
    try:
        from app.models.automation import AutomationExecutionLog

        db.add(AutomationExecutionLog(
            company_id=company_id,
            trigger_event=trigger_event,
            trigger_data=trigger_data,
            candidate_id=candidate_id,
            vacancy_id=vacancy_id,
            action_executed=action_executed,
            action_result=action_result,
            status=status,
            execution_time_ms=execution_time_ms,
        ))
        logger.info(f"📝 [{trigger_event.upper()}] Automation execution log created")
    except Exception as e:
        logger.error(f"❌ [{trigger_event.upper()}] Failed to create execution log: {e}")


# ---------------------------------------------------------------------------
# Helper: ensure_company_access
# ---------------------------------------------------------------------------

async def ensure_company_access(
    db,
    *,
    candidate_id: str,
    vacancy_id: str,
    company_id: str,
    handler_tag: str = "HANDLER",
) -> None:
    """Validate multi-tenancy and raise HTTP 403 on mismatch.

    Combines the validate_multi_tenancy call with the repeated
    if-not-valid / log-warning / raise-HTTPException pattern.
    """
    is_valid, error_message = await validate_multi_tenancy(
        db=db,
        candidate_id=candidate_id,
        vacancy_id=vacancy_id,
        company_id=company_id,
    )
    if not is_valid:
        logger.warning(f"🚫 [{handler_tag}] Multi-tenancy validation failed: {error_message}")
        raise HTTPException(status_code=403, detail=error_message)
