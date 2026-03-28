"""
Cultural Fit API — E2

GET /api/v1/candidates/{candidate_id}/cultural-fit?job_id=
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.cultural_fit_integration_service import cultural_fit_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/candidates", tags=["cultural-fit"])


def _require_company_id(
    x_company_id: Optional[str] = Header(None, alias="X-Company-ID"),
) -> str:
    if not x_company_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="X-Company-ID obrigatório")
    return x_company_id


@router.get("/{candidate_id}/cultural-fit")
async def get_cultural_fit(
    candidate_id: str,
    job_id: str = Query(..., description="ID da vaga"),
    company_id: str = Depends(_require_company_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Retorna score de fit cultural integrado (WSI + entrevista + cultura empresa).
    Score em [0–100]. Fail-open: retorna 50.0 em caso de dados insuficientes.
    """
    try:
        result = await cultural_fit_service.compute_integrated_fit(
            candidate_id=candidate_id,
            job_id=job_id,
            company_id=company_id,
            db=db,
        )
        return result.to_dict()
    except Exception as exc:
        logger.error("[cultural-fit] Erro: %s", exc)
        raise HTTPException(status_code=500, detail="Erro ao calcular fit cultural")
