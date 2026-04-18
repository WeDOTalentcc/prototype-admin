"""
Proactive Actions API - Endpoints for proactive LIA suggestions.
"""
import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel

from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN
from app.domains.automation.services.autonomous_agent_service import AutonomousAgentService, get_autonomous_agent_service

logger = logging.getLogger(__name__)

# Task #458 — Same routing-shadowing blindagem applied to /job-vacancies in
# Task #455 is now applied here. Two layers of defense:
#   1. Every ``{*_id}`` path parameter is constrained to UUID-or-digit so a
#      future static sibling segment cannot be silently captured by an item
#      handler (e.g. ``/proactive-actions/insights`` vs an item route).
#   2. Collection-scoped routes are kept before item-scoped routes in the
#      final route list — the ordering is reasserted at the bottom of this
#      module so source-order regressions cannot reintroduce shadowing.
router = APIRouter(prefix="/proactive-actions", tags=["Proactive Actions"])

_DualId = Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)]


class ActionResponse(BaseModel):
    id: str
    company_id: str
    action_type: str
    title: str
    description: str
    priority: str
    status: str
    suggested_action: dict[str, Any] = {}
    trigger_reason: str | None = None
    auto_executable: bool = False
    created_at: str | None = None
    expires_at: str | None = None


class AcceptRejectRequest(BaseModel):
    user_id: str


class AcceptRejectResponse(BaseModel):
    success: bool
    action_id: str
    message: str = ""
    execution_result: dict[str, Any] | None = None


class ProactiveFeedItem(BaseModel):
    id: str
    title: str
    message: str
    severity: str
    action_type: str
    suggested_action: dict[str, Any] = {}
    action_label: str = ""
    created_at: str
    expires_at: str | None = None


class PlanTemplateResponse(BaseModel):
    name: str
    display_name: str
    description: str
    steps_count: int
    retry_policy: dict[str, Any]


class MonitorTriggerResponse(BaseModel):
    success: bool
    events_count: int
    actions_created: int
    notifications_sent: int


@router.get("/pending/{company_id}", response_model=list[ActionResponse])
async def get_pending_actions(
    company_id: _DualId,
    limit: int = Query(default=10, le=50),
    service: AutonomousAgentService = Depends(get_autonomous_agent_service),
):
    """Get pending proactive actions for a company."""
    try:
        actions = await service.get_pending_actions(company_id, limit=limit)
        
        return [
            ActionResponse(
                id=str(a.id),
                company_id=str(a.company_id),
                action_type=a.action_type or "",
                title=a.title or "",
                description=a.description or "",
                priority=a.priority or "normal",
                status=a.status or "pending",
                suggested_action=a.suggested_action or {},
                trigger_reason=a.trigger_reason,
                auto_executable=a.auto_executable or False,
                created_at=a.created_at.isoformat() if a.created_at else None,
                expires_at=a.expires_at.isoformat() if a.expires_at else None,
            )
            for a in actions
        ]
    except Exception as e:
        logger.error(f"Error getting pending actions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{company_id}", response_model=list[ActionResponse])
async def get_action_history(
    company_id: _DualId,
    status: str = Query(default="accepted"),
    limit: int = Query(default=20, le=100),
    service: AutonomousAgentService = Depends(get_autonomous_agent_service),
):
    """Get action history (accepted/rejected) for a company."""
    try:
        actions = await service.get_actions_by_status(company_id, status=status, limit=limit)
        
        return [
            ActionResponse(
                id=str(a.id),
                company_id=str(a.company_id),
                action_type=a.action_type or "",
                title=a.title or "",
                description=a.description or "",
                priority=a.priority or "normal",
                status=a.status or "",
                suggested_action=a.suggested_action or {},
                trigger_reason=a.trigger_reason,
                auto_executable=a.auto_executable or False,
                created_at=a.created_at.isoformat() if a.created_at else None,
                expires_at=a.expires_at.isoformat() if a.expires_at else None,
            )
            for a in actions
        ]
    except Exception as e:
        logger.error(f"Error getting action history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/accept/{action_id}", response_model=AcceptRejectResponse)
async def accept_action(
    action_id: _DualId,
    request: AcceptRejectRequest,
    service: AutonomousAgentService = Depends(get_autonomous_agent_service),
):
    """Accept a proactive action suggestion."""
    try:
        result = await service.accept_action(action_id, request.user_id)
        
        return AcceptRejectResponse(
            success=result.get("success", False),
            action_id=action_id,
            message="Ação aceita com sucesso" if result.get("success") else result.get("error", "Erro"),
            execution_result=result.get("execution_result"),
        )
    except Exception as e:
        logger.error(f"Error accepting action: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reject/{action_id}", response_model=AcceptRejectResponse)
async def reject_action(
    action_id: _DualId,
    request: AcceptRejectRequest,
    service: AutonomousAgentService = Depends(get_autonomous_agent_service),
):
    """Reject a proactive action suggestion."""
    try:
        result = await service.reject_action(action_id, request.user_id)
        
        return AcceptRejectResponse(
            success=result.get("success", False),
            action_id=action_id,
            message="Ação rejeitada" if result.get("success") else result.get("error", "Erro"),
        )
    except Exception as e:
        logger.error(f"Error rejecting action: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feed/{company_id}", response_model=list[ProactiveFeedItem])
async def get_proactive_feed(
    company_id: _DualId,
    limit: int = Query(default=10, le=30),
    service: AutonomousAgentService = Depends(get_autonomous_agent_service),
):
    """
    Get proactive feed for chat integration.
    Returns pending actions formatted as chat-ready suggestions.
    """
    try:
        actions = await service.get_pending_actions(company_id, limit=limit)
        
        severity_map = {
            "high": "urgent",
            "normal": "warning",
            "low": "info",
        }
        
        return [
            ProactiveFeedItem(
                id=str(a.id),
                title=a.title or "",
                message=a.description or "",
                severity=severity_map.get(a.priority, "info"),
                action_type=a.action_type or "",
                suggested_action=a.suggested_action or {},
                action_label=(a.suggested_action or {}).get("action_label", "Executar"),
                created_at=a.created_at.isoformat() if a.created_at else "",
                expires_at=a.expires_at.isoformat() if a.expires_at else None,
            )
            for a in actions
        ]
    except Exception as e:
        logger.error(f"Error getting proactive feed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger-monitor/{company_id}", response_model=MonitorTriggerResponse)
async def trigger_pipeline_monitor(company_id: _DualId):
    """
    Manually trigger pipeline monitor for a specific company.
    Useful for testing and admin purposes.
    """
    try:
        from app.core.database import async_session_factory
        from app.domains.automation.services.event_action_connector import event_action_connector
        from app.domains.automation.services.pipeline_monitor import PipelineMonitor
        
        monitor = PipelineMonitor()
        async with async_session_factory() as db:
            events = await monitor.scan_company(company_id, db)
        
        stats = {"actions_created": 0, "notifications_sent": 0}
        if events:
            stats = await event_action_connector.process_events(events)
        
        return MonitorTriggerResponse(
            success=True,
            events_count=len(events),
            actions_created=stats.get("actions_created", 0),
            notifications_sent=stats.get("notifications_sent", 0),
        )
    except Exception as e:
        logger.error(f"Error triggering monitor: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/plan-templates", response_model=list[PlanTemplateResponse])
async def list_plan_templates():
    """List available plan templates for multi-step actions."""
    try:
        from app.shared.execution.plan_templates import PlanTemplateRegistry
        
        templates = []
        for name in PlanTemplateRegistry.get_template_names():
            template = PlanTemplateRegistry.get_template(name)
            if template:
                templates.append(PlanTemplateResponse(
                    name=name,
                    display_name=template["name"],
                    description=template["description"],
                    steps_count=len(template["steps"]),
                    retry_policy=template["retry_policy"],
                ))
        
        return templates
    except Exception as e:
        logger.error(f"Error listing templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# D8 — Proactive Insights para Kanban
class ProactiveInsight(BaseModel):
    id: str
    title: str
    message: str
    urgency: str  # "low" | "normal" | "high" | "urgent"
    type: str
    action_url: str | None = None
    created_at: str


@router.get("/insights", response_model=list[ProactiveInsight])
async def get_proactive_insights(
    company_id: str = Query(...),
    job_id: str | None = Query(default=None),
    limit: int = Query(default=5, le=20),
    service: AutonomousAgentService = Depends(get_autonomous_agent_service),
):
    # If service is a Depends object (test calling directly), create a real instance
    if not hasattr(service, 'get_pending_actions'):
        from app.domains.automation.services.autonomous_agent_service import AutonomousAgentService as _AAS
        service = _AAS()
    """
    Retorna insights proativos da LIA para o Kanban.
    Filtra por job_id quando fornecido.
    """
    try:
        actions = await service.get_pending_actions(company_id, limit=limit * 2)

        results = []
        for a in actions:
            sa = a.suggested_action or {}
            if job_id and sa.get("job_id") and sa["job_id"] != job_id:
                continue
            results.append(
                ProactiveInsight(
                    id=str(a.id),
                    title=a.title or "",
                    message=a.description or "",
                    urgency=a.priority or "normal",
                    type=a.action_type or "general",
                    action_url=sa.get("action_url"),
                    created_at=a.created_at.isoformat() if a.created_at else "",
                )
            )
            if len(results) >= limit:
                break

        return results
    except Exception as exc:
        logger.warning("Error getting proactive insights: %s", exc)
        return []


# ---------------------------------------------------------------------------
# Routing invariant (Task #458) — collection-scoped routes before item routes.
# Combined with ``Path(pattern=DUAL_ID_PATH_PATTERN)`` on every ``{*_id}``,
# this is the same blindagem applied to /job-vacancies in Task #455.
# ---------------------------------------------------------------------------
from app.api.v1._path_patterns import reorder_collection_before_item as _reorder

_reorder(router)
