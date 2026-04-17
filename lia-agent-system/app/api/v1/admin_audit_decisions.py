"""Admin endpoint for filtering AI decision audit entries by user.

Task #366 — promote ``actor_user_id`` to a structured audit field.

The existing ``audit-logs`` router (``audit_logs.py``) reads from the SOX
compliance table (``SOXAuditLog``). The AI decision trail produced by
``audit_service.log_decision`` lives in a separate table (``audit_logs``
mapped by ``lia_models.audit_log.AuditLog``). This module exposes the new
``actor_user_id`` column on that AI decision table so admin reports can
filter who authored which decision (e.g. who edited each hiring policy).
"""
from __future__ import annotations

import logging
from datetime import datetime

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth.dependencies import require_admin
from app.shared.compliance.audit_service import audit_service
from app.shared.tenant_guard import get_verified_company_id

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin/audit-decisions",
    tags=["admin-audit-decisions"],
)


@router.get(
    "/by-user/{actor_user_id}",
    summary="List AI decisions triggered by a specific user",
)
async def list_decisions_by_user(
    actor_user_id: str,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    date_from: datetime | None = Query(None, alias="date_from"),
    date_to: datetime | None = Query(None, alias="date_to"),
    company_id: str = Depends(get_verified_company_id),
    _user: Any = Depends(require_admin),
) -> dict:
    """Return paginated audit entries authored by ``actor_user_id``.

    Backed by the structured ``actor_user_id`` column on ``audit_logs``,
    so the filter is an indexed column lookup (no JSON scanning).
    """
    if not actor_user_id or not actor_user_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="actor_user_id is required",
        )
    return await audit_service.get_decisions_by_user(
        company_id=company_id,
        actor_user_id=actor_user_id.strip(),
        start_date=date_from,
        end_date=date_to,
        limit=limit,
        offset=offset,
    )
