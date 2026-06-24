"""
Voice API Endpoints

REST API para transcrição de áudio usando Gemini Flash.
"""
import logging
import mimetypes

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.shared.services.gemini_voice_service import get_voice_service
from fastapi import Depends
from app.shared.security.require_company_id import require_company_id
from app.shared.errors import LIAError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["voice"])


def detect_mime_type(filename: str, content_type: str | None) -> str:
    """
    Detect MIME type from filename if content_type is missing or generic.
    
    Fallback when uploads come with application/octet-stream.
    """
    # MIME type normalization map (Python's mimetypes vs Gemini expected)
    MIME_TYPE_ALIASES = {
        "audio/x-wav": "audio/wav",
        "audio/x-m4a": "audio/mp4",
    }
    
    if content_type and content_type != "application/octet-stream":
        return MIME_TYPE_ALIASES.get(content_type, content_type)
    
    # Try to guess from filename extension
    if filename:
        guessed_type, _ = mimetypes.guess_type(filename)
        if guessed_type:
            return MIME_TYPE_ALIASES.get(guessed_type, guessed_type)
    
    # Default fallback
    return "audio/mpeg"


@router.get("/voice/health", response_model=None)
async def voice_health_check(company_id: str = Depends(require_company_id)):
    # multi-tenancy: public endpoint (health) — no tenant data
    """Check if Gemini Voice service is configured."""
    try:
        get_voice_service()
        return {
            "service": "Gemini Voice-to-Text",
            "status": "configured",
            "model": "gemini-2.5-flash",
            "provider": "Replit AI Integrations",
            "message": "Voice transcription ready"
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "service": "Gemini Voice-to-Text",
                "status": "unavailable",
                "error": str(e)
            }
        )


@router.post("/voice/transcribe", response_model=None)
async def transcribe_audio(
    audio: UploadFile = File(..., description="Audio file to transcribe"),
    language: str = Form("pt-BR", description="Target language (default: pt-BR)"),
    prompt: str | None = Form(None, description="Custom transcription prompt"), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Transcreve arquivo de áudio para texto.
    
    Formatos suportados:
    - Audio: MP3, M4A, WAV, OGG, WEBM, FLAC
    - Video: MP4, MPEG, WEBM, MOV
    
    Exemplo:
    ```bash
    curl -X POST http://localhost:8000/api/v1/voice/transcribe \
      -F "audio=@interview.mp3" \
      -F "language=pt-BR"
    ```
    """
    try:
        service = get_voice_service()
        
        audio_data = await audio.read()
        mime_type = detect_mime_type(audio.filename, audio.content_type)
        
        logger.info(f"📤 Received audio: {audio.filename}, {mime_type}, {len(audio_data)} bytes")
        
        result = await service.transcribe_audio(
            audio_data=audio_data,
            mime_type=mime_type,
            prompt=prompt,
            language=language
        )
        
        return {
            "success": True,
            "transcription": result["text"],
            "metadata": {
                "filename": audio.filename,
                "language": result["language"],
                "mime_type": result["mime_type"],
                "size_bytes": result["size_bytes"],
                "model": result["model"]
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Transcription failed: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.post("/voice/analyze", response_model=None)
async def analyze_audio(
    audio: UploadFile = File(..., description="Audio file to analyze"),
    analysis_type: str = Form("full", description="Analysis type: full, sentiment, topics, summary"), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Analisa áudio além de transcrição (sentimento, tópicos, insights).
    
    Tipos de análise:
    - **full**: Transcrição + sentimento + tópicos + soft skills + resumo
    - **sentiment**: Apenas análise de sentimento e emoções
    - **topics**: Identifica os 5 tópicos principais
    - **summary**: Resumo em 2-3 parágrafos
    
    Exemplo:
    ```bash
    curl -X POST http://localhost:8000/api/v1/voice/analyze \
      -F "audio=@candidate_response.mp3" \
      -F "analysis_type=sentiment"
    ```
    """
    try:
        service = get_voice_service()
        
        audio_data = await audio.read()
        mime_type = detect_mime_type(audio.filename, audio.content_type)
        
        logger.info(f"📊 Analyzing audio: {audio.filename}, type={analysis_type}")
        
        result = await service.analyze_audio(
            audio_data=audio_data,
            mime_type=mime_type,
            analysis_type=analysis_type
        )
        
        return {
            "success": True,
            "analysis": result["analysis"],
            "metadata": {
                "filename": audio.filename,
                "analysis_type": result["analysis_type"],
                "mime_type": result["mime_type"],
                "size_bytes": result["size_bytes"],
                "model": result["model"]
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.post("/voice/interview", response_model=None)
async def analyze_interview(
    audio: UploadFile = File(..., description="Interview audio file"),
    job_title: str | None = Form(None, description="Job title for context"),
    questions: str | None = Form(None, description="Expected questions (comma-separated)"), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Transcreve e analisa entrevista de candidato com scoring.
    
    Retorna:
    - Transcrição completa
    - Análise de respostas
    - Scores de comunicação, conhecimento técnico, fit cultural
    - Recomendação (Avançar/Reconsiderar/Não avançar)
    - Próximos passos sugeridos
    
    Exemplo:
    ```bash
    curl -X POST http://localhost:8000/api/v1/voice/interview \
      -F "audio=@interview.mp3" \
      -F "job_title=Senior Python Developer" \
      -F "questions=Conte sobre sua experiência,Qual seu maior projeto,Como você lida com prazos"
    ```
    """
    try:
        service = get_voice_service()
        
        audio_data = await audio.read()
        mime_type = detect_mime_type(audio.filename, audio.content_type)
        
        questions_list = None
        if questions:
            questions_list = [q.strip() for q in questions.split(",") if q.strip()]
        
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"🎯 Analyzing interview: {audio.filename}, job={job_title}")
        
        result = await service.transcribe_interview(
            audio_data=audio_data,
            mime_type=mime_type,
            job_title=job_title,
            questions=questions_list
        )
        
        return {
            "success": True,
            "interview_analysis": result["interview_analysis"],
            "metadata": {
                "filename": audio.filename,
                "job_title": result["job_title"],
                "questions_count": result["questions_count"],
                "mime_type": result["mime_type"],
                "size_bytes": result["size_bytes"],
                "model": result["model"]
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Interview analysis failed: {e}")
        raise LIAError(message="Erro interno do servidor")
