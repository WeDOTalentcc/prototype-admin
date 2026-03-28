"""
WebSocket de Chat com Agentes — /ws/chat/{session_id}

Endpoint bidirecional para conversa em tempo real com os agentes LIA.

Protocolo de mensagens (JSON):
  Cliente → Servidor:
    { "type": "message", "content": "...", "context": {...}, "domain": "wizard" }
    { "type": "ping" }
    { "type": "abort" }

  Servidor → Cliente:
    { "type": "thinking" }          — agente iniciou processamento
    { "type": "token", "content": "..." }  — streaming de token (futuro)
    { "type": "message", "content": "...", "confidence": 0.9 }  — resposta final
    { "type": "error", "message": "..." }
    { "type": "pong" }

Arquitetura:
  WS → despachante de domínio → agente ReAct/LangGraph → resposta → WS

Auth: query param ?token=<jwt> ou header Authorization.
Multi-tenant: company_id extraído do JWT.
"""
import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from app.api.v1.ws_manager import ws_manager
from app.core.config import settings
from app.services.token_budget_service import (
    check_budget,
    get_plan_for_company,
    increment_usage,
)
from app.shared.prompt_injection import PromptInjectionGuard

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


def _strip_react_json(text: str) -> str:
    """Remove JSON bruto do ReAct loop, retornando apenas o campo 'response'."""
    if not text:
        return text
    stripped = text.strip()
    raw = stripped
    if stripped.startswith("```json"):
        raw = stripped.removeprefix("```json").strip()
        if raw.endswith("```"):
            raw = raw[:-3].strip()
    elif stripped.startswith("```"):
        raw = stripped.removeprefix("```").strip()
        if raw.endswith("```"):
            raw = raw[:-3].strip()
    if raw.startswith("{"):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict) and "response" in parsed:
                resp = parsed["response"]
                if resp:
                    return resp
                return "Desculpe, não consegui gerar uma resposta. Tente novamente."
        except (json.JSONDecodeError, ValueError):
            pass
    return text

# Timeout por mensagem (segundos) — evita travamento em agentes lentos
_AGENT_TIMEOUT = settings.LLM_TIMEOUT_SECONDS

# SEG-1: singleton de proteção contra injeção de prompt
_injection_guard = PromptInjectionGuard()


def _build_agent_input(
    content: str,
    context: Dict[str, Any],
    session_id: str,
    company_id: str,
    user_id: str,
    conversation_history: list,
):
    """Constrói AgentInput a partir dos dados da mensagem WS."""
    from app.shared.agents.agent_interface import AgentInput
    return AgentInput(
        message=content,
        context=context,
        session_id=session_id,
        company_id=company_id,
        user_id=user_id,
        conversation_history=conversation_history,
    )


def _subagent_for_kanban(message: str) -> str:
    """Z1-01: classifica mensagem kanban → subagente especializado.

    Retorna um de: kanban_action | kanban_insight | kanban_search
    Fail-safe: retorna "kanban" (agente original) se não conseguir classificar.
    """
    msg = message.lower()
    # Action: mutations, batch ops, communications
    _action_kw = (
        "mover", "aprovar", "reprovar", "rejeitar", "lote", "batch",
        "em massa", "triagem em lote", "relatório de pipeline", "prata da casa",
        "silver medalist", "backlog", "benchmark do recrutador", "fairness",
        "check_rejection", "comunicação em massa",
    )
    # Insight: analytics, predictions, bottlenecks
    _insight_kw = (
        "gargalo", "bottleneck", "previsão", "risco", "aging",
        "tempo na etapa", "analisar etapa", "comparar etapa",
        "sugerir movimentação", "journey metric", "predição",
        "identify_bottleneck", "at_risk", "pipeline_prediction",
    )
    if any(kw in msg for kw in _action_kw):
        return "kanban_action"
    if any(kw in msg for kw in _insight_kw):
        return "kanban_insight"
    # Default for kanban: read-only search (safer)
    return "kanban_search"


def _subagent_for_sourcing(message: str) -> str:
    """Z2-02: classifica mensagem sourcing → subagente especializado.

    Retorna um de: sourcing_engagement | sourcing_enrich | sourcing_search | sourcing_planner
    Fail-safe: retorna "sourcing" (agente original) se não conseguir classificar.
    """
    msg = message.lower()
    # Engagement: outreach, mensagem, rastreamento de resposta
    _engagement_kw = (
        "abordagem", "outreach", "enviar mensagem", "mensagem de contato",
        "contatar candidato", "rastrear resposta", "gerar mensagem",
    )
    # Enrich: análise, scoring, shortlist, comparação
    _enrich_kw = (
        "analisar perfil", "score", "shortlist", "comparar candidatos",
        "ranking", "avaliar perfil", "adicionar shortlist", "remover shortlist",
    )
    # Search: busca, filtrar, ver candidato
    _search_kw = (
        "busca de talentos", "talent search", "talent pool", "filtrar candidatos",
        "listar candidatos encontrados", "ver perfil do candidato",
        "boolean search", "busca booleana",
    )
    # Planner: critérios, parâmetros, skills
    _planner_kw = (
        "critérios de busca", "parâmetros de busca", "definir critérios",
        "configurar busca", "sugerir skills", "sugestão de skills",
    )
    if any(kw in msg for kw in _engagement_kw):
        return "sourcing_engagement"
    if any(kw in msg for kw in _enrich_kw):
        return "sourcing_enrich"
    if any(kw in msg for kw in _search_kw):
        return "sourcing_search"
    if any(kw in msg for kw in _planner_kw):
        return "sourcing_planner"
    # Default: search (leitura — mais seguro)
    return "sourcing_search"


def _subagent_for_pipeline(message: str) -> str:
    """Z1-02: classifica mensagem pipeline → subagente especializado.

    Retorna um de: pipeline_action | pipeline_decision | pipeline_context
    Fail-safe: retorna "pipeline_transition" (agente original) se falhar.
    """
    msg = message.lower()
    # Action: field updates, interview management, fairness
    _action_kw = (
        "atualizar candidato", "personalizar comunicação", "cancelar entrevista",
        "reagendar entrevista", "update_candidate", "personalize_communication",
        "fairness", "check_rejection",
    )
    # Decision: transitions, preferences, sub-status
    _decision_kw = (
        "validar transição", "sub-status", "preferências do recrutador",
        "coletar dados", "agendar tarefa secundária", "validate_transition",
        "suggest_sub_status", "recruiter_preference",
    )
    if any(kw in msg for kw in _action_kw):
        return "pipeline_action"
    if any(kw in msg for kw in _decision_kw):
        return "pipeline_decision"
    # Default for pipeline: read-only context (safer)
    return "pipeline_context"


def _get_agent(domain: str) -> Optional[Any]:
    """Retorna instância do agente para o domínio solicitado."""
    try:
        if domain == "wizard":
            from app.domains.job_management.agents.wizard_react_agent import WizardReActAgent
            return WizardReActAgent()
        elif domain in ("pipeline", "cv_screening"):
            from app.domains.cv_screening.agents.pipeline_react_agent import PipelineReActAgent
            return PipelineReActAgent()
        elif domain == "sourcing":
            from app.domains.sourcing.agents.sourcing_react_agent import SourcingReActAgent
            return SourcingReActAgent()
        # Z2-02: Sourcing subagents
        elif domain == "sourcing_planner":
            from app.domains.sourcing.agents.sourcing_planner_agent import SourcingPlannerAgent
            return SourcingPlannerAgent()
        elif domain == "sourcing_search":
            from app.domains.sourcing.agents.sourcing_search_agent import SourcingSearchAgent
            return SourcingSearchAgent()
        elif domain == "sourcing_enrich":
            from app.domains.sourcing.agents.sourcing_enrich_agent import SourcingEnrichAgent
            return SourcingEnrichAgent()
        elif domain == "sourcing_engagement":
            from app.domains.sourcing.agents.sourcing_engagement_agent import SourcingEngagementAgent
            return SourcingEngagementAgent()
        elif domain == "talent":
            from app.domains.recruiter_assistant.agents.talent_react_agent import TalentReActAgent
            return TalentReActAgent()
        elif domain == "kanban":
            from app.domains.recruiter_assistant.agents.kanban_react_agent import KanbanReActAgent
            return KanbanReActAgent()
        # Z1-01: Kanban subagents
        elif domain == "kanban_search":
            from app.domains.recruiter_assistant.agents.kanban_search_agent import KanbanSearchAgent
            return KanbanSearchAgent()
        elif domain == "kanban_insight":
            from app.domains.recruiter_assistant.agents.kanban_insight_agent import KanbanInsightAgent
            return KanbanInsightAgent()
        elif domain == "kanban_action":
            from app.domains.recruiter_assistant.agents.kanban_action_agent import KanbanActionAgent
            return KanbanActionAgent()
        elif domain in ("jobs_management", "jobs_mgmt"):
            from app.domains.recruiter_assistant.agents.jobs_mgmt_react_agent import JobsManagementReActAgent
            return JobsManagementReActAgent()
        elif domain == "policy":
            from app.domains.hiring_policy.agents.policy_react_agent import PolicyReActAgent
            return PolicyReActAgent()
        elif domain == "pipeline_transition":
            from app.domains.pipeline.agents.pipeline_transition_agent import PipelineTransitionAgent
            return PipelineTransitionAgent()
        # Z1-02: Pipeline subagents
        elif domain == "pipeline_context":
            from app.domains.pipeline.agents.pipeline_context_agent import PipelineContextAgent
            return PipelineContextAgent()
        elif domain == "pipeline_decision":
            from app.domains.pipeline.agents.pipeline_decision_agent import PipelineDecisionAgent
            return PipelineDecisionAgent()
        elif domain == "pipeline_action":
            from app.domains.pipeline.agents.pipeline_action_agent import PipelineActionAgent
            return PipelineActionAgent()
        elif domain == "analytics":
            from app.domains.analytics.agents.analytics_react_agent import AnalyticsReActAgent
            return AnalyticsReActAgent()
        elif domain in ("communication", "comms"):
            from app.domains.communication.agents.communication_react_agent import CommunicationReActAgent
            return CommunicationReActAgent()
        elif domain in ("ats_integration", "ats"):
            from app.domains.ats_integration.agents.ats_integration_react_agent import ATSIntegrationReActAgent
            return ATSIntegrationReActAgent()
        else:
            # Fallback: recruiter assistant (talent)
            from app.domains.recruiter_assistant.agents.talent_react_agent import TalentReActAgent
            return TalentReActAgent()
    except Exception as exc:
        logger.error("[AgentChatWS] Falha ao carregar agente domain=%s: %s", domain, exc)
        return None


def _extract_auth(token: Optional[str]) -> Dict[str, Any]:
    """Extrai company_id e user_id do JWT (best-effort, sem bloquear WS)."""
    if not token:
        return {"company_id": "", "user_id": "anonymous"}
    try:
        import jwt as pyjwt
        payload = pyjwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return {
            "company_id": str(payload.get("company_id") or payload.get("organization_id") or ""),
            "user_id": str(payload.get("sub") or payload.get("user_id") or "anonymous"),
        }
    except Exception:
        return {"company_id": "", "user_id": "anonymous"}


@router.websocket("/ws/chat/{session_id}")
async def agent_chat_ws(
    websocket: WebSocket,
    session_id: str,
    token: Optional[str] = Query(None),
    domain: str = Query("recruiter_assistant"),
):
    """
    WebSocket bidirecional para chat com agentes LIA.

    Parâmetros:
    - session_id: ID único da sessão de chat
    - token: JWT para autenticação (query param)
    - domain: domínio do agente alvo (query param)
    """
    auth = _extract_auth(token)
    company_id = auth["company_id"]
    user_id = auth["user_id"]

    connected = await ws_manager.connect(websocket, session_id, company_id or "anonymous")
    if not connected:
        return

    conversation_history: list = []

    try:
        await ws_manager.send_to_session(session_id, {
            "type": "connected",
            "session_id": session_id,
            "domain": domain,
        })

        while True:
            try:
                raw = await asyncio.wait_for(websocket.receive_text(), timeout=300.0)
            except asyncio.TimeoutError:
                # Ping de keepalive
                await ws_manager.send_to_session(session_id, {"type": "ping"})
                continue

            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await ws_manager.send_to_session(session_id, {
                    "type": "error", "message": "JSON inválido"
                })
                continue

            msg_type = msg.get("type", "message")

            if msg_type == "ping":
                await ws_manager.send_to_session(session_id, {"type": "pong"})
                continue

            if msg_type == "abort":
                break

            # HITL — recebe resposta de aprovação humana via WS
            if msg_type == "approval_response":
                try:
                    from app.services.hitl_service import hitl_service
                    ws_thread_id = msg.get("thread_id", "")
                    ws_pending_id = msg.get("pending_id", "")
                    ws_approved = bool(msg.get("approved", False))
                    ws_comment = msg.get("comment")
                    await hitl_service.receive_approval(
                        thread_id=ws_thread_id,
                        pending_id=ws_pending_id,
                        approved=ws_approved,
                        comment=ws_comment,
                    )
                    await ws_manager.send_to_session(session_id, {
                        "type": "approval_confirmed",
                        "thread_id": ws_thread_id,
                        "pending_id": ws_pending_id,
                    })

                    # ── Resume grafo após aprovação ───────────────────────────
                    resume_info = await hitl_service.get_resume_info(ws_thread_id)
                    if resume_info:
                        resume_domain = resume_info.get("domain", "")
                        resume_input_dict = resume_info.get("agent_input", {})
                        if ws_approved and resume_domain and resume_input_dict:
                            # Re-invocar agente com hitl_approved=True no context
                            resume_context = resume_input_dict.get("context", {})
                            resume_context["hitl_approved"] = True
                            resume_input_dict["context"] = resume_context

                            await ws_manager.send_to_session(session_id, {"type": "thinking"})
                            try:
                                # cv_screening (WSI) usa ainvoke(None) direto — grafo pausado
                                if resume_domain == "cv_screening":
                                    from app.domains.cv_screening.agents.wsi_interview_graph import WSIInterviewGraph
                                    wsi_g = WSIInterviewGraph()
                                    if wsi_g._compiled_lg is None:
                                        wsi_g._compiled_lg = wsi_g._build_langgraph()
                                    _wsi_config = {"configurable": {"thread_id": ws_thread_id}}
                                    _wsi_result = await asyncio.wait_for(
                                        wsi_g._compiled_lg.ainvoke(None, config=_wsi_config),
                                        timeout=_AGENT_TIMEOUT,
                                    )
                                    _wsi_data = _wsi_result.get("wsi_data", {}) if isinstance(_wsi_result, dict) else {}
                                    _wsi_msg = _wsi_data.get("feedback", _wsi_data.get("final_message", "Avaliação WSI concluída."))
                                    await ws_manager.send_to_session(session_id, {
                                        "type": "message",
                                        "content": _wsi_msg,
                                        "confidence": 0.95,
                                        "actions": [],
                                        "domain": "cv_screening",
                                        "source": "hitl_resume",
                                    })
                                    conversation_history.append({"role": "assistant", "content": _wsi_msg})
                                # wizard (JobWizardGraph) usa ainvoke(None) direto — grafo pausado
                                elif resume_domain == "wizard":
                                    from app.domains.job_management.agents.job_wizard_graph import JobWizardGraph
                                    wiz_g = JobWizardGraph()
                                    if wiz_g._compiled_lg is None:
                                        wiz_g._compiled_lg = wiz_g._build_langgraph()
                                    _wiz_config = {"configurable": {"thread_id": ws_thread_id}}
                                    _wiz_result = await asyncio.wait_for(
                                        wiz_g._compiled_lg.ainvoke(None, config=_wiz_config),
                                        timeout=_AGENT_TIMEOUT,
                                    )
                                    _wiz_msg = (
                                        _wiz_result.get("response", "") or
                                        _wiz_result.get("user_message", "Vaga criada com sucesso.")
                                        if isinstance(_wiz_result, dict) else "Vaga criada com sucesso."
                                    )
                                    _wiz_msg = _strip_react_json(_wiz_msg)
                                    await ws_manager.send_to_session(session_id, {
                                        "type": "message",
                                        "content": _wiz_msg,
                                        "confidence": 0.95,
                                        "actions": [],
                                        "domain": "wizard",
                                        "source": "hitl_resume",
                                    })
                                    conversation_history.append({"role": "assistant", "content": _wiz_msg})
                                else:
                                    resume_agent = _get_agent(resume_domain)
                                    if resume_agent:
                                        from app.shared.agents.agent_interface import AgentInput
                                        resume_agent_input = AgentInput(
                                            message=resume_input_dict.get("message", ""),
                                            context=resume_context,
                                            session_id=resume_input_dict.get("session_id", session_id),
                                            company_id=resume_input_dict.get("company_id", company_id),
                                            user_id=resume_input_dict.get("user_id", user_id),
                                            conversation_history=resume_input_dict.get("conversation_history", []),
                                        )
                                        resume_output = await asyncio.wait_for(
                                            resume_agent.process(resume_agent_input),
                                            timeout=_AGENT_TIMEOUT,
                                        )
                                        _resume_clean = _strip_react_json(resume_output.message or "")
                                        await ws_manager.send_to_session(session_id, {
                                            "type": "message",
                                            "content": _resume_clean,
                                            "confidence": resume_output.confidence,
                                            "actions": [a.dict() for a in (resume_output.actions or [])],
                                            "domain": resume_domain,
                                            "source": "hitl_resume",
                                        })
                                        conversation_history.append({"role": "user", "content": "[HITL aprovado]"})
                                        conversation_history.append({"role": "assistant", "content": _resume_clean})
                            except Exception as _resume_exc:
                                logger.error("[AgentChatWS] HITL resume falhou: %s", _resume_exc)
                                await ws_manager.send_to_session(session_id, {
                                    "type": "error",
                                    "message": "Erro ao retomar execução após aprovação.",
                                })
                        elif not ws_approved:
                            # Rejeitado — notificar usuário
                            await ws_manager.send_to_session(session_id, {
                                "type": "message",
                                "content": "Ação cancelada pelo aprovador. Nenhuma alteração foi feita.",
                                "domain": resume_domain or domain,
                                "source": "hitl_rejected",
                            })

                            # SEG-5: AuditService — registrar rejeição HITL
                            try:
                                from app.shared.compliance.audit_service import audit_service, PROTECTED_CRITERIA
                                _rejected_candidate_id = str(
                                    resume_input_dict.get("context", {}).get("candidate_id", "")
                                    if resume_input_dict else ""
                                )
                                await audit_service.log_decision(
                                    company_id=str(company_id or ""),
                                    agent_name="hitl_ws",
                                    decision_type="move_stage",
                                    action=f"hitl_rejected:{resume_domain or domain}",
                                    decision="rejected",
                                    reasoning=["Ação rejeitada pelo aprovador humano via WebSocket HITL"],
                                    criteria_used=[resume_domain or domain],
                                    candidate_id=_rejected_candidate_id or None,
                                    human_review_required=False,
                                    criteria_ignored=list(PROTECTED_CRITERIA),
                                )
                            except Exception as _audit_rej_exc:
                                logger.debug(
                                    "[AgentChatWS][SEG-5] AuditService HITL rejected skipped: %s",
                                    _audit_rej_exc,
                                )

                except Exception as _hitl_exc:
                    logger.warning("[AgentChatWS] HITL approval_response falhou: %s", _hitl_exc)
                    await ws_manager.send_to_session(session_id, {
                        "type": "error",
                        "message": "Erro ao processar resposta de aprovação.",
                    })
                continue

            if msg_type != "message":
                continue

            content = msg.get("content", "").strip()
            if not content:
                continue

            # SEG-1: verificação de injeção de prompt antes de qualquer processamento
            _inj_result = _injection_guard.check(content)
            if _inj_result.risk_level == "high":
                logger.warning(
                    "[AgentChatWS][SEG-1] Injeção de prompt bloqueada session=%s "
                    "patterns=%s confidence=%.2f",
                    session_id, _inj_result.matched_patterns, _inj_result.confidence,
                )
                await ws_manager.send_to_session(session_id, {
                    "type": "error",
                    "message": "Mensagem bloqueada por segurança. Por favor, reformule sua solicitação.",
                    "error_code": "prompt_injection_blocked",
                })
                continue
            elif _inj_result.risk_level == "medium":
                logger.info(
                    "[AgentChatWS][SEG-1] Injeção de prompt suspeita (medium) session=%s "
                    "patterns=%s — prosseguindo com log",
                    session_id, _inj_result.matched_patterns,
                )

            context = msg.get("context", {})
            context.setdefault("company_id", company_id)
            context.setdefault("user_id", user_id)
            active_domain = msg.get("domain", domain)

            # Indicar que está processando
            await ws_manager.send_to_session(session_id, {"type": "thinking"})

            # Roteamento via CascadedRouter (Fase 2 — Gap #2)
            # Verifica se o domínio precisa de clarificação antes de invocar agente
            if active_domain in ("auto", "recruiter_assistant", ""):
                try:
                    from app.orchestrator.cascaded_router import CascadedRouter
                    _router = CascadedRouter()
                    route = await _router.route(
                        message=content,
                        context=context,
                        session_id=session_id,
                    )
                    if route.needs_clarification:
                        await ws_manager.send_to_session(session_id, {
                            "type": "clarification",
                            "question": route.clarification_question,
                            "options": route.clarification_options,
                            "session_id": session_id,
                        })
                        continue  # Não chamar agente até o usuário responder

                    # Domínio resolvido pelo router
                    active_domain = route.domain_id
                except Exception as _route_exc:
                    logger.debug(
                        "[AgentChatWS] CascadedRouter skipped, usando domain original: %s", _route_exc
                    )

            # Z1/Z2: sub-rotear kanban/pipeline/sourcing para subagentes especializados
            if active_domain == "kanban":
                active_domain = _subagent_for_kanban(content)
                logger.debug("[AgentChatWS][Z1] kanban → %s", active_domain)
            elif active_domain == "pipeline_transition":
                active_domain = _subagent_for_pipeline(content)
                logger.debug("[AgentChatWS][Z1] pipeline_transition → %s", active_domain)
            elif active_domain == "sourcing":
                active_domain = _subagent_for_sourcing(content)
                logger.debug("[AgentChatWS][Z2] sourcing → %s", active_domain)

            agent = _get_agent(active_domain)
            if agent is None:
                await ws_manager.send_to_session(session_id, {
                    "type": "error",
                    "message": f"Agente '{active_domain}' indisponível.",
                })
                continue

            # E7: injeta streaming_callback no context antes de construir agent_input
            async def _thinking_callback_pre(event: dict) -> None:
                """Retransmite evento thinking do ReAct loop para o cliente WebSocket."""
                try:
                    await ws_manager.send_to_session(session_id, {
                        "type": "thinking",
                        "content": event.get("thought", ""),
                        "step": event.get("step", 0),
                    })
                except Exception:
                    pass  # fail-silent
            context["streaming_callback"] = _thinking_callback_pre

            agent_input = _build_agent_input(
                content=content,
                context=context,
                session_id=session_id,
                company_id=company_id,
                user_id=user_id,
                conversation_history=conversation_history[-10:],
            )

            # Verifica se o domínio exige execução assíncrona (evita timeout WS)
            try:
                from app.shared.messaging.celery_config import is_async_domain
                from app.shared.messaging.dispatchers import domain_dispatcher
                from app.shared.messaging.message_schemas import AgentChatMessage

                if is_async_domain(active_domain) and await domain_dispatcher.is_available():
                    # Domínio assíncrono — despacha via RabbitMQ + Celery
                    chat_msg = AgentChatMessage(
                        session_id=session_id,
                        user_id=user_id,
                        company_id=company_id,
                        domain=active_domain,
                        message=content,
                        context=context,
                        conversation_history=conversation_history[-10:],
                    )
                    job_id = await domain_dispatcher.dispatch(chat_msg)
                    await ws_manager.send_to_session(session_id, {
                        "type": "thinking",
                        "job_id": job_id,
                        "message": "Processando em background...",
                    })
                    # Resultado chegará via rabbitmq_consumer → ws_manager.send_to_session()
                    continue
            except Exception as _dispatch_exc:
                logger.debug(
                    "[AgentChatWS] Dispatch async falhou, executando síncronamente: %s", _dispatch_exc
                )

            # ── Token Budget check (André R6) ─────────────────────────────
            # Verificar antes de chamar LLM. Falha silenciosa = permite.
            try:
                _plan = await get_plan_for_company(company_id)
                _budget_ok, _used, _limit = await check_budget(company_id, _plan)
                if not _budget_ok:
                    await ws_manager.send_to_session(session_id, {
                        "type": "error",
                        "message": (
                            f"Limite diário de uso de IA atingido ({_used:,} / {_limit:,} tokens). "
                            "O budget será renovado à meia-noite UTC."
                        ),
                        "error_code": "budget_exhausted",
                    })
                    continue
            except Exception as _budget_exc:
                logger.warning("[AgentChatWS] Budget check falhou — continuando: %s", _budget_exc)

            # Execução síncrona (domínio sync ou RabbitMQ indisponível)
            try:
                output = await asyncio.wait_for(
                    agent.process(agent_input),
                    timeout=_AGENT_TIMEOUT,
                )

                # ── Registrar consumo de tokens (André R6) ────────────────
                _tokens_used = output.metadata.get("tokens_used", 0) if output.metadata else 0
                if _tokens_used <= 0:
                    # Estimativa conservadora: ~1.3 tokens por palavra (BPE avg)
                    _input_words = len(content.split())
                    _output_words = len((output.message or "").split())
                    _tokens_used = int((_input_words + _output_words) * 1.3)
                if _tokens_used > 0 and company_id:
                    try:
                        await increment_usage(company_id, _tokens_used)
                    except Exception as _inc_exc:
                        logger.warning("[AgentChatWS] increment_usage falhou: %s", _inc_exc)

                clean_message = _strip_react_json(output.message or "")
                conversation_history.append({"role": "user", "content": content})
                conversation_history.append({"role": "assistant", "content": clean_message})

                # FAR-3: incluir soft_warnings de fairness na resposta ao cliente
                _fairness_warnings = (output.metadata or {}).get("fairness_warnings", [])
                _ws_payload: Dict[str, Any] = {
                    "type": "message",
                    "content": clean_message,
                    "confidence": output.confidence,
                    "actions": [a.dict() for a in (output.actions or [])],
                    "navigation": output.navigation.dict() if output.navigation else None,
                    "state_updates": output.state_updates or {},
                    "domain": active_domain,
                    "source": "direct",
                }
                if _fairness_warnings:
                    _ws_payload["fairness_warnings"] = _fairness_warnings
                await ws_manager.send_to_session(session_id, _ws_payload)

            except asyncio.TimeoutError:
                await ws_manager.send_to_session(session_id, {
                    "type": "error",
                    "message": "Tempo limite de processamento excedido. Tente novamente.",
                })
            except Exception as exc:
                logger.error("[AgentChatWS] Erro no agente session=%s: %s", session_id, exc, exc_info=True)
                await ws_manager.send_to_session(session_id, {
                    "type": "error",
                    "message": "Erro interno ao processar sua mensagem.",
                })

    except WebSocketDisconnect:
        logger.info("[AgentChatWS] Desconectado session=%s", session_id)
    except Exception as exc:
        logger.error("[AgentChatWS] Erro inesperado session=%s: %s", session_id, exc)
    finally:
        ws_manager.disconnect(session_id)
        # Remove subscription de resposta RabbitMQ para esta sessão
        try:
            from app.shared.messaging.rabbitmq_consumer import rabbitmq_consumer
            await rabbitmq_consumer.unsubscribe_session(session_id)
        except Exception:
            pass


class HTTPChatRequest(BaseModel):
    message: str
    domain: str = ""
    session_id: str = ""
    context: Dict[str, Any] = {}

    class Config:
        from_attributes = True


class HTTPChatResponse(BaseModel):
    content: str
    confidence: float = 0.0
    domain: str = ""
    actions: list = []
    error: Optional[str] = None


@router.post("/chat/message", response_model=HTTPChatResponse)
async def http_chat_message(req: HTTPChatRequest, request: Request):
    """
    HTTP fallback for agent chat when WebSocket is unavailable.
    Same logic as WS handler but synchronous request/response.
    """
    content = req.message.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    auth_header = request.headers.get("authorization", "")
    token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else None
    auth = _extract_auth(token)
    company_id = auth["company_id"]
    user_id = auth["user_id"]

    session_id = req.session_id or str(uuid4())
    active_domain = req.domain or "recruiter_assistant"
    context = req.context or {}
    context.setdefault("company_id", company_id)
    context.setdefault("user_id", user_id)

    _inj_result = _injection_guard.check(content)
    if _inj_result.risk_level == "high":
        return HTTPChatResponse(
            content="Mensagem bloqueada por segurança. Por favor, reformule sua solicitação.",
            error="prompt_injection_blocked",
        )

    try:
        _plan = await get_plan_for_company(company_id)
        _budget_ok, _used, _limit = await check_budget(company_id, _plan)
        if not _budget_ok:
            return HTTPChatResponse(
                content=f"Limite diário de uso de IA atingido ({_used:,} / {_limit:,} tokens). O budget será renovado à meia-noite UTC.",
                error="budget_exhausted",
            )
    except Exception as _budget_exc:
        logger.warning("[HTTPChat] Budget check falhou — continuando: %s", _budget_exc)

    if active_domain in ("auto", "recruiter_assistant", ""):
        try:
            from app.orchestrator.cascaded_router import CascadedRouter
            _router = CascadedRouter()
            route = await _router.route(
                message=content, context=context, session_id=session_id,
            )
            if not route.needs_clarification:
                active_domain = route.domain_id
        except Exception:
            pass

    # Z1/Z2: sub-rotear kanban/pipeline/sourcing para subagentes especializados
    if active_domain == "kanban":
        active_domain = _subagent_for_kanban(content)
        logger.debug("[HTTPChat][Z1] kanban → %s", active_domain)
    elif active_domain == "pipeline_transition":
        active_domain = _subagent_for_pipeline(content)
        logger.debug("[HTTPChat][Z1] pipeline_transition → %s", active_domain)
    elif active_domain == "sourcing":
        active_domain = _subagent_for_sourcing(content)
        logger.debug("[HTTPChat][Z2] sourcing → %s", active_domain)

    agent = _get_agent(active_domain)
    if agent is None:
        return HTTPChatResponse(
            content=f"Agente '{active_domain}' indisponível.",
            error="agent_unavailable",
        )

    agent_input = _build_agent_input(
        content=content, context=context, session_id=session_id,
        company_id=company_id, user_id=user_id, conversation_history=[],
    )

    try:
        output = await asyncio.wait_for(
            agent.process(agent_input), timeout=_AGENT_TIMEOUT,
        )

        _tokens_used = output.metadata.get("tokens_used", 0) if output.metadata else 0
        if _tokens_used <= 0:
            _input_words = len(content.split())
            _output_words = len((output.message or "").split())
            _tokens_used = int((_input_words + _output_words) * 1.3)
        if _tokens_used > 0 and company_id:
            try:
                await increment_usage(company_id, _tokens_used)
            except Exception as _inc_exc:
                logger.warning("[HTTPChat] increment_usage falhou: %s", _inc_exc)

        return HTTPChatResponse(
            content=_strip_react_json(output.message or ""),
            confidence=output.confidence,
            domain=active_domain,
            actions=[a.dict() for a in (output.actions or [])],
        )
    except asyncio.TimeoutError:
        return HTTPChatResponse(
            content="Tempo limite de processamento excedido. Tente novamente.",
            error="timeout",
        )
    except Exception as exc:
        logger.error("[HTTPChat] Erro: %s", exc, exc_info=True)
        return HTTPChatResponse(
            content="Erro interno ao processar sua mensagem.",
            error="internal_error",
        )
