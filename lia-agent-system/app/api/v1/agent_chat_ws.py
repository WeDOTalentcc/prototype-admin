"""
WebSocket de Chat com Agentes — /api/v1/ws/chat/{session_id}

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
    { "type": "panel_update", "panel_type": "...", "panel_data": {...}, "panel_title": "...", "action": "open|update|close" }
    { "type": "background_task_update", "task_id": "...", "task_type": "sourcing|screening|communication|analysis", "label": "...", "status": "running|completed|failed", "progress": 0-100, "message": "..." }
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
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from app.api.v1.ws_manager import ws_manager, get_ws_manager, WSManager
from app.core.config import settings
from app.shared.observability.token_budget_service import (
    check_budget,
    get_plan_for_company,
    increment_usage,
)
from app.shared.chat_event_serializer import (
    serialize_background_task_update,
    serialize_error,
    serialize_message,
    serialize_panel_update,
    serialize_thinking,
)
from app.shared.prompt_injection import PromptInjectionGuard
from app.shared.robustness.security_patterns import check_input_security, get_block_response
from app.shared.compliance.fairness_guard import FairnessGuard
from app.shared.compliance.c3b_layer import pre_compliance, post_compliance, ComplianceContext
from app.shared.tenant_session import create_session_id
from app.core.tenant import normalize_demo_company_id

_EMPTY_AGENT_RESPONSE_MESSAGE = (
    "Desculpe, não consegui gerar uma resposta para essa mensagem. "
    "Pode reformular ou tentar novamente?"
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


def _strip_thought_tags(text: str) -> str:
    """Remove <thought>...</thought> XML tags from LLM output."""
    import re
    cleaned = re.sub(r'<thought>[\s\S]*?</thought>', '', text, flags=re.IGNORECASE)
    cleaned = re.sub(r'<thought>[\s\S]*', '', cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def _strip_react_json(text: str) -> str:
    """Remove JSON bruto do ReAct loop, retornando apenas o campo 'response'."""
    if not text:
        return text
    text = _strip_thought_tags(text)
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

async def send_panel_update(
    session_id: str,
    panel_type: str,
    panel_data: dict[str, Any],
    panel_title: str = "",
    action: str = "open",
) -> None:
    """Send a panel_update event to the frontend via WebSocket.

    panel_type: one of calibration, candidate_review, profile, job_creation, scheduling
    action: "open" | "update" | "close"
    """
    try:
        await ws_manager.send_to_session(
            session_id,
            serialize_panel_update(
                panel_type=panel_type,
                panel_data=panel_data,
                panel_title=panel_title,
                action=action,
            ),
        )
    except Exception as exc:
        logger.debug("[AgentChatWS] panel_update send failed: %s", exc)


async def send_background_task_update(
    session_id: str,
    task_id: str,
    task_type: str,
    label: str,
    status: str,
    progress: int | None = None,
    message: str = "",
    result: dict[str, Any] | None = None,
) -> None:
    """Send a background_task_update event to the frontend via WebSocket.

    task_type: one of sourcing, screening, communication, analysis
    status: "running" | "completed" | "failed"
    progress: 0-100 (optional, only for running tasks)
    """
    try:
        await ws_manager.send_to_session(
            session_id,
            serialize_background_task_update(
                task_id=task_id,
                task_type=task_type,
                label=label,
                status=status,
                progress=progress,
                message=message,
                result=result,
            ),
        )
    except Exception as exc:
        logger.debug("[AgentChatWS] background_task_update send failed: %s", exc)


@router.get("/sessions/active", response_model=None)
async def list_active_sessions(
    request: Request,
    authorization: str = Header(default=""),
    token: str = Query(default=""),
    ws_mgr: WSManager = Depends(get_ws_manager),
):
    """List active WebSocket sessions for the authenticated user.

    Returns only session IDs belonging to the current user, not all
    sessions in the company/tenant.
    """
    jwt_token = token or (authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else "")
    auth = _extract_auth(jwt_token)
    user_id = auth.get("user_id", "")
    if not user_id or user_id == "anonymous":
        raise HTTPException(status_code=401, detail="Token required")

    session_ids = list(ws_mgr.get_user_sessions(user_id))
    return {
        "sessions": [
            {"id": sid, "active": True}
            for sid in session_ids
        ],
        "count": len(session_ids),
    }


# Timeout por mensagem (segundos) — evita travamento em agentes lentos
_AGENT_TIMEOUT = settings.LLM_TIMEOUT_SECONDS

# SEG-1: singleton de proteção contra injeção de prompt
_injection_guard = PromptInjectionGuard()
_fairness_guard = FairnessGuard()  # Item 4: inline FairnessGuard for WS


def _build_agent_input(
    content: str,
    context: dict[str, Any],
    session_id: str,
    company_id: str,
    user_id: str,
    conversation_history: list,
):
    """Constroì AgentInput a partir dos dados da mensagem WS."""
    from lia_agents_core.agent_interface import AgentInput
    # LIA-CTX-01: inject company_id so domain agents never ask the user for it.
    ctx = dict(context)
    if company_id and not ctx.get("tenant_context_snippet"):
        ctx["tenant_context_snippet"] = (
            "Empresa autenticada: company_id=" + company_id + ". "
            "Nao peca ao usuario o ID da empresa - ja esta disponivel no contexto."
        )
    ctx.setdefault("company_id", company_id)
    ctx.setdefault("user_id", user_id)
    return AgentInput(
        message=content,
        context=ctx,
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


def _get_agent(
    domain: str,
    *,
    company_id: str | int | None = None,
    session_id: str | None = None,
    user_id: str | int | None = None,
) -> Any | None:
    """Retorna instancia do agente para o dominio solicitado.

    Fase 3a (Wave 2): Delegates to AgentRegistry. The 21-branch if/elif
    was replaced — each agent class is decorated with @register_agent(id).
    Fallback to "talent" preserved for unknown domain.

    Task #861 (N-07): Each call emits a `wizard.agent_chat.get_agent` span so
    the WS dispatcher path is debuggable in OTLP. Callers should pass
    `company_id`/`session_id`/`user_id` so the span carries the canonical
    tenant attributes — they default to empty strings when missing, and the
    surrounding gate (`validate_span_attributes`) flags such cases in CI.
    """
    from app.orchestrator._observability import WIZARD_SPANS
    from app.shared.observability.tracing import finish_span, get_tracer

    tracer = get_tracer()
    attrs = {
        "service.name": "wizard",
        "wizard.graph": "agent_chat",
        "wizard.stage": "get_agent",
        "domain": str(domain or ""),
        "tenant.company_id": str(company_id or ""),
        "user.id": str(user_id or ""),
        "conversation.id": str(session_id or ""),
        "orchestrator.version": "wizard",
    }
    span = tracer.create_span(
        WIZARD_SPANS.AGENT_CHAT_GET_AGENT, attributes=attrs, _start_otel=True,
    )
    try:
        # Trigger agent module imports (one-time, idempotent) so decorators run.
        # Each import registers the class in AgentRegistry.
        _ensure_agents_loaded()

        from app.shared.agents.agent_registry import AgentRegistry
        agent = AgentRegistry().get_or_fallback(domain, fallback_id="talent")
        span.set_attribute(
            "agent.resolved_id", type(agent).__name__ if agent is not None else "",
        )
        finish_span(span, status="ok")
        return agent
    except Exception as exc:
        logger.error("[AgentChatWS] Falha ao carregar agente domain=%s: %s", domain, exc)
        finish_span(span, status="error", error=exc)
        return None


_AGENTS_LOADED = False


def _resume_wizard_canonical(
    thread_id: str,
    resume_input_dict: dict,
) -> tuple[str, dict]:
    """Resume a paused JobCreationGraph after HITL approval.

    Task #850: this replaces the legacy `wiz_g._graph.ainvoke(None, ...)`
    pattern that read response from `response`/`user_message` keys
    (which JobCreationGraph does not emit). We now:

      1. Pull `prior_state` from the LangGraph checkpointer.
      2. Merge recruiter approval payload + `hitl_approved=True` flag.
      3. Call the canonical `JobCreationGraph.resume(thread_id, prior,
         updates)` so the audit callback stays wired.
      4. Extract recruiter-facing message from the canonical
         `ws_stage_payload.data` with stage-aware fallback.

    Returns:
        (message, ws_stage_payload) — both safe to pass directly to the
        WS layer. `ws_stage_payload` may be empty dict if the resumed
        node didn't emit one.
    """
    from app.domains.job_creation.graph import job_creation_graph as wiz_g

    config = {"configurable": {"thread_id": thread_id}}
    try:
        prior_snapshot = wiz_g._graph.get_state(config)
        prior_state = dict(prior_snapshot.values or {})
    except Exception:  # checkpointer miss — fall back to empty seed
        prior_state = {}

    resume_context = (resume_input_dict or {}).get("context") or {}
    approval_payload = (resume_input_dict or {}).get("approval_payload") or {}
    updates: dict = {
        "hitl_approved": True,
        **approval_payload,
    }
    # Carry recruiter context (e.g. updated draft fields) if the HITL
    # step accumulated any — keeps the canonical domain contract.
    if isinstance(resume_context, dict):
        for k in ("draft", "intake_payload", "jd_enriched", "wsi_questions"):
            if k in resume_context and resume_context[k] is not None:
                updates[k] = resume_context[k]

    result = wiz_g.resume(thread_id, prior_state, updates)

    if not isinstance(result, dict):
        return ("Vaga atualizada após aprovação.", {})

    stage_payload = result.get("ws_stage_payload") or {}
    stage_data = stage_payload.get("data") or {}
    current_stage = result.get("current_stage", "") or ""
    message = (
        stage_data.get("message")
        or stage_data.get("response_text")
        or {
            "intake": "Captei a vaga. Vou seguir para o próximo passo.",
            "jd_enrichment": "Descrição da vaga enriquecida — preciso da sua aprovação.",
            "wsi_questions": "Perguntas de triagem WSI sugeridas — preciso da sua aprovação.",
            "completed": "Vaga criada com sucesso.",
        }.get(current_stage, f"Etapa atual: {current_stage or 'wizard'}.")
    )
    return (message, stage_payload)


async def _resume_wizard_canonical_streaming(
    thread_id: str,
    resume_input_dict: dict,
    on_token: Any,
) -> tuple[str, dict, int]:
    """Token-streaming variant of :func:`_resume_wizard_canonical`.

    PM-02 (Audit Rev 4): drives ``JobCreationGraph.stream_invoke`` so
    each LLM token surfaces as a WS ``token`` frame while still
    returning the canonical recruiter-facing message + stage payload.

    Falls back transparently to a single ``invoke()`` call if the graph
    instance does not expose ``stream_invoke`` (e.g. older deploys).
    """
    from app.domains.job_creation.graph import job_creation_graph as wiz_g

    config = {"configurable": {"thread_id": thread_id}}
    try:
        prior_snapshot = wiz_g._graph.get_state(config)
        prior_state = dict(prior_snapshot.values or {})
    except Exception:
        prior_state = {}

    resume_context = (resume_input_dict or {}).get("context") or {}
    approval_payload = (resume_input_dict or {}).get("approval_payload") or {}
    updates: dict = {"hitl_approved": True, **approval_payload}
    if isinstance(resume_context, dict):
        for k in ("draft", "intake_payload", "jd_enriched", "wsi_questions"):
            if k in resume_context and resume_context[k] is not None:
                updates[k] = resume_context[k]

    merged_state = {**prior_state, **updates}
    tokens_emitted = 0
    if hasattr(wiz_g, "stream_invoke"):
        result, tokens_emitted = await wiz_g.stream_invoke(
            merged_state, thread_id, on_token=on_token,
        )
    else:  # pragma: no cover — defensive fallback
        result = await asyncio.to_thread(
            wiz_g.resume, thread_id, prior_state, updates,
        )

    if not isinstance(result, dict):
        return ("Vaga atualizada após aprovação.", {}, tokens_emitted)

    stage_payload = result.get("ws_stage_payload") or {}
    stage_data = stage_payload.get("data") or {}
    current_stage = result.get("current_stage", "") or ""
    message = (
        stage_data.get("message")
        or stage_data.get("response_text")
        or {
            "intake": "Captei a vaga. Vou seguir para o próximo passo.",
            "jd_enrichment": "Descrição da vaga enriquecida — preciso da sua aprovação.",
            "wsi_questions": "Perguntas de triagem WSI sugeridas — preciso da sua aprovação.",
            "completed": "Vaga criada com sucesso.",
        }.get(current_stage, f"Etapa atual: {current_stage or 'wizard'}.")
    )
    return (message, stage_payload, tokens_emitted)


def _ensure_agents_loaded() -> None:
    """Import all agent modules once to trigger @register_agent decorators.

    Idempotent. Safe to call repeatedly.
    """
    global _AGENTS_LOADED
    if _AGENTS_LOADED:
        return

    try:
        # Top-level ReAct agents
        # WizardReActAgent removed in Task #850 — JobCreationGraph replaces it.
        from app.domains.cv_screening.agents.pipeline_react_agent import PipelineReActAgent  # noqa: F401
        from app.domains.sourcing.agents.sourcing_react_agent import SourcingReActAgent  # noqa: F401
        from app.domains.recruiter_assistant.agents.talent_react_agent import TalentReActAgent  # noqa: F401
        from app.domains.recruiter_assistant.agents.kanban_react_agent import KanbanReActAgent  # noqa: F401
        from app.domains.recruiter_assistant.agents.jobs_mgmt_react_agent import JobsManagementReActAgent  # noqa: F401
        from app.domains.hiring_policy.agents.policy_react_agent import PolicyReActAgent  # noqa: F401
        from app.domains.pipeline.agents.pipeline_transition_agent import PipelineTransitionAgent  # noqa: F401
        from app.domains.analytics.agents.analytics_react_agent import AnalyticsReActAgent  # noqa: F401
        from app.domains.communication.agents.communication_react_agent import CommunicationReActAgent  # noqa: F401
        from app.domains.ats_integration.agents.ats_integration_react_agent import ATSIntegrationReActAgent  # noqa: F401
        from app.domains.company_settings.agents.company_react_agent import CompanySettingsReActAgent  # noqa: F401

        # Sourcing sub-agents
        from app.domains.sourcing.agents.sourcing_planner_agent import SourcingPlannerAgent  # noqa: F401
        from app.domains.sourcing.agents.sourcing_search_agent import SourcingSearchAgent  # noqa: F401
        from app.domains.sourcing.agents.sourcing_enrich_agent import SourcingEnrichAgent  # noqa: F401
        from app.domains.sourcing.agents.sourcing_engagement_agent import SourcingEngagementAgent  # noqa: F401

        # Kanban sub-agents
        from app.domains.recruiter_assistant.agents.kanban_search_agent import KanbanSearchAgent  # noqa: F401
        from app.domains.recruiter_assistant.agents.kanban_insight_agent import KanbanInsightAgent  # noqa: F401
        from app.domains.recruiter_assistant.agents.kanban_action_agent import KanbanActionAgent  # noqa: F401

        # Pipeline sub-agents
        from app.domains.pipeline.agents.pipeline_context_agent import PipelineContextAgent  # noqa: F401
        from app.domains.pipeline.agents.pipeline_decision_agent import PipelineDecisionAgent  # noqa: F401
        from app.domains.pipeline.agents.pipeline_action_agent import PipelineActionAgent  # noqa: F401

        _AGENTS_LOADED = True
    except Exception as exc:
        logger.error("[AgentChatWS] Falha ao carregar modulos de agentes: %s", exc)

def _extract_auth(token: str | None) -> dict[str, Any]:
    """Extrai company_id e user_id do JWT (best-effort, sem bloquear WS)."""
    if not token:
        return {"company_id": "", "user_id": "anonymous"}
    try:
        import jwt as pyjwt
        payload = pyjwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        raw_cid = str(payload.get("company_id") or payload.get("organization_id") or "")
        normalized_cid = normalize_demo_company_id(raw_cid, context="agent_chat_ws._extract_auth") or ""
        return {
            "company_id": normalized_cid,
            "user_id": str(payload.get("sub") or payload.get("user_id") or "anonymous"),
        }
    except Exception:
        return {"company_id": "", "user_id": "anonymous"}


@router.websocket("/ws/chat/{session_id}")
async def agent_chat_ws(
    websocket: WebSocket,
    session_id: str,
    token: str | None = Query(None),
    domain: str = Query("recruiter_assistant"),
    ws_mgr: WSManager = Depends(get_ws_manager),
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

    if not token or user_id == "anonymous":
        await websocket.accept()
        await websocket.close(code=1008, reason="Authentication required")
        logger.warning("[AgentChatWS] Rejected unauthenticated WS session=%s", session_id)
        return

    connected = await ws_mgr.connect(websocket, session_id, company_id or "anonymous", user_id=user_id)
    if not connected:
        return

    conversation_history: list = []

    try:
        # PM-03 (Audit Rev 4): announce protocol version on connect so
        # the client can probe for MAJOR compatibility.
        from app.shared.websocket.ws_message_schemas import (
            LIA_WS_PROTOCOL_VERSION,
            WSConnectedMessage,
            is_protocol_compatible,
        )

        await ws_mgr.send_to_session(
            session_id,
            WSConnectedMessage(
                session_id=session_id,
                domain=domain,
            ).model_dump(),
        )

        while True:
            try:
                raw = await asyncio.wait_for(websocket.receive_text(), timeout=300.0)
            except TimeoutError:
                # Ping de keepalive
                await ws_mgr.send_to_session(session_id, {"type": "ping"})
                continue

            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await ws_mgr.send_to_session(session_id, serialize_error("JSON inválido"))
                continue

            msg_type = msg.get("type", "message")

            if msg_type == "ping":
                await ws_mgr.send_to_session(session_id, {"type": "pong"})
                continue

            # PM-03 (Audit Rev 4): client → server handshake. The client
            # may send `{"type": "hello", "protocol_version": "X.Y"}` to
            # announce its supported MAJOR. We close the socket with code
            # 4400 (RFC-compliant private range) on MAJOR mismatch so the
            # client can surface a "please update" error to the user.
            if msg_type == "hello":
                client_version = str(msg.get("protocol_version") or "").strip()
                if not is_protocol_compatible(client_version):
                    logger.warning(
                        "[AgentChatWS] Protocol mismatch session=%s "
                        "client=%r server=%r — closing 4400",
                        session_id, client_version, LIA_WS_PROTOCOL_VERSION,
                    )
                    await ws_mgr.send_to_session(session_id, serialize_error(
                        f"Protocol version {client_version!r} incompatible with "
                        f"server {LIA_WS_PROTOCOL_VERSION!r}",
                        "protocol_mismatch",
                    ))
                    try:
                        await websocket.close(code=4400, reason="protocol_mismatch")
                    except Exception:  # pragma: no cover — best-effort close
                        pass
                    break
                # Echo the server's version so the client can confirm.
                await ws_mgr.send_to_session(session_id, {
                    "type": "hello_ack",
                    "protocol_version": LIA_WS_PROTOCOL_VERSION,
                })
                continue

            if msg_type == "abort":
                break

            # HITL — recebe resposta de aprovação humana via WS
            if msg_type == "approval_response":
                try:
                    from app.domains.cv_screening.services.hitl_service import hitl_service
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
                    await ws_mgr.send_to_session(session_id, {
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

                            await ws_mgr.send_to_session(session_id, serialize_thinking())
                            try:
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
                                    await ws_mgr.send_to_session(session_id, serialize_message(
                                        content=_wsi_msg,
                                        confidence=0.95,
                                        domain="cv_screening",
                                        source="hitl_resume",
                                    ))
                                    conversation_history.append({"role": "assistant", "content": _wsi_msg})
                                # wizard (JobCreationGraph) — Task #850 canonical
                                # path. Use the canonical `resume(thread_id,
                                # prior_state, updates)` API: pulls prior state
                                # from the checkpointer, merges recruiter
                                # approval payload, and re-invokes the graph
                                # with the audit callback wired (no bypass of
                                # the canonical domain contract).
                                elif resume_domain == "wizard":
                                    # PM-02 (Audit Rev 4): when token streaming
                                    # is enabled, drive the canonical wizard
                                    # graph via `astream_events("v2")` so each
                                    # LLM chunk surfaces as a `token` frame in
                                    # real time. Falls back to the historical
                                    # threaded `invoke()` path otherwise — the
                                    # contract (final message + stage payload)
                                    # is unchanged.
                                    from app.api.v1._ws_stream_helpers import (
                                        is_token_streaming_enabled,
                                    )
                                    if is_token_streaming_enabled():
                                        async def _on_wiz_token(chunk: str) -> None:
                                            try:
                                                await ws_mgr.send_to_session(
                                                    session_id,
                                                    {"type": "token", "content": chunk, "domain": "wizard"},
                                                )
                                            except Exception:  # pragma: no cover — fail-silent
                                                pass

                                        await ws_mgr.send_to_session(
                                            session_id,
                                            {"type": "token_stream_start", "domain": "wizard"},
                                        )
                                        _wiz_msg, _wiz_stage_payload, _wiz_tokens = await asyncio.wait_for(
                                            _resume_wizard_canonical_streaming(
                                                ws_thread_id,
                                                resume_input_dict,
                                                _on_wiz_token,
                                            ),
                                            timeout=_AGENT_TIMEOUT,
                                        )
                                        await ws_mgr.send_to_session(
                                            session_id,
                                            {"type": "token_stream_end", "domain": "wizard", "tokens": _wiz_tokens},
                                        )
                                    else:
                                        _wiz_msg, _wiz_stage_payload = await asyncio.wait_for(
                                            asyncio.to_thread(
                                                _resume_wizard_canonical,
                                                ws_thread_id,
                                                resume_input_dict,
                                            ),
                                            timeout=_AGENT_TIMEOUT,
                                        )
                                    _wiz_msg = _strip_react_json(_wiz_msg)
                                    await ws_mgr.send_to_session(session_id, serialize_message(
                                        content=_wiz_msg,
                                        confidence=0.95,
                                        domain="wizard",
                                        source="hitl_resume",
                                    ))
                                    # Forward the canonical wizard stage payload
                                    # to the UI so the right-panel form / stage
                                    # cards stay in sync with the graph.
                                    if _wiz_stage_payload:
                                        await ws_mgr.send_to_session(session_id, _wiz_stage_payload)
                                    conversation_history.append({"role": "assistant", "content": _wiz_msg})
                                else:
                                    resume_agent = _get_agent(
                                        resume_domain,
                                        company_id=company_id,
                                        session_id=session_id,
                                        user_id=user_id,
                                    )
                                    if resume_agent:
                                        from lia_agents_core.agent_interface import AgentInput
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
                                        await ws_mgr.send_to_session(session_id, serialize_message(
                                            content=_resume_clean,
                                            confidence=resume_output.confidence,
                                            domain=resume_domain,
                                            source="hitl_resume",
                                            actions=[a.dict() for a in (resume_output.actions or [])],
                                        ))
                                        conversation_history.append({"role": "user", "content": "[HITL aprovado]"})
                                        conversation_history.append({"role": "assistant", "content": _resume_clean})
                            except Exception as _resume_exc:
                                logger.error("[AgentChatWS] HITL resume falhou: %s", _resume_exc)
                                await ws_mgr.send_to_session(session_id, serialize_error(
                                    "Erro ao retomar execução após aprovação.",
                                ))
                        elif not ws_approved:
                            await ws_mgr.send_to_session(session_id, serialize_message(
                                content="Ação cancelada pelo aprovador. Nenhuma alteração foi feita.",
                                domain=resume_domain or domain,
                                source="hitl_rejected",
                            ))

                            # SEG-5: AuditService — registrar rejeição HITL
                            try:
                                from app.shared.compliance.audit_service import PROTECTED_CRITERIA, audit_service
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
                    await ws_mgr.send_to_session(session_id, serialize_error(
                        "Erro ao processar resposta de aprovação.",
                    ))
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
                await ws_mgr.send_to_session(session_id, serialize_error(
                    "Mensagem bloqueada por segurança. Por favor, reformule sua solicitação.",
                    "prompt_injection_blocked",
                ))
                continue
            elif _inj_result.risk_level == "medium":
                logger.info(
                    "[AgentChatWS][SEG-1] Injeção de prompt suspeita (medium) session=%s "
                    "patterns=%s — prosseguindo com log",
                    session_id, _inj_result.matched_patterns,
                )

            # Item 4: SecurityPatterns pre-check (inline for WS)
            _sec_result = check_input_security(content)
            if _sec_result.is_blocked:
                logger.warning(
                    "[AgentChatWS][SEG-2] SecurityPatterns blocked session=%s risk=%s",
                    session_id, _sec_result.risk_level,
                )
                await ws_mgr.send_to_session(session_id, serialize_error(
                    get_block_response(_sec_result, language="pt"),
                    "security_blocked",
                ))
                continue

            # Item 4: FairnessGuard pre-check (inline for WS)
            _fg_result = _fairness_guard.check(content)
            if _fg_result.is_blocked:
                logger.warning(
                    "[AgentChatWS][SEG-3] FairnessGuard blocked session=%s",
                    session_id,
                )
                await ws_mgr.send_to_session(session_id, serialize_error(
                    _fg_result.educational_message or "Solicitacao bloqueada por criterios de equidade.",
                    "fairness_blocked",
                ))
                continue

            context = msg.get("context", {})
            context.setdefault("company_id", company_id)
            context.setdefault("user_id", user_id)
            active_domain = msg.get("domain", domain)

            # PR-J: Rail A capability gate (Phase 0.5)
            try:
                from app.orchestrator.rail_a_capability_check import check_rail_a_capability
                _cap_payload = await check_rail_a_capability(
                    context=context,
                    message=content,
                    company_id=company_id,
                    db=None,
                )
                if _cap_payload is not None:
                    await ws_mgr.send_to_session(session_id, _cap_payload)
                    continue
            except Exception as _prj_exc:
                logger.debug("[PR-J] Capability check skipped: %s", _prj_exc)

            _c3b_result = await pre_compliance(content, company_id, active_domain)
            if _c3b_result.fairness_blocked:
                await ws_mgr.send_to_session(session_id, {"type": "error", "code": "fairness_block", "message": _c3b_result.block_reason})
                continue
            content = _c3b_result.clean_message

            await ws_mgr.send_to_session(session_id, serialize_thinking())

            # ── Plan Detection (multi-step workflows) ─────────────────────
            _plan_handled = False
            try:
                # Budget check before plan execution (same as agent path)
                try:
                    _plan_budget = await get_plan_for_company(company_id)
                    _budget_ok, _used, _limit = await check_budget(company_id, _plan_budget)
                    if not _budget_ok:
                        await ws_mgr.send_to_session(session_id, serialize_error(
                            f"Limite diário de uso de IA atingido ({_used:,} / {_limit:,} tokens). "
                            "O budget será renovado à meia-noite UTC.",
                            "budget_exhausted",
                        ))
                        continue
                except Exception as _budget_exc:
                    logger.warning("[AgentChatWS] Budget check falhou (plan path) — continuando: %s", _budget_exc)

                from app.domains.registry import DomainRegistry
                from app.domains.workflow import DomainWorkflow
                from app.shared.execution import PlanDetector, PlanExecutor

                _plan_detector = PlanDetector()
                _detected_plan = _plan_detector.detect(content)
                if _detected_plan:
                    logger.info(
                        "[AgentChatWS] Multi-step plan detected: %s (%d tasks)",
                        _detected_plan.detected_pattern,
                        len(_detected_plan.tasks),
                    )
                    _domain_registry = DomainRegistry()
                    _domain_workflow = DomainWorkflow()
                    _plan_executor = PlanExecutor(
                        domain_registry=_domain_registry,
                        domain_workflow=_domain_workflow,
                    )

                    _plan_task_id = f"plan-{session_id[:8]}"

                    async def _ws_plan_progress(event_type: str, data: dict) -> None:
                        try:
                            await ws_mgr.send_to_session(session_id, {
                                "type": "plan_progress",
                                "event": event_type,
                                **data,
                            })
                            _progress = data.get("progress", 0)
                            _label = data.get("label", _detected_plan.detected_pattern or "Plano multi-step")
                            _status = "completed" if event_type == "plan_complete" else ("failed" if event_type == "plan_error" else "running")
                            await send_background_task_update(
                                session_id=session_id,
                                task_id=_plan_task_id,
                                task_type="analysis",
                                label=_label,
                                status=_status,
                                progress=_progress,
                                message=data.get("message", ""),
                            )
                        except Exception:
                            pass

                    await send_background_task_update(
                        session_id=session_id,
                        task_id=_plan_task_id,
                        task_type="analysis",
                        label=_detected_plan.detected_pattern or "Plano multi-step",
                        status="running",
                        progress=0,
                        message=f"Executando plano com {len(_detected_plan.tasks)} tarefas",
                    )

                    _executed = await _plan_executor.execute(
                        plan=_detected_plan,
                        user_id=user_id,
                        session_id=session_id,
                        tenant_id=company_id,
                        base_context={"company_id": company_id, "user_id": user_id},
                        progress_callback=_ws_plan_progress,
                    )
                    _consolidated = _plan_executor.build_consolidated_response(_executed)
                    _plan_msg = _strip_thought_tags(_consolidated.message or "Plano executado.")
                    conversation_history.append({"role": "user", "content": content})
                    conversation_history.append({"role": "assistant", "content": _plan_msg})

                    # Meter token usage for plan execution
                    _plan_tokens = int((len(content.split()) + len(_plan_msg.split())) * 1.3)
                    if _plan_tokens > 0 and company_id:
                        try:
                            await increment_usage(company_id, _plan_tokens)
                        except Exception as _inc_exc:
                            logger.warning("[AgentChatWS] plan increment_usage falhou: %s", _inc_exc)

                    await ws_mgr.send_to_session(session_id, serialize_message(
                        content=_plan_msg,
                        confidence=0.9,
                        domain="plan_executor",
                        source="plan_executor",
                        execution_plan=_executed.get_summary(),
                    ))
                    await send_background_task_update(
                        session_id=session_id,
                        task_id=_plan_task_id,
                        task_type="analysis",
                        label=_detected_plan.detected_pattern or "Plano multi-step",
                        status="completed",
                        progress=100,
                        message="Plano executado com sucesso",
                    )
                    _plan_handled = True
            except Exception as _plan_exc:
                logger.warning(
                    "[AgentChatWS] Plan detection/execution failed (non-blocking): %s",
                    _plan_exc,
                )

            if _plan_handled:
                continue

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
                        await ws_mgr.send_to_session(session_id, {
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

            agent = _get_agent(
                active_domain,
                company_id=company_id,
                session_id=session_id,
                user_id=user_id,
            )
            if agent is None:
                await ws_mgr.send_to_session(session_id, serialize_error(
                    f"Agente '{active_domain}' indisponível.", "agent_unavailable",
                ))
                continue

            # E7: injeta streaming_callback no context antes de construir agent_input
            async def _thinking_callback_pre(event: dict) -> None:
                """Retransmite evento thinking do ReAct loop para o cliente WebSocket."""
                try:
                    await ws_mgr.send_to_session(session_id, serialize_thinking(
                        content=event.get("thought", ""),
                        step=event.get("step", 0),
                    ))
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
                    _task_type_map = {
                        "sourcing": "sourcing", "cv_screening": "screening",
                        "communication": "communication",
                    }
                    await send_background_task_update(
                        session_id=session_id,
                        task_id=job_id,
                        task_type=_task_type_map.get(active_domain, "analysis"),
                        label=f"Agente {active_domain}",
                        status="running",
                        progress=0,
                        message="Processando em background...",
                    )
                    await ws_mgr.send_to_session(session_id, serialize_thinking(
                        content="Processando em background...",
                    ))
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
                    await ws_mgr.send_to_session(session_id, serialize_error(
                        f"Limite diário de uso de IA atingido ({_used:,} / {_limit:,} tokens). "
                        "O budget será renovado à meia-noite UTC.",
                        "budget_exhausted",
                    ))
                    continue
            except Exception as _budget_exc:
                logger.warning("[AgentChatWS] Budget check falhou — continuando: %s", _budget_exc)

            try:
                output = await asyncio.wait_for(
                    agent.process(agent_input),
                    timeout=_AGENT_TIMEOUT,
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
                        logger.warning("[AgentChatWS] increment_usage falhou: %s", _inc_exc)

                clean_message = _strip_react_json(output.message or "")
                if not clean_message or not clean_message.strip():
                    logger.error(
                        "[AgentChatWS] Agent '%s' returned empty response session=%s "
                        "company_id=%s raw=%r",
                        active_domain, session_id, company_id, output.message,
                    )
                    await ws_mgr.send_to_session(session_id, serialize_message(
                        content=_EMPTY_AGENT_RESPONSE_MESSAGE,
                        confidence=0.0,
                        domain=active_domain,
                        source="agent_empty_response",
                    ))
                    await ws_mgr.send_to_session(session_id, serialize_error(
                        _EMPTY_AGENT_RESPONSE_MESSAGE,
                        "agent_empty_response",
                    ))
                    continue

                _c3b_ctx = ComplianceContext(
                    company_id=company_id or "",
                    user_id=user_id,
                    session_id=session_id,
                    domain=active_domain,
                    agent_id=active_domain,
                    original_message=_c3b_result.original_message,
                    fairness_flags=_c3b_result.fairness_flags,
                )
                clean_message = await post_compliance(clean_message, _c3b_ctx)

                conversation_history.append({"role": "user", "content": content})
                conversation_history.append({"role": "assistant", "content": clean_message})

                _panel_meta = (output.metadata or {}).get("panel_update")
                if _panel_meta and isinstance(_panel_meta, dict):
                    await send_panel_update(
                        session_id=session_id,
                        panel_type=_panel_meta.get("panel_type", ""),
                        panel_data=_panel_meta.get("panel_data", {}),
                        panel_title=_panel_meta.get("panel_title", ""),
                        action=_panel_meta.get("action", "open"),
                    )

                _fairness_warnings = (output.metadata or {}).get("fairness_warnings", [])

                # Gap 4 — run PreConditionChecker for proactive hints (fail-open)
                _proactive_hints: list[dict] | None = None
                try:
                    from app.orchestrator.precondition_checker import precondition_checker

                    class _HintCtx:
                        pass
                    _hctx = _HintCtx()
                    _hctx.company_id = company_id or ""
                    _hctx.intent = active_domain or ""
                    _hctx.vacancy_id = (context or {}).get("vacancy_id") or (context or {}).get("job_id")

                    _hints = await precondition_checker.check(_hctx)
                    if _hints:
                        _proactive_hints = [
                            {
                                "type": h.type,
                                "message": h.message,
                                "severity": h.severity,
                                "action": h.action,
                                "metadata": h.metadata,
                            }
                            for h in _hints
                        ]
                        logger.info(
                            "[AgentChatWS] %d proactive hints attached to session=%s",
                            len(_proactive_hints), session_id,
                        )
                except Exception as _ph_exc:
                    logger.debug("[AgentChatWS] proactive hints skipped: %s", _ph_exc)

                await ws_mgr.send_to_session(session_id, serialize_message(
                    content=clean_message,
                    confidence=output.confidence,
                    domain=active_domain,
                    source="direct",
                    actions=[a.dict() for a in (output.actions or [])],
                    navigation=output.navigation.dict() if output.navigation else None,
                    state_updates=output.state_updates or None,
                    fairness_warnings=_fairness_warnings or None,
                    proactive_hints=_proactive_hints,
                ))

            except TimeoutError:
                await ws_mgr.send_to_session(session_id, serialize_error(
                    "Tempo limite de processamento excedido. Tente novamente.",
                ))
            except Exception as exc:
                logger.error("[AgentChatWS] Erro no agente session=%s: %s", session_id, exc, exc_info=True)
                await ws_mgr.send_to_session(session_id, serialize_error(
                    "Erro interno ao processar sua mensagem.",
                ))

    except WebSocketDisconnect:
        logger.info("[AgentChatWS] Desconectado session=%s", session_id)
    except Exception as exc:
        logger.error("[AgentChatWS] Erro inesperado session=%s: %s", session_id, exc)
    finally:
        ws_mgr.disconnect(session_id)
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
    context: dict[str, Any] = {}

    class Config:
        from_attributes = True


class HTTPChatResponse(BaseModel):
    content: str
    confidence: float = 0.0
    domain: str = ""
    actions: list = []
    error: str | None = None


_SCOPE_TO_DOMAIN = {
    "Vagas": "jobs_management", "vagas": "jobs_management",
    "jobs": "jobs_management", "job": "jobs_management",
    "Candidatos": "sourcing", "candidatos": "sourcing",
    "Analytics": "analytics", "analytics": "analytics",
    "Configuracoes": "company_settings", "Configuracoes": "company_settings",
    "Kanban": "kanban", "kanban": "kanban",
    "Sourcing": "sourcing",
}


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

    session_id = req.session_id or create_session_id(company_id)
    active_domain = req.domain or "recruiter_assistant"
    context = req.context or {}
    context.setdefault("company_id", company_id)
    context.setdefault("user_id", user_id)
    # A2a: map frontend scope to domain agent
    if not req.domain and context.get("scope"):
        _page_domain = _SCOPE_TO_DOMAIN.get(context["scope"])
        if _page_domain:
            active_domain = _page_domain
    if context.get("scope") and context["scope"] not in ("global", ""):
        context.setdefault("page_context_hint", f"Usuário está na página: {context['scope']}")

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

    agent = _get_agent(
        active_domain,
        company_id=company_id,
        session_id=session_id,
        user_id=user_id,
    )
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

        _clean_content = _strip_react_json(output.message or "")
        if not _clean_content or not _clean_content.strip():
            logger.error(
                "[HTTPChat] Agent '%s' returned empty response for session=%s company_id=%s. "
                "Raw message=%r metadata_keys=%s",
                active_domain, session_id, company_id,
                output.message,
                list((output.metadata or {}).keys()),
            )
            return HTTPChatResponse(
                content=_EMPTY_AGENT_RESPONSE_MESSAGE,
                confidence=0.0,
                domain=active_domain,
                error="agent_empty_response",
            )
        return HTTPChatResponse(
            content=_clean_content,
            confidence=output.confidence,
            domain=active_domain,
            actions=[a.dict() for a in (output.actions or [])],
        )
    except TimeoutError:
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
