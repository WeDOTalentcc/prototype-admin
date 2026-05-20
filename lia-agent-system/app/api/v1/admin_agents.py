"""
Admin — Agent Registry hot-reload endpoint.

Endpoints:
  POST /api/v1/admin/agents/reload  → trigger hot-reload of agents_registry.yaml

Acesso restrito a admins (require_admin).
Referência: app/core/agent_registry_watcher.py
"""
import logging
from typing import Any

from fastapi import APIRouter, Depends

from app.auth.dependencies import require_admin
from app.core.agent_registry_watcher import (
    AGENTS_REGISTRY_YAML,
    agent_registry_watcher,
    reload_agents_registry,
)
from app.shared.security.require_company_id import require_company_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/agents", tags=["Admin - Agents"])


@router.post("/reload", response_model=None)
async def reload_agent_registry(
    _user: Any = Depends(require_admin),
    company_id: str = Depends(require_company_id),
) -> dict[str, Any]:
    # multi-tenancy: admin/platform-level (admin_) — role-based access required
    """Trigger hot-reload of the agent YAML registry.

    Checks both ``agents_registry.yaml`` and ``tool_registry_metadata.yaml``
    for changes and reloads them.  Also performs a forced reload of the
    agents registry regardless of mtime so that an admin can force a sync.

    Args:
        company_id: Company identifier from JWT (admin-only; validated by require_admin).

    Returns:
        JSON with ``reloaded`` (list of agent names) and ``total`` (count).
    """
    logger.info(
        "[admin_agents] reload_agent_registry called by admin for company=%s",
        company_id,
    )

    # 1. Check-and-reload (mtime-gated, covers both YAML files).
    checked_names = await agent_registry_watcher.check_and_reload()

    # 2. Force reload agents registry so the response always reflects the
    #    current file state (even if mtime did not change since last check).
    forced_names = reload_agents_registry(AGENTS_REGISTRY_YAML)

    # Merge: union of names from both passes (order preserved, deduped).
    seen: set = set()
    reloaded = []
    for name in list(checked_names) + list(forced_names):
        if name not in seen:
            seen.add(name)
            reloaded.append(name)

    logger.info(
        "[admin_agents] Reload complete: %d agents — %s",
        len(reloaded),
        reloaded,
    )

    return {"reloaded": reloaded, "total": len(reloaded)}
