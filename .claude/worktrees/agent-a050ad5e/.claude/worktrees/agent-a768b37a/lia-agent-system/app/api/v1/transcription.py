"""
Audio Transcription API - Endpoints for speech-to-text using Deepgram.

Deepgram Nova-2 is used for high-accuracy Portuguese transcription.
Cost: $0.0043/minute
Free tier: 12,000 minutes/year
"""
import logging
from fastapi import APIRouter, File, UploadFile, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.deepgram_service import deepgram_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/transcribe", tags=["transcription"])


class TranscriptionResponse(BaseModel):
    """Response from audio transcription."""
    text: str
    language: Optional[str] = None
    confidence: Optional[float] = None
    duration_seconds: Optional[float] = None
    cost_estimate: Optional[float] = None
    error: Optional[str] = None


class TranscribeUrlRequest(BaseModel):
    """Request to transcribe audio from URL."""
    audio_url: str
    language: str = "pt-BR"


@router.post("/audio", response_model=TranscriptionResponse)
async def transcribe_audio(audio: UploadFile = File(...)):
    """
    Transcribe uploaded audio to text using Deepgram Nova-2.
    
    Supports WebM, MP4, MP3, WAV, OGG audio formats.
    Optimized for Brazilian Portuguese (pt-BR).
    """
    if not audio.filename:
        raise HTTPException(status_code=400, detail="No audio file provided")
    
    try:
        content = await audio.read()
        
        if len(content) < 1000:
            return TranscriptionResponse(
                text="",
                error="Áudio muito curto para transcrição",
            )
        
        filename = audio.filename.lower() if audio.filename else "audio.webm"
        if filename.endswith('.webm'):
            mime_type = "audio/webm"
        elif filename.endswith('.mp4'):
            mime_type = "audio/mp4"
        elif filename.endswith('.mp3'):
            mime_type = "audio/mp3"
        elif filename.endswith('.wav'):
            mime_type = "audio/wav"
        elif filename.endswith('.ogg'):
            mime_type = "audio/ogg"
        elif filename.endswith('.m4a'):
            mime_type = "audio/mp4"
        else:
            mime_type = "audio/webm"
        
        logger.info(f"🎤 Transcribing {len(content)} bytes of {mime_type} audio via Deepgram")
        
        result = await deepgram_service.transcribe_audio_bytes(
            audio_data=content,
            mimetype=mime_type,
            language="pt-BR"
        )
        
        if result.is_error:
            logger.error(f"Deepgram transcription error: {result.error_message}")
            return TranscriptionResponse(
                text="",
                language="pt-BR",
                error=f"Erro na transcrição: {result.error_message}"
            )
        
        logger.info(f"✅ Transcription complete: {len(result.text)} chars, {result.duration_seconds:.1f}s")
        
        return TranscriptionResponse(
            text=result.text,
            language=result.language,
            confidence=result.confidence,
            duration_seconds=result.duration_seconds,
            cost_estimate=result.cost_estimate,
        )
            
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        return TranscriptionResponse(
            text="",
            error=f"Erro ao processar áudio: {str(e)}",
        )


@router.post("/url", response_model=TranscriptionResponse)
async def transcribe_audio_url(request: TranscribeUrlRequest):
    """
    Transcribe audio from URL using Deepgram Nova-2.
    
    Useful for:
    - WhatsApp voice messages (media URLs)
    - S3/cloud storage audio files
    - OpenMic.ai call recordings
    """
    if not request.audio_url:
        raise HTTPException(status_code=400, detail="audio_url is required")
    
    try:
        logger.info(f"🎤 Transcribing audio from URL via Deepgram")
        
        result = await deepgram_service.transcribe_audio_url(
            audio_url=request.audio_url,
            language=request.language
        )
        
        if result.is_error:
            logger.error(f"Deepgram URL transcription error: {result.error_message}")
            return TranscriptionResponse(
                text="",
                language=request.language,
                error=f"Erro na transcrição: {result.error_message}"
            )
        
        logger.info(f"✅ URL transcription complete: {len(result.text)} chars, {result.duration_seconds:.1f}s")
        
        return TranscriptionResponse(
            text=result.text,
            language=result.language,
            confidence=result.confidence,
            duration_seconds=result.duration_seconds,
            cost_estimate=result.cost_estimate,
        )
            
    except Exception as e:
        logger.error(f"Error transcribing audio URL: {e}")
        return TranscriptionResponse(
            text="",
            error=f"Erro ao processar áudio: {str(e)}",
        )


@router.get("/status")
async def get_transcription_status():
    """
    Check if transcription service is configured and ready.
    """
    return {
        "service": "deepgram",
        "model": "nova-2",
        "configured": deepgram_service.is_configured,
        "cost_per_minute": deepgram_service.COST_PER_MINUTE,
        "supported_languages": ["pt-BR", "en-US", "es"],
        "supported_formats": ["webm", "mp3", "mp4", "wav", "ogg", "m4a"]
    }
