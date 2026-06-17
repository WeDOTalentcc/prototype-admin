"""
Cultural Fit API — E2

GET /api/v1/candidates/{candidate_id}/cultural-fit?job_id=
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.shared.services.cultural_fit_integration_service import cultural_fit_service
from app.shared.tenant_guard import get_verified_company_id
from app.shared.security.require_company_id import require_company_id
from app.shared.errors import LIAError
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/candidates", tags=["cultural-fit"])


@router.get("/{candidate_id}/cultural-fit", response_model=None)
async def get_cultural_fit(
    candidate_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    job_id: str = Query(..., description="ID da vaga"),
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id)) -> dict:
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
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
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[cultural-fit] Erro: %s", exc)
        raise LIAError(message="Erro ao calcular fit cultural")

reorder_collection_before_item(router)
