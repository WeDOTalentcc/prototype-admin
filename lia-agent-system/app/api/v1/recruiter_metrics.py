"""
Recruiter Metrics API — Sprint 2A + 2D (Recruiter Intelligence + Benchmarking).

Endpoints:
  GET /api/v1/recruiter-metrics/{recruiter_id}            — resumo semanal
  GET /api/v1/recruiter-metrics/{recruiter_id}/backlog    — lista priorizada de candidatos aguardando
  GET /api/v1/recruiter-metrics/{recruiter_id}/benchmark  — comparação com mediana da empresa
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user_or_demo
from app.core.database import get_db
from app.shared.services.recruiter_metrics_service import recruiter_metrics_service
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match
from app.shared.errors import LIAError
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recruiter-metrics", tags=["recruiter-metrics"])


@router.get("/{recruiter_id}", response_model=None)
async def get_recruiter_summary(
    recruiter_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    company_id: str = Query(..., description="ID da empresa (multi-tenant)"),
    period_days: int = Query(30, ge=1, le=90, description="Período em dias para avg response time"),
    current_user=Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: public endpoint (metrics) — no tenant data
    """
    Retorna o resumo semanal de produtividade do recrutador:
    backlog_count, critical_count, most_urgent, avg_response_time_days,
    candidates_advanced_this_week, offers_pending.
    """
    try:
        summary = await recruiter_metrics_service.get_weekly_summary(
            recruiter_id=recruiter_id,
            company_id=company_id,
            db=db,
        )
        return {"success": True, "recruiter_id": recruiter_id, "data": summary}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"get_recruiter_summary failed: {e}", exc_info=True)
        raise LIAError(message="Erro ao calcular métricas do recrutador")


@router.get("/{recruiter_id}/backlog", response_model=None)
async def get_recruiter_backlog(
    recruiter_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    company_id: str = Query(..., description="ID da empresa (multi-tenant)"),
    current_user=Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: public endpoint (metrics) — no tenant data
    """
    Retorna a lista priorizada de candidatos aguardando ação do recrutador,
    ordenada por urgência (offer > entrevista > triagem).
    Apenas candidatos que já ultrapassaram o threshold da etapa.
    """
    try:
        backlog = await recruiter_metrics_service.get_action_backlog(
            recruiter_id=recruiter_id,
            company_id=company_id,
            db=db,
        )
        return {
            "success": True,
            "recruiter_id": recruiter_id,
            "total": len(backlog),
            "critical": sum(1 for b in backlog if b["is_critical"]),
            "data": backlog,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"get_recruiter_backlog failed: {e}", exc_info=True)
        raise LIAError(message="Erro ao buscar backlog do recrutador")


@router.get("/{recruiter_id}/benchmark", response_model=None)
async def get_recruiter_benchmark(
    recruiter_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    company_id: str = Query(..., description="ID da empresa (multi-tenant)"),
    current_user=Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: public endpoint (metrics) — no tenant data
    """
    Compara métricas do recrutador com a mediana anônima da empresa.
    Requer ≥ 2 recrutadores ativos na empresa para garantir privacidade.

    Retorna: personal metrics, benchmark (mediana), comparison por métrica,
    overall_performance (above_average | average | below_average).
    """
    try:
        result = await recruiter_metrics_service.get_recruiter_benchmark_comparison(
            recruiter_id=recruiter_id,
            company_id=company_id,
            db=db,
        )
        return {"success": True, **result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"get_recruiter_benchmark failed: {e}", exc_info=True)
        raise LIAError(message="Erro ao calcular benchmark do recrutador")

reorder_collection_before_item(router)
