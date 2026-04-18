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

from app.core.database import get_db
from app.domains.cv_screening.services.wsi_async_session_service import WSIAsyncSessionService, get_wsi_async_session_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/wsi/async", tags=["wsi-async"])


class AnswerRequest(BaseModel):
    answer: str


# NOTE: o endpoint POST /wsi/async/invite foi REMOVIDO em 2026-04-18 (audit P1-5,
# Phase 2). Era duplicado de /api/v1/communication/send-screening-invite, que é o
# canônico — único usado pelo frontend (wsi-triagem-invite-modal.tsx) e pelo
# proxy /api/backend-proxy/communication/send-screening-invite. Manter dois
# endpoints com mesmo propósito mas semânticas levemente diferentes mantinha
# ambiguidade para integrações externas (recrutadores via curl, ATS).
# A criação de sessão WSI async agora é responsabilidade exclusiva de
# CommunicationService.send_screening_invite quando o canal é 'chat'/'whatsapp'.
# O hook frontend useWsiAsync continua funcionando (consome /{token}, /{token}/answer,
# /{token}/complete) — apenas o convite mudou de origem.


@router.get("/{token}", response_model=None)
async def get_session_state(
    token: str,
    db: AsyncSession = Depends(get_db),
    svc: WSIAsyncSessionService = Depends(get_wsi_async_session_service),
) -> dict:
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
) -> dict:
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
    db: AsyncSession = Depends(get_db),
    svc: WSIAsyncSessionService = Depends(get_wsi_async_session_service),
) -> dict:
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
            _r = redis.from_url(settings.REDIS_URL)
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
