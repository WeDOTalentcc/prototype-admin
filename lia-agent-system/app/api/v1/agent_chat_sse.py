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
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

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
    session_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
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

    active_domain = req.domain or "recruiter_assistant"
    context = req.context or {}
    context.setdefault("company_id", company_id)
    context.setdefault("user_id", user_id)
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
                from app.shared.sessions import is_wizard_session_active
                if await is_wizard_session_active(company_id, session_id):
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

                while not _wiz_task.done():
                    try:
                        _tok = await asyncio.wait_for(sse_queue.get(), timeout=0.5)
                        if _tok is not None:
                            yield format_sse_event(_tok, next_id())
                    except asyncio.TimeoutError:
                        continue

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

        from app.api.v1.agent_chat_ws import _get_agent, _build_agent_input

        agent = _get_agent(resolved_domain)
        if agent is None:
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
            else:
                await sse_queue.put(serialize_thinking(
                    content=event.get("thought", event.get("content", "")),
                    step=event.get("step", 0),
                ))

        context["streaming_callback"] = _streaming_callback

        # === Audit 2026-05-24 P1: propagar streaming_callback ate _generate_with_tools_claude ===
        # ContextVar canonical (sibling de _current_company_id). Set antes de agent.process,
        # reset depois (mesmo padrao do RuntimeContext).
        from app.domains.ai.services.llm import _llm_streaming_callback
        _llm_stream_token = _llm_streaming_callback.set(_streaming_callback)

        agent_input = _build_agent_input(
            content=content,
            context=context,
            session_id=session_id,
            company_id=company_id,
            user_id=user_id,
            conversation_history=[],
        )

        async def _run_agent():
            try:
                output = await asyncio.wait_for(
                    agent.process(agent_input),
                    timeout=_AGENT_TIMEOUT,
                )
                await sse_queue.put({"_done": True, "_output": output})
            except TimeoutError:
                await sse_queue.put({"_done": True, "_error": "timeout"})
            except Exception as exc:
                logger.error("[SSEChat] Agent error session=%s: %s", session_id, exc, exc_info=True)
                await sse_queue.put({"_done": True, "_error": str(exc)})

        agent_task = asyncio.create_task(_run_agent())

        # Garantir reset do ContextVar quando task encerrar (success/error/cancel)
        def _cleanup_stream_ctx(_t):
            try:
                _llm_streaming_callback.reset(_llm_stream_token)
            except Exception:
                pass
        agent_task.add_done_callback(_cleanup_stream_ctx)

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
                                conversation_id=req.conversation_id,
                            ),
                            next_id(),
                        )
                    break
                else:
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
