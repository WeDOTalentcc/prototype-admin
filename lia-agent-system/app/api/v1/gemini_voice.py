"""
Gemini Live Audio WebSocket Endpoint — Bidirectional voice streaming for screening.

Replaces the Twilio-based VoIP pipeline with a direct browser↔Gemini Live Audio
WebSocket connection. Handles STT, LLM conversation, and TTS in a single stream.

Endpoints:
- /gemini-voice/live-stream     : WebSocket for bidirectional audio streaming
- /gemini-voice/start-session   : POST to create a new screening session
- /gemini-voice/session/{id}    : GET session status and results
- /gemini-voice/health          : GET service health check

Security:
- Session must be pre-created via /start-session (validates consent, company_id)
- WebSocket validates session_id before accepting connection
- PII masked in all logs (LGPD Art. 12)
- Session timeout: 20 minutes max
- Rate limiting on session creation
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
from app.shared.resilience.circuit_breaker import GEMINI_LIVE_CIRCUIT
from fastapi import Depends
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item


def _get_hmac_secret() -> str:
    secret = os.environ.get("SECRET_KEY") or os.environ.get("APP_SECRET_KEY")
    if not secret:
        raise RuntimeError(
            "SECRET_KEY or APP_SECRET_KEY must be set for WebSocket token signing. "
            "Cannot generate secure ws_token without a server secret."
        )
    return secret


def _generate_ws_token(session_id: str, company_id: str, candidate_id: str) -> str:
    secret = _get_hmac_secret()
    payload = f"{session_id}:{company_id}:{candidate_id}"
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()[:32]


def _verify_ws_token(ws_token: str, session_id: str, company_id: str, candidate_id: str) -> bool:
    try:
        expected = _generate_ws_token(session_id, company_id, candidate_id)
    except RuntimeError:
        return False
    return hmac.compare_digest(ws_token, expected)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["gemini-voice"])


class StartSessionRequest(WeDoBaseModel):
    candidate_id: str
    candidate_name: str
    job_title: str
    job_id: str | None = None
    language: str = "pt-BR"


class StartSessionResponse(WeDoBaseModel):
    success: bool
    session_id: str
    status: str
    voice_provider: str = "gemini_live"
    gemini_available: bool
    ws_token: str | None = None
    error: str | None = None
    fallback_channel: str | None = None


@router.post("/gemini-voice/start-session", response_model=StartSessionResponse)
async def start_gemini_voice_session(
    request_body: StartSessionRequest,
    request: Request,
company_id: str = Depends(require_company_id)) -> StartSessionResponse:
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Create a new Gemini Live Audio screening session.

    Validates LGPD consent, creates session state, and returns session_id
    for the WebSocket connection. The session must be created before
    connecting to /gemini-voice/live-stream.

    Rate limited to MAX_SESSIONS_PER_IP_PER_MINUTE per client IP.

    Fallback: If Gemini Live is unavailable (circuit open or not configured),
    returns gemini_available=False with fallback_channel suggestion.
    """
    client_ip = "unknown"
    if request.client:
        client_ip = request.client.host or "unknown"
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()

    now = time.time()
    timestamps = _session_creation_timestamps.get(client_ip, [])
    timestamps = [t for t in timestamps if now - t < 60]
    if len(timestamps) >= MAX_SESSIONS_PER_IP_PER_MINUTE:
        raise HTTPException(
            status_code=429,
            detail="Limite de criação de sessões atingido. Aguarde um momento.",
        )
    timestamps.append(now)
    _session_creation_timestamps[client_ip] = timestamps

    try:
        from app.shared.services.gemini_live_audio_service import get_gemini_live_service
        from app.domains.voice.services.voice_screening_orchestrator import (
            ConsentNotGrantedError,
            voice_screening_orchestrator,
        )

        try:
            from app.core.database import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                await voice_screening_orchestrator.verify_consent(
                    candidate_id=request_body.candidate_id,
                    company_id=company_id,
                    db=db,
                )
        except ConsentNotGrantedError:
            raise HTTPException(
                status_code=451,
                detail={
                    "error": "consent_revoked",
                    "message": "Candidato não concedeu consentimento para triagem por voz (LGPD Art. 7)",
                },
            )

        live_service = get_gemini_live_service()

        if not live_service.is_available:
            logger.warning(
                "[GEMINI VOICE] Gemini Live Audio not available — returning fallback"
            )
            return StartSessionResponse(
                success=False,
                session_id="",
                status="fallback",
                gemini_available=False,
                error="Gemini Live Audio não configurado",
                fallback_channel="twilio",
            )

        if GEMINI_LIVE_CIRCUIT.state.value == "open":
            logger.warning(
                "[GEMINI VOICE] GEMINI_LIVE_CIRCUIT open — returning fallback"
            )
            return StartSessionResponse(
                success=False,
                session_id="",
                status="fallback",
                gemini_available=False,
                error="Gemini Live Audio temporariamente indisponível (circuit breaker)",
                fallback_channel="twilio",
            )

        job_context = None
        try:
            from app.core.database import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                job_context = await voice_screening_orchestrator._fetch_job_context_from_db(
                    request_body.job_id or "",
                    db,
                    company_id=company_id,
                )
        except Exception as e:
            logger.debug("[GEMINI VOICE] Job context fetch failed (non-blocking): %s", e)

        session = live_service.create_session(
            candidate_id=request_body.candidate_id,
            candidate_name=request_body.candidate_name,
            job_title=request_body.job_title,
            company_id=company_id,
            job_id=request_body.job_id,
            language=request_body.language,
            job_context=job_context,
        )

        logger.info(
            "[GEMINI VOICE] Session started: session=%s candidate=%s company=%s",
            session.session_id,
            mask_pii(request_body.candidate_id),
            company_id,
        )

        ws_token = _generate_ws_token(
            session.session_id,
            company_id,
            request_body.candidate_id,
        )

        return StartSessionResponse(
            success=True,
            session_id=session.session_id,
            status="ready",
            gemini_available=True,
            ws_token=ws_token,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("[GEMINI VOICE] Start session error: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")


_active_ws_sessions: dict[str, bool] = {}
_ws_ip_connections: dict[str, int] = {}
MAX_WS_PER_IP = 3
_session_creation_timestamps: dict[str, list[float]] = {}
MAX_SESSIONS_PER_IP_PER_MINUTE = 5


@router.websocket("/gemini-voice/live-stream")
async def gemini_live_stream_websocket(
    websocket: WebSocket,
    session_id: str = Query(...),
    ws_token: str = Query(...),
company_id: str = Depends(require_company_id)):
    """
    WebSocket endpoint for bidirectional Gemini Live Audio streaming.

    Protocol (browser → server):
      {"type": "audio", "data": "<base64_pcm_16khz>"}
      {"type": "text", "data": "candidate typed message"}
      {"type": "end"}

    Protocol (server → browser):
      {"type": "audio", "data": "<base64_audio>", "mime_type": "audio/pcm"}
      {"type": "transcript", "role": "candidate"|"lia", "text": "..."}
      {"type": "status", "status": "connected"|"processing"|"ended"|"error"}
      {"type": "metrics", "latency_ms": 123, "tokens": {...}}

    Security:
      - session_id must match a pre-created session via /start-session or triagem voip-start
      - Unknown session_id is rejected with 4403
      - Only one concurrent WebSocket per session (prevents replay)
      - Per-IP rate limiting (max 3 concurrent connections)
      - Session timeout enforced (20 minutes)
      - company_id and candidate_id validated from session (tenant isolation)
    """
    from app.shared.services.gemini_live_audio_service import get_gemini_live_service

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
            "message": "Limite de conexões simultâneas atingido. Tente novamente em instantes.",
        })
        await websocket.close(code=4429)
        return

    live_service = get_gemini_live_service()
    session = live_service.get_session(session_id)

    if not session:
        await websocket.accept()
        await websocket.send_json({
            "type": "error",
            "message": "Sessão inválida ou expirada. Crie uma nova sessão.",
        })
        await websocket.close(code=4403)
        return

    if session_id in _active_ws_sessions:
        await websocket.accept()
        await websocket.send_json({
            "type": "error",
            "message": "Sessão já possui uma conexão ativa.",
        })
        await websocket.close(code=4409)
        return

    if not session.company_id or not session.candidate_id:
        await websocket.accept()
        await websocket.send_json({
            "type": "error",
            "message": "Sessão sem tenant ou candidato vinculado.",
        })
        await websocket.close(code=4403)
        return

    if not _verify_ws_token(ws_token, session_id, session.company_id, session.candidate_id):
        await websocket.accept()
        await websocket.send_json({
            "type": "error",
            "message": "Token de autenticação WebSocket inválido.",
        })
        await websocket.close(code=4401)
        logger.warning(
            "[GEMINI VOICE WS] Invalid ws_token for session=%s ip=%s",
            session_id, client_ip,
        )
        return

    _active_ws_sessions[session_id] = True
    _ws_ip_connections[client_ip] = current_ip_count + 1

    await websocket.accept()
    logger.info(
        "[GEMINI VOICE WS] Live stream connected session=%s company=%s",
        session_id,
        session.company_id,
    )

    session.status = "connected"

    await websocket.send_json({
        "type": "status",
        "status": "connected",
        "session_id": session_id,
        "voice_provider": "gemini_live",
    })

    try:
        config = await live_service.create_live_connection_config(session)

        import os

        from google import genai
        from google.genai import types  # W3-027-EXEMPT: google.genai.types import for Gemini Live config building, client via get_gemini_client_for_tenant

        # === Tenant-aware Gemini client (LGPD compliance) ===
        try:
            from app.shared.tenant_llm_context import get_gemini_client_for_tenant
            client = get_gemini_client_for_tenant(session.company_id)
        except (ValueError, Exception) as _client_err:
            logger.warning("[GEMINI VOICE WS] Gemini unavailable: %s", _client_err)
            await websocket.send_json({
                "type": "error",
                "message": "Gemini Live Audio não configurado no servidor",
            })
            await websocket.close(code=4500)
            return

        live_config = types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name="Aoede",
                    )
                )
            ),
            system_instruction=types.Content(
                parts=[types.Part(text=config["system_instruction"])]
            ),
        )

        gemini_model = config.get("model", "gemini-2.0-flash-exp")

        async with client.aio.live.connect(
            model=gemini_model,
            config=live_config,
        ) as gemini_session:
            session.status = "in_progress"
            await websocket.send_json({
                "type": "status",
                "status": "in_progress",
            })

            turn_audio_buffer: list[bytes] = []

            async def receive_from_gemini():
                try:
                    while True:
                        turn_start = time.monotonic()
                        turn_audio_buffer.clear()
                        turn_text_parts: list[str] = []

                        async for response in gemini_session.receive():
                            if response.data:
                                turn_audio_buffer.append(response.data)

                            if response.text:
                                turn_text_parts.append(response.text)

                            if response.server_content and hasattr(response.server_content, 'input_transcription') and response.server_content.input_transcription:
                                candidate_text = response.server_content.input_transcription
                                if isinstance(candidate_text, str) and candidate_text.strip():
                                    await live_service.process_candidate_text(session, candidate_text)
                                    await websocket.send_json({
                                        "type": "transcript",
                                        "role": "candidate",
                                        "text": candidate_text,
                                    })
                                    logger.debug(
                                        "[GEMINI VOICE WS] Candidate transcript captured session=%s len=%d",
                                        session_id, len(candidate_text),
                                    )

                            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                                um = response.usage_metadata
                                if hasattr(um, 'prompt_token_count') and um.prompt_token_count:
                                    live_service.record_token_usage(session, input_tokens=um.prompt_token_count, output_tokens=0)
                                if hasattr(um, 'candidates_token_count') and um.candidates_token_count:
                                    live_service.record_token_usage(session, input_tokens=0, output_tokens=um.candidates_token_count)

                            if response.server_content and hasattr(response.server_content, 'turn_complete') and response.server_content.turn_complete:
                                turn_text = "".join(turn_text_parts)

                                fairness_ok = True
                                if turn_text:
                                    result = await live_service.process_lia_text(session, turn_text)
                                    if result is None and turn_text.strip():
                                        fairness_ok = False
                                        logger.warning(
                                            "[GEMINI VOICE WS] FairnessGuard blocked turn — audio suppressed session=%s",
                                            session_id,
                                        )
                                elif turn_audio_buffer:
                                    fairness_ok = False
                                    logger.warning(
                                        "[GEMINI VOICE WS] Audio without text transcript — suppressed for fairness safety session=%s",
                                        session_id,
                                    )

                                if fairness_ok:
                                    for audio_chunk in turn_audio_buffer:
                                        audio_b64 = base64.b64encode(audio_chunk).decode()
                                        await websocket.send_json({
                                            "type": "audio",
                                            "data": audio_b64,
                                            "mime_type": "audio/pcm",
                                        })
                                    if turn_text:
                                        await websocket.send_json({
                                            "type": "transcript",
                                            "role": "lia",
                                            "text": turn_text,
                                        })

                                latency_ms = (time.monotonic() - turn_start) * 1000
                                live_service.record_turn_latency(session, latency_ms)
                                await websocket.send_json({
                                    "type": "metrics",
                                    "latency_ms": round(latency_ms, 1),
                                    "tokens": session.token_usage,
                                })
                                turn_audio_buffer.clear()
                                break

                        if live_service.is_session_expired(session):
                            await websocket.send_json({
                                "type": "status",
                                "status": "timeout",
                                "message": "Sessão expirada (tempo máximo atingido)",
                            })
                            break

                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    logger.error(
                        "[GEMINI VOICE WS] Gemini receive error session=%s: %s",
                        session_id, e,
                    )
                    try:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Erro na comunicação com Gemini",
                        })
                    except Exception:
                        pass

            gemini_task = asyncio.create_task(receive_from_gemini())

            try:
                while True:
                    if live_service.is_session_expired(session):
                        await websocket.send_json({
                            "type": "status",
                            "status": "timeout",
                            "message": "Sessão expirada (tempo máximo atingido)",
                        })
                        break

                    try:
                        message = await asyncio.wait_for(
                            websocket.receive(),
                            timeout=300,
                        )
                    except TimeoutError:
                        await websocket.send_json({
                            "type": "status",
                            "status": "timeout",
                            "message": "Inatividade detectada",
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
                                    await gemini_session.send(
                                        input=types.LiveClientRealtimeInput(
                                            media_chunks=[
                                                types.Blob(
                                                    data=audio_bytes,
                                                    mime_type="audio/pcm;rate=16000",
                                                )
                                            ]
                                        )
                                    )

                            elif msg_type == "text":
                                text_input = data.get("data", "")
                                if text_input:
                                    await live_service.process_candidate_text(session, text_input)
                                    await gemini_session.send(
                                        input=text_input,
                                        end_of_turn=True,
                                    )

                            elif msg_type == "end":
                                logger.info(
                                    "[GEMINI VOICE WS] Client requested end session=%s",
                                    session_id,
                                )
                                break

                        except json.JSONDecodeError:
                            logger.warning(
                                "[GEMINI VOICE WS] Invalid JSON from client session=%s",
                                session_id,
                            )

                    elif "bytes" in message:
                        audio_bytes = message["bytes"]
                        if audio_bytes:
                            await gemini_session.send(
                                input=types.LiveClientRealtimeInput(
                                    media_chunks=[
                                        types.Blob(
                                            data=audio_bytes,
                                            mime_type="audio/pcm;rate=16000",
                                        )
                                    ]
                                )
                            )

            except WebSocketDisconnect:
                logger.info(
                    "[GEMINI VOICE WS] Client disconnected session=%s",
                    session_id,
                )
            finally:
                gemini_task.cancel()
                try:
                    await gemini_task
                except asyncio.CancelledError:
                    pass

        try:
            await GEMINI_LIVE_CIRCUIT.record_success()
        except Exception:
            pass

    except Exception as e:
        logger.error(
            "[GEMINI VOICE WS] Live stream error session=%s: %s",
            session_id, e,
        )
        try:
            await GEMINI_LIVE_CIRCUIT.record_failure()
        except Exception:
            pass
        try:
            await websocket.send_json({
                "type": "error",
                "message": "Erro na sessão de voz. Tente novamente.",
            })
        except Exception:
            pass
    finally:
        result = await live_service.finalize_session(session)
        logger.info(
            "[GEMINI VOICE WS] Session finalized session=%s result=%s",
            session_id,
            {k: v for k, v in result.items() if k != "transcript_segments"},
        )

        try:
            from app.core.database import AsyncSessionLocal
            from app.shared.services.token_tracking_service import TokenTrackingService
            async with AsyncSessionLocal() as tok_db:
                token_svc = TokenTrackingService(db=tok_db)
                total_latency = sum(session.turn_latencies_ms) if session.turn_latencies_ms else 0.0
                await token_svc.record_usage(
                    user_id=session.candidate_id,
                    company_id=session.company_id,
                    agent_type="screening",
                    intent="gemini_live_audio_interview",
                    input_tokens=session.token_usage.get("input", 0),
                    output_tokens=session.token_usage.get("output", 0),
                    model=gemini_model,
                    latency_ms=total_latency,
                    candidate_id=session.candidate_id,
                    vacancy_id=session.job_id,
                    extra_data={
                        "voice_provider": "gemini_live",
                        "turns": len(session.turn_latencies_ms),
                        "p95_latency_ms": sorted(session.turn_latencies_ms)[int(len(session.turn_latencies_ms) * 0.95)] if session.turn_latencies_ms else 0,
                    },
                )
        except Exception as tok_err:
            logger.warning(
                "[GEMINI VOICE WS] Token tracking record failed session=%s: %s",
                session_id, tok_err,
            )

        try:
            from app.core.database import AsyncSessionLocal
            from app.domains.voice.services.voice_screening_orchestrator import voice_screening_orchestrator

            async with AsyncSessionLocal() as db:
                orch_session = await voice_screening_orchestrator.get_or_restore_session(
                    session_id, db
                )
                if orch_session:
                    orch_session.transcript_segments = session.transcript_segments
                    orch_session.status = "analyzing"
                    orch_session.ended_at = session.ended_at
                    await voice_screening_orchestrator.persist_session_state(orch_session, db)
                    await voice_screening_orchestrator.finalize_screening(session_id, db=db)
        except Exception as finalize_err:
            logger.error(
                "[GEMINI VOICE WS] Orchestrator finalization failed session=%s: %s",
                session_id,
                finalize_err,
            )

        try:
            await websocket.send_json({
                "type": "status",
                "status": "ended",
                "metrics": live_service.get_session_metrics(session),
            })
        except Exception:
            pass

        try:
            await websocket.close()
        except Exception:
            pass

        live_service.remove_session(session_id)
        _active_ws_sessions.pop(session_id, None)
        ip_count = _ws_ip_connections.get(client_ip, 1)
        if ip_count <= 1:
            _ws_ip_connections.pop(client_ip, None)
        else:
            _ws_ip_connections[client_ip] = ip_count - 1


@router.get("/gemini-voice/session/{session_id}", response_model=None)
async def get_gemini_session_status(session_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)], company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    from app.shared.services.gemini_live_audio_service import get_gemini_live_service

    live_service = get_gemini_live_service()
    session = live_service.get_session(session_id)

    if not session:
        from app.core.database import AsyncSessionLocal
        from app.domains.voice.services.voice_screening_orchestrator import voice_screening_orchestrator

        try:
            async with AsyncSessionLocal() as db:
                orch_session = await voice_screening_orchestrator.get_or_restore_session(
                    session_id, db
                )
                if orch_session:
                    return {
                        "session_id": session_id,
                        "status": orch_session.status,
                        "voice_provider": getattr(orch_session, "voice_provider", "unknown"),
                        "transcript_segments": len(orch_session.transcript_segments),
                        "wsi_result": orch_session.wsi_result,
                    }
        except Exception:
            pass

        raise HTTPException(status_code=404, detail="Session not found")

    return live_service.get_session_metrics(session)


@router.get("/gemini-voice/health", response_model=None)
async def gemini_voice_health(company_id: str = Depends(require_company_id)):
    # multi-tenancy: public endpoint (health) — no tenant data
    from app.shared.services.gemini_live_audio_service import get_gemini_live_service

    live_service = get_gemini_live_service()
    circuit_stats = GEMINI_LIVE_CIRCUIT.get_stats()

    return {
        "service": "Gemini Live Audio Screening",
        "gemini_available": live_service.is_available,
        "circuit_breaker": {
            "state": circuit_stats["state"],
            "failure_count": circuit_stats["failure_count"],
        },
        "status": "ready" if live_service.is_available else "unconfigured",
        "fallback_chain": ["chat", "whatsapp"],
        "cost_per_interview_usd": "~0.065 (15 min)",
        "target_latency_p95_ms": 500,
    }

reorder_collection_before_item(router)
