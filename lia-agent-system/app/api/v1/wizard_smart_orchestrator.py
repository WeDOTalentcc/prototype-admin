"""
Wizard Smart Orchestrator API - LLM-powered Job Wizard Graph Execution.

This endpoint executes the JobWizardGraph with LLM processing,
enabling intelligent intent classification, field extraction,
tool routing, and response generation.
"""
import logging
from typing import Any

from fastapi import APIRouter, Depends
from lia_agents_core.state_machine import (
    JobWizardState,
    WizardStage,
    normalize_fields_for_frontend,
)
from pydantic import BaseModel, Field

from app.auth.dependencies import get_current_user_or_demo, get_user_company_id
from app.auth.models import User
from app.core.database import AsyncSessionLocal
from app.domains.job_management.agents.job_wizard_graph import job_wizard_graph
from app.domains.job_management.services.job_vacancy_service import job_vacancy_service
from app.shared.tenant_session import create_session_id

router = APIRouter()
logger = logging.getLogger(__name__)


def format_enrichment_as_conversational_message(enrichment_result: dict[str, Any], title: str) -> str:
    """
    Format enrichment suggestions as a rich conversational message for the chat.
    
    This follows the conversational philosophy where LIA presents suggestions
    in the chat prompt, allowing natural discussion and feedback.
    """
    if not enrichment_result.get("success"):
        return ""
    
    sections = enrichment_result.get("sections", [])
    compensation = enrichment_result.get("compensation")
    wsi_score = enrichment_result.get("wsiQualityScore", 0)
    total_suggestions = enrichment_result.get("totalSuggestions", 0)
    
    if total_suggestions == 0:
        return f"""✨ **Análise de Enriquecimento Concluída**

Analisei os dados da vaga **{title}** contra benchmarks de mercado, histórico da empresa e catálogos de skills.

A descrição está bem completa! O score de qualidade WSI é **{wsi_score}%**, o que significa que as perguntas de triagem terão boa qualidade.

Quer que eu avance para definir a remuneração, ou prefere revisar algum ponto?"""
    
    # Build conversational message with suggestions
    parts = []
    parts.append(f"""✨ **Análise de Enriquecimento Concluída**

Analisei os dados da vaga **{title}** contra 5 fontes de dados:
• **Benchmark de Mercado** - práticas do setor para este cargo
• **Histórico da Empresa** - padrões das suas vagas anteriores  
• **Catálogo de Skills** - competências validadas para a função
• **Configurações da Empresa** - políticas e preferências internas
• **Integração ATS** - dados de recrutamentos passados

📊 **Score de Qualidade WSI: {wsi_score}%** | {total_suggestions} sugestões para melhorar
""")
    
    # Format each section with suggestions
    section_icons = {
        "responsibilities": "📋",
        "technical_skills": "💻", 
        "behavioral_competencies": "🧠",
        "compensation": "💰"
    }
    
    for section in sections:
        section_name = section.get("sectionName", "")
        section_title = section.get("sectionTitle", section_name)
        suggestions = section.get("suggestions", [])
        detected_items = section.get("detectedItems", [])
        
        if not suggestions:
            continue
            
        icon = section_icons.get(section_name, "📌")
        
        parts.append(f"\n---\n{icon} **{section_title}**")
        
        if detected_items:
            items_preview = ", ".join(detected_items[:3])
            if len(detected_items) > 3:
                items_preview += f" +{len(detected_items) - 3}"
            parts.append(f"*Já detectados:* {items_preview}")
        
        parts.append("\n**Sugestões para adicionar:**")
        
        for i, suggestion in enumerate(suggestions[:5], 1):  # Limit to top 5 per section
            value = suggestion.get("value", "")
            source = suggestion.get("source", "")
            justification = suggestion.get("justification", "")
            impact = suggestion.get("impactLevel", "medium")
            
            source_labels = {
                "market_benchmark": "Mercado",
                "company_history": "Histórico",
                "skills_catalog": "Catálogo",
                "company_config": "Empresa",
                "ats_integration": "ATS"
            }
            source_label = source_labels.get(source, source)
            
            impact_emoji = {"high": "🔥", "medium": "⭐", "low": "💡"}.get(impact, "💡")
            
            parts.append(f"{i}. **{value}** {impact_emoji}")
            parts.append(f"   ↳ *{justification}* `[{source_label}]`")
    
    # Add compensation analysis if available
    if compensation and compensation.get("marketRange"):
        current_range = compensation.get("currentRange", {})
        market_range = compensation.get("marketRange", {})
        market_position = compensation.get("marketPosition", "competitive")
        
        position_text = {
            "below": "⚠️ **Abaixo do mercado** - pode dificultar atrair talentos",
            "competitive": "✅ **Competitivo** - alinhado com o mercado",
            "above": "🎯 **Acima do mercado** - atrativo para top talentos"
        }.get(market_position, "")
        
        parts.append("\n---\n💰 **Análise de Remuneração**")
        if current_range.get("min") and current_range.get("max"):
            parts.append(f"*Sua proposta:* R$ {current_range['min']:,.0f} - R$ {current_range['max']:,.0f}")
        if market_range.get("min") and market_range.get("max"):
            parts.append(f"*Benchmark de mercado:* R$ {market_range['min']:,.0f} - R$ {market_range['max']:,.0f}")
        if position_text:
            parts.append(position_text)
    
    # Add closing conversational prompt
    parts.append("""
---

💬 **O que você acha dessas sugestões?**

Você pode responder naturalmente, por exemplo:
• *"Aceito todas as sugestões"*
• *"Adiciona apenas Python e Docker"*  
• *"Não preciso de liderança, remove essa"*
• *"Vamos avançar para remuneração"*

Ou me diga se quer discutir alguma sugestão específica!""")
    
    return "\n".join(parts)

FRONTEND_TO_BACKEND_STAGE: dict[str, str] = {
    "input-evaluation": WizardStage.TITLE_DEPARTMENT.value,
    "title-department": WizardStage.TITLE_DEPARTMENT.value,
    "job-summary": WizardStage.JOB_SUMMARY.value,
    "jd-enrichment": WizardStage.JOB_SUMMARY.value,
    "job_summary": WizardStage.JOB_SUMMARY.value,
    "salary": WizardStage.SALARY.value,
    "competencies": WizardStage.COMPETENCIES.value,
    "wsi-questions": WizardStage.SCREENING.value,
    "screening": WizardStage.SCREENING.value,
    "review-publish": WizardStage.REVIEW.value,
    "review": WizardStage.REVIEW.value,
    "complete": WizardStage.COMPLETE.value,
    "initial": WizardStage.INITIAL.value,
}

BACKEND_TO_FRONTEND_STAGE: dict[str, str] = {
    WizardStage.INITIAL.value: "input-evaluation",
    WizardStage.TITLE_DEPARTMENT.value: "input-evaluation",
    WizardStage.JOB_SUMMARY.value: "jd-enrichment",
    WizardStage.SALARY.value: "salary",
    WizardStage.COMPETENCIES.value: "competencies",
    WizardStage.SCREENING.value: "wsi-questions",
    WizardStage.REVIEW.value: "review-publish",
    WizardStage.COMPLETE.value: "complete",
}


class SmartOrchestrateRequest(BaseModel):
    """Request for smart orchestration using LLM-powered graph."""
    message: str = Field(..., description="User message to process")
    current_stage: str = Field(
        default="input-evaluation",
        description="Current wizard stage (frontend format)"
    )
    collected_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Data already collected in the wizard"
    )
    conversation_history: list[dict[str, str]] = Field(
        default_factory=list,
        description="Previous conversation messages"
    )
    conversation_id: str | None = Field(
        None,
        description="Conversation ID for context continuity"
    )
    company_id: str | None = Field(None, description="Company ID override")
    user_id: str | None = Field(None, description="User ID override")


class SmartOrchestrateResponse(BaseModel):
    """Response from smart orchestration."""
    success: bool = Field(..., description="Whether processing succeeded")
    lia_message: str = Field(
        default="",
        description="LIA's response generated by LLM"
    )
    detected_criteria: dict[str, Any] = Field(
        default_factory=dict,
        description="Extracted fields from user message"
    )
    next_stage: str | None = Field(
        None,
        description="Next stage if transition occurred (frontend format)"
    )
    auto_transition: bool = Field(
        default=False,
        description="Whether to auto-transition to next stage"
    )
    tool_results: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Results from executed tools"
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Overall confidence of the response"
    )
    reasoning_steps: list[str] = Field(
        default_factory=list,
        description="Reasoning steps for debugging"
    )
    intent: str | None = Field(
        None,
        description="Detected user intent"
    )
    error: str | None = Field(
        None,
        description="Error message if processing failed"
    )
    awaiting_confirmation: bool = Field(
        default=False,
        description="Whether the wizard is blocked waiting for user confirmation"
    )
    job_vacancy_id: str | None = Field(
        None,
        description="ID of created job vacancy when wizard completes"
    )
    job_published: bool = Field(
        default=False,
        description="Whether the job was successfully published to database"
    )
    conversation_id: str | None = Field(
        None,
        description="Session/conversation ID — send back in next request to maintain multi-turn memory"
    )


def map_frontend_to_backend_stage(frontend_stage: str) -> str:
    """Map frontend stage names to backend WizardStage values."""
    return FRONTEND_TO_BACKEND_STAGE.get(
        frontend_stage.lower(),
        WizardStage.INITIAL.value
    )


def map_backend_to_frontend_stage(backend_stage: str) -> str:
    """Map backend WizardStage values to frontend stage names."""
    return BACKEND_TO_FRONTEND_STAGE.get(
        backend_stage,
        "input-evaluation"
    )


def build_messages_from_history(
    conversation_history: list[dict[str, str]],
    current_message: str
) -> list[dict[str, str]]:
    """Build messages list from conversation history plus current message."""
    messages = []
    for msg in conversation_history[-10:]:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": current_message})
    return messages


def calculate_overall_confidence(state: JobWizardState) -> float:
    """Calculate overall confidence from state confidence scores."""
    scores = state.get("confidence_scores", {})
    if not scores:
        return 0.5
    return sum(scores.values()) / len(scores)


async def finalize_job_vacancy_from_wizard(
    job_draft: dict[str, Any],
    session_id: str,
    company_id: str,
    user_id: str,
) -> str | None:
    """
    Create job vacancy in database when wizard completes.
    
    Includes idempotency check to prevent duplicate job creation.
    Handles FK constraint by validating conversation exists first.
    
    Returns:
        job_vacancy_id if successful, None otherwise
    """
    try:
        if not job_draft.get("title") and not job_draft.get("job_title"):
            logger.warning("Cannot finalize job: no title provided")
            return None
        
        async with AsyncSessionLocal() as db:
            try:
                from uuid import UUID

                from sqlalchemy import select

                from app.models.conversation import Conversation
                from app.models.job_vacancy import JobVacancy
                
                conv_uuid = None
                valid_conversation_id = None
                
                try:
                    conv_uuid = UUID(session_id)
                except (ValueError, TypeError):
                    logger.warning(f"Session ID '{session_id}' is not a valid UUID, will create job without conversation link")
                
                from sqlalchemy import text
                idempotency_result = await db.execute(
                    text("SELECT id FROM job_vacancies WHERE additional_data->>'wizard_session_id' = :session_id LIMIT 1"),
                    {"session_id": session_id}
                )
                existing_by_session = idempotency_result.scalar_one_or_none()
                if existing_by_session:
                    logger.info(f"⚠️ Job already exists for wizard session {session_id}: {existing_by_session}")
                    return str(existing_by_session)
                
                if conv_uuid:
                    existing_job = await db.execute(
                        select(JobVacancy).where(JobVacancy.conversation_id == conv_uuid)
                    )
                    existing = existing_job.scalar_one_or_none()
                    
                    if existing:
                        logger.info(f"⚠️ Job already exists for conversation {session_id}: {existing.id}")
                        return str(existing.id)
                    
                    existing_conv = await db.execute(
                        select(Conversation).where(Conversation.id == conv_uuid)
                    )
                    if existing_conv.scalar_one_or_none():
                        valid_conversation_id = session_id
                    else:
                        logger.info(f"Conversation {session_id} not found in DB, creating job without FK link")
                
                job_vacancy = await job_vacancy_service.create_from_wizard_draft(
                    draft=job_draft,
                    conversation_id=valid_conversation_id or session_id,
                    created_by=user_id,
                    company_id=company_id,
                    db=db,
                    use_session_for_idempotency=(valid_conversation_id is None),
                )

                await db.commit()
                await db.refresh(job_vacancy)
                job_id = str(job_vacancy.id)
                logger.info(f"✅ Job vacancy created from wizard: {job_id}")

                # Persist WSI screening questions configured during the wizard.
                # They live in job_draft["screening_questions"] (backend key) or
                # "wsi_questions" (frontend alias mapped by normalize_fields_for_frontend).
                screening_questions = (
                    job_draft.get("screening_questions")
                    or job_draft.get("wsi_questions")
                    or []
                )
                if screening_questions:
                    try:
                        from app.domains.cv_screening.services.screening_question_set_service import (
                            ScreeningQuestionSetService,
                        )
                        question_set_service = ScreeningQuestionSetService()
                        await question_set_service.save_question_set(
                            db=db,
                            job_vacancy_id=job_id,
                            questions=screening_questions,
                            source="wizard",
                            created_by=user_id,
                            company_id=company_id,
                        )
                        await db.commit()
                        logger.info(
                            f"✅ Saved {len(screening_questions)} WSI questions for job {job_id}"
                        )
                    except Exception as q_error:
                        logger.warning(
                            f"⚠️ Failed to save WSI questions for job {job_id}: {q_error}"
                        )

                return job_id
                
            except Exception as db_error:
                await db.rollback()
                logger.error(f"❌ Database error creating job: {db_error}")
                raise db_error
                
    except Exception as e:
        logger.error(f"❌ Failed to finalize job vacancy: {e}", exc_info=True)
        return None


@router.post("/smart-orchestrate", response_model=SmartOrchestrateResponse)
async def smart_orchestrate(
    request: SmartOrchestrateRequest,
    current_user: User = Depends(get_current_user_or_demo),
) -> SmartOrchestrateResponse:
    """
    Execute the JobWizardGraph with LLM processing.
    
    This endpoint runs the complete LangGraph-style state machine,
    including:
    1. Intent classification (what does the user want?)
    2. Field extraction (what data is being provided?)
    3. Tool routing (should we call any tools?)
    4. Tool execution (execute matched tools)
    5. Response generation (generate LIA's response)
    6. Stage transition (should we move to next stage?)
    
    Returns:
        SmartOrchestrateResponse with LIA's message and extracted data
    """
    session_id = request.conversation_id or create_session_id(current_user.company_id)
    company_id = request.company_id or get_user_company_id(current_user)
    user_id = request.user_id or (str(current_user.id) if current_user.id is not None else "anonymous")
    
    logger.info(
        f"Smart orchestrate request: stage={request.current_stage}, "
        f"message_len={len(request.message)}, session={session_id}"
    )
    
    try:
        backend_stage = map_frontend_to_backend_stage(request.current_stage)
        
        messages = build_messages_from_history(
            request.conversation_history,
            request.message
        )
        
        initial_state: JobWizardState = {
            "messages": messages,
            "current_stage": backend_stage,
            "job_draft": request.collected_data.copy(),
            "confidence_scores": {},
            "reasoning_steps": [],
            "next_action": None,
            "intent": None,
            "tool_calls": [],
            "tool_results": [],
            "session_id": session_id,
            "company_id": company_id,
            "user_id": user_id,
            "should_continue": False,
            "needs_clarification": False,
            "error": None,
            "response_text": None,
            "extracted_fields": {},
            "current_node": "start",
            "auto_transition": False,
            "awaiting_confirmation": False,
        }
        
        logger.debug(f"Initial state created for session {session_id}")
        
        final_state = await job_wizard_graph.invoke(initial_state)
        
        detected_criteria = normalize_fields_for_frontend(final_state.get("extracted_fields", {}))
        for key, value in final_state.get("job_draft", {}).items():
            if key not in request.collected_data or request.collected_data.get(key) != value:
                if value is not None:
                    detected_criteria[key] = value
        
        current_backend_stage = final_state.get("current_stage", backend_stage)
        next_stage = None
        auto_transition = False
        
        if current_backend_stage != backend_stage:
            next_stage = map_backend_to_frontend_stage(current_backend_stage)
            auto_transition = True
        elif final_state.get("should_continue"):
            auto_transition = True
        
        # generate_enriched_jd is now called autonomously by the WizardReActAgent
        # when the stage is jd-enrichment and title is available (see wizard_system_prompt.py).
        # The endpoint no longer bypasses agent autonomy by calling it directly.
        tool_results = final_state.get("tool_results", [])
        
        awaiting_confirmation = final_state.get("awaiting_confirmation", False)
        
        logger.debug(
            f"Stage mapping validation: frontend='{request.current_stage}' -> "
            f"backend='{backend_stage}' -> current='{current_backend_stage}' -> "
            f"frontend_next='{next_stage}', awaiting_confirmation={awaiting_confirmation}"
        )
        
        job_vacancy_id = None
        job_published = False

        # Auto-save draft progress after each successful agent turn (not only at completion).
        # Persists collected_data + detected_criteria into Redis so the session can be
        # recovered if the user refreshes mid-wizard.
        if detected_criteria and current_backend_stage != WizardStage.COMPLETE.value:
            try:
                import json

                from app.core.config import settings
                merged_progress = {**request.collected_data, **detected_criteria}
                if merged_progress.get("title") or merged_progress.get("job_title"):
                    redis_key = f"wizard_draft:{session_id}"
                    async with __import__("redis.asyncio", fromlist=["Redis"]).Redis.from_url(
                        settings.REDIS_URL, decode_responses=True
                    ) as redis_client:
                        await redis_client.setex(redis_key, 86400, json.dumps(merged_progress))
                    logger.debug(f"[wizard] Draft auto-saved to Redis: key={redis_key}")
            except Exception as draft_err:
                logger.debug(f"[wizard] Draft auto-save skipped: {draft_err}")

        if current_backend_stage == WizardStage.COMPLETE.value:
            merged_draft = {**request.collected_data, **detected_criteria}
            
            job_vacancy_id = await finalize_job_vacancy_from_wizard(
                job_draft=merged_draft,
                session_id=session_id,
                company_id=company_id,
                user_id=user_id,
            )
            
            if job_vacancy_id:
                job_published = True
                logger.info(f"🎉 Wizard completed! Job vacancy created: {job_vacancy_id}")
            else:
                logger.warning("⚠️ Wizard completed but job vacancy creation failed")
        
        response = SmartOrchestrateResponse(
            success=final_state.get("error") is None,
            lia_message=final_state.get("response_text") or "",
            detected_criteria=detected_criteria,
            next_stage=next_stage,
            auto_transition=auto_transition and not awaiting_confirmation,
            tool_results=final_state.get("tool_results", []),
            confidence=calculate_overall_confidence(final_state),
            reasoning_steps=final_state.get("reasoning_steps", []),
            intent=final_state.get("intent"),
            error=final_state.get("error"),
            awaiting_confirmation=awaiting_confirmation,
            job_vacancy_id=job_vacancy_id,
            job_published=job_published,
            conversation_id=session_id,
        )
        
        logger.info(
            f"Smart orchestrate complete: session={session_id}, "
            f"intent={response.intent}, extracted_fields={len(detected_criteria)}, "
            f"confidence={response.confidence:.2f}"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Smart orchestrate error: {e}", exc_info=True)
        return SmartOrchestrateResponse(
            success=False,
            lia_message="Desculpe, ocorreu um erro ao processar sua mensagem. Por favor, tente novamente.",
            detected_criteria={},
            next_stage=None,
            auto_transition=False,
            tool_results=[],
            confidence=0.0,
            reasoning_steps=[f"Error: {str(e)}"],
            intent=None,
            error=str(e),
            awaiting_confirmation=False,
            job_vacancy_id=None,
            job_published=False,
            conversation_id=session_id if 'session_id' in locals() else None,
        )


@router.post("/react-orchestrate", response_model=SmartOrchestrateResponse)
async def react_orchestrate(
    request: SmartOrchestrateRequest,
    current_user: User = Depends(get_current_user_or_demo),
) -> SmartOrchestrateResponse:
    """
    Execute the WizardReActAgent for autonomous job creation.

    This endpoint uses the ReAct loop (Reason-Act-Observe-Decide)
    instead of the linear pipeline. The agent autonomously decides
    which tools to call and when to respond.

    Feature flag: USE_REACT_AGENTS (defaults to False).
    """
    import os
    use_react = os.environ.get("USE_REACT_AGENTS", "false").lower() == "true"
    if not use_react:
        return await smart_orchestrate(request, current_user)

    session_id = request.conversation_id or create_session_id(current_user.company_id)
    company_id = request.company_id or get_user_company_id(current_user)
    user_id = request.user_id or (
        str(current_user.id) if current_user.id is not None else "anonymous"
    )

    logger.info(
        f"ReAct orchestrate: stage={request.current_stage}, "
        f"message_len={len(request.message)}, session={session_id}"
    )

    try:
        from lia_agents_core.agent_interface import AgentInput

        from app.domains.job_management.agents.wizard_react_agent import (
            WizardReActAgent,
        )

        normalized_stage = FRONTEND_TO_BACKEND_STAGE.get(
            request.current_stage.lower(),
            request.current_stage,
        )
        frontend_stage = BACKEND_TO_FRONTEND_STAGE.get(
            normalized_stage, request.current_stage
        )

        agent = WizardReActAgent()

        agent_input = AgentInput(
            message=request.message,
            session_id=session_id,
            company_id=company_id,
            user_id=user_id,
            conversation_history=[
                {"role": m.get("role", "user"), "content": m.get("content", "")}
                for m in request.conversation_history[-10:]
            ],
            context={
                "current_stage": frontend_stage,
                "collected_data": request.collected_data,
            },
            metadata={},
        )

        agent_output = await agent.process(agent_input)

        detected_criteria = agent_output.state_updates or {}
        next_stage = None
        auto_transition = False
        if agent_output.navigation:
            raw_next = agent_output.navigation.target_stage
            next_stage = BACKEND_TO_FRONTEND_STAGE.get(raw_next, raw_next)
            auto_transition = agent_output.navigation.auto_navigate

        job_vacancy_id = None
        job_published = False
        if next_stage == "complete":
            merged_draft = {**request.collected_data, **detected_criteria}
            job_vacancy_id = await finalize_job_vacancy_from_wizard(
                job_draft=merged_draft,
                session_id=session_id,
                company_id=company_id,
                user_id=user_id,
            )
            if job_vacancy_id:
                job_published = True

        return SmartOrchestrateResponse(
            success=agent_output.error is None,
            lia_message=agent_output.message,
            detected_criteria=detected_criteria,
            next_stage=next_stage,
            auto_transition=auto_transition,
            tool_results=agent_output.tool_results,
            confidence=agent_output.confidence,
            reasoning_steps=agent_output.reasoning_steps,
            intent=agent_output.metadata.get("intent"),
            error=agent_output.error,
            awaiting_confirmation=False,
            job_vacancy_id=job_vacancy_id,
            job_published=job_published,
            conversation_id=session_id,
        )

    except Exception as e:
        logger.error(f"ReAct orchestrate error: {e}", exc_info=True)
        return SmartOrchestrateResponse(
            success=False,
            lia_message=(
                "Desculpe, ocorreu um erro ao processar sua mensagem. "
                "Por favor, tente novamente."
            ),
            detected_criteria={},
            next_stage=None,
            auto_transition=False,
            tool_results=[],
            confidence=0.0,
            reasoning_steps=[f"Error: {str(e)}"],
            intent=None,
            error=str(e),
            awaiting_confirmation=False,
            job_vacancy_id=None,
            job_published=False,
            conversation_id=session_id if 'session_id' in locals() else None,
        )


@router.get("/graph-structure", response_model=None)
async def get_graph_structure(
    current_user: User = Depends(get_current_user_or_demo),
) -> dict[str, Any]:
    """
    Get the structure of the JobWizardGraph for visualization.
    
    Returns nodes, edges, and configuration of the graph.
    """
    return job_wizard_graph.get_graph_structure()


@router.get("/stage-mapping", response_model=None)
async def get_stage_mapping() -> dict[str, Any]:
    """
    Get the mapping between frontend and backend stage names.
    
    Useful for debugging stage transitions.
    """
    return {
        "frontend_to_backend": FRONTEND_TO_BACKEND_STAGE,
        "backend_to_frontend": BACKEND_TO_FRONTEND_STAGE,
        "backend_stages": [stage.value for stage in WizardStage],
    }
