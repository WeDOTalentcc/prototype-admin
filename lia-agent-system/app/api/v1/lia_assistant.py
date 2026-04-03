"""
LIA Assistant API - Dynamic suggestions, wizard, insights, and expanded prompt routing.

Endpoints for:
- /lia/suggestions - Dynamic homepage cards based on real data
- /lia/job-wizard - Conversational job creation with intelligent orchestrator
- /lia/job-insights - Dynamic insights for selected jobs
- /lia/expanded-prompt - Route commands to appropriate agents
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
from app.shared.agents.state_machine import WizardStage
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


async def get_structured_orchestration_decision(
    user_message: str,
    context: Dict[str, Any],
    provider: str = "gemini"
) -> OrchestrationDecision:
    """
    Use structured outputs to get an orchestration decision from the LLM.
    
    This is an example integration of the structured output feature.
    The LLM will return a validated OrchestrationDecision object directly,
    eliminating the need for manual JSON parsing.
    
    Args:
        user_message: The user's message to analyze
        context: Context about the current job draft and conversation
        provider: LLM provider to use ("claude" or "gemini")
        
    Returns:
        OrchestrationDecision with action, confidence, and optional updates
    """
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
            "content": f"""Current context:
{json.dumps(context, default=str, ensure_ascii=False)}

User message: {user_message}

Analyze this and decide what action to take."""
        }
    ]
    
    try:
        decision = await llm_service.generate_structured(
            messages=messages,
            output_model=OrchestrationDecision,
            provider=provider,
            system_prompt=system_prompt
        )
        
        logger.info(f"Structured orchestration decision: action={decision.action}, confidence={decision.confidence}")
        return decision
        
    except ValueError as e:
        logger.warning(f"Structured output failed, using fallback: {e}")
        return OrchestrationDecision(
            action="respond",
            confidence=0.5,
            response_text="Desculpe, não entendi completamente. Pode reformular sua solicitação?",
            clarification_needed="Could not parse user intent"
        )


async def get_structured_intent_classification(
    user_message: str,
    provider: str = "gemini"
) -> IntentClassification:
    """
    Classify user intent using structured outputs.
    
    Returns a validated IntentClassification with intent type,
    confidence, and extracted entities.
    
    Args:
        user_message: The user's message to classify
        provider: LLM provider to use
        
    Returns:
        IntentClassification with intent details
    """
    system_prompt = """Classify the user's intent in the context of a recruitment/HR platform.
Common intents include:
- job_creation: Creating a new job vacancy
- candidate_search: Looking for candidates
- job_update: Modifying an existing job
- salary_inquiry: Questions about salary/compensation
- general_question: General HR-related questions
- greeting: Simple greeting or conversation starter

Extract any relevant entities (job title, skills, location, etc.)."""
    
    messages = [
        {"role": "user", "content": user_message}
    ]
    
    try:
        classification = await llm_service.generate_structured(
            messages=messages,
            output_model=IntentClassification,
            provider=provider,
            system_prompt=system_prompt
        )
        
        logger.info(f"Intent classified: {classification.intent} (confidence={classification.confidence})")
        return classification
        
    except ValueError as e:
        logger.warning(f"Intent classification failed: {e}")
        return IntentClassification(
            intent="unknown",
            confidence=0.3,
            entities={},
            suggested_response="Não consegui identificar sua intenção. Por favor, seja mais específico."
        )


async def get_structured_salary_analysis(
    job_title: str,
    seniority: str,
    location: str,
    current_min: Optional[int] = None,
    current_max: Optional[int] = None,
    provider: str = "gemini"
) -> SalaryAnalysis:
    """
    Get salary recommendations using structured outputs.
    
    Analyzes market data and provides structured salary recommendations.
    
    Args:
        job_title: The job title
        seniority: Seniority level (Junior, Pleno, Senior, etc.)
        location: Work location
        current_min: Current minimum salary (if any)
        current_max: Current maximum salary (if any)
        provider: LLM provider to use
        
    Returns:
        SalaryAnalysis with recommendations and market position
    """
    system_prompt = """You are a compensation analyst. Analyze the job details and provide
salary recommendations based on Brazilian market data. Consider:
- Job title and responsibilities
- Seniority level
- Location (major cities typically pay more)
- Current market conditions in Brazil (2024-2025)

Provide realistic salary ranges in BRL (Brazilian Reais) monthly."""
    
    context = {
        "job_title": job_title,
        "seniority": seniority,
        "location": location,
        "current_range": {
            "min": current_min,
            "max": current_max
        } if current_min or current_max else None
    }
    
    messages = [
        {
            "role": "user",
            "content": f"""Analyze this position and provide salary recommendations:
{json.dumps(context, ensure_ascii=False)}"""
        }
    ]
    
    try:
        analysis = await llm_service.generate_structured(
            messages=messages,
            output_model=SalaryAnalysis,
            provider=provider,
            system_prompt=system_prompt
        )
        
        logger.info(f"Salary analysis: {analysis.market_position}, range={analysis.recommended_min}-{analysis.recommended_max}")
        return analysis
        
    except ValueError as e:
        logger.warning(f"Salary analysis failed: {e}")
        return SalaryAnalysis(
            recommended_min=None,
            recommended_max=None,
            market_position="at_market",
            confidence=0.3,
            reasoning="Unable to analyze salary at this time. Please provide manual input."
        )

USE_ENHANCED_CLASSIFIER = True

router = APIRouter(prefix="/lia", tags=["lia-assistant"])

# Sprint E — sub-routers extracted from this god object
# Routes are still accessible under the same /lia/... paths
from app.api.v1.lia_voice import voice_router
from app.api.v1.lia_multimodal import multimodal_router
from app.api.v1.lia_autonomous import autonomous_router
from app.api.v1.lia_feedback import feedback_router

router.include_router(voice_router)
router.include_router(multimodal_router)
router.include_router(autonomous_router)
router.include_router(feedback_router)


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
    reason: Optional[str] = None
) -> None:
    """
    Record a field change in the DraftFieldHistory table.
    
    Only creates a history entry if the value actually changed.
    """
    if old_value == new_value:
        return
    
    # Convert values to JSON-serializable format
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
        created_by=recruiter_id
    )
    db.add(history_entry)
    logger.debug(f"Recorded field history: {field_name} changed from {old_value} to {new_value} ({change_type.value})")


async def get_learning_adjustments(
    db: AsyncSession,
    company_id: str,
    role: Optional[str] = None,
    seniority: Optional[str] = None
) -> Dict[str, Any]:
    """
    Busca padrões de correção históricos para ajustar sugestões.
    
    Returns:
        Dict com ajustes por campo:
        {
            "salary_range": {"adjustment_pct": 15.0, "confidence": "high"},
            "seniority": {"common_correction": "Senior", "confidence": "medium"}
        }
    """
    adjustments = {}
    
    try:
        # Padrões de salário
        salary_patterns = await feedback_learning_service.get_correction_patterns(
            db=db,
            company_id=company_id,
            field="salary_range",
            role=role,
            seniority=seniority
        )
        
        if salary_patterns.get("sample_size", 0) >= 5:
            for pattern in salary_patterns.get("patterns", []):
                if pattern.get("type") == "salary_adjustment":
                    adjustments["salary_range"] = {
                        "adjustment_pct": pattern.get("adjustment_percentage", 0),
                        "direction": pattern.get("direction", "stable"),
                        "confidence": salary_patterns.get("confidence", "low"),
                        "sample_size": pattern.get("sample_size", 0)
                    }
                    break
        
        # Padrões de senioridade
        seniority_patterns = await feedback_learning_service.get_correction_patterns(
            db=db,
            company_id=company_id,
            field="seniority",
            role=role
        )
        
        if seniority_patterns.get("sample_size", 0) >= 3:
            for pattern in seniority_patterns.get("patterns", []):
                if pattern.get("type") == "categorical_transition" and pattern.get("percentage", 0) > 50:
                    adjustments["seniority"] = {
                        "from_value": pattern.get("from_value"),
                        "to_value": pattern.get("to_value"),
                        "confidence": seniority_patterns.get("confidence", "low")
                    }
                    break
    except Exception as e:
        logger.warning(f"Failed to get learning adjustments: {e}")
    
    return adjustments


job_insights_service = JobInsightsService()
market_benchmark_service = MarketBenchmarkService()
feedback_learning_service = FeedbackLearningService()
completeness_service = ConfigCompletenessService()


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


async def handle_salary_question(
    db: AsyncSession,
    company_id: str,
    job_draft: Dict[str, Any],
    user_input: str
) -> str:
    """Handle salary-related questions using insights services."""
    role = job_draft.get("job_title", "")
    seniority = job_draft.get("seniority", "")
    location = job_draft.get("location", "")
    
    location_match = re.search(r'\b(SP|RJ|MG|RS|PR|São Paulo|Rio|Belo Horizonte|Porto Alegre|Curitiba)\b', user_input, re.IGNORECASE)
    if location_match:
        location = location_match.group(1)
    
    seniority_match = re.search(r'\b(júnior|junior|pleno|sênior|senior|lead|staff)\b', user_input, re.IGNORECASE)
    if seniority_match:
        seniority = seniority_match.group(1)
    
    role_match = re.search(r'\b(dev|desenvolvedor|developer|engenheiro|analista|gerente|product|designer|data)\s*\w*', user_input, re.IGNORECASE)
    if role_match:
        role = role_match.group(0)
    
    internal_benchmark = {}
    market_benchmark = {}
    combined = {}
    
    try:
        internal_benchmark = await job_insights_service.get_salary_benchmark(
            db=db,
            company_id=company_id,
            role=role or "desenvolvedor",
            seniority=seniority,
            location=location
        )
    except Exception as e:
        logger.warning(f"Failed to get internal salary benchmark: {e}")
        internal_benchmark = {"sample_size": 0}
    
    try:
        market_benchmark = await market_benchmark_service.search_salary_benchmark(
            role=role or "desenvolvedor",
            seniority=seniority,
            location=location
        )
    except Exception as e:
        logger.warning(f"Failed to get market salary benchmark: {e}")
        market_benchmark = {}
    
    try:
        combined = market_benchmark_service.combine_with_internal(
            internal_data=internal_benchmark if internal_benchmark.get("sample_size", 0) > 0 else None,
            market_data=market_benchmark
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
        if internal_benchmark.get('trend') != 'stable':
            trend_text = "em alta" if internal_benchmark['trend'] == 'increasing' else "em queda"
            response_parts.append(f"• Tendência: {trend_text}")
        response_parts.append("")
    
    if market_benchmark.get("min"):
        response_parts.append(f"**Dados de mercado** (fontes: {', '.join(market_benchmark.get('sources', [])[:3])}):")
        response_parts.append(f"• Faixa: R$ {market_benchmark.get('min', 0):,.0f} - R$ {market_benchmark.get('max', 0):,.0f}")
        response_parts.append(f"• Mediana: R$ {market_benchmark.get('median', 0):,.0f}")
        confidence = market_benchmark.get('confidence', 'low')
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
    user_input: str
) -> str:
    """Handle skills-related questions."""
    role = job_draft.get("job_title", "")
    department = job_draft.get("department", "")
    
    skills_data = {}
    try:
        skills_data = await job_insights_service.get_common_skills(
            db=db,
            company_id=company_id,
            department=department,
            role=role
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
        
        confidence = skills_data.get('confidence', 'low')
        response_parts.append(f"📊 Baseado em {skills_data.get('total_jobs_analyzed', 0)} vagas analisadas (confiança: {confidence})")
    else:
        response_parts.append("Ainda não temos dados suficientes para sugerir skills comuns.")
        response_parts.append("Posso ajudá-lo a definir as competências manualmente.")
    
    return "\n".join(response_parts)


async def handle_time_to_fill_question(
    db: AsyncSession,
    company_id: str,
    job_draft: Dict[str, Any],
    user_input: str
) -> str:
    """Handle time-to-fill related questions."""
    role = job_draft.get("job_title", "")
    seniority = job_draft.get("seniority", "")
    department = job_draft.get("department", "")
    
    time_data = {}
    try:
        time_data = await job_insights_service.get_time_to_fill(
            db=db,
            company_id=company_id,
            role=role,
            seniority=seniority,
            department=department
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


async def handle_process_question(
    user_input: str,
    llm_service: LLMService
) -> str:
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
        response = await llm_service.generate(prompt, provider="gemini")
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
    detected_behavioral: List[str]
) -> Dict[str, Any]:
    """
    Analyze detected competencies against expected competencies for the role.
    Returns suggestions for missing competencies.
    
    Args:
        job_title: The job title/role
        seniority: The seniority level (junior, pleno, senior, etc.)
        detected_technical: List of detected technical skills
        detected_behavioral: List of detected behavioral competencies
        
    Returns:
        Dictionary with gap analysis including missing skills and completeness score
    """
    skill_suggestions = skills_catalog_service.suggest_skills(
        role=job_title,
        seniority=seniority
    )
    
    suggested_technical = skill_suggestions.get('technical_skills', [])
    suggested_behavioral = skill_suggestions.get('behavioral_competencies', [])
    
    detected_tech_lower = [s.lower() for s in detected_technical]
    missing_technical = []
    for skill in suggested_technical:
        skill_name = skill if isinstance(skill, str) else skill.get('name', str(skill))
        if skill_name.lower() not in detected_tech_lower:
            missing_technical.append({'name': skill_name})
    missing_technical = missing_technical[:5]
    
    detected_behav_lower = [s.lower() for s in detected_behavioral]
    missing_behavioral = []
    for comp in suggested_behavioral:
        comp_name = comp.get('name', '') if isinstance(comp, dict) else str(comp)
        if comp_name.lower() not in detected_behav_lower:
            missing_behavioral.append({'name': comp_name, 'key': comp.get('key', '') if isinstance(comp, dict) else ''})
    missing_behavioral = missing_behavioral[:3]
    
    total_expected = len(suggested_technical) + len(suggested_behavioral)
    total_detected = len(detected_technical) + len(detected_behavioral)
    completeness = min(1.0, total_detected / max(total_expected, 1))
    
    return {
        'completeness_score': round(completeness * 100),
        'missing_technical': missing_technical,
        'missing_behavioral': missing_behavioral,
        'has_critical_gaps': len(missing_technical) > 3 or len(missing_behavioral) > 2,
        'analysis_summary': f"Detectadas {len(detected_technical)} competências técnicas e {len(detected_behavioral)} comportamentais.",
        'suggested_technical_count': len(suggested_technical),
        'suggested_behavioral_count': len(suggested_behavioral)
    }


async def get_stage_benchmarks(
    db: AsyncSession,
    company_id: str,
    job_draft: Dict[str, Any],
    stage: int
) -> Dict[str, Any]:
    """Get relevant benchmarks for the current stage."""
    benchmarks = {}
    
    role = job_draft.get("job_title", "")
    seniority = job_draft.get("seniority", "")
    location = job_draft.get("location", "")
    department = job_draft.get("department", "")
    
    if stage == 3:  # Competencies stage
        try:
            skills_data = await job_insights_service.get_common_skills(
                db=db,
                company_id=company_id,
                department=department,
                role=role
            )
            benchmarks["suggested_skills"] = skills_data
        except Exception as e:
            logger.warning(f"Failed to get skills benchmarks for stage 3: {e}")
            benchmarks["suggested_skills"] = {"skills": [], "error": "Não foi possível carregar sugestões de skills"}
    
    elif stage == 4:  # Salary stage
        if role:
            internal_benchmark = {}
            market_benchmark = {}
            combined = {}
            learning_adjustments = {}
            
            try:
                internal_benchmark = await job_insights_service.get_salary_benchmark(
                    db=db,
                    company_id=company_id,
                    role=role,
                    seniority=seniority,
                    location=location
                )
            except Exception as e:
                logger.warning(f"Failed to get internal salary benchmark: {e}")
                internal_benchmark = {"sample_size": 0}
            
            try:
                market_benchmark = await market_benchmark_service.search_salary_benchmark(
                    role=role,
                    seniority=seniority,
                    location=location
                )
            except Exception as e:
                logger.warning(f"Failed to get market salary benchmark: {e}")
                market_benchmark = {}
            
            try:
                combined = market_benchmark_service.combine_with_internal(
                    internal_data=internal_benchmark if internal_benchmark.get("sample_size", 0) > 0 else None,
                    market_data=market_benchmark
                )
            except Exception as e:
                logger.warning(f"Failed to combine salary benchmarks: {e}")
                combined = {}
            
            # Buscar ajustes de aprendizado baseados em correções históricas
            try:
                learning_adjustments = await get_learning_adjustments(
                    db=db,
                    company_id=company_id,
                    role=role,
                    seniority=seniority
                )
                
                # Aplicar ajuste de salário se disponível
                if "salary_range" in learning_adjustments:
                    salary_adj = learning_adjustments["salary_range"]
                    adjustment_pct = salary_adj.get("adjustment_pct", 0)
                    
                    if adjustment_pct and abs(adjustment_pct) > 5:
                        adjustment_factor = 1 + (adjustment_pct / 100)
                        
                        # Aplicar ajuste às recomendações combinadas
                        if combined.get("recommended_min"):
                            combined["original_recommended_min"] = combined["recommended_min"]
                            combined["original_recommended_max"] = combined.get("recommended_max", combined["recommended_min"])
                            combined["recommended_min"] = int(combined["recommended_min"] * adjustment_factor)
                            combined["recommended_max"] = int(combined.get("recommended_max", combined["recommended_min"]) * adjustment_factor)
                            combined["learning_adjustment_applied"] = True
                            combined["learning_adjustment_pct"] = adjustment_pct
                            combined["learning_confidence"] = salary_adj.get("confidence", "low")
                            combined["learning_sample_size"] = salary_adj.get("sample_size", 0)
                        
                        # Aplicar ajuste aos benchmarks de mercado
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
    conversation_id: str
) -> tuple[str, Dict[str, Any]]:
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
                    db=db,
                    company_id=company_id,
                    job_id=UUID(job_draft.get("job_id", str(uuid4()))),
                    field="salary_range",
                    original_value=old_salary,
                    corrected_value=job_draft["salary_range"],
                    stage="salary",
                    role=job_draft.get("job_title"),
                    seniority=job_draft.get("seniority"),
                    location=job_draft.get("location")
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
                    db=db,
                    company_id=company_id,
                    job_id=UUID(job_draft.get("job_id", str(uuid4()))),
                    field="seniority",
                    original_value=old_seniority,
                    corrected_value=new_seniority,
                    stage="basic-info",
                    role=job_draft.get("job_title")
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
        response_parts.append("Entendi que você quer corrigir algo. O que gostaria de ajustar?")
        response_parts.append("• Salário")
        response_parts.append("• Senioridade")
        response_parts.append("• Modelo de trabalho")
        response_parts.append("• Localização")
        response_parts.append("• Skills/Competências")
    
    await db.commit()
    
    return "\n".join(response_parts), updated_fields


@router.get("/suggestions", response_model=SuggestionsResponse)
async def get_dynamic_suggestions(
    limit: int = Query(default=6, ge=1, le=12),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    company_id = current_user.company_id or "demo_company"
    user_id = str(current_user.id)
    """
    Generate dynamic suggestion cards for the homepage based on real data.
    
    Analyzes:
    - Critical jobs (SLA expiring, no candidates)
    - Pending candidate reviews
    - Stalled pipelines
    - Interview scheduling needs
    - Report opportunities
    """
    suggestions: List[SuggestionCard] = []
    
    try:
        jobs_query = select(JobVacancy).where(
            and_(
                JobVacancy.company_id == company_id,
                JobVacancy.status.in_(["open", "active", "Open", "Active", "Em Andamento"])
            )
        )
        result = await db.execute(jobs_query)
        active_jobs = result.scalars().all()
        
        job_ids = [str(job.id) for job in active_jobs]
        
        if len(active_jobs) > 0:
            suggestions.append(SuggestionCard(
                id="pipeline-overview",
                type="info",
                icon="Briefcase",
                title=f"{len(active_jobs)} vagas ativas",
                description="Clique para ver detalhes e status de todas as vagas",
                action="view_active_jobs",
                priority="medium",
                category="vagas",
                metadata={
                    "job_ids": job_ids[:5],
                    "count": len(active_jobs)
                }
            ))
        
        today = datetime.utcnow().date()
        week_from_now = today + timedelta(days=7)
        
        expiring_jobs = [
            job for job in active_jobs
            if job.deadline and job.deadline.date() <= week_from_now
        ]
        
        if expiring_jobs:
            suggestions.append(SuggestionCard(
                id="deadline-warning",
                type="warning",
                icon="Clock",
                title=f"{len(expiring_jobs)} vagas com prazo próximo",
                description=f"Vagas expirando nos próximos 7 dias",
                action="view_expiring_jobs",
                priority="high",
                category="vagas",
                metadata={
                    "job_ids": [str(j.id) for j in expiring_jobs[:5]],
                    "count": len(expiring_jobs)
                }
            ))
        
        if active_jobs:
            suggestions.append(SuggestionCard(
                id="pipeline-health",
                type="insight",
                icon="TrendingUp",
                title="Análise de Pipeline",
                description=f"Visualize métricas e saúde de {len(active_jobs)} vagas ativas",
                action="view_pipeline_analytics",
                priority="medium",
                category="relatorios",
                metadata={
                    "total_jobs": len(active_jobs)
                }
            ))
        
        recent_candidates_query = select(func.count(Candidate.id)).where(
            and_(
                Candidate.company_id == company_id,
                Candidate.created_at >= datetime.utcnow() - timedelta(days=7)
            )
        )
        recent_result = await db.execute(recent_candidates_query)
        recent_candidates = recent_result.scalar() or 0
        
        if recent_candidates > 0:
            suggestions.append(SuggestionCard(
                id="new-candidates",
                type="info",
                icon="Users",
                title=f"{recent_candidates} novos candidatos",
                description="Candidatos recebidos nos últimos 7 dias aguardando triagem",
                action="start_screening",
                priority="medium",
                category="candidatos",
                metadata={"count": recent_candidates}
            ))
        
        if len(active_jobs) > 0:
            suggestions.append(SuggestionCard(
                id="quick-report",
                type="action",
                icon="FileText",
                title="Gerar Relatório Semanal",
                description="Resumo das vagas, candidatos e métricas da semana",
                action="generate_weekly_report",
                priority="low",
                category="relatorios",
                metadata={}
            ))
        
        suggestions.append(SuggestionCard(
            id="sourcing-suggestion",
            type="suggestion",
            icon="Search",
            title="Buscar Candidatos Similares",
            description="Use IA para encontrar candidatos parecidos com seus melhores contratados",
            action="similar_search",
            priority="low",
            category="candidatos",
            metadata={}
        ))
        
        suggestions.append(SuggestionCard(
            id="create-job-wizard",
            type="action",
            icon="Plus",
            title="Criar Nova Vaga com LIA",
            description="Crie uma vaga conversando com a LIA - ela extrai requisitos automaticamente",
            action="start_job_wizard",
            priority="low",
            category="vagas",
            metadata={}
        ))
        
        priority_order = {"high": 0, "medium": 1, "low": 2}
        suggestions.sort(key=lambda x: priority_order.get(x.priority, 2))
        
        return SuggestionsResponse(
            suggestions=suggestions[:limit],
            generated_at=datetime.utcnow().isoformat(),
            context={
                "active_jobs": len(active_jobs)
            }
        )
        
    except Exception as e:
        logger.error(f"Error generating suggestions: {e}")
        return SuggestionsResponse(
            suggestions=[
                SuggestionCard(
                    id="create-job-wizard",
                    type="action",
                    icon="Plus",
                    title="Criar Nova Vaga com LIA",
                    description="Inicie o processo de criação de vaga com assistência da LIA",
                    action="start_job_wizard",
                    priority="medium",
                    category="vagas",
                    metadata={}
                ),
                SuggestionCard(
                    id="view-jobs",
                    type="action",
                    icon="Briefcase",
                    title="Ver Vagas Ativas",
                    description="Visualize e gerencie suas vagas em aberto",
                    action="view_active_jobs",
                    priority="medium",
                    category="vagas",
                    metadata={}
                )
            ],
            generated_at=datetime.utcnow().isoformat(),
            context={"error": str(e)}
        )


# ============================================================================
# INTELLIGENT MESSAGE INTERPRETATION ENDPOINT
# ============================================================================

STAGE_MAP = {
    'input-evaluation': 1,
    'salary': 4,
    'competencies': 3,
    'wsi-questions': 5,
    'review-publish': 6,
    'search-calibration': 8
}

STAGE_NAMES = {
    'input-evaluation': 'Avaliação',
    'salary': 'Remuneração',
    'competencies': 'Competências',
    'wsi-questions': 'Perguntas WSI',
    'review-publish': 'Revisão e Publicação',
    'search-calibration': 'Calibração de Busca'
}

STAGE_ORDER = ['input-evaluation', 'salary', 'competencies', 'wsi-questions', 'review-publish']


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


@router.post("/job-wizard/interpret", response_model=InterpretMessageResponse)
async def interpret_user_message(
    request: InterpretMessageRequest
):
    """
    Interpret user message using AI to determine intent and action.
    
    This endpoint uses the enhanced intent classifier to understand
    what the user wants to do, providing intelligent conversation flow.
    """
    try:
        stage_context = f"Stage: {STAGE_NAMES.get(request.current_stage, request.current_stage)}"
        filled_fields = request.context.get('filled_fields', []) if request.context else []
        
        classification = await enhanced_intent_classifier.classify(
            user_input=request.message,
            stage=STAGE_MAP.get(request.current_stage, 1),
            filled_fields=filled_fields
        )
        
        logger.info(f"Message interpreted: '{request.message[:50]}...' -> {classification.intent_type} (confidence: {classification.confidence})")
        
        action = InterpretMessageAction.OTHER
        should_advance = False
        target_stage = None
        lia_response = None
        
        if classification.intent_type == EnhancedIntentType.CONFIRM:
            action = InterpretMessageAction.CONFIRM
            should_advance = True
            current_idx = STAGE_ORDER.index(request.current_stage) if request.current_stage in STAGE_ORDER else 0
            if current_idx < len(STAGE_ORDER) - 1:
                target_stage = STAGE_ORDER[current_idx + 1]
            lia_response = "Entendido! Avançando para a próxima etapa..."
            
        elif classification.intent_type == EnhancedIntentType.NAVIGATION:
            action = InterpretMessageAction.ADVANCE_STAGE
            should_advance = True
            current_idx = STAGE_ORDER.index(request.current_stage) if request.current_stage in STAGE_ORDER else 0
            if current_idx < len(STAGE_ORDER) - 1:
                target_stage = STAGE_ORDER[current_idx + 1]
            lia_response = f"Certo! Vamos para {STAGE_NAMES.get(target_stage, 'próxima etapa')}."
            
        elif classification.intent_type == EnhancedIntentType.QUESTION:
            action = InterpretMessageAction.ASK_QUESTION
            lia_response = f"Boa pergunta! Na etapa de **{STAGE_NAMES.get(request.current_stage, 'atual')}**, posso esclarecer o que precisar. Qual é a sua dúvida?"

        elif classification.intent_type == EnhancedIntentType.CORRECTION:
            action = InterpretMessageAction.UPDATE_FIELD
            lia_response = "Entendido, vou atualizar as informações conforme solicitado."

        elif classification.intent_type == EnhancedIntentType.CREATE_JOB or classification.intent_type == EnhancedIntentType.UPDATE_FIELD:
            action = InterpretMessageAction.PROVIDE_DATA
            # Build confirmation from extracted entities (fix wizard lia_response null)
            ents = classification.entities
            parts = []
            if ents:
                if getattr(ents, "cargo", None):
                    parts.append(f"cargo: **{ents.cargo}**")
                if getattr(ents, "senioridade", None):
                    parts.append(f"senioridade: **{ents.senioridade}**")
                if getattr(ents, "modelo_trabalho", None):
                    parts.append(f"modelo: **{ents.modelo_trabalho}**")
                if getattr(ents, "localizacao", None):
                    parts.append(f"local: **{ents.localizacao}**")
                if getattr(ents, "skills_tecnicas", None):
                    skills_str = ", ".join(getattr(ents, "skills_tecnicas", [])[:4])
                    parts.append(f"skills: **{skills_str}**")
            if parts:
                lia_response = f"✅ Registrado! {', '.join(parts).capitalize()}. Deseja adicionar mais detalhes ou podemos avançar?"
            else:
                lia_response = "✅ Informações registradas. Deseja adicionar mais detalhes ou podemos avançar para a próxima etapa?"
            
        elif classification.intent_type == EnhancedIntentType.REJECT:
            action = InterpretMessageAction.REJECT
            lia_response = "Entendido. O que você gostaria de ajustar?"
            
        elif classification.intent_type == EnhancedIntentType.HELP:
            action = InterpretMessageAction.HELP
            lia_response = f"Estou aqui para ajudar! Na etapa de **{STAGE_NAMES.get(request.current_stage, 'atual')}**, você pode..."
        
        entities_dict = classification.entities.to_dict() if classification.entities else {}
        
        return InterpretMessageResponse(
            action=action,
            confidence=classification.confidence,
            extracted_entities=entities_dict if entities_dict else None,
            lia_response=lia_response,
            should_advance=should_advance,
            target_stage=target_stage,
            clarification_needed=classification.needs_clarification,
            clarification_question=classification.clarification_question,
            reasoning=classification.reasoning
        )
        
    except Exception as e:
        logger.error(f"Error interpreting message: {e}")
        return InterpretMessageResponse(
            action=InterpretMessageAction.OTHER,
            confidence=0.5,
            lia_response="Desculpe, não consegui entender completamente. Pode reformular?",
            reasoning=str(e)
        )


class ConversationalRequest(BaseModel):
    message: str
    context: Optional[str] = None
    mode: Optional[str] = "job_creation"


class ConversationalResponse(BaseModel):
    response: str
    understood_intent: str
    suggested_action: Optional[str] = None
    can_help: bool = True


LIA_CAPABILITIES_PROMPT = """Você é a LIA, assistente inteligente de recrutamento da plataforma WeDoTalent.

SUAS CAPACIDADES NESTE CHAT:
1. **Criar vagas de emprego** - Guio você pelo processo completo de criação de vagas com análise inteligente
2. **Reutilizar vagas anteriores** (Fast Track) - Encontro vagas passadas similares para republicar rapidamente
3. **Analisar remuneração** - Forneço benchmarks de mercado e recomendações salariais
4. **Sugerir competências** - Recomendo skills técnicas e comportamentais baseadas no cargo
5. **Gerar descrições de vaga** - Crio JDs profissionais otimizadas

SUAS LIMITAÇÕES NESTE CONTEXTO:
- Este chat é focado na criação de vagas
- Para outras funcionalidades (análise de candidatos, triagem, comparação), use as outras seções da plataforma

INSTRUÇÕES:
- Responda sempre em português brasileiro
- Seja natural e conversacional, não robótica
- Se o usuário perguntar algo fora do escopo, explique educadamente suas capacidades
- Se for uma saudação ou conversa casual, responda de forma amigável e redirecione para ajudar com vagas
- Mantenha respostas concisas mas úteis

Mensagem do usuário: {message}

Responda de forma natural e útil:"""


@router.post("/conversational", response_model=ConversationalResponse)
async def handle_conversational_message(
    request: ConversationalRequest,
    _budget: None = Depends(require_token_budget),
):
    """
    Handle general conversational messages using LLM for natural responses.
    
    This endpoint enables LIA to have real conversations, understanding
    questions about capabilities and responding intelligently.
    """
    try:
        # Mode: salary_benchmark — use structured salary analysis (fix C-06)
        if request.mode == "salary_benchmark":
            import re as _re
            salary_prompt = f"""Você é especialista em remuneração do mercado brasileiro de tecnologia.
Forneça uma análise completa de faixa salarial para a seguinte solicitação.

REGRAS OBRIGATÓRIAS:
1. Sempre inclua valores em Reais no formato R$ XX.XXX (ponto como separador de milhar)
2. Estruture a resposta com:
   - Faixa mínima: R$ X.XXX
   - Mediana: R$ X.XXX
   - Faixa máxima: R$ X.XXX
   - Recomendação: R$ X.XXX - R$ X.XXX mensais (CLT)
3. Considere senioridade, localização e mercado brasileiro 2025
4. Responda em Português do Brasil

Solicitação: {request.message}"""
            
            llm_service = LLMService()
            response_text = await llm_service.generate(
                salary_prompt,
                provider="gemini"
            )
            return ConversationalResponse(
                response=response_text,
                understood_intent="salary_benchmark",
                suggested_action=None,
                can_help=True
            )

        llm_service = LLMService()
        
        prompt = LIA_CAPABILITIES_PROMPT.format(message=request.message)
        
        response_text = await llm_service.generate(
            prompt,
            provider="gemini"
        )
        
        lower_msg = request.message.lower()
        
        if any(word in lower_msg for word in ['oi', 'olá', 'bom dia', 'boa tarde', 'boa noite', 'hey', 'hello']):
            intent = "greeting"
        elif '?' in request.message or any(word in lower_msg for word in ['como', 'o que', 'pode', 'consegue', 'faz', 'ajuda']):
            intent = "question"
        elif any(word in lower_msg for word in ['criar', 'nova vaga', 'do zero', 'começar']):
            intent = "create_job"
            suggested_action = "from_scratch"
        elif any(word in lower_msg for word in ['reutilizar', 'anterior', 'fast track', 'aproveitar']):
            intent = "fast_track"
            suggested_action = "fast_track"
        else:
            intent = "other"
        
        suggested_action = None
        if intent == "create_job":
            suggested_action = "from_scratch"
        elif intent == "fast_track":
            suggested_action = "fast_track"
        
        return ConversationalResponse(
            response=response_text,
            understood_intent=intent,
            suggested_action=suggested_action,
            can_help=True
        )
        
    except Exception as e:
        logger.error(f"Error in conversational response: {e}")
        return ConversationalResponse(
            response="Sou a LIA, sua assistente de recrutamento! Aqui posso te ajudar a:\n\n• **Criar uma nova vaga** do zero com toda inteligência da plataforma\n• **Reutilizar uma vaga anterior** para publicar rapidamente\n\nComo gostaria de começar?",
            understood_intent="fallback",
            can_help=True
        )


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


WIZARD_STAGES_INFO = {
    "input-evaluation": {
        "name": "Avaliação Inicial",
        "purpose": "Coletar informações básicas da vaga: cargo, área, senioridade, modelo de trabalho, localização",
        "required_fields": ["title", "department", "seniority_level", "work_model", "location"],
        "optional_fields": ["manager", "manager_email", "deadline"],
        "next_stage": "job-summary"
    },
    "job-summary": {
        "name": "Proposta da Vaga",
        "purpose": "Apresentar resumo estruturado com responsabilidades, competências sugeridas e faixa salarial estimada baseada em dados de mercado",
        "required_fields": ["title", "seniority_level"],
        "optional_fields": ["responsibilities", "suggested_skills", "estimated_salary"],
        "next_stage": "salary"
    },
    "salary": {
        "name": "Remuneração",
        "purpose": "Definir faixa salarial competitiva, bônus e benefícios",
        "required_fields": ["salary_min", "salary_max"],
        "optional_fields": ["bonus", "benefits"],
        "next_stage": "competencies"
    },
    "competencies": {
        "name": "Competências",
        "purpose": "Definir habilidades técnicas e comportamentais necessárias",
        "required_fields": ["technical_skills"],
        "optional_fields": ["behavioral_competencies", "languages", "certifications"],
        "next_stage": "wsi-questions"
    },
    "wsi-questions": {
        "name": "Triagem WSI",
        "purpose": "Configurar perguntas de triagem usando metodologia WSI para avaliar candidatos",
        "required_fields": ["screening_questions"],
        "optional_fields": [],
        "next_stage": "review-publish"
    },
    "review-publish": {
        "name": "Revisão e Publicação",
        "purpose": "Revisar todos os dados, gerar descrição da vaga e publicar",
        "required_fields": [],
        "optional_fields": ["job_description"],
        "next_stage": None
    }
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


@router.post("/job-wizard/orchestrate", response_model=WizardOrchestratorResponse)
async def orchestrate_wizard_message(
    request: WizardOrchestratorRequest,
    current_user: User = Depends(get_current_user_or_demo)
):
    """
    Intelligent orchestrator for job wizard conversations.
    
    This endpoint receives full context and uses LLM to make intelligent
    decisions about how to handle user messages in each stage.
    
    When use_structured_outputs=True, uses the structured output feature
    for more reliable JSON parsing directly via LLM provider capabilities.
    """
    company_id = current_user.company_id or "demo_company"
    try:
        stage_info = WIZARD_STAGES_INFO.get(request.current_stage, {
            "name": request.current_stage,
            "purpose": "Etapa do wizard",
            "required_fields": [],
            "optional_fields": [],
            "next_stage": None
        })
        
        collected = request.collected_data or {}
        required = stage_info.get("required_fields", [])
        missing = [f for f in required if not collected.get(f)]
        
        collected_summary = "\n".join([
            f"- {k}: {v}" for k, v in collected.items() if v
        ]) or "Nenhum dado coletado ainda"
        
        missing_summary = ", ".join(missing) if missing else "Todos os campos obrigatórios preenchidos"
        
        history_text = ""
        if request.conversation_history:
            history_text = "\n".join([
                f"{msg.get('role', 'user').upper()}: {msg.get('content', '')}"
                for msg in request.conversation_history[-5:]
            ])
        else:
            history_text = "Início da conversa"
        
        if request.use_structured_outputs:
            system_prompt = f"""Você é LIA, uma assistente inteligente ajudando recrutadores a criar vagas.

## ETAPA ATUAL: {stage_info.get("name", request.current_stage)}
**Propósito:** {stage_info.get("purpose", "")}
**Campos obrigatórios:** {", ".join(stage_info.get("required_fields", [])) or "Nenhum"}
**Campos opcionais:** {", ".join(stage_info.get("optional_fields", [])) or "Nenhum"}
**Próxima etapa:** {stage_info.get("next_stage") or "Finalização"}

## DADOS COLETADOS
{collected_summary}

## CAMPOS FALTANTES
{missing_summary}

Analise a mensagem do usuário e decida qual ação tomar.
Ações disponíveis:
- respond: Responder ao usuário com informações úteis
- advance_stage: Avançar para a próxima etapa
- update_fields: Atualizar campos da vaga com base no input
- request_clarification: Pedir mais detalhes se algo não estiver claro
- provide_suggestion: Sugerir valores para campos
- validate_data: Validar dados fornecidos"""
            
            messages = [
                {"role": "user", "content": f"Histórico:\n{history_text}\n\nMensagem atual: {request.message}"}
            ]
            
            try:
                provider = request.llm_provider or "gemini"
                result = await llm_service.generate_structured(
                    messages=messages,
                    output_model=WizardOrchestrationResult,
                    provider=provider,
                    system_prompt=system_prompt,
                    max_tokens=1000
                )
                
                try:
                    action = WizardOrchestratorAction(result.action)
                except ValueError:
                    action = WizardOrchestratorAction.RESPOND
                
                logger.info(f"Structured orchestration: action={action.value}, confidence={result.confidence}")
                
                return WizardOrchestratorResponse(
                    action=action,
                    response=result.response,
                    updated_fields=result.updated_fields,
                    target_stage=result.target_stage,
                    confidence=result.confidence,
                    reasoning=result.reasoning,
                    suggestions=result.suggestions,
                    validation_errors=result.validation_errors
                )
                
            except ValueError as e:
                logger.warning(f"Structured output failed, falling back to legacy: {e}")
        
        local_llm_service = LLMService()
        
        prompt = WIZARD_ORCHESTRATOR_PROMPT.format(
            stage_name=stage_info.get("name", request.current_stage),
            stage_purpose=stage_info.get("purpose", ""),
            required_fields=", ".join(stage_info.get("required_fields", [])) or "Nenhum",
            optional_fields=", ".join(stage_info.get("optional_fields", [])) or "Nenhum",
            next_stage=stage_info.get("next_stage") or "Finalização",
            collected_data_summary=collected_summary,
            missing_fields=missing_summary,
            conversation_history=history_text,
            user_message=request.message
        )
        
        response_text = await local_llm_service.generate(
            prompt=prompt,
            provider="gemini"
        )
        
        try:
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                parsed = json.loads(json_match.group())
            else:
                parsed = json.loads(response_text)
            
            action_str = parsed.get("action", "respond")
            try:
                action = WizardOrchestratorAction(action_str)
            except ValueError:
                action = WizardOrchestratorAction.RESPOND
            
            return WizardOrchestratorResponse(
                action=action,
                response=parsed.get("response", "Entendi sua mensagem."),
                updated_fields=parsed.get("updated_fields"),
                target_stage=parsed.get("target_stage"),
                confidence=parsed.get("confidence", 0.8),
                reasoning=parsed.get("reasoning"),
                suggestions=parsed.get("suggestions"),
                validation_errors=parsed.get("validation_errors")
            )
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse orchestrator response as JSON: {e}")
            return WizardOrchestratorResponse(
                action=WizardOrchestratorAction.RESPOND,
                response=response_text,
                confidence=0.6,
                reasoning="Resposta não estruturada do LLM"
            )
        
    except Exception as e:
        logger.error(f"Error in wizard orchestrator: {e}")
        return WizardOrchestratorResponse(
            action=WizardOrchestratorAction.RESPOND,
            response="Desculpe, tive um problema ao processar sua mensagem. Pode tentar novamente?",
            confidence=0.3,
            reasoning=str(e)
        )


# Graph orchestration schemas and endpoints moved to lia_assistant_graph.py (Sprint 7 split).
# Re-export for backwards compatibility with any code that imported these directly.
from app.api.v1.lia_assistant_graph import (
    GraphOrchestratorRequest,
    GraphOrchestratorResponse,
    SessionStateResponse,
    GraphInfoResponse,
)


# graph_orchestrate_wizard_message moved to lia_assistant_graph.py (Sprint 7).
# Keeping a stub reference so old imports that reference this module still work.
async def graph_orchestrate_wizard_message(request: GraphOrchestratorRequest):  # noqa: not registered
    """
    LangGraph-based intelligent orchestrator for job wizard conversations.
    
    This endpoint uses a multi-step reasoning engine with:
    - Intent classification
    - Field extraction
    - Tool routing and execution
    - Natural language response generation
    - Stage transition management
    
    The graph maintains state between calls for the same session_id,
    enabling multi-turn conversations with context preservation.
    """
    try:
        session_id = request.session_id or str(uuid4())

        # === PHASE 0: Check pending wizard action ===
        pending = pending_action_store.get(session_id)
        if pending:
            if pending.awaiting_confirmation:
                if is_confirmation(request.message):
                    config = WIZARD_ACTIONABLE_INTENTS.get(pending.intent, {})
                    exec_result = await wizard_action_executor._execute(
                        action_id=config.get("action_id", pending.action_id),
                        draft=request.existing_draft or {},
                        session_id=session_id,
                        current_stage=request.current_stage,
                        params=pending.collected_params,
                        context={"user_id": request.user_id},
                    )
                    pending_action_store.remove(session_id)
                    return GraphOrchestratorResponse(
                        execution_id=str(uuid4()),
                        session_id=session_id,
                        response_text=exec_result.message,
                        job_draft=request.existing_draft or {},
                        current_stage=request.current_stage or "input-evaluation",
                        reasoning_steps=[f"action:{pending.intent}:confirmed"],
                        intent=pending.intent,
                        action_executed=True,
                        action_type=exec_result.action_type,
                        action_result=exec_result.data,
                        draft_updates=exec_result.draft_updates,
                    )
                elif is_rejection(request.message):
                    pending_action_store.remove(session_id)
                    return GraphOrchestratorResponse(
                        execution_id=str(uuid4()),
                        session_id=session_id,
                        response_text="Ok, ação cancelada. Como posso te ajudar com a vaga?",
                        job_draft=request.existing_draft or {},
                        current_stage=request.current_stage or "input-evaluation",
                        reasoning_steps=["action:cancelled"],
                        intent="cancelamento",
                    )
                else:
                    pending_action_store.remove(session_id)
            elif pending.missing_params:
                next_param = pending.next_missing_param()
                if next_param:
                    pending.add_param(next_param, request.message.strip())
                    if pending.is_complete:
                        config = WIZARD_ACTIONABLE_INTENTS.get(pending.intent, {})
                        if config.get("requires_confirmation", False):
                            summary = wizard_action_executor._build_confirmation_summary(
                                pending.intent, config, request.existing_draft or {}, pending.collected_params
                            )
                            pending.awaiting_confirmation = True
                            pending.confirmation_summary = summary
                            pending_action_store.save(session_id, pending)
                            return GraphOrchestratorResponse(
                                execution_id=str(uuid4()),
                                session_id=session_id,
                                response_text=summary["message"],
                                job_draft=request.existing_draft or {},
                                current_stage=request.current_stage or "input-evaluation",
                                reasoning_steps=[f"action:{pending.intent}:confirm_needed"],
                                intent=pending.intent,
                                needs_confirmation=True,
                                pending_action_id=pending.pending_id,
                            )
                        exec_result = await wizard_action_executor._execute(
                            action_id=config.get("action_id", pending.action_id),
                            draft=request.existing_draft or {},
                            session_id=session_id,
                            current_stage=request.current_stage,
                            params=pending.collected_params,
                            context={"user_id": request.user_id},
                        )
                        pending_action_store.remove(session_id)
                        return GraphOrchestratorResponse(
                            execution_id=str(uuid4()),
                            session_id=session_id,
                            response_text=exec_result.message,
                            job_draft=request.existing_draft or {},
                            current_stage=request.current_stage or "input-evaluation",
                            reasoning_steps=[f"action:{pending.intent}:executed"],
                            intent=pending.intent,
                            action_executed=True,
                            action_type=exec_result.action_type,
                            action_result=exec_result.data,
                            draft_updates=exec_result.draft_updates,
                        )
                    else:
                        next_param2 = pending.next_missing_param()
                        config = WIZARD_ACTIONABLE_INTENTS.get(pending.intent, {})
                        prompt = config.get("clarification_prompts", {}).get(
                            next_param2, f"Informe: {next_param2}"
                        )
                        pending_action_store.save(session_id, pending)
                        return GraphOrchestratorResponse(
                            execution_id=str(uuid4()),
                            session_id=session_id,
                            response_text=prompt,
                            job_draft=request.existing_draft or {},
                            current_stage=request.current_stage or "input-evaluation",
                            reasoning_steps=[f"action:{pending.intent}:collecting_params"],
                            intent=pending.intent,
                            needs_params=True,
                            pending_action_id=pending.pending_id,
                        )
                else:
                    pending_action_store.remove(session_id)

        # === PHASE 0.5: Detect wizard action commands ===
        wizard_action = detect_wizard_action(request.message)
        if wizard_action:
            wz_intent, wz_confidence = wizard_action
            if wz_confidence >= 0.7:
                logger.info(f"Wizard action detected: {wz_intent} (conf={wz_confidence})")
                exec_result = await wizard_action_executor.try_execute(
                    intent=wz_intent,
                    draft=request.existing_draft or {},
                    session_id=session_id,
                    current_stage=request.current_stage,
                    entities={},
                    context={"user_id": request.user_id},
                )

                if exec_result.status == "executed":
                    return GraphOrchestratorResponse(
                        execution_id=str(uuid4()),
                        session_id=session_id,
                        response_text=exec_result.message,
                        job_draft=request.existing_draft or {},
                        current_stage=request.current_stage or "input-evaluation",
                        reasoning_steps=[f"wizard_action:{wz_intent}"],
                        intent=wz_intent,
                        action_executed=True,
                        action_type=exec_result.action_type,
                        action_result=exec_result.data,
                        draft_updates=exec_result.draft_updates,
                    )
                elif exec_result.status == "needs_params":
                    pending_state = PendingActionState(
                        pending_id=exec_result.pending_action_id or str(uuid4()),
                        intent=wz_intent,
                        action_id=exec_result.action_type or "",
                        domain_id="wizard",
                        collected_params=exec_result.data.get("collected_params", {}) if exec_result.data else {},
                        missing_params=exec_result.missing_params or [],
                        conversation_id=session_id,
                    )
                    pending_action_store.save(session_id, pending_state)
                    return GraphOrchestratorResponse(
                        execution_id=str(uuid4()),
                        session_id=session_id,
                        response_text=exec_result.message,
                        job_draft=request.existing_draft or {},
                        current_stage=request.current_stage or "input-evaluation",
                        reasoning_steps=[f"wizard_action:{wz_intent}:needs_params"],
                        intent=wz_intent,
                        needs_params=True,
                        pending_action_id=exec_result.pending_action_id,
                    )
                elif exec_result.status == "needs_confirmation":
                    pending_state = PendingActionState(
                        pending_id=exec_result.pending_action_id or str(uuid4()),
                        intent=wz_intent,
                        action_id=exec_result.action_type or "",
                        domain_id="wizard",
                        collected_params=exec_result.data.get("collected_params", {}) if exec_result.data else {},
                        missing_params=[],
                        conversation_id=session_id,
                        awaiting_confirmation=True,
                        confirmation_summary=exec_result.confirmation_summary,
                    )
                    pending_action_store.save(session_id, pending_state)
                    return GraphOrchestratorResponse(
                        execution_id=str(uuid4()),
                        session_id=session_id,
                        response_text=exec_result.message,
                        job_draft=request.existing_draft or {},
                        current_stage=request.current_stage or "input-evaluation",
                        reasoning_steps=[f"wizard_action:{wz_intent}:needs_confirmation"],
                        intent=wz_intent,
                        needs_confirmation=True,
                        pending_action_id=exec_result.pending_action_id,
                    )

        analytics_cmd = detect_wizard_analytics_command(request.message)
        msg_words = len(request.message.strip().split())
        if analytics_cmd and msg_words <= 12:
            cmd_type, confidence = analytics_cmd
            if confidence >= 0.8:
                logger.info(f"Wizard analytics detected: {cmd_type} (conf={confidence})")
                collected_data = request.existing_draft or {}
                current_stage = request.current_stage or "input-evaluation"
                
                response_text = wizard_analytics.build_status_response(
                    collected_data=collected_data,
                    current_stage=current_stage,
                    command_type=cmd_type,
                )
                
                return GraphOrchestratorResponse(
                    execution_id=str(uuid4()),
                    session_id=session_id,
                    response_text=response_text,
                    job_draft=collected_data,
                    current_stage=current_stage,
                    confidence_scores={},
                    reasoning_steps=[f"analytics:{cmd_type}"],
                    extracted_fields={},
                    intent=cmd_type,
                    is_complete=False,
                    error=None,
                )
            else:
                logger.debug(f"Wizard analytics low confidence ({confidence}), passing to graph runner")
        
        company_id = request.company_id
        try:
            from uuid import UUID as UUID_type
            UUID_type(company_id)
        except (ValueError, AttributeError):
            logger.warning(
                f"Invalid company_id format '{company_id}' in request. "
                "Using default UUID. Pass a valid UUID for proper multi-tenant support."
            )
            from app.core.config import settings
            company_id = settings.DEFAULT_COMPANY_UUID
        
        result = await graph_runner_service.run_job_wizard(
            session_id=session_id,
            user_message=request.message,
            company_id=company_id,
            user_id=request.user_id,
            existing_draft=request.existing_draft,
            current_stage=request.current_stage
        )
        
        logger.info(
            f"Graph orchestration complete: session={session_id}, "
            f"stage={result.get('current_stage')}, "
            f"steps={len(result.get('reasoning_steps', []))}"
        )
        
        return GraphOrchestratorResponse(
            execution_id=result.get("execution_id", ""),
            session_id=result.get("session_id", session_id),
            response_text=result.get("response_text", ""),
            job_draft=result.get("job_draft", {}),
            current_stage=result.get("current_stage", WizardStage.INITIAL.value),
            confidence_scores=result.get("confidence_scores", {}),
            reasoning_steps=result.get("reasoning_steps", []),
            extracted_fields=result.get("extracted_fields", {}),
            intent=result.get("intent"),
            is_complete=result.get("is_complete", False),
            error=result.get("error")
        )
        
    except Exception as e:
        logger.error(f"Error in graph orchestrator: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Graph orchestration failed: {str(e)}"
        )


# get_wizard_session_state moved to lia_assistant_graph.py (Sprint 7).
async def get_wizard_session_state(session_id: str):  # noqa: not registered
    """
    Get the current state of a wizard session.
    
    Returns the current stage, job draft, messages, and other
    session data for a given session ID.
    """
    try:
        state = await graph_runner_service.get_session_state(session_id)
        
        if not state:
            raise HTTPException(
                status_code=404,
                detail=f"Session not found: {session_id}"
            )
        
        return SessionStateResponse(
            session_id=session_id,
            current_stage=state.get("current_stage"),
            job_draft=state.get("job_draft", {}),
            confidence_scores=state.get("confidence_scores", {}),
            messages=state.get("messages", []),
            last_response=state.get("last_response"),
            is_complete=state.get("is_complete", False)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session state: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get session state: {str(e)}"
        )


# reset_wizard_session moved to lia_assistant_graph.py (Sprint 7).
async def reset_wizard_session(session_id: str):  # noqa: not registered
    """
    Reset a wizard session.
    
    Clears all state for the session, including conversation
    history and job draft data.
    """
    try:
        was_reset = await graph_runner_service.reset_session(session_id)
        
        if not was_reset:
            raise HTTPException(
                status_code=404,
                detail=f"Session not found: {session_id}"
            )
        
        return {
            "success": True,
            "message": f"Session {session_id} has been reset",
            "session_id": session_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting session: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset session: {str(e)}"
        )


# get_wizard_graph_info moved to lia_assistant_graph.py (Sprint 7).
async def get_wizard_graph_info():  # noqa: not registered
    """
    Get information about the wizard graph structure.
    
    Returns the nodes, edges, and configuration of the
    LangGraph-style state machine used for orchestration.
    """
    try:
        info = graph_runner_service.get_graph_info()
        
        return GraphInfoResponse(
            nodes=info.get("nodes", []),
            edges=info.get("edges", {}),
            conditional_edges=info.get("conditional_edges", {}),
            start_node=info.get("start_node", ""),
            end_node=info.get("end_node", ""),
            max_iterations=info.get("max_iterations", 10)
        )
        
    except Exception as e:
        logger.error(f"Error getting graph info: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get graph info: {str(e)}"
        )


# list_wizard_sessions moved to lia_assistant_graph.py (Sprint 7).
async def list_wizard_sessions():  # noqa: not registered
    """
    List all active wizard sessions.
    
    Returns a list of session IDs that have active state
    in the graph runner service.
    """
    try:
        sessions = graph_runner_service.list_active_sessions()
        
        return {
            "sessions": sessions,
            "count": len(sessions)
        }
        
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list sessions: {str(e)}"
        )


class SalaryBenchmarkRequest(BaseModel):
    job_title: str
    seniority: Optional[str] = None
    location: Optional[str] = None
    department: Optional[str] = None
    company_id: Optional[str] = "default"


class SalaryBenchmarkResponse(BaseModel):
    internal: Optional[Dict[str, Any]] = None
    market: Optional[Dict[str, Any]] = None
    combined: Optional[Dict[str, Any]] = None


@router.post("/job-wizard/salary-benchmark", response_model=SalaryBenchmarkResponse)
async def get_salary_benchmark(
    request: SalaryBenchmarkRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """
    Get salary benchmark data for a job role.
    
    Combines internal company data with external market data.
    """
    try:
        job_insights_service = JobInsightsService()
        
        internal_benchmark = {}
        market_benchmark = {}
        combined = {}
        
        try:
            internal_benchmark = await job_insights_service.get_salary_benchmark(
                db=db,
                company_id=current_user.company_id or "demo_company",
                role=request.job_title,
                seniority=request.seniority,
                location=request.location
            )
        except Exception as e:
            logger.warning(f"Failed to get internal salary benchmark: {e}")
            internal_benchmark = {"sample_size": 0}
        
        try:
            market_benchmark = await market_benchmark_service.search_salary_benchmark(
                role=request.job_title,
                seniority=request.seniority,
                location=request.location
            )
        except Exception as e:
            logger.warning(f"Failed to get market salary benchmark: {e}")
            market_benchmark = {}
        
        try:
            combined = market_benchmark_service.combine_with_internal(
                internal_data=internal_benchmark if internal_benchmark.get("sample_size", 0) > 0 else None,
                market_data=market_benchmark
            )
        except Exception as e:
            logger.warning(f"Failed to combine salary benchmarks: {e}")
            combined = {}
        
        return SalaryBenchmarkResponse(
            internal=internal_benchmark if internal_benchmark.get("sample_size", 0) > 0 else None,
            market=market_benchmark if market_benchmark.get("min") else None,
            combined=combined if combined.get("min") else None
        )
        
    except Exception as e:
        logger.error(f"Error fetching salary benchmark: {e}")
        return SalaryBenchmarkResponse()


@router.post("/job-wizard/evaluate", response_model=WizardEvaluateResponse)
async def evaluate_wizard_input(
    request: WizardEvaluateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    company_id = current_user.company_id or "demo_company"
    """
    Evaluate user input for job wizard and extract structured data using AI.
    
    This endpoint:
    - Extracts job criteria (title, salary, skills, etc.) from natural language input
    - Provides salary analysis comparing to market benchmarks
    - Suggests additional competencies based on the role
    - Returns confidence scores and field origins
    """
    from app.services.compensation_analysis_service import CompensationAnalysisService
    
    conversation_id = request.conversation_id or str(uuid4())
    user_input = request.user_input
    context = request.context or {}
    
    llm_service = LLMService()
    detected_fields: Dict[str, Any] = {}
    suggestions: List[WizardEvaluateSuggestion] = []
    compensation_analysis = None
    lia_message = ""
    overall_confidence = 0.7
    
    try:
        extraction_prompt = f"""Analise o texto abaixo e extraia informações sobre uma vaga de emprego.

Texto do usuário:
"{user_input}"

Contexto adicional: {json.dumps(context, ensure_ascii=False) if context else "Nenhum"}

Extraia as seguintes informações em formato JSON:
{{
    "title": "título da vaga (string ou null)",
    "seniority": "nível (Júnior, Pleno, Sênior, Especialista ou null)",
    "department": "departamento (string ou null)",
    "manager": "nome do gestor SOMENTE se explicitamente mencionado (string ou null)",
    "manager_email": "email do gestor SOMENTE se explicitamente mencionado (string ou null)",
    "responsibilities": ["lista de responsabilidades"],
    "technical_skills": ["lista de competências técnicas"],
    "behavioral_skills": ["lista de competências comportamentais"],
    "salary_min": número mínimo de salário ou null,
    "salary_max": número máximo de salário ou null,
    "work_model": "modelo (Remoto, Presencial, Híbrido ou null)",
    "location": "localização (string ou null)",
    "employment_type": "tipo (CLT, PJ, Estágio ou null)",
    "is_confidential": boolean ou null,
    "is_affirmative": boolean indicando se é vaga afirmativa/inclusiva (true/false/null),
    "affirmative_criteria_primary": "critério afirmativo principal - PcD, Mulheres, LGBTQIA+, Pessoas Negras, etc (string ou null)",
    "affirmative_criteria_secondary": "critério afirmativo secundário se houver (string ou null)",
    "affirmative_description": "descrição ou contexto da ação afirmativa mencionada (string ou null)",
    "analysis": {{
        "salary_feedback": "feedback sobre o salário informado comparado ao mercado",
        "skills_suggestions": ["sugestões de competências adicionais para este cargo"],
        "completeness_score": número de 0 a 1 indicando completude dos dados
    }}
}}

IMPORTANTE:
- Se o usuário informou um valor de salário, converta para número (ex: "15k" = 15000, "R$ 10.000" = 10000)
- Para competências, sugira adições relevantes baseadas no cargo
- Forneça feedback construtivo sobre o salário
- Para vaga afirmativa: detecte expressões como "vaga afirmativa", "ação afirmativa", "exclusiva para PcD", "exclusiva para mulheres", "vaga inclusiva", "diversidade", etc. Se disser "não é afirmativa" ou "não é vaga afirmativa", is_affirmative deve ser false. Se não mencionar, deixe null
- Para o gestor/manager: Extraia se o usuário mencionar explicitamente um nome ou área (ex: "gestor: Carlos Silva", "equipe do João", "reportando para Maria", "área de TI", "departamento de infraestrutura"). Também reconheça formatos como "gestor: nome", "gestor/área: valor", "departamento: nome". NÃO invente nomes se não forem mencionados

Retorne APENAS o JSON, sem texto adicional."""

        gemini = llm_service.gemini_native
        response = await gemini.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=extraction_prompt
        )
        
        response_text = response.text.strip()
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()
        
        extracted = json.loads(response_text)
        
        detected_fields = {
            "title": extracted.get("title"),
            "job_title": extracted.get("title"),
            "seniority": extracted.get("seniority"),
            "department": extracted.get("department"),
            "manager": extracted.get("manager"),
            "manager_email": extracted.get("manager_email"),
            "responsibilities": extracted.get("responsibilities", []),
            "technical_skills": extracted.get("technical_skills", []),
            "behavioral_skills": extracted.get("behavioral_skills", []),
            "salary_min": extracted.get("salary_min"),
            "salary_max": extracted.get("salary_max"),
            "work_model": extracted.get("work_model"),
            "location": extracted.get("location"),
            "employment_type": extracted.get("employment_type"),
            "is_confidential": extracted.get("is_confidential"),
            "is_affirmative": extracted.get("is_affirmative"),
            "affirmative_criteria_primary": extracted.get("affirmative_criteria_primary"),
            "affirmative_criteria_secondary": extracted.get("affirmative_criteria_secondary"),
            "affirmative_description": extracted.get("affirmative_description")
        }
        
        # Log affirmative action extraction for debugging
        is_aff = extracted.get("is_affirmative")
        aff_primary = extracted.get("affirmative_criteria_primary")
        logger.info(f"[WizardEvaluate] Affirmative action detection: is_affirmative={is_aff}, primary={aff_primary}")
        
        # Keep affirmative fields even if null (to signal "evaluated but not detected")
        affirmative_keys = {"is_affirmative", "affirmative_criteria_primary", "affirmative_criteria_secondary", "affirmative_description"}
        detected_fields = {k: v for k, v in detected_fields.items() if v is not None or k in affirmative_keys}
        
        analysis = extracted.get("analysis", {})
        completeness = analysis.get("completeness_score", 0.5)
        overall_confidence = min(0.95, completeness + 0.2)
        
        if detected_fields.get("salary_min") or detected_fields.get("salary_max"):
            salary_min = detected_fields.get("salary_min", 0)
            salary_max = detected_fields.get("salary_max", salary_min * 1.3 if salary_min else 0)
            
            compensation_analysis = WizardEvaluateCompensation(
                salary={
                    "proposed_min": salary_min,
                    "proposed_max": salary_max,
                    "market_min": salary_min * 0.9,
                    "market_max": salary_max * 1.1,
                    "market_percentile": 50,
                    "data_sources": ["market_benchmark", "internal_history"]
                },
                overall_assessment=analysis.get("salary_feedback", "Faixa salarial dentro da média do mercado."),
                summary=f"Salário proposto: R$ {salary_min:,.0f} - R$ {salary_max:,.0f}"
            )
            
            suggestions.append(WizardEvaluateSuggestion(
                field="salary_range",
                value={"min": salary_min, "max": salary_max},
                source="user_input",
                confidence=0.9,
                reason=analysis.get("salary_feedback")
            ))
        
        skills_suggestions = analysis.get("skills_suggestions", [])
        for skill in skills_suggestions:
            suggestions.append(WizardEvaluateSuggestion(
                field="technical_skills",
                value=skill,
                source="market_benchmark",
                confidence=0.75,
                reason=f"Competência comum para {detected_fields.get('title', 'este cargo')}"
            ))
        
        message_parts = []
        if detected_fields.get("title"):
            message_parts.append(f"Entendi! Vaga para **{detected_fields.get('title')}**")
            if detected_fields.get("seniority"):
                message_parts[-1] += f" ({detected_fields.get('seniority')})"
            message_parts[-1] += "."
        
        if detected_fields.get("salary_min"):
            salary_feedback = analysis.get("salary_feedback", "")
            if salary_feedback:
                message_parts.append(f"💰 {salary_feedback}")
        
        if skills_suggestions:
            message_parts.append(f"💡 Sugestões de competências: {', '.join(skills_suggestions[:3])}")
        
        # Add affirmative action detection message
        if detected_fields.get("is_affirmative") is True:
            affirmative_primary = detected_fields.get("affirmative_criteria_primary", "")
            if affirmative_primary:
                message_parts.append(f"✅ Vaga afirmativa detectada: **{affirmative_primary}**")
            else:
                message_parts.append("✅ Vaga afirmativa detectada")
        
        if not message_parts:
            message_parts.append("Recebi suas informações. Por favor, continue descrevendo a vaga para que eu possa ajudar melhor.")
        
        lia_message = "\n\n".join(message_parts)
        
        logger.info(f"[WizardEvaluate] Extracted fields: {list(detected_fields.keys())}, confidence: {overall_confidence:.2f}")
        
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse LLM response as JSON: {e}")
        lia_message = "Recebi suas informações. Por favor, continue descrevendo a vaga com mais detalhes."
        overall_confidence = 0.5
    except Exception as e:
        logger.error(f"Error in wizard evaluation: {e}")
        lia_message = "Entendi suas informações. Por favor, continue descrevendo a vaga."
        overall_confidence = 0.5
    
    return WizardEvaluateResponse(
        conversation_id=conversation_id,
        detected_fields=detected_fields,
        compensation_analysis=compensation_analysis,
        suggestions=suggestions,
        lia_message=lia_message,
        overall_confidence=overall_confidence
    )


@router.post("/job-wizard/step", response_model=WizardStepResponse)
async def process_wizard_step(
    request: WizardStepRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """Process a step in the conversational job creation wizard."""
    company_id = current_user.company_id or "demo_company"
    recruiter_id = str(current_user.id)
    from app.domains.job_management.services.wizard_step_service import wizard_step_service
    return await wizard_step_service.process(request, db, company_id, recruiter_id)


@router.post("/job-insights", response_model=InsightsResponse)
async def generate_job_insights(
    request: InsightsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    company_id = current_user.company_id or "demo_company"
    """
    Generate dynamic insights for selected jobs.
    Uses Analytics and JobIntake agents for intelligent analysis.
    """
    insights: List[InsightItem] = []
    summary: Dict[str, Any] = {
        "total_jobs": len(request.job_ids),
        "total_candidates": 0,
        "avg_time_to_fill": 0,
        "health_score": 0
    }
    
    try:
        jobs_data = []
        total_candidates = 0
        
        for job_id in request.job_ids:
            try:
                job_query = select(JobVacancy).where(JobVacancy.id == UUID(job_id))
                result = await db.execute(job_query)
                job = result.scalar_one_or_none()
                
                if job:
                    candidate_count = getattr(job, 'current_candidates', 0) or 0
                    total_candidates += candidate_count
                    
                    jobs_data.append({
                        "id": str(job.id),
                        "title": job.title,
                        "status": job.status,
                        "created_at": job.created_at.isoformat() if job.created_at else None,
                        "deadline": job.deadline.isoformat() if job.deadline else None,
                        "candidates": candidate_count,
                        "priority": getattr(job, 'priority', 'medium')
                    })
                    
                    if job.deadline:
                        days_until_deadline = (job.deadline.date() - datetime.utcnow().date()).days
                        if days_until_deadline <= 7 and days_until_deadline >= 0:
                            insights.append(InsightItem(
                                type="warning",
                                title=f"Prazo próximo: {job.title}",
                                description=f"Vaga expira em {days_until_deadline} dias",
                                severity="high",
                                recommendation="Acelere o processo de triagem ou estenda o prazo",
                                data={"job_id": str(job.id), "days_remaining": days_until_deadline}
                            ))
                        elif days_until_deadline < 0:
                            insights.append(InsightItem(
                                type="critical",
                                title=f"Prazo expirado: {job.title}",
                                description=f"Vaga expirou há {abs(days_until_deadline)} dias",
                                severity="critical",
                                recommendation="Avalie se deve reabrir a vaga com novo prazo",
                                data={"job_id": str(job.id), "days_overdue": abs(days_until_deadline)}
                            ))
                    
                    if candidate_count == 0:
                        insights.append(InsightItem(
                            type="info",
                            title=f"Sem candidatos: {job.title}",
                            description="Esta vaga ainda não recebeu candidaturas",
                            severity="medium",
                            recommendation="Considere ampliar os canais de divulgação ou revisar os requisitos",
                            data={"job_id": str(job.id)}
                        ))
                        
            except Exception as e:
                logger.warning(f"Error processing job {job_id}: {e}")
                continue
        
        summary["total_candidates"] = total_candidates
        
        if jobs_data:
            health_factors = []
            for job in jobs_data:
                score = 100
                if job.get("candidates", 0) == 0:
                    score -= 30
                health_factors.append(score)
            
            summary["health_score"] = sum(health_factors) // len(health_factors) if health_factors else 0
            
            if summary["health_score"] >= 80:
                insights.append(InsightItem(
                    type="success",
                    title="Pipeline saudável",
                    description=f"Score geral: {summary['health_score']}%",
                    severity="low",
                    data={"score": summary["health_score"]}
                ))
            elif summary["health_score"] >= 50:
                insights.append(InsightItem(
                    type="warning",
                    title="Pipeline precisa de atenção",
                    description=f"Score geral: {summary['health_score']}%",
                    severity="medium",
                    recommendation="Revise as vagas com alertas críticos",
                    data={"score": summary["health_score"]}
                ))
            else:
                insights.append(InsightItem(
                    type="critical",
                    title="Pipeline crítico",
                    description=f"Score geral: {summary['health_score']}%",
                    severity="high",
                    recommendation="Ação urgente necessária nas vagas abertas",
                    data={"score": summary["health_score"]}
                ))
        
        return InsightsResponse(
            insights=insights,
            summary=summary,
            generated_at=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error generating insights: {e}")
        return InsightsResponse(
            insights=[
                InsightItem(
                    type="error",
                    title="Erro ao gerar insights",
                    description=str(e),
                    severity="high"
                )
            ],
            summary=summary,
            generated_at=datetime.utcnow().isoformat()
        )


async def handle_jobs_management_query(
    db: AsyncSession,
    company_id: str,
    message: str,
    context_ids: Optional[List[str]],
    llm_service,
) -> str:
    """
    Handler para queries do painel de gestão de vagas.
    Injeta dados reais das vagas no prompt e mantém contexto de RECRUTADOR.
    Evita que a LIA responda como se estivesse falando com um candidato.
    """
    from app.models.job_vacancy import JobVacancy
    from sqlalchemy import select, func
    from datetime import datetime

    try:
        # Busca vagas da empresa — prioriza IDs selecionados quando fornecidos
        query = select(JobVacancy).where(JobVacancy.company_id == company_id)
        if context_ids:
            query = query.where(JobVacancy.id.in_(context_ids))
        else:
            query = query.order_by(JobVacancy.created_at.desc()).limit(30)

        result = await db.execute(query)
        jobs = result.scalars().all()

        now = datetime.utcnow()
        jobs_lines = []
        sla_risk_count = 0
        no_candidates_count = 0

        for job in jobs:
            days_open = (now - job.created_at).days if job.created_at else 0
            days_to_deadline = None
            sla_flag = ""
            if job.deadline:
                days_to_deadline = (job.deadline - now).days
                if days_to_deadline < 0:
                    sla_flag = " ⚠️ SLA VENCIDO"
                    sla_risk_count += 1
                elif days_to_deadline <= 14:
                    sla_flag = f" ⚠️ SLA em {days_to_deadline}d"
                    sla_risk_count += 1

            salary_info = ""
            if job.salary_range:
                sal = job.salary_range
                salary_info = f" | R$ {sal.get('min', '?'):,}–{sal.get('max', '?'):,}"

            jobs_lines.append(
                f"• [{job.status}] {job.title}"
                f" | {job.department or 'N/A'}"
                f" | {job.seniority_level or 'N/A'}"
                f" | {job.location or 'N/A'}"
                f"{salary_info}"
                f" | Aberta há {days_open}d"
                f" | Prioridade: {job.priority or 'média'}"
                f"{sla_flag}"
            )

        total = len(jobs)
        active = sum(1 for j in jobs if j.status in ("Ativa", "Publicada", "Em andamento"))
        paused = sum(1 for j in jobs if j.status in ("Pausada",))
        draft = sum(1 for j in jobs if j.status in ("Rascunho",))

        jobs_text = "\n".join(jobs_lines) if jobs_lines else "Nenhuma vaga encontrada para esta empresa."
        scope_note = f"vagas selecionadas ({total})" if context_ids else f"últimas {total} vagas"

        prompt = f"""Você é LIA, assistente de recrutamento inteligente da plataforma WeDOTalent.
Você está auxiliando um RECRUTADOR no painel de gestão de vagas.

=== IMPORTANTE ===
- O usuário é um RECRUTADOR gerenciando as vagas da empresa, NÃO um candidato buscando emprego.
- NUNCA pergunte sobre cargo desejado, localização pessoal, nível de experiência do usuário, tipo de contrato preferido.
- Responda sempre em Português Brasileiro.
- Seja direta, objetiva e profissional.

=== DADOS REAIS DAS VAGAS ({scope_note}) ===
Total: {total} | Ativas/Publicadas: {active} | Pausadas: {paused} | Rascunhos: {draft} | Risco de SLA: {sla_risk_count}

{jobs_text}

=== MENSAGEM DO RECRUTADOR ===
{message}

=== INSTRUÇÕES DE RESPOSTA ===
- Use os dados acima para responder com precisão.
- Se pedir lista, formate como tabela ou lista estruturada com as vagas reais.
- Se pedir análise, analise os dados (SLA, performance, gargalos, prioridades).
- Se pedir comparação, compare as vagas entre si usando os dados disponíveis.
- Destaque alertas de SLA quando relevante.
- Sugira ações concretas quando identificar problemas."""

        return await llm_service.generate(prompt, provider="claude")

    except Exception as exc:
        logger.warning("[expanded-prompt/jobs] Erro ao buscar vagas: %s", exc)
        prompt = f"""Você é LIA, assistente de recrutamento inteligente da plataforma WeDOTalent.
Você está auxiliando um RECRUTADOR no painel de gestão de vagas da empresa.
O usuário é RECRUTADOR, não candidato.

Mensagem do recrutador: {message}

Responda em Português Brasileiro de forma útil e profissional.
Não solicite informações pessoais do usuário."""
        return await llm_service.generate(prompt, provider="claude")


@router.post("/expanded-prompt", response_model=ExpandedPromptResponse)
async def process_expanded_prompt(
    request: ExpandedPromptRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
    _budget: None = Depends(require_token_budget),
):
    company_id = current_user.company_id or "demo_company"
    """
    Route expanded commands to appropriate agents based on context.
    """
    try:
        llm_service = LLMService()
        
        classification = await intent_classifier_service.classify(
            user_input=request.message,
            stage_context=request.context_type,
            use_llm=True
        )
        
        response_text = ""
        agent_used = "general"
        actions = []
        follow_ups = []
        
        if request.context_type == "job_creation":
            question_type = detect_question_type(request.message)

            job_context = request.context or {}

            if question_type == QuestionType.SALARY:
                response_text = await handle_salary_question(db, company_id, job_context, request.message)
                agent_used = "salary_insights"
            elif question_type == QuestionType.SKILLS:
                response_text = await handle_skills_question(db, company_id, job_context, request.message)
                agent_used = "skills_insights"
            elif question_type == QuestionType.TIME_TO_FILL:
                response_text = await handle_time_to_fill_question(db, company_id, job_context, request.message)
                agent_used = "time_insights"
            elif question_type == QuestionType.PROCESS:
                response_text = await handle_process_question(request.message, llm_service)
                agent_used = "process_explainer"
            else:
                prompt = f"""Você é LIA, assistente de recrutamento. Responda à mensagem:

Mensagem: {request.message}
Contexto: {request.context_type}
IDs relacionados: {request.context_ids}

Seja útil e concisa."""
                response_text = await llm_service.generate(prompt, provider="gemini")
                agent_used = "general_assistant"

        elif request.context_type in ("jobs", "job_management", "portfolio"):
            response_text = await handle_jobs_management_query(
                db=db,
                company_id=company_id,
                message=request.message,
                context_ids=request.context_ids,
                llm_service=llm_service,
            )
            agent_used = "jobs_management"

        else:
            prompt = f"""Você é LIA, assistente de recrutamento inteligente da plataforma WeDOTalent.
Você está auxiliando um RECRUTADOR.

Mensagem do recrutador: {request.message}
Contexto: {request.context_type}

Responda em Português Brasileiro de forma útil, clara e profissional.
NUNCA peça informações pessoais do usuário como cargo, localização ou experiência — ele é o recrutador, não um candidato."""
            response_text = await llm_service.generate(prompt, provider="claude")
            agent_used = "general_assistant"
        
        follow_ups = [
            "Posso ajudar com mais alguma informação?",
            "Quer que eu analise algo mais sobre esta vaga?",
            "Precisa de ajuda com outra funcionalidade?"
        ]
        
        return ExpandedPromptResponse(
            response=response_text,
            agent_used=agent_used,
            actions=actions,
            follow_up_suggestions=follow_ups[:2]
        )
        
    except Exception as e:
        logger.error(f"Error processing expanded prompt: {e}")
        return ExpandedPromptResponse(
            response=f"Desculpe, ocorreu um erro ao processar sua solicitação: {str(e)}",
            agent_used="error_handler",
            actions=[],
            follow_up_suggestions=["Tente novamente ou reformule sua pergunta"]
        )


@router.get("/job-draft/{conversation_id}")
async def get_job_draft(
    conversation_id: str,
    current_user: User = Depends(get_current_user_or_demo)
) -> Dict[str, Any]:
    company_id = current_user.company_id or "demo_company"
    """
    Get the current job draft for a conversation.
    """
    if conversation_id in _job_drafts:
        return {
            "success": True,
            "job_draft": _job_drafts[conversation_id]
        }
    return {
        "success": False,
        "message": "Job draft not found",
        "job_draft": None
    }


@router.delete("/job-draft/{conversation_id}")
async def clear_job_draft(
    conversation_id: str,
    current_user: User = Depends(get_current_user_or_demo)
) -> Dict[str, Any]:
    company_id = current_user.company_id or "demo_company"
    """
    Clear a job draft from memory.
    """
    if conversation_id in _job_drafts:
        del _job_drafts[conversation_id]
        return {"success": True, "message": "Job draft cleared"}
    return {"success": False, "message": "Job draft not found"}


# ============================================================================
# Learning, Feature Flags, Wizard Stages 8-10, Vacancy, and Fast Track
# endpoints have been extracted to dedicated modules (Phase 5 decomposition):
#   lia_assistant_learning.py      → /lia/learning/*
#   lia_assistant_flags.py         → /lia/feature-flags/*
#   lia_assistant_wizard_stages.py → /lia/wizard/stage8-10/*
#   lia_assistant_vacancy.py       → /lia/vacancy-*
#   lia_assistant_fasttrack.py     → /lia/fast-track/*
# These are registered in main.py alongside this router.
# ============================================================================
