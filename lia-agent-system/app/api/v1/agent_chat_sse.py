"""
SSE Streaming endpoint for Agent Chat — POST /api/v1/chat/{session_id}/stream

Fallback transport for environments where WebSocket is unavailable
(corporate proxies, restrictive firewalls, load balancers).

Protocol:
  Client → Server: POST with JSON body { message, domain, context }
  Server → Client: SSE stream with events:
    id: <event_id>
    data: { "type": "thinking" | "token" | "message" | "error" | ... }

  Reconnection: client sends Last-Event-ID header to resume from last event.

Auth: Bearer token in Authorization header.

Note: Last-Event-ID header is accepted and tracked by the client for future
reconnection support. Full event replay (server-side event store) is planned
for a subsequent phase. Currently, if the SSE connection drops mid-stream,
the client re-sends the original message.
"""
import asyncio
import contextlib
import hashlib
import json
import logging
import os
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query, Request
from pydantic import BaseModel
from starlette.responses import StreamingResponse

from app.core.config import settings
from app.shared.chat_event_serializer import (
    format_sse_event,
    format_sse_keepalive,
    serialize_error,
    serialize_message,
    serialize_panel_update,
    serialize_thinking,
    serialize_token,
    serialize_token_done,
    serialize_tool_started,
    serialize_tool_finished,
    serialize_reasoning_step,
)
from app.shared.prompt_injection import PromptInjectionGuard
from app.shared.pii_masking import mask_pii_outbound
from app.domains.credits.services.token_budget_service import (
    check_budget,
    get_plan_for_company,
    increment_usage,
)
from fastapi import Depends
from app.shared.security.require_company_id import require_company_id
from app.shared.errors import LIAError
from app.shared.types import WeDoBaseModel
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, SESSION_ID_PATH_PATTERN, reorder_collection_before_item

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# PII identity cache: (user_id, company_id) -> (mask_bool, user_name, user_email, ts)
# TTL=300s: user role/PII visibility does not change per-turn.
# Harness: guide=computacional (deterministic cache, no inference).
# ---------------------------------------------------------------------------
import time as _time_module
_pii_identity_cache: dict[tuple, tuple] = {}
_PII_IDENTITY_TTL = 300.0  # 5 minutes

router = APIRouter(tags=["chat-sse"])
# ---------------------------------------------------------------------------
# STREAMING BEHAVIOR (UC-P3-06)
# ---------------------------------------------------------------------------
# Transport: Server-Sent Events (SSE) via HTTP POST — fallback for environments
# where WebSocket is unavailable (corporate proxies, load-balancers).
#
# Token delivery: token-by-token (one SSE event per token chunk).
# Each token is emitted immediately via the streaming_callback injected into
# the agent context. The agent runs in a background asyncio Task while tokens
# flow through an asyncio.Queue into the event_generator coroutine.
#
# Event types emitted (data.type field in each SSE data payload):
#   "thinking"    — agent is processing; optionally includes a thought/step field
#   "token"       — single text token chunk (content field)
#   "token_done"  — stream complete; includes tokens_sent count
#   "message"     — full assembled response (content, actions, navigation, etc.)
#   "panel_update"— side-panel update (panel_type, panel_data, panel_title, action)
#   "error"       — error occurred (reason, error_code fields)
#   keepalive     — empty comment line ": keepalive\n\n" sent every 30s of silence
#
# Event IDs: "<session_id[:8]>-<seq>" — sequential, used for Last-Event-ID reconnection.
# Reconnection: client sends Last-Event-ID header; server-side event replay is NOT
# yet implemented (full replay planned for a subsequent phase). On reconnect, the
# client re-sends the original message.
#
# Frontend expectations:
#   1. Open EventSource / fetch with ReadableStream on POST /api/v1/chat/{session_id}/stream
#   2. Listen for "token" events to render streaming text incrementally
#   3. Wait for "message" event to get final assembled response + actions
#   4. Handle "error" events and display user-facing message
#   5. Set Authorization: Bearer <token> header (required — 401 if missing)
#
# Configurable via environment:
#   LLM_TIMEOUT_SECONDS — agent processing timeout in seconds (default varies)
#   LIA_WS_TOKEN_STREAMING — enables token streaming in WS transport (sibling flag)
# ---------------------------------------------------------------------------


_AGENT_TIMEOUT = settings.LLM_TIMEOUT_SECONDS


async def _drain_queue_with_keepalive(queue, is_done, next_id, *, poll_s: float = 0.5, keepalive_after_s: float = 15.0):
    """Drena a fila de eventos SSE emitindo keepalive em silêncio prolongado.

    Harness (sensor de liveness): operações longas do wizard (geração WSI ~100s,
    JD ~60s) NÃO podem deixar o stream SSE em silêncio — o gateway HTTP derruba a
    conexão (502). Mesma estratégia do loop principal (format_sse_keepalive), porém
    com poll curto (responsivo a tokens) + heartbeat throttled a cada
    keepalive_after_s de silêncio. Extraído do route handler para ser testável.
    """
    silent = 0.0
    while not is_done():
        try:
            tok = await asyncio.wait_for(queue.get(), timeout=poll_s)
            silent = 0.0
            if tok is not None:
                yield format_sse_event(tok, next_id())
        except (asyncio.TimeoutError, TimeoutError):
            silent += poll_s
            if silent >= keepalive_after_s:
                silent = 0.0
                yield format_sse_keepalive()

_injection_guard = PromptInjectionGuard()


class SSEChatRequest(WeDoBaseModel):
    message: str
    domain: str = "recruiter_assistant"
    context: dict[str, Any] = {}
    conversation_id: str | None = None
    # HITL (AUD-4 1b-c): quando o usuario aprova uma acao sensivel pendente, o FE
    # re-envia a mensagem original COM este id. Server valida + libera o gate.
    approve_pending_id: str | None = None
    # Vaga em Foco: when recruiter is on a job kanban page, FE stores the
    # active job and sends its ID here so LIA can prioritize that job.
    # Multi-tenancy enforced via get_vacancy_by_id_and_company (company_id from JWT).
    focused_job_id: str | None = None
    focused_job_mode: str | None = None  # "active"|"background" [Fix P1 focus-mode]

    class Config:
        from_attributes = True


def _extract_auth(token: str | None) -> dict[str, Any]:
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


def _strip_thought_tags(text: str) -> str:
    import re
    cleaned = re.sub(r'<thought>[\s\S]*?</thought>', '', text, flags=re.IGNORECASE)
    cleaned = re.sub(r'<thought>[\s\S]*', '', cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def _strip_react_json(text: str) -> str:
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


def _build_approval_frame(pending_id: str, hitl_pending: dict) -> dict:
    """Monta o frame SSE approval_required a partir do hitl_pending drenado do
    metadata do agente (sink hitl_pending_sink). Mesmo shape do ramo supervisor
    (_orchestrator_result_to_frames em chat.py:947). Puro/testavel."""
    _hp = hitl_pending or {}
    return {
        "type": "approval_required",
        "pending_id": pending_id or "",
        "description": _hp.get("message") or "",
        "action": _hp.get("tool") or "",
    }


async def _detect_hitl_approval(
    *, approve_pending_id, session_id: str, company_id: str, user_id: str
) -> bool:
    """Server-authoritative: True se o usuario aprovou um pending VALIDO desta
    sessao. Valida que existe pending com esse id pra este thread (session_id)
    ANTES de receive_approval (audit LGPD). NUNCA confia na LLM. Fail-CLOSED:
    sem id / sem match / erro -> False (acao NAO e liberada)."""
    if not approve_pending_id:
        return False
    try:
        from app.services.hitl_service import hitl_service as _hsvc
        pending = await _hsvc.get_pending(session_id)
        if not pending or pending.get("pending_id") != approve_pending_id:
            logger.warning(
                "[SSEChat] HITL approve_pending_id sem match nesta sessao "
                "(ignorado): %s", approve_pending_id,
            )
            return False
        await _hsvc.receive_approval(
            thread_id=session_id,
            pending_id=approve_pending_id,
            approved=True,
            resolved_by=user_id,
            company_id=company_id or "",
            domain=pending.get("domain", ""),
            action=pending.get("action", ""),
        )
        logger.info(
            "[SSEChat] HITL aprovado pending=%s session=%s",
            approve_pending_id, session_id,
        )
        return True
    except Exception as exc:
        logger.warning(
            "[SSEChat] HITL approval detection falhou (fail-closed): %s", exc
        )
        return False


class SSEActionRequest(WeDoBaseModel):
    type: str
    pending_id: str = ""
    thread_id: str = ""
    approved: bool = False
    session_id: str = ""

    class Config:
        from_attributes = True


@router.post("/chat/action", response_model=None)
async def sse_chat_action(
    req: SSEActionRequest,
    request: Request,
    authorization: str = Header(default=""),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    REST endpoint for HITL approval actions when using SSE transport.

    Accepts the same approval_response payload that would normally be sent
    via WebSocket sendRaw, but via HTTP POST.
    """
    auth_header = authorization
    token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else None
    auth = _extract_auth(token)
    user_id = auth["user_id"]

    if not token or user_id == "anonymous":
        raise HTTPException(status_code=401, detail="Authentication required")

    if req.type == "approval_response" and req.pending_id:
        try:
            # AUD-4 fix: HITLService nao tem approve/reject -> era AttributeError
            # (500). O metodo canonico e receive_approval (mesmo do WS). Usa o
            # singleton compartilhado p/ casar com o pending mintado no /stream.
            from app.services.hitl_service import hitl_service
            _thread = req.thread_id or req.session_id
            await hitl_service.receive_approval(
                thread_id=_thread,
                pending_id=req.pending_id,
                approved=bool(req.approved),
                resolved_by=user_id,
            )
            return {"status": "ok", "approved": req.approved}
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("[SSEAction] HITL action failed: %s", exc, exc_info=True)
            raise LIAError(message="Failed to process approval")

    return {"status": "ok", "message": "Action received"}


@router.post("/chat/{session_id}/stream", response_model=None)
async def sse_chat_stream(
    session_id: Annotated[str, Path(pattern=SESSION_ID_PATH_PATTERN)],
    req: SSEChatRequest,
    request: Request,
    authorization: str = Header(default=""),
    last_event_id: str = Header(default="", alias="Last-Event-ID"),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    SSE streaming endpoint for agent chat.

    Processes a single message and returns the response as a Server-Sent Events stream.
    Supports reconnection via Last-Event-ID header.
    """
    auth_header = authorization
    token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else None
    auth = _extract_auth(token)
    company_id = auth["company_id"]
    user_id = auth["user_id"]

    if not token or user_id == "anonymous":
        raise HTTPException(status_code=401, detail="Authentication required")

    content = req.message.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    inj_result = _injection_guard.check(content)
    if inj_result.risk_level == "high":
        logger.warning(
            "[SSEChat][SEG-1] Prompt injection blocked session=%s patterns=%s",
            session_id, inj_result.matched_patterns,
        )
        raise HTTPException(
            status_code=422,
            detail="Mensagem bloqueada por segurança. Por favor, reformule sua solicitação.",
        )


    # LIA-P03: Add FairnessGuard and SecurityPatterns to agent SSE
    try:
        from app.shared.compliance.fairness_guard import FairnessGuard
        from app.shared.robustness.security_patterns import check_input_security

        _security_result = check_input_security(content)
        if _security_result and _security_result.get("blocked"):
            raise HTTPException(
                status_code=400,
                detail="Mensagem bloqueada por verificacao de seguranca."
            )

        _fg = FairnessGuard()
        _fr = _fg.check(content)
        if _fr and _fr.is_blocked:
            import asyncio as _asyncio
            try:
                _asyncio.get_event_loop().create_task(
                    _fg.log_check(
                        result=_fr,
                        context="chat_sse",
                        company_id=company_id or None,
                        recruiter_id=user_id or None,
                        session_id=session_id or None,
                    )
                )
            except Exception as _lc_exc:
                logger.debug("[LIA-P03] log_check enqueue failed (fail-open): %s", _lc_exc)
            raise HTTPException(
                status_code=400,
                detail=_fr.educational_message or "Sua solicitacao contem termos que podem gerar vies."
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.debug("[LIA-P03] Agent SSE compliance skipped: %s", e)

    # LGPD (2026-05-31): harmonizar com o WS — mascarar PII no inbound ANTES
    # de qualquer LLM. O WS faz via pre_compliance; o SSE nao fazia (email/CPF/
    # telefone iam crus ao LLM). Captura o texto CRU antes do strip para a
    # captura deterministica do email do gestor no wizard (que grava no state
    # mas NUNCA envia ao LLM — o LLM ve o content mascarado).
    _raw_content = content
    try:
        from app.shared.pii_masking import strip_pii_for_llm_prompt
        content = strip_pii_for_llm_prompt(content, mask_names=False)  # chat do recrutador: preserva nome/titulo p/ busca; CPF/email/tel seguem mascarados
    except Exception as _pii_exc:
        logger.warning("[SSEChat] PII strip inbound failed (fail-open): %s", _pii_exc)

    active_domain = req.domain or "recruiter_assistant"
    context = req.context or {}
    context.setdefault("company_id", company_id)
    context.setdefault("user_id", user_id)
    context["_raw_user_message"] = _raw_content
    if req.conversation_id:
        context["conversation_id"] = req.conversation_id

    # HITL approval detection (AUD-4 1b-b/c): turno que carrega approve_pending_id
    # = usuario aprovou a acao sensivel pendente. _approved_turn liga o ContextVar
    # DENTRO da task de dispatch (abaixo) -> a tool re-chamada passa o gate.
    _approved_turn = await _detect_hitl_approval(
        approve_pending_id=req.approve_pending_id,
        session_id=session_id,
        company_id=company_id,
        user_id=user_id,
    )


    # ── SSE reconnect dedup guard (GAP-09-002) ──────────────────────
    # When FE reconnects after a stream drop, it re-POSTs the same message.
    # Without this guard, the agent re-processes and tools execute twice.
    # Redis SETNX ensures at-most-once processing per (session, message) pair.
    _turn_hash = hashlib.sha256(f"{session_id}:{content}:{user_id}".encode()).hexdigest()[:16]
    _dedup_key = f"sse_turn_dedup:{session_id}:{_turn_hash}"
    _is_reconnect = bool(last_event_id)
    try:
        from app.core.redis_client import get_redis
        _redis = get_redis()
        if _redis:
            _already = _redis.get(_dedup_key)
            if _already and _is_reconnect:
                logger.info(
                    "[SSE-dedup] Reconnect detected session=%s last_event_id=%s — skipping re-processing",
                    session_id, last_event_id,
                )
                async def _reconnect_generator():
                    # GAP-09-002: emit turn_id so FE can identify completed turns on reconnect
                    yield format_sse_event(
                        {"type": "stream_start", "turn_id": _turn_hash},
                        f"{session_id[:8]}-reconn-0",
                    )
                    yield format_sse_event(
                        {"type": "info", "message": "Reconectado — resposta anterior preservada."},
                        f"{session_id[:8]}-reconn-1",
                    )
                    yield format_sse_event(
                        {"type": "done", "reconnected": True},
                        f"{session_id[:8]}-reconn-2",
                    )
                return StreamingResponse(
                    _reconnect_generator(),
                    media_type="text/event-stream",
                    headers={"Cache-Control": "no-cache", "Connection": "keep-alive",
                             "X-Accel-Buffering": "no", "X-Transport": "sse"},
                )
            if _already and not _is_reconnect:
                logger.warning(
                    "[SSE-dedup] Duplicate POST without Last-Event-ID session=%s — allowing (may be intentional retry)",
                    session_id,
                )
            else:
                _redis.set(_dedup_key, "1", ex=120, nx=True)
    except Exception as _dedup_exc:
        logger.debug("[SSE-dedup] Redis dedup check failed (fail-open): %s", _dedup_exc)
    # ── end dedup guard ─────────────────────────────────────────────

    async def event_generator():
        event_seq = 0

        def next_id() -> str:
            nonlocal event_seq
            event_seq += 1
            return f"{session_id[:8]}-{event_seq}"

        # GAP-09-002: emit stable turn_id at stream start so FE can track
        # completed turns and skip duplicate processing on reconnect.
        yield format_sse_event(
            {"type": "stream_start", "turn_id": _turn_hash},
            f"{session_id[:8]}-0",
        )
        # Fix 1: emit thinking IMMEDIATELY — before any DB queries so the user
        # sees "Pensando..." without a blank-screen delay.
        yield format_sse_event(serialize_thinking(), next_id())
        # Emit first reasoning phase immediately so FE AgentActivityTimeline
        # shows dynamic multistep instead of static "Pensando" fallback.
        # _process_langgraph emits again later; FE deduplicates via seenPhasesRef.
        yield format_sse_event(serialize_reasoning_step("understanding"), next_id())

        # Fix 1 (continued) — B2 (2026-06): per-turn identity masking
        # (CPF/RG/CNPJ). Now runs in parallel with budget + router + tenant
        # context so it no longer blocks the thinking event.
        # ContextVar is request-context-scoped — no leak across turns.
        # Guaranteed to finish before first token (agent takes >>200 ms).
        async def _b2_setup_async():
            try:
                import uuid as _uuid_b2
                from app.shared.pii_masking import set_chat_pii_mask_identity, chat_should_mask_identity
                if user_id and user_id != "anonymous" and company_id:
                    _b2_cache_key = (str(user_id), str(company_id))
                    _b2_cached = _pii_identity_cache.get(_b2_cache_key)
                    if _b2_cached is not None and _time_module.time() - _b2_cached[3] < _PII_IDENTITY_TTL:
                        # Cache hit: apply cached identity without any DB round-trip
                        _mask_b2, _name_b2, _email_b2, _ = _b2_cached
                        set_chat_pii_mask_identity(_mask_b2)
                        context.setdefault("user_name", _name_b2)
                        context.setdefault("user_email", _email_b2)
                        logger.debug("[B2] pii_identity cache hit user=%s", user_id)
                    else:
                        from app.core.database import AsyncSessionLocal as _SessB2
                        from app.domains.company.repositories.user_repository import UserRepository as _UserRepoB2
                        from app.domains.hiring_policy.repositories.hiring_policy_repository import HiringPolicyRepository as _HPRepoB2
                        async with _SessB2() as _db_b2:
                            _u_b2 = await _UserRepoB2(_db_b2).get_by_id(_uuid_b2.UUID(str(user_id)), company_id=company_id)
                            _pol_b2 = await _HPRepoB2(_db_b2).get_by_company(company_id)
                        _rd_b2 = (getattr(_pol_b2, "pii_visibility_defaults", None) or {}) if _pol_b2 else {}
                        if _u_b2 is not None:
                            _mask_val = chat_should_mask_identity(_u_b2, _rd_b2)
                            _name_val = getattr(_u_b2, "name", None) or None
                            _email_val = getattr(_u_b2, "email", None) or None
                            set_chat_pii_mask_identity(_mask_val)
                            # W0-A: wizard recruiter identity — carried in context so _build_state can populate
                            # parsed_recruiter_name/email at session start without a separate DB lookup at publish.
                            context.setdefault("user_name", _name_val)
                            context.setdefault("user_email", _email_val)
                            # Store in cache for subsequent turns (TTL=300s)
                            _pii_identity_cache[_b2_cache_key] = (_mask_val, _name_val, _email_val, _time_module.time())
            except Exception:
                logger.debug("[B2] chat identity-masking setup skipped (non-blocking)", exc_info=True)

        async def _check_budget_async():
            try:
                plan = await get_plan_for_company(company_id)
                return await check_budget(company_id, plan)
            except Exception as exc:
                logger.warning("[SSEChat] Budget check failed — continuing: %s", exc)
                return True, 0, 0

        # Fix 2: tenant context now runs in parallel with the router so its
        # ~200 ms DB query is hidden behind routing latency.
        async def _inject_tenant_context_async():
            try:
                from app.core.database import AsyncSessionLocal
                from app.shared.services.tenant_context_service import TenantContextService
                async with AsyncSessionLocal() as _tc_db:
                    _tenant_ctx = await TenantContextService().get_context(
                        company_id=company_id, db=_tc_db,
                    )
                    _snippet = _tenant_ctx.to_prompt_snippet()
                    if company_id:
                        _snippet += "\n" + TenantContextService.build_authenticated_snippet(company_id)
                    context["tenant_context_snippet"] = _snippet
                    logger.info(
                        "[SSEChat] tenant_context injected company=%s name=%s",
                        company_id, _tenant_ctx.company_name,
                    )
            except Exception as _tc_exc:
                if company_id:
                    from app.shared.services.tenant_context_service import TenantContextService
                    context["tenant_context_snippet"] = TenantContextService.build_authenticated_snippet(company_id)
                    logger.info("[SSEChat] tenant_context fallback: authenticated snippet for %s", company_id)
                else:
                    logger.warning("[SSEChat] TenantContext injection skipped: %s", _tc_exc)

        async def _inject_focused_job_async():
            """Inject Vaga em Foco context into the chat context dict.

            Runs in parallel with other setup tasks. Fail-open: any exception
            (missing job, invalid UUID, DB error) is silently logged at DEBUG
            level — a stale focused_job_id must never break the chat turn.
            Multi-tenancy: company_id comes from JWT (not from req payload).
            """
            _fj_id = req.focused_job_id
            if not _fj_id or not company_id:
                return
            try:
                from app.core.database import AsyncSessionLocal
                from app.shared.services.lia_agent_context_builder import (
                    build_focused_job_context,
                )

                async with AsyncSessionLocal() as _fj_db:
                    _fj_snippet = await build_focused_job_context(
                        _fj_id, company_id, _fj_db
                    )
                    if _fj_snippet:
                        # [Fix P1 focus-mode] modo background: sem auto-briefing
                        if req.focused_job_mode == "background":
                            _fj_snippet += (
                                "\n(Nota: usuario NAO esta na pagina desta vaga agora"
                                " - disponivel como referencia. Nao auto-briefing.)"
                            )
                        context["focused_job_snippet"] = _fj_snippet
                        logger.info(
                            "[SSEChat] focused_job injected id=%s", _fj_id
                        )
            except Exception as _fj_exc:
                logger.debug(
                    "[SSEChat] focused_job injection skipped: %s", _fj_exc
                )

        async def _route_domain_async():
            if active_domain not in ("auto", "recruiter_assistant", ""):
                return active_domain

            # Task #1080: wizard session pin BEFORE router (canonical layer
            # for "this conversation is the wizard"). Mirrors agent_chat_ws.
            try:
                from app.shared.sessions import should_pin_to_wizard
                _settings_hint = (context.get("metadata") or {}).get("domain_hint")
                if await should_pin_to_wizard(company_id, session_id, content, domain_hint=_settings_hint):
                    logger.info(
                        "[SSEChat] wizard_session_pin: session=%s company=%s "
                        "→ wizard (Task #1080)", session_id, company_id,
                    )
                    return "wizard"
            except Exception as _pin_exc:
                logger.debug("[SSEChat] wizard_session_pin skipped: %s", _pin_exc)

            # Bonus fix: when LIA_FEDERATED_PRIMARY is active the full
            # CascadedRouter result is discarded for non-special domains anyway
            # (recruiter_copilot is always chosen). Skip the expensive Tier-5
            # Gemini Flash call and use only the lightweight FastRouter (regex,
            # no LLM) to detect the domains that actually matter here:
            # wizard / kanban / pipeline_transition / sourcing.
            # Everything else returns active_domain — federated agent handles it.
            try:
                from app.tools.scope_config import federated_primary_enabled as _fed_check
                _is_federated = _fed_check()
            except Exception:
                _is_federated = False

            if _is_federated:
                try:
                    from app.orchestrator.routing.fast_router import FastRouter
                    from lia_config.config import settings as _cfg
                    _fast_result = FastRouter().match(content)
                    _ROUTABLE = {"wizard", "kanban", "pipeline_transition", "sourcing"}
                    if (
                        _fast_result
                        and _fast_result.confidence >= _cfg.ROUTER_FAST_CONFIDENCE_THRESHOLD
                        and _fast_result.domain_id in _ROUTABLE
                    ):
                        logger.debug(
                            "[SSEChat] federated fast-path → %s (conf=%.2f)",
                            _fast_result.domain_id, _fast_result.confidence,
                        )
                        return _fast_result.domain_id
                except Exception as _fp_exc:
                    logger.debug("[SSEChat] federated fast-path skipped: %s", _fp_exc)
                return active_domain

            # Fix 4: use process-level singleton so the in-process LRU cache
            # survives across turns (previously CascadedRouter() was instantiated
            # per request, making the 1000-entry LRU permanently empty).
            try:
                from app.orchestrator.routing.cascaded_router import get_router
                _router = get_router()
                route = await _router.route(
                    message=content, context=context, session_id=session_id,
                )
                if not route.needs_clarification:
                    return route.domain_id
            except Exception:
                pass
            return active_domain

        # All 5 setup tasks run in parallel — budget, routing, B2 identity
        # masking, tenant context, and focused job are fully independent I/O ops.
        # [HARNESS FIX P0 keepalive-setup] Keepalive loop emite SSE comment a cada 8s
        # durante o gather para evitar timeout de 90s no gateway/frontend.
        _setup_ka_q: asyncio.Queue = asyncio.Queue()
        _setup_ka_stop = asyncio.Event()

        async def _setup_ka_loop() -> None:
            try:
                while not _setup_ka_stop.is_set():
                    await asyncio.sleep(8)
                    if not _setup_ka_stop.is_set():
                        await _setup_ka_q.put(format_sse_keepalive())
            except asyncio.CancelledError:
                pass

        _setup_ka_task = asyncio.create_task(_setup_ka_loop())
        _gather_task = asyncio.create_task(asyncio.gather(
            _check_budget_async(),
            _route_domain_async(),
            _b2_setup_async(),
            _inject_tenant_context_async(),
            _inject_focused_job_async(),
        ))
        try:
            while not _gather_task.done():
                try:
                    _ka_chunk = _setup_ka_q.get_nowait()
                    yield _ka_chunk
                except asyncio.QueueEmpty:
                    pass
                await asyncio.sleep(0.1)
            _gather_results = await _gather_task
        finally:
            _setup_ka_stop.set()
            _setup_ka_task.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await _setup_ka_task

        budget_result, resolved_domain, _, _, _ = _gather_results
        budget_ok, used, limit = budget_result
        # Vaga em Foco: append focused job snippet to tenant context so all
        # downstream agents see it as part of the injected company context.
        if context.get("focused_job_snippet"):
            context["tenant_context_snippet"] = (
                context.get("tenant_context_snippet", "")
                + context.pop("focused_job_snippet")
            )
        if not budget_ok:
            yield format_sse_event(
                serialize_error(
                    f"Limite diário de uso de IA atingido ({used:,} / {limit:,} tokens). "
                    "O budget será renovado à meia-noite UTC.",
                    "budget_exhausted",
                ),
                next_id(),
            )
            return

        # ── T12: Post-wizard continuation check (before routing) ──────
        # When a composite request like "crie e publique" was parked and
        # the wizard already finished (status=awaiting_confirmation), the
        # next recruiter message may be a Y/N reply. Intercept it BEFORE
        # routing to wizard/agent so the continuation can be consumed.
        if os.environ.get("LIA_POST_WIZARD_CONTINUATION", "1") == "1":
            try:
                from app.orchestrator.routing.post_wizard_continuation import (
                    get_continuation as _pwc_get,
                    clear_continuation as _pwc_clear,
                    dispatch_for as _pwc_dispatch,
                )
                from app.orchestrator.routing.confirmation_classifier import (
                    classify_confirmation as _pwc_classify,
                )

                _pwc_state = _pwc_get(req.conversation_id or session_id)
                if _pwc_state is not None and _pwc_state.awaiting_confirmation:
                    _pwc_decision = _pwc_classify(content)
                    _pwc_conv_id = req.conversation_id or session_id
                    logger.info(
                        "[SSEChat-T12] continuation reply classified=%s conv=%s kind=%s",
                        _pwc_decision,
                        _pwc_conv_id,
                        (_pwc_state.collected_params or {}).get("continuation_kind"),
                    )

                    if _pwc_decision == "no":
                        _pwc_clear(_pwc_conv_id)
                        yield format_sse_event(
                            serialize_message(
                                content=(
                                    "Combinado \u2014 a vaga fica como est\u00e1 por enquanto. "
                                    "Quando quiser seguir, \u00e9 s\u00f3 me avisar."
                                ),
                                confidence=0.95,
                                domain="post_wizard_continuation",
                                source="continuation_declined",
                                conversation_id=_pwc_conv_id,
                            ),
                            next_id(),
                        )
                        return

                    if _pwc_decision == "ambiguous":
                        yield format_sse_event(
                            serialize_message(
                                content=(
                                    "S\u00f3 pra confirmar: quer que eu siga com essa "
                                    "etapa agora? Responda *sim* ou *agora n\u00e3o*."
                                ),
                                confidence=0.95,
                                domain="post_wizard_continuation",
                                source="continuation_clarify",
                                conversation_id=_pwc_conv_id,
                            ),
                            next_id(),
                        )
                        return

                    if _pwc_decision == "yes":
                        _pwc_params = dict(_pwc_state.collected_params or {})
                        _pwc_connected = bool(_pwc_params.get("continuation_connected"))
                        _pwc_disp = _pwc_dispatch(_pwc_params.get("continuation_kind"))
                        _pwc_job_id = _pwc_params.get("job_id")
                        _pwc_clear(_pwc_conv_id)

                        if not _pwc_connected or not _pwc_disp:
                            yield format_sse_event(
                                serialize_message(
                                    content=(
                                        "Essa etapa ainda n\u00e3o est\u00e1 conectada para "
                                        "execu\u00e7\u00e3o autom\u00e1tica \u2014 por enquanto voc\u00ea "
                                        "precisa faz\u00ea-la manualmente. Posso ajudar "
                                        "em mais alguma coisa?"
                                    ),
                                    confidence=0.95,
                                    domain="post_wizard_continuation",
                                    source="continuation_not_connected",
                                    conversation_id=_pwc_conv_id,
                                ),
                                next_id(),
                            )
                            return

                        # Execute via PlanExecutor (same as supervisor path)
                        _pwc_domain_id, _pwc_action_id, _pwc_label = _pwc_disp
                        try:
                            from app.domains.registry import DomainRegistry
                            from app.domains.workflow import DomainWorkflow
                            from app.shared.execution.execution_plan import (
                                AgentTask,
                                ExecutionPlan,
                            )
                            from app.shared.execution.plan_executor import PlanExecutor

                            _pwc_plan = ExecutionPlan(
                                plan_id=f"continuation_{_pwc_conv_id}"
                            )
                            _pwc_plan.detected_pattern = (
                                f"post_wizard_{_pwc_params.get('continuation_kind')}"
                            )
                            _pwc_plan.add_task(
                                AgentTask(
                                    task_id="task_0",
                                    domain_id=_pwc_domain_id,
                                    action_id=_pwc_action_id,
                                    params=(
                                        {"job_id": _pwc_job_id}
                                        if _pwc_job_id
                                        else {}
                                    ),
                                )
                            )
                            _pwc_executor = PlanExecutor(
                                domain_registry=DomainRegistry(),
                                domain_workflow=DomainWorkflow(),
                            )
                            _pwc_completed = await _pwc_executor.execute(
                                _pwc_plan,
                                user_id=str(user_id or "system"),
                                session_id=_pwc_conv_id,
                                tenant_id=str(company_id) if company_id else None,
                                base_context=(
                                    {"job_id": _pwc_job_id}
                                    if _pwc_job_id
                                    else None
                                ),
                            )
                            _pwc_resp = _pwc_executor.build_consolidated_response(
                                _pwc_completed
                            )
                            logger.info(
                                "[SSEChat-T12] continuation executed kind=%s "
                                "job_id=%s status=%s",
                                _pwc_params.get("continuation_kind"),
                                _pwc_job_id,
                                _pwc_completed.status.value,
                            )
                            yield format_sse_event(
                                serialize_message(
                                    content=_pwc_resp.message,
                                    confidence=0.95,
                                    domain="post_wizard_continuation",
                                    source="continuation_executed",
                                    conversation_id=_pwc_conv_id,
                                ),
                                next_id(),
                            )
                        except Exception as _pwc_exec_exc:
                            logger.error(
                                "[SSEChat-T12] continuation execution failed: %s",
                                _pwc_exec_exc,
                                exc_info=True,
                            )
                            yield format_sse_event(
                                serialize_message(
                                    content=(
                                        f"N\u00e3o consegui {_pwc_label} agora \u2014 "
                                        "tente novamente em instantes."
                                    ),
                                    confidence=0.5,
                                    domain="post_wizard_continuation",
                                    source="continuation_exec_error",
                                    conversation_id=_pwc_conv_id,
                                ),
                                next_id(),
                            )
                        return
            except Exception as _pwc_exc:
                logger.debug(
                    "[SSEChat-T12] post-wizard continuation check skipped: %s",
                    _pwc_exc,
                )

        if resolved_domain == "kanban":
            from app.api.v1.chat_shared import _subagent_for_kanban
            resolved_domain = _subagent_for_kanban(content)
        elif resolved_domain == "pipeline_transition":
            from app.api.v1.chat_shared import _subagent_for_pipeline
            resolved_domain = _subagent_for_pipeline(content)
        elif resolved_domain == "sourcing":
            from app.api.v1.chat_shared import _subagent_for_sourcing
            resolved_domain = _subagent_for_sourcing(content)

        # Wizard canonical path (mirrors agent_chat_ws.py)
        if resolved_domain == "wizard":
            _wizard_handled = False
            try:
                from app.domains.job_creation.services.wizard_session_service import (
                    WizardSessionService,
                )

                token_count = 0
                sse_queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()

                async def _wiz_on_token(_chunk: str) -> None:
                    nonlocal token_count
                    token_count += 1
                    _safe = mask_pii_outbound(_chunk) if isinstance(_chunk, str) else _chunk
                    await sse_queue.put(serialize_token(_safe))

                # Task #1080: canonical pure derive (no context dict honor).
                from app.shared.sessions import derive_thread_id as _derive_tid
                _wiz_thread_id = _derive_tid(company_id, session_id)
                # ── T12: Disambiguator at wizard bootstrap ──────────────────
                # Detect composite phrases ("crie e publique") on the FIRST
                # message to the wizard (new session, no existing checkpoint).
                # Parks the continuation so LIA can offer it after wizard finishes.
                if os.environ.get("LIA_POST_WIZARD_CONTINUATION", "1") == "1":
                    try:
                        from app.shared.sessions import is_wizard_session_active as _t12_is_active
                        _t12_is_new = not await _t12_is_active(company_id, session_id)
                        if _t12_is_new:
                            from app.orchestrator.routing.job_creation_disambiguator import (
                                detect_job_creation as _t12_detect,
                            )
                            from app.orchestrator.routing.post_wizard_continuation import (
                                store_continuation as _t12_store,
                            )
                            _t12_detection = _t12_detect(content)
                            if (
                                _t12_detection is not None
                                and _t12_detection.continuation_text
                            ):
                                _t12_store(
                                    req.conversation_id or session_id,
                                    company_id,
                                    _t12_detection,
                                    content,
                                )
                                logger.info(
                                    "[SSEChat-T12] continuation stored conv=%s kind=%s text=%s",
                                    req.conversation_id or session_id,
                                    _t12_detection.continuation_kind,
                                    _t12_detection.continuation_text,
                                )
                    except Exception as _t12_store_exc:
                        logger.debug(
                            "[SSEChat-T12] disambiguator skipped: %s", _t12_store_exc,
                        )

                async def _run_wizard():
                    return await WizardSessionService.process_message(
                        thread_id=_wiz_thread_id,
                        user_message=content,
                        user_id=user_id,
                        company_id=company_id,
                        session_id=session_id,
                        context=context,
                        on_token=_wiz_on_token,
                    )

                # wizard-reasoning (2026-06-11): wire SSE sink para reasoning_step
                # emitidos pelo WizardOrchestrator.process_turn (sync, via to_thread).
                # asyncio.to_thread copia o contextvars context -> _sse_frame_sink fica
                # visível na thread; o orchestrator usa run_coroutine_threadsafe p/ await.
                async def _wiz_sse_push(_frame: dict) -> None:
                    await sse_queue.put(_frame)

                from lia_agents_core.streaming_callback import (
                    set_sse_frame_sink as _wiz_set_sink,
                    reset_sse_frame_sink as _wiz_reset_sink,
                )
                _wiz_sink_token = _wiz_set_sink(_wiz_sse_push)

                _wiz_task = asyncio.create_task(
                    asyncio.wait_for(_run_wizard(), timeout=_AGENT_TIMEOUT)
                )

                # Harness fix (502 WSI/JD): drena a fila COM keepalive em
                # silêncio prolongado. Operações longas (WSI ~100s) deixavam o
                # stream mudo → gateway derrubava (502). _drain_queue_with_keepalive
                # emite : keepalive a cada 15s de silêncio (testável).
                async for _ev in _drain_queue_with_keepalive(
                    sse_queue, _wiz_task.done, next_id
                ):
                    yield _ev

                _wiz_msg, _wiz_payload, _wiz_tokens = await _wiz_task
                _wiz_reset_sink(_wiz_sink_token)  # cleanup sink (wizard-reasoning 2026-06-11)

                while not sse_queue.empty():
                    _tok = sse_queue.get_nowait()
                    if _tok is not None:
                        yield format_sse_event(_tok, next_id())

                _wiz_clean = mask_pii_outbound(_strip_react_json(_wiz_msg or ""))

                if _wiz_payload and isinstance(_wiz_payload, dict):
                    yield format_sse_event(
                        serialize_panel_update(
                            panel_type="wizard_stage",
                            panel_data=_wiz_payload.get("data", _wiz_payload),
                            panel_title=_wiz_payload.get("stage", "wizard"),
                            action="open",
                            thread_id=_wiz_thread_id,
                            completeness=_wiz_payload.get("completeness"),
                        ),
                        next_id(),
                    )

                # ── T12: Post-wizard continuation OFFER ──────────────────────
                # When the wizard reaches a terminal stage and a composite
                # continuation was parked at bootstrap, LIA proactively offers
                # the remaining task in the chat.
                if os.environ.get("LIA_POST_WIZARD_CONTINUATION", "1") == "1":
                    try:
                        _t12_stage = (
                            (_wiz_payload or {}).get("stage", "")
                            if isinstance(_wiz_payload, dict)
                            else ""
                        )
                        _T12_DONE_STAGES = {"done", "completed", "finished", "handoff"}
                        if _t12_stage in _T12_DONE_STAGES:
                            from app.orchestrator.routing.post_wizard_continuation import (
                                mark_offered as _t12_mark,
                                build_offer_message as _t12_build_offer,
                                get_continuation as _t12_get_cont,
                            )
                            _t12_cont = _t12_get_cont(req.conversation_id or session_id)
                            if _t12_cont is not None:
                                _t12_job_id = None
                                if isinstance(_wiz_payload, dict):
                                    _t12_job_id = _wiz_payload.get("job_vacancy_id") or (
                                        _wiz_payload.get("data") or {}
                                    ).get("job_id")
                                _t12_offered = _t12_mark(
                                    req.conversation_id or session_id, _t12_job_id,
                                )
                                if _t12_offered is not None:
                                    _wiz_clean = _wiz_clean + _t12_build_offer(_t12_offered)
                                    logger.info(
                                        "[SSEChat-T12] offer surfaced conv=%s stage=%s job_id=%s",
                                        req.conversation_id or session_id,
                                        _t12_stage,
                                        _t12_job_id,
                                    )
                    except Exception as _t12_offer_exc:
                        logger.debug(
                            "[SSEChat-T12] post-wizard offer skipped: %s", _t12_offer_exc,
                        )

                # P0-E fix (2026-06-14): propagar ui_action do wizard payload
                # (ex.: navigate_to page=chat quando user pede chat full no wizard).
                _wiz_ui_action = (
                    _wiz_payload.get("ui_action")
                    if isinstance(_wiz_payload, dict)
                    else None
                )
                _wiz_ui_params = (
                    _wiz_payload.get("ui_action_params")
                    if isinstance(_wiz_payload, dict)
                    else None
                )
                # Bug #3 fix: RRP juicybox cards from wizard orchestrator
                _wiz_response_blocks = (
                    _wiz_payload.get("response_blocks")
                    if isinstance(_wiz_payload, dict)
                    else None
                )
                yield format_sse_event(
                    serialize_message(
                        content=_wiz_clean,
                        confidence=0.95,
                        domain="wizard",
                        source="wizard_session_canonical",
                        conversation_id=req.conversation_id,
                        ws_stage_payload=_wiz_payload if isinstance(_wiz_payload, dict) else None,
                        ui_action=_wiz_ui_action,
                        ui_action_params=_wiz_ui_params,
                        response_blocks=_wiz_response_blocks,
                    ),
                    next_id(),
                )
                _wizard_handled = True
            except Exception as _wiz_exc:
                logger.error(
                    "[SSEChat] WizardSessionService canonical path crashed: %s",
                    _wiz_exc, exc_info=True,
                )
                yield format_sse_event(
                    serialize_error(
                        "Não consegui processar a criação da vaga agora. "
                        "Pode tentar novamente em instantes?",
                        "wizard_canonical_error",
                    ),
                    next_id(),
                )
                return  # falha alto — NUNCA cai pro agente genérico (REGRA 4)
            if _wizard_handled:
                return

        import os as _os_bvs
        _bubble_via_supervisor = _os_bvs.getenv(
            "LIA_BUBBLE_VIA_SUPERVISOR", "false"
        ).lower() in ("true", "1")

        from app.api.v1.chat_shared import _get_agent, _build_agent_input

        # Fase 4 (LIA_FEDERATED_PRIMARY): a bolha roteia pro federado unico
        # (escopado) em vez dos agentes de dominio isolados. Off = atual.
        try:
            from app.tools.scope_config import federated_primary_enabled as _fed_primary
            _use_federated = (not _bubble_via_supervisor) and _fed_primary()
        except Exception:
            _use_federated = False
        if _bubble_via_supervisor:
            agent = None
        elif _use_federated:
            agent = _get_agent("recruiter_copilot")
        else:
            agent = _get_agent(resolved_domain)
        if not _bubble_via_supervisor and agent is None:
            yield format_sse_event(
                serialize_error(f"Agente '{resolved_domain}' indisponível.", "agent_unavailable"),
                next_id(),
            )
            return

        token_count = 0
        sse_queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()

        async def _streaming_callback(event: dict) -> None:
            nonlocal token_count
            event_type = event.get("type", "")
            if event_type == "token" and event.get("content"):
                token_count += 1
                _safe_token = mask_pii_outbound(event["content"]) if isinstance(event["content"], str) else event["content"]
                await sse_queue.put(serialize_token(_safe_token))
            elif event_type == "token_done":
                await sse_queue.put(serialize_token_done(event.get("tokens_sent", token_count)))
            elif event_type == "tool_started":
                # SSE-e2e Fase B: repassa preservando shape (não achata em thinking)
                await sse_queue.put(serialize_tool_started(
                    name=event.get("name", "tool"),
                    args=mask_pii_outbound(str(event.get("args") or "")),
                    tool_id=event.get("tool_id", ""),
                ))
            elif event_type == "tool_finished":
                await sse_queue.put(serialize_tool_finished(
                    name=event.get("name", "tool"),
                    status=event.get("status", "ok"),
                    duration_ms=event.get("duration_ms"),
                    result=mask_pii_outbound(str(event.get("result") or "")),
                    tool_id=event.get("tool_id", ""),
                ))
            elif event_type == "reasoning_step":
                await sse_queue.put(serialize_reasoning_step(
                    label=event.get("label", ""),
                    detail=mask_pii_outbound(str(event.get("detail") or "")),
                ))
            else:
                await sse_queue.put(serialize_thinking(
                    content=event.get("thought", event.get("content", "")),
                    step=event.get("step", 0),
                ))


        # === Audit 2026-05-24 P1: propagar streaming_callback ate _generate_with_tools_claude ===
        # ContextVar canonical (sibling de _current_company_id). Set antes de agent.process,
        # reset depois (mesmo padrao do RuntimeContext).
        from app.domains.ai.services.llm import _llm_streaming_callback
        _llm_stream_token = _llm_streaming_callback.set(_streaming_callback)

        # wire-B (2026-06-06): registra sink SSE p/ os frames de ATIVIDADE
        # (tool_started/tool_finished/reasoning_step) emitidos pelo
        # StreamingCallback dos domain agents — que antes so iam pro ws_manager
        # (chat lateral SSE ficava com "Pensando" estatico).
        async def _sse_frame_push(_frame: dict) -> None:
            await sse_queue.put(_frame)
        from lia_agents_core.streaming_callback import (
            set_sse_frame_sink as _set_sse_sink,
            reset_sse_frame_sink as _reset_sse_sink,
        )
        _sse_sink_token = _set_sse_sink(_sse_frame_push)
        logger.info("[SSE-SINK-DBG] sink registrado session=%s", session_id)

        async def _run_via_supervisor():
            # Fase 2 item 6: bolha roteada pro MainOrchestrator (LIA_BUBBLE_VIA_SUPERVISOR).
            # Reusa _streaming_callback (tokens/tools) + o loop drain+keepalive abaixo.
            try:
                if _approved_turn:
                    from app.shared.hitl.hitl_approval_context import (
                        set_hitl_approved,
                    )
                    set_hitl_approved(True)
                from app.api.v1.chat import _build_supervisor_context
                from app.core.database import AsyncSessionLocal
                from app.orchestrator.execution.main_orchestrator import (
                    get_main_orchestrator,
                )

                _sup_ctx = _build_supervisor_context(
                    content=_eff_content,  # F5 memory (2026-06-09): enriched com historico+entity hint
                    context=context,
                    company_id=company_id,
                    user_id=user_id,
                    conversation_id=_cid,  # F5 memory (2026-06-09): ID canônico resolvido do DB, não session_id fresco
                )
                async with AsyncSessionLocal() as _orch_db:
                    _result = await asyncio.wait_for(
                        get_main_orchestrator().process(
                            _sup_ctx, _orch_db, streaming_callback=_streaming_callback
                        ),
                        timeout=_AGENT_TIMEOUT,
                    )
                await sse_queue.put({"_done": True, "_orch_result": _result})
            except TimeoutError:
                await sse_queue.put({"_done": True, "_error": "timeout"})
            except Exception as exc:
                logger.error("[SSEChat] Supervisor error session=%s: %s", session_id, exc, exc_info=True)
                await sse_queue.put({"_done": True, "_error": str(exc)})

        async def _run_agent():
            try:
                if _approved_turn:
                    from app.shared.hitl.hitl_approval_context import (
                        set_hitl_approved,
                    )
                    set_hitl_approved(True)

                # ── Rail A capability gate (federated path) ──────────────────
                # Espelho do MainOrchestrator Phase 0.5. Quando LIA_FEDERATED_PRIMARY=true
                # o path supervisor (que ja tem o gate) e bypass-ado — wired aqui antes
                # de despachar pro recruiter_copilot. Fail-open: erro = fallthrough.
                # Guard source=="rail_a": zero overhead em turnos normais.
                _meta_ctx = (context.get("metadata") or {})
                if _meta_ctx.get("source") == "rail_a" and _meta_ctx.get("intent_hint"):
                    try:
                        from app.orchestrator.guards.rail_a_capability_check import (
                            check_rail_a_capability,
                        )
                        from app.core.database import AsyncSessionLocal as _RASL
                        async with _RASL() as _cap_db:
                            _cap_result = await check_rail_a_capability(
                                context=context,
                                message=_raw_content,
                                company_id=company_id,
                                db=_cap_db,
                            )
                        if _cap_result is not None:
                            logger.info(
                                "[SSEChat] federated Rail A gate short-circuit: "
                                "intent=%r ui_action=%r session=%s",
                                _meta_ctx.get("intent_hint"),
                                _cap_result.get("ui_action"),
                                session_id,
                            )
                            await sse_queue.put({"_done": True, "_orch_result": _cap_result})
                            return
                    except Exception as _cap_exc:
                        logger.debug(
                            "[SSEChat] federated Rail A gate skipped (fail-open): %s",
                            _cap_exc,
                        )

                # Fase 2/4: seta o escopo do turno na contextvar p/ o federado carregar
                # tools escopadas (~30 vs 179). Ativo se SCOPED_TOOLS ou PRIMARY. Fail-open.
                try:
                    from app.tools.scope_config import (
                        federated_scoping_enabled,
                        scope_for_context,
                        set_active_scope,
                    )
                    if federated_scoping_enabled():
                        _pg = context.get("page_type") or (context.get("view_context") or {}).get("page_type")
                        # Context selector fix (2026-06-13): prefere metadata.domain_hint
                        # (sinal explícito do FE — "Foco em Vaga"/"Foco em Candidato") sobre
                        # resolved_domain, que no caminho LIA_FEDERATED_PRIMARY é "auto".
                        from app.orchestrator.context.view_context import effective_domain_for_scope
                        _eff_domain = effective_domain_for_scope(context, resolved_domain)
                        set_active_scope(scope_for_context(_pg, _eff_domain))
                except Exception:
                    pass
                # F5 memory (2026-06-09): _ctx_prefix/_eff_content hoisted p/ escopo
                # compartilhado (supervisor+federado); variável já disponível aqui.
                agent_input = _build_agent_input(
                    content=_eff_content,
                    context=context,
                    session_id=session_id,
                    company_id=company_id,
                    user_id=user_id,
                    conversation_history=[],  # revert 2026-06-06: injecao causava 'multiple non-consecutive system messages'; memoria sera via checkpointer/thread_id (canonico)
                )
                # F4 workflows encadeados (2026-06-09): detecta plano multi-step
                # antes de agent.process. Se detectado executa via PlanExecutor +
                # emite background_task_update SSE. Fail-open: falha cai no
                # caminho normal agent.process. Guard >=2 tasks evita deteccao
                # falso-positivo em frases simples.
                _plan_executed = False

                # -- /planejar slash command: decompose + execute --------
                import re as _re_plan
                _PLANEJAR_RE = _re_plan.compile(r"^/planejar\b\s*(.*)", _re_plan.IGNORECASE)
                _planejar_match = _PLANEJAR_RE.match((_eff_content or "").strip())
                if _planejar_match:
                    _task_desc = _planejar_match.group(1).strip()
                    if _task_desc:
                        try:
                            from app.domains.automation.agents.automation_react_agent import AutomationReActAgent
                            from app.shared.execution import PlanExecutor
                            from app.shared.execution.plan_detector import ExecutionPlan, AgentTask

                            _auto = AutomationReActAgent()
                            _decomp = await _auto.decompose_task(
                                task_description=_task_desc,
                                company_id=str(company_id or ""),
                                user_id=str(user_id or "system"),
                                persist=False,
                            )
                            _subtasks = _decomp.get("subtasks", []) if isinstance(_decomp, dict) else []
                            if _subtasks and len(_subtasks) >= 2:
                                _AGENT_TYPE_TO_DOMAIN = {
                                    "sourcing": "sourcing",
                                    "cv_screening": "cv_screening",
                                    "interviewer": "cv_screening",
                                    "wsi_evaluator": "cv_screening",
                                    "job_planner": "job_management",
                                    "scheduling": "communication",
                                    "analyst_feedback": "communication",
                                    "communication": "communication",
                                    "automation": "automation",
                                }
                                _DOMAIN_DEFAULT_ACTION = {
                                    "sourcing": "search_candidates",
                                    "cv_screening": "score_candidates",
                                    "communication": "send_notification",
                                    "job_management": "generate_jd",
                                    "automation": "move_candidate_stage",
                                }
                                _agent_tasks = []
                                for i, st in enumerate(_subtasks):
                                    _raw_domain = st.get("domain_id") or _AGENT_TYPE_TO_DOMAIN.get(st.get("agent_type", ""), "automation")
                                    _raw_action = st.get("action_id") or _DOMAIN_DEFAULT_ACTION.get(_raw_domain, "generic_step")
                                    _agent_tasks.append(AgentTask(
                                        task_id=st.get("id", st.get("task_id", f"t{i}")),
                                        domain_id=_raw_domain,
                                        action_id=_raw_action,
                                        description=st.get("description", ""),
                                        depends_on=st.get("depends_on", []),
                                        is_critical=st.get("is_critical", True),
                                        context_mappings=st.get("context_mappings", {}),
                                    ))
                                _plan = ExecutionPlan(
                                    plan_id=f"planejar-{session_id[:8]}",
                                    detected_pattern=f"/planejar {_task_desc[:40]}",
                                    tasks=_agent_tasks,
                                )
                                _plan_task_id = _plan.plan_id

                                async def _sse_planejar_cb(event_type: str, data: dict) -> None:
                                    try:
                                        _ev = {"type": "plan_progress"}
                                        if event_type == "step_running":
                                            _ev["event"] = "step_running"
                                        elif event_type == "step_completed":
                                            _ev["event"] = "step_completed"
                                            _ev["status"] = data.get("status", "completed")
                                        elif event_type == "step_skipped":
                                            _ev["event"] = "step_skipped"
                                        elif event_type in ("plan_started", "plan_completed"):
                                            return
                                        else:
                                            return
                                        _ev["task_id"] = data.get("task_id", "")
                                        _ev["action_id"] = data.get("action_id", "")
                                        _ev["domain_id"] = data.get("domain_id", "")
                                        await sse_queue.put(_ev)
                                    except Exception:
                                        pass

                                await sse_queue.put({
                                    "type": "plan_progress",
                                    "event": "plan_started",
                                    "plan_id": _plan_task_id,
                                    "total_tasks": len(_agent_tasks),
                                    "tasks": [{"task_id": t.task_id, "action_id": t.action_id, "domain_id": t.domain_id} for t in _agent_tasks],
                                })

                                _plan_exec = PlanExecutor()
                                _exec_result = await asyncio.wait_for(
                                    _plan_exec.execute(
                                        plan=_plan,
                                        user_id=user_id,
                                        session_id=session_id,
                                        tenant_id=company_id,
                                        base_context={"company_id": company_id, "user_id": user_id},
                                        progress_callback=_sse_planejar_cb,
                                    ),
                                    timeout=_AGENT_TIMEOUT,
                                )

                                await sse_queue.put({
                                    "type": "plan_progress",
                                    "event": "plan_completed",
                                    "plan_id": _plan_task_id,
                                    "status": "completed",
                                })

                                _consolidated = _plan_exec.build_consolidated_response(_exec_result)
                                from types import SimpleNamespace as _NS2
                                await sse_queue.put({"_done": True, "_output": _NS2(
                                    message=_consolidated.message or "Plano executado.",
                                    confidence=getattr(_consolidated, "confidence", 0.9),
                                    actions=[],
                                    navigation=None,
                                    state_updates=None,
                                    metadata=getattr(_consolidated, "metadata", {}) or {},
                                )})
                                _plan_executed = True
                                logger.info("[SSEChat] /planejar executed: %d tasks", len(_agent_tasks))
                            else:
                                logger.info("[SSEChat] /planejar decompose returned < 2 subtasks, falling through")
                        except Exception as _pe:
                            logger.warning("[SSEChat] /planejar execution (fail-open): %s", _pe)

                try:
                    from app.shared.execution import PlanDetector, PlanExecutor
                    from app.shared.execution.plan_progress_mapper import (
                        map_plan_event,
                        new_plan_progress_state,
                    )
                    from app.shared.chat_event_serializer import serialize_background_task_update as _ser_bg
                    _plan_det = PlanDetector()
                    _detected = _plan_det.detect(_eff_content)
                    if _detected and len(_detected.tasks) >= 2:
                        logger.info(
                            "[SSEChat] Multi-step plan detected: %s (%d tasks)",
                            _detected.detected_pattern, len(_detected.tasks),
                        )
                        _plan_task_id = f"plan-{session_id[:8]}"
                        _plan_state = new_plan_progress_state()

                        async def _sse_plan_cb(event_type: str, data: dict) -> None:
                            try:
                                _ev = {"type": "plan_progress"}
                                if event_type == "step_running":
                                    _ev["event"] = "step_running"
                                    _ev["task_id"] = data.get("task_id", "")
                                    _ev["action_id"] = data.get("action_id", "")
                                    _ev["domain_id"] = data.get("domain_id", "")
                                elif event_type == "step_completed":
                                    _ev["event"] = "step_completed"
                                    _ev["task_id"] = data.get("task_id", "")
                                    _ev["action_id"] = data.get("action_id", "")
                                    _ev["domain_id"] = data.get("domain_id", "")
                                    _ev["status"] = data.get("status", "completed")
                                elif event_type == "step_skipped":
                                    _ev["event"] = "step_skipped"
                                    _ev["task_id"] = data.get("task_id", "")
                                    _ev["action_id"] = data.get("action_id", "")
                                    _ev["domain_id"] = data.get("domain_id", "")
                                elif event_type in ("plan_started", "plan_completed"):
                                    return
                                else:
                                    return
                                await sse_queue.put(_ev)
                            except Exception:
                                pass

                        await sse_queue.put({
                            "type": "plan_progress",
                            "event": "plan_started",
                            "plan_id": _plan_task_id,
                            "total_tasks": len(_detected.tasks),
                            "tasks": [{"task_id": t.task_id, "action_id": t.action_id, "domain_id": t.domain_id} for t in _detected.tasks],
                        })
                        _plan_exec = PlanExecutor()
                        _exec_result = await asyncio.wait_for(
                            _plan_exec.execute(
                                plan=_detected,
                                user_id=user_id,
                                session_id=session_id,
                                tenant_id=company_id,
                                base_context={"company_id": company_id, "user_id": user_id},
                                progress_callback=_sse_plan_cb,
                            ),
                            timeout=_AGENT_TIMEOUT,
                        )
                        _consolidated = _plan_exec.build_consolidated_response(_exec_result)
                        try:
                            async with AsyncSessionLocal() as _pdb:
                                await _cmem.add_message(
                                    _pdb, conversation_id=_cid, role="user", content=content
                                )
                                await _cmem.add_message(
                                    _pdb, conversation_id=_cid, role="assistant",
                                    content=_consolidated.message or "",
                                )
                                await _pdb.commit()
                        except Exception as _pme:
                            logger.warning("[SSEChat] plan memoria persist (fail-open): %s", _pme)
                        from types import SimpleNamespace as _NS
                        await sse_queue.put({
                            "type": "plan_progress",
                            "event": "plan_completed",
                            "plan_id": _plan_task_id,
                            "status": "completed",
                        })
                        await sse_queue.put({"_done": True, "_output": _NS(
                            message=_consolidated.message or "Plano executado.",
                            confidence=getattr(_consolidated, "confidence", 0.9),
                            actions=[],
                            navigation=None,
                            state_updates=None,
                            metadata=getattr(_consolidated, "metadata", {}) or {},
                        )})
                        _plan_executed = True
                except Exception as _plan_exc:
                    logger.warning("[SSEChat] plan detection (fail-open): %s", _plan_exc)
                if not _plan_executed:
                    output = await asyncio.wait_for(
                        agent.process(agent_input),
                        timeout=_AGENT_TIMEOUT,
                    )
                    try:
                        async with AsyncSessionLocal() as _pdb:
                            await _cmem.add_message(
                                _pdb, conversation_id=_cid, role="user", content=content
                            )
                            await _cmem.add_message(
                                _pdb, conversation_id=_cid, role="assistant",
                                content=output.message or "",
                            )
                            await _pdb.commit()
                    except Exception as _pe:
                        logger.warning("[SSEChat] memoria persist (fail-open): %s", _pe)
                    await sse_queue.put({"_done": True, "_output": output})
            except TimeoutError:
                await sse_queue.put({"_done": True, "_error": "timeout"})
            except Exception as exc:
                logger.error("[SSEChat] Agent error session=%s: %s", session_id, exc, exc_info=True)
                await sse_queue.put({"_done": True, "_error": str(exc)})

        # === Shared (refactor 2026-06-06): memoria-load + entity-resolve ANTES
        # do dispatch -> TANTO agente QUANTO supervisor herdam active_vacancy/
        # active_candidate (dor 'achar vaga/candidato por nome'). create_task copia
        # o context -> as tasks herdam os contextvars setados aqui. Cada trilha
        # consome o que precisa: agente monta _eff_content; supervisor mantem a
        # propria memoria (so ganha os contextvars).
        # Bloqueador-1 MEMORIA (canonical-fix): a bolha bypassava o produtor
        # unico conversation_memory (passava conversation_history=[] ->
        # agente dizia "primeira mensagem"). Agora carrega historico do MESMO
        # servico que o chat-page usa + persiste o turno. Fail-open: falha de
        # memoria nao derruba a resposta.
        from app.domains.recruiter_assistant.services.conversation_memory import (
            conversation_memory as _cmem,
        )
        _hist: list = []
        _ehint = ""
        _cid = req.conversation_id or session_id
        try:
            from app.core.database import AsyncSessionLocal
            async with AsyncSessionLocal() as _mdb:
                _conv = None
                if req.conversation_id:
                    _conv = await _cmem.get_conversation(
                        _mdb, req.conversation_id, include_messages=False
                    )
                if _conv is None:
                    _conv = await _cmem.get_or_create_conversation(
                        _mdb, user_id=user_id, company_id=company_id,
                        context_type="chat_bubble",
                    )
                    await _mdb.commit()
                _cid = str(_conv.id)
                # Canonical: propaga conversation_id resolvido para agente e FE.
                # Garante thread_id = session::domain::_cid (fresco p/ nova conversa,
                # correto p/ conversa carregada da sidebar).
                context["conversation_id"] = _cid
                _hctx = await _cmem.get_context_for_llm(
                    _mdb, _cid, max_messages=20
                )
                _hist = _hctx.get("messages", []) or []
                try:
                    from app.shared.entity_resolver import resolve_named_entities
                    _hist_text = "\n".join(
                        str(_m.get("content") or "")[:300]
                        for _m in (_hist[-6:] if _hist else [])
                        if _m.get("content")
                    )
                    # resolve-then-strip (ADR-LGPD-002): resolver recebe o RAW
                    # (com CPF/email/tel) p/ casar candidato por identificador.
                    # Retorna só nome+id no hint -> nada cru vaza ao LLM.
                    _ent = await resolve_named_entities(
                        _raw_content, company_id, _mdb, history_text=_hist_text
                    )
                    _ehint = _ent.get("hint") or ""
                    try:
                        from app.shared.entity_resolver import (
                            set_active_vacancy,
                            set_active_candidate,
                            sticky_vacancy,
                        )
                        _jb = _ent.get("jobs") or []
                        # fix #1: escopo de vaga STICKY -> nao zera num follow-up
                        # sem vaga (mantem a ultima desta conversa).
                        set_active_vacancy(sticky_vacancy(_cid, _jb[0][0] if _jb else ""))
                        _cd = _ent.get("candidates") or []
                        set_active_candidate(_cd[0][0] if len(_cd) == 1 else "")
                    except Exception:
                        pass
                except Exception as _ee:
                    logger.warning("[SSEChat] entity resolve (fail-open): %s", _ee)
        except Exception as _he:
            logger.warning("[SSEChat] memoria load (fail-open): %s", _he)

        # ── GAP-07-004: LGPD consent gate (both paths) ──────────────────
        # When the recruiter's message resolves to a specific candidate,
        # verify LGPD consent before AI processing. Revoked consent = hard
        # block (HTTP 451 equivalent via SSE). Absent consent = soft warning
        # + continue. Fail-open: consent check failure never blocks chat.
        _consent_blocked = False
        try:
            from app.shared.entity_resolver import get_active_candidate
            _resolved_cid = get_active_candidate()
            if _resolved_cid:
                from app.core.database import AsyncSessionLocal as _ConsentASL
                from app.domains.lgpd.services.consent_checker_service import ConsentCheckerService
                async with _ConsentASL() as _consent_db:
                    _consent_svc = ConsentCheckerService(_consent_db)
                    _consent_result = await _consent_svc.check_candidate_consent(
                        candidate_id=_resolved_cid,
                        company_id=company_id,
                        purpose="ai_screening",
                    )
                if not _consent_result.allowed:
                    _consent_blocked = True
                    logger.warning(
                        "[SSEChat] LGPD consent revoked — blocking AI processing "
                        "session=%s candidate=%s reason=%s",
                        session_id, _resolved_cid, _consent_result.reason,
                    )
                    _seq = 0
                    _seq += 1
                    yield format_sse_event(
                        {
                            "type": "message",
                            "content": (
                                "Nao posso processar informacoes deste candidato "
                                "por IA porque o consentimento LGPD foi revogado. "
                                "Para prosseguir, solicite novo consentimento ao "
                                "candidato via Gestao de Consentimentos."
                            ),
                            "consent_blocked": True,
                            "candidate_id": _resolved_cid,
                        },
                        f"{session_id[:8]}-{_seq}",
                    )
                    _seq += 1
                    yield format_sse_event(
                        {"type": "done", "consent_blocked": True},
                        f"{session_id[:8]}-{_seq}",
                    )
                    return
                elif _consent_result.soft_warning:
                    logger.info(
                        "[SSEChat] LGPD consent absent (soft warning) "
                        "session=%s candidate=%s",
                        session_id, _resolved_cid,
                    )
                    context["_consent_soft_warning"] = True
        except Exception as _consent_exc:
            logger.debug("[SSEChat] consent gate (fail-open): %s", _consent_exc)

        # F5 memory (2026-06-09): _eff_content hoisted p/ escopo compartilhado
        # supervisor+federado. Ambos recebem: historico recente (text prefix) +
        # entity hint resolvido. Antes só o federado recebia; supervisor usava
        # content cru → "quem é o Felipe?" sem UUID.
        _eff_content = content
        _ctx_prefix = ""
        if _hist:
            _lines = []
            for _m in _hist[-6:]:
                _r = "Recrutador" if _m.get("role") == "user" else "LIA"
                _c = (_m.get("content") or "")[:300]
                if _c:
                    _lines.append(f"{_r}: {_c}")
            if _lines:
                _ctx_prefix = (
                    "Historico recente desta conversa (use p/ resolver "
                    "referencias como 'ja disse'/'esse'/'ele'):\n"
                    + "\n".join(_lines) + "\n\n"
                )
        if _ctx_prefix:
            _eff_content = _ctx_prefix + "Mensagem atual do recrutador: " + content
        if _ehint:
            _eff_content = (
                _eff_content
                + "\n\n[Contexto resolvido pelo sistema — use EXATAMENTE isto, "
                + "NAO invente outro nome/titulo:\n" + _ehint + "]"
            )

        # GAP-12-004: OTEL span wrapping the full chat turn
        _chat_span = None
        try:
            from app.shared.observability.tracing import get_tracer as _get_chat_tracer
            _chat_tracer = _get_chat_tracer()
            _chat_span = _chat_tracer.create_span(
                "sse_chat.process",
                attributes={
                    "session_id": session_id,
                    "company_id": company_id,
                    "domain": active_domain,
                    "path": "supervisor" if _bubble_via_supervisor else "federated",
                },
                _start_otel=True,
            )
        except Exception:
            pass

        agent_task = asyncio.create_task(
            _run_via_supervisor() if _bubble_via_supervisor else _run_agent()
        )

        # Garantir reset do ContextVar quando task encerrar (success/error/cancel)
        def _cleanup_stream_ctx(_t):
            try:
                _llm_streaming_callback.reset(_llm_stream_token)
            except Exception:
                pass
            _reset_sse_sink(_sse_sink_token)
            if _chat_span is not None:
                try:
                    from app.shared.observability.tracing import finish_span
                    _exc = _t.exception() if not _t.cancelled() else None
                    finish_span(_chat_span, status="error" if _exc else "ok", error=_exc)
                except Exception:
                    pass
        agent_task.add_done_callback(_cleanup_stream_ctx)

        # Harness sensor (2026-06-04): per-frame timing to localize SSE
        # delivery buffering (backend streams incrementally vs downstream
        # burst). OFF by default. Activate: env LIA_SSE_TIMING_LOG=1 OR touch
        # /tmp/lia_sse_timing_on (flips a running uvicorn without a restart).
        import os as _os_sse
        _sse_timing = (
            _os_sse.getenv("LIA_SSE_TIMING_LOG", "").lower() in ("1", "true", "yes")
            or _os_sse.path.exists("/tmp/lia_sse_timing_on")
        )
        _t_stream0 = asyncio.get_event_loop().time()

        try:
            while True:
                try:
                    item = await asyncio.wait_for(sse_queue.get(), timeout=30.0)
                except TimeoutError:
                    yield format_sse_keepalive()
                    continue

                if item is None:
                    break

                if item.get("_done"):
                    if item.get("_error") == "timeout":
                        yield format_sse_event(
                            serialize_error("Tempo limite de processamento excedido. Tente novamente."),
                            next_id(),
                        )
                    elif item.get("_error"):
                        yield format_sse_event(
                            serialize_error("Erro interno ao processar sua mensagem."),
                            next_id(),
                        )
                    elif item.get("_orch_result") is not None:
                        # Fase 2 item 6: serializa o ChatResponse do MainOrchestrator
                        # via produtor unico (paridade com o ramo agente).
                        _orch = item["_orch_result"]
                        # FIX-C3B-SUP (2026-06-06): paridade de GOVERNANCA com o ramo
                        # agente -> post_compliance (FactChecker + audit LGPD da SAIDA)
                        # faltava na trilha supervisor (MainOrchestrator faz FairnessGuard
                        # no INPUT, nao post_compliance no OUTPUT). + mask_pii_outbound
                        # (passthrough p/ recrutador; mascara se flag). Fail-open.
                        try:
                            _is_d = isinstance(_orch, dict)
                            _gm = (lambda k: _orch.get(k) if _is_d else getattr(_orch, k, None))
                            _msg = _gm("content") or _gm("message") or ""
                            if _msg:
                                from app.shared.compliance.c3b_layer import (
                                    ComplianceContext,
                                    post_compliance,
                                )
                                _ctx_sup = ComplianceContext(
                                    company_id=company_id or "",
                                    user_id=user_id,
                                    session_id=session_id,
                                    domain=resolved_domain,
                                    agent_id="supervisor",
                                    original_message=_raw_content,
                                    fairness_flags=[],
                                )
                                _checked = await post_compliance(mask_pii_outbound(_msg), _ctx_sup)
                                _fld = "content" if _gm("content") else "message"
                                if _is_d:
                                    _orch[_fld] = _checked
                                else:
                                    setattr(_orch, _fld, _checked)
                        except Exception as _csup:
                            logger.warning("[SSEChat] supervisor post_compliance skipped (fail-open): %s", _csup)
                        from app.api.v1.chat import _orchestrator_result_to_frames
                        for _frame in _orchestrator_result_to_frames(
                            _orch, req.conversation_id
                        ):
                            yield format_sse_event(_frame, next_id())

                        # HITL surfacing supervisor (AUD-4 §4.2 bird, 2026-06-07):
                        # se um sub-agente ReAct do supervisor bloqueou uma tool, o
                        # hitl_pending viajou no metadata -> ChatResponse -> aqui
                        # minta o pending (thread_id=session_id, p/ _detect_hitl_approval
                        # achar no replay) + emite approval_required. Simetrico ao
                        # ramo agente. Fail-open: uuid se o mint falhar.
                        _hp_sup = (
                            _orch.get("hitl_pending")
                            if isinstance(_orch, dict)
                            else getattr(_orch, "hitl_pending", None)
                        )
                        if _hp_sup:
                            try:
                                from app.services.hitl_service import (
                                    hitl_service as _hsvc_sup,
                                )
                                _pid_sup = await _hsvc_sup.request_approval(
                                    thread_id=session_id,
                                    action=_hp_sup.get("tool") or "sensitive_action",
                                    description=_hp_sup.get("message")
                                    or "Confirme para prosseguir.",
                                    data=_hp_sup.get("data") or {},
                                    ws_session_id=session_id,
                                    domain=_hp_sup.get("domain") or resolved_domain,
                                    company_id=company_id or "",
                                    user_id=user_id,
                                )
                            except Exception as _hpsx:
                                import uuid as _uuid
                                logger.warning(
                                    "[SSEChat] HITL(sup) request_approval falhou "
                                    "(fail-open): %s", _hpsx,
                                )
                                _pid_sup = str(_uuid.uuid4())
                            yield format_sse_event(
                                _build_approval_frame(_pid_sup, _hp_sup), next_id()
                            )
                    else:
                        output = item["_output"]
                        tokens_used = output.metadata.get("tokens_used", 0) if output.metadata else 0
                        if tokens_used <= 0:
                            input_words = len(content.split())
                            output_words = len((output.message or "").split())
                            tokens_used = int((input_words + output_words) * 1.3)
                        if tokens_used > 0 and company_id:
                            try:
                                await increment_usage(company_id, tokens_used)
                            except Exception:
                                pass

                        clean_message = mask_pii_outbound(_strip_react_json(output.message or ""))
                        # FIX-NAVIGATE-LEAK (Fase 0 + hardening 2026-06-09):
                        # [NAVIGATE:...] vazava como texto no SSE. Fix em 2 camadas:
                        # Camada 1: extrai o PRIMEIRO marker -> strip + ui_action.
                        # Camada 2 (defesa em profundidade): strip regex de QUALQUER
                        #   marker residual (multiplos markers, ou falha do import).
                        #   Garante que NUNCA vaza para o FE mesmo com excecao.
                        _nav_ui_action = None
                        _nav_ui_params = None
                        try:
                            from app.orchestrator.context.chat_adapter import (
                                _extract_navigate_marker,
                            )
                            _nav = _extract_navigate_marker(clean_message)
                            if _nav is not None:
                                clean_message, _np, _npar = _nav
                                if _np != "general":
                                    _nav_ui_action = "navigate_to"
                                    _nav_ui_params = {"page": _np, **_npar}
                        except Exception:
                            pass
                        # Camada 2: strip residual — quaisquer [NAVIGATE:...] que
                        # sobraram (multiplos markers ou excecao silenciada acima).
                        import re as _re_nav
                        clean_message = _re_nav.sub(
                            r"\[NAVIGATE:[^\]]*\]", "", clean_message
                        ).strip()

                        # FIX-C3B-SSE (Fase 0): paridade c/ WS — post_compliance
                        # (FactChecker + audit log LGPD da decisao) faltava no SSE.
                        # Fecha o gap de governanca/auditoria na saida. Fail-open.
                        try:
                            from app.shared.compliance.c3b_layer import (
                                ComplianceContext,
                                post_compliance,
                            )
                            _c3b_ctx = ComplianceContext(
                                company_id=company_id or "",
                                user_id=user_id,
                                session_id=session_id,
                                domain=resolved_domain,
                                agent_id=resolved_domain,
                                original_message=_raw_content,
                                fairness_flags=[],
                            )
                            clean_message = await post_compliance(clean_message, _c3b_ctx)
                        except Exception as _c3b_exc:
                            logger.warning("[SSEChat] post_compliance skipped (fail-open): %s", _c3b_exc)

                        # Fase 2 (2026-06-09): diretiva ui_action surfacada por
                        # um tool (open_ui/apply_table_state) via ui_action_sink
                        # -> output.metadata (drenado no react base). Precede o
                        # nav marker — acao explicita do tool ganha. Sem isso o
                        # produtor era ghost no caminho federado.
                        _tool_ui_action = (output.metadata or {}).get("ui_action")
                        _tool_ui_params = (output.metadata or {}).get("ui_action_params")
                        _eff_ui_action = _tool_ui_action or _nav_ui_action
                        _eff_ui_params = (
                            _tool_ui_params if _tool_ui_action else _nav_ui_params
                        )

                        # T7 (2026-06-13): start_wizard_seeded no caminho federado.
                        # Quando o recruiter_copilot chama start_creation_from_source
                        # e a tool retorna ui_action="start_wizard_seeded" + seed_source,
                        # o SSE handler delega ao WizardSessionService (espelho do
                        # MainOrchestrator._start_seeded_wizard). Sem isso a diretiva
                        # era ghost — o FE recebia "start_wizard_seeded" mas sem a
                        # sessao wizard semeada no backend.
                        _seed_source = (output.metadata or {}).get("seed_source")
                        _seeded_wizard_handled = False
                        if _tool_ui_action == "start_wizard_seeded" and _seed_source:
                            try:
                                from app.domains.job_creation.services.wizard_session_service import (
                                    WizardSessionService as _SeedWizSvc,
                                )
                                from app.shared.sessions import derive_thread_id as _seed_derive

                                _seed_thread = _seed_derive(company_id, session_id)
                                _seed_ctx = dict(context or {})
                                _seed_ctx["seed_source"] = _seed_source
                                _seed_ctx.setdefault("user_id", user_id)
                                _seed_ctx.setdefault("company_id", company_id)
                                _seed_ctx.setdefault("session_id", session_id)

                                _seed_msg, _seed_payload, _seed_tokens = (
                                    await _SeedWizSvc.process_message(
                                        thread_id=_seed_thread,
                                        user_message=content,
                                        user_id=user_id,
                                        company_id=company_id,
                                        session_id=session_id,
                                        context=_seed_ctx,
                                        on_token=None,
                                    )
                                )
                                _seed_clean = mask_pii_outbound(
                                    _strip_react_json(_seed_msg or clean_message)
                                )
                                if _seed_payload and isinstance(_seed_payload, dict):
                                    yield format_sse_event(
                                        serialize_panel_update(
                                            panel_type="wizard_stage",
                                            panel_data=_seed_payload.get("data", _seed_payload),
                                            panel_title=_seed_payload.get("stage", "wizard"),
                                            action="open",
                                            thread_id=_seed_thread,
                                            completeness=_seed_payload.get("completeness"),
                                        ),
                                        next_id(),
                                    )
                                yield format_sse_event(
                                    serialize_message(
                                        content=_seed_clean,
                                        confidence=0.95,
                                        domain="wizard",
                                        source="wizard_session_canonical",
                                        conversation_id=_cid,
                                        ws_stage_payload=_seed_payload if isinstance(_seed_payload, dict) else None,
                                        ui_action="start_wizard_seeded",
                                        ui_action_params=_seed_source,
                                    ),
                                    next_id(),
                                )
                                _seeded_wizard_handled = True
                                logger.info(
                                    "[SSEChat] start_wizard_seeded consumed "
                                    "(federated): session=%s seed=%s",
                                    session_id, _seed_source,
                                )
                            except Exception as _seed_exc:
                                logger.error(
                                    "[SSEChat] start_wizard_seeded delegation "
                                    "failed (fallback to normal msg): %s",
                                    _seed_exc, exc_info=True,
                                )

                        # panel_update removed (F5 cleanup 2026-06-09): recruiter_copilot
                        # never sets metadata["panel_update"] — wizard panels are handled by
                        # the wizard path (resolved_domain=="wizard") before reaching this
                        # drain. Dead code removed to avoid confusion.

                        if not _seeded_wizard_handled:
                            fairness_warnings = (output.metadata or {}).get("fairness_warnings", [])

                            yield format_sse_event(
                                serialize_message(
                                    content=clean_message,
                                    confidence=output.confidence,
                                    domain=resolved_domain,
                                    source="sse",
                                    actions=[a.dict() for a in (output.actions or [])],
                                    navigation=output.navigation.dict() if output.navigation else None,
                                    state_updates=output.state_updates or None,
                                    fairness_warnings=fairness_warnings or None,
                                    response_blocks=(output.metadata or {}).get(
                                        "response_blocks"
                                    ),
                                    ui_action=_eff_ui_action,
                                    ui_action_params=_eff_ui_params,
                                    conversation_id=_cid,
                                ),
                                next_id(),
                            )

                        # HITL surfacing (AUD-4 1b, 2026-06-07): se a tool
                        # sensivel foi bloqueada pelo gate, o sink propagou
                        # hitl_pending pro metadata -> emite frame
                        # approval_required (mesmo shape do ramo supervisor).
                        # Mint via HITLService (produtor canonico: durable +
                        # audit LGPD). Fail-open: uuid se o mint falhar.
                        _hp = (output.metadata or {}).get("hitl_pending")
                        if _hp:
                            try:
                                from app.services.hitl_service import (
                                    hitl_service as _hsvc,
                                )
                                _pid = await _hsvc.request_approval(
                                    thread_id=session_id,
                                    action=_hp.get("tool") or "sensitive_action",
                                    description=_hp.get("message")
                                    or "Confirme para prosseguir.",
                                    data=_hp.get("data") or {},
                                    ws_session_id=session_id,
                                    domain=_hp.get("domain") or resolved_domain,
                                    company_id=company_id or "",
                                    user_id=user_id,
                                )
                            except Exception as _hpx:
                                import uuid as _uuid
                                logger.warning(
                                    "[SSEChat] HITL request_approval falhou "
                                    "(fail-open): %s", _hpx,
                                )
                                _pid = str(_uuid.uuid4())
                            yield format_sse_event(
                                _build_approval_frame(_pid, _hp), next_id()
                            )
                    break
                else:
                    if _sse_timing:
                        _ft = (
                            item.get("type", "?")
                            if isinstance(item, dict)
                            else "?"
                        )
                        logger.info(
                            "[SSE-TIMING] yield frame type=%s at +%.2fs",
                            _ft,
                            asyncio.get_event_loop().time() - _t_stream0,
                        )
                    yield format_sse_event(item, next_id())
        finally:
            if not agent_task.done():
                agent_task.cancel()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "X-Transport": "sse",
        },
    )


# ---------------------------------------------------------------------------
# GET /sessions/active — migrado de agent_chat_ws.py (2026-06-09)
# O transporte ativo é SSE; sessões WS não existem mais.
# Retorna lista vazia para compatibilidade com SwitchTaskModal.tsx.
# ---------------------------------------------------------------------------
@router.get("/sessions/active", response_model=None)
async def list_active_sessions(
    company_id: str = Depends(require_company_id),
):
    """List active sessions for the authenticated user.

    SSE transport does not maintain persistent server-side session state
    the way WebSocket does. Returns empty list for UI backward compatibility.
    """
    return {"sessions": [], "count": 0}


reorder_collection_before_item(router)
