"""
Candidate Compare API — D9 (Análise Comparativa Visual)

POST /api/v1/candidates/compare — compara 2-4 candidatos lado a lado.
Delega para CandidateComparisonService que calcula scores por dimensão.

Requer X-Company-ID header para isolamento multi-tenant.
"""
import logging
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.candidates.services.candidate_comparison_service import CandidateComparisonService
from app.domains.candidates.services.candidate_comparison_service import get_candidate_comparison_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/candidates", tags=["candidate-compare"])


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


class CompareRequest(BaseModel):
    candidate_ids: list[str] = Field(..., min_length=2, max_length=4)
    job_id: str | None = None
    scenario: Literal["A", "B", "C"] | None = None


@router.post("/compare", response_model=None)
async def compare_candidates(
    payload: CompareRequest,
    company_id: str = Depends(_require_company_id),
    db: AsyncSession = Depends(get_db),
    service: CandidateComparisonService = Depends(get_candidate_comparison_service),
) -> dict:
    """
    Compara 2 a 4 candidatos lado a lado (D9 — Análise Comparativa Visual).

    Retorna scores por dimensão, candidato vencedor e análise.
    Delega para CandidateComparisonService (cenários A, B, C baseados em dados disponíveis).

    Returns 200 com resultado da comparação.
    """
    try:
        result = await service.compare_candidates(
            db=db,
            candidate_ids=payload.candidate_ids,
            job_id=payload.job_id,
            force_scenario=payload.scenario,
        )
        return result
    except Exception as exc:
        logger.error("candidates/compare erro: %s", exc)
        raise HTTPException(
            status_code=500,
            detail="Erro ao comparar candidatos",
        )
