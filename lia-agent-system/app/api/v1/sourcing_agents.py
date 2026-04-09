"""
Sourcing Agents API — endpoints for managing persistent sourcing agents.

Apply to: lia-agent-system/app/api/v1/sourcing_agents.py
Register: app.include_router(sourcing_agents_router)
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.dependencies import get_current_user
from app.core.database import get_db
from pydantic import BaseModel, Field
from typing import Optional

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
    from app.services.sourcing_agent_orchestrator import sourcing_agent_orchestrator
    result = await sourcing_agent_orchestrator.create_agent(
        company_id=getattr(current_user, "company_id", "unknown"),
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
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List sourcing agents for the current company."""
    from libs.models.lia_models.sourcing_agent import SourcingAgent
    from sqlalchemy import select

    query = select(SourcingAgent).where(
        SourcingAgent.company_id == getattr(current_user, "company_id", "unknown")
    )
    if job_id:
        query = query.where(SourcingAgent.job_id == job_id)
    if talent_pool_id:
        query = query.where(SourcingAgent.talent_pool_id == talent_pool_id)
    if status:
        query = query.where(SourcingAgent.status == status)

    query = query.order_by(SourcingAgent.created_at.desc())
    result = await db.execute(query)
    agents = result.scalars().all()

    return {"agents": [
        {
            "id": str(a.id),
            "agent_name": a.agent_name,
            "status": a.status,
            "calibration_v": a.calibration_v,
            "job_id": a.job_id,
            "talent_pool_id": str(a.talent_pool_id) if a.talent_pool_id else None,
            "search_strategy": a.search_strategy,
            "preferences": a.preferences,
            "profiles_viewed": a.profiles_viewed,
            "profiles_approved": a.profiles_approved,
            "profiles_rejected": a.profiles_rejected,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in agents
    ]}


@router.get("/{agent_id}")
async def get_sourcing_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    """Get details of a specific sourcing agent."""
    from libs.models.lia_models.sourcing_agent import SourcingAgent
    from sqlalchemy import select

    result = await db.execute(select(SourcingAgent).where(SourcingAgent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(404, "Agent not found")

    return {
        "id": str(agent.id),
        "agent_name": agent.agent_name,
        "status": agent.status,
        "calibration_v": agent.calibration_v,
        "search_strategy": agent.search_strategy,
        "preferences": agent.preferences,
        "profiles_viewed": agent.profiles_viewed,
        "profiles_approved": agent.profiles_approved,
        "profiles_rejected": agent.profiles_rejected,
    }


@router.post("/{agent_id}/feedback")
async def submit_feedback(
    agent_id: str,
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
    }


@router.get("/{agent_id}/calibration-candidates")
async def get_calibration_candidates(
    agent_id: str,
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
    agent_id: str,
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
async def pause_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    """Pause a sourcing agent."""
    from libs.models.lia_models.sourcing_agent import SourcingAgent
    from sqlalchemy import select

    result = await db.execute(select(SourcingAgent).where(SourcingAgent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(404, "Agent not found")

    agent.status = "paused"
    await db.commit()
    return {"status": "paused"}


@router.patch("/{agent_id}/resume")
async def resume_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    """Resume a paused sourcing agent."""
    from libs.models.lia_models.sourcing_agent import SourcingAgent
    from sqlalchemy import select

    result = await db.execute(select(SourcingAgent).where(SourcingAgent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(404, "Agent not found")

    agent.status = "active"
    await db.commit()
    return {"status": "active"}
