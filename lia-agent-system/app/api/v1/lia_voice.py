"""
LIA Voice & Audio endpoints — extracted from lia_assistant.py (Sprint E).
Router is included by lia_assistant.router, so all routes resolve under /lia/voice/...
"""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form, WebSocket, WebSocketDisconnect, Response
from pydantic import BaseModel
import base64
import json
import logging
from uuid import uuid4

from app.services.voice_service import voice_service, VoiceServiceError, TranscriptionError, SynthesisError
from app.services.graph_runner import graph_runner_service

logger = logging.getLogger(__name__)

voice_router = APIRouter()

DEFAULT_COMPANY_UUID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"


# ── Schemas ──────────────────────────────────────────────────────────────────

class VoiceTranscriptionResponse(BaseModel):
    """Response from audio transcription."""
    text: str
    confidence: float
    duration: float
    words: List[Dict[str, Any]]
    language: str
    provider: str


class VoiceChatResponse(BaseModel):
    """Response from voice chat endpoint."""
    transcription: str
    response_text: str
    response_audio_base64: str
    session_id: str
    job_draft: Dict[str, Any]
    current_stage: Optional[str] = None
    is_complete: bool = False


class VoiceAvailabilityResponse(BaseModel):
    """Response showing which voice services are available."""
    transcription_deepgram: bool
    transcription_openai: bool
    synthesis_openai: bool
    any_transcription: bool
    any_synthesis: bool


# ── Endpoints ─────────────────────────────────────────────────────────────────

@voice_router.get("/voice/status")
async def get_voice_status() -> VoiceAvailabilityResponse:
    """Check which voice services are available."""
    availability = voice_service.is_available()
    return VoiceAvailabilityResponse(**availability)


@voice_router.post("/voice/transcribe", response_model=VoiceTranscriptionResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str = Query(default="pt-BR", description="Language code (e.g., pt-BR, en-US)")
) -> VoiceTranscriptionResponse:
    """
    Transcribe audio file to text.
    Accepts common audio formats: mp3, wav, webm, m4a, ogg, flac.
    """
    availability = voice_service.is_available()
    if not availability["any_transcription"]:
        raise HTTPException(
            status_code=503,
            detail="No transcription service available. Please configure DEEPGRAM_API_KEY or OPENAI_API_KEY."
        )
    try:
        audio_data = await file.read()
        if not audio_data:
            raise HTTPException(status_code=400, detail="Empty audio file")
        result = await voice_service.transcribe_audio(
            audio_data=audio_data,
            language=language,
            filename=file.filename
        )
        logger.info(
            f"Transcribed audio: {len(audio_data)} bytes, "
            f"duration={result.get('duration', 0):.1f}s, "
            f"provider={result.get('provider', 'unknown')}"
        )
        return VoiceTranscriptionResponse(**result)
    except TranscriptionError as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected transcription error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@voice_router.post("/voice/synthesize")
async def synthesize_speech(
    text: str = Form(..., description="Text to convert to speech"),
    voice: str = Form(default="nova", description="Voice: alloy, echo, fable, onyx, nova, shimmer"),
    speed: float = Form(default=1.0, ge=0.25, le=4.0, description="Speech speed (0.25-4.0)")
) -> Response:
    """Convert text to speech using OpenAI TTS. Returns MP3 audio."""
    availability = voice_service.is_available()
    if not availability["any_synthesis"]:
        raise HTTPException(
            status_code=503,
            detail="Speech synthesis not available. Please configure OPENAI_API_KEY."
        )
    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="Text is required for synthesis")
    try:
        audio_bytes = await voice_service.synthesize_speech(text=text, voice=voice, speed=speed)
        logger.info(f"Synthesized speech: {len(text)} chars -> {len(audio_bytes)} bytes, voice={voice}")
        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "attachment; filename=speech.mp3",
                "X-Text-Length": str(len(text)),
                "X-Voice": voice
            }
        )
    except SynthesisError as e:
        logger.error(f"Synthesis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected synthesis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Synthesis failed: {str(e)}")


@voice_router.post("/voice/chat", response_model=VoiceChatResponse)
async def voice_chat(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(default=None),
    company_id: str = Form(default=DEFAULT_COMPANY_UUID),
    user_id: str = Form(default="default_user"),
    language: str = Form(default="pt-BR"),
    voice: str = Form(default="nova"),
    skip_synthesis: bool = Form(default=False, description="Skip TTS to reduce latency")
) -> VoiceChatResponse:
    """Complete voice conversation flow with LIA job wizard."""
    availability = voice_service.is_available()
    if not availability["any_transcription"]:
        raise HTTPException(status_code=503, detail="Transcription service not available.")
    effective_session_id = session_id or str(uuid4())
    try:
        audio_data = await file.read()
        if not audio_data:
            raise HTTPException(status_code=400, detail="Empty audio file")
        transcription_result = await voice_service.transcribe_audio(
            audio_data=audio_data, language=language, filename=file.filename
        )
        transcribed_text = transcription_result.get("text", "")
        if not transcribed_text.strip():
            return VoiceChatResponse(
                transcription="",
                response_text="Desculpe, não consegui entender o que você disse. Pode repetir?",
                response_audio_base64="",
                session_id=effective_session_id,
                job_draft={},
                current_stage=None,
                is_complete=False
            )
        logger.info(f"Voice chat transcription: '{transcribed_text[:100]}...'")
        wizard_result = await graph_runner_service.run_job_wizard(
            session_id=effective_session_id,
            user_message=transcribed_text,
            company_id=company_id,
            user_id=user_id
        )
        response_text = wizard_result.get("response_text", "")
        audio_base64 = ""
        if not skip_synthesis and response_text and availability["any_synthesis"]:
            try:
                audio_response = await voice_service.synthesize_speech(text=response_text, voice=voice)
                audio_base64 = base64.b64encode(audio_response).decode()
            except Exception as e:
                logger.warning(f"TTS synthesis failed, returning text only: {e}")
        return VoiceChatResponse(
            transcription=transcribed_text,
            response_text=response_text,
            response_audio_base64=audio_base64,
            session_id=effective_session_id,
            job_draft=wizard_result.get("job_draft", {}),
            current_stage=wizard_result.get("current_stage"),
            is_complete=wizard_result.get("is_complete", False)
        )
    except TranscriptionError as e:
        logger.error(f"Voice chat transcription error: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    except Exception as e:
        logger.error(f"Voice chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Voice chat failed: {str(e)}")


@voice_router.websocket("/voice/stream")
async def voice_stream_websocket(websocket: WebSocket):
    """
    WebSocket for real-time voice streaming and transcription.
    Events: {"type": "partial"/"final"/"error"/"config_ack", ...}
    """
    await websocket.accept()
    availability = voice_service.is_available()
    if not availability["any_transcription"]:
        await websocket.send_json({"type": "error", "message": "Transcription service not available"})
        await websocket.close(code=1003)
        return

    language = "pt-BR"
    session_id = str(uuid4())
    audio_buffer = bytearray()

    try:
        while True:
            try:
                message = await websocket.receive()
                if message.get("type") == "websocket.disconnect":
                    break
                if "text" in message:
                    try:
                        data = json.loads(message["text"])
                        msg_type = data.get("type")
                        if msg_type == "config":
                            language = data.get("language", language)
                            session_id = data.get("session_id", session_id)
                            await websocket.send_json({"type": "config_ack", "session_id": session_id, "language": language})
                        elif msg_type == "end":
                            if audio_buffer:
                                result = await voice_service.transcribe_audio(bytes(audio_buffer), language=language)
                                await websocket.send_json({
                                    "type": "final",
                                    "text": result.get("text", ""),
                                    "confidence": result.get("confidence", 0.0),
                                    "duration": result.get("duration", 0.0)
                                })
                            break
                    except json.JSONDecodeError:
                        pass
                elif "bytes" in message:
                    audio_buffer.extend(message["bytes"])
                    if len(audio_buffer) >= 32000:
                        try:
                            result = await voice_service.transcribe_audio(bytes(audio_buffer), language=language)
                            await websocket.send_json({"type": "partial", "text": result.get("text", "")})
                        except Exception as e:
                            logger.warning(f"Partial transcription error: {e}")
            except WebSocketDisconnect:
                break
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
