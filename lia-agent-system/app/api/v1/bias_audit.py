from __future__ import annotations
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

"""
Bias Audit API — E.2

Endpoint para auditoria de adverse impact real por vaga.
Retorna apenas estatísticas agregadas (LGPD-safe, sem PII).

GET /api/v1/bias-audit/job/{job_id}

Referências:
- dei-fairness §4 (Four-Fifths Rule)
- EU AI Act Art. 10 (dados de treino / auditoria)
"""
import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.shared.tenant_guard import get_verified_company_id
from typing import TYPE_CHECKING

from app.shared.security.require_company_id import require_company_id

if TYPE_CHECKING:
    from app.shared.services.bias_audit_service import BiasAuditReport



logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bias-audit", tags=["bias-audit"])


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class DemographicAuditResultResponse(BaseModel):
    dimension: str
    groups: dict[str, dict]
    adverse_impact_ratio: float
    below_threshold: bool
    alert_level: str
    disparate_impact: dict = {}   # D3: {"chi2", "p_value", "significant", "available"}
    eeoc_compliant: bool = True   # D3: Four-Fifths ok AND p >= 0.05


# DUPLICATE_OF_INTENT: app/schemas/observability.py:491 — API-side 5-field summary subset of DB-backed canonical response (Sprint Q.4: M-bucket — defer rename until handler converges)
class BiasAuditReportResponse(BaseModel):
    job_id: str
    evaluated_at: datetime
    total_candidates: int
    dimensions: list[DemographicAuditResultResponse]
    has_alerts: bool

# P2-W4 DUPLICATE_OF_INTENT backward-compat alias
# (see app/schemas/observability.py:491 for the canonical DB-backed version)
BiasAuditSummaryResponse = BiasAuditReportResponse


def _to_response(report: BiasAuditReport) -> BiasAuditReportResponse:
    return BiasAuditReportResponse(
        job_id=report.job_id,
        evaluated_at=report.evaluated_at,
        total_candidates=report.total_candidates,
        dimensions=[
            DemographicAuditResultResponse(
                dimension=d.dimension,
                groups=d.groups,
                adverse_impact_ratio=d.adverse_impact_ratio,
                below_threshold=d.below_threshold,
                alert_level=d.alert_level,
                disparate_impact=d.disparate_impact,
                eeoc_compliant=d.eeoc_compliant,
            )
            for d in report.dimensions
        ],
        has_alerts=report.has_alerts,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/job/{job_id}", response_model=BiasAuditReportResponse)
async def get_bias_audit(
    job_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id)) -> BiasAuditReportResponse:
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Retorna auditoria de adverse impact para a vaga indicada.

    Calcula Four-Fifths Rule (adverse_impact_ratio >= 0.80) em 4 dimensões:
    - gender: masculino, feminino, outro/não informado
    - age_group: <30, 30-44, 45+
    - disability: pcd, sem pcd
    - region: por estado

    Apenas estatísticas agregadas são retornadas (LGPD-safe, sem IDs individuais).
    alert_level: "ok" | "warning" (ratio < 0.80)
    """
    try:
        from app.shared.services.bias_audit_service import bias_audit_service as _svc
        report = await _svc.get_adverse_impact_by_job(db, job_id, company_id=UUID(company_id))
        return _to_response(report)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("bias_audit/job/%s erro: %s", job_id, exc)
        raise HTTPException(status_code=500, detail="Erro ao calcular auditoria de viés")


@router.get("/job/{job_id}/history", response_model=None)
async def get_bias_audit_history(
    job_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    company_id: str = Depends(get_verified_company_id),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Retorna histórico de snapshots de auditoria de viés para a vaga.

    Retornados em ordem decrescente de data (mais recente primeiro).
    Isolamento multi-tenant via X-Company-ID header.
    """
    try:
        from app.shared.services.bias_audit_service import bias_audit_service as _svc
        snapshots = await _svc.get_snapshot_history(db, UUID(company_id), job_id, limit)
        return {
            "job_id": job_id,
            "history": [s.to_dict() for s in snapshots],
            "count": len(snapshots),
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("bias_audit/job/%s/history erro: %s", job_id, exc)
        raise HTTPException(status_code=500, detail="Erro ao buscar histórico de auditoria")

reorder_collection_before_item(router)
