"""
ML Feedback API — D6 (Feedback Loop Adaptativo)

POST /api/v1/ml-feedback/signal     — registra sinal de feedback
GET  /api/v1/ml-feedback/weights    — retorna pesos adaptativos por vaga

Requer X-Company-ID header.
"""
import logging
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.ml_feedback_service import FeedbackSignal, MLFeedbackService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ml-feedback", tags=["ml-feedback"])


def _require_company_id(
    x_company_id: str | None = Header(None, alias="X-Company-ID"),
) -> str:
    if not x_company_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-Company-ID header obrigatório",
        )
    try:
        UUID(x_company_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-Company-ID inválido — deve ser UUID",
        )
    return x_company_id


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class FeedbackSignalRequest(BaseModel):
    candidate_id: str
    job_id: str
    ai_score: float = Field(..., ge=0, le=100)
    recruiter_decision: Literal["hire", "reject", "override_approve", "override_reject"]
    recruiter_score: float | None = Field(None, ge=0, le=100)
    dimension_overrides: dict[str, float] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/signal", response_model=None)
async def record_feedback_signal(
    payload: FeedbackSignalRequest,
    company_id: str = Depends(_require_company_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Registra sinal de feedback de recrutador (D6 — ML Adaptativo).

    Usado após decisão de contratação/rejeição para alimentar o loop adaptativo
    de calibração de scores LIA.
    """
    service = MLFeedbackService()
    signal = FeedbackSignal(
        candidate_id=payload.candidate_id,
        job_id=payload.job_id,
        company_id=company_id,
        ai_score=payload.ai_score,
        recruiter_decision=payload.recruiter_decision,
        recruiter_score=payload.recruiter_score,
        dimension_overrides=payload.dimension_overrides,
    )
    ok = await service.record_signal(db, signal)
    return {"recorded": ok, "job_id": payload.job_id, "candidate_id": payload.candidate_id}


@router.get("/weights", response_model=None)
async def get_adaptive_weights(
    job_id: str = Query(..., description="ID da vaga"),
    company_id: str = Depends(_require_company_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Retorna pesos adaptativos calculados pelo feedback loop para uma vaga.

    Os pesos refletem padrões de aprovação/rejeição dos recrutadores nas últimas
    4 semanas. Pesos em [0.7, 1.3] — acima de 1.0 = dimensão mais importante
    que o baseline, abaixo = menos importante conforme feedback.
    """
    service = MLFeedbackService()
    try:
        weights = await service.get_weights_for_job(db, job_id, company_id)
        return weights.to_dict()
    except Exception as exc:
        logger.error("ml-feedback/weights erro: %s", exc)
        raise HTTPException(status_code=500, detail="Erro ao buscar pesos adaptativos")
