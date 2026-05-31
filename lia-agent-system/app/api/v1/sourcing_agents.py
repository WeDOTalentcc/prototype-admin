"""
Sourcing Agents API — endpoints for managing persistent sourcing agents.

Apply to: lia-agent-system/app/api/v1/sourcing_agents.py
Register: app.include_router(sourcing_agents_router)

# DEPRECATED — 2026-05-30
# Esses endpoints são legado do modelo de "sourcing agent" como entidade standalone.
# O modelo canonical atual é custom-agents (app/api/v1/custom_agents.py), que cobre
# criação, configuração, deploy e lifecycle de todos os tipos de agentes.
#
# Não adicionar novos endpoints aqui. Migrar consumers para:
#   GET  /api/v1/custom-agents              (lista agentes)
#   POST /api/v1/custom-agents              (cria agente)
#   PATCH /api/v1/custom-agents/{id}        (atualiza status/config)
#
# Este arquivo será removido quando o frontend não referenciar mais
# /api/backend-proxy/sourcing-agents diretamente.
# Tracked: migração pendente no backlog (não há ticket criado ainda).
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.core.database import get_db
from pydantic import BaseModel, Field
from typing import Optional
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN
from typing import Annotated
from fastapi import Path

# Task #489 — UUID-or-digit constraint for dual-ID path params,
# preventing static sibling routes from being shadowed by
# item handlers (Task #455-class bug).
_DualId = Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)]

logger = logging.getLogger(__name__)


def _ca_to_sourcing_dict(a) -> dict:
    """Mapeia um CustomAgent (category='sourcing') para o shape legado consumido
    pelo frontend (interface SourcingAgent). job_id/talent_pool_id/preferences
    vivem em config; métricas em runtime_metrics."""
    cfg = a.config or {}
    rm = a.runtime_metrics or {}
    return {
        "id": str(a.id),
        "agent_name": a.name,
        "status": a.status,
        "calibration_v": rm.get("calibration_v", 0),
        "job_id": cfg.get("job_id"),
        "talent_pool_id": cfg.get("talent_pool_id"),
        "search_strategy": a.search_strategy or {},
        "preferences": cfg.get("preferences") or a.preferences or {},
        "profiles_viewed": rm.get("profiles_viewed", 0),
        "profiles_approved": rm.get("profiles_approved", 0),
        "profiles_rejected": rm.get("profiles_rejected", 0),
        "created_at": a.created_at.isoformat() if a.created_at else None,
    }


router = APIRouter(prefix="/sourcing-agents", tags=["Sourcing Agents"])


class CreateSourcingAgentRequest(BaseModel):
    agent_name: str = Field(..., min_length=3, max_length=256)
    job_id: Optional[str] = None
    talent_pool_id: Optional[str] = None
    agent_template_id: Optional[str] = None
    search_strategy: Optional[dict] = None
    preferences: Optional[dict] = None


class FeedbackRequest(BaseModel):
    candidate_id: str
    signal_type: str = Field(..., pattern="^(positive|negative)$")
    reason: str = Field(..., min_length=3, max_length=500)


@router.post("")
async def create_sourcing_agent(
    body: CreateSourcingAgentRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new persistent sourcing agent for a job or talent pool."""
    from app.services.quota_enforcement import enforce_quota
    await enforce_quota("sourcing_agents", current_user.company_id, db)
    from app.services.sourcing_agent_orchestrator import sourcing_agent_orchestrator
    result = await sourcing_agent_orchestrator.create_agent(
        company_id=current_user.company_id,
        agent_name=body.agent_name,
        job_id=body.job_id,
        talent_pool_id=body.talent_pool_id,
        agent_template_id=body.agent_template_id,
        search_strategy=body.search_strategy,
        preferences=body.preferences,
        db=db,
    )
    return result


@router.get("")
async def list_sourcing_agents(
    job_id: Optional[str] = None,
    talent_pool_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List sourcing agents for the current company."""
    from lia_models.custom_agent import CustomAgent
    from sqlalchemy import select

    # Defensive: company_id MUST exist for tenant-scoped listing (ADR multi-tenant).
    # Without it the query would leak or explode — return 400 with a clear message
    # instead of 500, so the frontend can render a meaningful error.
    company_id = getattr(current_user, "company_id", None)
    if not company_id:
        logger.warning(
            "sourcing_agents.list_denied_no_company user_id=%s",
            getattr(current_user, "id", "unknown"),
        )
        raise HTTPException(
            status_code=400,
            detail="Usuário sem empresa associada. Não é possível listar agentes.",
        )

    try:
        query = select(CustomAgent).where(
            CustomAgent.company_id == str(company_id),
            CustomAgent.category == "sourcing",
        )
        if status:
            query = query.where(CustomAgent.status == status)
        query = query.order_by(CustomAgent.created_at.desc())
        result = await db.execute(query)
        agents = list(result.scalars().all())
        # job_id/talent_pool_id vivem em config (JSONB) — filtro em Python.
        if job_id:
            agents = [a for a in agents if (a.config or {}).get("job_id") == job_id]
        if talent_pool_id:
            agents = [a for a in agents if (a.config or {}).get("talent_pool_id") == talent_pool_id]
    except Exception as exc:
        logger.error(
            "sourcing_agents.list_failed company_id=%s job_id=%s talent_pool_id=%s status=%s error=%s",
            company_id, job_id, talent_pool_id, status, exc,
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Falha ao listar agentes de sourcing: {exc.__class__.__name__}",
        )

    logger.info(
        "sourcing_agents.list_ok company_id=%s count=%d",
        company_id, len(agents),
    )

    return {"agents": [_ca_to_sourcing_dict(a) for a in agents]}


@router.get("/{agent_id}")
async def get_sourcing_agent(agent_id: _DualId, db: AsyncSession = Depends(get_db)):
    """Get details of a specific sourcing agent."""
    from lia_models.custom_agent import CustomAgent
    from sqlalchemy import select

    result = await db.execute(
        select(CustomAgent).where(
            CustomAgent.id == agent_id,
            CustomAgent.category == "sourcing",
        )
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(404, "Agent not found")

    return _ca_to_sourcing_dict(agent)


@router.post("/{agent_id}/feedback")
async def submit_feedback(
    agent_id: _DualId,
    body: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Process recruiter feedback (approve/reject) on a candidate.
    Triggers strategy recalibration.
    """
    from app.services.sourcing_agent_orchestrator import sourcing_agent_orchestrator
    result = await sourcing_agent_orchestrator.process_feedback(
        agent_id=agent_id,
        candidate_id=body.candidate_id,
        signal_type=body.signal_type,
        reason=body.reason,
        db=db,
    )
    return {
        "calibration_version": result.calibration_version,
        "strategy_updated": result.strategy_updated,
        "new_exclusions": result.new_exclusions,
        "new_positive_signals": result.new_positive_signals,
        "approved_count": result.approved_count,
        "rejected_count": result.rejected_count,
        "viewed_count": result.approved_count + result.rejected_count,
    }


@router.get("/{agent_id}/calibration-candidates")
async def get_calibration_candidates(
    agent_id: _DualId,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """Get candidates for the Big Card calibration modal."""
    from app.services.sourcing_agent_orchestrator import sourcing_agent_orchestrator
    candidates = await sourcing_agent_orchestrator.get_calibration_candidates(
        agent_id=agent_id, limit=limit, db=db,
    )
    return {"candidates": candidates}


@router.get("/{agent_id}/timeline")
async def get_agent_timeline(
    agent_id: _DualId,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """Get activity timeline for the Agents tab."""
    from app.services.sourcing_agent_orchestrator import sourcing_agent_orchestrator
    timeline = await sourcing_agent_orchestrator.get_agent_timeline(
        agent_id=agent_id, limit=limit, db=db,
    )
    return {"timeline": timeline}


@router.patch("/{agent_id}/pause")
async def pause_agent(agent_id: _DualId, db: AsyncSession = Depends(get_db)):
    """Pause a sourcing agent."""
    from lia_models.custom_agent import CustomAgent
    from sqlalchemy import select

    result = await db.execute(
        select(CustomAgent).where(
            CustomAgent.id == agent_id,
            CustomAgent.category == "sourcing",
        )
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(404, "Agent not found")

    agent.status = "paused"
    await db.commit()
    return {"status": "paused"}


@router.patch("/{agent_id}/resume")
async def resume_agent(agent_id: _DualId, db: AsyncSession = Depends(get_db)):
    """Resume a paused sourcing agent."""
    from lia_models.custom_agent import CustomAgent
    from sqlalchemy import select

    result = await db.execute(
        select(CustomAgent).where(
            CustomAgent.id == agent_id,
            CustomAgent.category == "sourcing",
        )
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(404, "Agent not found")

    agent.status = "active"
    await db.commit()
    return {"status": "active"}

# Task #489 — Keep collection-scoped routes ahead of item-scoped
# routes so a static sibling segment cannot be silently shadowed
# by an {*_id} handler (the Task #455 routing-shadowing bug).
from app.api.v1._path_patterns import reorder_collection_before_item as _reorder_collection_before_item  # noqa: E402

_reorder_collection_before_item(router)
