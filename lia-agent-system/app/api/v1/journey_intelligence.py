"""
Journey Intelligence API — Sprint 2C.

GET /api/v1/journey/metrics?vacancy_id=<uuid>&company_id=<uuid>
GET /api/v1/journey/company-overview?company_id=<uuid>
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user_or_demo
from app.core.database import get_db
from app.shared.services.journey_intelligence_service import journey_intelligence_service
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match
from app.shared.errors import LIAError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/journey", tags=["journey-intelligence"])


@router.get("/metrics", response_model=None)
async def get_journey_metrics(
    vacancy_id: str = Query(..., description="ID da vaga"),
    company_id: str = Query(..., description="ID da empresa (multi-tenant)"),
    current_user=Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: public endpoint (metrics) — no tenant data
    """
    Retorna métricas detalhadas do funil de uma vaga:
    conversão por etapa, drop-off, health score e padrões de risco preditivos.
    """
    try:
        result = await journey_intelligence_service.get_vacancy_metrics(
            vacancy_id=vacancy_id,
            company_id=company_id,
            db=db,
        )
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error", "Vaga não encontrada"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"get_journey_metrics failed: {e}", exc_info=True)
        raise LIAError(message="Erro ao calcular métricas de jornada")


@router.get("/company-overview", response_model=None)
async def get_company_overview(
    company_id: str = Query(..., description="ID da empresa (multi-tenant)"),
    current_user=Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Visão geral da saúde de pipeline por vaga ativa da empresa.
    Vagas ordenadas por health_score ASC (piores primeiro).
    Inclui contagem de vagas em estado critical/warning/healthy.
    """
    try:
        result = await journey_intelligence_service.get_company_overview(
            company_id=company_id,
            db=db,
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"get_company_overview failed: {e}", exc_info=True)
        raise LIAError(message="Erro ao calcular visão geral de jornada")
