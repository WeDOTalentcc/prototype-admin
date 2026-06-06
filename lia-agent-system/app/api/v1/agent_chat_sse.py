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
import json
import logging
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
from app.shared.pii_masking import mask_pii
from app.domains.credits.services.token_budget_service import (
    check_budget,
    get_plan_for_company,
    increment_usage,
)
from fastapi import Depends
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, SESSION_ID_PATH_PATTERN, reorder_collection_before_item

logger = logging.getLogger(__name__)

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
            from app.domains.cv_screening.services.hitl_service import HITLService
            hitl_service = HITLService()
            if req.approved:
                await hitl_service.approve(req.pending_id, user_id)
            else:
                await hitl_service.reject(req.pending_id, user_id)
            return {"status": "ok", "approved": req.approved}
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("[SSEAction] HITL action failed: %s", exc)
            raise HTTPException(status_code=500, detail="Failed to process approval")

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

    async def event_generator():
        event_seq = 0

        def next_id() -> str:
            nonlocal event_seq
            event_seq += 1
            return f"{session_id[:8]}-{event_seq}"

        yield format_sse_event(serialize_thinking(), next_id())


        async def _check_budget_async():
            try:
                plan = await get_plan_for_company(company_id)
                return await check_budget(company_id, plan)
            except Exception as exc:
                logger.warning("[SSEChat] Budget check failed — continuing: %s", exc)
                return True, 0, 0

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
            try:
                from app.orchestrator.routing.cascaded_router import CascadedRouter
                _router = CascadedRouter()
                route = await _router.route(
                    message=content, context=context, session_id=session_id,
                )
                if not route.needs_clarification:
                    return route.domain_id
            except Exception:
                pass
            return active_domain

        budget_result, resolved_domain = await asyncio.gather(
            _check_budget_async(), _route_domain_async()
        )
        budget_ok, used, limit = budget_result
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

        if resolved_domain == "kanban":
            from app.api.v1.agent_chat_ws import _subagent_for_kanban
            resolved_domain = _subagent_for_kanban(content)
        elif resolved_domain == "pipeline_transition":
            from app.api.v1.agent_chat_ws import _subagent_for_pipeline
            resolved_domain = _subagent_for_pipeline(content)
        elif resolved_domain == "sourcing":
            from app.api.v1.agent_chat_ws import _subagent_for_sourcing
            resolved_domain = _subagent_for_sourcing(content)

        # Inject tenant context so agents know the authenticated company
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
                    _safe = mask_pii(_chunk) if isinstance(_chunk, str) else _chunk
                    await sse_queue.put(serialize_token(_safe))

                # Task #1080: canonical pure derive (no context dict honor).
                from app.shared.sessions import derive_thread_id as _derive_tid
                _wiz_thread_id = _derive_tid(company_id, session_id)
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

                while not sse_queue.empty():
                    _tok = sse_queue.get_nowait()
                    if _tok is not None:
                        yield format_sse_event(_tok, next_id())

                _wiz_clean = mask_pii(_strip_react_json(_wiz_msg or ""))

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

                yield format_sse_event(
                    serialize_message(
                        content=_wiz_clean,
                        confidence=0.95,
                        domain="wizard",
                        source="wizard_session_canonical",
                        conversation_id=req.conversation_id,
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

        from app.api.v1.agent_chat_ws import _get_agent, _build_agent_input

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
                _safe_token = mask_pii(event["content"]) if isinstance(event["content"], str) else event["content"]
                await sse_queue.put(serialize_token(_safe_token))
            elif event_type == "token_done":
                await sse_queue.put(serialize_token_done(event.get("tokens_sent", token_count)))
            elif event_type == "tool_started":
                # SSE-e2e Fase B: repassa preservando shape (não achata em thinking)
                await sse_queue.put(serialize_tool_started(
                    name=event.get("name", "tool"),
                    args=mask_pii(str(event.get("args") or "")),
                    tool_id=event.get("tool_id", ""),
                ))
            elif event_type == "tool_finished":
                await sse_queue.put(serialize_tool_finished(
                    name=event.get("name", "tool"),
                    status=event.get("status", "ok"),
                    duration_ms=event.get("duration_ms"),
                    result=mask_pii(str(event.get("result") or "")),
                    tool_id=event.get("tool_id", ""),
                ))
            elif event_type == "reasoning_step":
                await sse_queue.put(serialize_reasoning_step(
                    label=event.get("label", ""),
                    detail=mask_pii(str(event.get("detail") or "")),
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
                from app.api.v1.chat import _build_supervisor_context
                from app.core.database import AsyncSessionLocal
                from app.orchestrator.execution.main_orchestrator import (
                    get_main_orchestrator,
                )

                _sup_ctx = _build_supervisor_context(
                    content=content,
                    context=context,
                    company_id=company_id,
                    user_id=user_id,
                    conversation_id=req.conversation_id or session_id,
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
                        set_active_scope(scope_for_context(_pg, resolved_domain))
                except Exception:
                    pass
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
                        _hctx = await _cmem.get_context_for_llm(
                            _mdb, _cid, max_messages=20
                        )
                        _hist = _hctx.get("messages", []) or []
                        try:
                            from app.shared.entity_resolver import resolve_named_entities
                            _ent = await resolve_named_entities(content, company_id, _mdb)
                            _ehint = _ent.get("hint") or ""
                        except Exception as _ee:
                            logger.warning("[SSEChat] entity resolve (fail-open): %s", _ee)
                except Exception as _he:
                    logger.warning("[SSEChat] memoria load (fail-open): %s", _he)
                # bloqueador-1 MEMORIA (v2): embute historico recente como TEXTO no
                # content — SEM injetar mensagens separadas (que causava 'multiple
                # non-consecutive system messages'). bloqueador-2: + hint de entidade.
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
                _eff_content = (
                    (_ctx_prefix + "Mensagem atual do recrutador: " + content)
                    if _ctx_prefix else content
                )
                if _ehint:
                    _eff_content = (
                        _eff_content
                        + "\n\n[Contexto resolvido pelo sistema — use EXATAMENTE isto, "
                        + "NAO invente outro nome/titulo:\n" + _ehint + "]"
                    )
                agent_input = _build_agent_input(
                    content=_eff_content,
                    context=context,
                    session_id=session_id,
                    company_id=company_id,
                    user_id=user_id,
                    conversation_history=[],  # revert 2026-06-06: injecao causava 'multiple non-consecutive system messages'; memoria sera via checkpointer/thread_id (canonico)
                )
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
                        from app.api.v1.chat import _orchestrator_result_to_frames
                        for _frame in _orchestrator_result_to_frames(
                            item["_orch_result"], req.conversation_id
                        ):
                            yield format_sse_event(_frame, next_id())
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

                        clean_message = mask_pii(_strip_react_json(output.message or ""))
                        # FIX-NAVIGATE-LEAK (Fase 0): [NAVIGATE:...] vazava como
                        # texto no SSE (so o orquestrador passava pelo helper
                        # canonico). Reusa _extract_navigate_marker -> strip +
                        # ui_action navigate_to (mesmo contrato do FE).
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

                        panel_meta = (output.metadata or {}).get("panel_update")
                        if panel_meta and isinstance(panel_meta, dict):
                            yield format_sse_event(
                                serialize_panel_update(
                                    panel_type=panel_meta.get("panel_type", ""),
                                    panel_data=panel_meta.get("panel_data", {}),
                                    panel_title=panel_meta.get("panel_title", ""),
                                    action=panel_meta.get("action", "open"),
                                ),
                                next_id(),
                            )

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
                                ui_action=_nav_ui_action,
                                ui_action_params=_nav_ui_params,
                                conversation_id=req.conversation_id,
                            ),
                            next_id(),
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

reorder_collection_before_item(router)
