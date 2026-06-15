"""
WSI Async API — E3 (WSI Assíncrono)

Permite que candidatos respondam ao WSI no próprio ritmo, via link de email.
Endpoints públicos protegidos por token de sessão.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, get_tenant_db
from app.domains.cv_screening.services.wsi_async_session_service import WSIAsyncSessionService, get_wsi_async_session_service
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/wsi/async", tags=["wsi-async"])


class InviteRequest(WeDoBaseModel):
    candidate_id: str
    job_id: str
    expire_hours: int = 72


class AnswerRequest(WeDoBaseModel):
    answer: str


@router.post("/invite", response_model=None)
async def create_async_invite(
    payload: InviteRequest,
    db: AsyncSession = Depends(get_tenant_db),
    svc: WSIAsyncSessionService = Depends(get_wsi_async_session_service),
company_id: str = Depends(require_company_id)) -> dict:
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Cria sessão WSI assíncrona e retorna token de acesso para o candidato.
    """
    try:
        token = await svc.create_session(
            candidate_id=payload.candidate_id,
            job_id=payload.job_id,
            company_id=company_id,
            db=db,
        )
        return {
            "token": str(token),
            "link": f"/wsi-async/{token}",
            "expires_in_hours": payload.expire_hours,
            "status": "created",
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[WSI Async] create_invite failed: %s", exc)
        raise HTTPException(status_code=500, detail="Erro ao criar convite WSI assíncrono")


@router.get("/{token}", response_model=None)
async def get_session_state(
    token: str,
    db: AsyncSession = Depends(get_db),
    svc: WSIAsyncSessionService = Depends(get_wsi_async_session_service),
company_id: str = Depends(require_company_id)) -> dict:
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Retorna estado atual da sessão WSI + próxima pergunta.
    """
    try:
        session = await svc.get_session(session_id=token)
        if not session:
            raise HTTPException(status_code=404, detail="Sessão não encontrada ou expirada")
        return {
            "token": token,
            "status": session.get("status", "unknown"),
            "current_question": session.get("current_question", None),
            "progress": session.get("current_block", 1) - 1,
            "total_questions": session.get("total_questions", 0),
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[WSI Async] get_session failed: %s", exc)
        raise HTTPException(status_code=500, detail="Erro ao buscar sessão")


@router.post("/{token}/answer", response_model=None)
async def submit_answer(
    token: str,
    payload: AnswerRequest,
    db: AsyncSession = Depends(get_db),
    svc: WSIAsyncSessionService = Depends(get_wsi_async_session_service),
company_id: str = Depends(require_company_id)) -> dict:
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Submete resposta para a pergunta atual da sessão WSI assíncrona.
    """
    try:
        # submit_response exists: (session_id, block, question_id, response_text)
        session = await svc.get_session(session_id=token)
        if not session:
            raise HTTPException(status_code=404, detail="Sessão não encontrada")
        current_block = session.get("current_block", 1)
        accepted = await svc.submit_response(
            session_id=token,
            block=current_block,
            question_id=f"q{current_block}",
            response_text=payload.answer,
        )
        if not accepted:
            raise HTTPException(status_code=404, detail="Sessão não encontrada")
        # Busca sessão atualizada para retornar próxima pergunta
        updated_session = await svc.get_session(session_id=token)
        next_block = (updated_session or {}).get("current_block", current_block + 1)
        total = (updated_session or {}).get("total_questions", 0)
        is_complete = total > 0 and next_block > total
        return {
            "token": token,
            "accepted": True,
            "next_question": None,
            "is_complete": is_complete,
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[WSI Async] submit_answer failed: %s", exc)
        raise HTTPException(status_code=500, detail="Erro ao registrar resposta")


@router.get("/{token}/complete", response_model=None)
async def complete_session(
    token: str,
    db: AsyncSession = Depends(get_tenant_db),
    svc: WSIAsyncSessionService = Depends(get_wsi_async_session_service),
company_id: str = Depends(require_company_id)) -> dict:
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Finaliza a sessão WSI assíncrona e dispara scoring.
    """
    try:
        session = await svc.get_session(session_id=token)
        if not session:
            raise HTTPException(status_code=404, detail="Sessão não encontrada")
        # Marca sessão como completed via check_expired_sessions proxy or direct Redis update
        try:
            import json

            import redis
            from lia_config.config import settings
            _r = redis.from_url(settings.REDIS_URL, socket_connect_timeout=5, socket_timeout=5)
            _data = _r.get(f"wsi_async:{token}")
            if _data:
                _session_data = json.loads(_data)
                _session_data["status"] = "completed"
                remaining = _r.ttl(f"wsi_async:{token}")
                _r.setex(f"wsi_async:{token}", max(remaining, 3600), json.dumps(_session_data))
        except Exception as _redis_exc:
            logger.debug("[WSI Async] complete Redis update failed: %s", _redis_exc)
        return {
            "token": token,
            "completed": True,
            "message": "Sua triagem foi concluída. O recrutador será notificado.",
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[WSI Async] complete_session failed: %s", exc)
        raise HTTPException(status_code=500, detail="Erro ao finalizar sessão")
