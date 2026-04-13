"""
REST API for AgentDeployments — binding agents to jobs, pools, stages, lists.
"""
import logging
import time

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.schemas.agent_deployment import (
    CreateDeploymentRequest,
    DeploymentListResponse,
    DeploymentResponse,
    RunDeploymentRequest,
    RunDeploymentResponse,
    UpdateDeploymentRequest,
)
from app.services.agent_deployment_service import agent_deployment_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/custom-agents", tags=["Agent Deployments"])


@router.post("/{agent_id}/deployments", response_model=DeploymentResponse, status_code=201)
async def create_deployment(
    agent_id: str,
    body: CreateDeploymentRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Bind an agent to a target (job, talent pool, pipeline stage, candidate list)."""
    try:
        deployment = await agent_deployment_service.create_deployment(
            db=db,
            agent_id=agent_id,
            company_id=current_user.company_id,
            created_by=str(current_user.id),
            data=body.model_dump(),
        )
        await db.commit()
        return DeploymentResponse(**deployment.to_dict())
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        logger.error("Error creating deployment: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create deployment")


@router.get("/{agent_id}/deployments", response_model=DeploymentListResponse)
async def list_agent_deployments(
    agent_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all deployments for a specific agent."""
    deployments = await agent_deployment_service.list_by_agent(
        db=db, agent_id=agent_id, company_id=current_user.company_id
    )
    return DeploymentListResponse(
        deployments=[DeploymentResponse(**d.to_dict()) for d in deployments],
        total=len(deployments),
    )


# Separate router for target-based queries (not nested under agent_id)
target_router = APIRouter(prefix="/agent-deployments", tags=["Agent Deployments"])


@target_router.get("", response_model=DeploymentListResponse)
async def list_deployments_by_target(
    target_type: str = Query(..., description="job | talent_pool | pipeline_stage | candidate_list"),
    target_id: str = Query(..., description="UUID of the target"),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all active agent deployments for a specific target (e.g., a job or pool)."""
    deployments = await agent_deployment_service.list_by_target(
        db=db,
        company_id=current_user.company_id,
        target_type=target_type,
        target_id=target_id,
    )
    return DeploymentListResponse(
        deployments=[DeploymentResponse(**d.to_dict()) for d in deployments],
        total=len(deployments),
    )


@target_router.patch("/{deployment_id}", response_model=DeploymentResponse)
async def update_deployment(
    deployment_id: str,
    body: UpdateDeploymentRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a deployment (change trigger, pause/resume, override config)."""
    deployment = await agent_deployment_service.update_deployment(
        db=db,
        deployment_id=deployment_id,
        company_id=current_user.company_id,
        data=body.model_dump(exclude_none=True),
    )
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    await db.commit()
    return DeploymentResponse(**deployment.to_dict())


@target_router.delete("/{deployment_id}", status_code=204)
async def delete_deployment(
    deployment_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a deployment binding."""
    deleted = await agent_deployment_service.delete_deployment(
        db=db, deployment_id=deployment_id, company_id=current_user.company_id
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Deployment not found")
    await db.commit()


@target_router.post("/{deployment_id}/run", response_model=RunDeploymentResponse)
async def run_deployment(
    deployment_id: str,
    body: RunDeploymentRequest = None,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger an agent on its target.

    Executes the agent with context from the target (job details, pool candidates, etc).
    """
    deployment = await agent_deployment_service.get_deployment(
        db=db, deployment_id=deployment_id, company_id=current_user.company_id
    )
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    if not deployment.is_active:
        raise HTTPException(status_code=400, detail="Deployment is not active")

    # Load agent
    from sqlalchemy import select
    from lia_models.custom_agent import CustomAgent
    agent_result = await db.execute(
        select(CustomAgent).where(CustomAgent.id == deployment.agent_id)
    )
    agent = agent_result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Execute
    from app.domains.agent_studio.custom_agent_runtime import get_or_create_runtime

    runtime = get_or_create_runtime(
        agent_id=str(agent.id),
        agent_name=agent.name,
        system_prompt=agent.system_prompt,
        allowed_tools=agent.allowed_tools or [],
        domain=agent.domain or "general",
        max_steps=agent.max_steps or 8,
        temperature=agent.temperature or 0.7,
        model_override=agent.model_override,
        company_id=current_user.company_id,
        enable_memory=getattr(agent, "enable_memory", True),
        excluded_tools=getattr(agent, "excluded_tools", None),
        context_level=getattr(agent, "context_level", "full"),
    )

    # Build context from target
    context = dict((body.context if body else {}) or {})
    context["deployment_id"] = str(deployment.id)
    context["target_type"] = deployment.target_type
    context["target_id"] = str(deployment.target_id)
    context["target_name"] = deployment.target_name or ""

    message = (body.message if body and body.message else
               f"Executar no alvo: {deployment.target_type} '{deployment.target_name or deployment.target_id}'")

    start = time.time()
    output = await runtime.execute(
        message=message,
        user_id=str(current_user.id),
        company_id=current_user.company_id,
        context=context,
    )
    elapsed_ms = int((time.time() - start) * 1000)

    # Record metrics
    await agent_deployment_service.record_execution(db, str(deployment.id))
    await db.commit()

    return RunDeploymentResponse(
        deployment_id=str(deployment.id),
        agent_id=str(agent.id),
        target_type=deployment.target_type,
        target_id=str(deployment.target_id),
        candidates_processed=1,
        execution_time_ms=elapsed_ms,
        status="completed",
    )
