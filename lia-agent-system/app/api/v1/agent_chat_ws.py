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
    { "type": "panel_update", "panel_type": "...", "panel_data": {...}, "panel_title": "...", "action": "open|update|close" }
    { "type": "background_task_update", "task_id": "...", "task_type": "sourcing|screening|communication|analysis", "label": "...", "status": "running|completed|failed|deferred", "progress": 0-100, "message": "..." }
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
from app.domains.credits.services.token_budget_service import (
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
from app.shared.pii_masking import mask_pii
from app.shared.robustness.security_patterns import check_input_security, get_block_response
from app.shared.compliance.fairness_guard import FairnessGuard
from app.shared.compliance.c3b_layer import pre_compliance, post_compliance, ComplianceContext
from app.shared.tenant_session import create_session_id
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


async def _persist_chat_turn(
    conversation_id: str | None,
    company_id: str | None,
    user_content: str,
    assistant_content: str,
) -> None:
    """B9 (2026-05-31): persiste o turno (user+assistant) no store canônico de
    conversations, para sobreviver à navegação/reload.

    O caminho WS streamava a resposta sem persistir → loadHistory
    (/conversations/{id}) não via as respostas da IA (só as do usuário). RLS-aware
    via set_tenant_context (conversations tem RLS por company_id). Fail-open: a
    persistência NUNCA derruba o chat.
    """
    if not (conversation_id and company_id and assistant_content):
        return
    try:
        from app.core.database import AsyncSessionLocal, set_tenant_context
        from app.domains.recruiter_assistant.services.conversation_memory import (
            conversation_memory,
        )
        async with AsyncSessionLocal() as _db:
            await set_tenant_context(_db, str(company_id))
            if user_content:
                await conversation_memory.add_message(
                    _db, str(conversation_id), "user", user_content
                )
            await conversation_memory.add_message(
                _db, str(conversation_id), "assistant", assistant_content
            )
            await _db.commit()
    except Exception as _exc:  # noqa: BLE001 — fail-open
        logger.warning("[AgentChatWS] persist chat turn falhou (fail-open): %s", _exc)


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
    status: "running" | "completed" | "failed" | "deferred"
        ("deferred" = honest P&E→agent handoff: step belongs to a continuous
        agent and was NOT executed — Task #1222)
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
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
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
    """Constrói AgentInput a partir dos dados da mensagem WS."""
    from lia_agents_core.agent_interface import AgentInput
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


def _get_agent(domain: str) -> Any | None:
    """Retorna instancia do agente para o dominio solicitado.

    Fase 3a (Wave 2): Delegates to AgentRegistry. The 21-branch if/elif
    was replaced — each agent class is decorated with @register_agent(id).
    Fallback to "talent" preserved for unknown domain.
    """
    try:
        # Trigger agent module imports (one-time, idempotent) so decorators run.
        # Each import registers the class in AgentRegistry.
        _ensure_agents_loaded()

        from app.shared.agents.agent_registry import AgentRegistry
        return AgentRegistry().get_or_fallback(domain, fallback_id="talent")
    except Exception as exc:
        logger.error("[AgentChatWS] Falha ao carregar agente domain=%s: %s", domain, exc)
        return None


_AGENTS_LOADED = False


def _ensure_agents_loaded() -> None:
    """Import all agent modules once to trigger @register_agent decorators.

    Idempotent. Safe to call repeatedly.
    """
    global _AGENTS_LOADED
    if _AGENTS_LOADED:
        return

    try:
        # Top-level ReAct agents
        from app.domains.job_management.agents.wizard_react_agent import WizardReActAgent  # noqa: F401
        from app.domains.cv_screening.agents.pipeline_react_agent import PipelineReActAgent  # noqa: F401
        from app.domains.sourcing.agents.sourcing_react_agent import SourcingReActAgent  # noqa: F401
        from app.domains.recruiter_assistant.agents.talent_react_agent import TalentReActAgent  # noqa: F401  # backward-compat shim
        from app.domains.recruiter_assistant.agents.talent_funnel_react_agent import TalentFunnelReActAgent  # noqa: F401
        from app.domains.recruiter_assistant.agents.kanban_react_agent import KanbanReActAgent  # noqa: F401
        from app.domains.recruiter_assistant.agents.jobs_mgmt_react_agent import JobsManagementReActAgent  # noqa: F401
        from app.domains.hiring_policy.agents.policy_react_agent import PolicyReActAgent  # noqa: F401
        from app.domains.pipeline.agents.pipeline_transition_agent import PipelineTransitionAgent  # noqa: F401
        from app.domains.analytics.agents.analytics_react_agent import AnalyticsReActAgent  # noqa: F401
        from app.domains.communication.agents.communication_react_agent import CommunicationReActAgent  # noqa: F401
        from app.domains.ats_integration.agents.ats_integration_react_agent import ATSIntegrationReActAgent  # noqa: F401

        # Sourcing sub-agents (W1-001 cleanup 2026-05-22 — granular)
        from app.domains.sourcing.agents.github_sourcing_agent import GithubSourcingAgent  # noqa: F401
        from app.domains.sourcing.agents.stackoverflow_sourcing_agent import StackOverflowSourcingAgent  # noqa: F401
        from app.domains.sourcing.agents.diversity_sourcing_agent import DiversitySourcingAgent  # noqa: F401
        from app.domains.sourcing.agents.passive_pipeline_agent import PassivePipelineAgent  # noqa: F401
        from app.domains.sourcing.agents.referral_agent import ReferralAgent  # noqa: F401
        from app.domains.sourcing.agents.nurture_sequence_agent import NurtureSequenceAgent  # noqa: F401
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

        # Standalone domain agents (added 2026-05-20 by Sprint A.1 — Task #28)
        from app.domains.talent_pool.agents.talent_pool_agent import TalentPoolReActAgent  # noqa: F401
        from app.domains.autonomous.agents.autonomous_react_agent import AutonomousReActAgent  # noqa: F401  # Tier 6 ReAct fallback canonical — registration trigger pro @register_agent decorator (ADR-V3.1)
        from app.domains.company_settings.agents.company_react_agent import CompanySettingsReActAgent  # noqa: F401
        from app.domains.candidate_self_service.agents.candidate_react_agent import CandidateSelfServiceAgent  # noqa: F401

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
    token: str | None = Query(None),
    domain: str = Query("recruiter_assistant"),
    ws_mgr: WSManager = Depends(get_ws_manager),
company_id: str = Depends(require_company_id)):
    """
    WebSocket bidirecional para chat com agentes LIA.

    Parâmetros:
    - session_id: ID único da sessão de chat
    - token: JWT para autenticação (query param)
    - domain: domínio do agente alvo (query param)
    """
    # UC-P0-19: first-message auth — JWT must NOT be in the URL query string.
    # New path: connect without token, then send {type:auth,token:...} as the
    # very first WS message.  The query-string path still works (backward compat)
    # but logs a deprecation warning so we can remove it once all clients migrate.
    _first_msg_raw: str | None = None
    if token:
        # Legacy path — token in query param (DEPRECATED, UC-P0-19)
        logger.warning(
            "[AgentChatWS][DEPRECATED] JWT via query param exposes token in logs "
            "(session=%s). Clients must migrate to first-message auth (UC-P0-19).",
            session_id,
        )
        auth = _extract_auth(token)
        company_id = auth["company_id"]
        user_id = auth["user_id"]
        if user_id == "anonymous":
            await websocket.accept()
            await websocket.close(code=1008, reason="Authentication required")
            logger.warning("[AgentChatWS] Rejected invalid token (query param) session=%s", session_id)
            return
    else:
        # New path (UC-P0-19): accept the connection, then wait for the auth message
        await websocket.accept()
        try:
            _first_msg_raw = await asyncio.wait_for(websocket.receive_text(), timeout=10.0)
        except asyncio.TimeoutError:
            await websocket.close(code=1008, reason="Auth timeout")
            logger.warning("[AgentChatWS] Auth timeout session=%s", session_id)
            return
        except Exception:
            await websocket.close(code=1008, reason="Auth read error")
            logger.warning("[AgentChatWS] Auth read error session=%s", session_id)
            return
        try:
            _first_msg = json.loads(_first_msg_raw)
        except (json.JSONDecodeError, ValueError):
            await websocket.close(code=1008, reason="Invalid auth message format")
            logger.warning("[AgentChatWS] Invalid auth message format session=%s", session_id)
            return
        if _first_msg.get("type") != "auth" or not _first_msg.get("token"):
            await websocket.close(code=1008, reason="Authentication required as first message")
            logger.warning("[AgentChatWS] Missing auth first-message session=%s", session_id)
            return
        token = _first_msg["token"]
        auth = _extract_auth(token)
        company_id = auth["company_id"]
        user_id = auth["user_id"]
        if user_id == "anonymous":
            await websocket.close(code=1008, reason="Invalid token")
            logger.warning("[AgentChatWS] Rejected invalid token (first-msg) session=%s", session_id)
            return

    # Connect to WS session manager.
    # ws_mgr.connect() calls websocket.accept() internally.
    # When the first-message auth path was taken, accept() was already called;
    # use connect_already_accepted() to skip the double-accept.
    if _first_msg_raw is not None:
        # first-message auth path — socket already accepted
        connected = await ws_mgr.connect_already_accepted(
            websocket, session_id, company_id or "anonymous", user_id=user_id
        )
    else:
        # legacy query-param path — ws_mgr.connect() will call accept()
        connected = await ws_mgr.connect(websocket, session_id, company_id or "anonymous", user_id=user_id)
    if not connected:
        return

    conversation_history: list = []

    try:
        await ws_mgr.send_to_session(session_id, {
            "type": "connected",
            "session_id": session_id,
            "domain": domain,
        })

        # ── Wizard resume resync (Task #1097) ─────────────────────────────
        # When the browser reloads mid-wizard, the LangGraph checkpoint is
        # preserved (Task #1080) but the FE loses the in-memory `wizard_stage`
        # payload that drives the right-side panel + `useWizardFlow` state.
        # If localStorage was also cleared (incognito, clean profile, LGPD
        # purge), the panel and chat fall out of sync until the user types.
        # Re-emit the persisted ws_stage_payload right after `connected` so
        # the FE rehydrates panel + wizard hook deterministically from the
        # backend source of truth. Fail-open: any error is logged and skipped
        # so a broken checkpointer never blocks the chat handshake.
        try:
            from app.shared.sessions import (
                derive_thread_id as _resume_derive_tid,
                is_wizard_session_active as _resume_is_active,
            )

            if await _resume_is_active(company_id, session_id):
                _resume_thread_id = _resume_derive_tid(company_id, session_id)
                from app.domains.job_creation.graph import (
                    get_job_creation_graph as _resume_get_graph,
                )

                _resume_graph = _resume_get_graph()
                _resume_snapshot = await asyncio.to_thread(
                    _resume_graph._graph.get_state,
                    {"configurable": {"thread_id": _resume_thread_id}},
                )
                _resume_values = (
                    getattr(_resume_snapshot, "values", None) or {}
                )
                _resume_payload = _resume_values.get("ws_stage_payload") or {}
                _resume_stage = (
                    _resume_payload.get("stage")
                    or _resume_values.get("current_stage")
                    or "wizard"
                )
                if _resume_payload or _resume_stage:
                    await ws_mgr.send_to_session(session_id, {
                        "type": "wizard_stage",
                        "session_id": session_id,
                        "thread_id": _resume_thread_id,
                        "stage": _resume_stage,
                        "data": _resume_payload.get(
                            "data", _resume_values.get("right_panel_form") or {},
                        ),
                        "completeness": _resume_payload.get(
                            "completeness",
                            _resume_values.get("completeness", 0.0),
                        ),
                        "requires_approval": bool(
                            _resume_payload.get(
                                "requires_approval",
                                _resume_values.get("requires_approval", False),
                            ),
                        ),
                        "resumed": True,
                    })
                    logger.info(
                        "[AgentChatWS] wizard_resume_resync: session=%s "
                        "stage=%s (Task #1097)",
                        session_id, _resume_stage,
                    )
        except Exception as _resume_exc:  # pragma: no cover — fail-open
            logger.debug(
                "[AgentChatWS] wizard_resume_resync skipped: %s", _resume_exc,
            )

        # ── HITL pending resync (Task #1110) ──────────────────────────────
        # When a recruiter opens a SECOND tab while the first tab already
        # received an `approval_required` frame, the second tab missed the
        # broadcast (it wasn't connected yet). Re-emit the most recent
        # pending HITL request scoped to this user/company so the new tab
        # renders the HITLConfirmCard within ~connect RTT, instead of
        # forcing an F5. Fail-open: any DB/Redis error is logged and
        # skipped — a broken HITL store never blocks the chat handshake.
        try:
            from app.domains.cv_screening.services.hitl_service import (
                hitl_service as _resync_hitl_service,
            )

            _pending_list = await _resync_hitl_service.get_all_pending_by_company(
                company_id or ""
            )
            # Filter to pendings owned by THIS recruiter when the payload
            # records it (request_approval persists `user_id` via the DB
            # row's resolved_by/created_by audit; in-flight items use the
            # `agent_input.user_id` snapshot). Items without a user_id are
            # treated as visible — same-company recruiters share visibility
            # of HITL approvals (consistent with /api/v1/hitl/pending).
            def _owned_by(item: dict) -> bool:
                if not user_id or user_id == "anonymous":
                    return True
                _agent_input = item.get("agent_input") or {}
                _owner = (
                    item.get("user_id")
                    or item.get("resolved_by")
                    or _agent_input.get("user_id")
                    or ""
                )
                return not _owner or str(_owner) == str(user_id)

            _replay_candidates = [p for p in _pending_list if _owned_by(p)]
            if _replay_candidates:
                # Most recent first — already sorted by request_approval()
                # callers (DB ORDER BY created_at DESC). Replay just the
                # latest to avoid stacking obsolete cards on the new tab.
                _latest = _replay_candidates[0]
                await ws_mgr.send_to_session(session_id, {
                    "type": "approval_required",
                    "thread_id": _latest.get("thread_id", ""),
                    "pending_id": _latest.get("pending_id", ""),
                    "action": _latest.get("action", ""),
                    "description": _latest.get("description", ""),
                    "data": _latest.get("data", {}),
                    "domain": _latest.get("domain", ""),
                    "resumed": True,
                })
                logger.info(
                    "[AgentChatWS] hitl_resync: session=%s replayed pending=%s "
                    "thread=%s (Task #1110)",
                    session_id,
                    _latest.get("pending_id", ""),
                    _latest.get("thread_id", ""),
                )
        except Exception as _hitl_resync_exc:  # pragma: no cover — fail-open
            logger.debug(
                "[AgentChatWS] hitl_resync skipped: %s", _hitl_resync_exc,
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
                    _confirmed_frame = {
                        "type": "approval_confirmed",
                        "thread_id": ws_thread_id,
                        "pending_id": ws_pending_id,
                    }
                    await ws_mgr.send_to_session(session_id, _confirmed_frame)
                    # Task #1110 — fan-out the resolution to the recruiter's
                    # OTHER open tabs so the HITL card disappears everywhere
                    # instead of leaving stale "pendente" cards on the tabs
                    # that didn't click. Best-effort: failure to broadcast
                    # never blocks the originating tab's resume flow.
                    if user_id and user_id != "anonymous":
                        try:
                            await ws_mgr.broadcast_to_user(
                                user_id,
                                _confirmed_frame,
                                exclude_session_id=session_id,
                            )
                        except Exception as _bcast_exc:
                            logger.debug(
                                "[AgentChatWS] broadcast_to_user approval_confirmed falhou: %s",
                                _bcast_exc,
                            )

                    # ── Resume grafo após aprovação ───────────────────────────
                    resume_info = await hitl_service.get_resume_info(ws_thread_id)
                    if resume_info:
                        resume_domain = resume_info.get("domain", "")
                        resume_input_dict = resume_info.get("agent_input", {})
                        # Wizard: APPROVED e REJECTED ambos roteiam pelo service
                        # canônico (Task #1084 / T1 — entry point único, CAS
                        # idempotente, audit row 1×). Esta branch precisa vir
                        # ANTES do `if ws_approved` para capturar AMBOS os casos
                        # do wizard antes do branch legacy de rejeição genérica.
                        if resume_domain == "wizard":
                            from app.domains.job_creation.services.wizard_gate_service import (
                                wizard_gate_service,
                            )
                            try:
                                _gate_result = await wizard_gate_service.resume_gate(
                                    thread_id=ws_thread_id,
                                    pending_id=ws_pending_id,
                                    decision="approved" if ws_approved else "rejected",
                                    ws_session_id=session_id,
                                    company_id=str(company_id or ""),
                                    user_id=str(user_id or ""),
                                    comment=ws_comment,
                                    resume_domain="wizard",
                                    agent_timeout=_AGENT_TIMEOUT,
                                )
                                _wiz_msg = _strip_react_json(_gate_result.get("message", ""))
                                _wiz_source = (
                                    "hitl_resume" if ws_approved else "hitl_rejected"
                                )
                                await ws_mgr.send_to_session(session_id, serialize_message(
                                    content=_wiz_msg,
                                    confidence=0.95,
                                    domain="wizard",
                                    source=_wiz_source,
                                ))
                                conversation_history.append({"role": "assistant", "content": _wiz_msg})
                            except ValueError as _val_exc:
                                logger.error(
                                    "[AgentChatWS] wizard gate ValueError: %s", _val_exc
                                )
                                await ws_mgr.send_to_session(session_id, serialize_error(
                                    "Pedido de aprovação inválido.",
                                ))
                            except Exception as _wiz_exc:
                                logger.error(
                                    "[AgentChatWS] wizard gate erro: %s", _wiz_exc, exc_info=True
                                )
                                await ws_mgr.send_to_session(session_id, serialize_error(
                                    "Erro ao processar a aprovação do wizard.",
                                ))
                        elif ws_approved and resume_domain and resume_input_dict:
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
                                # NOTE: wizard (approved E rejected) é tratado pela
                                # branch top-level `if resume_domain == "wizard"`
                                # acima — entry point único via `wizard_gate_service.resume_gate`.
                                # Não há `elif resume_domain == "wizard"` aqui de propósito.
                                else:
                                    resume_agent = _get_agent(resume_domain)
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
            # Rail A hint: promote top-level metadata into context (idempotent — caller wins)
            if not context.get("metadata"):
                _msg_metadata = msg.get("metadata")
                if _msg_metadata:
                    context["metadata"] = _msg_metadata
            active_domain = msg.get("domain", domain)

            # NOTE (Task #1080): Wizard session-pin previously lived inside
            # ``CascadedRouter`` as a "Tier 0.5" pre-route step. It now lives
            # at the transport boundary (this handler + ``agent_chat_sse.py``)
            # so all router consumers — WS, SSE, REST orchestrator,
            # autonomous_react_agent — get the pin without duplication.
            # See ``app/orchestrator/cascaded_router.py`` "wizard_session_pin".

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
                    # Task #1222: never report a fake success. When a step handed
                    # off to a continuous agent (or the plan failed), the
                    # consolidated response is success=False — reflect that
                    # honestly in the background channel instead of "com sucesso".
                    _plan_ok = bool(_consolidated.success)
                    _plan_has_handoff = bool(
                        (_consolidated.metadata or {}).get("agent_handoffs")
                    )
                    if _plan_has_handoff:
                        _bg_status, _bg_message = "deferred", "Etapa encaminhada a um agente"
                    elif _plan_ok:
                        _bg_status, _bg_message = "completed", "Plano executado com sucesso"
                    else:
                        _bg_status, _bg_message = "failed", "Plano não concluído"
                    await send_background_task_update(
                        session_id=session_id,
                        task_id=_plan_task_id,
                        task_type="analysis",
                        label=_detected_plan.detected_pattern or "Plano multi-step",
                        status=_bg_status,
                        progress=100,
                        message=_bg_message,
                    )
                    _plan_handled = True
            except Exception as _plan_exc:
                logger.warning(
                    "[AgentChatWS] Plan detection/execution failed (non-blocking): %s",
                    _plan_exc,
                )

            if _plan_handled:
                continue

            # ── Wizard session pin (Task #1080 canonical) ──────────────────
            # Single source of truth for "this conversation belongs to the
            # wizard": the LangGraph checkpoint for the canonical thread_id
            # derived from (company_id, session_id). Pin lives here in the
            # transport handler — NOT in CascadedRouter — so the router stays
            # domain-agnostic. Fires only when the FE has not already
            # specified an explicit domain (replaces the previous router-level
            # placement: explicit FE intent always wins). Fail-open.
            if active_domain in ("auto", "recruiter_assistant", ""):
                try:
                    from app.shared.sessions import should_pin_to_wizard
                    _settings_hint = (context.get("metadata") or {}).get("domain_hint")
                    if await should_pin_to_wizard(company_id, session_id, content, domain_hint=_settings_hint):
                        logger.info(
                            "[AgentChatWS] wizard_session_pin: session=%s "
                            "company=%s → wizard (Task #1080)",
                            session_id, company_id,
                        )
                        active_domain = "wizard"
                except Exception as _pin_exc:
                    logger.debug(
                        "[AgentChatWS] wizard_session_pin skipped: %s", _pin_exc,
                    )

            # Roteamento via CascadedRouter (Fase 2 — Gap #2)
            # Verifica se o domínio precisa de clarificação antes de invocar agente
            if active_domain in ("auto", "recruiter_assistant", ""):
                try:
                    from app.orchestrator.routing.cascaded_router import CascadedRouter
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

            # ── Onda 37.B.0 + Sprint A.1 — Wizard canonical INITIAL path ─────────
            # Restored Sprint A.1 canonical: WizardSessionService.process_message()
            # is the entry point. Service handles:
            #   • thread_id derivation (continuidade entre turnos)
            #   • prior_state retrieval (Bug 6 fix — state loss between turns)
            #   • _build_state (merge right_panel_form + metadata + prior)
            #   • manager_preferences apply_to_state (centralizado, não duplicar)
            #   • graph.stream_invoke (streaming token-by-token)
            #   • record_job_completion on handoff (idempotente, centralizado)
            # Frente 3 (2026-05-29): canonical SEMPRE trata o domínio wizard.
            # Em exceção dura, falha alto com erro explícito ao cliente e
            # encerra o turno — NUNCA cai pro ReAct legacy (REGRA 4
            # anti-silent-fallback). O fallback silencioso mascarava crashes
            # do canonical com respostas de um agente diferente.
            if active_domain == "wizard":
                _wizard_canonical_handled = False
                try:
                    from app.domains.job_creation.services.wizard_session_service import (
                        WizardSessionService,
                    )

                    # Stream callback retransmite tokens LLM para o cliente WS
                    async def _wiz_on_token(_chunk: str) -> None:
                        try:
                            await ws_mgr.send_to_session(session_id, {
                                "type": "token",
                                "session_id": session_id,
                                "domain": "wizard",
                                "delta": mask_pii(_chunk) if isinstance(_chunk, str) else _chunk,
                            })
                        except Exception:
                            pass  # fail-silent — streaming não bloqueia

                    # Task #1080: canonical pure derive — no msg["thread_id"] honor.
                    from app.shared.sessions import derive_thread_id as _derive_tid
                    _wiz_thread_id = _derive_tid(company_id, session_id)
                    # P0 email fix (Paulo 2026-05-31): passa a mensagem CRUA
                    # (pre-masking) ao wizard para captura deterministica do
                    # email do gestor no servidor. NUNCA vai ao LLM (o wizard
                    # extrai via regex e grava no state). content segue mascarado.
                    try:
                        context = {**(context or {}), "_raw_user_message": _c3b_result.original_message}
                    except Exception:
                        pass
                    _wiz_message, _wiz_payload, _tokens_emitted = await WizardSessionService.process_message(
                        thread_id=_wiz_thread_id,
                        user_message=content,
                        user_id=user_id,
                        company_id=company_id,
                        session_id=session_id,
                        context=context,
                        on_token=_wiz_on_token,
                    )

                    _wiz_clean = mask_pii(_strip_react_json(_wiz_message or ""))
                    await ws_mgr.send_to_session(session_id, serialize_message(
                        content=_wiz_clean,
                        confidence=0.95,
                        domain="wizard",
                        source="wizard_session_canonical",
                    ))
                    conversation_history.append({"role": "user", "content": content})
                    conversation_history.append({"role": "assistant", "content": _wiz_clean})
                    await _persist_chat_turn(
                        (context or {}).get("conversation_id"), company_id, content, _wiz_clean
                    )

                    # ws_stage_payload -> panel update event (Onda 2 PLAN_FIX_wizard_memory_loss
                    # 2026-05-10: include thread_id explicitly so FE persists session)
                    # original comment:
                    # → panel update event
                    if _wiz_payload:
                        await ws_mgr.send_to_session(session_id, {
                            "type": "wizard_stage",
                            "session_id": session_id,
                            "thread_id": _wiz_thread_id,
                            "stage": _wiz_payload.get("stage", "wizard"),
                            **_wiz_payload,
                        })
                    _wizard_canonical_handled = True
                except Exception as _wiz_exc:
                    logger.error(
                        "[AgentChatWS] WizardSessionService canonical path crashed: %s",
                        _wiz_exc, exc_info=True,
                    )
                    await ws_mgr.send_to_session(session_id, serialize_error(
                        "Não consegui processar a criação da vaga agora. "
                        "Pode tentar novamente em instantes?",
                        "wizard_canonical_error",
                    ))
                    continue  # falha alto — NUNCA cai pro ReAct legacy (REGRA 4)
                if _wizard_canonical_handled:
                    continue  # canonical handled — skip ReAct loop

            agent = _get_agent(active_domain)
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

                clean_message = mask_pii(_strip_react_json(output.message or ""))

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
                await _persist_chat_turn(
                    (context or {}).get("conversation_id"), company_id, content, clean_message
                )

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
                await ws_mgr.send_to_session(session_id, serialize_message(
                    content=clean_message,
                    confidence=output.confidence,
                    domain=active_domain,
                    source="direct",
                    actions=[a.dict() for a in (output.actions or [])],
                    navigation=output.navigation.dict() if output.navigation else None,
                    state_updates=output.state_updates or None,
                    fairness_warnings=_fairness_warnings or None,
                    # PR6 (Task #1006) — Bridge IA→UI: forward tool execution
                    # metadata so the FE WS consumer can dispatch the
                    # `lia:settings-updated` CustomEvent (origin="agent") for
                    # canonical save tools, refreshing settings cards without
                    # full-page reload.
                    tool_results=output.tool_results or None,
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


class HTTPChatRequest(WeDoBaseModel):
    message: str
    domain: str = ""
    session_id: str = ""
    context: dict[str, Any] = {}
    # Rail A hint metadata — promotes into context["metadata"] for cascaded_router
    metadata: dict[str, Any] = {}

    class Config:
        from_attributes = True


class HTTPChatResponse(BaseModel):
    content: str
    confidence: float = 0.0
    domain: str = ""
    actions: list = []
    error: str | None = None


@router.post("/chat/message", response_model=HTTPChatResponse)
async def http_chat_message(req: HTTPChatRequest, request: Request, company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
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
    # Rail A hint: promote req.metadata into context (idempotent — caller wins)
    if not context.get("metadata") and req.metadata:
        context["metadata"] = req.metadata

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
            from app.orchestrator.routing.cascaded_router import CascadedRouter
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



# ---------------------------------------------------------------------------
# _resume_wizard_canonical — sync HITL resume (used by REST + tests)
# ---------------------------------------------------------------------------

def _resume_wizard_canonical(
    thread_id: str,
    message: dict,
) -> "tuple[str, dict]":
    """Resume a wizard session after HITL approval (sync, non-streaming).

    Retrieves prior checkpointed state, merges approval updates from *message*,
    and invokes JobCreationGraph.resume().

    Args:
        thread_id: Wizard session / checkpointer thread identifier.
        message: Dict that may contain:
            - ``"context"``: Flat dict of recruiter updates
              (e.g. ``{"draft": {...}}``).
            - ``"approval_payload"``: Dict of additional params merged into
              state (e.g. ``{"approved_by": "u-7"}``).

    Returns:
        Tuple of:
        - ``message_str``: Recruiter-facing status message.
        - ``stage_payload``: The raw ``ws_stage_payload`` dict (or ``{}``).
    """
    from app.domains.job_creation import graph as graph_module

    jc_graph_inst = graph_module.job_creation_graph

    # Retrieve prior state from checkpointer.
    try:
        prior_snapshot = jc_graph_inst._graph.get_state(
            {"configurable": {"thread_id": thread_id}}
        )
        prior_state: dict = dict(prior_snapshot.values) if prior_snapshot else {}
    except Exception:
        prior_state = {}

    # Build merged updates: approval_payload fields + context flags.
    context_updates: dict = message.get("context") or {}
    approval_payload: dict = message.get("approval_payload") or {}

    resume_updates: dict = {
        "hitl_approved": True,
        **approval_payload,   # e.g. approved_by, approval notes
        **context_updates,    # e.g. draft, updated fields
    }

    # Invoke via canonical resume API (keeps audit callback wired).
    final_state: dict = jc_graph_inst.resume(thread_id, prior_state, resume_updates)

    # Extract stage payload and recruiter-facing message.
    stage_payload: dict = final_state.get("ws_stage_payload") or {}
    message_str: str = ""
    if stage_payload:
        message_str = (
            stage_payload.get("data", {}).get("message")
            or stage_payload.get("message")
            or ""
        )
    if not message_str:
        cs = final_state.get("current_stage", "")
        if cs == "completed":
            message_str = "Vaga criada com sucesso."
        else:
            message_str = "Captei a vaga. Vou seguir para o próximo passo."

    return message_str, stage_payload


# _resume_wizard_canonical_streaming — HITL/approval resume via canonical graph
# ---------------------------------------------------------------------------

async def _resume_wizard_canonical_streaming(
    thread_id: str,
    message: dict,
    on_token,
) -> "tuple[str, dict, int]":
    """Resume a wizard session after HITL approval, with token streaming.

    Merges the prior checkpointed state with recruiter updates contained in
    *message*, then delegates to ``JobCreationGraph.stream_invoke`` which
    drives the compiled LangGraph with streaming output.

    Args:
        thread_id: Wizard session / checkpointer thread identifier.
        message: Dict containing:
            - ``"context"``: Flat dict of recruiter-supplied updates
              (e.g. ``{"hitl_approved": True, "draft": {...}}``).
            - ``"approval_payload"``: Optional dict of additional params
              (merged into state at the top level).
        on_token: Async callable that receives each streaming LLM chunk.

    Returns:
        Tuple of:
        - ``message_str``: Human-readable status message extracted from
          the terminal ``ws_stage_payload``, or a safe fallback.
        - ``stage_payload``: The raw ``ws_stage_payload`` dict (or ``{}``).
        - ``tokens_emitted``: Number of tokens reported by ``stream_invoke``.
    """
    from app.domains.job_creation import graph as graph_module

    # Retrieve prior state from checkpointer.  On miss/error, fall back to
    # an empty dict so the resume is still safe.
    try:
        prior_snapshot = graph_module.job_creation_graph._graph.get_state(
            {"configurable": {"thread_id": thread_id}}
        )
        prior_state: dict = dict(prior_snapshot.values) if prior_snapshot else {}
    except Exception:
        prior_state = {}

    # Build merged state: prior < approval_payload < context flags.
    context_updates: dict = message.get("context") or {}
    approval_updates: dict = message.get("approval_payload") or {}
    merged_state: dict = {**prior_state, **approval_updates, **context_updates}

    # Invoke the graph with streaming.
    result_tuple = await graph_module.job_creation_graph.stream_invoke(
        merged_state, thread_id, on_token
    )
    final_state, tokens_emitted = result_tuple

    # Extract stage payload and human message.
    stage_payload: dict = final_state.get("ws_stage_payload") or {}
    if stage_payload:
        message_str: str = (
            stage_payload.get("data", {}).get("message")
            or stage_payload.get("message")
            or "Captei a vaga. Vou seguir para o próximo passo."
        )
    elif final_state.get("current_stage") == "completed":
        message_str = "Vaga criada com sucesso."
    else:
        message_str = "Captei a vaga. Vou seguir para o próximo passo."

    return message_str, stage_payload, tokens_emitted
