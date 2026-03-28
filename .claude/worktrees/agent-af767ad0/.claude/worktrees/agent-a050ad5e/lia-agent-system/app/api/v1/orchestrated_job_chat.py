"""
Orchestrated Job Chat API - Routes job-specific queries through multi-agent system.

This endpoint enriches job context and routes queries through the main Orchestrator,
leveraging specialized agents with full context about the vacancy and candidates.

v2.0: Closed-loop action execution - LIA executes actions directly instead of
opening modals for the user to act manually.
"""
from fastapi import APIRouter, HTTPException, Depends
from app.dependencies.token_budget import require_token_budget
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
import os
import uuid

from app.services.job_context_service import job_context_service, EnrichedJobContext
from app.orchestrator import Orchestrator
from app.api.orchestrator_routes import get_orchestrator
from app.orchestrator.action_executor import (
    action_executor, ActionResult, is_confirmation, is_rejection, ACTIONABLE_INTENTS,
    resolve_candidate_from_context, resolve_stage,
)
from app.orchestrator.pending_action import pending_action_store, PendingActionState
from app.domains.recruiter_assistant.prompts.kanban_assistant_prompts import detect_command_type, KanbanCommandType

_ANALYTICAL_COMMAND_TYPES = {
    KanbanCommandType.RANKEAR_CANDIDATOS.value,
    KanbanCommandType.PERFORMANCE_FUNIL.value,
    KanbanCommandType.GARGALOS_PROCESSO.value,
    KanbanCommandType.COMPARAR_CANDIDATOS.value,
    KanbanCommandType.RESUMIR_PERFIL.value,
    KanbanCommandType.CANDIDATOS_ATIVOS.value,
    KanbanCommandType.TAXA_CONVERSAO.value,
    KanbanCommandType.TEMPO_MEDIO.value,
    KanbanCommandType.CANDIDATOS_PARADOS.value,
    KanbanCommandType.TOP_CANDIDATOS.value,
    KanbanCommandType.ANALISAR_PERFIL.value,
    KanbanCommandType.ANALISE_GERAL.value,
}

logger = logging.getLogger(__name__)

router = APIRouter()


class OrchestratedJobChatRequest(BaseModel):
    """Request for orchestrated job chat."""
    message: str = Field(..., description="User's natural language query")
    job_context: Dict[str, Any] = Field(
        ..., 
        description="Job vacancy context: title, department, level, requirements, skills, etc."
    )
    candidates: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of candidates in the pipeline with their data"
    )
    selected_candidate_ids: Optional[List[str]] = Field(
        None,
        description="IDs of selected candidates for focused operations"
    )
    conversation_id: Optional[str] = Field(
        None,
        description="Optional conversation ID for context continuity"
    )
    user_id: str = Field(default="recruiter", description="User ID for routing")
    company_id: str = Field(default="", description="Tenant company ID for multi-tenancy isolation")


class OrchestratedJobChatResponse(BaseModel):
    """Response from orchestrated job chat."""
    success: bool
    content: str = Field(..., description="Formatted markdown response")
    agent_used: str = Field(..., description="Primary agent that handled the query")
    agents_consulted: List[str] = Field(default_factory=list, description="All agents consulted")
    intent_detected: str = Field(..., description="Detected user intent")
    confidence: float = Field(..., description="Routing confidence")
    structured_data: Optional[Dict[str, Any]] = None
    suggested_prompts: List[str] = Field(default_factory=list)
    actions: List[Dict[str, Any]] = Field(default_factory=list, description="Suggested UI actions")
    conversation_id: Optional[str] = None
    ui_action: Optional[str] = Field(None, description="Frontend action trigger (fallback)")
    ui_action_params: Optional[Dict[str, Any]] = Field(None, description="Parameters for UI action (fallback)")
    action_executed: bool = Field(default=False, description="Whether a real action was executed via closed-loop")
    action_result: Optional[Dict[str, Any]] = Field(None, description="Result data of executed action")
    action_type: Optional[str] = Field(None, description="Type of action executed (move_candidate, send_email, etc.)")
    needs_confirmation: bool = Field(default=False, description="Whether action awaits user confirmation")
    needs_params: bool = Field(default=False, description="Whether action needs more parameters from user")
    pending_action_id: Optional[str] = Field(None, description="ID for pending multi-turn action")


def build_enriched_context_summary(enriched: EnrichedJobContext) -> str:
    """Build a structured context summary for the orchestrator."""
    fm = enriched.funnel_metrics
    
    lines = [
        f"[CONTEXTO DA VAGA: {enriched.title}]",
        f"Departamento: {enriched.department or 'N/A'}",
        f"Senioridade: {enriched.seniority or 'N/A'}",
        f"Modelo: {enriched.work_model or 'N/A'}",
        f"Localização: {enriched.location or 'N/A'}",
        f"Skills requeridas: {', '.join(enriched.required_skills[:5])}",
        "",
        "[FUNIL]",
        f"Total candidatos: {fm.total_candidates}",
        f"Status: {fm.health_status.value}",
        f"Gargalo: {fm.bottleneck_stage or 'Nenhum'}",
        f"Parados >7d: {len(fm.stalled_candidates)}",
        f"Aguardando feedback: {len(fm.candidates_needing_feedback)}",
        "",
        "[CANDIDATOS POR ETAPA]",
    ]
    
    for stage, count in fm.by_stage.items():
        if count > 0:
            lines.append(f"- {stage}: {count}")
    
    if enriched.candidates:
        lines.append("")
        lines.append(f"[TOP CANDIDATOS - {min(10, len(enriched.candidates))} de {len(enriched.candidates)}]")
        
        sorted_candidates = sorted(
            enriched.candidates,
            key=lambda c: c.wsi_score or 0,
            reverse=True
        )[:10]
        
        for c in sorted_candidates:
            wsi = f"WSI:{c.wsi_score:.1f}" if c.wsi_score else "WSI:N/A"
            fit = f"Fit:{c.fit_score}%" if c.fit_score else ""
            big5 = ""
            if c.big_five:
                big5 = f"Big5(O:{c.big_five.get('O','?')},C:{c.big_five.get('C','?')},E:{c.big_five.get('E','?')},A:{c.big_five.get('A','?')},N:{c.big_five.get('N','?')})"
            
            lines.append(
                f"- {c.name} | {c.stage}({c.days_in_stage}d) | {wsi} {fit} | Skills:{','.join(c.skills[:3])}"
            )
            if big5:
                lines.append(f"  {big5}")
    
    return "\n".join(lines)


def extract_suggested_prompts(intent: str, agent: str) -> List[str]:
    """Get suggested follow-up prompts based on intent and agent."""
    prompts_map = {
        "avaliador_wsi": [
            "Compare os top 3 candidatos em detalhes",
            "Quais candidatos têm melhor fit técnico?",
            "Analise o perfil Big Five dos finalistas"
        ],
        "analista_feedback": [
            "Identifique gargalos no processo",
            "Quem precisa de feedback urgente?",
            "Como melhorar a taxa de conversão?"
        ],
        "sourcing": [
            "Quais candidatos têm melhor match com a vaga?",
            "Sugira filtros para refinar a busca",
            "Compare perfis similares"
        ],
        "recruiter_assistant": [
            "Quem são os melhores candidatos?",
            "Como está o funil?",
            "Quais próximos passos você sugere?"
        ],
        "mover_candidato": [
            "Mover todos os aprovados para entrevista",
            "Quais candidatos estão prontos para avançar?",
            "Rejeitar candidatos com score abaixo de 50%"
        ],
        "triagem_curricular": [
            "Quais CVs precisam de análise?",
            "Compare experiências dos candidatos",
            "Identifique gaps nos perfis"
        ]
    }
    
    for key, prompts in prompts_map.items():
        if key in (agent or "").lower():
            return prompts
    
    return prompts_map.get("recruiter_assistant", [])


def extract_actions(enriched: EnrichedJobContext, intent: str) -> List[Dict[str, Any]]:
    """Extract actionable UI suggestions based on context."""
    actions = []
    
    stalled = enriched.funnel_metrics.stalled_candidates
    if stalled and len(stalled) > 0:
        actions.append({
            "type": "bulk_action",
            "action": "move_stage",
            "label": f"Revisar {len(stalled)} candidatos parados",
            "candidate_ids": [c["id"] for c in stalled]
        })
    
    needing_feedback = enriched.funnel_metrics.candidates_needing_feedback
    if needing_feedback and len(needing_feedback) > 0:
        actions.append({
            "type": "bulk_action",
            "action": "send_feedback",
            "label": f"Enviar feedback para {len(needing_feedback)} candidatos",
            "candidate_ids": [c["id"] for c in needing_feedback]
        })
    
    return actions


INTENT_TO_UI_ACTION: Dict[str, str] = {
    "mover_candidato": "move_candidate",
    "atualizar_status_candidato": "move_candidate",
    "update_candidate_status": "move_candidate",
    "reprovar_candidato": "move_candidate",
    
    "aprovar_candidato": "approve_candidate",
    
    "enviar_email": "send_email",
    "enviar_mensagem": "send_email",
    "send_email": "send_email",
    
    "disparar_triagem": "start_screening",
    "iniciar_triagem": "start_screening",
    "start_screening": "start_screening",
    "cv_screening": "start_screening",
    "triagem_curricular": "start_screening",
    
    "agendar_entrevista": "schedule_interview",
    "schedule_interview": "schedule_interview",
    "scheduling": "schedule_interview",
    "reagendar_entrevista": "schedule_interview",
    
    "solicitar_dados": "request_data",
    "pedir_documentos": "request_data",
    "request_data": "request_data",
    
    "analisar_perfil": "analyze_profile",
    "analise_detalhada": "analyze_profile",
    "analyze_profile": "analyze_profile",
    
    "create_job_vacancy": "start_job_wizard",
    "create_job": "start_job_wizard",
}

def get_ui_action_from_intent(intent: str, message: str, entities: Optional[Dict[str, Any]] = None) -> tuple[Optional[str], Optional[Dict[str, Any]]]:
    """Determine UI action from LLM-classified intent. No keyword matching needed."""
    ui_action = INTENT_TO_UI_ACTION.get(intent)
    
    if not ui_action:
        message_lower = message.lower()
        for kw in ["criar vaga", "nova vaga", "abrir vaga", "create job"]:
            if kw in message_lower:
                return "start_job_wizard", {"initial_message": message}
        return None, None
    
    params: Dict[str, Any] = {"initial_message": message}
    
    if entities:
        if entities.get("candidate_name"):
            params["candidate_name"] = entities["candidate_name"]
        if entities.get("action_type"):
            params["action_type"] = entities["action_type"]
    
    return ui_action, params


async def _extract_param_value_smart(
    message: str, param_name: str, candidates: List[Dict[str, Any]]
) -> Optional[Any]:
    """Extract a specific parameter value from user message using LLM when needed."""
    msg = message.strip()
    if not msg:
        return None

    if param_name == "candidate_id":
        resolved = resolve_candidate_from_context(msg, None, candidates)
        if resolved:
            return str(resolved.get("id", ""))
        return None

    if param_name == "to_stage":
        return resolve_stage(msg)

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


@router.post("/orchestrator/job-chat", response_model=OrchestratedJobChatResponse)
async def orchestrated_job_chat(
    request: OrchestratedJobChatRequest,
    orch: Orchestrator = Depends(get_orchestrator),
    _budget: None = Depends(require_token_budget),
) -> OrchestratedJobChatResponse:
    """
    Process a job-context query through the multi-agent orchestrator.
    
    v2.0 Closed-loop flow:
    1. Check for pending multi-turn action (confirmation or parameter collection)
    2. Enrich context and route through Orchestrator for intent classification
    3. If intent is actionable → ActionExecutorService tries to execute directly
    4. If execution succeeds → return result in chat (no modal needed)
    5. If params missing → ask user and store PendingActionState
    6. If confirmation needed → ask user and store PendingActionState
    7. Fallback: return ui_action for frontend modal (backward compatible)
    """
    if not request.message:
        raise HTTPException(status_code=400, detail="Message is required")

    if not request.job_context:
        raise HTTPException(status_code=400, detail="Job context is required")

    try:
        logger.info(f"Orchestrated job chat: {request.message[:100]}...")

        conv_id = request.conversation_id or str(uuid.uuid4())

        # === PHASE 1: Check pending action (multi-turn / confirmation) ===
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

                    return OrchestratedJobChatResponse(
                        success=True,
                        content=exec_result.message,
                        agent_used="ActionExecutor",
                        agents_consulted=["ActionExecutor"],
                        intent_detected=pending.intent,
                        confidence=1.0,
                        suggested_prompts=extract_suggested_prompts(pending.intent, "ActionExecutor"),
                        actions=[],
                        conversation_id=conv_id,
                        action_executed=True,
                        action_result=exec_result.data,
                        action_type=exec_result.action_type,
                    )
                elif is_rejection(request.message):
                    pending_action_store.remove(conv_id)
                    return OrchestratedJobChatResponse(
                        success=True,
                        content="Ok, ação cancelada. Como posso te ajudar?",
                        agent_used="ActionExecutor",
                        agents_consulted=["ActionExecutor"],
                        intent_detected="cancelamento",
                        confidence=1.0,
                        suggested_prompts=["Quem são os melhores candidatos?", "Como está o funil?"],
                        actions=[],
                        conversation_id=conv_id,
                    )
                else:
                    pending_action_store.remove(conv_id)

            elif pending.missing_params:
                next_param = pending.next_missing_param()
                if next_param:
                    extracted_value = await _extract_param_value_smart(request.message, next_param, request.candidates)
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

                                return OrchestratedJobChatResponse(
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
                                return OrchestratedJobChatResponse(
                                    success=True,
                                    content=exec_result.message,
                                    agent_used="ActionExecutor",
                                    agents_consulted=["ActionExecutor"],
                                    intent_detected=pending.intent,
                                    confidence=1.0,
                                    suggested_prompts=extract_suggested_prompts(pending.intent, "ActionExecutor"),
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

                            return OrchestratedJobChatResponse(
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

        # === PHASE 2: Kanban subagent — Z1-01 sub-routing por intenção ===
        # Seleciona o subagente especializado com base no conteúdo da mensagem.
        try:
            from app.api.v1.agent_chat_ws import _subagent_for_kanban, _get_agent
            from app.shared.agents.agent_interface import AgentInput as ReactAgentInput

            _kanban_domain = _subagent_for_kanban(request.message)
            agent = _get_agent(_kanban_domain)
            if agent is None:
                # Fallback seguro: agente original completo
                from app.domains.recruiter_assistant.agents.kanban_react_agent import KanbanReActAgent
                agent = KanbanReActAgent()
                _kanban_domain = "kanban"

            agent_input = ReactAgentInput(
                message=request.message,
                session_id=conv_id,
                company_id=request.company_id or "default",
                user_id=request.user_id,
                context={
                    "job_context": request.job_context,
                    "candidates": request.candidates,
                    "selected_candidate_ids": request.selected_candidate_ids or [],
                },
            )

            output = await agent.process(agent_input)

            return OrchestratedJobChatResponse(
                success=True,
                content=output.message,
                agent_used=_kanban_domain,
                agents_consulted=[_kanban_domain],
                intent_detected="react_agent",
                confidence=output.confidence,
                structured_data=output.state_updates or None,
                suggested_prompts=extract_suggested_prompts("react_agent", "KanbanReActAgent"),
                actions=[{"type": a.action_type, "data": a.params} for a in output.actions] if output.actions else [],
                conversation_id=conv_id,
                needs_confirmation=any(a.requires_confirmation for a in output.actions) if output.actions else False,
                action_executed=bool(output.tool_results),
            )
        except Exception as react_error:
            logger.warning(f"[JobChat] ReAct agent failed, falling back to legacy: {react_error}")

        # === PHASE 3 (FALLBACK): Detect analytical queries and route through kanban assistant ===
        detected_cmd_type, cmd_confidence = detect_command_type(request.message)

        is_specific_analytical = detected_cmd_type in _ANALYTICAL_COMMAND_TYPES and detected_cmd_type != KanbanCommandType.ANALISE_GERAL.value
        if is_specific_analytical and cmd_confidence >= 0.3:
            try:
                from app.services.kanban_assistant_service import kanban_assistant_service
                kas_result = await kanban_assistant_service.process_command(
                    command=request.message,
                    command_type=detected_cmd_type,
                    job_context=request.job_context,
                    candidates=request.candidates,
                    selected_candidate_ids=request.selected_candidate_ids,
                )
                if kas_result.get("success") and kas_result.get("content"):
                    enriched = job_context_service.enrich_from_frontend_data(
                        job_context=request.job_context,
                        candidates=request.candidates,
                        selected_candidate_ids=request.selected_candidate_ids,
                    )
                    return OrchestratedJobChatResponse(
                        success=True,
                        content=kas_result["content"],
                        agent_used="KanbanAssistant",
                        agents_consulted=["KanbanAssistant"],
                        intent_detected=detected_cmd_type,
                        confidence=cmd_confidence,
                        structured_data=kas_result.get("structured_data"),
                        suggested_prompts=kas_result.get("follow_up_prompts", []),
                        actions=kas_result.get("suggested_actions", []),
                        conversation_id=conv_id,
                        ui_action=kas_result.get("ui_action"),
                        ui_action_params=kas_result.get("ui_action_params"),
                    )
            except Exception as e:
                logger.warning(f"KanbanAssistant analytical routing failed, falling back to orchestrator: {e}")

        # === PHASE 3b: Normal orchestrator processing (fallback) ===
        enriched = job_context_service.enrich_from_frontend_data(
            job_context=request.job_context,
            candidates=request.candidates,
            selected_candidate_ids=request.selected_candidate_ids
        )

        context_summary = build_enriched_context_summary(enriched)
        enhanced_message = f"{request.message}\n\n---\n{context_summary}"

        job_context_data = job_context_service.to_context_dict(enriched)

        context = {
            "job_id": enriched.job_id,
            "job_title": enriched.title,
            "current_job": enriched.job_id,
            "job_context": job_context_data.get("job"),
            "funnel_metrics": job_context_data.get("funnel"),
            "candidates_data": job_context_data.get("candidates"),
            "selected_candidates": request.selected_candidate_ids,
            "source": "job_chat",
            "enriched_context": True
        }

        result = await orch.process_request(
            user_id=request.user_id,
            message=enhanced_message,
            conversation_id=conv_id,
            context=context
        )

        agent_used = result.get("agent", "RecruiterAssistant")
        intent = result.get("intent", "analise_geral")
        confidence = result.get("confidence", 0.5)

        response_message = result.get("message", "")
        if not response_message and result.get("result"):
            response_message = result["result"].get("message", "")
        if not response_message:
            response_message = "Desculpe, não consegui processar sua solicitação. Por favor, tente novamente."

        suggested_prompts = extract_suggested_prompts(intent, agent_used)
        actions = extract_actions(enriched, intent)

        entities = result.get("result", {}).get("entities") if isinstance(result.get("result"), dict) else None
        if not entities:
            entities = result.get("entities", {})

        # === PHASE 4: Try closed-loop execution for actionable intents ===
        action_exec_result = await action_executor.try_execute(
            intent=intent,
            entities=entities or {},
            candidates_data=request.candidates,
            context={"conversation_id": conv_id, "user_id": request.user_id, **context},
        )

        if action_exec_result.status == "executed":
            return OrchestratedJobChatResponse(
                success=True,
                content=action_exec_result.message,
                agent_used=agent_used,
                agents_consulted=[agent_used, "ActionExecutor"],
                intent_detected=intent,
                confidence=confidence,
                suggested_prompts=suggested_prompts,
                actions=actions,
                conversation_id=result.get("conversation_id"),
                action_executed=True,
                action_result=action_exec_result.data,
                action_type=action_exec_result.action_type,
            )

        elif action_exec_result.status == "needs_params":
            pending_state = PendingActionState(
                pending_id=action_exec_result.pending_action_id or "",
                intent=intent,
                action_id=action_exec_result.action_type or "",
                domain_id=ACTIONABLE_INTENTS.get(intent, {}).get("domain_id", ""),
                collected_params=action_exec_result.data.get("collected_params", {}) if action_exec_result.data else {},
                missing_params=action_exec_result.missing_params or [],
                conversation_id=conv_id,
            )
            pending_action_store.save(conv_id, pending_state)

            return OrchestratedJobChatResponse(
                success=True,
                content=action_exec_result.message,
                agent_used=agent_used,
                agents_consulted=[agent_used, "ActionExecutor"],
                intent_detected=intent,
                confidence=confidence,
                suggested_prompts=[],
                actions=actions,
                conversation_id=result.get("conversation_id"),
                needs_params=True,
                pending_action_id=action_exec_result.pending_action_id,
            )

        elif action_exec_result.status == "needs_confirmation":
            pending_state = PendingActionState(
                pending_id=action_exec_result.pending_action_id or "",
                intent=intent,
                action_id=action_exec_result.action_type or "",
                domain_id=ACTIONABLE_INTENTS.get(intent, {}).get("domain_id", ""),
                collected_params=action_exec_result.data.get("collected_params", {}) if action_exec_result.data else {},
                missing_params=[],
                conversation_id=conv_id,
                awaiting_confirmation=True,
                confirmation_summary=action_exec_result.confirmation_summary,
            )
            pending_action_store.save(conv_id, pending_state)

            return OrchestratedJobChatResponse(
                success=True,
                content=action_exec_result.message,
                agent_used=agent_used,
                agents_consulted=[agent_used, "ActionExecutor"],
                intent_detected=intent,
                confidence=confidence,
                suggested_prompts=[],
                actions=actions,
                conversation_id=result.get("conversation_id"),
                needs_confirmation=True,
                pending_action_id=action_exec_result.pending_action_id,
            )

        # === PHASE 5: Fallback to UI action (backward compatible) ===
        ui_action, ui_action_params = get_ui_action_from_intent(intent, request.message, entities)

        if ui_action and ui_action_params and ui_action != "start_job_wizard":
            candidate_name = (ui_action_params.get("candidate_name") or "").lower().strip()
            if candidate_name and request.candidates:
                matched_ids = []
                for c in request.candidates:
                    c_name = (c.get("name") or "").lower().strip()
                    if candidate_name in c_name or c_name in candidate_name:
                        matched_ids.append(str(c.get("id", "")))
                if matched_ids:
                    ui_action_params["candidate_ids"] = matched_ids

        if ui_action == "start_job_wizard":
            response_message = "Entendi! Vou abrir o assistente de criação de vagas para você."

        return OrchestratedJobChatResponse(
            success=result.get("success", False),
            content=response_message,
            agent_used=agent_used,
            agents_consulted=[agent_used],
            intent_detected=intent,
            confidence=confidence,
            structured_data={
                "funnel_metrics": job_context_data.get("funnel"),
                "top_candidates": job_context_data.get("candidates", [])[:5]
            },
            suggested_prompts=suggested_prompts,
            actions=actions,
            conversation_id=result.get("conversation_id"),
            ui_action=ui_action,
            ui_action_params=ui_action_params,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Orchestrated job chat error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing job chat: {str(e)}"
        )


@router.get("/orchestrator/job-chat/intents")
async def get_job_chat_intents():
    """Get available intents and agent mappings for job chat."""
    return {
        "intents": [
            {
                "id": "criar_vaga",
                "description": "Criar uma nova vaga de recrutamento",
                "keywords": ["criar vaga", "nova vaga", "abrir vaga", "nova posição"],
                "agent": "JobPlanner",
                "ui_action": "start_job_wizard"
            },
            {
                "id": "ranking_candidatos",
                "description": "Ranking de candidatos por fit com a vaga",
                "keywords": ["melhores", "ranking", "top", "ordenar"],
                "agent": "AvaliadorWSI"
            },
            {
                "id": "analise_funil",
                "description": "Análise de métricas do funil de recrutamento",
                "keywords": ["funil", "pipeline", "métricas", "conversão"],
                "agent": "AnalistaFeedback"
            },
            {
                "id": "gargalos",
                "description": "Identificação de gargalos no processo",
                "keywords": ["gargalo", "problema", "travado", "parado"],
                "agent": "AnalistaFeedback"
            },
            {
                "id": "comparar_candidatos",
                "description": "Comparação detalhada entre candidatos",
                "keywords": ["comparar", "versus", "diferenças"],
                "agent": "AvaliadorWSI"
            },
            {
                "id": "candidatos_feedback",
                "description": "Candidatos que precisam de feedback",
                "keywords": ["feedback", "devolutiva", "retorno"],
                "agent": "AnalistaFeedback"
            },
            {
                "id": "perfil_candidato",
                "description": "Análise detalhada de perfil",
                "keywords": ["perfil", "resumo", "detalhes"],
                "agent": "TriagemCurricular"
            },
            {
                "id": "proximos_passos",
                "description": "Recomendações de próximos passos",
                "keywords": ["próximos passos", "sugestão", "recomendação"],
                "agent": "RecruiterAssistant"
            },
            {
                "id": "mover_candidato",
                "description": "Mover candidato para outra etapa do pipeline",
                "keywords": ["mover", "avançar", "mudar etapa", "aprovar", "reprovar", "rejeitar", "transferir"],
                "agent": "RecruiterAssistant",
                "ui_action": "move_candidate"
            }
        ]
    }
