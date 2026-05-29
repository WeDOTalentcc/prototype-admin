"""
Agent Monitoring API Endpoints
Provides real-time metrics, health scores, and activity tracking for AI agents.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.analytics.services.agent_monitoring_service import AgentMonitoringService
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match
from app.shared.types import WeDoBaseModel

router = APIRouter(prefix="/agent-monitoring", tags=["Agent Monitoring"])

logger = logging.getLogger(__name__)


class GlobalMetricsResponse(BaseModel):
    actions_today: int
    actions_delta: int
    active_agents: int
    total_agents: int
    success_rate: float
    avg_response_time: float
    proactive_alerts: int


class AgentSummaryResponse(BaseModel):
    id: str
    name: str
    icon: str
    status: str
    actions_today: int
    daily_goal: int
    progress: int
    delta: int
    sparkline: list[int]
    last_action: str | None = None
    last_action_time: str | None = None


class HealthDriverResponse(BaseModel):
    name: str
    value: float
    weight: int
    impact: str


class AgentHealthResponse(BaseModel):
    agent_id: str
    score: int
    tier: str
    drivers: list[HealthDriverResponse]
    recommendations: list[str]


class ActivityResponse(BaseModel):
    id: str
    agent_id: str
    agent_name: str
    agent_icon: str | None = None
    type: str
    title: str
    description: str | None = None
    status: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    duration_seconds: float | None = None
    sla_breach: bool | None = None
    related_job_id: str | None = None
    related_candidate_id: str | None = None


class AgentAlertResponse(BaseModel):
    id: str
    type: str
    agent_id: str
    agent_name: str
    title: str
    description: str
    created_at: str | None = None
    severity: str


class LogActivityRequest(WeDoBaseModel):
    agent_id: str
    activity_type: str
    title: str
    description: str | None = None
    status: str = "success"
    duration_seconds: float | None = None
    related_job_id: str | None = None
    related_candidate_id: str | None = None
    metadata: dict | None = None
    error_message: str | None = None
    sla_breach: bool = False


@router.get("/metrics", response_model=GlobalMetricsResponse)
async def get_global_metrics(db: AsyncSession = Depends(get_db), company_id: str = Depends(require_company_id)):
    # multi-tenancy: public endpoint (metrics) — no tenant data
    """Get global metrics across all agents."""
    service = AgentMonitoringService(db)
    metrics = await service.get_global_metrics()
    return GlobalMetricsResponse(**metrics)


@router.get("/agents", response_model=list[AgentSummaryResponse])
async def get_all_agents_summary(db: AsyncSession = Depends(get_db), company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get summary for all agents."""
    service = AgentMonitoringService(db)
    summaries = await service.get_all_agents_summary()
    return [AgentSummaryResponse(**s) for s in summaries]


@router.get("/agents/{agent_id}", response_model=AgentSummaryResponse)
async def get_agent_summary(agent_id: str, db: AsyncSession = Depends(get_db), company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get summary for a specific agent."""
    service = AgentMonitoringService(db)
    summary = await service.get_agent_summary(agent_id)
    if not summary:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    return AgentSummaryResponse(**summary)


@router.get("/agents/{agent_id}/health", response_model=AgentHealthResponse)
async def get_agent_health(agent_id: str, db: AsyncSession = Depends(get_db), company_id: str = Depends(require_company_id)):
    # multi-tenancy: public endpoint (health) — no tenant data
    """Get health score and details for a specific agent."""
    service = AgentMonitoringService(db)
    health = await service.get_agent_health(agent_id)
    if not health:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    return AgentHealthResponse(**health)


@router.get("/agents/{agent_id}/activities", response_model=list[ActivityResponse])
async def get_agent_activities(
    agent_id: str,
    status: str | None = Query(None, description="Filter by status"),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get activity feed for a specific agent."""
    service = AgentMonitoringService(db)
    activities = await service.get_activity_feed(
        agent_id=agent_id,
        status=status,
        limit=limit,
        offset=offset
    )
    return [ActivityResponse(**a) for a in activities]


@router.get("/activity-feed", response_model=list[ActivityResponse])
async def get_activity_feed(
    agent_id: str | None = Query(None, description="Filter by agent"),
    status: str | None = Query(None, description="Filter by status"),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get global activity feed with optional filters."""
    service = AgentMonitoringService(db)
    activities = await service.get_activity_feed(
        agent_id=agent_id,
        status=status,
        limit=limit,
        offset=offset
    )
    return [ActivityResponse(**a) for a in activities]


@router.get("/alerts", response_model=list[AgentAlertResponse])
async def get_proactive_alerts(db: AsyncSession = Depends(get_db), company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get current proactive alerts requiring attention."""
    service = AgentMonitoringService(db)
    alerts = await service.get_proactive_alerts()
    return [AgentAlertResponse(**a) for a in alerts]


@router.post("/activities", response_model=ActivityResponse)
async def log_activity(request: LogActivityRequest, db: AsyncSession = Depends(get_db), company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Log a new agent activity."""
    from app.models.agent_activity import ActivityStatus
    
    service = AgentMonitoringService(db)
    
    try:
        status_enum = ActivityStatus(request.status)
    except ValueError:
        status_enum = ActivityStatus.SUCCESS
    
    activity = await service.log_activity(
        agent_id=request.agent_id,
        activity_type=request.activity_type,
        title=request.title,
        description=request.description,
        status=status_enum,
        duration_seconds=request.duration_seconds,
        related_job_id=request.related_job_id,
        related_candidate_id=request.related_candidate_id,
        metadata=request.metadata,
        error_message=request.error_message,
        sla_breach=request.sla_breach,
    )
    
    return ActivityResponse(**activity.to_dict())


@router.get("/domains/health", response_model=None)
async def get_domains_health(
    company_id: str = Query(..., description="ID da empresa"),
    days: int = Query(30, ge=1, le=90, description="Janela de análise em dias"),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: public endpoint (health) — no tenant data
    """
    Saúde dos agentes por domínio — baseado em AgentExecutionRecord.

    Retorna métricas reais de execução (taxa de falha de tools, confiança,
    iterações, uptime) agrupadas por domínio nos últimos N dias.
    """
    from lia_agents_core.execution_log_store import ExecutionLogStore
    store = ExecutionLogStore()
    domains = await store.get_domain_health(company_id=company_id, days=days)
    return {
        "company_id": company_id,
        "window_days": days,
        "domains": domains,
        "total_domains": len(domains),
        "unhealthy_count": sum(1 for d in domains if d["status"] in ("degraded", "stale")),
    }


@router.get("/domains/{domain}/metrics", response_model=None)
async def get_domain_metrics(
    domain: str,
    company_id: str = Query(..., description="ID da empresa"),
    days: int = Query(30, ge=1, le=90, description="Janela de análise em dias"),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: public endpoint (metrics) — no tenant data
    """
    Métricas detalhadas de um domínio específico — baseado em AgentExecutionRecord.
    """
    from lia_agents_core.execution_log_store import ExecutionLogStore
    store = ExecutionLogStore()
    all_domains = await store.get_domain_health(company_id=company_id, days=days)
    domain_data = next((d for d in all_domains if d["domain"] == domain), None)
    if not domain_data:
        raise HTTPException(
            status_code=404,
            detail=f"Sem dados para domínio '{domain}' nos últimos {days} dias.",
        )
    return {"company_id": company_id, "window_days": days, **domain_data}


@router.post("/seed-demo", response_model=None)
async def seed_demo_data(db: AsyncSession = Depends(get_db), company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Seed demo data for testing. Only use in development."""
    service = AgentMonitoringService(db)
    result = await service.seed_demo_data()
    return {
        "success": True,
        "message": f"Created {result['activities_created']} demo activities",
        **result
    }


# ============================================================================
# Onda 1 B4 — Studio Control Room endpoints (2026-05-27)
# ============================================================================
# Sala de Controle = 4ª aba do Agent Studio. Recruiter ve em real-time:
#   1. Execucoes ativas (running last 1h)
#   2. Reasoning detalhado de uma execucao (decision tree LGPD-compliant)
#   3. Historico recente (paginado)
#
# Multi-tenancy: require_company_id obrigatorio em todos endpoints.
# LGPD Art. 9: campo data_fields_NOT_accessed declarativo em B4.2 declara
# que campos sensiveis (cpf, raca, religiao, genero, estado_civil) NUNCA
# aparecem em data_fields_accessed dos steps. Sensor B5.2 garante invariante.
# ============================================================================

from datetime import datetime, timedelta, timezone
from typing import Literal
from uuid import UUID as PyUUID

from sqlalchemy import and_, desc, or_, select
from sqlalchemy.orm import aliased

from app.shared.types import WeDoBaseModel as _WeDoBaseModel
from lia_agents_core.agent_interface import AgentReasoningStep
from lia_models.agent_deployment import AgentDeployment as _AgentDeployment
from lia_models.custom_agent import CustomAgent as _CustomAgent
from lia_models.pool_agent_assignment import PoolAgentAssignment as _PoolAgentAssignment
from lia_models.pool_agent_run import PoolAgentRun as _PoolAgentRun
from lia_models.talent_pool import TalentPool as _TalentPool

# C1.6a (2026-05-29): pool_agent_runs agora têm DUAS origens canonical —
# `assignment_id` (legacy/talent_pool via pool_agent_assignments) OU
# `deployment_id` (motor unificado Onda C1, qualquer surface: job, funil,
# pool, candidate_list). O CustomAgent é alcançado por caminhos distintos:
#   - run.assignment_id → pool_agent_assignments.custom_agent_id → custom_agents
#   - run.deployment_id → agent_deployments.agent_id            → custom_agents
# Para surfacar AMBAS as origens num único SELECT mock-friendly, juntamos via
# LEFT OUTER em todos os hops e resolvemos o agent/target efetivo em Python
# (_resolve_agent / _resolve_target_info). Aliases dão dois caminhos distintos
# até custom_agents sem colidir no FROM.
_AgentViaAssignment = aliased(_CustomAgent, name="agent_via_assignment")
_AgentViaDeployment = aliased(_CustomAgent, name="agent_via_deployment")


# LGPD Art. 9 — fields canonical que NUNCA podem aparecer em data_fields_accessed.
# Declarativo: B4.2 response sempre inclui essa lista pra audit transparency.
# Sensor B5.2 (check_lgpd_data_access_logged.py) garante invariante.
_LGPD_NEVER_ACCESSED_FIELDS = [
    "cpf",
    "raca",
    "religiao",
    "genero",
    "estado_civil",
]

_StudioTargetSurface = Literal["talent_pool", "job", "pipeline_stage", "candidate_list"]


class ActiveExecutionResponse(_WeDoBaseModel):
    execution_id: str
    agent_id: str
    agent_name: str
    target_type: str
    target_id: str
    target_name: str | None = None
    status: Literal["running", "completed", "error"]
    started_at: datetime
    progress_pct: int | None = None
    candidates_processed: int | None = None
    eta_seconds: int | None = None


class RecentExecutionResponse(_WeDoBaseModel):
    execution_id: str
    agent_id: str
    agent_name: str
    target_type: str
    target_id: str
    target_name: str | None = None
    status: Literal["success", "error", "timeout", "cancelled", "running", "queued"]
    started_at: datetime | None = None
    finished_at: datetime | None = None
    latency_ms: int | None = None
    success_summary: str | None = None


class ExecutionReasoningResponse(_WeDoBaseModel):
    execution_id: str
    agent_id: str
    agent_name: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    model_used: str | None = None
    cost_usd: float | None = None
    latency_ms: int | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    reasoning_trace: list[AgentReasoningStep]
    data_fields_accessed_summary: list[str]
    data_fields_NOT_accessed: list[str]


def _resolve_target_info(
    assignment: _PoolAgentAssignment | None,
    talent_pool: _TalentPool | None,
    deployment: "_AgentDeployment | None" = None,
) -> tuple[str, str, str | None]:
    """Resolve target_type / target_id / target_name canonical multi-surface.

    C1.6a (2026-05-29): pool_agent_runs agora têm duas origens —
    `assignment_id` (legacy/talent_pool) OU `deployment_id` (motor unificado
    Onda C1, qualquer surface). Precedência canonical:

      1. deployment presente → agent_deployments.{target_type,target_id,
         target_name} é a fonte de verdade (target_name já denormalizado).
         Cobre todos os surfaces: job, talent_pool, pipeline_stage,
         candidate_list.
      2. talent_pool presente (caminho legacy assignment) → talent_pool.
      3. assignment presente sem pool join → talent_pool sem nome.
      4. nada → ('talent_pool', 'unknown', None) fail-safe.
    """
    if deployment is not None:
        target_name = deployment.target_name
        return (
            str(deployment.target_type),
            str(deployment.target_id),
            target_name,
        )
    if talent_pool is not None:
        return "talent_pool", str(talent_pool.id), talent_pool.name
    if assignment is not None:
        return "talent_pool", str(assignment.talent_pool_id), None
    return "talent_pool", "unknown", None


def _resolve_agent(
    agent_via_assignment: _CustomAgent | None,
    agent_via_deployment: _CustomAgent | None,
) -> _CustomAgent | None:
    """Coalesce o CustomAgent das duas origens (assignment OU deployment).

    Um run tem exatamente uma origem (chk_par_source_present), então no máximo
    um dos dois aliases é não-nulo. Precedência: deployment (motor novo) >
    assignment (legacy) — irrelevante na prática pois são mutuamente
    exclusivos, mas determinística por segurança.
    """
    return agent_via_deployment or agent_via_assignment


def _studio_runs_select():
    """SELECT canonical multi-surface pra Studio Control Room.

    C1.6a (2026-05-29): driver é pool_agent_runs (fonte única). Cada run vem
    de assignment_id OU deployment_id. Resolvemos agent/target via DOIS
    caminhos LEFT OUTER (sem perder runs de nenhuma origem):

      run ─┬─ assignment ── agent_via_assignment
           │      └──────── talent_pool (nome legacy)
           └─ deployment ── agent_via_deployment
                  (agent_deployments traz target_type/id/name denormalizado)

    Tuple shape devolvido por linha:
      (run, assignment, agent_via_assignment, talent_pool,
       deployment, agent_via_deployment)

    Multi-tenancy: o caller adiciona `_PoolAgentRun.company_id == company_id`
    no .where() — fail-closed mantido. Os outer joins não relaxam o filtro de
    tenant porque o run (driver) já é tenant-scoped.
    """
    return (
        select(
            _PoolAgentRun,
            _PoolAgentAssignment,
            _AgentViaAssignment,
            _TalentPool,
            _AgentDeployment,
            _AgentViaDeployment,
        )
        .outerjoin(
            _PoolAgentAssignment,
            _PoolAgentRun.assignment_id == _PoolAgentAssignment.id,
        )
        .outerjoin(
            _AgentViaAssignment,
            _PoolAgentAssignment.custom_agent_id == _AgentViaAssignment.id,
        )
        .outerjoin(
            _TalentPool,
            _PoolAgentAssignment.talent_pool_id == _TalentPool.id,
        )
        .outerjoin(
            _AgentDeployment,
            _PoolAgentRun.deployment_id == _AgentDeployment.id,
        )
        .outerjoin(
            _AgentViaDeployment,
            _AgentDeployment.agent_id == _AgentViaDeployment.id,
        )
    )


def _map_status_to_studio(db_status: str) -> Literal["running", "completed", "error"]:
    """Map pool_agent_runs.status (6 valores) -> Studio Control Room (3 buckets)."""
    if db_status == "running":
        return "running"
    if db_status == "success":
        return "completed"
    return "error"


@router.get("/active-executions", response_model=list[ActiveExecutionResponse])
async def list_active_executions(
    surface: _StudioTargetSurface | None = Query(
        default=None,
        description="Filtra por target surface (talent_pool|job|pipeline_stage|candidate_list)",
    ),
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(require_company_id),
) -> list[ActiveExecutionResponse]:
    """Onda 1 B4.1 — Studio Control Room: execuções rodando agora.

    Multi-tenancy fail-closed via require_company_id.
    Filtro: status='running' AND started_at > now() - 1h (exclui orphans).
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
    stmt = _studio_runs_select().where(
        and_(
            _PoolAgentRun.company_id == company_id,
            _PoolAgentRun.status == "running",
            _PoolAgentRun.started_at != None,  # noqa: E711 — sqlalchemy idiom
            _PoolAgentRun.started_at > cutoff,
        )
    ).order_by(desc(_PoolAgentRun.started_at))
    result = await db.execute(stmt)
    rows = result.all()

    out: list[ActiveExecutionResponse] = []
    for run, assignment, agent_a, pool, deployment, agent_d in rows:
        agent = _resolve_agent(agent_a, agent_d)
        if agent is None:
            # Defesa: run órfão sem agent resolvível (FK quebrada) — skip.
            continue
        target_type, target_id, target_name = _resolve_target_info(
            assignment, pool, deployment
        )
        # C1.6a (2026-05-29): filtro surface agora vale pra TODOS os
        # target_types (deployment_id surfaca job/funil/pool/list).
        if surface is not None and surface != target_type:
            continue
        rm = run.runtime_metrics or {}
        candidates_processed = rm.get("candidates_processed")
        progress_pct = rm.get("progress_pct")
        eta_seconds = rm.get("eta_seconds")
        out.append(
            ActiveExecutionResponse(
                execution_id=str(run.id),
                agent_id=str(agent.id),
                agent_name=agent.name,
                target_type=target_type,
                target_id=target_id,
                target_name=target_name,
                status="running",
                started_at=run.started_at,
                progress_pct=int(progress_pct) if progress_pct is not None else None,
                candidates_processed=(
                    int(candidates_processed)
                    if candidates_processed is not None
                    else None
                ),
                eta_seconds=int(eta_seconds) if eta_seconds is not None else None,
            )
        )
    return out


@router.get(
    "/executions/{execution_id}/reasoning",
    response_model=ExecutionReasoningResponse,
)
async def get_execution_reasoning(
    execution_id: str,
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(require_company_id),
) -> ExecutionReasoningResponse:
    """Onda 1 B4.2 — decision tree completo de uma execução.

    Retorna AgentReasoningStep[] + LGPD declarative trail.
    404 se reasoning_payload é None (execução pre-B3 ou agent não-instrumentado).
    """
    try:
        exec_uuid = PyUUID(execution_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="execution_id deve ser UUID válido")

    # C1.6a (2026-05-29): reasoning funciona pra run de QUALQUER origem
    # (assignment_id legacy OU deployment_id multi-surface). Multi-surface
    # select resolve o agent via ambos os caminhos.
    stmt = _studio_runs_select().where(
        and_(
            _PoolAgentRun.id == exec_uuid,
            _PoolAgentRun.company_id == company_id,
        )
    )
    result = await db.execute(stmt)
    row = result.one_or_none()
    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Execução não encontrada ou pertence a outro tenant.",
        )
    run, _assignment, agent_a, _pool, _deployment, agent_d = row
    agent = _resolve_agent(agent_a, agent_d)
    if agent is None:
        raise HTTPException(
            status_code=404,
            detail="Execução sem agente resolvível (FK quebrada).",
        )
    if not run.reasoning_payload:
        raise HTTPException(
            status_code=404,
            detail=(
                "Decision tree não disponível para esta execução. "
                "Execuções gravadas antes da Onda 1 B3 ou via agentes "
                "não-instrumentados não têm reasoning_payload."
            ),
        )

    # Parse JSONB -> Pydantic models (validation).
    try:
        steps = [AgentReasoningStep(**s) for s in (run.reasoning_payload or [])]
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Reasoning payload corrompido (shape divergente): {exc}",
        )

    # Aggregate data_fields_accessed across all steps (LGPD audit summary).
    accessed_summary: set[str] = set()
    for s in steps:
        accessed_summary.update(s.data_fields_accessed)
    # Defense-in-depth: strip any LGPD-forbidden field that might have slipped.
    accessed_summary -= set(_LGPD_NEVER_ACCESSED_FIELDS)

    rm = run.runtime_metrics or {}
    return ExecutionReasoningResponse(
        execution_id=str(run.id),
        agent_id=str(agent.id),
        agent_name=agent.name,
        started_at=run.started_at,
        completed_at=run.finished_at,
        model_used=rm.get("model_used") or None,
        cost_usd=float(rm["cost_usd"]) if rm.get("cost_usd") is not None else None,
        latency_ms=int(rm["latency_ms"]) if rm.get("latency_ms") is not None else None,
        input_tokens=(
            int(rm["input_tokens"]) if rm.get("input_tokens") is not None else None
        ),
        output_tokens=(
            int(rm["output_tokens"]) if rm.get("output_tokens") is not None else None
        ),
        reasoning_trace=steps,
        data_fields_accessed_summary=sorted(accessed_summary),
        data_fields_NOT_accessed=list(_LGPD_NEVER_ACCESSED_FIELDS),
    )


@router.get("/recent-executions", response_model=list[RecentExecutionResponse])
async def list_recent_executions(
    limit: int = Query(default=50, ge=1, le=200),
    agent_id: str | None = Query(default=None),
    surface: _StudioTargetSurface | None = Query(default=None),
    status: Literal["completed", "error", "all"] = Query(default="all"),
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(require_company_id),
) -> list[RecentExecutionResponse]:
    """Onda 1 B4.3 — histórico recente de execuções (não-running).

    Filtros opcionais: agent_id, surface, status.
    Paginação: limit (max 200), order by created_at desc.
    """
    conditions = [
        _PoolAgentRun.company_id == company_id,
        _PoolAgentRun.status != "running",
        _PoolAgentRun.status != "queued",
    ]
    if status == "completed":
        conditions.append(_PoolAgentRun.status == "success")
    elif status == "error":
        conditions.append(_PoolAgentRun.status.in_(["error", "timeout", "cancelled"]))
    if agent_id is not None:
        try:
            agent_uuid = PyUUID(agent_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="agent_id deve ser UUID válido")
        # C1.6a (2026-05-29): agent_id filter precisa casar AMBAS as origens —
        # via assignment.custom_agent_id (legacy) OU deployment.agent_id (novo).
        conditions.append(
            or_(
                _PoolAgentAssignment.custom_agent_id == agent_uuid,
                _AgentDeployment.agent_id == agent_uuid,
            )
        )

    stmt = (
        _studio_runs_select()
        .where(and_(*conditions))
        .order_by(desc(_PoolAgentRun.created_at))
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.all()

    out: list[RecentExecutionResponse] = []
    for run, assignment, agent_a, pool, deployment, agent_d in rows:
        agent = _resolve_agent(agent_a, agent_d)
        if agent is None:
            continue
        target_type, target_id, target_name = _resolve_target_info(
            assignment, pool, deployment
        )
        if surface is not None and surface != target_type:
            continue
        rm = run.runtime_metrics or {}
        results = run.results or {}
        success_summary = None
        if run.status == "success":
            response = results.get("response", "")
            success_summary = response[:140] if response else None
        elif run.error_message:
            success_summary = run.error_message[:140]
        out.append(
            RecentExecutionResponse(
                execution_id=str(run.id),
                agent_id=str(agent.id),
                agent_name=agent.name,
                target_type=target_type,
                target_id=target_id,
                target_name=target_name,
                status=run.status,
                started_at=run.started_at,
                finished_at=run.finished_at,
                latency_ms=(
                    int(rm["latency_ms"]) if rm.get("latency_ms") is not None else None
                ),
                success_summary=success_summary,
            )
        )
    return out


# ============================================================================
# Onda 2 B1 — /agent-monitoring/active-summary (2026-05-28)
# ============================================================================
# AgentsCard no Decidir + indicador global "N agentes trabalhando agora".
# Top N agentes mais ativos do tenant (last hour). surface=decidir mostra
# todos os surfaces; pool/job/funil filtram pelo target_type canonical.
#
# Multi-tenancy: require_company_id + filter explícito.
# ADR-001: lê via select() em api/ (não em services/) — pattern canonical
# dos endpoints B4 Onda 1.
# ============================================================================

from lia_models.approval import ApprovalRequest, ApprovalStatus

_AgentsCardSurface = Literal["decidir", "pool", "job", "funil", "all"]

# Mapping surface (UI-level) -> target_type (model-level canonical).
# "decidir" e "all" não filtram; outros mapeiam 1-1 com DeploymentTargetType.
_SURFACE_TO_TARGET_TYPE = {
    "pool": "talent_pool",
    "job": "job",
    "funil": "pipeline_stage",
}


class ActiveAgentSummary(_WeDoBaseModel):
    agent_id: str
    agent_name: str
    agent_category: str
    status: Literal["running", "idle", "pending_approval"]
    target_type: str | None = None
    target_id: str | None = None
    target_name: str | None = None
    last_action_label: str | None = None
    last_execution_id: str | None = None
    pending_approvals_count: int = 0
    last_activity_at: datetime | None = None


class ActiveSummaryResponse(_WeDoBaseModel):
    running_count: int
    items: list[ActiveAgentSummary]


def _build_action_label(run) -> str | None:
    """Heurística leve pra um label humano-legível do progresso atual."""
    rm = run.runtime_metrics or {}
    cp = rm.get("candidates_processed")
    pp = rm.get("progress_pct")
    if cp is not None and pp is not None:
        return f"Processando {cp} candidato(s) — {pp}%"
    if cp is not None:
        return f"Processando {cp} candidato(s)"
    if pp is not None:
        return f"Progresso: {pp}%"
    results = run.results or {}
    resp = results.get("response")
    if resp:
        return resp[:120]
    return None


@router.get("/active-summary", response_model=ActiveSummaryResponse)
async def get_active_agents_summary(
    surface: _AgentsCardSurface = Query(
        default="decidir",
        description="Afinidade UI (decidir=mix; pool/job/funil filtram por target_type).",
    ),
    limit: int = Query(default=5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(require_company_id),
) -> ActiveSummaryResponse:
    """Onda 2 B1 — top N agentes ativos (Decidir + indicador global).

    Agrega `pool_agent_runs` da última hora, top-N por last_activity desc.
    Multi-tenancy fail-closed via require_company_id.

    surface canonical mapping:
      - decidir / all  -> mix completo
      - pool           -> target_type=talent_pool
      - job            -> target_type=job (Onda 2/3 wiring)
      - funil          -> target_type=pipeline_stage (Onda 2 B2)
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=1)

    # 1) Pegar runs RUNNING + recentes (excluindo orphans), ordenados por última atividade.
    # C1.6a (2026-05-29): multi-surface — surfaca runs de assignment E deployment.
    base_stmt = _studio_runs_select().where(
        and_(
            _PoolAgentRun.company_id == company_id,
            _PoolAgentRun.started_at != None,  # noqa: E711
            _PoolAgentRun.started_at > cutoff,
        )
    ).order_by(desc(_PoolAgentRun.started_at))
    result = await db.execute(base_stmt)
    rows = result.all()

    # 2) Normalizar cada row pra (run, assignment, agent, pool, deployment) e
    #    dedupe por agent_id, manter o run mais recente (já ordenado desc).
    seen_agents: set[str] = set()
    dedup_rows: list[tuple] = []
    for row in rows:
        run, assignment, agent_a, pool, deployment, agent_d = row
        agent = _resolve_agent(agent_a, agent_d)
        if agent is None:
            continue
        aid = str(agent.id)
        if aid in seen_agents:
            continue
        seen_agents.add(aid)
        dedup_rows.append((run, assignment, agent, pool, deployment))

    # 3) Filtrar por surface (canonical mapping). Agora vale pra TODOS os
    #    target_types — job/funil/pool surfaçam via deployment_id.
    target_filter = _SURFACE_TO_TARGET_TYPE.get(surface)
    filtered_rows: list[tuple] = []
    for row in dedup_rows:
        _run, assignment, _agent, pool, deployment = row
        target_type, _tid, _tname = _resolve_target_info(
            assignment, pool, deployment
        )
        if target_filter is not None and target_type != target_filter:
            continue
        filtered_rows.append(row)

    # 4) Running count = total ÚNICOS após filtro de surface (não limitado).
    running_count = sum(
        1 for row in filtered_rows if row[0].status == "running"
    )

    # 5) Aplicar limit pra montar items.
    top_rows = filtered_rows[:limit]

    # 6) Pending approvals — agregar por agent_id em UMA query (evita N+1).
    agent_ids = [str(row[2].id) for row in top_rows]
    pending_by_agent: dict[str, int] = {}
    if agent_ids:
        try:
            approvals_stmt = (
                select(ApprovalRequest.target_id, ApprovalRequest.id)
                .where(
                    and_(
                        ApprovalRequest.company_id == company_id,
                        ApprovalRequest.status == ApprovalStatus.PENDING.value,
                        ApprovalRequest.target_type == "custom_agent",
                        ApprovalRequest.target_id.in_(agent_ids),
                    )
                )
            )
            approvals_result = await db.execute(approvals_stmt)
            for row in approvals_result.fetchall():
                aid = str(row[0])
                pending_by_agent[aid] = pending_by_agent.get(aid, 0) + 1
        except Exception:
            # Defense: approvals query schema drift não deve quebrar o endpoint.
            # Endpoint serve UI cyan-dot — failure recoverable retornando 0.
            logger.warning(
                "[active-summary] pending approvals query failed", exc_info=True
            )

    # 7) Montar response items.
    items: list[ActiveAgentSummary] = []
    for run, assignment, agent, pool, deployment in top_rows:
        target_type, target_id, target_name = _resolve_target_info(
            assignment, pool, deployment
        )
        aid = str(agent.id)
        pending = pending_by_agent.get(aid, 0)

        if run.status == "running":
            status_mapped: Literal["running", "idle", "pending_approval"] = "running"
        elif pending > 0:
            status_mapped = "pending_approval"
        else:
            status_mapped = "idle"

        items.append(
            ActiveAgentSummary(
                agent_id=aid,
                agent_name=agent.name,
                agent_category=getattr(agent, "category", None) or "general",
                status=status_mapped,
                target_type=target_type,
                target_id=target_id,
                target_name=target_name,
                last_action_label=_build_action_label(run),
                last_execution_id=str(run.id),
                pending_approvals_count=pending,
                last_activity_at=run.started_at,
            )
        )

    return ActiveSummaryResponse(running_count=running_count, items=items)


# ============================================================================
# Onda 2 B3 — /agent-monitoring/candidate/{id}/touches (2026-05-28)
# ============================================================================
# Alimenta o icone "candidato tocado por agente nas últimas 24h" no card
# de candidato (kanban + preview).
#
# MVP scope: deriva touches de pool_agent_runs.results JSONB procurando
# arrays candidate_ids. Forward-compat — quando agents canonical popularem
# este campo, endpoint passa a retornar dados sem mudanca de contrato.
#
# Multi-tenancy fail-closed: lookup do candidate FILTRA por company_id;
# se candidate.company_id != current_company_id, retorna 404 (nao vaza).
# ============================================================================

from lia_models.candidate import Candidate as _Candidate


class CandidateTouch(_WeDoBaseModel):
    execution_id: str
    agent_id: str
    agent_name: str
    action_type: str
    timestamp: datetime
    outcome: str | None = None


class CandidateTouchesResponse(_WeDoBaseModel):
    candidate_id: str
    touch_count: int
    last_touch_at: datetime | None = None
    touches: list[CandidateTouch]


def _extract_candidate_action(results: dict | None) -> tuple[str, str | None]:
    """Heurística MVP: deriva action_type + outcome do results JSONB.

    Forward-compat: quando agents canonical populardem com structured
    fields, este helper passa a ser source-of-truth. Hoje default é
    "processed" / None.
    """
    if not isinstance(results, dict):
        return "processed", None
    action = results.get("action_type") or "processed"
    outcome = results.get("outcome")
    return str(action), str(outcome) if outcome is not None else None


@router.get(
    "/candidate/{candidate_id}/touches",
    response_model=CandidateTouchesResponse,
)
async def list_candidate_touches(
    candidate_id: str,
    since_hours: int = Query(default=24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(require_company_id),
) -> CandidateTouchesResponse:
    """Onda 2 B3 — runs de agentes que tocaram este candidato.

    MVP lê de `pool_agent_runs.results[candidate_ids]` (JSONB array
    containment). Forward-compat: quando agents canonical popularem
    estruturadamente, endpoint só fica mais rico — contrato estavel.

    Multi-tenancy fail-closed: lookup do candidate FILTRA por company_id.
    Tenant cross-access => 404 (nao vaza existencia de candidato).
    """
    # 1) Validar candidate pertence ao tenant.
    candidate_stmt = (
        select(_Candidate)
        .where(
            and_(
                _Candidate.id == candidate_id,
                _Candidate.company_id == company_id,
            )
        )
        .limit(1)
    )
    candidate_result = await db.execute(candidate_stmt)
    candidate = candidate_result.scalar_one_or_none()
    if candidate is None:
        # Fail-closed: nao distinguir "nao existe" de "outro tenant".
        raise HTTPException(
            status_code=404,
            detail="Candidato nao encontrado ou pertence a outro tenant.",
        )

    # 2) Buscar runs no window since_hours que mencionem este candidate_id.
    cutoff = datetime.now(timezone.utc) - timedelta(hours=since_hours)

    # JSONB containment: results @> {"candidate_ids": ["<id>"]}.
    # MVP usa filter Python-side defensivo (mock-friendly) + filter SQL window.
    # C1.6a (2026-05-29): multi-surface — runs de deployment (job/funil) que
    # tocaram este candidato também aparecem.
    runs_stmt = _studio_runs_select().where(
        and_(
            _PoolAgentRun.company_id == company_id,
            _PoolAgentRun.started_at != None,  # noqa: E711
            _PoolAgentRun.started_at > cutoff,
        )
    ).order_by(desc(_PoolAgentRun.started_at))
    runs_result = await db.execute(runs_stmt)
    rows = runs_result.all()

    # 3) Filter Python-side: results.candidate_ids inclui o candidate_id.
    touches: list[CandidateTouch] = []
    cid_str = str(candidate_id)
    for row in rows:
        run, _assignment, agent_a, _pool, _deployment, agent_d = row
        agent = _resolve_agent(agent_a, agent_d)
        if agent is None:
            continue
        results = run.results or {}
        cids = results.get("candidate_ids") or []
        if cid_str not in [str(c) for c in cids]:
            continue
        action_type, outcome = _extract_candidate_action(results)
        touches.append(
            CandidateTouch(
                execution_id=str(run.id),
                agent_id=str(agent.id),
                agent_name=agent.name,
                action_type=action_type,
                timestamp=run.started_at,
                outcome=outcome,
            )
        )

    last_touch_at = touches[0].timestamp if touches else None
    return CandidateTouchesResponse(
        candidate_id=str(candidate_id),
        touch_count=len(touches),
        last_touch_at=last_touch_at,
        touches=touches,
    )


# ============================================================================
# Onda C4.2 — /agent-monitoring/daily-digest (2026-05-29)
# ============================================================================
# Morning Brief / Daily Digest — "o que aconteceu enquanto eu não estava".
# Curado por relevância: os top N eventos mais dignos de atenção do recrutador
# nas últimas 24h (configurável via since_hours).
#
# Fontes (multi-surface via _studio_runs_select — assignment OU deployment):
#   - agent_error        : runs status in (error, timeout, cancelled)
#   - pending_approval   : ApprovalRequest PENDING (target_type=custom_agent)
#   - decision_approved  : runs success com results.approved_count > 0
#   - candidates_surfaced: runs success com results.candidate_ids não-vazio
#   - high_cost          : runs com runtime_metrics.cost_usd acima de threshold
#
# Relevância (ordem decrescente de prioridade — sort key):
#   agent_error > pending_approval > decision_approved (celebration) >
#   candidates_surfaced > high_cost (info)
#
# Multi-tenancy fail-closed: company_id do JWT, todo SELECT filtra company_id.
# canonical-fix: reusa _studio_runs_select() (C1.6a) + _resolve_agent /
# _resolve_target_info (multi-surface) + lógica candidate_ids de C4.1.
# ============================================================================

_DigestKind = Literal[
    "decision_approved",
    "candidates_surfaced",
    "agent_error",
    "pending_approval",
    "high_cost",
]
_DigestSeverity = Literal["info", "attention", "celebration"]

# Threshold canonical de "execução cara" (USD). Acima disso vira item de digest.
# Escolha conservadora: a maioria das execuções LLM custa centavos; >$0.50
# numa única run sinaliza um job grande/caro que merece visibilidade.
_HIGH_COST_THRESHOLD_USD = 0.50

# Peso de relevância por kind — menor = mais relevante (sort ascendente).
# Errors primeiro (precisa ação), depois aprovações pendentes (bloqueiam o
# recrutador), depois celebrações (aprovações concluídas), surfaced, e por fim
# high_cost (informativo).
_DIGEST_RELEVANCE_WEIGHT: dict[str, int] = {
    "agent_error": 0,
    "pending_approval": 1,
    "decision_approved": 2,
    "candidates_surfaced": 3,
    "high_cost": 4,
}

_DIGEST_SEVERITY_BY_KIND: dict[str, _DigestSeverity] = {
    "agent_error": "attention",
    "pending_approval": "attention",
    "decision_approved": "celebration",
    "candidates_surfaced": "celebration",
    "high_cost": "info",
}


class DigestItem(_WeDoBaseModel):
    kind: _DigestKind
    agent_id: str
    agent_name: str
    summary: str
    target_type: str | None = None
    target_name: str | None = None
    count: int | None = None
    severity: _DigestSeverity
    execution_id: str | None = None
    timestamp: datetime


class DailyDigestResponse(_WeDoBaseModel):
    period_hours: int
    generated_at: datetime
    items: list[DigestItem]
    total_runs: int
    total_candidates_processed: int


def _extract_approved_count(results: dict | None) -> int:
    """Quantos candidatos foram aprovados nesta run.

    Forward-compat com C4.1: agents canonical populam `approved_count` OU
    `approved_candidate_ids` em results. Sem isso, retorna 0.
    """
    if not isinstance(results, dict):
        return 0
    ac = results.get("approved_count")
    if isinstance(ac, int) and ac > 0:
        return ac
    approved_ids = results.get("approved_candidate_ids")
    if isinstance(approved_ids, list):
        return len(approved_ids)
    return 0


def _extract_surfaced_count(results: dict | None) -> int:
    """Quantos candidatos foram surfaced (results.candidate_ids — lógica C4.1)."""
    if not isinstance(results, dict):
        return 0
    cids = results.get("candidate_ids")
    if isinstance(cids, list):
        return len(cids)
    return 0


def _digest_target_phrase(target_type: str | None, target_name: str | None) -> str:
    """Sufixo humano do summary: ' · <target_name>' quando houver nome."""
    if target_name:
        return f" · {target_name}"
    return ""


@router.get("/daily-digest", response_model=DailyDigestResponse)
async def get_daily_digest(
    since_hours: int = Query(default=24, ge=1, le=168),
    limit: int = Query(default=8, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(require_company_id),
) -> DailyDigestResponse:
    """Onda C4.2 — Morning Brief: top eventos relevantes das últimas N horas.

    Curado por relevância (errors > pending > celebrations > surfaced > info),
    limitado a `limit` items. Multi-tenancy fail-closed via require_company_id.

    Multi-surface: runs de assignment (pool legacy) E deployment (job/funil/
    pool/lista) entram no digest via _studio_runs_select (C1.6a).
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=since_hours)

    # 1) Runs da janela (multi-surface). Driver tenant-scoped (fail-closed).
    runs_stmt = (
        _studio_runs_select()
        .where(
            and_(
                _PoolAgentRun.company_id == company_id,
                _PoolAgentRun.created_at != None,  # noqa: E711
                _PoolAgentRun.created_at > cutoff,
            )
        )
        .order_by(desc(_PoolAgentRun.created_at))
    )
    runs_result = await db.execute(runs_stmt)
    rows = runs_result.all()

    candidate_items: list[DigestItem] = []
    total_runs = 0
    total_candidates_processed = 0

    for row in rows:
        run, assignment, agent_a, pool, deployment, agent_d = row
        agent = _resolve_agent(agent_a, agent_d)
        if agent is None:
            continue
        total_runs += 1
        target_type, _target_id, target_name = _resolve_target_info(
            assignment, pool, deployment
        )
        results = run.results or {}
        rm = run.runtime_metrics or {}

        cp = rm.get("candidates_processed")
        if isinstance(cp, int):
            total_candidates_processed += cp

        agent_id = str(agent.id)
        agent_name = agent.name
        run_id = str(run.id)
        ts = run.finished_at or run.started_at or run.created_at
        suffix = _digest_target_phrase(target_type, target_name)

        # error (qualquer status de falha)
        if run.status in ("error", "timeout", "cancelled"):
            candidate_items.append(
                DigestItem(
                    kind="agent_error",
                    agent_id=agent_id,
                    agent_name=agent_name,
                    summary=f"{agent_name} teve uma falha de execução{suffix}",
                    target_type=target_type,
                    target_name=target_name,
                    count=None,
                    severity=_DIGEST_SEVERITY_BY_KIND["agent_error"],
                    execution_id=run_id,
                    timestamp=ts,
                )
            )
            continue

        if run.status != "success":
            # queued/running não geram item de digest (ainda em andamento).
            continue

        # decision_approved (celebração)
        approved = _extract_approved_count(results)
        if approved > 0:
            candidate_items.append(
                DigestItem(
                    kind="decision_approved",
                    agent_id=agent_id,
                    agent_name=agent_name,
                    summary=(
                        f"{agent_name} aprovou {approved} candidato(s){suffix}"
                    ),
                    target_type=target_type,
                    target_name=target_name,
                    count=approved,
                    severity=_DIGEST_SEVERITY_BY_KIND["decision_approved"],
                    execution_id=run_id,
                    timestamp=ts,
                )
            )
            continue

        # candidates_surfaced (lógica C4.1 — results.candidate_ids)
        surfaced = _extract_surfaced_count(results)
        if surfaced > 0:
            candidate_items.append(
                DigestItem(
                    kind="candidates_surfaced",
                    agent_id=agent_id,
                    agent_name=agent_name,
                    summary=(
                        f"{agent_name} encontrou {surfaced} candidato(s) novo(s)"
                        f"{suffix}"
                    ),
                    target_type=target_type,
                    target_name=target_name,
                    count=surfaced,
                    severity=_DIGEST_SEVERITY_BY_KIND["candidates_surfaced"],
                    execution_id=run_id,
                    timestamp=ts,
                )
            )
            continue

        # high_cost (informativo)
        cost = rm.get("cost_usd")
        if isinstance(cost, (int, float)) and cost >= _HIGH_COST_THRESHOLD_USD:
            candidate_items.append(
                DigestItem(
                    kind="high_cost",
                    agent_id=agent_id,
                    agent_name=agent_name,
                    summary=(
                        f"{agent_name} consumiu ${cost:.2f} numa execução{suffix}"
                    ),
                    target_type=target_type,
                    target_name=target_name,
                    count=None,
                    severity=_DIGEST_SEVERITY_BY_KIND["high_cost"],
                    execution_id=run_id,
                    timestamp=ts,
                )
            )

    # 2) Aprovações pendentes — agregadas por agente (uma query, evita N+1).
    #    Não dependem de run; surfaçam tudo que aguarda o recrutador.
    try:
        approvals_stmt = (
            select(
                ApprovalRequest.target_id,
                ApprovalRequest.target_name,
                ApprovalRequest.created_at,
            )
            .where(
                and_(
                    ApprovalRequest.company_id == company_id,
                    ApprovalRequest.status == ApprovalStatus.PENDING.value,
                    ApprovalRequest.target_type == "custom_agent",
                )
            )
            .order_by(desc(ApprovalRequest.created_at))
        )
        approvals_result = await db.execute(approvals_stmt)
        approval_rows = approvals_result.fetchall()
    except Exception:
        # Defense: schema drift em approvals não deve quebrar o digest inteiro.
        logger.warning(
            "[daily-digest] pending approvals query failed", exc_info=True
        )
        approval_rows = []

    pending_by_agent: dict[str, dict] = {}
    for ar in approval_rows:
        aid = str(ar[0]) if ar[0] is not None else None
        if aid is None:
            continue
        entry = pending_by_agent.setdefault(
            aid, {"count": 0, "name": ar[1], "ts": ar[2]}
        )
        entry["count"] += 1

    for aid, entry in pending_by_agent.items():
        ts = entry["ts"]
        if ts is not None and ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        candidate_items.append(
            DigestItem(
                kind="pending_approval",
                agent_id=aid,
                agent_name=entry["name"] or "Agente",
                summary=(
                    f"{entry['count']} aprovação(ões) aguardando você"
                ),
                target_type="custom_agent",
                target_name=entry["name"],
                count=entry["count"],
                severity=_DIGEST_SEVERITY_BY_KIND["pending_approval"],
                execution_id=None,
                timestamp=ts or datetime.now(timezone.utc),
            )
        )

    # 3) Ordenar por relevância (weight asc) e desempate por recência (desc).
    candidate_items.sort(
        key=lambda it: (
            _DIGEST_RELEVANCE_WEIGHT.get(it.kind, 99),
            -(it.timestamp.timestamp() if it.timestamp else 0),
        )
    )

    return DailyDigestResponse(
        period_hours=since_hours,
        generated_at=datetime.now(timezone.utc),
        items=candidate_items[:limit],
        total_runs=total_runs,
        total_candidates_processed=total_candidates_processed,
    )
