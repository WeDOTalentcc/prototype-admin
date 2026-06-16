"""
Early Warning API — Sprint 2B.

GET /api/v1/early-warning?company_id=<uuid>&min_risk_level=medium
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user_or_demo
from app.core.database import get_db
from app.shared.services.early_warning_service import early_warning_service
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match
from app.shared.errors import LIAError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/early-warning", tags=["early-warning"])


@router.get("", response_model=None)
async def get_early_warning(
    company_id: str = Query(..., description="ID da empresa (multi-tenant)"),
    min_risk_level: str = Query(
        "medium",
        description="Nível mínimo de risco: medium | high | critical",
        pattern="^(medium|high|critical)$",
    ),
    current_user=Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Retorna candidatos em risco de desengajamento ordenados por EWS score.
    Inclui resumo por nível de risco e top candidatos críticos.
    """
    try:
        summary = await early_warning_service.get_summary_by_risk_level(
            company_id=company_id,
            db=db,
        )
        candidates = await early_warning_service.get_at_risk_candidates(
            company_id=company_id,
            min_risk_level=min_risk_level,
            db=db,
        )
        return {
            "success": True,
            "company_id": company_id,
            "min_risk_level": min_risk_level,
            "summary": summary,
            "data": candidates,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"get_early_warning failed: {e}", exc_info=True)
        raise LIAError(message="Erro ao calcular Early Warning Score")
