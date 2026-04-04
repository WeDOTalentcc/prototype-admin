import re
import logging
from typing import Optional, Any

from fastapi import APIRouter, HTTPException, Depends, Header, UploadFile, File, Form, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.services.triagem_session_service import triagem_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/triagem", tags=["triagem"])


class SendMessageRequest(BaseModel):
    content: str
    message_type: str = "text"
    selected_option: Optional[str] = None
    likert_value: Optional[int] = None
    voice_mode: Optional[bool] = None


class InviteRequest(BaseModel):
    candidate_id: str
    candidate_name: Optional[str] = None
    candidate_email: Optional[str] = None
    job_id: str
    job_title: Optional[str] = None
    company_id: str
    company_name: Optional[str] = None
    company_logo_url: Optional[str] = None
    invite_channel: str = "email"
    expires_days: int = 7
    voice_mode: bool = False


@router.get("/{token}")
async def get_triagem_session(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    config = await triagem_service.get_session_config(db, token)

    if config is None:
        raise HTTPException(status_code=404, detail="Session not found")

    if not config.get("valid"):
        error = config.get("error")
        if error == "not_found":
            raise HTTPException(status_code=404, detail="Token inválido ou sessão não encontrada")
        if error == "expired":
            raise HTTPException(
                status_code=410,
                detail="Este link de triagem expirou. Solicite um novo convite ao recrutador.",
            )

    return JSONResponse(content=config)


@router.post("/{token}/message")
async def send_message(
    token: str,
    request: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
):
    validation = await triagem_service.validate_token(db, token)

    if not validation.get("valid"):
        error = validation.get("error")
        if error == "not_found":
            raise HTTPException(status_code=404, detail="Token inválido")
        if error == "expired":
            raise HTTPException(status_code=410, detail="Link expirado")

    if validation.get("completed"):
        raise HTTPException(status_code=409, detail="Triagem já foi concluída")

    result = await triagem_service.process_message(
        db, token, request.content, request.message_type,
        voice_mode=request.voice_mode,
    )

    if result.get("error") == "not_found":
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    if result.get("error") == "already_completed":
        raise HTTPException(status_code=409, detail="Triagem já foi concluída")

    return JSONResponse(content=result)


@router.get("/{token}/history")
async def get_history(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    result = await triagem_service.get_history(db, token)

    if result.get("error") == "not_found":
        raise HTTPException(status_code=404, detail="Token inválido ou sessão não encontrada")

    return JSONResponse(content=result)


@router.post("/{token}/complete")
async def complete_triagem(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    validation = await triagem_service.validate_token(db, token)

    if not validation.get("valid"):
        error = validation.get("error")
        if error == "not_found":
            raise HTTPException(status_code=404, detail="Token inválido")
        if error == "expired":
            raise HTTPException(status_code=410, detail="Link expirado")

    if validation.get("completed"):
        raise HTTPException(status_code=409, detail="Triagem já foi concluída anteriormente")

    result = await triagem_service.complete_session(db, token)

    if result.get("error") == "not_found":
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    if result.get("error") == "already_completed":
        return JSONResponse(
            status_code=409,
            content={"detail": "Triagem já concluída", "session": result.get("session")},
        )

    return JSONResponse(content=result)


@router.post("/invite", status_code=201)
async def create_invite(
    request: InviteRequest,
    db: AsyncSession = Depends(get_db),
    x_company_id: Optional[str] = Header(None, alias="X-Company-ID"),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
):
    company_id = request.company_id or x_company_id
    if not company_id:
        raise HTTPException(status_code=400, detail="company_id é obrigatório")

    session = await triagem_service.create_session(
        db=db,
        candidate_id=request.candidate_id,
        job_id=request.job_id,
        company_id=company_id,
        candidate_name=request.candidate_name,
        candidate_email=request.candidate_email,
        job_title=request.job_title,
        company_name=request.company_name,
        company_logo_url=request.company_logo_url,
        invite_channel=request.invite_channel,
        created_by=x_user_id,
        expires_days=request.expires_days,
        voice_mode=request.voice_mode,
    )

    triagem_url = f"/triagem/{session.token}"

    logger.info(
        f"[Triagem] Invite created: token={session.token}, "
        f"candidate={request.candidate_name}, job={request.job_title}, "
        f"channel={request.invite_channel}"
    )

    return JSONResponse(
        status_code=201,
        content={
            "session": session.to_dict(),
            "triagem_url": triagem_url,
            "token": session.token,
            "message": f"Convite de triagem criado. Link: {triagem_url}",
        },
    )


_E164_BR_PATTERN = re.compile(r"^\+55\d{10,11}$")


class RequestCallRequest(BaseModel):
    candidate_phone: str

    @classmethod
    def __get_validators__(cls):
        yield from super().__get_validators__()

    def model_post_init(self, __context: Any = None) -> None:
        phone = self.candidate_phone.strip()
        digits = re.sub(r"\D", "", phone)
        if not phone.startswith("+"):
            if len(digits) == 10 or len(digits) == 11:
                phone = f"+55{digits}"
            elif len(digits) == 12 or len(digits) == 13:
                phone = f"+{digits}"
        if not _E164_BR_PATTERN.match(phone):
            raise ValueError("Telefone inválido. Use formato (DDD) + número, ex: (11) 99999-9999")
        object.__setattr__(self, "candidate_phone", phone)


@router.post("/{token}/request-call")
async def request_phone_call(
    token: str,
    request: RequestCallRequest,
    db: AsyncSession = Depends(get_db),
):
    """Request an automated phone call from LIA to the candidate via OpenMic.ai."""
    validation = await triagem_service.validate_token(db, token)

    if not validation.get("valid"):
        error = validation.get("error")
        if error == "not_found":
            raise HTTPException(status_code=404, detail="Token inválido")
        if error == "expired":
            raise HTTPException(status_code=410, detail="Link expirado")

    if validation.get("completed"):
        raise HTTPException(status_code=409, detail="Triagem já foi concluída")

    result = await triagem_service.request_phone_call(
        db, token, request.candidate_phone
    )

    if result.get("error") == "not_found":
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    if result.get("error") == "already_completed":
        raise HTTPException(status_code=409, detail="Triagem já foi concluída")
    if result.get("error") == "phone_not_enabled":
        raise HTTPException(status_code=403, detail="Canal de ligação não habilitado para esta vaga")
    if result.get("error") == "call_already_requested":
        raise HTTPException(status_code=429, detail=result.get("message", "Ligação já solicitada recentemente"))
    if result.get("error") == "agent_creation_failed":
        raise HTTPException(status_code=502, detail="Falha ao criar agente de voz")
    if result.get("error") == "call_failed":
        raise HTTPException(status_code=502, detail="Falha ao iniciar ligação")

    return JSONResponse(content=result)


class StartSessionRequest(BaseModel):
    voice_mode: Optional[bool] = None


@router.post("/{token}/start")
async def start_triagem(
    token: str,
    request: Optional[StartSessionRequest] = None,
    db: AsyncSession = Depends(get_db),
):
    validation = await triagem_service.validate_token(db, token)

    if not validation.get("valid"):
        error = validation.get("error")
        if error == "not_found":
            raise HTTPException(status_code=404, detail="Token inválido")
        if error == "expired":
            raise HTTPException(status_code=410, detail="Link expirado")

    if validation.get("completed"):
        raise HTTPException(status_code=409, detail="Triagem já foi concluída")

    vm = request.voice_mode if request else None
    result = await triagem_service.start_session(db, token, voice_mode=vm)

    if result.get("error") == "not_found":
        raise HTTPException(status_code=404, detail="Sessão não encontrada")

    return JSONResponse(content=result)


@router.post("/{token}/audio")
async def transcribe_audio(
    token: str,
    audio: UploadFile = File(...),
    question_index: Optional[int] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """Transcribe candidate audio using Deepgram STT (fallback OpenAI Whisper)."""
    validation = await triagem_service.validate_token(db, token)
    if not validation.get("valid"):
        error = validation.get("error")
        if error == "not_found":
            raise HTTPException(status_code=404, detail="Token inválido")
        if error == "expired":
            raise HTTPException(status_code=410, detail="Link expirado")
    if validation.get("completed"):
        raise HTTPException(status_code=409, detail="Triagem já foi concluída")

    audio_data = await audio.read()
    if not audio_data:
        raise HTTPException(status_code=400, detail="Arquivo de áudio vazio")

    from app.domains.cv_screening.services.deepgram_service import deepgram_triagem_service

    result = await deepgram_triagem_service.transcribe_candidate_audio(
        audio_data=audio_data,
        session_token=token,
        question_index=question_index,
        filename=audio.filename,
    )

    if result.get("error") and not result.get("text"):
        raise HTTPException(status_code=502, detail=f"Falha na transcrição: {result['error']}")

    return JSONResponse(content=result)


class TTSRequest(BaseModel):
    text: str
    voice: str = "nova"
    speed: float = 1.0
    question_index: Optional[int] = None


@router.post("/{token}/tts")
async def synthesize_speech(
    token: str,
    request: TTSRequest,
    db: AsyncSession = Depends(get_db),
):
    """Generate TTS audio for a triagem question using OpenAI TTS."""
    validation = await triagem_service.validate_token(db, token)
    if not validation.get("valid"):
        error = validation.get("error")
        if error == "not_found":
            raise HTTPException(status_code=404, detail="Token inválido")
        if error == "expired":
            raise HTTPException(status_code=410, detail="Link expirado")

    from app.domains.cv_screening.services.voice_service import triagem_voice_service

    result = await triagem_voice_service.synthesize_question(
        text=request.text,
        session_token=token,
        question_index=request.question_index,
        voice=request.voice,
        speed=request.speed,
    )

    if result.get("error") and not result.get("audio_base64"):
        raise HTTPException(status_code=502, detail=f"Falha na síntese: {result['error']}")

    return JSONResponse(content=result)


@router.post("/{token}/tts/{message_id}")
async def synthesize_message_speech(
    token: str,
    message_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Generate TTS audio on demand for a specific LIA message."""
    validation = await triagem_service.validate_token(db, token)
    if not validation.get("valid"):
        error = validation.get("error")
        if error == "not_found":
            raise HTTPException(status_code=404, detail="Token inválido")
        if error == "expired":
            raise HTTPException(status_code=410, detail="Link expirado")

    result = await triagem_service.generate_tts_for_message(db, token, message_id)

    if result.get("error") == "not_found":
        raise HTTPException(status_code=404, detail="Mensagem não encontrada")
    if result.get("error") == "not_lia_message":
        raise HTTPException(status_code=400, detail="TTS disponível apenas para mensagens da LIA")
    if result.get("error") == "tts_failed":
        raise HTTPException(status_code=502, detail="Falha na geração de áudio")

    return JSONResponse(content=result)


@router.get("/{token}/voice-status")
async def voice_status(token: str, db: AsyncSession = Depends(get_db)):
    """Check availability of voice services (STT/TTS) for the session."""
    validation = await triagem_service.validate_token(db, token)
    if not validation.get("valid"):
        raise HTTPException(status_code=404, detail="Token inválido")

    from app.domains.cv_screening.services.deepgram_service import deepgram_triagem_service
    from app.domains.cv_screening.services.voice_service import triagem_voice_service

    return JSONResponse(content={
        "stt_available": deepgram_triagem_service.is_available(),
        "tts_available": triagem_voice_service.is_available(),
    })
