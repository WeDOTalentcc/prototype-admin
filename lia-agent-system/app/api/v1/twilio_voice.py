"""
Twilio Voice TwiML Endpoints — Programmable Voice for LIA screening.

These endpoints are called by Twilio during the call lifecycle:
- /greeting            : Initial TwiML served when Twilio connects
- /consent-response    : Handles candidate's YES/NO consent via Gather
- /audio-stream        : WebSocket for real-time bidirectional audio (Twilio Media Streams)
- /status              : Call status webhook (initiated/completed/failed)
- /end-call/{id}       : Programmatic call termination
- /initiate            : REST endpoint to start an outbound call (with DB consent check)
- /sessions/{id}       : Session status/results
- /health              : Service health check

Security:
- Twilio webhook signature validated via X-Twilio-Signature header
- WebSocket sessions validated against known session_id
- PII masked in all logs (LGPD Art. 12)
- Consent enforced before call initiation (LGPD Art. 7 / Crença #4)
"""

import asyncio
import base64
import json
import logging
from typing import Optional, Dict, Any

from fastapi import (
    APIRouter,
    Depends,
    Form,
    HTTPException,
    Query,
    Request,
    Response,
    WebSocket,
    WebSocketDisconnect,
)
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.voice_screening_orchestrator import (
    voice_screening_orchestrator,
    ConsentNotGrantedError,
    VoiceScreeningOrchestratorError,
)
from app.domains.communication.services.twilio_voice_service import (
    twilio_voice_service,
    TwilioVoiceError,
    TwilioVoiceUnconfiguredError,
)
from app.shared.pii_masking import mask_pii

logger = logging.getLogger(__name__)

router = APIRouter(tags=["twilio-voice"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class InitiateCallRequest(BaseModel):
    """Request to initiate an outbound voice screening call."""
    candidate_id: str
    candidate_name: str
    phone_number: str
    job_title: str
    company_id: str
    job_id: Optional[str] = None
    language: str = "pt-BR"


class InitiateCallResponse(BaseModel):
    """Response from call initiation."""
    success: bool
    session_id: str
    call_sid: Optional[str] = None
    status: str
    error: Optional[str] = None
    fallback_channel: Optional[str] = None


# ── Helpers ────────────────────────────────────────────────────────────────────

def _twiml_response(xml: str) -> Response:
    """Return TwiML XML response with correct content type."""
    return Response(content=xml, media_type="application/xml")


def _verify_twilio_signature(request: Request, params: Dict[str, str]) -> bool:
    """
    Validate Twilio webhook request signature.

    In development (no auth_token configured), always returns True.
    In production, validates X-Twilio-Signature against the full URL + params.
    """
    signature = request.headers.get("X-Twilio-Signature", "")
    url = str(request.url)
    return twilio_voice_service.verify_webhook_signature(url, params, signature)


# ── Initiate call endpoint ─────────────────────────────────────────────────────

@router.post("/twilio-voice/initiate", response_model=InitiateCallResponse)
async def initiate_voice_screening(
    request_body: InitiateCallRequest,
    request: Request,
) -> InitiateCallResponse:
    """
    Initiate an outbound voice screening call to a candidate.

    - Verifies LGPD consent via DB (hard-block on revoke, soft-warn on absent)
    - Opens TWILIO_VOICE_CIRCUIT protected Twilio call
    - Returns fallback_channel='whatsapp' when voice unavailable (explicit, not mock)
    """
    try:
        from app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            session_obj = await voice_screening_orchestrator.initiate_call(
                candidate_id=request_body.candidate_id,
                candidate_name=request_body.candidate_name,
                phone_number=request_body.phone_number,
                job_title=request_body.job_title,
                company_id=request_body.company_id,
                job_id=request_body.job_id,
                language=request_body.language,
                db=session,
            )
    except ConsentNotGrantedError as e:
        raise HTTPException(
            status_code=451,
            detail={
                "error": "consent_revoked",
                "message": "Candidato revogou consentimento para triagem por voz (LGPD Art. 18)",
                "detail": str(e),
            },
        )
    except Exception as e:
        logger.error("[TWILIO VOICE API] Initiate call error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

    fallback = None
    if session_obj.status in ("fallback", "failed"):
        fallback = "whatsapp"

    return InitiateCallResponse(
        success=session_obj.status == "initiated",
        session_id=session_obj.session_id,
        call_sid=session_obj.call_sid,
        status=session_obj.status,
        error=session_obj.error,
        fallback_channel=fallback,
    )


# ── TwiML webhooks (called by Twilio) ─────────────────────────────────────────

@router.post("/twilio-voice/greeting")
async def twiml_greeting(
    request: Request,
    session_id: str = Query(...),
    candidate_name: str = Query("candidato"),
    job_title: str = Query("a vaga"),
    language: str = Query("pt-BR"),
):
    """
    TwiML endpoint: serve greeting when Twilio connects the outbound call.
    Validates Twilio signature to prevent spoofing.
    """
    form_data = await request.form()
    params = dict(form_data)

    if not _verify_twilio_signature(request, params):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    try:
        twiml = twilio_voice_service.generate_greeting_twiml(
            session_id=session_id,
            candidate_name=candidate_name,
            job_title=job_title,
            language=language,
        )
        logger.info(
            "[TWILIO VOICE] Serving greeting TwiML session=%s", session_id
        )
        return _twiml_response(twiml)
    except (TwilioVoiceError, TwilioVoiceUnconfiguredError) as e:
        logger.error("[TWILIO VOICE] Greeting TwiML error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


def _parse_consent_speech(speech: str) -> bool:
    """
    Parse consent from speech-to-text output with negative-intent precedence (LGPD-safe).

    Algorithm:
    1. Empty/whitespace-only → deny (default-deny)
    2. Normalise: strip accents, lowercase, tokenize on word boundaries
    3. ANY single negation token in the token set → deny (covers "não", "nao", "no", …)
       This handles compound phrases like "não aceito" because "não"/"nao" is itself
       a negation token — no multi-word entry needed.
    4. ANY single affirmative token in the token set → consent
    5. No recognised token → deny (ambiguous = deny)
    """
    import re
    import unicodedata

    if not speech or not speech.strip():
        return False

    def _normalise(text: str) -> str:
        nfd = unicodedata.normalize("NFD", text.lower())
        return "".join(c for c in nfd if unicodedata.category(c) != "Mn")

    normalised = _normalise(speech)
    tokens = set(re.findall(r"\b\w+\b", normalised))

    negation_tokens = {
        "nao", "no", "never", "nunca", "jamais", "recuso",
        "recusando", "negar", "nego", "discordo", "discordando",
        "nope", "negativo",
    }

    affirmative_tokens = {
        "sim", "yes", "pode", "claro", "ok", "certo", "concordo",
        "aceito", "topo", "vamos", "continuar", "prosseguir",
        "autorizo", "autorizar", "permito", "permitir", "consinto",
        "consentir", "afirmativo",
    }

    if tokens & negation_tokens:
        return False

    return bool(tokens & affirmative_tokens)


@router.post("/twilio-voice/consent-response")
async def twiml_consent_response(
    request: Request,
    session_id: str = Query(...),
    language: str = Query("pt-BR"),
    SpeechResult: Optional[str] = Form(None),
    Confidence: Optional[str] = Form(None),
    CallSid: Optional[str] = Form(None),
):
    """
    TwiML endpoint: handle candidate's consent response (YES/NO from Gather).
    Validates Twilio signature.
    """
    form_data = await request.form()
    params = dict(form_data)

    if not _verify_twilio_signature(request, params):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    speech = (SpeechResult or "").lower().strip()
    logger.info(
        "[TWILIO VOICE] Consent response: session=%s speech='%s' confidence=%s",
        session_id,
        mask_pii(speech)[:50],
        Confidence,
    )

    consent_given = _parse_consent_speech(speech)

    if consent_given:
        try:
            twiml = twilio_voice_service.generate_stream_twiml(
                session_id=session_id,
                language=language,
            )
        except (TwilioVoiceError, TwilioVoiceUnconfiguredError) as e:
            logger.error("[TWILIO VOICE] Stream TwiML error: %s", e)
            raise HTTPException(status_code=500, detail=str(e))
    else:
        twiml = twilio_voice_service.generate_end_twiml(
            message=(
                "Entendido! Respeitamos sua decisão. "
                "Você pode participar da triagem via chat quando preferir. "
                "Obrigada e tenha um ótimo dia!"
            ),
            language=language,
        )
        session = voice_screening_orchestrator.get_session(session_id)
        if session:
            session.status = "declined"

    return _twiml_response(twiml)


@router.post("/twilio-voice/status")
async def twiml_call_status(
    request: Request,
    CallSid: str = Form(...),
    CallStatus: str = Form(...),
    CallDuration: Optional[str] = Form(None),
    From: Optional[str] = Form(None),
    To: Optional[str] = Form(None),
):
    """
    Twilio call status callback webhook.
    Validates Twilio signature and processes call lifecycle events.
    """
    form_data = await request.form()
    params = dict(form_data)

    if not _verify_twilio_signature(request, params):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    logger.info(
        "[TWILIO VOICE] Call status: sid=%s status=%s duration=%s",
        CallSid,
        CallStatus,
        CallDuration,
    )

    if CallStatus in ("completed", "failed", "busy", "no-answer", "canceled"):
        for active in voice_screening_orchestrator.list_active_sessions():
            s = voice_screening_orchestrator.get_session(active["session_id"])
            if s and s.call_sid == CallSid:
                if CallStatus == "completed" and s.status not in (
                    "completed", "analyzing", "analysis_failed", "declined"
                ):
                    logger.info(
                        "[TWILIO VOICE] Call completed, finalizing session=%s",
                        s.session_id,
                    )
                    asyncio.create_task(
                        voice_screening_orchestrator.finalize_screening(s.session_id)
                    )
                elif CallStatus in ("failed", "busy", "no-answer", "canceled"):
                    s.status = CallStatus
                break

    return Response(content="", status_code=204)


# ── WebSocket: Twilio Media Streams ──────────────────────────────────────────

@router.websocket("/twilio-voice/audio-stream")
async def audio_stream_websocket(
    websocket: WebSocket,
    session_id: str = Query(...),
):
    """
    WebSocket endpoint for Twilio Bidirectional Media Streams.

    Audio pipeline (inbound from Twilio):
      base64(raw μ-law 8kHz) → decode → mulaw_to_wav() → Gemini STT → text

    Audio pipeline (outbound to Twilio):
      LIA text → OpenAI TTS → MP3 → mp3_to_mulaw() → base64 → Twilio media event

    Protocol (Twilio Media Streams):
      {"event": "connected"} → {"event": "start", "streamSid": "..."} →
      {"event": "media", "media": {"payload": "<base64_mulaw>"}} →
      {"event": "stop"}

    Security:
      - session_id must match an existing session created via /initiate
      - Unknown session_id is rejected immediately
    """
    session = voice_screening_orchestrator.get_session(session_id)
    if not session:
        await websocket.accept()
        await websocket.send_json({
            "event": "error",
            "message": f"Unknown session_id: {session_id}. Call must be initiated via /initiate first.",
        })
        await websocket.close(code=4403)
        return

    await websocket.accept()
    logger.info("[TWILIO VOICE WS] Audio stream connected session=%s", session_id)

    audio_buffer = bytearray()
    stream_sid = None
    BUFFER_THRESHOLD = 8000

    try:
        while True:
            try:
                message = await websocket.receive()
                if message.get("type") == "websocket.disconnect":
                    break

                if "text" in message:
                    data = json.loads(message["text"])
                    event = data.get("event")

                    if event == "connected":
                        logger.debug("[TWILIO VOICE WS] Stream connected")

                    elif event == "start":
                        stream_sid = data.get("streamSid")
                        logger.info(
                            "[TWILIO VOICE WS] Stream started: sid=%s session=%s",
                            stream_sid,
                            session_id,
                        )
                        session.status = "in_progress"

                    elif event == "media":
                        payload = data.get("media", {}).get("payload", "")
                        if payload:
                            chunk = base64.b64decode(payload)
                            audio_buffer.extend(chunk)

                            if len(audio_buffer) >= BUFFER_THRESHOLD:
                                transcript = await voice_screening_orchestrator.process_audio_chunk(
                                    session_id=session_id,
                                    audio_data=bytes(audio_buffer),
                                    mime_type="audio/mulaw",
                                )
                                audio_buffer.clear()

                                if transcript:
                                    lia_response = await voice_screening_orchestrator.generate_lia_response(
                                        session_id=session_id,
                                        candidate_utterance=transcript,
                                    )

                                    if lia_response and stream_sid:
                                        mulaw_audio = await voice_screening_orchestrator.synthesize_lia_response(
                                            lia_response, for_twilio_stream=True
                                        )
                                        if mulaw_audio:
                                            audio_b64 = base64.b64encode(mulaw_audio).decode()
                                            await websocket.send_json({
                                                "event": "media",
                                                "streamSid": stream_sid,
                                                "media": {"payload": audio_b64},
                                            })
                                        else:
                                            logger.info(
                                                "[TWILIO VOICE WS] TTS→μ-law unavailable; "
                                                "LIA response logged but not streamed: %s",
                                                lia_response[:80],
                                            )

                    elif event == "stop":
                        logger.info(
                            "[TWILIO VOICE WS] Stream stopped session=%s", session_id
                        )
                        if audio_buffer:
                            await voice_screening_orchestrator.process_audio_chunk(
                                session_id=session_id,
                                audio_data=bytes(audio_buffer),
                                mime_type="audio/mulaw",
                            )
                            audio_buffer.clear()
                        break

                elif "bytes" in message:
                    audio_buffer.extend(message["bytes"])

            except WebSocketDisconnect:
                break

    except Exception as e:
        logger.error("[TWILIO VOICE WS] Stream error session=%s: %s", session_id, e)
    finally:
        try:
            await websocket.close()
        except Exception:
            pass

        if audio_buffer:
            await voice_screening_orchestrator.process_audio_chunk(
                session_id=session_id,
                audio_data=bytes(audio_buffer),
                mime_type="audio/mulaw",
            )

        logger.info("[TWILIO VOICE WS] Stream closed session=%s", session_id)


# ── Management endpoints ───────────────────────────────────────────────────────

@router.post("/twilio-voice/end-call/{session_id}")
async def end_call(session_id: str):
    """Programmatically end an active screening call."""
    session = voice_screening_orchestrator.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.call_sid:
        result = twilio_voice_service.end_call(session.call_sid)
        if result.get("success"):
            finalization = await voice_screening_orchestrator.finalize_screening(session_id)
            return {"success": True, "session_id": session_id, "result": finalization}
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to end call"),
            )

    return {"success": True, "session_id": session_id, "message": "No active call to end"}


@router.get("/twilio-voice/sessions/{session_id}")
async def get_session_status(session_id: str):
    """Get status and results of a voice screening session."""
    session = voice_screening_orchestrator.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": session.session_id,
        "status": session.status,
        "call_sid": session.call_sid,
        "job_title": session.job_title,
        "language": session.language,
        "questions_asked": len(session.questions_asked),
        "transcript_segments": len(session.transcript_segments),
        "started_at": session.started_at.isoformat() if session.started_at else None,
        "ended_at": session.ended_at.isoformat() if session.ended_at else None,
        "wsi_result": session.wsi_result,
        "error": session.error,
        "consent_verified": session.consent_verified,
    }


@router.get("/twilio-voice/health")
async def voice_health():
    """Health check for Twilio Voice service."""
    return {
        "service": "Twilio Voice Screening",
        "twilio_configured": twilio_voice_service.is_configured,
        "voice_number": twilio_voice_service.voice_number or "not configured",
        "base_url": twilio_voice_service.base_url or "not configured",
        "status": "ready" if twilio_voice_service.is_configured else "unconfigured",
        "fallback_channels": ["whatsapp", "chat"],
        "note": (
            "When unconfigured, /initiate returns status='fallback' with fallback_channel='whatsapp'"
        ),
    }
