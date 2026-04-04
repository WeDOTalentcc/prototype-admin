"""
Orchestrated Talent Chat API - Routes candidate/sourcing queries through
the TalentAssistantService with analytical routing and closed-loop execution.

v2.0: Analytical routing via TalentAssistantService + closed-loop for actionable intents.
v3.0: ActionExecutor + PendingActionState + closed-loop multi-turn flow.
"""
from fastapi import APIRouter, HTTPException, Depends
from app.dependencies.token_budget import require_token_budget
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
import os
import uuid

from app.orchestrator import Orchestrator
from app.api.orchestrator_routes import get_orchestrator
from app.domains.recruiter_assistant.prompts.talent_assistant_prompts import (
    detect_talent_command_type,
    detect_talent_command_type_enhanced,
    TalentCommandType,
)
from app.domains.recruiter_assistant.services.talent_assistant_service import (
    talent_assistant,
)
from app.orchestrator.action_executor import (
    action_executor, ActionResult, ACTIONABLE_INTENTS,
    is_confirmation, is_rejection, resolve_candidate_from_context,
)
from app.orchestrator.pending_action import PendingActionState, pending_action_store

logger = logging.getLogger(__name__)

router = APIRouter()

_ANALYTICAL_COMMAND_TYPES = {
    TalentCommandType.RANKEAR_CANDIDATOS.value,
    TalentCommandType.COMPARAR_CANDIDATOS.value,
    TalentCommandType.ANALISAR_PERFIL.value,
    TalentCommandType.BUSCAR_SIMILAR.value,
    TalentCommandType.SKILLS_ANALYSIS.value,
    TalentCommandType.TOP_CANDIDATOS.value,
    TalentCommandType.DIVERSIDADE.value,
    TalentCommandType.MATCH_VAGA.value,
    TalentCommandType.ANALISE_POOL.value,
    TalentCommandType.RESUMO_BUSCA.value,
    TalentCommandType.SOURCING_STRATEGY.value,
    TalentCommandType.MARKET_INSIGHTS.value,
    TalentCommandType.ANALISE_GERAL.value,
}

INTENT_TO_UI_ACTION: Dict[str, str] = {
    "criar_vaga": "start_job_wizard",
    "create_job": "start_job_wizard",
    "nova_vaga": "start_job_wizard",
    "contact_candidate": "open_communication_modal",
    "schedule_interview": "open_schedule_modal",
    "export_candidates": "trigger_export",
    "add_to_list": "open_add_to_list_modal",
    "wsi_screening": "open_screening_modal",
    "buscar_similar": "switch_search_mode",
}


class OrchestratedTalentChatRequest(BaseModel):
    message: str = Field(..., description="User's natural language query")
    candidates: List[Dict[str, Any]] = Field(
        default_factory=list, description="List of candidates in current view"
    )
    selected_candidate_ids: Optional[List[str]] = Field(
        None, description="IDs of selected candidates for focused operations"
    )
    search_context: Optional[Dict[str, Any]] = Field(
        None, description="Current search context: query, mode, filters, results count"
    )
    target_job: Optional[Dict[str, Any]] = Field(
        None, description="Optional job vacancy for matching/scoring context"
    )
    conversation_id: Optional[str] = Field(
        None, description="Optional conversation ID for context continuity"
    )
    user_id: str = Field(default="recruiter", description="User ID for routing")
    company_id: str = Field(default="", description="Tenant company ID for multi-tenancy isolation")


class OrchestratedTalentChatResponse(BaseModel):
    success: bool
    content: str = Field(..., description="Formatted markdown response")
    agent_used: str = Field(..., description="Primary agent that handled the query")
    agents_consulted: List[str] = Field(default_factory=list)
    intent_detected: str = Field(..., description="Detected user intent")
    confidence: float = Field(..., description="Routing confidence")
    structured_data: Optional[Dict[str, Any]] = None
    suggested_prompts: List[str] = Field(default_factory=list)
    actions: List[Dict[str, Any]] = Field(default_factory=list)
    conversation_id: Optional[str] = None
    ui_action: Optional[str] = Field(None, description="Frontend action trigger")
    ui_action_params: Optional[Dict[str, Any]] = Field(None)
    action_executed: bool = Field(default=False)
    action_result: Optional[Dict[str, Any]] = None
    action_type: Optional[str] = None
    needs_confirmation: bool = Field(default=False, description="Whether action awaits user confirmation")
    needs_params: bool = Field(default=False, description="Whether action needs more parameters from user")
    pending_action_id: Optional[str] = Field(None, description="ID for pending multi-turn action")
    execution_plan: Optional[Dict[str, Any]] = Field(None, description="Multi-step plan summary if a plan was executed")


def detect_actionable_intent(message: str) -> Optional[tuple[str, Optional[str], Optional[Dict[str, Any]]]]:
    msg_lower = message.lower().strip()

    if any(kw in msg_lower for kw in ["criar vaga", "nova vaga", "abrir vaga", "nova posição"]):
        return "create_job", "start_job_wizard", {"initial_message": message}

    if any(kw in msg_lower for kw in ["enviar email", "contatar", "mensagem para", "whatsapp"]):
        return "contact_candidate", "open_communication_modal", None

    if any(kw in msg_lower for kw in ["agendar", "entrevista", "schedule"]):
        return "schedule_interview", "open_schedule_modal", None

    if any(kw in msg_lower for kw in ["exportar", "export", "csv", "download"]):
        return "export_candidates", "trigger_export", None

    if any(kw in msg_lower for kw in ["adicionar à lista", "salvar lista", "favoritos"]):
        return "add_to_list", "open_add_to_list_modal", None

    if any(kw in msg_lower for kw in ["triagem", "screening", "wsi"]):
        return "wsi_screening", "open_screening_modal", None

    if any(kw in msg_lower for kw in ["perfil similar", "similar a", "parecido com"]):
        return "buscar_similar", "switch_search_mode", {"mode": "perfil-similar"}

    return None


async def _extract_talent_param_value_smart(
    message: str, param_name: str, candidates: List[Dict[str, Any]]
) -> Optional[Any]:
    msg = message.strip()
    if not msg:
        return None

    if param_name == "candidate_id":
        resolved = resolve_candidate_from_context(msg, None, candidates)
        if resolved:
            return str(resolved.get("id", ""))
        return None

    if param_name in ("subject", "body", "reason"):
        if len(msg) > 0:
            return msg
        return None

    if param_name in ("datetime", "interviewer"):
        try:
            from app.services.llm import LLMService
            llm = LLMService()
            prompt = f"""Extraia o valor do campo '{param_name}' da mensagem do usuário.
Mensagem: "{msg}"
Campo a extrair: {param_name}
- Se param é "datetime": extraia data e hora mencionada. Formato: YYYY-MM-DD HH:MM. Se "amanhã", calcule a partir de hoje.
- Se param é "interviewer": extraia o nome do entrevistador mencionado.
Responda APENAS com o valor extraído, sem explicações. Se não encontrar, responda "NULL"."""

            response = await llm.generate(prompt, max_tokens=50)
            if response and response.strip() and response.strip().upper() != "NULL":
                return response.strip()
        except Exception as e:
            logger.warning(f"LLM extraction failed for {param_name}: {e}")

        if len(msg) > 0:
            return msg
        return None

    if len(msg) > 0:
        return msg
    return None


@router.post("/talent-chat", response_model=OrchestratedTalentChatResponse)
async def orchestrated_talent_chat(
    request: OrchestratedTalentChatRequest,
    orchestrator: Orchestrator = Depends(get_orchestrator),
    _budget: None = Depends(require_token_budget),
):
    """
    Process talent funnel queries through:
    Phase 0: Check pending multi-turn action (confirmation or parameter collection)
    Phase 1: Actionable intent detection (UI actions, closed-loop)
    Phase 2: Analytical routing via TalentAssistantService (dedicated LLM analysis)
    Phase 3: ActionExecutor try_execute for actionable intents
    Phase 4: Generic orchestrator fallback
    """
    try:
        logger.info(f"[TalentChat] Processing: {request.message[:100]}...")

        selected_count = len(request.selected_candidate_ids) if request.selected_candidate_ids else 0
        candidates_count = len(request.candidates)

        conv_id = request.conversation_id or str(uuid.uuid4())

        # === PHASE 0: Check pending action (multi-turn / confirmation) ===
        pending = pending_action_store.get(conv_id)

        if pending:
            if pending.awaiting_confirmation:
                if is_confirmation(request.message):
                    config = ACTIONABLE_INTENTS.get(pending.intent, {})
                    exec_result = await action_executor._execute_action(
                        pending.intent, config, pending.collected_params,
                        {"conversation_id": conv_id, "user_id": request.user_id}
                    )
                    pending_action_store.remove(conv_id)

                    return OrchestratedTalentChatResponse(
                        success=True,
                        content=exec_result.message,
                        agent_used="ActionExecutor",
                        agents_consulted=["ActionExecutor"],
                        intent_detected=pending.intent,
                        confidence=1.0,
                        suggested_prompts=_get_suggested_prompts(pending.intent, candidates_count, selected_count),
                        actions=[],
                        conversation_id=conv_id,
                        action_executed=True,
                        action_result=exec_result.data,
                        action_type=exec_result.action_type,
                    )
                elif is_rejection(request.message):
                    pending_action_store.remove(conv_id)
                    return OrchestratedTalentChatResponse(
                        success=True,
                        content="Ok, ação cancelada. Como posso te ajudar?",
                        agent_used="ActionExecutor",
                        agents_consulted=["ActionExecutor"],
                        intent_detected="cancelamento",
                        confidence=1.0,
                        suggested_prompts=["Quem são os melhores candidatos?", "Busque perfis similares"],
                        actions=[],
                        conversation_id=conv_id,
                    )
                else:
                    pending_action_store.remove(conv_id)

            elif pending.missing_params:
                next_param = pending.next_missing_param()
                if next_param:
                    extracted_value = await _extract_talent_param_value_smart(request.message, next_param, request.candidates)
                    if extracted_value:
                        pending.add_param(next_param, extracted_value)

                        if next_param == "candidate_id":
                            resolved = resolve_candidate_from_context(None, extracted_value, request.candidates)
                            if resolved:
                                pending.collected_params["candidate_name"] = resolved.get("name", "")
                                pending.collected_params["candidate_email"] = resolved.get("email", "")
                                if resolved.get("stage"):
                                    pending.collected_params["from_stage"] = resolved["stage"]

                        if pending.is_complete:
                            config = ACTIONABLE_INTENTS.get(pending.intent, {})
                            if config.get("requires_confirmation", False):
                                summary = action_executor._build_confirmation_summary(
                                    pending.intent, config, pending.collected_params
                                )
                                pending.awaiting_confirmation = True
                                pending.confirmation_summary = summary
                                pending_action_store.save(conv_id, pending)

                                return OrchestratedTalentChatResponse(
                                    success=True,
                                    content=summary["message"],
                                    agent_used="ActionExecutor",
                                    agents_consulted=["ActionExecutor"],
                                    intent_detected=pending.intent,
                                    confidence=1.0,
                                    suggested_prompts=[],
                                    actions=[],
                                    conversation_id=conv_id,
                                    needs_confirmation=True,
                                    pending_action_id=pending.pending_id,
                                )
                            else:
                                exec_result = await action_executor._execute_action(
                                    pending.intent, config, pending.collected_params,
                                    {"conversation_id": conv_id, "user_id": request.user_id}
                                )
                                pending_action_store.remove(conv_id)
                                return OrchestratedTalentChatResponse(
                                    success=True,
                                    content=exec_result.message,
                                    agent_used="ActionExecutor",
                                    agents_consulted=["ActionExecutor"],
                                    intent_detected=pending.intent,
                                    confidence=1.0,
                                    suggested_prompts=_get_suggested_prompts(pending.intent, candidates_count, selected_count),
                                    actions=[],
                                    conversation_id=conv_id,
                                    action_executed=True,
                                    action_result=exec_result.data,
                                    action_type=exec_result.action_type,
                                )
                        else:
                            next_param2 = pending.next_missing_param()
                            config = ACTIONABLE_INTENTS.get(pending.intent, {})
                            prompt = config.get("clarification_prompts", {}).get(
                                next_param2, f"Informe: {next_param2}"
                            )
                            pending_action_store.save(conv_id, pending)

                            return OrchestratedTalentChatResponse(
                                success=True,
                                content=prompt,
                                agent_used="ActionExecutor",
                                agents_consulted=["ActionExecutor"],
                                intent_detected=pending.intent,
                                confidence=1.0,
                                suggested_prompts=[],
                                actions=[],
                                conversation_id=conv_id,
                                needs_params=True,
                                pending_action_id=pending.pending_id,
                            )
                    else:
                        pending_action_store.remove(conv_id)

        # === PHASE 1: Actionable intent detection ===
        actionable = detect_actionable_intent(request.message)
        if actionable:
            intent, ui_action, ui_action_params = actionable

            intent_to_executor_map = {
                "contact_candidate": "enviar_email",
                "schedule_interview": "agendar_entrevista",
                "wsi_screening": "disparar_triagem",
            }
            executor_intent = intent_to_executor_map.get(intent)

            if executor_intent and executor_intent in ACTIONABLE_INTENTS:
                extracted_entities: Dict[str, Any] = {}
                if request.selected_candidate_ids and len(request.selected_candidate_ids) == 1:
                    extracted_entities["candidate_id"] = request.selected_candidate_ids[0]

                action_exec_result = await action_executor.try_execute(
                    intent=executor_intent,
                    entities=extracted_entities,
                    candidates_data=request.candidates,
                    context={"conversation_id": conv_id, "user_id": request.user_id},
                )

                if action_exec_result.status == "executed":
                    return OrchestratedTalentChatResponse(
                        success=True,
                        content=action_exec_result.message,
                        agent_used="ActionExecutor",
                        agents_consulted=["TalentAssistant", "ActionExecutor"],
                        intent_detected=executor_intent,
                        confidence=0.95,
                        suggested_prompts=_get_suggested_prompts(intent, candidates_count, selected_count),
                        conversation_id=conv_id,
                        action_executed=True,
                        action_result=action_exec_result.data,
                        action_type=action_exec_result.action_type,
                    )

                elif action_exec_result.status == "needs_params":
                    pending_state = PendingActionState(
                        pending_id=action_exec_result.pending_action_id or "",
                        intent=executor_intent,
                        action_id=action_exec_result.action_type or "",
                        domain_id=ACTIONABLE_INTENTS.get(executor_intent, {}).get("domain_id", ""),
                        collected_params=action_exec_result.data.get("collected_params", {}) if action_exec_result.data else {},
                        missing_params=action_exec_result.missing_params or [],
                        conversation_id=conv_id,
                    )
                    pending_action_store.save(conv_id, pending_state)

                    return OrchestratedTalentChatResponse(
                        success=True,
                        content=action_exec_result.message,
                        agent_used="ActionExecutor",
                        agents_consulted=["TalentAssistant", "ActionExecutor"],
                        intent_detected=executor_intent,
                        confidence=0.95,
                        suggested_prompts=[],
                        conversation_id=conv_id,
                        needs_params=True,
                        pending_action_id=action_exec_result.pending_action_id,
                    )

                elif action_exec_result.status == "needs_confirmation":
                    pending_state = PendingActionState(
                        pending_id=action_exec_result.pending_action_id or "",
                        intent=executor_intent,
                        action_id=action_exec_result.action_type or "",
                        domain_id=ACTIONABLE_INTENTS.get(executor_intent, {}).get("domain_id", ""),
                        collected_params=action_exec_result.data.get("collected_params", {}) if action_exec_result.data else {},
                        missing_params=[],
                        conversation_id=conv_id,
                        awaiting_confirmation=True,
                        confirmation_summary=action_exec_result.confirmation_summary,
                    )
                    pending_action_store.save(conv_id, pending_state)

                    return OrchestratedTalentChatResponse(
                        success=True,
                        content=action_exec_result.message,
                        agent_used="ActionExecutor",
                        agents_consulted=["TalentAssistant", "ActionExecutor"],
                        intent_detected=executor_intent,
                        confidence=0.95,
                        suggested_prompts=[],
                        conversation_id=conv_id,
                        needs_confirmation=True,
                        pending_action_id=action_exec_result.pending_action_id,
                    )

            logger.info(f"[TalentChat] Actionable intent: {intent} -> {ui_action}")

            content_map = {
                "create_job": "Entendi! Vou abrir o **assistente de criação de vagas** para você. 🚀",
                "contact_candidate": "Para **contatar candidatos**, vou abrir o painel de comunicação.",
                "schedule_interview": "Vou abrir o **agendamento de entrevista** para você.",
                "export_candidates": f"Exportando **{candidates_count} candidatos** para CSV. 📥",
                "add_to_list": "Vou abrir a opção de **adicionar à lista**.",
                "wsi_screening": "Vou iniciar a **triagem WSI** para os candidatos selecionados.",
                "buscar_similar": "Ativando modo de **busca por perfil similar**. 🔍",
            }

            return OrchestratedTalentChatResponse(
                success=True,
                content=content_map.get(intent, "Processando sua ação..."),
                agent_used="TalentAssistant",
                agents_consulted=["TalentAssistant"],
                intent_detected=intent,
                confidence=0.95,
                suggested_prompts=_get_suggested_prompts(intent, candidates_count, selected_count),
                conversation_id=conv_id,
                ui_action=ui_action,
                ui_action_params=ui_action_params,
            )

        # === PHASE 2: TalentReActAgent — ReAct loop com tool calling ao DB ===
        # Caminho principal: agente autônomo com acesso real ao banco de dados.
        # Pode responder qualquer pergunta aberta, buscar dados complementares,
        # acessar formação acadêmica, histórico completo, etc.
        try:
            from app.domains.recruiter_assistant.agents.talent_react_agent import TalentReActAgent
            from app.shared.agents.agent_interface import AgentInput as ReactAgentInput

            agent_input = ReactAgentInput(
                message=request.message,
                session_id=conv_id,
                company_id=request.company_id or "default",
                user_id=request.user_id,
                context={
                    "candidates": request.candidates,
                    "selected_candidate_ids": request.selected_candidate_ids or [],
                    "search_context": request.search_context or {},
                    "target_job": request.target_job or {},
                },
            )

            agent = TalentReActAgent()
            output = await agent.process(agent_input)

            return OrchestratedTalentChatResponse(
                success=True,
                content=output.message,
                agent_used="TalentReActAgent",
                agents_consulted=["TalentReActAgent"],
                intent_detected="react_agent",
                confidence=output.confidence,
                structured_data=output.state_updates or None,
                suggested_prompts=_get_suggested_prompts("react_agent", candidates_count, selected_count),
                actions=[{"type": a.action_type, "data": a.params} for a in output.actions] if output.actions else [],
                conversation_id=conv_id,
                needs_confirmation=any(a.requires_confirmation for a in output.actions) if output.actions else False,
                action_executed=bool(output.tool_results),
            )
        except Exception as react_error:
            logger.warning(f"[TalentChat] ReAct agent failed, falling back to legacy: {react_error}")

        # === PHASE 3 (FALLBACK): Analytical routing via TalentAssistantService ===
        # Usado apenas quando o ReAct agent falhar.
        cmd_type, confidence = await detect_talent_command_type_enhanced(request.message)
        logger.info(f"[TalentChat] Fallback analytical command: {cmd_type} (confidence: {confidence:.2f})")

        if cmd_type in _ANALYTICAL_COMMAND_TYPES:
            try:
                result = await talent_assistant.process_command(
                    command=request.message,
                    command_type=cmd_type,
                    candidates=request.candidates,
                    selected_candidate_ids=request.selected_candidate_ids,
                    search_context=request.search_context,
                    target_job=request.target_job,
                )

                return OrchestratedTalentChatResponse(
                    success=True,
                    content=result["content"],
                    agent_used="TalentAssistant",
                    agents_consulted=["TalentAssistant"],
                    intent_detected=cmd_type,
                    confidence=result.get("confidence", confidence),
                    structured_data=result.get("structured_data"),
                    suggested_prompts=result.get("suggested_prompts", []),
                    conversation_id=conv_id,
                )
            except Exception as svc_error:
                logger.warning(f"[TalentChat] TalentAssistant error: {svc_error}, falling back to orchestrator")

        # === PHASE 4 (FALLBACK): Orchestrator fallback + ActionExecutor try_execute ===
        try:
            from app.domains.recruiter_assistant.prompts.talent_assistant_prompts import build_talent_prompt
            enriched_message = build_talent_prompt(
                command_type=cmd_type,
                user_query=request.message,
                candidates=request.candidates,
                selected_ids=request.selected_candidate_ids,
                search_context=request.search_context,
                target_job=request.target_job,
            )

            result = await orchestrator.route_message(
                message=enriched_message,
                user_id=request.user_id,
                context={
                    "source": "talent_funnel",
                    "intent": cmd_type,
                    "candidates_count": candidates_count,
                    "selected_count": selected_count,
                    "search_context": request.search_context,
                    "target_job": request.target_job,
                    "conversation_id": conv_id,
                },
            )

            orch_intent = result.get("intent", cmd_type)
            orch_entities = result.get("entities", {})

            if orch_intent in ACTIONABLE_INTENTS:
                action_exec_result = await action_executor.try_execute(
                    intent=orch_intent,
                    entities=orch_entities,
                    candidates_data=request.candidates,
                    context={"conversation_id": conv_id, "user_id": request.user_id},
                )

                if action_exec_result.status == "executed":
                    return OrchestratedTalentChatResponse(
                        success=True,
                        content=action_exec_result.message,
                        agent_used=result.get("agent_used", "Orchestrator"),
                        agents_consulted=[result.get("agent_used", "Orchestrator"), "ActionExecutor"],
                        intent_detected=orch_intent,
                        confidence=result.get("confidence", 0.8),
                        suggested_prompts=_get_suggested_prompts(orch_intent, candidates_count, selected_count),
                        actions=[],
                        conversation_id=conv_id,
                        action_executed=True,
                        action_result=action_exec_result.data,
                        action_type=action_exec_result.action_type,
                    )

                elif action_exec_result.status == "needs_params":
                    pending_state = PendingActionState(
                        pending_id=action_exec_result.pending_action_id or "",
                        intent=orch_intent,
                        action_id=action_exec_result.action_type or "",
                        domain_id=ACTIONABLE_INTENTS.get(orch_intent, {}).get("domain_id", ""),
                        collected_params=action_exec_result.data.get("collected_params", {}) if action_exec_result.data else {},
                        missing_params=action_exec_result.missing_params or [],
                        conversation_id=conv_id,
                    )
                    pending_action_store.save(conv_id, pending_state)

                    return OrchestratedTalentChatResponse(
                        success=True,
                        content=action_exec_result.message,
                        agent_used=result.get("agent_used", "Orchestrator"),
                        agents_consulted=[result.get("agent_used", "Orchestrator"), "ActionExecutor"],
                        intent_detected=orch_intent,
                        confidence=result.get("confidence", 0.8),
                        suggested_prompts=[],
                        actions=[],
                        conversation_id=conv_id,
                        needs_params=True,
                        pending_action_id=action_exec_result.pending_action_id,
                    )

                elif action_exec_result.status == "needs_confirmation":
                    pending_state = PendingActionState(
                        pending_id=action_exec_result.pending_action_id or "",
                        intent=orch_intent,
                        action_id=action_exec_result.action_type or "",
                        domain_id=ACTIONABLE_INTENTS.get(orch_intent, {}).get("domain_id", ""),
                        collected_params=action_exec_result.data.get("collected_params", {}) if action_exec_result.data else {},
                        missing_params=[],
                        conversation_id=conv_id,
                        awaiting_confirmation=True,
                        confirmation_summary=action_exec_result.confirmation_summary,
                    )
                    pending_action_store.save(conv_id, pending_state)

                    return OrchestratedTalentChatResponse(
                        success=True,
                        content=action_exec_result.message,
                        agent_used=result.get("agent_used", "Orchestrator"),
                        agents_consulted=[result.get("agent_used", "Orchestrator"), "ActionExecutor"],
                        intent_detected=orch_intent,
                        confidence=result.get("confidence", 0.8),
                        suggested_prompts=[],
                        actions=[],
                        conversation_id=conv_id,
                        needs_confirmation=True,
                        pending_action_id=action_exec_result.pending_action_id,
                    )

            _plan_content = result.get("message") or result.get("response", "Processando sua solicitação...")
            return OrchestratedTalentChatResponse(
                success=True,
                content=_plan_content,
                agent_used=result.get("agent", result.get("agent_used", "Orchestrator")),
                agents_consulted=result.get("agents_consulted", ["Orchestrator"]),
                intent_detected=result.get("intent", cmd_type),
                confidence=result.get("confidence", 0.8),
                structured_data=result.get("structured_data"),
                suggested_prompts=result.get("suggested_prompts") or _get_suggested_prompts(cmd_type, candidates_count, selected_count),
                actions=result.get("actions", []),
                conversation_id=conv_id,
                execution_plan=result.get("execution_plan"),
            )

        except Exception as orch_error:
            logger.warning(f"[TalentChat] Orchestrator error: {orch_error}, using fallback")

            return OrchestratedTalentChatResponse(
                success=True,
                content=_generate_fallback(request.message, candidates_count, selected_count),
                agent_used="TalentAssistant",
                agents_consulted=["TalentAssistant"],
                intent_detected=cmd_type,
                confidence=0.5,
                suggested_prompts=_get_suggested_prompts(cmd_type, candidates_count, selected_count),
                conversation_id=conv_id,
            )

    except Exception as e:
        logger.error(f"[TalentChat] Error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error processing talent chat: {str(e)}"
        )


@router.get("/talent-chat/intents")
async def get_talent_chat_intents():
    return {
        "intents": [
            {"id": "rankear_candidatos", "description": "Ranking de candidatos", "keywords": ["ranking", "ordenar", "top", "melhores"]},
            {"id": "comparar_candidatos", "description": "Comparar candidatos", "keywords": ["comparar", "compare", "versus", "vs"]},
            {"id": "analisar_perfil", "description": "Analisar perfil", "keywords": ["analisar", "analise", "avaliar", "parecer"]},
            {"id": "buscar_similar", "description": "Buscar perfis similares", "keywords": ["perfil similar", "similar a", "parecido"], "ui_action": "switch_search_mode"},
            {"id": "skills_analysis", "description": "Análise de skills", "keywords": ["skills", "habilidades", "competências"]},
            {"id": "match_vaga", "description": "Match com vaga", "keywords": ["match", "fit", "aderência"]},
            {"id": "analise_pool", "description": "Análise do pool", "keywords": ["pool", "banco", "base de candidatos"]},
            {"id": "contact_candidate", "description": "Contatar candidatos", "keywords": ["email", "contatar", "whatsapp"], "ui_action": "open_communication_modal"},
            {"id": "schedule_interview", "description": "Agendar entrevistas", "keywords": ["agendar", "entrevista"], "ui_action": "open_schedule_modal"},
            {"id": "wsi_screening", "description": "Triagem WSI", "keywords": ["triagem", "screening", "wsi"], "ui_action": "open_screening_modal"},
            {"id": "criar_vaga", "description": "Criar nova vaga", "keywords": ["criar vaga", "nova vaga", "abrir vaga"], "ui_action": "start_job_wizard"},
        ],
        "context": "talent_funnel",
    }


def _get_suggested_prompts(intent: str, candidates_count: int, selected_count: int) -> List[str]:
    if selected_count > 1:
        return [
            f"Compare os {selected_count} candidatos selecionados",
            "Qual é o melhor candidato entre os selecionados?",
            "Gere um ranking dos selecionados por fit",
        ]
    elif selected_count == 1:
        return [
            "Analise este candidato em detalhes",
            "Quais são os pontos fortes e fracos?",
            "Busque perfis similares a este candidato",
        ]
    elif candidates_count > 0:
        return [
            f"Quem são os top 5 entre os {candidates_count}?",
            "Analise a qualidade geral dos candidatos",
            "Identifique padrões nos perfis encontrados",
        ]
    return [
        "Busque desenvolvedores Python em São Paulo",
        "Encontre candidatos com perfil de liderança",
        "Quais skills estão em alta no mercado?",
    ]


def _generate_fallback(message: str, candidates_count: int, selected_count: int) -> str:
    return (
        f"Entendi sua solicitação. Com **{candidates_count} candidatos** em visualização"
        + (f" ({selected_count} selecionados)" if selected_count > 0 else "")
        + ", como posso ajudá-lo?\n\n"
        "Posso:\n"
        "• Rankear e comparar candidatos\n"
        "• Analisar perfis em detalhes\n"
        "• Avaliar match com uma vaga\n"
        "• Sugerir estratégias de sourcing\n"
        "• Criar uma nova vaga"
    )
