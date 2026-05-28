"""
Onda 3.B2 — /jobs/{job_id}/agents canonical shortcut.

Convenção REST mais natural pra UI "Agentes desta vaga":
  GET    /jobs/{job_id}/agents               → list active deployments + joined agent metadata
  POST   /jobs/{job_id}/agents               → attach an existing agent to job
  DELETE /jobs/{job_id}/agents/{deployment_id} → detach (delete deployment)

Internamente delega ao AgentDeploymentService canonical existente (target_type='job').
NÃO cria modelo separado job_agent_assignments — sensor B5 enforça unicidade.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db, get_tenant_db
from app.domains.job_management.repositories.job_vacancy_crud_repository import (
    JobVacancyCRUDRepository,
)
from app.schemas.agent_deployment import (
    AgentDeploymentWithAgent,
    AttachJobAgentRequest,
    JobAgentListResponse,
)
from app.services.agent_deployment_service import agent_deployment_service
from app.shared.security.require_company_id import require_company_id
from app.shared.trigger_mode_validation import validate_trigger_mode
from lia_models.agent_deployment import AgentDeployment
from lia_models.custom_agent import CustomAgent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["Job Agents"])


async def _validate_job_ownership(
    db: AsyncSession, job_id: str, company_id: str
) -> None:
    """Raise 404 if job doesn't exist OR doesn't belong to the tenant."""
    repo = JobVacancyCRUDRepository(db)
    job = await repo.get_vacancy_by_id_and_company(job_id, company_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")


def _to_with_agent(deployment: AgentDeployment, agent: Optional[CustomAgent]) -> dict:
    """Merge deployment.to_dict() with selected CustomAgent fields."""
    base = deployment.to_dict()
    if agent:
        base["agent_name"] = agent.name
        base["agent_category"] = getattr(agent, "category", None)
        base["agent_status"] = agent.status
        base["agent_domain"] = getattr(agent, "domain", None)
    else:
        base["agent_name"] = None
        base["agent_category"] = None
        base["agent_status"] = None
        base["agent_domain"] = None
    return base


@router.get("/{job_id}/agents", response_model=JobAgentListResponse)
async def list_job_agents(
    job_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(require_company_id),
):
    """List active agent deployments attached to this job, with joined agent metadata."""
    await _validate_job_ownership(db, job_id, current_user.company_id)

    deployments = await agent_deployment_service.list_by_target(
        db=db,
        company_id=current_user.company_id,
        target_type="job",
        target_id=job_id,
    )

    # Join with CustomAgent (1 query for all agent_ids).
    agent_map: dict = {}
    if deployments:
        agent_ids = list({str(d.agent_id) for d in deployments})
        # Multi-tenancy fail-closed: CustomAgent.company_id filter
        result = await db.execute(
            select(CustomAgent).where(
                and_(
                    CustomAgent.id.in_(agent_ids),
                    CustomAgent.company_id == current_user.company_id,
                )
            )
        )
        agent_map = {str(a.id): a for a in result.scalars().all()}

    items = [
        AgentDeploymentWithAgent(**_to_with_agent(d, agent_map.get(str(d.agent_id))))
        for d in deployments
    ]
    return JobAgentListResponse(deployments=items, total=len(items))


@router.post(
    "/{job_id}/agents",
    response_model=AgentDeploymentWithAgent,
    status_code=201,
)
async def attach_agent_to_job(
    job_id: str,
    body: AttachJobAgentRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
    company_id: str = Depends(require_company_id),
):
    """Attach a Studio agent to this job (creates AgentDeployment target_type='job')."""
    await _validate_job_ownership(db, job_id, current_user.company_id)

    # B4 — coerência target_type=job × trigger_mode.
    validate_trigger_mode("job", body.trigger_mode)

    # Validate agent exists in tenant before delegating.
    agent_result = await db.execute(
        select(CustomAgent).where(
            and_(
                CustomAgent.id == body.agent_id,
                CustomAgent.company_id == current_user.company_id,
            )
        )
    )
    agent = agent_result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    try:
        deployment = await agent_deployment_service.create_deployment(
            db=db,
            agent_id=body.agent_id,
            company_id=current_user.company_id,
            created_by=str(current_user.id),
            data={
                "target_type": "job",
                "target_id": job_id,
                "target_name": None,
                "trigger_mode": body.trigger_mode,
                "schedule_cron": body.schedule_cron,
                "config_overrides": body.config_overrides,
            },
        )
        # is_active override (default true on create)
        if body.is_active is False:
            deployment.is_active = False
        await db.commit()
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error("[JobAgents] attach failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to attach agent to job")

    return AgentDeploymentWithAgent(**_to_with_agent(deployment, agent))


@router.delete("/{job_id}/agents/{deployment_id}", status_code=204)
async def detach_agent_from_job(
    job_id: str,
    deployment_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
    company_id: str = Depends(require_company_id),
):
    """Detach (remove) a deployment from this job."""
    await _validate_job_ownership(db, job_id, current_user.company_id)

    # Ensure the deployment actually belongs to THIS job (not just to the tenant).
    deployment = await agent_deployment_service.get_deployment(
        db=db,
        deployment_id=deployment_id,
        company_id=current_user.company_id,
    )
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    if deployment.target_type != "job" or str(deployment.target_id) != str(job_id):
        raise HTTPException(
            status_code=404,
            detail="Deployment does not belong to this job",
        )

    deleted = await agent_deployment_service.delete_deployment(
        db=db,
        deployment_id=deployment_id,
        company_id=current_user.company_id,
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Deployment not found")
    await db.commit()
