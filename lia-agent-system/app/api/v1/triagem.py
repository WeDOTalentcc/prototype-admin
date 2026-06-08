"""
Triagem REST endpoints (recrutador admin + candidato público).

AUTH MATRIX canonical (Sprint 4 B.1, 2026-05-23):

| Endpoint                                  | Auth          | Tenant resolution                |
|-------------------------------------------|---------------|----------------------------------|
| POST /api/v1/triagem/invite               | JWT obrigatório | company_id from JWT (REGRA 2)  |
| GET  /api/v1/triagem/{token}              | PUBLIC (token) | session.company_id              |
| POST /api/v1/triagem/{token}/message      | PUBLIC (token) | session.company_id              |
| GET  /api/v1/triagem/{token}/history      | PUBLIC (token) | session.company_id              |
| POST /api/v1/triagem/{token}/complete     | PUBLIC (token) | session.company_id              |
| POST /api/v1/triagem/{token}/request-call | PUBLIC (token) | session.company_id              |
| POST /api/v1/triagem/{token}/start        | PUBLIC (token) | session.company_id              |
| POST /api/v1/triagem/{token}/audio        | PUBLIC (token) | session.company_id              |
| POST /api/v1/triagem/{token}/tts          | PUBLIC (token) | session.company_id              |
| POST /api/v1/triagem/{token}/tts/{msg_id} | PUBLIC (token) | session.company_id              |
| GET  /api/v1/triagem/{token}/voice-status | PUBLIC (token) | session.company_id              |
| POST /api/v1/triagem/{token}/voip-start   | PUBLIC (token) | session.company_id              |

Por que candidato anônimo: candidato recebe link (email/WhatsApp) e abre sem
estar logado na plataforma. JWT só existe para recrutador interno.

Token canonical: UUID v4 gerado em create_session (uuid.uuid4(), 36 chars,
não-guessable). Validado em validate_token: 404 not_found / 410 expired /
409 already_completed.

Multi-tenancy (sem JWT mas com isolation):
- session.company_id é set em create_session a partir do JWT do recrutador
- TriagemRepository.get_session_by_token filtra por token único (não cross-tenant)
- Postgres RLS no nível de query (Task #1143) garante company_id correto
  setado em SET app.company_id quando services usam o session.company_id

Middleware: app/middleware/auth_enforcement.py — PUBLIC_REGEX_PATHS contém
regex para `/api/v1/triagem/{uuid-v4}(/{verb})?` (não matchea /invite nem
malformados).

Refs:
- AUDIT_CANDIDATE_CHAT_PUBLIC_2026-05-23.md (P0 production blocker descoberta)
- Sprint 4 B.1 (Paulo decisão 2026-05-23 — Replit canonical produção)
"""
import logging
import re
from typing import Any

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.domains.triagem.dependencies import get_triagem_repo
# P2 D (2026-05-23): canonical TriagemSessionRepository em domain recruitment.
# Re-export via domains.triagem.repositories.__init__ mantém backward compat.
from app.domains.recruitment.repositories.triagem_session_repository import (
    TriagemSessionRepository as TriagemRepository,
)
from app.domains.recruitment.services.triagem_session_service import (
    TriagemSessionService,
    get_triagem_service,
)
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/triagem", tags=["triagem"])


class SendMessageRequest(WeDoBaseModel):
    content: str
    message_type: str = "text"
    selected_option: str | None = None
    likert_value: int | None = None
    voice_mode: bool | None = None


class InviteRequest(WeDoBaseModel):
    candidate_id: str
    candidate_name: str | None = None
    candidate_email: str | None = None
    job_id: str
    job_title: str | None = None
    company_name: str | None = None
    company_logo_url: str | None = None
    invite_channel: str = "email"
    expires_days: int = 7
    voice_mode: bool = False


@router.get("/sessions", response_model=None)
async def get_eligibility_results_for_candidate_job(
    candidate_id: str = Query(..., description="Internal candidate ID"),
    job_id: str = Query(..., description="Job vacancy ID"),
    company_id: str = Depends(require_company_id),
):
    """Busca os resultados de elegibilidade da triagem mais recente de um candidato numa vaga.

    Usado pelo WSITextScreeningModal ao abrir para exibir a seção de elegibilidade
    mesmo quando o payload do kanban não inclui esse campo.

    Retorna lista vazia quando não há sessão ou quando a fase de elegibilidade não foi
    iniciada (vaga sem perguntas eliminatórias). Nunca lança 4xx/5xx por ausência de dados
    — o cliente faz fallback silencioso.

    Tenant guard: queries diretas com company_id no WHERE (triagem_sessions não tem RLS
    clássico — defesa app-layer, igual ao /wsi/sessions endpoint, Onda 4.2c-P0).
    """
    from sqlalchemy import select, desc, and_
    from app.core.database import AsyncSessionLocal
    from lia_models.triagem import TriagemSession, TriagemMessage

    try:
        async with AsyncSessionLocal() as _db:
            result = await _db.execute(
                select(TriagemSession)
                .where(
                    TriagemSession.candidate_id == candidate_id,
                    TriagemSession.job_id == job_id,
                    TriagemSession.company_id == company_id,
                )
                .order_by(desc(TriagemSession.created_at))
                .limit(1)
            )
            session = result.scalar_one_or_none()

            if not session:
                return {"eligibility_results": [], "session_status": None}

            elig = (session.metadata_json or {}).get("eligibility") or {}
            items = _extract_eligibility_items(elig)

            # Busca as respostas verbatim do candidato na fase de elegibilidade.
            # A elegibilidade é SEMPRE a primeira fase da triagem, portanto as
            # primeiras N mensagens do candidato (ordered by created_at) correspondem
            # às N perguntas de elegibilidade na mesma ordem.
            if items:
                msgs_result = await _db.execute(
                    select(TriagemMessage)
                    .where(
                        and_(
                            TriagemMessage.session_id == session.id,
                            TriagemMessage.sender == "candidate",
                        )
                    )
                    .order_by(TriagemMessage.created_at)
                    .limit(len(items))
                )
                candidate_msgs = list(msgs_result.scalars().all())
                for i, item in enumerate(items):
                    if i < len(candidate_msgs):
                        item["answer"] = candidate_msgs[i].content

        return {
            "eligibility_results": items,
            "session_status": session.status,
            "session_id": str(session.id),
        }
    except Exception as exc:
        logger.warning("[triagem/sessions] Failed to fetch eligibility results: %s", exc)
        return {"eligibility_results": [], "session_status": None}


def _extract_eligibility_items(elig: dict) -> list[dict]:
    """Reconstrói resultados por-pergunta a partir do snapshot de elegibilidade na session.

    Regra de pass/fail baseada em eligibility_phase.py:
    - phase == 'complete': todas passaram (index >= len(questions))
    - phase == 'talent_pool': questions[0..index-1] passaram; questions[index] falhou
    - outros (asking/reconsidering/confirming): mostra o que já foi processado
    """
    questions = elig.get("questions") or []
    phase = elig.get("phase", "asking")
    idx = int(elig.get("index") or 0)

    results = []
    for i, q in enumerate(questions):
        if phase == "complete":
            passed = True
        elif phase == "talent_pool":
            passed = i < idx
        else:
            passed = i < idx

        results.append({
            "id": str(q.get("id") or i),
            "question": q.get("question") or q.get("question_text") or "",
            "passed": passed,
            "is_eliminatory": bool(q.get("is_eliminatory", True)),
        })

    return results


@router.get("/{token}", response_model=None)
async def get_triagem_session(
    token: str,
    repo: TriagemRepository = Depends(get_triagem_repo),
    triagem_svc: TriagemSessionService = Depends(get_triagem_service),
):
    # multi-tenancy: tenant resolved via session.company_id (set at invite time by
    # authenticated recruiter). Token = UUID v4 in URL is the auth credential. (B.1 2026-05-23)
    config = await triagem_svc.get_session_config(repo.db, token)

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


@router.post("/{token}/message", response_model=None)
async def send_message(
    token: str,
    request: SendMessageRequest,
    repo: TriagemRepository = Depends(get_triagem_repo),
    triagem_svc: TriagemSessionService = Depends(get_triagem_service),
):
    # multi-tenancy: tenant resolved via session.company_id (set at invite time by
    # authenticated recruiter). Token = UUID v4 in URL is the auth credential. (B.1 2026-05-23)
    validation = await triagem_svc.validate_token(repo.db, token)

    if not validation.get("valid"):
        error = validation.get("error")
        if error == "not_found":
            raise HTTPException(status_code=404, detail="Token inválido")
        if error == "expired":
            raise HTTPException(status_code=410, detail="Link expirado")

    if validation.get("completed"):
        raise HTTPException(status_code=409, detail="Triagem já foi concluída")

    result = await triagem_svc.process_message(
        repo.db, token, request.content, request.message_type,
        voice_mode=request.voice_mode,
    )

    if result.get("error") == "not_found":
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    if result.get("error") == "already_completed":
        raise HTTPException(status_code=409, detail="Triagem já foi concluída")

    return JSONResponse(content=result)


@router.get("/{token}/history", response_model=None)
async def get_history(
    token: str,
    repo: TriagemRepository = Depends(get_triagem_repo),
    triagem_svc: TriagemSessionService = Depends(get_triagem_service),
):
    # multi-tenancy: tenant resolved via session.company_id (set at invite time by
    # authenticated recruiter). Token = UUID v4 in URL is the auth credential. (B.1 2026-05-23)
    result = await triagem_svc.get_history(repo.db, token)

    if result.get("error") == "not_found":
        raise HTTPException(status_code=404, detail="Token inválido ou sessão não encontrada")

    return JSONResponse(content=result)


@router.post("/{token}/complete", response_model=None)
async def complete_triagem(
    token: str,
    repo: TriagemRepository = Depends(get_triagem_repo),
    triagem_svc: TriagemSessionService = Depends(get_triagem_service),
):
    # multi-tenancy: tenant resolved via session.company_id (set at invite time by
    # authenticated recruiter). Token = UUID v4 in URL is the auth credential. (B.1 2026-05-23)
    validation = await triagem_svc.validate_token(repo.db, token)

    if not validation.get("valid"):
        error = validation.get("error")
        if error == "not_found":
            raise HTTPException(status_code=404, detail="Token inválido")
        if error == "expired":
            raise HTTPException(status_code=410, detail="Link expirado")

    if validation.get("completed"):
        raise HTTPException(status_code=409, detail="Triagem já foi concluída anteriormente")

    result = await triagem_svc.complete_session(repo.db, token)

    if result.get("error") == "not_found":
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    if result.get("error") == "already_completed":
        return JSONResponse(
            status_code=409,
            content={"detail": "Triagem já concluída", "session": result.get("session")},
        )

    return JSONResponse(content=result)


@router.post("/invite", status_code=201, response_model=None)
async def create_invite(
    request: InviteRequest,
    repo: TriagemRepository = Depends(get_triagem_repo),
    x_user_id: str | None = Header(None, alias="X-User-ID"),
    triagem_svc: TriagemSessionService = Depends(get_triagem_service),
    company_id: str = Depends(require_company_id),
):
    # multi-tenancy: company_id from JWT (R4 canonical). request.company_id and
    # X-Company-ID header are NOT trusted — JWT is authoritative.

    session = await triagem_svc.create_session(
        db=repo.db,
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
        f"[Triagem] Invite created: job={request.job_title}, channel={request.invite_channel}"
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


class RequestCallRequest(WeDoBaseModel):
    candidate_phone: str

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


@router.post("/{token}/request-call", response_model=None)
async def request_phone_call(
    token: str,
    request: RequestCallRequest,
    repo: TriagemRepository = Depends(get_triagem_repo),
    triagem_svc: TriagemSessionService = Depends(get_triagem_service),
):
    # multi-tenancy: tenant resolved via session.company_id (set at invite time by
    # authenticated recruiter). Token = UUID v4 in URL is the auth credential. (B.1 2026-05-23)
    """Request an automated phone call from LIA to the candidate via Twilio Voice."""
    validation = await triagem_svc.validate_token(repo.db, token)

    if not validation.get("valid"):
        error = validation.get("error")
        if error == "not_found":
            raise HTTPException(status_code=404, detail="Token inválido")
        if error == "expired":
            raise HTTPException(status_code=410, detail="Link expirado")

    if validation.get("completed"):
        raise HTTPException(status_code=409, detail="Triagem já foi concluída")

    result = await triagem_svc.request_phone_call(
        repo.db, token, request.candidate_phone
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


class StartSessionRequest(WeDoBaseModel):
    voice_mode: bool | None = None


@router.post("/{token}/start", response_model=None)
async def start_triagem(
    token: str,
    request: StartSessionRequest | None = None,
    repo: TriagemRepository = Depends(get_triagem_repo),
    triagem_svc: TriagemSessionService = Depends(get_triagem_service),
):
    # multi-tenancy: tenant resolved via session.company_id (set at invite time by
    # authenticated recruiter). Token = UUID v4 in URL is the auth credential. (B.1 2026-05-23)
    validation = await triagem_svc.validate_token(repo.db, token)

    if not validation.get("valid"):
        error = validation.get("error")
        if error == "not_found":
            raise HTTPException(status_code=404, detail="Token inválido")
        if error == "expired":
            raise HTTPException(status_code=410, detail="Link expirado")

    if validation.get("completed"):
        raise HTTPException(status_code=409, detail="Triagem já foi concluída")

    vm = request.voice_mode if request else None
    result = await triagem_svc.start_session(repo.db, token, voice_mode=vm)

    if result.get("error") == "not_found":
        raise HTTPException(status_code=404, detail="Sessão não encontrada")

    return JSONResponse(content=result)


@router.post("/{token}/audio", response_model=None)
async def transcribe_audio(
    token: str,
    audio: UploadFile = File(...),
    question_index: int | None = Form(None),
    repo: TriagemRepository = Depends(get_triagem_repo),
    triagem_svc: TriagemSessionService = Depends(get_triagem_service),
):
    # multi-tenancy: tenant resolved via session.company_id (set at invite time by
    # authenticated recruiter). Token = UUID v4 in URL is the auth credential. (B.1 2026-05-23)
    """Transcribe candidate audio using OpenAI Whisper STT."""
    validation = await triagem_svc.validate_token(repo.db, token)
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

    from app.shared.services.voice_service import voice_service

    try:
        transcription = await voice_service.transcribe_audio(
            audio_data=audio_data,
            language="pt-BR",
            filename=audio.filename,
        )
        result = {
            "text": transcription.get("text", ""),
            "confidence": transcription.get("confidence", 0.0),
            "duration_seconds": transcription.get("duration", 0.0),
            "session_token": token,
            "question_index": question_index,
        }
    except Exception as e:
        result = {"text": "", "error": str(e)}

    if result.get("error") and not result.get("text"):
        raise HTTPException(status_code=502, detail=f"Falha na transcrição: {result['error']}")

    return JSONResponse(content=result)


class TTSRequest(WeDoBaseModel):
    text: str
    voice: str = "nova"
    speed: float = 1.0
    question_index: int | None = None


@router.post("/{token}/tts", response_model=None)
async def synthesize_speech(
    token: str,
    request: TTSRequest,
    repo: TriagemRepository = Depends(get_triagem_repo),
    triagem_svc: TriagemSessionService = Depends(get_triagem_service),
):
    # multi-tenancy: tenant resolved via session.company_id (set at invite time by
    # authenticated recruiter). Token = UUID v4 in URL is the auth credential. (B.1 2026-05-23)
    """Generate TTS audio for a triagem question using OpenAI TTS."""
    validation = await triagem_svc.validate_token(repo.db, token)
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


@router.post("/{token}/tts/{message_id}", response_model=None)
async def synthesize_message_speech(
    token: str,
    message_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    repo: TriagemRepository = Depends(get_triagem_repo),
    triagem_svc: TriagemSessionService = Depends(get_triagem_service),
):
    # multi-tenancy: tenant resolved via session.company_id (set at invite time by
    # authenticated recruiter). Token = UUID v4 in URL is the auth credential. (B.1 2026-05-23)
    """Generate TTS audio on demand for a specific LIA message."""
    validation = await triagem_svc.validate_token(repo.db, token)
    if not validation.get("valid"):
        error = validation.get("error")
        if error == "not_found":
            raise HTTPException(status_code=404, detail="Token inválido")
        if error == "expired":
            raise HTTPException(status_code=410, detail="Link expirado")

    result = await triagem_svc.generate_tts_for_message(repo.db, token, message_id)

    if result.get("error") == "not_found":
        raise HTTPException(status_code=404, detail="Mensagem não encontrada")
    if result.get("error") == "not_lia_message":
        raise HTTPException(status_code=400, detail="TTS disponível apenas para mensagens da LIA")
    if result.get("error") == "tts_failed":
        raise HTTPException(status_code=502, detail="Falha na geração de áudio")

    return JSONResponse(content=result)


@router.get("/{token}/voice-status", response_model=None)
async def voice_status(
    token: str,
    repo: TriagemRepository = Depends(get_triagem_repo),
    triagem_svc: TriagemSessionService = Depends(get_triagem_service),
):
    # multi-tenancy: tenant resolved via session.company_id (set at invite time by
    # authenticated recruiter). Token = UUID v4 in URL is the auth credential. (B.1 2026-05-23)
    """Check availability of voice services (STT/TTS) for the session."""
    validation = await triagem_svc.validate_token(repo.db, token)
    if not validation.get("valid"):
        raise HTTPException(status_code=404, detail="Token inválido")

    from app.domains.cv_screening.services.voice_service import triagem_voice_service
    from app.shared.services.voice_service import voice_service

    availability = voice_service.is_available()
    return JSONResponse(content={
        "stt_available": availability.get("any_transcription", False),
        "tts_available": triagem_voice_service.is_available(),
    })


@router.post("/{token}/voip-start", response_model=None)
async def voip_start(
    token: str,
    repo: TriagemRepository = Depends(get_triagem_repo),
    triagem_svc: TriagemSessionService = Depends(get_triagem_service),
):
    # multi-tenancy: tenant resolved via session.company_id (set at invite time by
    # authenticated recruiter). Token = UUID v4 in URL is the auth credential. (B.1 2026-05-23)
    """
    Initiate a VoIP (browser call) screening session.

    Provider strategy:
    1. Gemini Live Audio (preferred) — single WebSocket, ~$0.065/interview
    2. Twilio pipeline (PSTN fallback) — if Gemini Live unavailable

    The browser connects via WebSocket to /gemini-voice/live-stream for Gemini Live,
    or falls back to the Twilio Voice SDK pipeline.

    Returns:
        - success: Whether a session was created
        - session_id: Voice screening session ID
        - gemini_available: True when Gemini Live Audio is the provider
        - voice_provider: "gemini_live" | "twilio" | "unavailable"
        - voip_available: Backward-compat flag (True when any provider is ready)
    """
    from app.domains.voice.services.voice_screening_orchestrator import (
        voice_screening_orchestrator,
    )

    validation = await triagem_svc.validate_token(repo.db, token)
    if not validation.get("valid"):
        error = validation.get("error")
        if error == "not_found":
            raise HTTPException(status_code=404, detail="Token inválido")
        if error == "expired":
            raise HTTPException(status_code=410, detail="Link expirado")

    if validation.get("completed"):
        raise HTTPException(status_code=409, detail="Triagem já foi concluída")

    session_data = validation.get("session") or {}
    if not session_data:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")

    candidate_id = str(session_data.get("candidate_id") or "")
    candidate_name = str(session_data.get("candidate_name") or "Candidato")
    job_title = str(session_data.get("job_title") or "a vaga")
    company_id = str(session_data.get("company_id") or "")
    job_id = str(session_data.get("job_id") or "")

    voip_session = await voice_screening_orchestrator.initiate_voip_session(
        candidate_id=candidate_id,
        candidate_name=candidate_name,
        job_title=job_title,
        company_id=company_id,
        job_id=job_id,
        language="pt-BR",
        db=repo.db,
    )

    if voip_session.status == "ready" and voip_session.voice_provider == "gemini_live":
        import asyncio as _asyncio

        async def _cleanup_abandoned_voip_session(sid: str, delay: int = 7200) -> None:
            await _asyncio.sleep(delay)
            orphan = voice_screening_orchestrator._sessions.get(sid)
            if orphan and orphan.status in ("pending", "ready"):
                logger.info("[Triagem VoIP] Cleaning up abandoned VoIP session=%s", sid)
                voice_screening_orchestrator._sessions.pop(sid, None)

        _asyncio.create_task(_cleanup_abandoned_voip_session(voip_session.session_id))

        logger.info(
            "[Triagem VoIP] Gemini Live session created: session=%s candidate=%s",
            voip_session.session_id,
            candidate_id,
        )

        from app.api.v1.gemini_voice import _generate_ws_token
        ws_token = _generate_ws_token(
            voip_session.session_id, company_id, candidate_id,
        )

        return JSONResponse(content={
            "success": True,
            "voip_available": True,
            "session_id": voip_session.session_id,
            "gemini_available": True,
            "voice_provider": "gemini_live",
            "ws_token": ws_token,
            "message": "Sessão de voz Gemini Live criada. Conecte via WebSocket.",
        })

    logger.info(
        "[Triagem VoIP] Gemini Live unavailable (status=%s) for token=%s — falling back to chat (Twilio is PSTN-only)",
        voip_session.status,
        token,
    )

    return JSONResponse(content={
        "success": False,
        "voip_available": False,
        "session_id": "",
        "gemini_available": False,
        "voice_provider": "unavailable",
        "fallback_channel": "chat",
        "message": "Chamada de voz temporariamente indisponível. Use o chat de texto para continuar a triagem.",
    })

reorder_collection_before_item(router)
