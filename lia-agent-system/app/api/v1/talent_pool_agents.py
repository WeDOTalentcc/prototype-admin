"""Sub-sprint 7A: endpoints canonical para talent pool agent assignments.

Plan: ~/Documents/wedotalent_audit_2026-05-25/AGENT_STUDIO_SPRINT7_PLAN.md §1.2

Multi-tenancy: company_id via Depends(require_company_id) — REGRA 2 (nunca payload).
Audit: log_decision em assign/unassign/run/update.

Dispatch on-demand (POST .../run) e listagem de runs estão STUB nesta sprint —
Sprint 7C implementa Celery task + run history table. Endpoints expostos pra
contrato congelar e frontend (Sprint 7B) integrar sem espera.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_tenant_db
from app.domains.agent_studio.repositories.custom_agent_repository import (
    CustomAgentRepository,
)
from app.domains.agent_studio.repositories.pool_agent_assignment_repository import (
    CrossTenantError,
    PoolAgentAssignmentRepository,
)
from app.schemas.pool_agent_assignment import (
    PoolAgentAssignmentCreate,
    PoolAgentAssignmentResponse,
    PoolAgentAssignmentUpdate,
)
from app.shared.security.require_company_id import require_company_id
from app.domains.agent_studio.repositories.pool_agent_run_repository import (
    PoolAgentRunRepository,
)
from app.jobs.tasks.pool_agents import dispatch_pool_agent_assignment_task
from app.schemas.pool_agent_run import PoolAgentRunResponse
from app.shared.types import AgentIdParam

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/talent-pools", tags=["talent-pool-agents"])


def _to_response(
    row, *, agent_name: Optional[str] = None, agent_category: Optional[str] = None
) -> PoolAgentAssignmentResponse:
    return PoolAgentAssignmentResponse(
        id=str(row.id),
        talent_pool_id=str(row.talent_pool_id),
        custom_agent_id=str(row.custom_agent_id),
        custom_agent_name=agent_name,
        custom_agent_category=agent_category,
        status=row.status,
        schedule_type=row.schedule_type,
        schedule_config=row.schedule_config or {},
        config_overrides=row.config_overrides or {},
        last_run_at=row.last_run_at,
        last_run_status=row.last_run_status,
        runtime_metrics=row.runtime_metrics or {},
        created_at=row.created_at,
        updated_at=row.updated_at,
        created_by=row.created_by,
    )


@router.get("/{pool_id}/agents", response_model=list[PoolAgentAssignmentResponse])
async def list_pool_agents(
    pool_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
    company_id: str = Depends(require_company_id),
):
    repo = PoolAgentAssignmentRepository(db)
    rows = await repo.list_by_pool(pool_id=pool_id, company_id=company_id)
    # Enrich with custom_agent name+category (single round-trip via in-memory join)
    agent_repo = CustomAgentRepository(db)
    out: list[PoolAgentAssignmentResponse] = []
    for r in rows:
        agent = await agent_repo.get_by_id(
            agent_id=str(r.custom_agent_id), company_id=company_id
        )
        out.append(
            _to_response(
                r,
                agent_name=agent.name if agent else None,
                agent_category=getattr(agent, "category", None) if agent else None,
            )
        )
    return out


@router.post(
    "/{pool_id}/agents",
    response_model=PoolAgentAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def assign_agent_to_pool(
    pool_id: str,
    payload: PoolAgentAssignmentCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
    company_id: str = Depends(require_company_id),
):
    repo = PoolAgentAssignmentRepository(db)
    try:
        row = await repo.create(
            company_id=company_id,
            pool_id=pool_id,
            custom_agent_id=payload.custom_agent_id,
            schedule_type=payload.schedule_type,
            schedule_config=payload.schedule_config,
            config_overrides=payload.config_overrides,
            created_by=str(getattr(current_user, "id", "system")),
        )
    except CrossTenantError as exc:
        logger.warning("pool_agent_assign cross_tenant: %s", exc)
        raise HTTPException(status_code=403, detail="cross_tenant_assignment_forbidden")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    await db.commit()
    return _to_response(row)


@router.patch(
    "/{pool_id}/agents/{assignment_id}",
    response_model=PoolAgentAssignmentResponse,
)
async def update_assignment(
    pool_id: str,
    assignment_id: str,
    payload: PoolAgentAssignmentUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
    company_id: str = Depends(require_company_id),
):
    repo = PoolAgentAssignmentRepository(db)
    row = await repo.update(
        assignment_id=assignment_id,
        company_id=company_id,
        **payload.model_dump(exclude_unset=True),
    )
    if row is None:
        raise HTTPException(status_code=404, detail="assignment_not_found")
    if str(row.talent_pool_id) != pool_id:
        raise HTTPException(status_code=400, detail="pool_id_mismatch")
    await db.commit()
    return _to_response(row)


@router.delete(
    "/{pool_id}/agents/{assignment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def unassign_agent(
    pool_id: str,
    assignment_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
    company_id: str = Depends(require_company_id),
):
    repo = PoolAgentAssignmentRepository(db)
    # Verify pool_id match before delete
    row = await repo.get_by_id(assignment_id=assignment_id, company_id=company_id)
    if row is None:
        raise HTTPException(status_code=404, detail="assignment_not_found")
    if str(row.talent_pool_id) != pool_id:
        raise HTTPException(status_code=400, detail="pool_id_mismatch")
    await repo.delete(assignment_id=assignment_id, company_id=company_id)
    await db.commit()


@router.post(
    "/{pool_id}/agents/{assignment_id}/run",
    status_code=status.HTTP_202_ACCEPTED,
)
async def dispatch_on_demand(
    pool_id: str,
    assignment_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
    company_id: str = Depends(require_company_id),
):
    """Sprint 7C Part 1.5c — wire dispatch_pool_agent_assignment_task.delay (REAL).

    Pre-valida assignment existe (cross-tenant via company_id no repo) + pool match.
    Despacha via Celery (trigger_source='on_demand'). Worker cria PoolAgentRun + executa
    CustomAgentRuntime + persiste resultados (Part 1.5b _dispatch_impl canonical).
    """
    repo = PoolAgentAssignmentRepository(db)
    row = await repo.get_by_id(assignment_id=assignment_id, company_id=company_id)
    if row is None:
        raise HTTPException(status_code=404, detail="assignment_not_found")
    if str(row.talent_pool_id) != pool_id:
        raise HTTPException(status_code=400, detail="pool_id_mismatch")

    dispatch_pool_agent_assignment_task.delay(
        assignment_id=str(assignment_id),
        trigger_source="on_demand",
    )
    logger.info(
        "dispatch_on_demand canonical assignment_id=%s pool=%s agent=%s company=%s",
        assignment_id, pool_id, row.custom_agent_id, company_id,
    )
    return {"status": "queued", "assignment_id": assignment_id}


@router.get(
    "/{pool_id}/agents/{assignment_id}/runs",
    response_model=list[PoolAgentRunResponse],
    summary="Lista histórico de runs do assignment (Sprint 7C Part 1.5a canonical).",
)
async def list_runs(
    pool_id: str,
    assignment_id: AgentIdParam,
    limit: int = 50,
    offset: int = 0,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
    company_id: str = Depends(require_company_id),
):
    """Lista runs canonical. Sprint 7C Part 1.5a substituiu stub Sprint 7A.

    Orchestrator real (Part 1.5b futuro) escreve via PoolAgentRunRepository.create
    + update_status. Este endpoint apenas le.
    """
    # Tenant gate + pool consistency: valida assignment pertence ao tenant + pool
    assign_repo = PoolAgentAssignmentRepository(db)
    row = await assign_repo.get_by_id(
        assignment_id=assignment_id, company_id=company_id
    )
    if row is None:
        raise HTTPException(status_code=404, detail="assignment_not_found")
    if str(row.talent_pool_id) != pool_id:
        raise HTTPException(status_code=400, detail="pool_id_mismatch")

    runs_repo = PoolAgentRunRepository(db)
    runs = await runs_repo.list_by_assignment(
        assignment_id, company_id, limit=limit, offset=offset
    )
    return [
        PoolAgentRunResponse(
            id=r.id,
            assignment_id=r.assignment_id,
            company_id=r.company_id,
            trigger_source=r.trigger_source,
            status=r.status,
            started_at=r.started_at,
            finished_at=r.finished_at,
            dispatch_metadata=r.dispatch_metadata or {},
            results=r.results or {},
            runtime_metrics=r.runtime_metrics or {},
            error_message=r.error_message,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in runs
    ]
