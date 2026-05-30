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
- /voip-token          : Generate Twilio Access Token for browser/VoIP calls (Twilio Client SDK)
- /voip-connect        : TwiML webhook called when browser client places a VoIP call (routes to audio-stream)

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

from fastapi import (
    APIRouter,
    Form,
    HTTPException,
    Query,
    Request,
    Response,
    WebSocket,
    WebSocketDisconnect,
)
from pydantic import BaseModel

from app.domains.communication.services.twilio_voice_service import (
    TwilioVoiceError,
    TwilioVoiceUnconfiguredError,
    twilio_voice_service,
)
from app.domains.voice.services.voice_screening_orchestrator import (
    ConsentNotGrantedError,
    voice_screening_orchestrator,
)
from app.shared.pii_masking import mask_pii
from fastapi import Depends
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

logger = logging.getLogger(__name__)

router = APIRouter(tags=["twilio-voice"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class InitiateCallRequest(WeDoBaseModel):
    """Request to initiate an outbound voice screening call."""
    candidate_id: str
    candidate_name: str
    phone_number: str
    job_title: str
    job_id: str | None = None
    language: str = "pt-BR"


class InitiateCallResponse(WeDoBaseModel):
    """Response from call initiation."""
    success: bool
    session_id: str
    call_sid: str | None = None
    status: str
    error: str | None = None
    fallback_channel: str | None = None


# ── Helpers ────────────────────────────────────────────────────────────────────

# TODO(phase2): extract to repository — Twilio call log storage
def _twiml_response(xml: str) -> Response:
    """Return TwiML XML response with correct content type."""
    return Response(content=xml, media_type="application/xml")


def _verify_twilio_signature(request: Request, params: dict[str, str]) -> bool:
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
    company_id: str = Depends(require_company_id),
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
                company_id=company_id,
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
    except HTTPException:
        raise
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

@router.post("/twilio-voice/greeting", response_model=None)
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


@router.post("/twilio-voice/consent-response", response_model=None)
async def twiml_consent_response(
    request: Request,
    session_id: str = Query(...),
    language: str = Query("pt-BR"),
    SpeechResult: str | None = Form(None),
    Confidence: str | None = Form(None),
    CallSid: str | None = Form(None),
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
        # F-15: get_session is now async (Redis-backed, multi-worker safe).
        session = await voice_screening_orchestrator.get_session(session_id)
        if session:
            session.status = "declined"
            # F-15: persist mutation back to Redis so other workers see it.
            await voice_screening_orchestrator._store_session(session)

    return _twiml_response(twiml)


@router.post("/twilio-voice/status", response_model=None)
async def twiml_call_status(
    request: Request,
    CallSid: str = Form(...),
    CallStatus: str = Form(...),
    CallDuration: str | None = Form(None),
    From: str | None = Form(None),
    To: str | None = Form(None),
):
    """
    Twilio call status callback webhook.
    Validates Twilio signature and processes call lifecycle events.
    """
    form_data = await request.form()
    params = dict(form_data)

    # Task #1146 — canonical ownership/signature validator. Twilio's signing
    # input is the request URL concatenated with sorted ``key+value`` of all
    # form params (NOT the raw body). The status callback payload carries no
    # tenant id, so we resolve it lazily via call_sid → session below and
    # use ``allow_anonymous_global=True`` during the 90-day dual-validate
    # window. ``_verify_twilio_signature`` (legacy path) is now subsumed.
    from app.shared.security.webhook_ownership import (
        WebhookOwnershipError,
        verify_webhook_owner,
    )

    twilio_canonical = str(request.url) + "".join(
        f"{k}{params[k]}" for k in sorted(params.keys())
    )
    twilio_signature = request.headers.get("X-Twilio-Signature", "")

    # Task #1146 — tenant-first single helper invocation. Resolve tenant
    # via wsi_sessions.call_id BEFORE signature verification; emit exactly
    # one canonical audit row per request (one of: unresolved_tenant, ok,
    # signature_invalid). D+90 deprecation works because we ALWAYS pass
    # the per-tenant ``declared_company_id`` once resolved.
    from app.shared.security.webhook_ownership import emit_ownership_audit

    resolved_company_id: str | None = None
    try:
        from app.core.database import AsyncSessionLocal as _ASL_lookup
        from sqlalchemy import text as _sa_text

        async with _ASL_lookup() as _db_lookup:
            _res = await _db_lookup.execute(
                _sa_text(
                    "SELECT company_id FROM wsi_sessions WHERE call_id = :sid LIMIT 1"
                ),
                {"sid": CallSid},
            )
            _row = _res.fetchone()
            if _row and _row[0]:
                resolved_company_id = str(_row[0])
    except Exception as _exc:
        logger.warning("[TWILIO VOICE] Tenant resolution failed: %s", _exc)

    if not resolved_company_id:
        await emit_ownership_audit(
            provider="twilio",
            decision="unresolved_tenant",
            company_id=None,
            session_id=CallSid,
        )
        logger.warning(
            "[TWILIO VOICE] CallSid=%s could not be bound to a tenant — "
            "rejecting 403 (Task #1146)",
            CallSid,
        )
        raise HTTPException(
            status_code=403,
            detail="webhook callback could not be bound to a tenant",
        )

    try:
        await verify_webhook_owner(
            provider="twilio",
            raw_body=b"",
            signature=twilio_signature,
            signature_payload=twilio_canonical.encode("utf-8"),
            declared_company_id=resolved_company_id,
            session_id=CallSid,
            enforce_ownership=False,
        )
    except WebhookOwnershipError as exc:
        logger.warning("[TWILIO VOICE] Ownership/signature rejected: %s", exc)
        raise HTTPException(status_code=exc.status_code, detail=str(exc))

    logger.info(
        "[TWILIO VOICE] Call status: sid=%s status=%s duration=%s",
        CallSid,
        CallStatus,
        CallDuration,
    )

    if CallStatus in ("completed", "failed", "busy", "no-answer", "canceled"):
        # F-15: in-memory iteration removed (multi-worker unsafe). Use DB lookup
        # by CallSid as the canonical path — wsi_sessions.call_id is the
        # globally-unique identifier and works across workers/restarts.
        matched_session = None
        from app.core.database import AsyncSessionLocal
        try:
            async with AsyncSessionLocal() as db:
                from app.domains.voice.repositories.wsi_repository import WsiRepository
                wsi_repo = WsiRepository(db)
                session_id = await wsi_repo.get_session_id_by_call_sid(CallSid)
                if session_id:
                    matched_session = await voice_screening_orchestrator.get_or_restore_session(session_id, db)
        except Exception as e:
            logger.warning("[TWILIO VOICE] DB session lookup by call_sid failed: %s", e)

        if matched_session:
            if CallStatus == "completed" and matched_session.status not in (
                "completed", "analyzing", "analysis_failed", "declined"
            ):
                logger.info(
                    "[TWILIO VOICE] Call completed, finalizing session=%s",
                    matched_session.session_id,
                )

                async def _finalize_with_db(sid: str):
                    from app.core.database import AsyncSessionLocal as _ASL
                    async with _ASL() as _db:
                        await voice_screening_orchestrator.finalize_screening(sid, db=_db)

                asyncio.create_task(_finalize_with_db(matched_session.session_id))
            elif CallStatus in ("failed", "busy", "no-answer", "canceled"):
                matched_session.status = CallStatus

                async def _persist_terminal_status(session):
                    from app.core.database import AsyncSessionLocal as _ASL
                    async with _ASL() as _db:
                        await voice_screening_orchestrator.persist_session_state(session, _db)

                asyncio.create_task(_persist_terminal_status(matched_session))

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
      LIA text → FairnessGuard → OpenAI TTS → MP3 → mp3_to_mulaw() → base64 → Twilio

    Protocol (Twilio Media Streams):
      {"event": "connected"} → {"event": "start", "streamSid": "..."} →
      {"event": "media", "media": {"payload": "<base64_mulaw>"}} →
      {"event": "stop"}

    Security:
      - session_id must match a session in memory or PostgreSQL (post-restart recovery)
      - Unknown session_id is rejected immediately
    """
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        session = await voice_screening_orchestrator.get_or_restore_session(session_id, db)
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
        turns_since_persist = 0
        PERSIST_EVERY_N_TURNS = 2

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
                            start_payload = data.get("start", {})
                            twilio_call_sid = start_payload.get("callSid") or data.get("callSid")
                            logger.info(
                                "[TWILIO VOICE WS] Stream started: sid=%s session=%s call_sid=%s",
                                stream_sid,
                                session_id,
                                twilio_call_sid,
                            )
                            session.status = "in_progress"
                            if twilio_call_sid and not session.call_sid:
                                session.call_sid = twilio_call_sid
                                try:
                                    from app.domains.voice.repositories.wsi_repository import WsiRepository
                                    wsi_repo = WsiRepository(db)
                                    await wsi_repo.bind_call_sid_to_session(session_id, twilio_call_sid)
                                except Exception as _bind_err:
                                    logger.warning("[TWILIO VOICE WS] Failed to bind call_sid to wsi_session: %s", _bind_err)
                            await voice_screening_orchestrator.persist_session_state(session, db)

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
                                            db=db,
                                        )

                                        turns_since_persist += 1
                                        if turns_since_persist >= PERSIST_EVERY_N_TURNS:
                                            await voice_screening_orchestrator.persist_session_state(session, db)
                                            turns_since_persist = 0

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
                            await voice_screening_orchestrator.persist_session_state(session, db)
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

            is_voip_session = getattr(session, "phone_number", None) == "voip"
            session_was_active = session.status in ("in_progress", "pending")
            await voice_screening_orchestrator.persist_session_state(session, db)
            logger.info("[TWILIO VOICE WS] Stream closed session=%s", session_id)

            if is_voip_session and session_was_active and session.status not in ("completed", "finalized"):
                logger.info(
                    "[TWILIO VOICE WS] VoIP session ended — triggering finalization session=%s",
                    session_id,
                )
                try:
                    from app.core.database import AsyncSessionLocal as _FinalizeASL
                    async with _FinalizeASL() as _fdb:
                        await voice_screening_orchestrator.finalize_screening(session_id, db=_fdb)
                except Exception as _finalize_err:
                    logger.error(
                        "[TWILIO VOICE WS] VoIP finalization failed session=%s: %s",
                        session_id,
                        _finalize_err,
                    )


# ── Management endpoints ───────────────────────────────────────────────────────

@router.post("/twilio-voice/end-call/{session_id}", response_model=None)
async def end_call(session_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)], ):
    """Programmatically end an active screening call."""
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        session = await voice_screening_orchestrator.get_or_restore_session(session_id, db)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        if session.call_sid:
            result = twilio_voice_service.end_call(session.call_sid)
            if result.get("success"):
                finalization = await voice_screening_orchestrator.finalize_screening(session_id, db=db)
                return {"success": True, "session_id": session_id, "result": finalization}
            else:
                raise HTTPException(
                    status_code=500,
                    detail=result.get("error", "Failed to end call"),
                )

        return {"success": True, "session_id": session_id, "message": "No active call to end"}


@router.get("/twilio-voice/sessions/{session_id}", response_model=None)
async def get_session_status(session_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)], ):
    """Get status and results of a voice screening session."""
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        session = await voice_screening_orchestrator.get_or_restore_session(session_id, db)
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


# ── VoIP (Browser Client) endpoints ───────────────────────────────────────────

class VoIPTokenRequest(WeDoBaseModel):
    """Request to generate a Twilio Access Token for the browser VoIP client."""
    session_id: str
    candidate_id: str
    identity: str | None = None


class VoIPTokenResponse(WeDoBaseModel):
    """Response with Twilio Access Token for the browser VoIP client."""
    token: str
    identity: str
    session_id: str
    twiml_app_sid: str | None = None
    expires_in: int = 3600
    voip_available: bool


@router.post("/twilio-voice/voip-token", response_model=VoIPTokenResponse)
async def generate_voip_token(request_body: VoIPTokenRequest, ) -> VoIPTokenResponse:
    """
    Generate a Twilio Access Token for the browser VoIP client (Twilio Client SDK).

    This token allows the frontend to place a VoIP call directly from the browser
    via WebRTC — without requiring a phone number. The call is routed through the
    same audio pipeline as PSTN calls (Twilio → WebSocket → Gemini STT → LIA → TTS).

    The token is scoped to:
    - A specific identity (candidate session)
    - TWILIO_TWIML_APP_SID (configured TwiML App that routes to /voip-connect)
    - 1-hour expiry

    Security: session_id must correspond to a known session created by the
    voice_screening_orchestrator (via /triagem/{token}/voip-start or /initiate).
    Requests for unknown sessions are rejected to prevent token minting abuse.

    Returns voip_available=False when Twilio is not configured (graceful degradation).
    """
    existing_session = voice_screening_orchestrator._sessions.get(request_body.session_id)
    if not existing_session:
        logger.warning(
            "[TWILIO VOIP] Token request for unknown session=%s — rejected",
            request_body.session_id,
        )
        raise HTTPException(status_code=404, detail="Sessão não encontrada")

    if existing_session.candidate_id != request_body.candidate_id:
        logger.warning(
            "[TWILIO VOIP] Token request session=%s candidate mismatch — rejected",
            request_body.session_id,
        )
        raise HTTPException(status_code=403, detail="Sessão não pertence ao candidato")

    if not twilio_voice_service.is_configured:
        logger.warning(
            "[TWILIO VOIP] Token request but Twilio not configured — returning unavailable. "
            "session=%s candidate=%s",
            request_body.session_id,
            mask_pii(request_body.candidate_id),
        )
        return VoIPTokenResponse(
            token="",
            identity="",
            session_id=request_body.session_id,
            twiml_app_sid=None,
            expires_in=0,
            voip_available=False,
        )

    try:
        token_result = twilio_voice_service.generate_voip_access_token(
            session_id=request_body.session_id,
            candidate_id=request_body.candidate_id,
            identity=request_body.identity,
        )
        logger.info(
            "[TWILIO VOIP] Access token generated: session=%s identity=%s",
            request_body.session_id,
            token_result["identity"],
        )
        return VoIPTokenResponse(
            token=token_result["token"],
            identity=token_result["identity"],
            session_id=request_body.session_id,
            twiml_app_sid=token_result.get("twiml_app_sid"),
            expires_in=token_result.get("expires_in", 3600),
            voip_available=True,
        )
    except TwilioVoiceUnconfiguredError:
        return VoIPTokenResponse(
            token="",
            identity="",
            session_id=request_body.session_id,
            voip_available=False,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("[TWILIO VOIP] Token generation failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to generate VoIP token: {e}")


@router.post("/twilio-voice/voip-connect", response_model=None)
async def twiml_voip_connect(
    request: Request,
    session_id: str | None = Query(None),
    language: str = Query("pt-BR"),
):
    """
    TwiML webhook: called by Twilio when the browser VoIP client places a call.

    Routes the browser VoIP call directly to the bidirectional audio-stream
    WebSocket (same pipeline as PSTN calls). No greeting/consent step is needed
    here because the candidate already consented via the web UI before clicking
    the VoIP call button.

    The session must have been pre-created via /initiate or already exist in
    memory/DB (the frontend creates the session before requesting the token).

    Note: Twilio Client SDK sends custom connect() params in the POST form body,
    NOT as query params. We read session_id from form body first, falling back
    to the query param (useful for direct TwiML App URL configuration).
    """
    form_data = await request.form()
    params = dict(form_data)

    if not _verify_twilio_signature(request, params):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    resolved_session_id = params.get("session_id") or session_id
    resolved_language = params.get("language") or language

    if not resolved_session_id:
        logger.error("[TWILIO VOIP] Missing session_id in voip-connect request (form=%s)", list(params.keys()))
        raise HTTPException(status_code=400, detail="session_id is required")

    logger.info(
        "[TWILIO VOIP] Browser VoIP call connected: session=%s language=%s",
        resolved_session_id,
        resolved_language,
    )

    try:
        twiml = twilio_voice_service.generate_voip_connect_twiml(
            session_id=resolved_session_id,
            language=resolved_language,
        )
        return _twiml_response(twiml)
    except (TwilioVoiceError, TwilioVoiceUnconfiguredError) as e:
        logger.error("[TWILIO VOIP] VoIP connect TwiML error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/twilio-voice/health", response_model=None)
async def voice_health():
    # multi-tenancy: public endpoint (health) — no tenant data
    """Health check for Twilio Voice service."""
    return {
        "service": "Twilio Voice Screening",
        "twilio_configured": twilio_voice_service.is_configured,
        "voice_number": twilio_voice_service.voice_number or "not configured",
        "base_url": twilio_voice_service.base_url or "not configured",
        "status": "ready" if twilio_voice_service.is_configured else "unconfigured",
        "fallback_channels": ["whatsapp", "chat"],
        "voip_available": twilio_voice_service.is_voip_configured,
        "note": (
            "When unconfigured, /initiate returns status='fallback' with fallback_channel='whatsapp'. "
            "VoIP requires TWILIO_TWIML_APP_SID in addition to standard Twilio config."
        ),
    }

reorder_collection_before_item(router)
