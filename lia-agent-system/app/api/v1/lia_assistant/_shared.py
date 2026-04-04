"""
Shared imports, constants, Pydantic models, and helper utilities used
across all lia_assistant sub-modules.
"""
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from fastapi import APIRouter, HTTPException, Query, Depends, Header, UploadFile, File, Response, WebSocket, WebSocketDisconnect, Form
from pydantic import BaseModel
import base64
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import logging
import re
import json

from sqlalchemy import select, func, and_, or_, case, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import JobVacancy, Candidate
from app.models.job_draft import JobDraft, DraftFieldHistory, JobDraftStatus, ChangeType
from app.services.intent_classifier import (
    IntentClassifierService, IntentType, ClassificationResult, intent_classifier_service
)
from app.services.job_insights_service import JobInsightsService
from app.services.market_benchmark_service import MarketBenchmarkService
from app.services.feedback_learning_service import FeedbackLearningService
from app.services.llm import LLMService
from app.services.organization_catalog_service import OrganizationCatalogService
from app.services.confidence_policy_service import ConfidencePolicyService
from app.services.config_completeness_service import ConfigCompletenessService
from app.services.skills_catalog_service import skills_catalog_service
from app.services.responsibilities_catalog_service import responsibilities_catalog_service
from app.services.jd_generator_service import jd_generator_service
from app.services.learning_hub_service import learning_hub_service
# SourcingAgent and AvaliadorWSIAgent moved to lia_assistant_wizard_stages.py (Phase 6 deprecation)
from app.services.vacancy_search_service import (
    vacancy_search_service, VacancySummary, VacancyFullDetails
)
from app.services.enhanced_intent_classifier import (
    EnhancedIntentClassifierService,
    EnhancedIntentType,
    EnhancedClassificationResult,
    enhanced_intent_classifier
)
from app.services.context_aggregator_service import (
    ContextAggregatorService,
    AggregatedContext,
    context_aggregator
)
from app.services.knowledge_base_service import (
    KnowledgeBaseService,
    KnowledgeResponse,
    knowledge_base
)
from app.models.structured_responses import (
    OrchestrationDecision,
    IntentClassification,
    SalaryAnalysis,
    JobFieldUpdate,
    WizardOrchestrationResult,
)
from app.services.llm import llm_service
from app.services.graph_runner import graph_runner_service, GraphRunnerService
from app.services.feedback_service import feedback_service, FeedbackService
from app.services.voice_service import voice_service, VoiceServiceError, TranscriptionError, SynthesisError
from app.services.autonomous_agent_service import autonomous_agent_service
from app.services.multimodal_service import (
    multimodal_service,
    MultimodalServiceError,
    ImageAnalysisError,
    VideoAnalysisError,
    DocumentAnalysisError
)
from lia_agents_core.state_machine import WizardStage
from app.domains.recruiter_assistant.services.wizard_analytics_service import (
    wizard_analytics, detect_wizard_analytics_command,
)
from app.domains.recruiter_assistant.services.wizard_action_executor import (
    wizard_action_executor, detect_wizard_action, WizardActionResult, robust_json_parse,
    WIZARD_ACTIONABLE_INTENTS,
)
from app.orchestrator.pending_action import PendingActionState, pending_action_store
from app.orchestrator.action_executor import is_confirmation, is_rejection
from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.dependencies.token_budget import require_token_budget

logger = logging.getLogger(__name__)

DEFAULT_COMPANY_UUID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
USE_ENHANCED_CLASSIFIER = True

# ---------------------------------------------------------------------------
# Shared service instances
# ---------------------------------------------------------------------------
job_insights_service = JobInsightsService()
market_benchmark_service = MarketBenchmarkService()
feedback_learning_service = FeedbackLearningService()
completeness_service = ConfigCompletenessService()

# In-memory store for job drafts used by conversational routes
_job_drafts: Dict[str, Any] = {}

# ---------------------------------------------------------------------------
# Wizard stage metadata
# ---------------------------------------------------------------------------
STAGE_MAP = {
    "input-evaluation": 1,
    "salary": 4,
    "competencies": 3,
    "wsi-questions": 5,
    "review-publish": 6,
    "search-calibration": 8,
}

STAGE_NAMES = {
    "input-evaluation": "Avaliação",
    "salary": "Remuneração",
    "competencies": "Competências",
    "wsi-questions": "Perguntas WSI",
    "review-publish": "Revisão e Publicação",
    "search-calibration": "Calibração de Busca",
}

STAGE_ORDER = ["input-evaluation", "salary", "competencies", "wsi-questions", "review-publish"]

WIZARD_STAGES_INFO = {
    "input-evaluation": {
        "name": "Avaliação Inicial",
        "purpose": "Coletar informações básicas da vaga: cargo, área, senioridade, modelo de trabalho, localização",
        "required_fields": ["title", "department", "seniority_level", "work_model", "location"],
        "optional_fields": ["manager", "manager_email", "deadline"],
        "next_stage": "job-summary",
    },
    "job-summary": {
        "name": "Proposta da Vaga",
        "purpose": "Apresentar resumo estruturado com responsabilidades, competências sugeridas e faixa salarial estimada baseada em dados de mercado",
        "required_fields": ["title", "seniority_level"],
        "optional_fields": ["responsibilities", "suggested_skills", "estimated_salary"],
        "next_stage": "salary",
    },
    "salary": {
        "name": "Remuneração",
        "purpose": "Definir faixa salarial competitiva, bônus e benefícios",
        "required_fields": ["salary_min", "salary_max"],
        "optional_fields": ["bonus", "benefits"],
        "next_stage": "competencies",
    },
    "competencies": {
        "name": "Competências",
        "purpose": "Definir habilidades técnicas e comportamentais necessárias",
        "required_fields": ["technical_skills"],
        "optional_fields": ["behavioral_competencies", "languages", "certifications"],
        "next_stage": "wsi-questions",
    },
    "wsi-questions": {
        "name": "Triagem WSI",
        "purpose": "Configurar perguntas de triagem usando metodologia WSI para avaliar candidatos",
        "required_fields": ["screening_questions"],
        "optional_fields": [],
        "next_stage": "review-publish",
    },
    "review-publish": {
        "name": "Revisão e Publicação",
        "purpose": "Revisar todos os dados, gerar descrição da vaga e publicar",
        "required_fields": [],
        "optional_fields": ["job_description"],
        "next_stage": None,
    },
}

WIZARD_ORCHESTRATOR_PROMPT = """Você é a LIA, uma consultora de recrutamento inteligente da plataforma WeDoTalent.

## OBJETIVO FINAL
Ajudar o recrutador a criar uma vaga de emprego completa e otimizada para atrair e triar os melhores candidatos.

## ETAPA ATUAL: {stage_name}
**Propósito:** {stage_purpose}
**Campos obrigatórios:** {required_fields}
**Campos opcionais:** {optional_fields}
**Próxima etapa:** {next_stage}

## DADOS JÁ COLETADOS
{collected_data_summary}

## DADOS FALTANTES PARA ESTA ETAPA
{missing_fields}

## HISTÓRICO DA CONVERSA
{conversation_history}

## INSTRUÇÕES DE COMPORTAMENTO

1. **Interprete a mensagem do usuário** considerando:
   - O contexto da etapa atual
   - Os dados já coletados
   - O objetivo final de criar uma vaga eficaz

2. **Extraia informações** relevantes da mensagem:
   - Se o usuário forneceu dados, identifique quais campos podem ser preenchidos
   - Se o usuário fez uma pergunta, responda de forma útil
   - Se o usuário quer confirmar/avançar, valide se os dados obrigatórios estão completos

3. **Decida a ação apropriada**:
   - RESPOND: Apenas responder uma pergunta ou comentário
   - UPDATE_FIELDS: Atualizar campos com dados extraídos da mensagem
   - ADVANCE_STAGE: Avançar para próxima etapa (só se campos obrigatórios estão preenchidos)
   - REQUEST_CLARIFICATION: Pedir esclarecimento quando informação é ambígua
   - PROVIDE_SUGGESTION: Oferecer sugestão baseada em dados de mercado/histórico
   - VALIDATE_DATA: Validar dados fornecidos e apontar problemas

4. **Seja proativo e inteligente**:
   - Se o usuário forneceu informações parciais, peça o que falta de forma natural
   - Se os dados parecem inconsistentes (ex: salário muito baixo para senioridade), alerte educadamente
   - Sugira melhorias quando apropriado
   - Não seja robótico - converse naturalmente

5. **Formato de resposta**:
   Responda APENAS com um JSON válido no seguinte formato:
   {{
     "action": "respond|update_fields|advance_stage|request_clarification|provide_suggestion|validate_data",
     "response": "Sua resposta para o usuário em português brasileiro",
     "updated_fields": {{"campo": "valor"}} ou null,
     "target_stage": "próxima etapa" ou null,
     "confidence": 0.0 a 1.0,
     "reasoning": "Breve explicação da decisão",
     "suggestions": [{{"field": "campo", "value": "sugestão", "reason": "motivo"}}] ou null,
     "validation_errors": ["erro1", "erro2"] ou null
   }}

## MENSAGEM DO USUÁRIO
{user_message}

Responda com o JSON:"""

# ---------------------------------------------------------------------------
# Shared Pydantic models
# ---------------------------------------------------------------------------

class SuggestionCard(BaseModel):
    id: str
    type: str
    icon: str
    title: str
    description: str
    action: str
    priority: str
    category: str
    metadata: Optional[Dict[str, Any]] = None


class SuggestionsResponse(BaseModel):
    suggestions: List[SuggestionCard]
    generated_at: str
    context: Optional[Dict[str, Any]] = None


class WizardStepRequest(BaseModel):
    conversation_id: Optional[str] = None
    stage: int
    user_input: str
    context: Optional[Dict[str, Any]] = None


class WizardStepResponse(BaseModel):
    conversation_id: str
    current_stage: int
    next_stage: Optional[int] = None
    stage_name: str
    lia_message: str
    detected_criteria: Optional[Dict[str, Any]] = None
    is_complete: bool
    created_job: Optional[Dict[str, Any]] = None
    intent_detected: Optional[str] = None
    benchmarks: Optional[Dict[str, Any]] = None
    suggestions: Optional[Dict[str, Any]] = None
    field_origins: Optional[Dict[str, Dict[str, Any]]] = None
    stage_skipped: Optional[bool] = None
    skip_reason: Optional[str] = None
    auto_filled_data: Optional[Dict[str, Any]] = None
    stages_to_skip: Optional[List[int]] = None


class WizardEvaluateRequest(BaseModel):
    """Request schema for job wizard evaluation endpoint."""
    conversation_id: Optional[str] = None
    user_input: str
    context: Optional[Dict[str, Any]] = None


class WizardEvaluateSuggestion(BaseModel):
    """A suggestion item returned by the evaluation."""
    field: str
    value: Any
    source: str
    confidence: float
    reason: Optional[str] = None


class WizardEvaluateCompensation(BaseModel):
    """Compensation analysis result."""
    salary: Optional[Dict[str, Any]] = None
    bonus: Optional[Dict[str, Any]] = None
    benefits: Optional[Dict[str, Any]] = None
    total_comp: Optional[Dict[str, Any]] = None
    overall_assessment: Optional[str] = None
    summary: Optional[str] = None


class WizardEvaluateResponse(BaseModel):
    """Response schema for job wizard evaluation endpoint."""
    conversation_id: str
    detected_fields: Dict[str, Any]
    compensation_analysis: Optional[WizardEvaluateCompensation] = None
    suggestions: List[WizardEvaluateSuggestion] = []
    lia_message: str
    overall_confidence: float = 0.7


class InsightsRequest(BaseModel):
    job_ids: List[str]
    insight_types: Optional[List[str]] = None


class InsightItem(BaseModel):
    type: str
    title: str
    description: str
    severity: str
    recommendation: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class InsightsResponse(BaseModel):
    insights: List[InsightItem]
    summary: Dict[str, Any]
    generated_at: str


class ExpandedPromptRequest(BaseModel):
    message: str
    context_type: str
    context_ids: Optional[List[str]] = None
    context: Optional[Dict[str, Any]] = None


class ExpandedPromptResponse(BaseModel):
    response: str
    agent_used: str
    actions: Optional[List[Dict[str, Any]]] = None
    follow_up_suggestions: Optional[List[str]] = None


class InterpretMessageAction(str, Enum):
    CONFIRM = "confirm"
    ADVANCE_STAGE = "advance_stage"
    ASK_QUESTION = "ask_question"
    UPDATE_FIELD = "update_field"
    PROVIDE_DATA = "provide_data"
    REJECT = "reject"
    HELP = "help"
    OTHER = "other"


class InterpretMessageRequest(BaseModel):
    message: str
    current_stage: str = "input-evaluation"
    context: Optional[Dict[str, Any]] = None


class InterpretMessageResponse(BaseModel):
    action: InterpretMessageAction
    confidence: float = 0.5
    extracted_entities: Optional[Dict[str, Any]] = None
    lia_response: Optional[str] = None
    should_advance: bool = False
    target_stage: Optional[str] = None
    clarification_needed: bool = False
    clarification_question: Optional[str] = None
    reasoning: Optional[str] = None


class ConversationalRequest(BaseModel):
    message: str
    context: Optional[str] = None
    mode: Optional[str] = "job_creation"


class ConversationalResponse(BaseModel):
    response: str
    understood_intent: str
    suggested_action: Optional[str] = None
    can_help: bool = True


class WizardOrchestratorRequest(BaseModel):
    message: str
    current_stage: str
    collected_data: Dict[str, Any]
    conversation_history: Optional[List[Dict[str, str]]] = None
    company_id: Optional[str] = "default"
    use_structured_outputs: bool = False
    llm_provider: Optional[str] = "gemini"


class WizardOrchestratorAction(str, Enum):
    RESPOND = "respond"
    ADVANCE_STAGE = "advance_stage"
    UPDATE_FIELDS = "update_fields"
    REQUEST_CLARIFICATION = "request_clarification"
    PROVIDE_SUGGESTION = "provide_suggestion"
    VALIDATE_DATA = "validate_data"


class WizardOrchestratorResponse(BaseModel):
    action: WizardOrchestratorAction
    response: str
    updated_fields: Optional[Dict[str, Any]] = None
    target_stage: Optional[str] = None
    confidence: float = 0.9
    reasoning: Optional[str] = None
    suggestions: Optional[List[Dict[str, Any]]] = None
    validation_errors: Optional[List[str]] = None


class SalaryBenchmarkRequest(BaseModel):
    job_title: str
    seniority: Optional[str] = None
    location: Optional[str] = None


class SalaryBenchmarkResponse(BaseModel):
    internal: Optional[Dict[str, Any]] = None
    market: Optional[Dict[str, Any]] = None
    combined: Optional[Dict[str, Any]] = None


class ContextBadge(BaseModel):
    """Badge showing the current page/entity context."""
    label: str
    icon: str
    color: str
    description: Optional[str] = None


class ContextSuggestion(BaseModel):
    """A proactive suggestion chip for the chat input."""
    id: str
    label: str
    prompt: str
    icon: Optional[str] = None
    category: str = "action"


class ContextSuggestionsResponse(BaseModel):
    context_badge: Optional[ContextBadge] = None
    suggestions: List[ContextSuggestion]
    page: str
    entity_id: Optional[str] = None
    generated_at: str


# ---------------------------------------------------------------------------
# Context suggestion data tables
# ---------------------------------------------------------------------------

_CONTEXT_SUGGESTIONS: Dict[str, List[Dict[str, str]]] = {
    "home": [
        {"id": "h1", "label": "Resumo do dia", "prompt": "Me dê um resumo das atividades e alertas de hoje", "icon": "Sun", "category": "analysis"},
        {"id": "h2", "label": "Vagas críticas", "prompt": "Quais vagas estão em estado crítico ou com prazo vencendo?", "icon": "AlertTriangle", "category": "analysis"},
        {"id": "h3", "label": "Candidatos aguardando", "prompt": "Quantos candidatos estão aguardando triagem ou retorno?", "icon": "Users", "category": "analysis"},
        {"id": "h4", "label": "Criar nova vaga", "prompt": "Quero criar uma nova vaga com a LIA", "icon": "Plus", "category": "action"},
        {"id": "h5", "label": "Relatório semanal", "prompt": "Gera o relatório semanal com métricas de recrutamento", "icon": "FileText", "category": "report"},
        {"id": "h6", "label": "Pipeline geral", "prompt": "Como está a saúde geral do pipeline de recrutamento?", "icon": "TrendingUp", "category": "analysis"},
    ],
    "vaga": [
        {"id": "v1", "label": "Buscar candidatos", "prompt": "Busca os melhores candidatos para esta vaga e compara os perfis", "icon": "Search", "category": "action"},
        {"id": "v2", "label": "Saúde do pipeline", "prompt": "Como está o pipeline desta vaga? Tem algum gargalo?", "icon": "Activity", "category": "analysis"},
        {"id": "v3", "label": "Candidatos triagem", "prompt": "Quais candidatos desta vaga ainda precisam de triagem WSI?", "icon": "ClipboardCheck", "category": "action"},
        {"id": "v4", "label": "Benchmark salarial", "prompt": "Qual o benchmark salarial para esta posição no mercado atual?", "icon": "DollarSign", "category": "analysis"},
        {"id": "v5", "label": "Relatório da vaga", "prompt": "Gera um relatório completo desta vaga com métricas e candidatos", "icon": "FileText", "category": "report"},
        {"id": "v6", "label": "Editar descrição", "prompt": "Quero revisar e melhorar a descrição desta vaga", "icon": "Edit", "category": "action"},
    ],
    "candidato": [
        {"id": "c1", "label": "Comparar candidatos", "prompt": "Compara este candidato com os outros finalistas da vaga", "icon": "GitMerge", "category": "analysis"},
        {"id": "c2", "label": "Parecer técnico", "prompt": "Gera um parecer técnico completo deste candidato", "icon": "FileText", "category": "report"},
        {"id": "c3", "label": "Disparar triagem", "prompt": "Dispara a triagem WSI para este candidato", "icon": "Zap", "category": "action"},
        {"id": "c4", "label": "Agendar entrevista", "prompt": "Quero agendar uma entrevista com este candidato", "icon": "Calendar", "category": "action"},
        {"id": "c5", "label": "Pontos fortes", "prompt": "Quais são os pontos fortes e fracos deste candidato para a vaga?", "icon": "Star", "category": "analysis"},
        {"id": "c6", "label": "Avançar no pipeline", "prompt": "Avança este candidato para a próxima etapa do pipeline", "icon": "ArrowRight", "category": "action"},
    ],
    "pipeline": [
        {"id": "p1", "label": "Vagas travadas", "prompt": "Quais vagas estão travadas no pipeline há mais de 5 dias?", "icon": "AlertTriangle", "category": "analysis"},
        {"id": "p2", "label": "Velocidade média", "prompt": "Qual a velocidade média do pipeline por etapa?", "icon": "TrendingUp", "category": "analysis"},
        {"id": "p3", "label": "Mover candidatos", "prompt": "Quero mover candidatos em lote no pipeline", "icon": "MoveRight", "category": "action"},
        {"id": "p4", "label": "Taxa de conversão", "prompt": "Qual a taxa de conversão entre as etapas do pipeline?", "icon": "BarChart", "category": "analysis"},
        {"id": "p5", "label": "Candidatos prontos", "prompt": "Quais candidatos estão prontos para avançar para oferta?", "icon": "CheckCircle", "category": "action"},
    ],
    "triagem": [
        {"id": "t1", "label": "Ver resultado WSI", "prompt": "Mostra o resultado completo da triagem WSI deste candidato", "icon": "BarChart2", "category": "analysis"},
        {"id": "t2", "label": "Comparar respostas", "prompt": "Compara as respostas deste candidato com o perfil ideal da vaga", "icon": "GitMerge", "category": "analysis"},
        {"id": "t3", "label": "Relatório de triagem", "prompt": "Gera o relatório de triagem com recomendação de contratação", "icon": "FileText", "category": "report"},
        {"id": "t4", "label": "Ajustar perguntas", "prompt": "Quero revisar e ajustar as perguntas da triagem WSI", "icon": "Edit", "category": "action"},
        {"id": "t5", "label": "Aprovação em lote", "prompt": "Quero aprovar ou rejeitar candidatos em lote baseado nos scores", "icon": "CheckSquare", "category": "action"},
    ],
    "relatorios": [
        {"id": "r1", "label": "Relatório semanal", "prompt": "Gera o relatório semanal completo de recrutamento", "icon": "FileText", "category": "report"},
        {"id": "r2", "label": "Análise de diversidade", "prompt": "Mostra os indicadores de diversidade e inclusão do mês", "icon": "Users", "category": "analysis"},
        {"id": "r3", "label": "Time-to-hire", "prompt": "Qual o time-to-hire médio por vaga e por etapa?", "icon": "Clock", "category": "analysis"},
        {"id": "r4", "label": "Custo por contratação", "prompt": "Analisa o custo por contratação e onde está o gasto maior", "icon": "DollarSign", "category": "analysis"},
        {"id": "r5", "label": "Exportar dados", "prompt": "Quero exportar os dados de recrutamento para análise", "icon": "Download", "category": "action"},
    ],
    "configuracoes": [
        {"id": "cfg1", "label": "Políticas de triagem", "prompt": "Quero revisar as políticas de triagem automática", "icon": "Shield", "category": "action"},
        {"id": "cfg2", "label": "Perfis de sourcing", "prompt": "Como estão configurados os perfis de sourcing?", "icon": "Search", "category": "analysis"},
        {"id": "cfg3", "label": "Integração ATS", "prompt": "Como está a integração com o ATS atual?", "icon": "Link", "category": "analysis"},
    ],
}

_PAGE_BADGES: Dict[str, Dict[str, str]] = {
    "home":          {"label": "Painel Principal",   "icon": "Home",           "color": "#6366F1"},
    "vaga":          {"label": "Vaga",               "icon": "Briefcase",      "color": "#8B5CF6"},
    "candidato":     {"label": "Candidato",          "icon": "User",           "color": "#0EA5E9"},
    "pipeline":      {"label": "Pipeline",           "icon": "GitBranch",      "color": "#F59E0B"},
    "triagem":       {"label": "Triagem",            "icon": "ClipboardCheck", "color": "#10B981"},
    "relatorios":    {"label": "Relatórios",         "icon": "BarChart2",      "color": "#EF4444"},
    "configuracoes": {"label": "Configurações",      "icon": "Settings",       "color": "#6B7280"},
}


# ---------------------------------------------------------------------------
# Shared helper functions
# ---------------------------------------------------------------------------

class QuestionType:
    SALARY = "salary"
    SKILLS = "skills"
    TIME_TO_FILL = "time_to_fill"
    PROCESS = "process"
    GENERAL = "general"


def detect_question_type(text: str) -> str:
    """Detect the type of question being asked."""
    text_lower = text.lower()

    salary_keywords = [
        "salário", "salario", "quanto paga", "remuneração", "remuneracao",
        "faixa salarial", "valor", "mercado", "benchmark", "média salarial",
        "media salarial", "piso", "teto", "bom salário", "competitivo"
    ]
    if any(kw in text_lower for kw in salary_keywords):
        return QuestionType.SALARY

    skills_keywords = [
        "skill", "habilidade", "competência", "competencia", "requisito",
        "conhecimento", "tecnologia", "ferramenta", "experiência técnica",
        "experiencia tecnica", "mais comum", "mais usado", "mais pedido"
    ]
    if any(kw in text_lower for kw in skills_keywords):
        return QuestionType.SKILLS

    time_keywords = [
        "tempo", "quanto demora", "prazo", "dias", "semanas", "meses",
        "preencher", "fechar vaga", "time to fill", "ttf", "sla"
    ]
    if any(kw in text_lower for kw in time_keywords):
        return QuestionType.TIME_TO_FILL

    process_keywords = [
        "wsi", "triagem", "processo", "etapa", "como funciona",
        "metodologia", "avaliação", "avaliacao", "pipeline", "fluxo",
        "entrevista", "screening"
    ]
    if any(kw in text_lower for kw in process_keywords):
        return QuestionType.PROCESS

    return QuestionType.GENERAL


async def record_field_history(
    db: AsyncSession,
    job_draft_model: JobDraft,
    field_name: str,
    old_value: Any,
    new_value: Any,
    change_type: ChangeType,
    recruiter_id: str,
    confidence: Optional[float] = None,
    source: Optional[str] = None,
    reason: Optional[str] = None,
) -> None:
    """Record a field change in the DraftFieldHistory table."""
    if old_value == new_value:
        return

    def serialize_value(val):
        if val is None:
            return None
        if isinstance(val, (dict, list)):
            return val
        return str(val)

    history_entry = DraftFieldHistory(
        draft_id=job_draft_model.id,
        field_name=field_name,
        old_value=serialize_value(old_value),
        new_value=serialize_value(new_value),
        change_type=change_type,
        confidence_at_change=confidence,
        source=source,
        reason=reason,
        created_by=recruiter_id,
    )
    db.add(history_entry)
    logger.debug(f"Recorded field history: {field_name} changed from {old_value} to {new_value} ({change_type.value})")


async def get_learning_adjustments(
    db: AsyncSession,
    company_id: str,
    role: Optional[str] = None,
    seniority: Optional[str] = None,
) -> Dict[str, Any]:
    """Fetch historical correction patterns to adjust suggestions."""
    adjustments = {}
    try:
        salary_patterns = await feedback_learning_service.get_correction_patterns(
            db=db, company_id=company_id, field="salary_range", role=role, seniority=seniority
        )
        if salary_patterns.get("sample_size", 0) >= 5:
            for pattern in salary_patterns.get("patterns", []):
                if pattern.get("type") == "salary_adjustment":
                    adjustments["salary_range"] = {
                        "adjustment_pct": pattern.get("adjustment_percentage", 0),
                        "direction": pattern.get("direction", "stable"),
                        "confidence": salary_patterns.get("confidence", "low"),
                        "sample_size": pattern.get("sample_size", 0),
                    }
                    break

        seniority_patterns = await feedback_learning_service.get_correction_patterns(
            db=db, company_id=company_id, field="seniority", role=role
        )
        if seniority_patterns.get("sample_size", 0) >= 3:
            for pattern in seniority_patterns.get("patterns", []):
                if pattern.get("type") == "categorical_transition" and pattern.get("percentage", 0) > 50:
                    adjustments["seniority"] = {
                        "from_value": pattern.get("from_value"),
                        "to_value": pattern.get("to_value"),
                        "confidence": seniority_patterns.get("confidence", "low"),
                    }
                    break
    except Exception as e:
        logger.warning(f"Failed to get learning adjustments: {e}")

    return adjustments


async def handle_salary_question(
    db: AsyncSession,
    company_id: str,
    job_draft: Dict[str, Any],
    user_input: str,
) -> str:
    """Handle salary-related questions using insights services."""
    role = job_draft.get("job_title", "")
    seniority = job_draft.get("seniority", "")
    location = job_draft.get("location", "")

    location_match = re.search(
        r'\b(SP|RJ|MG|RS|PR|São Paulo|Rio|Belo Horizonte|Porto Alegre|Curitiba)\b',
        user_input, re.IGNORECASE
    )
    if location_match:
        location = location_match.group(1)

    seniority_match = re.search(
        r'\b(júnior|junior|pleno|sênior|senior|lead|staff)\b', user_input, re.IGNORECASE
    )
    if seniority_match:
        seniority = seniority_match.group(1)

    role_match = re.search(
        r'\b(dev|desenvolvedor|developer|engenheiro|analista|gerente|product|designer|data)\s*\w*',
        user_input, re.IGNORECASE
    )
    if role_match:
        role = role_match.group(0)

    internal_benchmark = {}
    market_benchmark = {}
    combined = {}

    try:
        internal_benchmark = await job_insights_service.get_salary_benchmark(
            db=db, company_id=company_id, role=role or "desenvolvedor",
            seniority=seniority, location=location
        )
    except Exception as e:
        logger.warning(f"Failed to get internal salary benchmark: {e}")
        internal_benchmark = {"sample_size": 0}

    try:
        market_benchmark = await market_benchmark_service.search_salary_benchmark(
            role=role or "desenvolvedor", seniority=seniority, location=location
        )
    except Exception as e:
        logger.warning(f"Failed to get market salary benchmark: {e}")
        market_benchmark = {}

    try:
        combined = market_benchmark_service.combine_with_internal(
            internal_data=internal_benchmark if internal_benchmark.get("sample_size", 0) > 0 else None,
            market_data=market_benchmark,
        )
    except Exception as e:
        logger.warning(f"Failed to combine salary benchmarks: {e}")
        combined = {}

    response_parts = []
    role_desc = role or "a posição"
    seniority_desc = f" nível {seniority}" if seniority else ""
    location_desc = f" em {location}" if location else ""
    response_parts.append(f"📊 **Análise salarial para {role_desc}{seniority_desc}{location_desc}:**\n")

    if internal_benchmark.get("sample_size", 0) > 0:
        response_parts.append(f"**Dados internos** ({internal_benchmark['sample_size']} vagas similares):")
        response_parts.append(f"• Faixa: R$ {internal_benchmark.get('min', 0):,.0f} - R$ {internal_benchmark.get('max', 0):,.0f}")
        response_parts.append(f"• Mediana: R$ {internal_benchmark.get('median', 0):,.0f}")
        if internal_benchmark.get("trend") != "stable":
            trend_text = "em alta" if internal_benchmark["trend"] == "increasing" else "em queda"
            response_parts.append(f"• Tendência: {trend_text}")
        response_parts.append("")

    if market_benchmark.get("min"):
        response_parts.append(f"**Dados de mercado** (fontes: {', '.join(market_benchmark.get('sources', [])[:3])}):")
        response_parts.append(f"• Faixa: R$ {market_benchmark.get('min', 0):,.0f} - R$ {market_benchmark.get('max', 0):,.0f}")
        response_parts.append(f"• Mediana: R$ {market_benchmark.get('median', 0):,.0f}")
        confidence = market_benchmark.get("confidence", "low")
        conf_emoji = "🟢" if confidence == "high" else "🟡" if confidence == "medium" else "🔴"
        response_parts.append(f"• Confiança: {conf_emoji} {confidence}")
        response_parts.append("")

    if combined.get("recommended_min"):
        response_parts.append(f"💡 **Recomendação:** R$ {combined.get('recommended_min', 0):,.0f} - R$ {combined.get('recommended_max', 0):,.0f}")

    if not internal_benchmark.get("sample_size") and not market_benchmark.get("min"):
        response_parts.append("⚠️ Não foi possível obter dados de benchmark no momento. Por favor, defina a faixa salarial manualmente.")
    else:
        response_parts.append(f"\n⚠️ {market_benchmark_service.DISCLAIMER}")

    return "\n".join(response_parts)


async def handle_skills_question(
    db: AsyncSession,
    company_id: str,
    job_draft: Dict[str, Any],
    user_input: str,
) -> str:
    """Handle skills-related questions."""
    role = job_draft.get("job_title", "")
    department = job_draft.get("department", "")

    skills_data = {}
    try:
        skills_data = await job_insights_service.get_common_skills(
            db=db, company_id=company_id, department=department, role=role
        )
    except Exception as e:
        logger.warning(f"Failed to get common skills: {e}")
        skills_data = {"skills": []}

    response_parts = []
    role_desc = role or "posições similares"
    response_parts.append(f"🎯 **Skills mais comuns para {role_desc}:**\n")

    if skills_data.get("skills"):
        tech_skills = [s for s in skills_data["skills"] if s.get("category") == "Técnico"]
        behavioral_skills = [s for s in skills_data["skills"] if s.get("category") == "Comportamental"]

        if tech_skills:
            response_parts.append("**Competências Técnicas:**")
            for skill in tech_skills[:8]:
                required_badge = "✅" if skill.get("is_commonly_required") else "⚪"
                response_parts.append(f"{required_badge} {skill['skill']} ({skill['percentage']:.0f}% das vagas)")
            response_parts.append("")

        if behavioral_skills:
            response_parts.append("**Competências Comportamentais:**")
            for skill in behavioral_skills[:5]:
                response_parts.append(f"• {skill['skill']} ({skill['percentage']:.0f}% das vagas)")
            response_parts.append("")

        confidence = skills_data.get("confidence", "low")
        response_parts.append(f"📊 Baseado em {skills_data.get('total_jobs_analyzed', 0)} vagas analisadas (confiança: {confidence})")
    else:
        response_parts.append("Ainda não temos dados suficientes para sugerir skills comuns.")
        response_parts.append("Posso ajudá-lo a definir as competências manualmente.")

    return "\n".join(response_parts)


async def handle_time_to_fill_question(
    db: AsyncSession,
    company_id: str,
    job_draft: Dict[str, Any],
    user_input: str,
) -> str:
    """Handle time-to-fill related questions."""
    role = job_draft.get("job_title", "")
    seniority = job_draft.get("seniority", "")
    department = job_draft.get("department", "")

    time_data = {}
    try:
        time_data = await job_insights_service.get_time_to_fill(
            db=db, company_id=company_id, role=role, seniority=seniority, department=department
        )
    except Exception as e:
        logger.warning(f"Failed to get time-to-fill data: {e}")
        time_data = {}

    response_parts = []
    role_desc = role or "posições similares"
    seniority_desc = f" nível {seniority}" if seniority else ""
    response_parts.append(f"⏱️ **Tempo médio de preenchimento para {role_desc}{seniority_desc}:**\n")

    if time_data.get("average_days"):
        avg_days = time_data["average_days"]
        median_days = time_data.get("median_days", avg_days)
        response_parts.append(f"• Média: **{avg_days:.0f} dias**")
        response_parts.append(f"• Mediana: {median_days:.0f} dias")
        response_parts.append(f"• Variação: {time_data.get('min_days', 0)} - {time_data.get('max_days', 0)} dias")
        response_parts.append("")
        if avg_days <= 30:
            response_parts.append("💚 Tempo considerado **rápido** para o mercado")
        elif avg_days <= 60:
            response_parts.append("🟡 Tempo **dentro da média** do mercado")
        else:
            response_parts.append("🔴 Tempo **acima da média** - considere ampliar o funil")
        response_parts.append("")
        response_parts.append(f"📊 {time_data.get('based_on', '')}")
    else:
        response_parts.append("Ainda não temos dados históricos suficientes para esta posição.")
        response_parts.append("O tempo médio de mercado para posições de tecnologia é de 30-45 dias.")

    return "\n".join(response_parts)


async def handle_process_question(user_input: str, llm_svc: LLMService) -> str:
    """Handle process/methodology questions using LLM."""
    prompt = f"""Você é LIA, assistente de recrutamento especializada.
O usuário está no wizard de criação de vaga e tem uma pergunta sobre processo.

Pergunta: {user_input}

Explique de forma clara e concisa. Se for sobre:
- WSI (WeDoTalent Skill Index): Explique que é nossa metodologia de triagem com 7 blocos de perguntas
- Pipeline: Descreva as etapas típicas (triagem, entrevistas, proposta)
- Triagem: Explique como funciona a avaliação automatizada de candidatos

Mantenha a resposta em até 150 palavras, formatada em markdown."""
    try:
        response = await llm_svc.generate(prompt, provider="gemini")
        return response
    except Exception as e:
        logger.warning(f"Failed to generate LLM response for process question: {e}")
        return """**Sobre nosso processo:**

A metodologia **WSI (WeDoTalent Skill Index)** é nosso sistema de triagem inteligente com 7 blocos de avaliação:
1. Autodeclaração de contexto
2. Micro-cases técnicos
3. Situacional comportamental
4. Fit cultural
5. Autodeclaração de habilidades
6. Perguntas técnicas
7. Perguntas de elegibilidade

O pipeline típico inclui: triagem automatizada → entrevistas → proposta.

Se tiver dúvidas específicas, me pergunte!"""


async def analyze_competency_gaps(
    job_title: str,
    seniority: str,
    detected_technical: List[str],
    detected_behavioral: List[str],
) -> Dict[str, Any]:
    """Analyze detected competencies against expected competencies for the role."""
    skill_suggestions = skills_catalog_service.suggest_skills(role=job_title, seniority=seniority)

    suggested_technical = skill_suggestions.get("technical_skills", [])
    suggested_behavioral = skill_suggestions.get("behavioral_competencies", [])

    detected_tech_lower = [s.lower() for s in detected_technical]
    missing_technical = []
    for skill in suggested_technical:
        skill_name = skill if isinstance(skill, str) else skill.get("name", str(skill))
        if skill_name.lower() not in detected_tech_lower:
            missing_technical.append({"name": skill_name})
    missing_technical = missing_technical[:5]

    detected_behav_lower = [s.lower() for s in detected_behavioral]
    missing_behavioral = []
    for comp in suggested_behavioral:
        comp_name = comp.get("name", "") if isinstance(comp, dict) else str(comp)
        if comp_name.lower() not in detected_behav_lower:
            missing_behavioral.append({"name": comp_name, "key": comp.get("key", "") if isinstance(comp, dict) else ""})
    missing_behavioral = missing_behavioral[:3]

    total_expected = len(suggested_technical) + len(suggested_behavioral)
    total_detected = len(detected_technical) + len(detected_behavioral)
    completeness = min(1.0, total_detected / max(total_expected, 1))

    return {
        "completeness_score": round(completeness * 100),
        "missing_technical": missing_technical,
        "missing_behavioral": missing_behavioral,
        "has_critical_gaps": len(missing_technical) > 3 or len(missing_behavioral) > 2,
        "analysis_summary": f"Detectadas {len(detected_technical)} competências técnicas e {len(detected_behavioral)} comportamentais.",
        "suggested_technical_count": len(suggested_technical),
        "suggested_behavioral_count": len(suggested_behavioral),
    }


async def get_stage_benchmarks(
    db: AsyncSession,
    company_id: str,
    job_draft: Dict[str, Any],
    stage: int,
) -> Dict[str, Any]:
    """Get relevant benchmarks for the current stage."""
    benchmarks = {}
    role = job_draft.get("job_title", "")
    seniority = job_draft.get("seniority", "")
    location = job_draft.get("location", "")
    department = job_draft.get("department", "")

    if stage == 3:
        try:
            skills_data = await job_insights_service.get_common_skills(
                db=db, company_id=company_id, department=department, role=role
            )
            benchmarks["suggested_skills"] = skills_data
        except Exception as e:
            logger.warning(f"Failed to get skills benchmarks for stage 3: {e}")
            benchmarks["suggested_skills"] = {"skills": [], "error": "Não foi possível carregar sugestões de skills"}

    elif stage == 4:
        if role:
            internal_benchmark = {}
            market_benchmark = {}
            combined = {}
            learning_adjustments = {}

            try:
                internal_benchmark = await job_insights_service.get_salary_benchmark(
                    db=db, company_id=company_id, role=role, seniority=seniority, location=location
                )
            except Exception as e:
                logger.warning(f"Failed to get internal salary benchmark: {e}")
                internal_benchmark = {"sample_size": 0}

            try:
                market_benchmark = await market_benchmark_service.search_salary_benchmark(
                    role=role, seniority=seniority, location=location
                )
            except Exception as e:
                logger.warning(f"Failed to get market salary benchmark: {e}")
                market_benchmark = {}

            try:
                combined = market_benchmark_service.combine_with_internal(
                    internal_data=internal_benchmark if internal_benchmark.get("sample_size", 0) > 0 else None,
                    market_data=market_benchmark,
                )
            except Exception as e:
                logger.warning(f"Failed to combine salary benchmarks: {e}")
                combined = {}

            try:
                learning_adjustments = await get_learning_adjustments(
                    db=db, company_id=company_id, role=role, seniority=seniority
                )
                if "salary_range" in learning_adjustments:
                    salary_adj = learning_adjustments["salary_range"]
                    adjustment_pct = salary_adj.get("adjustment_pct", 0)
                    if adjustment_pct and abs(adjustment_pct) > 5:
                        adjustment_factor = 1 + (adjustment_pct / 100)
                        if combined.get("recommended_min"):
                            combined["original_recommended_min"] = combined["recommended_min"]
                            combined["original_recommended_max"] = combined.get("recommended_max", combined["recommended_min"])
                            combined["recommended_min"] = int(combined["recommended_min"] * adjustment_factor)
                            combined["recommended_max"] = int(combined.get("recommended_max", combined["recommended_min"]) * adjustment_factor)
                            combined["learning_adjustment_applied"] = True
                            combined["learning_adjustment_pct"] = adjustment_pct
                            combined["learning_confidence"] = salary_adj.get("confidence", "low")
                            combined["learning_sample_size"] = salary_adj.get("sample_size", 0)
                        if market_benchmark.get("min"):
                            market_benchmark["original_min"] = market_benchmark["min"]
                            market_benchmark["original_max"] = market_benchmark.get("max", market_benchmark["min"])
                            market_benchmark["min"] = int(market_benchmark["min"] * adjustment_factor)
                            market_benchmark["max"] = int(market_benchmark.get("max", market_benchmark["min"]) * adjustment_factor)
                            market_benchmark["median"] = int(market_benchmark.get("median", (market_benchmark["min"] + market_benchmark["max"]) / 2) * adjustment_factor)
                            market_benchmark["learning_adjusted"] = True
                        logger.info(f"Applied learning adjustment of {adjustment_pct:+.1f}% to salary benchmarks for {role}")
            except Exception as e:
                logger.warning(f"Failed to apply learning adjustments: {e}")

            benchmarks["internal_salary"] = internal_benchmark
            benchmarks["market_salary"] = market_benchmark
            benchmarks["combined_recommendation"] = combined
            benchmarks["learning_adjustments"] = learning_adjustments

    return benchmarks


async def handle_correction(
    db: AsyncSession,
    company_id: str,
    job_draft: Dict[str, Any],
    classification: ClassificationResult,
    user_input: str,
    conversation_id: str,
) -> tuple:
    """Handle correction intent - update job draft and record feedback."""
    entities = classification.extracted_entities
    response_parts = []
    updated_fields = {}

    if "salary" in entities:
        old_salary = job_draft.get("salary_range")
        new_salary = entities["salary"]
        job_draft["salary_range"] = {"min": new_salary, "max": new_salary * 1.2}
        updated_fields["salary_range"] = job_draft["salary_range"]
        response_parts.append(f"✅ Atualizei a faixa salarial para R$ {new_salary:,.0f}")
        if old_salary and job_draft.get("job_id"):
            try:
                await feedback_learning_service.record_correction(
                    db=db, company_id=company_id,
                    job_id=UUID(job_draft.get("job_id", str(uuid4()))),
                    field="salary_range", original_value=old_salary,
                    corrected_value=job_draft["salary_range"], stage="salary",
                    role=job_draft.get("job_title"), seniority=job_draft.get("seniority"),
                    location=job_draft.get("location"),
                )
            except Exception as e:
                logger.warning(f"Could not record correction: {e}")

    if "seniority" in entities:
        old_seniority = job_draft.get("seniority")
        new_seniority = entities["seniority"]
        job_draft["seniority"] = new_seniority
        updated_fields["seniority"] = new_seniority
        response_parts.append(f"✅ Atualizei a senioridade para {new_seniority}")
        if old_seniority and job_draft.get("job_id"):
            try:
                await feedback_learning_service.record_correction(
                    db=db, company_id=company_id,
                    job_id=UUID(job_draft.get("job_id", str(uuid4()))),
                    field="seniority", original_value=old_seniority,
                    corrected_value=new_seniority, stage="basic-info",
                    role=job_draft.get("job_title"),
                )
            except Exception as e:
                logger.warning(f"Could not record correction: {e}")

    if "work_model" in entities:
        job_draft["work_model"] = entities["work_model"]
        updated_fields["work_model"] = entities["work_model"]
        response_parts.append(f"✅ Atualizei o modelo de trabalho para {entities['work_model']}")

    if "location" in entities:
        job_draft["location"] = entities["location"]
        updated_fields["location"] = entities["location"]
        response_parts.append(f"✅ Atualizei a localização para {entities['location']}")

    if "skills" in entities:
        existing_skills = job_draft.get("detected_skills", [])
        new_skills = entities["skills"]
        job_draft["detected_skills"] = list(set(existing_skills + new_skills))
        updated_fields["detected_skills"] = job_draft["detected_skills"]
        response_parts.append(f"✅ Adicionei as skills: {', '.join(new_skills)}")

    if not response_parts:
        response_parts.extend([
            "Entendi que você quer corrigir algo. O que gostaria de ajustar?",
            "• Salário",
            "• Senioridade",
            "• Modelo de trabalho",
            "• Localização",
            "• Skills/Competências",
        ])

    await db.commit()
    return "\n".join(response_parts), updated_fields


# ---------------------------------------------------------------------------
# Structured output helpers (kept for backwards-compat imports)
# ---------------------------------------------------------------------------

async def get_structured_orchestration_decision(
    user_message: str,
    context: Dict[str, Any],
    provider: str = "gemini",
) -> OrchestrationDecision:
    system_prompt = """You are LIA, an intelligent assistant helping recruiters create job vacancies.
Analyze the user's message and determine the appropriate action to take.

Actions:
- respond: Just reply to the user with helpful information
- advance_stage: Move to the next stage in the wizard
- update_fields: Update job fields based on user input
- request_clarification: Ask for more details if something is unclear

Consider the current context and provide your decision with confidence level."""
    messages = [
        {
            "role": "user",
            "content": f"Current context:\n{json.dumps(context, default=str, ensure_ascii=False)}\n\nUser message: {user_message}\n\nAnalyze this and decide what action to take.",
        }
    ]
    try:
        decision = await llm_service.generate_structured(
            messages=messages, output_model=OrchestrationDecision,
            provider=provider, system_prompt=system_prompt,
        )
        logger.info(f"Structured orchestration decision: action={decision.action}, confidence={decision.confidence}")
        return decision
    except ValueError as e:
        logger.warning(f"Structured output failed, using fallback: {e}")
        return OrchestrationDecision(
            action="respond", confidence=0.5,
            response_text="Desculpe, não entendi completamente. Pode reformular sua solicitação?",
            clarification_needed="Could not parse user intent",
        )


async def get_structured_intent_classification(
    user_message: str,
    provider: str = "gemini",
) -> IntentClassification:
    system_prompt = """Classify the user's intent in the context of a recruitment/HR platform.
Common intents include:
- job_creation: Creating a new job vacancy
- candidate_search: Looking for candidates
- job_update: Modifying an existing job
- salary_inquiry: Questions about salary/compensation
- general_question: General HR-related questions
- greeting: Simple greeting or conversation starter

Extract any relevant entities (job title, skills, location, etc.)."""
    messages = [{"role": "user", "content": user_message}]
    try:
        classification = await llm_service.generate_structured(
            messages=messages, output_model=IntentClassification,
            provider=provider, system_prompt=system_prompt,
        )
        logger.info(f"Intent classified: {classification.intent} (confidence={classification.confidence})")
        return classification
    except ValueError as e:
        logger.warning(f"Intent classification failed: {e}")
        return IntentClassification(
            intent="unknown", confidence=0.3, entities={},
            suggested_response="Não consegui identificar sua intenção. Por favor, seja mais específico.",
        )


async def get_structured_salary_analysis(
    job_title: str,
    seniority: str,
    location: str,
    current_min: Optional[int] = None,
    current_max: Optional[int] = None,
    provider: str = "gemini",
) -> SalaryAnalysis:
    system_prompt = """You are a compensation analyst. Analyze the job details and provide
salary recommendations based on Brazilian market data. Consider:
- Job title and responsibilities
- Seniority level
- Location (major cities typically pay more)
- Current market conditions in Brazil (2024-2025)

Provide realistic salary ranges in BRL (Brazilian Reais) monthly."""
    context = {
        "job_title": job_title, "seniority": seniority, "location": location,
        "current_range": {"min": current_min, "max": current_max} if current_min or current_max else None,
    }
    messages = [{"role": "user", "content": f"Analyze this position and provide salary recommendations:\n{json.dumps(context, ensure_ascii=False)}"}]
    try:
        analysis = await llm_service.generate_structured(
            messages=messages, output_model=SalaryAnalysis,
            provider=provider, system_prompt=system_prompt,
        )
        logger.info(f"Salary analysis: {analysis.market_position}, range={analysis.recommended_min}-{analysis.recommended_max}")
        return analysis
    except ValueError as e:
        logger.warning(f"Salary analysis failed: {e}")
        return SalaryAnalysis(
            recommended_min=None, recommended_max=None, market_position="at_market",
            confidence=0.3, reasoning="Unable to analyze salary at this time. Please provide manual input.",
        )
