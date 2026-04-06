"""
Agent Monitoring API Endpoints
Provides real-time metrics, health scores, and activity tracking for AI agents.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.analytics.services.agent_monitoring_service import AgentMonitoringService

router = APIRouter(prefix="/agent-monitoring", tags=["Agent Monitoring"])


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


class AlertResponse(BaseModel):
    id: str
    type: str
    agent_id: str
    agent_name: str
    title: str
    description: str
    created_at: str | None = None
    severity: str


class LogActivityRequest(BaseModel):
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
async def get_global_metrics(db: AsyncSession = Depends(get_db)):
    """Get global metrics across all agents."""
    service = AgentMonitoringService(db)
    metrics = await service.get_global_metrics()
    return GlobalMetricsResponse(**metrics)


@router.get("/agents", response_model=list[AgentSummaryResponse])
async def get_all_agents_summary(db: AsyncSession = Depends(get_db)):
    """Get summary for all agents."""
    service = AgentMonitoringService(db)
    summaries = await service.get_all_agents_summary()
    return [AgentSummaryResponse(**s) for s in summaries]


@router.get("/agents/{agent_id}", response_model=AgentSummaryResponse)
async def get_agent_summary(agent_id: str, db: AsyncSession = Depends(get_db)):
    """Get summary for a specific agent."""
    service = AgentMonitoringService(db)
    summary = await service.get_agent_summary(agent_id)
    if not summary:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    return AgentSummaryResponse(**summary)


@router.get("/agents/{agent_id}/health", response_model=AgentHealthResponse)
async def get_agent_health(agent_id: str, db: AsyncSession = Depends(get_db)):
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
    db: AsyncSession = Depends(get_db)
):
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
    db: AsyncSession = Depends(get_db)
):
    """Get global activity feed with optional filters."""
    service = AgentMonitoringService(db)
    activities = await service.get_activity_feed(
        agent_id=agent_id,
        status=status,
        limit=limit,
        offset=offset
    )
    return [ActivityResponse(**a) for a in activities]


@router.get("/alerts", response_model=list[AlertResponse])
async def get_proactive_alerts(db: AsyncSession = Depends(get_db)):
    """Get current proactive alerts requiring attention."""
    service = AgentMonitoringService(db)
    alerts = await service.get_proactive_alerts()
    return [AlertResponse(**a) for a in alerts]


@router.post("/activities", response_model=ActivityResponse)
async def log_activity(request: LogActivityRequest, db: AsyncSession = Depends(get_db)):
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


@router.get("/domains/health")
async def get_domains_health(
    company_id: str = Query(..., description="ID da empresa"),
    days: int = Query(30, ge=1, le=90, description="Janela de análise em dias"),
):
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


@router.get("/domains/{domain}/metrics")
async def get_domain_metrics(
    domain: str,
    company_id: str = Query(..., description="ID da empresa"),
    days: int = Query(30, ge=1, le=90, description="Janela de análise em dias"),
):
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


@router.post("/seed-demo")
async def seed_demo_data(db: AsyncSession = Depends(get_db)):
    """Seed demo data for testing. Only use in development."""
    service = AgentMonitoringService(db)
    result = await service.seed_demo_data()
    return {
        "success": True,
        "message": f"Created {result['activities_created']} demo activities",
        **result
    }
