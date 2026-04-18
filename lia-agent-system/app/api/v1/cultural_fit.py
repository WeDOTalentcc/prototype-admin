"""
Cultural Fit API — E2

GET /api/v1/candidates/{candidate_id}/cultural-fit?job_id=
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN
from app.core.database import get_db
from app.shared.services.cultural_fit_integration_service import cultural_fit_service
from app.shared.tenant_guard import get_verified_company_id

# Task #489 — UUID-or-digit constraint for dual-ID path params,
# preventing static sibling routes from being shadowed by
# item handlers (Task #455-class bug).
_DualId = Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)]

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/candidates", tags=["cultural-fit"])


@router.get("/{candidate_id}/cultural-fit", response_model=None)
async def get_cultural_fit(
    candidate_id: _DualId,
    job_id: str = Query(..., description="ID da vaga"),
    company_id: str = Depends(get_verified_company_id),
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

# Task #489 — Keep collection-scoped routes ahead of item-scoped
# routes so a static sibling segment cannot be silently shadowed
# by an {*_id} handler (the Task #455 routing-shadowing bug).
from app.api.v1._path_patterns import reorder_collection_before_item as _reorder_collection_before_item  # noqa: E402

_reorder_collection_before_item(router)
