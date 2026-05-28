"""
REST API for AgentDeployments — binding agents to jobs, pools, stages, lists.
"""
import logging
import time

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db, get_tenant_db
from app.schemas.agent_deployment import (
    BatchTargetsRequest,
    BatchTargetsResponse,
    BulkDeploymentFailedItem,
    BulkDeploymentRequest,
    BulkDeploymentResponse,
    BulkDeploymentSkippedItem,
    CreateDeploymentRequest,
    DeploymentListResponse,
    DeploymentResponse,
    RunDeploymentRequest,
    RunDeploymentResponse,
    UpdateDeploymentRequest,
)
from app.services.agent_deployment_service import agent_deployment_service
from app.shared.trigger_mode_validation import validate_trigger_mode
from lia_models.agent_deployment import DeploymentTargetType
from app.shared.security.require_company_id import require_company_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/custom-agents", tags=["Agent Deployments"])


@router.post("/{agent_id}/deployments", response_model=DeploymentResponse, status_code=201)
async def create_deployment(
    agent_id: str,
    body: CreateDeploymentRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Bind an agent to a target (job, talent pool, pipeline stage, candidate list)."""
    # Onda 3.B4 — validate target_type × trigger_mode coherence canonical.
    validate_trigger_mode(body.target_type, body.trigger_mode)
    try:
        deployment = await agent_deployment_service.create_deployment(
            db=db,
            agent_id=agent_id,
            company_id=current_user.company_id,
            created_by=str(current_user.id),
            data=body.model_dump(),
        )
        await db.commit()

        # P2.5a: Internal notification (non-blocking)
        try:
            from app.services.studio_notification_service import studio_notification_service
            from sqlalchemy import select as _sel
            from lia_models.custom_agent import CustomAgent as _CA
            _agent_res = await db.execute(_sel(_CA).where(_CA.id == agent_id))
            _agent = _agent_res.scalar_one_or_none()
            if _agent:
                await studio_notification_service.notify_deployment_created(
                    db=db,
                    user_id=str(current_user.id),
                    agent_id=str(deployment.agent_id),
                    agent_name=_agent.name,
                    target_type=deployment.target_type,
                    target_name=deployment.target_name,
                )
                await db.commit()
        except Exception as _notif_err:
            logger.warning("[StudioNotif] deployment notify failed: %s", _notif_err)

        # P2.5b: External webhook dispatch (non-blocking)
        try:
            from app.services.webhook_dispatcher import webhook_service
            await webhook_service.dispatch(
                db=db,
                company_id=current_user.company_id,
                event="agent.deployment.created",
                payload={
                    "deployment_id": str(deployment.id),
                    "agent_id": str(deployment.agent_id),
                    "target_type": deployment.target_type,
                    "target_id": str(deployment.target_id),
                    "target_name": deployment.target_name,
                    "trigger_mode": deployment.trigger_mode,
                    "user_id": str(current_user.id),
                },
            )
        except Exception as _wh_err:
            logger.warning("[Webhook] deployment dispatch failed: %s", _wh_err)

        return DeploymentResponse(**deployment.to_dict())
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Error creating deployment: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create deployment")


@router.get("/{agent_id}/deployments", response_model=DeploymentListResponse)
async def list_agent_deployments(
    agent_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
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
    target_type: DeploymentTargetType = Query(
        ..., description="job | talent_pool | pipeline_stage | candidate_list (enum canonical)"
    ),
    target_id: str = Query(..., description="UUID of the target"),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    """List all active agent deployments for a specific target (e.g., a job or pool)."""
    deployments = await agent_deployment_service.list_by_target(
        db=db,
        company_id=current_user.company_id,
        target_type=target_type.value,
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
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    """Update a deployment (change trigger, pause/resume, override config)."""
    # Onda 3.B4 — if trigger_mode changes, re-validate against current target_type.
    if body.trigger_mode is not None:
        existing = await agent_deployment_service.get_deployment(
            db=db,
            deployment_id=deployment_id,
            company_id=current_user.company_id,
        )
        if not existing:
            raise HTTPException(status_code=404, detail="Deployment not found")
        validate_trigger_mode(existing.target_type, body.trigger_mode)

    deployment = await agent_deployment_service.update_deployment(
        db=db,
        deployment_id=deployment_id,
        company_id=current_user.company_id,
        data=body.model_dump(exclude_none=True),
    )
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    await db.commit()

    # P1-W3-10: dispatch agent.deployment.paused when is_active set to False (was ghost event)
    if body.is_active is False:
        try:
            from app.services.webhook_dispatcher import webhook_service
            await webhook_service.dispatch(
                db=db,
                company_id=current_user.company_id,
                event="agent.deployment.paused",
                payload={
                    "deployment_id": str(deployment.id),
                    "agent_id": str(deployment.agent_id),
                    "target_type": deployment.target_type,
                    "target_id": str(deployment.target_id),
                    "user_id": str(current_user.id),
                },
            )
        except Exception as _wh_err:
            logger.warning("[Webhook] deployment.paused dispatch error: %s", _wh_err)

    return DeploymentResponse(**deployment.to_dict())


@target_router.delete("/{deployment_id}", status_code=204)
async def delete_deployment(
    deployment_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
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
company_id: str = Depends(require_company_id)):
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
    # Multi-tenancy fail-closed: explicit company_id filter (REGRA ZERO + B.1).
    agent_result = await db.execute(
        select(CustomAgent).where(
            CustomAgent.id == deployment.agent_id,
            CustomAgent.company_id == current_user.company_id,
        )
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


# ─────────────────────────────────────────────────────────────────────────────
# Onda 3.B1 — Batch by-targets (elimina N+1 do frontend Onda 2)
# ─────────────────────────────────────────────────────────────────────────────


@target_router.post("/by-targets", response_model=BatchTargetsResponse)
async def get_deployments_by_targets(
    payload: BatchTargetsRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(require_company_id),
):
    """Batch lookup: dict[target_id → list[active deployments]] in ONE SQL query.

    Limite: <= 100 target_ids por request (enforced via Pydantic max_length).

    Multi-tenancy: company_id from JWT applied as outer filter; target_ids
    are filtered IN within tenant.
    """
    grouped = await agent_deployment_service.list_by_targets(
        db=db,
        company_id=current_user.company_id,
        target_type=payload.target_type.value,
        target_ids=payload.target_ids,
    )

    return BatchTargetsResponse(
        deployments_by_target={
            tid: [DeploymentResponse(**d.to_dict()) for d in deps]
            for tid, deps in grouped.items()
        }
    )


# ─────────────────────────────────────────────────────────────────────────────
# Onda 3.B3 — Bulk deployment (1 agent → N targets atomic)
# ─────────────────────────────────────────────────────────────────────────────


@router.post(
    "/{agent_id}/deployments/bulk",
    response_model=BulkDeploymentResponse,
    status_code=201,
)
async def bulk_create_deployments(
    agent_id: str,
    payload: BulkDeploymentRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
    company_id: str = Depends(require_company_id),
):
    """Onda 3.B3 — Acoplar 1 agente a N targets em transação atômica.

    Limite: <= 50 target_ids (enforced via Pydantic max_length).

    Semantics:
      - Validação target_type × trigger_mode upfront.
      - Targets já com deployment ativo do mesmo agente: soft-skip
        (não bloqueiam criação dos demais).
      - Per-target cap (MAX_DEPLOYMENTS_PER_TARGET=5): se ultrapassado,
        target vai para `failed`, demais prosseguem.
      - Global agent cap (MAX_DEPLOYMENTS_PER_AGENT=10): se snapshot inicial
        + len(target_ids) excederia, rejeita o batch INTEIRO (400).
      - Commit atomic: created só persistem se nenhum raise. Skipped/failed
        são returned sem afetar commit.
      - Audit trail: single AuditLog entry per bulk operation.
    """
    # B4 — coerência target_type × trigger_mode (1 vez para o batch).
    validate_trigger_mode(payload.target_type.value, payload.trigger_mode)

    try:
        created, skipped, failed = await agent_deployment_service.bulk_create_deployments(
            db=db,
            agent_id=agent_id,
            company_id=current_user.company_id,
            created_by=str(current_user.id),
            target_type=payload.target_type.value,
            target_ids=payload.target_ids,
            trigger_mode=payload.trigger_mode,
            schedule_cron=payload.schedule_cron,
            is_active=payload.is_active,
            config_overrides=payload.config_overrides,
        )
        await db.commit()
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error("[BulkDeploy] failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Bulk deployment failed")

    # LGPD audit trail — single entry per bulk operation.
    try:
        from app.shared.compliance.audit_service import get_audit_service

        audit_svc = get_audit_service()
        await audit_svc.log_decision(
            company_id=current_user.company_id,
            agent_name="agent_studio.bulk_deploy",
            decision_type="generate_feedback",
            action="bulk_deploy_agent",
            decision=(
                f"Acoplado agente {agent_id} a {len(created)} target(s) "
                f"(skipped={len(skipped)}, failed={len(failed)})"
            ),
            reasoning=[
                f"target_type={payload.target_type.value}",
                f"trigger_mode={payload.trigger_mode}",
                f"requested={len(payload.target_ids)}",
                f"created={len(created)}",
                f"skipped={len(skipped)}",
                f"failed={len(failed)}",
            ],
            criteria_used=["agent_studio.bulk_deploy"],
            actor_user_id=str(current_user.id),
        )
    except Exception as _audit_err:
        logger.warning("[BulkDeploy] audit log failed: %s", _audit_err)

    return BulkDeploymentResponse(
        created=[DeploymentResponse(**d.to_dict()) for d in created],
        skipped=[BulkDeploymentSkippedItem(**s) for s in skipped],
        failed=[BulkDeploymentFailedItem(**f) for f in failed],
    )
