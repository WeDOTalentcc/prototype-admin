"""
Pipeline Velocity API — Sprint 1B.

Expõe métricas de velocidade de pipeline baseadas em stage_entered_at
para o frontend e para integração com o agente Kanban.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.core.database import get_db
from app.shared.services.pipeline_velocity_service import pipeline_velocity_service
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pipeline/velocity", tags=["pipeline-velocity"])


@router.get("", response_model=None)
async def get_pipeline_velocity(
    vacancy_id: str | None = Query(None, description="ID da vaga (omitir para visão empresa)"),
    company_id: str | None = Query(None, description="ID da empresa (opcional)"),
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Retorna métricas de velocidade por etapa do pipeline.

    Usa o campo `stage_entered_at` (migration 023) para calcular tempo
    preciso em cada etapa. Identifica gargalos e saúde geral do pipeline.

    Resposta por etapa:
    - `avg_days`: média de dias na etapa
    - `median_days`: mediana (menos sensível a outliers)
    - `max_days`: candidato mais atrasado
    - `candidate_count`: candidatos ativos na etapa
    - `threshold_days`: limite recomendado para essa etapa
    - `is_bottleneck`: etapa acima do limite
    """
    effective_company_id = company_id or getattr(current_user, "company_id", None)

    try:
        metrics = await pipeline_velocity_service.get_velocity_metrics(
            vacancy_id=vacancy_id,
            company_id=effective_company_id,
            db=db,
        )
        return {
            "success": True,
            "data": metrics,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"pipeline_velocity endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro ao calcular métricas de velocidade")


@router.get("/bottlenecks", response_model=None)
async def get_velocity_bottlenecks(
    company_id: str | None = Query(None),
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Lista candidatos atualmente acima do limite de tempo em sua etapa.

    Usado para exibir alertas proativos no dashboard do recrutador.
    """
    effective_company_id = company_id or getattr(current_user, "company_id", None)
    if not effective_company_id:
        raise HTTPException(status_code=400, detail="company_id é obrigatório")

    try:
        bottlenecked = await pipeline_velocity_service.get_bottlenecked_candidates(
            company_id=effective_company_id,
            db=db,
        )
        return {
            "success": True,
            "total": len(bottlenecked),
            "data": bottlenecked,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"velocity_bottlenecks endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro ao buscar candidatos em gargalo")
