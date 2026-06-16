"""
Provider-Agnostic Voice Streaming Endpoint.

Uses get_voice_provider_for_tenant() to automatically select the correct
voice provider based on tenant configuration:
  - Gemini tenant → GeminiLiveVoiceProvider (native multimodal)
  - OpenAI tenant → OpenAIRealtimeVoiceProvider (native multimodal)
  - Claude/other  → CompositeVoiceProvider (STT + LLM + TTS pipeline)

Endpoints:
- /voice-stream/start-session  : POST to create a streaming voice session
- /voice-stream/live           : WebSocket for bidirectional audio streaming
- /voice-stream/status         : GET provider status for current tenant
"""
import asyncio
import base64
import hashlib
import hmac
import json
import logging
import os
import time

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from pydantic import BaseModel

from app.shared.pii_masking import mask_pii
from fastapi import Depends
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)

router = APIRouter(tags=["voice-stream"])

_session_timestamps: dict[str, list[float]] = {}
_active_sessions: dict[str, bool] = {}
MAX_SESSIONS_PER_IP_PER_MINUTE = 5
MAX_WS_PER_IP = 3
_ws_ip_connections: dict[str, int] = {}

_session_metadata: dict[str, dict] = {}


def _get_hmac_secret() -> str:
    secret = os.environ.get("SECRET_KEY") or os.environ.get("APP_SECRET_KEY")
    if not secret:
        raise RuntimeError("SECRET_KEY or APP_SECRET_KEY must be set")
    return secret


def _generate_ws_token(session_id: str, tenant_id: str) -> str:
    secret = _get_hmac_secret()
    payload = f"{session_id}:{tenant_id}"
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()[:32]


def _verify_ws_token(ws_token: str, session_id: str, tenant_id: str) -> bool:
    try:
        expected = _generate_ws_token(session_id, tenant_id)
    except RuntimeError:
        return False
    return hmac.compare_digest(ws_token, expected)


class VoiceStreamStartRequest(WeDoBaseModel):
    language: str = "pt-BR"
    system_prompt: str = ""
    voice_name: str = "Aoede"


class VoiceStreamStartResponse(BaseModel):
    success: bool
    session_id: str = ""
    status: str = ""
    voice_provider: str = ""
    voice_strategy: str = ""
    ws_token: str | None = None
    error: str | None = None


@router.post("/voice-stream/start-session", response_model=VoiceStreamStartResponse)
async def start_voice_stream_session(
    request_body: VoiceStreamStartRequest,
    request: Request,
company_id: str = Depends(require_company_id)) -> VoiceStreamStartResponse:
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    # R4 canonical: company_id from JWT via require_company_id dependency (authoritative)
    tenant_id = company_id

    client_ip = "unknown"
    if request.client:
        client_ip = request.client.host or "unknown"
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()

    now = time.time()
    timestamps = _session_timestamps.get(client_ip, [])
    timestamps = [t for t in timestamps if now - t < 60]
    if len(timestamps) >= MAX_SESSIONS_PER_IP_PER_MINUTE:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded for session creation.",
        )
    timestamps.append(now)
    _session_timestamps[client_ip] = timestamps

    try:
        from uuid import uuid4

        from app.shared.providers.llm_factory import get_voice_provider_for_tenant
        from app.shared.providers.voice_provider import VoiceSessionConfig

        voice_provider = get_voice_provider_for_tenant(
            tenant_id=tenant_id,
        )

        if not await voice_provider.is_available():
            return VoiceStreamStartResponse(
                success=False,
                status="unavailable",
                voice_provider=voice_provider.provider_name,
                voice_strategy=voice_provider.strategy_type,
                error=f"Voice provider {voice_provider.provider_name} is not available",
            )

        session_id = str(uuid4())
        config = VoiceSessionConfig(
            tenant_id=tenant_id,
            session_id=session_id,
            language=request_body.language,
            system_prompt=request_body.system_prompt,
            voice_name=request_body.voice_name,
        )

        result = await voice_provider.create_session(config)

        _session_metadata[session_id] = {
            "tenant_id": tenant_id,
            "provider_name": voice_provider.provider_name,
            "strategy_type": voice_provider.strategy_type,
            "provider_instance": voice_provider,
        }

        ws_token = _generate_ws_token(session_id, tenant_id)

        logger.info(
            "[VOICE STREAM] Session started: session=%s tenant=%s provider=%s strategy=%s",
            session_id,
            tenant_id,
            voice_provider.provider_name,
            voice_provider.strategy_type,
        )

        return VoiceStreamStartResponse(
            success=True,
            session_id=session_id,
            status="ready",
            voice_provider=voice_provider.provider_name,
            voice_strategy=voice_provider.strategy_type,
            ws_token=ws_token,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("[VOICE STREAM] Start session error: %s", e)
        raise LIAError(message="Erro interno do servidor")


@router.websocket("/voice-stream/live")
async def voice_stream_websocket(
    websocket: WebSocket,
    session_id: str = Query(...),
    ws_token: str = Query(...),
company_id: str = Depends(require_company_id)):
    client_ip = "unknown"
    if websocket.client:
        client_ip = websocket.client.host or "unknown"
    forwarded = websocket.headers.get("x-forwarded-for")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()

    current_ip_count = _ws_ip_connections.get(client_ip, 0)
    if current_ip_count >= MAX_WS_PER_IP:
        await websocket.accept()
        await websocket.send_json({
            "type": "error",
            "message": "Connection limit reached.",
        })
        await websocket.close(code=4429)
        return

    session_meta = _session_metadata.get(session_id)
    if not session_meta:
        await websocket.accept()
        await websocket.send_json({
            "type": "error",
            "message": "Invalid or expired session.",
        })
        await websocket.close(code=4403)
        return

    tenant_id = session_meta["tenant_id"]
    if not _verify_ws_token(ws_token, session_id, tenant_id):
        await websocket.accept()
        await websocket.send_json({
            "type": "error",
            "message": "Invalid WebSocket auth token.",
        })
        await websocket.close(code=4401)
        return

    if session_id in _active_sessions:
        await websocket.accept()
        await websocket.send_json({
            "type": "error",
            "message": "Session already has an active connection.",
        })
        await websocket.close(code=4409)
        return

    voice_provider = session_meta["provider_instance"]
    _active_sessions[session_id] = True
    _ws_ip_connections[client_ip] = current_ip_count + 1

    await websocket.accept()
    logger.info(
        "[VOICE STREAM WS] Connected session=%s provider=%s tenant=%s",
        session_id,
        voice_provider.provider_name,
        tenant_id,
    )

    await websocket.send_json({
        "type": "status",
        "status": "connected",
        "session_id": session_id,
        "voice_provider": voice_provider.provider_name,
    })

    try:
        async def forward_events():
            try:
                async for event in voice_provider.receive_events(session_id):
                    msg: dict = {"type": event.event_type}

                    if event.event_type == "audio" and event.data:
                        msg["data"] = base64.b64encode(event.data).decode()
                        msg["mime_type"] = event.mime_type

                    elif event.event_type == "transcript":
                        msg["text"] = event.text
                        msg["role"] = event.role

                    elif event.event_type == "turn_complete":
                        msg["type"] = "metrics"
                        msg["latency_ms"] = event.metadata.get("latency_ms", 0)
                        msg["tokens"] = event.metadata.get("tokens", {})

                    elif event.event_type == "error":
                        msg["message"] = event.text

                    elif event.event_type == "timeout":
                        msg["type"] = "status"
                        msg["status"] = "timeout"
                        msg["message"] = event.text

                    try:
                        await websocket.send_json(msg)
                    except Exception:
                        break

                    if event.event_type in ("error", "timeout"):
                        break
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.error(
                    "[VOICE STREAM WS] Event forward error session=%s: %s",
                    session_id, e,
                )

        event_task = asyncio.create_task(forward_events())

        try:
            while True:
                try:
                    message = await asyncio.wait_for(
                        websocket.receive(),
                        timeout=300,
                    )
                except TimeoutError:
                    await websocket.send_json({
                        "type": "status",
                        "status": "timeout",
                        "message": "Inactivity timeout",
                    })
                    break

                if message.get("type") == "websocket.disconnect":
                    break

                if "text" in message:
                    try:
                        data = json.loads(message["text"])
                        msg_type = data.get("type")

                        if msg_type == "audio":
                            audio_bytes = base64.b64decode(data.get("data", ""))
                            if audio_bytes:
                                await voice_provider.send_audio(session_id, audio_bytes)

                        elif msg_type == "text":
                            text_input = data.get("data", "")
                            if text_input:
                                await voice_provider.send_text(session_id, text_input)

                        elif msg_type == "end":
                            break

                    except json.JSONDecodeError:
                        pass

                elif "bytes" in message:
                    audio_bytes = message["bytes"]
                    if audio_bytes:
                        await voice_provider.send_audio(session_id, audio_bytes)

        except WebSocketDisconnect:
            logger.info("[VOICE STREAM WS] Client disconnected session=%s", session_id)
        finally:
            event_task.cancel()
            try:
                await event_task
            except asyncio.CancelledError:
                pass

    except Exception as e:
        logger.error("[VOICE STREAM WS] Error session=%s: %s", session_id, e)
        try:
            await websocket.send_json({
                "type": "error",
                "message": "Voice session error.",
            })
        except Exception:
            pass
    finally:
        metrics = await voice_provider.close_session(session_id)
        logger.info(
            "[VOICE STREAM WS] Session finalized session=%s metrics=%s",
            session_id,
            {
                "provider": metrics.provider,
                "strategy": metrics.strategy,
                "turns": metrics.turn_count,
                "avg_latency_ms": metrics.avg_latency_ms,
            },
        )

        try:
            await websocket.send_json({
                "type": "status",
                "status": "ended",
                "metrics": {
                    "provider": metrics.provider,
                    "strategy": metrics.strategy,
                    "turn_count": metrics.turn_count,
                    "avg_latency_ms": metrics.avg_latency_ms,
                    "p95_latency_ms": metrics.p95_latency_ms,
                    "token_usage": metrics.token_usage,
                },
            })
        except Exception:
            pass

        try:
            await websocket.close()
        except Exception:
            pass

        _session_metadata.pop(session_id, None)
        _active_sessions.pop(session_id, None)
        ip_count = _ws_ip_connections.get(client_ip, 1)
        if ip_count <= 1:
            _ws_ip_connections.pop(client_ip, None)
        else:
            _ws_ip_connections[client_ip] = ip_count - 1


@router.get("/voice-stream/status")
async def voice_stream_status(company_id: str = Query(""), _company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    from app.shared.providers.llm_factory import get_voice_provider_for_tenant
from app.shared.errors import LIAError

    voice_provider = get_voice_provider_for_tenant(
        tenant_id=company_id or None,
    )

    status = voice_provider.get_status()

    return {
        "streaming_available": status.get("configured", False),
        "voice_provider": voice_provider.provider_name,
        "voice_strategy": voice_provider.strategy_type,
        "provider_status": status,
    }
