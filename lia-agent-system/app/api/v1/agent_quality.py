"""
Agent Quality API — Sprint J1

Endpoint para trend analysis de qualidade de agentes.
Dados persistidos por AgentQualityEvaluator (shadow mode).

Endpoints:
  GET /agent-quality       — trend agregado por agent_id (últimos N dias)
  GET /agent-quality/{id}  — detalhe de uma avaliação
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.agent_quality_evaluation import AgentQualityEvaluation
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent-quality", tags=["agent-quality"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class AgentQualityTrend(BaseModel):
    agent_id: str
    company_id: str
    days: int
    samples_count: int
    avg_score: float
    avg_scores_by_metric: dict[str, float]
    trend: str  # "improving" | "stable" | "degrading" | "insufficient_data"


class AgentQualityDetail(BaseModel):
    id: str
    agent_id: str
    company_id: str
    session_id: str | None
    overall_score: float
    scores: dict[str, Any]
    evaluated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("", response_model=list[AgentQualityTrend])
# TODO(phase2): extract to repository — agent quality metrics
async def list_agent_quality_trends(
    company_id: str = Query(..., description="ID do tenant"),
    agent_id: str | None = Query(None, description="Filtrar por agente específico"),
    days: int = Query(30, ge=1, le=365, description="Janela de análise em dias"),
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Retorna trend de qualidade por agente nos últimos N dias.
    Agrega avg_score + scores por métrica + classificação de trend.
    """
    since = datetime.utcnow() - timedelta(days=days)

    stmt = select(AgentQualityEvaluation).where(
        AgentQualityEvaluation.company_id == company_id,
        AgentQualityEvaluation.evaluated_at >= since,
    )
    if agent_id:
        stmt = stmt.where(AgentQualityEvaluation.agent_id == agent_id)

    result = await db.execute(stmt.order_by(AgentQualityEvaluation.evaluated_at))
    rows = result.scalars().all()

    # Agrupar por agent_id
    groups: dict[str, list[AgentQualityEvaluation]] = {}
    for row in rows:
        groups.setdefault(row.agent_id, []).append(row)

    trends = []
    for aid, evaluations in groups.items():
        avg_score = sum(e.overall_score for e in evaluations) / len(evaluations)
        metric_sums: dict[str, float] = {}
        for e in evaluations:
            for metric, score in (e.scores or {}).items():
                metric_sums[metric] = metric_sums.get(metric, 0.0) + score
        avg_by_metric = {
            m: s / len(evaluations) for m, s in metric_sums.items()
        }
        trend = _classify_trend(evaluations)
        trends.append(AgentQualityTrend(
            agent_id=aid,
            company_id=company_id,
            days=days,
            samples_count=len(evaluations),
            avg_score=round(avg_score, 3),
            avg_scores_by_metric={m: round(v, 3) for m, v in avg_by_metric.items()},
            trend=trend,
        ))

    return trends


@router.get("/{evaluation_id}", response_model=AgentQualityDetail)
async def get_evaluation_detail(
    evaluation_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(require_company_id),
):
    """Retorna detalhe de uma avaliação específica pelo ID.

    Multi-tenancy fail-closed (REGRA ZERO): scopes by company_id from JWT
    so we cannot leak another tenant's evaluation detail.
    """
    stmt = select(AgentQualityEvaluation).where(
        AgentQualityEvaluation.id == evaluation_id,
        AgentQualityEvaluation.company_id == company_id,
    )
    result = await db.execute(stmt)
    ev = result.scalar_one_or_none()
    if not ev:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Avaliação {evaluation_id} não encontrada")
    return AgentQualityDetail(
        id=str(ev.id),
        agent_id=ev.agent_id,
        company_id=ev.company_id,
        session_id=ev.session_id,
        overall_score=ev.overall_score,
        scores=ev.scores,
        evaluated_at=ev.evaluated_at,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _classify_trend(evaluations: list[AgentQualityEvaluation]) -> str:
    """
    Classifica trend com base na comparação entre metade inicial e metade final.
    Requer ao menos 4 amostras para classificação (senão 'insufficient_data').
    """
    n = len(evaluations)
    if n < 4:
        return "insufficient_data"

    half = n // 2
    first_half_avg = sum(e.overall_score for e in evaluations[:half]) / half
    second_half_avg = sum(e.overall_score for e in evaluations[half:]) / (n - half)

    delta = second_half_avg - first_half_avg
    if delta > 0.05:
        return "improving"
    if delta < -0.05:
        return "degrading"
    return "stable"

reorder_collection_before_item(router)
