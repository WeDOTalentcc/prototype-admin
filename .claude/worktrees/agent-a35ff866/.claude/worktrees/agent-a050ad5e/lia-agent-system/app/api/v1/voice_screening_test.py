"""
Voice Screening Test Endpoints

Test endpoints to validate Deepgram and OpenMic integrations.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
import logging

from app.services.deepgram_service import deepgram_service, TranscriptionResult
from app.services.openmic_service import openmic_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/voice-test", tags=["Voice Screening Tests"])


class TranscribeUrlRequest(BaseModel):
    audio_url: str = Field(..., description="Public URL to audio file")
    language: str = Field(default="pt-BR", description="Language code")


class CreateAgentRequest(BaseModel):
    job_title: str = Field(..., description="Job title")
    job_description: str = Field(..., description="Full job description")
    required_skills: List[str] = Field(..., description="List of required skills")
    questions: Optional[List[str]] = Field(default=None, description="Optional custom questions")


class SimulateCallRequest(BaseModel):
    agent_id: str = Field(..., description="OpenMic agent ID")
    candidate_phone: str = Field(..., description="Phone number (+5511999999999)")
    candidate_name: str = Field(..., description="Candidate full name")
    candidate_id: Optional[str] = Field(default=None)
    job_title: Optional[str] = Field(default=None)
    dry_run: bool = Field(default=True, description="Simulate without calling API")


@router.get("/status")
async def check_voice_services_status():
    """Check status of voice screening services."""
    return {
        "deepgram": {
            "configured": deepgram_service.is_configured,
            "service": "Deepgram Nova-2",
            "use_case": "WhatsApp audio transcription",
            "cost_per_minute": deepgram_service.COST_PER_MINUTE
        },
        "openmic": {
            "configured": bool(openmic_service.api_key),
            "service": "OpenMic.ai",
            "use_case": "Automated voice screening calls",
            "base_url": openmic_service.base_url
        }
    }


@router.post("/transcribe-url")
async def test_transcribe_url(request: TranscribeUrlRequest):
    """
    Test Deepgram transcription with an audio URL.
    
    Args:
        request: TranscribeUrlRequest with audio_url and language
    """
    if not deepgram_service.is_configured:
        raise HTTPException(
            status_code=503,
            detail="Deepgram API key not configured. Set DEEPGRAM_API_KEY."
        )
    
    result = await deepgram_service.transcribe_audio_url(request.audio_url, request.language)
    
    return {
        "success": not result.is_error,
        "text": result.text,
        "confidence": result.confidence,
        "duration_seconds": result.duration_seconds,
        "language": result.language,
        "cost_estimate": result.cost_estimate,
        "word_count": len(result.words) if result.words else 0,
        "error": result.error_message if result.is_error else None
    }


@router.post("/transcribe-file")
async def test_transcribe_file(
    file: UploadFile = File(...),
    language: str = "pt-BR"
):
    """
    Test Deepgram transcription with uploaded audio file.
    
    Supported formats: ogg, mp3, wav, m4a, webm, flac
    """
    if not deepgram_service.is_configured:
        raise HTTPException(
            status_code=503,
            detail="Deepgram API key not configured. Set DEEPGRAM_API_KEY."
        )
    
    content = await file.read()
    
    content_type = file.content_type or "audio/ogg"
    
    result = await deepgram_service.transcribe_audio_bytes(
        audio_data=content,
        mimetype=content_type,
        language=language
    )
    
    return {
        "success": not result.is_error,
        "filename": file.filename,
        "text": result.text,
        "confidence": result.confidence,
        "duration_seconds": result.duration_seconds,
        "language": result.language,
        "cost_estimate": result.cost_estimate,
        "error": result.error_message if result.is_error else None
    }


@router.post("/create-screening-agent")
async def test_create_screening_agent(request: CreateAgentRequest):
    """
    Test OpenMic agent creation for voice screening.
    
    Creates a screening agent configured for Brazilian Portuguese.
    """
    if not openmic_service.api_key:
        raise HTTPException(
            status_code=503,
            detail="OpenMic API key not configured. Set OPENMIC_API_KEY."
        )
    
    try:
        agent = await openmic_service.create_screening_agent(
            job_title=request.job_title,
            job_description=request.job_description,
            required_skills=request.required_skills,
            questions=request.questions
        )
        
        return {
            "success": True,
            "agent_id": agent.get("agent_id"),
            "agent_name": agent.get("name"),
            "agent": agent
        }
    except Exception as e:
        logger.error(f"Failed to create screening agent: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create agent: {str(e)}"
        )


@router.post("/simulate-call")
async def test_simulate_screening_call(request: SimulateCallRequest):
    """
    Test starting a screening call via OpenMic.
    
    Args:
        request: SimulateCallRequest with agent_id, candidate details, and dry_run flag
    
    Note: When dry_run=False, this will actually initiate a call to the phone number!
    Use with caution - only for testing with consent.
    """
    if not openmic_service.api_key and not request.dry_run:
        raise HTTPException(
            status_code=503,
            detail="OpenMic API key not configured. Set OPENMIC_API_KEY or use dry_run=True."
        )
    
    try:
        call = await openmic_service.start_screening_call(
            agent_id=request.agent_id,
            candidate_phone=request.candidate_phone,
            candidate_name=request.candidate_name,
            candidate_id=request.candidate_id,
            job_title=request.job_title,
            dry_run=request.dry_run
        )
        
        return {
            "success": True,
            "dry_run": request.dry_run,
            "call_id": call.get("call_id"),
            "status": call.get("status"),
            "call": call
        }
    except Exception as e:
        logger.error(f"Failed to start call: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start call: {str(e)}"
        )
