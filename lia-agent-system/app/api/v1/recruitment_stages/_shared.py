"""
Shared imports, constants, Pydantic models, and helper functions for the
recruitment_stages package.
"""
import asyncio
import json
import logging
import re
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from starlette.responses import StreamingResponse

from app.auth.dependencies import (
    assert_resource_ownership,
    get_current_active_user,
    get_current_user_or_demo,
    get_user_company_id,
    require_admin_or_recruiter,
)
from app.auth.models import User
from app.core.config import settings
from app.domains.communication.services.return_event_service import (
    RETURN_EVENT_CONFIG,
    ReturnEventService,
)
from app.domains.recruiter_assistant.services.pipeline_stage_service import TransitionError, pipeline_stage_service
from app.domains.recruitment.dependencies import (
    get_ats_mapping_repo,
    get_screening_question_repo,
    get_stage_repo,
    get_sub_status_repo,
)
from app.domains.recruitment.repositories.ats_mapping_repository import ATSMappingRepository
from app.domains.recruitment.repositories.recruitment_stage_repository import RecruitmentStageRepository
from app.domains.recruitment.repositories.screening_question_repository import ScreeningQuestionRepository
from app.domains.recruitment.repositories.sub_status_repository import SubStatusRepository
from app.models.recruitment_stages import (
    CANONICAL_SUB_STATUSES,
    DEFAULT_RECRUITMENT_STAGES,
    DEFAULT_SUB_STATUSES,
    GUPY_STAGE_MAPPINGS,
    PANDAPE_STAGE_MAPPINGS,
    STANDARD_STAGE_CATALOG,
    RecruitmentStage,
    ScreeningQuestion,
)
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_ACTION_BEHAVIORS = [
    "intake", "screening", "scheduling", "evaluation", "verification",
    "offer", "passive", "conclusion_hired", "conclusion_rejected", "conclusion_declined"
]

STAGE_DISPLAY_NAMES = {s["name"]: s["display_name"] for s in DEFAULT_RECRUITMENT_STAGES}

ACTION_BEHAVIOR_LABELS = {
    "intake": "Adicionar ao Funil",
    "screening": "Iniciar Triagem",
    "scheduling": "Agendar Entrevista",
    "evaluation": "Enviar Avaliação",
    "verification": "Solicitar Referências",
    "offer": "Enviar Proposta",
    "passive": "Mover Candidato",
    "conclusion_hired": "Confirmar Contratação",
    "conclusion_rejected": "Confirmar Reprovação",
    "conclusion_declined": "Registrar Recusa",
}

# ---------------------------------------------------------------------------
# Pydantic models — Stage CRUD
# ---------------------------------------------------------------------------

class StageCreate(WeDoBaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    stage_order: int = Field(default=0, ge=0)
    color: str | None = Field(default="#6B7280", max_length=20)
    icon: str | None = Field(default="circle", max_length=50)
    stage_type: str = Field(default="active")
    is_initial: bool = False
    is_final: bool = False
    is_rejection: bool = False
    is_hired: bool = False
    allowed_transitions: list[str] = Field(default_factory=list)
    sla_hours: int | None = None
    action_behavior: str = Field(default="passive", description="Action behavior type for this stage")


class StageConfigUpdate(WeDoBaseModel):
    action_behavior: str | None = Field(None, description="Tipo de ação (screening, scheduling, evaluation, verification, offer, passive, etc.)")
    default_channel: str | None = Field(None, description="Canal padrão (email, whatsapp, email_whatsapp)")
    sla_hours: int | None = Field(None, description="SLA em horas")


class StageUpdate(WeDoBaseModel):
    display_name: str | None = None
    description: str | None = None
    stage_order: int | None = None
    color: str | None = None
    icon: str | None = None
    allowed_transitions: list[str] | None = None
    sla_hours: int | None = None
    is_active: bool | None = None
    action_behavior: str | None = None


class InlineStageEdit(WeDoBaseModel):
    display_name: str | None = Field(None, min_length=1, max_length=100)
    is_active: bool | None = None
    sla_hours: int | None = Field(None, ge=0)
    stage_order: int | None = Field(None, ge=0)


class StageReorderItem(BaseModel):
    stage_id: str
    new_order: int


class StageReorderRequest(WeDoBaseModel):
    stages: list[StageReorderItem]


# ---------------------------------------------------------------------------
# Pydantic models — Sub-status
# ---------------------------------------------------------------------------

class SubStatusCreate(WeDoBaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=150)
    description: str | None = None
    sub_status_order: int = Field(default=0, ge=0)
    color: str | None = None
    icon: str | None = None
    is_default: bool = False
    is_waiting: bool = False
    waiting_for: str | None = None
    sla_hours: int | None = None
    is_active: bool | None = None


# ---------------------------------------------------------------------------
# Pydantic models — ATS Mapping
# ---------------------------------------------------------------------------

class ATSMappingCreate(WeDoBaseModel):
    ats_type: str = Field(..., description="gupy, pandape, merge")
    ats_stage_id: str | None = None
    ats_stage_name: str = Field(..., min_length=1, max_length=255)
    ats_stage_order: int | None = None
    wedotalent_stage_id: str
    wedotalent_sub_status_id: str | None = None
    mapping_direction: str = Field(default="both", description="import, export, both")
    is_default_for_sync: bool = False
    priority: int = Field(default=0, ge=0)
    notes: str | None = None


# ---------------------------------------------------------------------------
# Pydantic models — Pipeline
# ---------------------------------------------------------------------------

class CompanyPipelineStageItem(WeDoBaseModel):
    id: str | None = None
    catalog_id: str | None = None
    name: str | None = None
    display_name: str | None = None
    stage_order: int
    color: str | None = None
    icon: str | None = None
    sla_hours: int | None = None
    is_active: bool = True
    action_behavior: str | None = None
    default_channel: str | None = None


class CompanyPipelineUpdate(WeDoBaseModel):
    stages: list[CompanyPipelineStageItem]


class JobPipelineStageItem(WeDoBaseModel):
    stage_name: str
    stage_order: int
    is_active: bool = True
    sla_hours: int | None = None
    display_name: str | None = None
    color: str | None = None
    icon: str | None = None


class JobPipelineUpdate(WeDoBaseModel):
    stages: list[JobPipelineStageItem]


# ---------------------------------------------------------------------------
# Pydantic models — Transition
# ---------------------------------------------------------------------------

class TransitionRequest(WeDoBaseModel):
    vacancy_candidate_id: str
    to_stage: str
    to_sub_status: str | None = None
    triggered_by: str = "user"
    triggered_by_user_id: str | None = None
    source_agent: str | None = None
    reason: str | None = None
    notes: str | None = None
    force: bool = False


class ChatMessageItem(BaseModel):
    role: str = "user"
    content: str = ""
    timestamp: float | None = None


class InterpretContextRequest(WeDoBaseModel):
    candidate_id: str
    candidate_name: str | None = None
    job_title: str | None = None
    job_id: str | None = None
    from_stage: str
    to_stage: str
    action_behavior: str
    prompt: str | None = None
    message_history: list[ChatMessageItem] | None = None
    conversation_id: str | None = Field(None, description="Conversation ID for multi-turn context persistence")


class TaskItem(BaseModel):
    type: str = ""
    description: str = ""
    data_type: str | None = None
    status: str = "scheduled"


class LearnedSuggestion(BaseModel):
    key: str = ""
    value: str = ""
    frequency: int = 0
    source: str = "recruiter_history"


class InterpretContextResponse(BaseModel):
    suggested_sub_status: str
    suggested_action: str
    action_label: str
    urgency: str
    lia_message: str | None = None
    extracted_preferences: dict | None = None
    ai_powered: bool = False
    confidence: float | None = None
    tasks: list[TaskItem] | None = None
    out_of_scope: bool = False
    candidate_info: dict | None = None
    learned_suggestions: list[LearnedSuggestion] | None = None
    fairness_result: dict | None = None
    layer: int = 1
    conversation_id: str | None = None


class DispatchResult(BaseModel):
    success: bool
    channel: str | None = None
    message_id: str | None = None
    template_name: str | None = None
    recipient: str | None = None
    mock: bool = False
    error: str | None = None
    ai_personalized: bool = False


class TransitionExecuteRequest(WeDoBaseModel):
    vacancy_candidate_id: str
    to_stage: str
    from_stage: str | None = None
    vacancy_id: str | None = None
    sub_status: str | None = None
    action: str | None = "just_move"
    prompt: str | None = None
    channel: str | None = "email"
    action_behavior: str | None = None
    extracted_preferences: dict[str, Any] | None = None
    hitl_approved: bool = False  # AUD-4: FE seta True ao confirmar (gate REST)


class PreviewFeedbackRequest(WeDoBaseModel):
    vacancy_candidate_id: str
    to_stage: str
    sub_status: str | None = None
    channel: str | None = "email"
    prompt: str | None = None


class PreviewFeedbackResponse(BaseModel):
    body: str
    subject: str | None = None
    generated_by: str = "unknown"
    ai_personalized: bool = False
    fairness_blocked: bool = False
    high_risk: bool = False
    uses_template_only: bool = False
    channel: str = "email"


class TransitionExecuteResponse(BaseModel):
    success: bool
    message: str
    candidate_id: str
    new_stage: str
    new_sub_status: str | None = None
    dispatch_results: list[DispatchResult] | None = None
    predicted_sub_status: str | None = None
    prediction_confidence: float | None = None
    requires_approval: bool = False  # AUD-4: feedback segurado por HITL gate


# ---------------------------------------------------------------------------
# Pydantic models — Return Events
# ---------------------------------------------------------------------------

class ReturnEventRequest(WeDoBaseModel):
    vacancy_candidate_id: str = Field(..., description="ID do VacancyCandidate")
    event_type: str = Field(..., description="Tipo do evento de retorno (screening_complete, interview_confirmed, etc.)")
    metadata: dict | None = Field(default=None, description="Dados adicionais do evento (score, notas, etc.)")
    triggered_by: str | None = Field(default=None, description="Quem disparou o evento (system, webhook, candidate)")


class ReturnEventResponse(BaseModel):
    success: bool
    event_type: str
    new_sub_status: str | None = None
    new_stage: str | None = None
    activity_id: str | None = None
    notification_sent: bool = False
    auto_moved: bool = False
    error: str | None = None


class BulkReturnEventRequest(WeDoBaseModel):
    events: list[ReturnEventRequest] = Field(..., description="Lista de eventos de retorno para processar em lote")


# ---------------------------------------------------------------------------
# Pydantic models — Infer Behavior
# ---------------------------------------------------------------------------

class InferBehaviorRequest(WeDoBaseModel):
    stage_name: str = Field(..., min_length=1, max_length=200, description="Nome da etapa customizada")
    description: str | None = None


class InferBehaviorResponse(BaseModel):
    suggested_behavior: str
    confidence: float
    alternatives: list[dict] = []
    method: str = "keyword"


# ---------------------------------------------------------------------------
# Shared helper functions
# ---------------------------------------------------------------------------

def _extract_scheduling_preferences(text: str) -> dict:
    preferences = {}
    days = re.findall(
        r'\b(segunda|terça|terca|quarta|quinta|sexta|sábado|sabado|domingo|hoje|amanhã|amanha)\b',
        text.lower()
    )
    if days:
        preferences["date"] = days[0]
    times = re.findall(r'\b(\d{1,2}[h:]\d{0,2})\b', text.lower())
    if times:
        preferences["time"] = times[0]
    return preferences


def _determine_suggested_action(action_behavior: str, prompt: str | None) -> str:
    if prompt:
        prompt_lower = prompt.lower()
        auto_keywords = ["automático", "automatico", "lia", "auto", "agendar", "enviar"]
        manual_keywords = ["manual", "eu mesmo", "eu mesma", "não enviar", "nao enviar", "só mover", "so mover"]
        if any(kw in prompt_lower for kw in manual_keywords):
            return "manual"
        if any(kw in prompt_lower for kw in auto_keywords):
            return "lia_auto"
    if action_behavior in ("scheduling", "screening", "offer"):
        return "lia_auto"
    if action_behavior in ("passive", "intake"):
        return "just_move"
    return "manual"


def _get_default_sub_status(to_stage: str) -> str:
    subs = DEFAULT_SUB_STATUSES.get(to_stage, [])
    for s in subs:
        if s.get("is_default"):
            return s["name"]
    return subs[0]["name"] if subs else "novo"


def _determine_urgency(action_behavior: str) -> str:
    if action_behavior in ("conclusion_rejected", "conclusion_hired", "conclusion_declined"):
        return "high"
    if action_behavior in ("passive",):
        return "low"
    return "normal"


def _build_lia_message(
    to_stage: str,
    action_behavior: str,
    candidate_name: str | None,
    preferences: dict,
    suggested_action: str,
) -> str:
    display = STAGE_DISPLAY_NAMES.get(to_stage, to_stage)
    name = candidate_name or "o candidato"

    if action_behavior == "scheduling" and preferences:
        parts = []
        if "date" in preferences:
            parts.append(f"dia {preferences['date']}")
        if "time" in preferences:
            parts.append(f"às {preferences['time']}")
        if "format" in preferences:
            parts.append(f"({preferences['format']})")
        time_str = " ".join(parts)
        if time_str:
            return f"Entendido! Vou enviar o convite de entrevista para {time_str}. Ao confirmar, {name} receberá o convite por e-mail."
        return f"Vou enviar o convite de agendamento para {name}. Ao confirmar, o candidato será notificado."

    if action_behavior == "scheduling":
        return f"Vou enviar o convite de agendamento para {name}. Ao confirmar, o candidato será notificado por e-mail."

    if action_behavior == "screening":
        return f"Vou iniciar a triagem WSI com {name}. Ao confirmar, o candidato receberá as perguntas por e-mail."
    if action_behavior == "evaluation":
        return f"Vou enviar o teste técnico para {name}. Ao confirmar, o candidato receberá o link de avaliação."
    if action_behavior == "verification":
        return f"Vou solicitar os documentos necessários a {name}. Ao confirmar, o candidato receberá a solicitação."
    if action_behavior == "offer":
        return f"Vou preparar a proposta para {name}. Ao confirmar, o candidato será notificado."
    if action_behavior == "conclusion_hired":
        return f"Confirmando contratação de {name}! Ao confirmar, o processo será finalizado."
    if action_behavior == "conclusion_rejected":
        return f"Registrando reprovação de {name}. Ao confirmar, o candidato receberá o feedback."
    if action_behavior == "conclusion_declined":
        return f"Registrando recusa de proposta de {name}."

    if suggested_action == "just_move":
        return f"Movendo {name} para {display}"

    return f"Movendo {name} para {display}"


async def _get_company_pipeline(
    company_id: str,
    stage_repo: RecruitmentStageRepository,
    sub_status_repo: SubStatusRepository,
):
    stages = await stage_repo.list_for_company(company_id)

    if not stages:
        stages = await pipeline_stage_service.initialize_company_stages(
            company_id=company_id, db=stage_repo.db
        )
        if not stages:
            return []
        stages = await stage_repo.list_for_company(company_id)

    pipeline = []
    for stage in stages:
        stage_dict = stage.to_dict()
        sub_statuses = await sub_status_repo.list_for_stage(stage.id)
        stage_dict["sub_statuses"] = [s.to_dict() for s in sub_statuses]
        pipeline.append(stage_dict)
    return pipeline
