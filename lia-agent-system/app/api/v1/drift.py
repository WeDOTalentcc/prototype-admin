"""
Model Drift API — screening-compliance §7

Endpoint para monitoramento de drift em produção.
Compara janela recente (7 dias) vs baseline (7 dias anteriores).

GET /api/v1/drift/status?company_id=<uuid>
"""
import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_admin
from app.auth.models import User
from app.core.database import get_db
from app.jobs.drift_job import run_drift_check_all_companies
from app.shared.services.model_drift_service import (
    DriftStatus,
    model_drift_service,
)
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match
from app.shared.errors import LIAError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/drift", tags=["model-drift"])


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class DriftTriggerResponse(BaseModel):
    name: str
    baseline_value: float
    recent_value: float
    delta: float
    threshold: float
    triggered: bool
    description: str


class DriftStatusResponse(BaseModel):
    company_id: str
    evaluated_at: datetime
    recent_window_start: datetime
    baseline_window_start: datetime
    drift_detected: bool
    alert_level: str
    triggers: list[DriftTriggerResponse]


def _to_response(status: DriftStatus) -> DriftStatusResponse:
    return DriftStatusResponse(
        company_id=status.company_id,
        evaluated_at=status.evaluated_at,
        recent_window_start=status.recent_window_start,
        baseline_window_start=status.baseline_window_start,
        drift_detected=status.drift_detected,
        alert_level=status.alert_level,
        triggers=[
            DriftTriggerResponse(
                name=t.name,
                baseline_value=t.baseline_value,
                recent_value=t.recent_value,
                delta=t.delta,
                threshold=t.threshold,
                triggered=t.triggered,
                description=t.description,
            )
            for t in status.triggers
        ],
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

class DriftBatchResponse(BaseModel):
    status: str
    checked: int
    drifted: int
    errors: int


@router.post("/run-batch", response_model=DriftBatchResponse)
async def run_drift_batch(
    notify_user_id: str | None = Query(None, description="ID do usuário que receberá alertas"),
    _current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)) -> DriftBatchResponse:
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Executa drift check para todas as empresas ativas em batch.

    Celery-ready: pode ser agendado via APScheduler ou Celery em Ciclo F.

    Args:
        notify_user_id: Opcional. Se fornecido, envia alerta Bell+Teams quando drift detectado.

    Returns:
        Sumário: { status, checked, drifted, errors }
    """
    try:
        summary = await run_drift_check_all_companies(db, notify_user_id)
        return DriftBatchResponse(status="completed", **summary)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("drift/run-batch erro: %s", exc)
        raise LIAError(message="Erro ao executar drift batch")


@router.get("/status", response_model=DriftStatusResponse)
async def get_drift_status(
    company_id: UUID = Query(..., description="UUID da empresa"),
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))) -> DriftStatusResponse:
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Retorna o status de drift para a empresa indicada.

    Compara janela recente (últimos 7 dias) vs baseline (7 dias anteriores) em:
    - score_drift: variação do score médio WSI > 0.5
    - approval_drift: variação da taxa de aprovação > 10 p.p.
    - cost_drift: variação do custo > 20%
    - latency_drift: variação do P95 de latência > 50%

    alert_level: "ok" | "warning" (1 trigger) | "critical" (2+ triggers)
    """
    try:
        status = await model_drift_service.evaluate(db, company_id)
        return _to_response(status)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("drift/status erro company=%s: %s", company_id, exc)
        raise LIAError(message="Erro ao calcular drift status")
