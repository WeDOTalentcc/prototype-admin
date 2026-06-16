"""Admin endpoint — Expurgo de gravações de áudio (Phase 3b LGPD Art. 16).

Surface DPO/admin WeDOTalent para visibilidade cross-tenant dos expurgos mensais.

Endpoint:
  GET /api/v1/admin/expurgo-audit?company_id=<optional>&from_date=<ISO>&to_date=<ISO>&page=1&per_page=50

Role gate: wedotalent_admin only (staff WeDOTalent / DPO).
Multi-tenancy: wedotalent_admin tem acesso cross-tenant intencional para auditoria LGPD.
               company_id filter é opcional — sem filter retorna todos os tenants.

Retorna: lista paginada de audit_logs com action="expurgo_audio_recording".

LGPD refs: Art. 16 (minimização), Art. 20 (rastreabilidade), ANPD Guia §3.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_wedotalent_admin
from app.core.database import get_db
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin/expurgo-audit",
    tags=["Admin - LGPD Expurgo"],
)

_EXPURGO_ACTION = "expurgo_audio_recording"


# ── Response schemas ──────────────────────────────────────────────────────────

class ExpurgoAuditEntry(WeDoBaseModel):
    """Single expurgo audit log entry."""

    id: str
    company_id: str
    agent_name: str
    action: str
    decision: str
    reasoning: list[str] = []
    criteria_used: list[str] = []
    created_at: Optional[str] = None
    retention_until: Optional[str] = None


class ExpurgoAuditResponse(WeDoBaseModel):
    """Paginated response for expurgo audit entries."""

    items: list[ExpurgoAuditEntry]
    total: int
    page: int
    per_page: int
    pages: int


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.get("", response_model=ExpurgoAuditResponse)
async def get_expurgo_audit(
    company_id: Optional[str] = Query(
        None,
        description="Filtrar por empresa (UUID). Ausente = todos os tenants (cross-tenant).",
    ),
    from_date: Optional[str] = Query(
        None,
        description="Data início ISO (ex: 2026-01-01). Filtra created_at >= from_date.",
    ),
    to_date: Optional[str] = Query(
        None,
        description="Data fim ISO (ex: 2026-12-31). Filtra created_at <= to_date.",
    ),
    page: int = Query(1, ge=1, description="Página (1-based)."),
    per_page: int = Query(50, ge=1, le=200, description="Itens por página (máx 200)."),
    _user=Depends(require_wedotalent_admin),
    db: AsyncSession = Depends(get_db),
) -> ExpurgoAuditResponse:
    """Listagem paginada de registros de expurgo de áudio (DPO / admin WeDOTalent).

    Retorna audit_logs com action='expurgo_audio_recording' registrados pelo job mensal.
    Cada entry representa UM registro de áudio expurgado (tabela + entity_id + status Twilio).

    Somente wedotalent_admin pode acessar — cross-tenant intencional para DPO.
    """
    from lia_models.audit_log import AuditLog

    # Build filter conditions
    conditions = [AuditLog.action == _EXPURGO_ACTION]

    if company_id:
        conditions.append(AuditLog.company_id == company_id)

    if from_date:
        try:
            from datetime import datetime
            dt_from = datetime.fromisoformat(from_date.replace("Z", "+00:00"))
            conditions.append(AuditLog.created_at >= dt_from)
        except ValueError:
            logger.warning("[expurgo-audit] invalid from_date: %s", from_date)

    if to_date:
        try:
            from datetime import datetime
            dt_to = datetime.fromisoformat(to_date.replace("Z", "+00:00"))
            conditions.append(AuditLog.created_at <= dt_to)
        except ValueError:
            logger.warning("[expurgo-audit] invalid to_date: %s", to_date)

    # Count total
    from sqlalchemy import func, select
    count_q = select(func.count()).select_from(AuditLog).where(and_(*conditions))
    total_result = await db.execute(count_q)
    total = int(total_result.scalar() or 0)

    # Fetch page
    offset = (page - 1) * per_page
    rows_q = (
        select(AuditLog)
        .where(and_(*conditions))
        .order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    result = await db.execute(rows_q)
    rows = result.scalars().all()

    items = [
        ExpurgoAuditEntry(
            id=str(row.id),
            company_id=str(row.company_id),
            agent_name=row.agent_name or "",
            action=row.action or "",
            decision=row.decision or "",
            reasoning=list(row.reasoning or []),
            criteria_used=list(row.criteria_used or []),
            created_at=row.created_at.isoformat() if row.created_at else None,
            retention_until=row.retention_until.isoformat() if row.retention_until else None,
        )
        for row in rows
    ]

    pages = max(1, (total + per_page - 1) // per_page)

    return ExpurgoAuditResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )
