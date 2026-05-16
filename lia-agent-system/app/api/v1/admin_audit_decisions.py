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

from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match

from app.auth.dependencies import require_admin
from app.shared.compliance.audit_service import audit_service
from app.shared.tenant_guard import get_verified_company_id
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN
from typing import Annotated
from fastapi import Path

# Task #489 — UUID-or-digit constraint for dual-ID path params,
# preventing static sibling routes from being shadowed by
# item handlers (Task #455-class bug).
_DualId = Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)]

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
    actor_user_id: _DualId,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    date_from: datetime | None = Query(None, alias="date_from"),
    date_to: datetime | None = Query(None, alias="date_to"),
    company_id: str = Depends(get_verified_company_id),
    _user: Any = Depends(require_admin),
_company_gate: str = Depends(require_company_id)) -> dict:
    # multi-tenancy: admin/platform-level (admin_) — role-based access required
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

# Task #489 — Keep collection-scoped routes ahead of item-scoped
# routes so a static sibling segment cannot be silently shadowed
# by an {*_id} handler (the Task #455 routing-shadowing bug).
from app.api.v1._path_patterns import reorder_collection_before_item as _reorder_collection_before_item  # noqa: E402

_reorder_collection_before_item(router)
