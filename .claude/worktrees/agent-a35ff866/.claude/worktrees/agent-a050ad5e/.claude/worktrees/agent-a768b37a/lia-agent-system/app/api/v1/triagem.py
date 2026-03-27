from fastapi import APIRouter, HTTPException, Depends, Header, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
import logging

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
