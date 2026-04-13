"""
Chat API endpoints for LIA conversation.
"""
import json
import logging
import os
import uuid
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.domains.chat.dependencies import get_chat_repo
from app.orchestrator.chat_adapter import ChatAdapter
from app.api.orchestrator_routes import get_main_orchestrator

UPLOAD_DIR = Path(os.getenv("LIA_UPLOAD_DIR", "/tmp/lia_uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Path A: ChatAdapter bridges chat.py -> MainOrchestrator
_chat_adapter = None

def _get_chat_adapter():
    global _chat_adapter
    if _chat_adapter is None:
        _main_orch = get_main_orchestrator()
        _chat_adapter = ChatAdapter(main_orchestrator=_main_orch)
    return _chat_adapter

from app.domains.chat.repositories.chat_repository import ChatRepository
from app.orchestrator.action_executor import (
    ACTIONABLE_INTENTS,
    ActionResult,
    action_executor,
    is_confirmation,
    is_rejection,
)
from app.orchestrator.pending_action import PendingActionState, pending_action_store
from app.schemas.chat import (
    ChatResponse,
    ConversationListResponse,
    ConversationResponse,
    MessageCreate,
    MessageResponse,
)

logger = logging.getLogger(__name__)

JOB_ACTION_MAP: dict[str, str] = {
    "pausar": "pausar_vaga",
    "pause": "pausar_vaga",
    "fechar": "fechar_vaga",
    "encerrar": "fechar_vaga",
    "close": "fechar_vaga",
    "reabrir": "reabrir_vaga",
    "reopen": "reabrir_vaga",
    "duplicar": "duplicar_vaga",
    "duplicate": "duplicar_vaga",
    "urgente": "vaga_urgente",
    "urgent": "vaga_urgente",
    "marcar urgente": "vaga_urgente",
}

SKIP_ACTION_INTENTS = {"create_job", "greeting", "general_question", "unknown", "search_candidates"}


async def resolve_candidate_by_name(
    candidate_name: str,
    company_id: str | None = None,
    job_id: str | None = None,
    db=None,
) -> dict | None:
    """Module-level wrapper around ChatRepository.resolve_candidate_by_name for testability."""
    if db is None:
        return None
    from app.domains.chat.repositories.chat_repository import ChatRepository
    repo = ChatRepository(db)
    return await repo.resolve_candidate_by_name(candidate_name, company_id=company_id, job_id=job_id)


async def _invoke_orchestrator_legacy(
    user_message: str,
    user_id: str,
    conversation_id: str,
    company_id: str,
    page_context: dict[str, Any] | None = None,
) -> dict:
    """Executa a mensagem do usuário via Orchestrator + ReAct agents.

    Retorna dict compatível com o restante do handler:
      response      str   — texto da resposta da LIA
      intent        str   — domínio/intent detectado
      entities      dict  — entidades extraídas (se o agente retornar)
      workflow_data dict  — search_results ou response_plan para context_data do FE
    """
    from app.api.orchestrator_routes import orchestrator as _orch

    if _orch is None:
        logger.warning("[chat] Orchestrator não inicializado, retornando resposta de fallback")
        return {
            "response": "Estou inicializando. Por favor, tente novamente em instantes.",
            "intent": "",
            "entities": {},
            "workflow_data": {},
        }

    orch_context: dict[str, Any] = {"company_id": company_id}
    if page_context:
        if page_context.get("job_vacancy_id"):
            orch_context["job_vacancy_id"] = page_context["job_vacancy_id"]
        if page_context.get("job_id"):
            orch_context["job_vacancy_id"] = page_context["job_id"]
        if page_context.get("candidate_ids"):
            orch_context["candidate_ids"] = page_context["candidate_ids"]
        if page_context.get("page_type"):
            orch_context["page_type"] = page_context["page_type"]
        if page_context.get("job_context"):
            orch_context["job_context"] = page_context["job_context"]

    result = await _orch.process_request(
        user_id=user_id,
        message=user_message,
        conversation_id=conversation_id,
        context=orch_context,
    )

    response_text = result.get("message") or ""
    intent = result.get("intent") or ""
    result_data = (result.get("result") or {}).get("data") or {}
    entities: dict = result_data if isinstance(result_data, dict) else {}

    # Mapeia chaves de workflow para context_data do FE (search_results, response_plan)
    workflow_data: dict = {}
    if "search_results" in entities:
        workflow_data["search_results"] = entities["search_results"]
    if "response_plan" in entities:
        workflow_data["response_plan"] = entities["response_plan"]

    prompt_version = result.get("prompt_version") or result.get("metadata", {}).get("prompt_version")
    if not prompt_version:
        try:
            from app.domains.ai.services.prompt_version_registry import prompt_version_registry
            prompt_version = prompt_version_registry.get_current_hash(intent) if intent else None
        except Exception:
            pass

    return {
        "response": response_text,
        "intent": intent,
        "entities": entities,
        "workflow_data": workflow_data,
        "prompt_version": prompt_version,
    }


router = APIRouter(prefix="/chat", tags=["chat"])


# =============================================
# REST API ENDPOINTS
# =============================================

@router.post("", response_model=ChatResponse)
async def send_message(
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user_or_demo),
    repo: ChatRepository = Depends(get_chat_repo),
):
    """
    Send a message to LIA and get response.

    This is the REST alternative to WebSocket for simpler integrations.
    """
    user_id = str(current_user.id)
    conversation_id = message_data.conversation_id

    # Create or get conversation
    if not conversation_id:
        conversation = await repo.create_conversation(user_id)
        conversation_id = str(conversation.id)
    else:
        conversation = await repo.get_conversation_by_id(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

    # M2: MainOrchestrator._setup_conversation_memory persists user message
    # await repo.add_user_message(conversation.id, message_data.content)

    # M2: Commit conversation so MainOrchestrator can find it in the same DB
    await repo.db.commit()
    await repo.db.refresh(conversation)

    page_context = message_data.context or {}

    # M2: Snapshot conversation attrs before orchestrator (commit expires objects)
    _conv_snapshot = {
        "id": str(conversation.id),
        "user_id": conversation.user_id,
        "user_role": getattr(conversation, "user_role", "") or "",
        "title": conversation.title,
        "intent": conversation.intent,
        "workflow_type": getattr(conversation, "workflow_type", None),
        "workflow_step": getattr(conversation, "workflow_step", None),
        "workflow_data": getattr(conversation, "workflow_data", None) or {},
        "status": conversation.status,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
    }

    orch_result = await _get_chat_adapter().process_message(
        user_message=message_data.content,
        user_id=user_id,
        company_id=str(current_user.company_id) if current_user.company_id else "",
        conversation_id=conversation_id,
        page_context=page_context,
        db=repo.db,
    )
    lia_response = orch_result["response"]
    detected_intent = orch_result["intent"]
    detected_entities = orch_result["entities"]

    if page_context.get("job_vacancy_id") and "job_id" not in detected_entities:
        detected_entities["job_id"] = page_context["job_vacancy_id"]

    if lia_response:
        # Item 2: handle_action_flow deleted — MainOrchestrator Phase 0+1 handles all actions
        final_response = lia_response

        msg_metadata: dict[str, Any] = {
            "intent": detected_intent,
            "entities": detected_entities,
        }

        # Item 2: action_metadata removed — MainOrchestrator handles actions

        # M2: MainOrchestrator._persist_response already committed via same db session
        # Session objects are expired after commit — use snapshot + orch_result for response
        # Use orchestrator conversation_id (may differ if MainOrchestrator created its own)
        _conv_id_str = str(orch_result.get("conversation_id", _conv_snapshot["id"]))
        _conv_snapshot["id"] = _conv_id_str

        workflow_data = orch_result["workflow_data"]
        context_data = None

        if "search_results" in workflow_data:
            search_results = workflow_data["search_results"]
            candidates = search_results.get("candidates", [])
            total_found = search_results.get("total_found", 0)

            if total_found > 0 and len(candidates) > 0:
                context_data = {
                    "type": "candidates",
                    "title": f"Candidatos Encontrados ({total_found})",
                    "shouldDisplay": True,
                    "data": {
                        "candidates": candidates,
                        "total_found": total_found,
                        "source": search_results.get("source"),
                        "local_count": search_results.get("local_count", 0),
                        "global_count": search_results.get("global_count", 0),
                        "credits_consumed": search_results.get("credits_consumed", 0),
                    },
                }

        elif "response_plan" in workflow_data:
            response_plan = workflow_data.get("response_plan", {})
            if response_plan.get("render_frame"):
                frame = response_plan["render_frame"]
                context_data = {
                    "type": frame.get("type", "job-creation-progress"),
                    "title": frame.get("title", "Criação de Vaga"),
                    "shouldDisplay": True,
                    "data": frame.get("data", {}),
                }

        # Build response entirely from in-memory data (session expired after commit)
        import uuid as _uuid
        _now = __import__("datetime").datetime.utcnow()
        _meta = msg_metadata.copy()
        if context_data:
            _meta["context_data"] = context_data

        # Update snapshot with orchestrator results
        _conv_snapshot["title"] = _conv_snapshot["title"] or message_data.content[:100]
        _conv_snapshot["intent"] = detected_intent or _conv_snapshot["intent"]

        return ChatResponse(
            message=MessageResponse(
                id=str(orch_result.get("message_id", _uuid.uuid4())),
                conversation_id=_conv_id_str,
                role="assistant",
                content=final_response,
                message_metadata=_meta,
                created_at=_now,
            ),
            conversation=ConversationResponse(
                id=_conv_snapshot["id"],
                user_id=_conv_snapshot["user_id"],
                user_role=_conv_snapshot["user_role"],
                title=_conv_snapshot["title"],
                intent=_conv_snapshot["intent"],
                workflow_type=_conv_snapshot["workflow_type"],
                workflow_step=_conv_snapshot["workflow_step"],
                workflow_data=_conv_snapshot["workflow_data"],
                status=_conv_snapshot["status"],
                created_at=_conv_snapshot["created_at"],
                updated_at=_now,
            ),
        )

    raise HTTPException(status_code=500, detail="Failed to generate response")


@router.post("/with-attachments", response_model=ChatResponse)
async def send_message_with_attachments(
    content: str = Form(...),
    conversation_id: str | None = Form(None),
    attachments: list[UploadFile] = File(default=[]),
    audio: UploadFile | None = File(default=None),
    current_user: User = Depends(get_current_user_or_demo),
    repo: ChatRepository = Depends(get_chat_repo),
):
    """
    Send a message to LIA with file attachments and/or audio.
    Uses the same conversation flow as send_message with attachment metadata.
    """
    attachment_info = []
    audio_info = None

    if attachments:
        for file in attachments:
            file_path = UPLOAD_DIR / f"{uuid.uuid4()}_{file.filename}"
            file_content = await file.read()
            with open(file_path, "wb") as f:
                f.write(file_content)

            file_size_kb = len(file_content) / 1024
            attachment_info.append({
                "filename": file.filename,
                "content_type": file.content_type,
                "size_kb": round(file_size_kb, 1),
                "path": str(file_path),
            })

    if audio:
        audio_path = UPLOAD_DIR / f"{uuid.uuid4()}_audio.webm"
        audio_content = await audio.read()
        with open(audio_path, "wb") as f:
            f.write(audio_content)
        audio_info = {
            "path": str(audio_path),
            "size_kb": round(len(audio_content) / 1024, 1),
        }

    augmented_content = content
    if attachment_info:
        files_summary = ", ".join([f"{a['filename']} ({a['size_kb']}KB)" for a in attachment_info])
        augmented_content = f"[Arquivos anexados: {files_summary}]\n\n{content}"

    if audio_info:
        augmented_content = f"[Áudio gravado para análise]\n\n{augmented_content}"

    user_id = str(current_user.id)
    if not conversation_id:
        conversation = await repo.create_conversation(user_id)
        conversation_id = str(conversation.id)
    else:
        conversation = await repo.get_conversation_by_id(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

    _conv_snapshot = {
        "id": str(conversation.id),
        "user_id": str(conversation.user_id),
        "user_role": conversation.user_role or "",
        "title": conversation.title,
        "intent": conversation.intent,
        "workflow_type": conversation.workflow_type,
        "workflow_step": conversation.workflow_step,
        "workflow_data": conversation.workflow_data,
        "status": conversation.status,
        "created_at": conversation.created_at,
    }

    orch_result = await _get_chat_adapter().process_message(
        user_message=augmented_content,
        user_id=user_id,
        company_id=str(current_user.company_id) if current_user.company_id else "",
        conversation_id=conversation_id,
        page_context=None,
        db=repo.db,
    )
    lia_response = orch_result["response"]

    if lia_response:
        _conv_id_str = str(orch_result.get("conversation_id", _conv_snapshot["id"]))
        _conv_snapshot["id"] = _conv_id_str

        workflow_data = orch_result["workflow_data"]
        context_data = None

        if "search_results" in workflow_data:
            search_results = workflow_data["search_results"]
            candidates = search_results.get("candidates", [])
            total_found = search_results.get("total_found", 0)
            if total_found > 0 and len(candidates) > 0:
                context_data = {
                    "type": "candidates",
                    "title": f"Candidatos Encontrados ({total_found})",
                    "shouldDisplay": True,
                    "data": {
                        "candidates": candidates,
                        "total_found": total_found,
                        "source": search_results.get("source"),
                        "local_count": search_results.get("local_count", 0),
                        "global_count": search_results.get("global_count", 0),
                        "credits_consumed": search_results.get("credits_consumed", 0),
                    },
                }
        elif "response_plan" in workflow_data:
            response_plan = workflow_data.get("response_plan", {})
            if response_plan.get("render_frame"):
                frame = response_plan["render_frame"]
                context_data = {
                    "type": frame.get("type", "job-creation-progress"),
                    "title": frame.get("title", "Criação de Vaga"),
                    "shouldDisplay": True,
                    "data": frame.get("data", {}),
                }

        import uuid as _uuid
        _now = __import__("datetime").datetime.utcnow()
        _meta = {
            "intent": orch_result.get("intent"),
            "entities": orch_result.get("entities"),
            "processed_attachments": attachment_info,
            "processed_audio": audio_info,
        }
        if context_data:
            _meta["context_data"] = context_data

        if attachment_info:
            _conv_snapshot["title"] = _conv_snapshot["title"] or f"Analise de {len(attachment_info)} arquivo(s)"
        elif audio_info:
            _conv_snapshot["title"] = _conv_snapshot["title"] or "Analise de audio"
        else:
            _conv_snapshot["title"] = _conv_snapshot["title"] or content[:100]

        return ChatResponse(
            message=MessageResponse(
                id=str(orch_result.get("message_id", _uuid.uuid4())),
                conversation_id=_conv_id_str,
                role="assistant",
                content=lia_response,
                message_metadata=_meta,
                created_at=_now,
            ),
            conversation=ConversationResponse(
                id=_conv_snapshot["id"],
                user_id=_conv_snapshot["user_id"],
                user_role=_conv_snapshot["user_role"],
                title=_conv_snapshot["title"],
                intent=orch_result.get("intent") or _conv_snapshot["intent"],
                workflow_type=_conv_snapshot["workflow_type"],
                workflow_step=_conv_snapshot["workflow_step"],
                workflow_data=_conv_snapshot["workflow_data"] or {},
                status=_conv_snapshot["status"],
                created_at=_conv_snapshot["created_at"],
                updated_at=_now,
            ),
        )

    raise HTTPException(status_code=500, detail="Failed to generate response")


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    current_user: User = Depends(get_current_user_or_demo),
    page: int = 1,
    page_size: int = 20,
    repo: ChatRepository = Depends(get_chat_repo),
):
    """
    List user's conversations.
    """
    user_id = str(current_user.id)
    conversations, total = await repo.list_conversations(user_id, page, page_size)

    return ConversationListResponse(
        conversations=conversations,
        total=total,
        page=page,
        page_size=page_size,
    )


# =============================================
# WEBSOCKET ENDPOINT
# =============================================

class ConnectionManager:
    """Manage WebSocket connections."""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_message(self, user_id: str, message: dict):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(message)


manager = ConnectionManager()


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str,
    repo: ChatRepository = Depends(get_chat_repo),
):
    """
    WebSocket endpoint for real-time chat with LIA.

    Message format:
    {
        "type": "message",
        "content": "text",
        "conversation_id": "uuid" (optional)
    }

    Response format:
    {
        "type": "message",
        "content": "text",
        "conversation_id": "uuid",
        "metadata": {...}
    }
    """
    await manager.connect(user_id, websocket)
    company_id = None

    try:
        while True:
            data = await websocket.receive_json()

            if data["type"] == "message":
                conversation_id = data.get("conversation_id")
                user_content = data["content"]

                # LIA-P02: Compliance enforcement for legacy WebSocket
                try:
                    from app.shared.compliance.fairness_guard import FairnessGuard
                    from app.shared.robustness.security_patterns import check_input_security

                    _security_result = check_input_security(user_content)
                    if _security_result and _security_result.get("blocked"):
                        await websocket.send_json({"type": "error", "message": "Mensagem bloqueada por seguranca."})
                        continue

                    _fg = FairnessGuard()
                    _fr = _fg.check(user_content)
                    if _fr and _fr.is_blocked:
                        await websocket.send_json({"type": "error", "message": _fr.educational_message or "Solicitacao com possivel vies."})
                        continue
                except Exception as e:
                    logger.debug("[LIA-P02] WS compliance check skipped: %s", e)

                # Create or get conversation
                if not conversation_id:
                    conversation = await repo.create_conversation(user_id)
                    conversation_id = str(conversation.id)
                else:
                    conversation = await repo.get_conversation_by_id(conversation_id)

                # Save user message
                await repo.add_user_message(conversation.id, user_content)

                # Run LIA via Orchestrator + ReAct agents
                ws_orch = await _invoke_orchestrator_legacy(

                    user_message=user_content,
                    user_id=user_id,
                    conversation_id=conversation_id,
                    company_id=company_id,
                )
                lia_response = ws_orch["response"]

                if lia_response:
                    # Item 2: handle_action_flow deleted — Phase 0+1 handles actions
                    ws_final_response = lia_response

                    ws_msg_metadata: dict[str, Any] = {
                        "intent": ws_orch["intent"],
                        "entities": ws_orch["entities"],
                    }

                    await repo.add_ai_message(
                        conversation.id,
                        ws_final_response,
                        ws_msg_metadata,
                    )
                    conversation.intent = ws_orch["intent"]

                    await repo.commit()

                    await manager.send_message(user_id, {
                        "type": "message",
                        "content": ws_final_response,
                        "conversation_id": conversation_id,
                        "metadata": ws_msg_metadata,
                    })

    except WebSocketDisconnect:
        manager.disconnect(user_id)


# =============================================
# SSE STREAMING ENDPOINT
# =============================================

# System prompt now composed dynamically via SystemPromptBuilder (persona + context)
# Replaces hardcoded _LIA_STREAM_SYSTEM_PROMPT — see prompt audit 2026-04-12


async def _sse_event_generator(
    conversation_id: str,
    user_message: str,
    history: list[dict[str, str]],
    repo: ChatRepository,
    conversation_obj,
    *,
    user_name: str = "",
    user_role: str = "",
    company_id: str = "",
    tenant_context_snippet: str = "",
) -> AsyncGenerator[str, None]:
    """Streams Claude tokens as SSE events and persists the full response.

    LIA-LLM-1: Uses get_anthropic_streaming_client_for_tenant to respect
    Choose Your AI — tenant gets billed on their own Anthropic key + model,
    not the global env key.
    """
    from app.shared.tenant_llm_context import get_anthropic_streaming_client_for_tenant

    try:
        client, _model = get_anthropic_streaming_client_for_tenant(company_id=company_id)
    except Exception as _e:
        logger.error("[SSE] Failed to get tenant streaming client: %s", _e)
        yield f"data: {json.dumps({'error': 'LLM not configured'})}\n\n"
        return

    full_response = ""

    from app.shared.prompts.system_prompt_builder import SystemPromptBuilder

    _system_prompt = SystemPromptBuilder.build(
        agent_type="orchestrator",
        tenant_context_snippet=tenant_context_snippet,
        user_name=user_name,
        user_role=user_role,
        conversation_history=history[-10:] if history else None,
        extra_instructions="Use markdown quando útil (listas, negrito), mas evite formatação excessiva em respostas simples.",
    )

    try:
        async with client.messages.stream(
            model=_model,
            max_tokens=2048,
            system=_system_prompt,
            messages=history,
        ) as stream:
            async for text_chunk in stream.text_stream:
                full_response += text_chunk
                yield f"data: {json.dumps({'token': text_chunk})}\n\n"

        yield "data: [DONE]\n\n"

        # Persist AI response to DB after streaming completes
        await repo.add_ai_message(
            conversation_obj.id,
            full_response,
            {"stream": True},
        )
        await repo.commit()

    except Exception as exc:
        logger.error(f"SSE stream error: {exc}", exc_info=True)
        yield f"data: {json.dumps({'error': str(exc)})}\n\n"


@router.post("/stream", response_model=None)
async def stream_message(
    request: Request,
    current_user: User = Depends(get_current_user_or_demo),
    repo: ChatRepository = Depends(get_chat_repo),
):
    """
    Stream LIA response as SSE (Server-Sent Events).

    Request body: {"content": "...", "conversation_id": "..." (optional)}

    Events emitted:
      data: {"token": "..."} — incremental token
      data: [DONE]           — stream finished
      data: {"error": "..."}  — on error
    """
    body = await request.json()
    user_content: str = body.get("content", "").strip()
    conversation_id: str | None = body.get("conversation_id")

    if not user_content:
        raise HTTPException(status_code=422, detail="content is required")

    user_id = str(current_user.id)

    # Create or retrieve conversation
    if not conversation_id:
        conversation = await repo.create_conversation(user_id)
        conversation_id = str(conversation.id)
    else:
        conversation = await repo.get_conversation_by_id(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

    # Save user message
    await repo.add_user_message(conversation.id, user_content)

    # Build history for Claude (last 20 messages to stay within context limits)
    history_msgs = await repo.get_recent_messages(conversation.id, limit=20)
    history = [
        {"role": "user" if m.role in ("human", "user") else "assistant", "content": m.content}
        for m in history_msgs
    ]

    # Fetch tenant context (same pattern as MainOrchestrator)
    _tenant_snippet = ""
    _company_id = str(getattr(current_user, "company_id", "")) or ""
    if _company_id:
        try:
            from app.shared.services.tenant_context_service import TenantContextService
            _tenant_ctx = await TenantContextService().get_context(
                company_id=_company_id, db=repo.db
            )
            _tenant_snippet = _tenant_ctx.to_prompt_snippet()
        except Exception:
            pass  # Fail-safe: proceed without tenant context


    # LIA-P01: Compliance enforcement for SSE streaming path
    try:
        from app.shared.compliance.fairness_guard import FairnessGuard
        from app.shared.robustness.security_patterns import check_input_security

        _security_result = check_input_security(user_content)
        if _security_result and _security_result.get("blocked"):
            return JSONResponse(
                status_code=400,
                content={"error": True, "message": "Mensagem bloqueada por verificacao de seguranca."}
            )

        _fairness_guard = FairnessGuard()
        _fairness_result = _fairness_guard.check(user_content)
        if _fairness_result and _fairness_result.is_blocked:
            return JSONResponse(
                status_code=400,
                content={"error": True, "message": _fairness_result.educational_message or "Sua solicitacao contem termos que podem gerar vies."}
            )
    except Exception as e:
        logger.debug("[LIA-P01] SSE compliance check skipped (fail-open): %s", e)

    return StreamingResponse(
        _sse_event_generator(
            conversation_id, user_content, history, repo, conversation,
            user_name=getattr(current_user, "name", "") or "",
            user_role=str(getattr(current_user, "role", "")) or "",
            company_id=_company_id,
            tenant_context_snippet=_tenant_snippet,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.post("/actions/candidate-field-update", response_model=None)
async def direct_candidate_field_update(
    request: Request,
    current_user: User = Depends(get_current_user_or_demo),
    repo: ChatRepository = Depends(get_chat_repo),
):
    """
    Structured endpoint to update one or more candidate fields directly.
    Used by the CV upload closed-loop confirmation flow to avoid
    reconstructing actions from natural language text.
    """
    body = await request.json()
    candidate_id: str = body.get("candidate_id", "")
    candidate_name: str = body.get("candidate_name", "").strip()
    fields: dict = body.get("fields", {})

    if not fields:
        raise HTTPException(status_code=400, detail="fields are required")

    # Resolve candidate_id by name if not provided directly
    if not candidate_id and candidate_name:
        try:
            found_id = await repo.lookup_candidate_id_by_name(candidate_name)
            if found_id:
                candidate_id = found_id
            else:
                raise HTTPException(status_code=404, detail=f"Candidato '{candidate_name}' não encontrado.")
        except HTTPException:
            raise
        except Exception as lookup_err:
            logger.warning(f"Candidate name lookup failed: {lookup_err}")
            raise HTTPException(status_code=400, detail="Não foi possível localizar o candidato pelo nome.")

    if not candidate_id:
        raise HTTPException(status_code=400, detail="candidate_id or candidate_name is required")

    intent_key = "atualizar_campo_candidato"
    action_config = ACTIONABLE_INTENTS.get(intent_key)
    if not action_config:
        raise HTTPException(status_code=500, detail="Action config not found for atualizar_campo_candidato")

    company_id = getattr(current_user, "company_id", None)

    # Authorization: verify the candidate belongs to the requester's company.
    # Uses vacancy_candidates join table which has both company_id and candidate_id.
    # If the user has no company_id (e.g. demo mode), skip the check and allow update.
    if company_id:
        try:
            owns = await repo.check_candidate_ownership(candidate_id, str(company_id))
            if not owns:
                raise HTTPException(
                    status_code=403,
                    detail="Candidate does not belong to your company or does not exist.",
                )
        except HTTPException:
            raise
        except Exception as authz_err:
            logger.warning(f"Authz check failed, proceeding cautiously: {authz_err}")
            # If vacancy_candidates table doesn't exist or query fails, reject
            raise HTTPException(status_code=403, detail="Unable to verify candidate ownership.")

    ctx = {
        "user_id": str(current_user.id),
        "company_id": company_id,
        "tenant_id": str(company_id) if company_id else None,
    }

    results = []
    for field_name, field_value in fields.items():
        result: ActionResult = await action_executor._execute_action(
            intent=intent_key,
            config=action_config,
            params={
                "candidate_id": candidate_id,
                "field_name": field_name,
                "field_value": str(field_value),
            },
            context=ctx,
        )
        results.append({
            "field": field_name,
            "value": field_value,
            "status": result.status,
            "message": result.message,
            "error": getattr(result, "error_detail", None),
        })

    all_ok = all(r["status"] in ("executed", "success") for r in results)
    updated_count = sum(1 for r in results if r["status"] in ("executed", "success"))
    return {
        "success": all_ok,
        "updated_count": updated_count,
        "total": len(results),
        "results": results,
    }
