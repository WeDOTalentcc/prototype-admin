"""
Proactive Actions API - Endpoints for proactive LIA suggestions.
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/proactive-actions", tags=["Proactive Actions"])


class ActionResponse(BaseModel):
    id: str
    company_id: str
    action_type: str
    title: str
    description: str
    priority: str
    status: str
    suggested_action: Dict[str, Any] = {}
    trigger_reason: Optional[str] = None
    auto_executable: bool = False
    created_at: Optional[str] = None
    expires_at: Optional[str] = None


class AcceptRejectRequest(BaseModel):
    user_id: str


class AcceptRejectResponse(BaseModel):
    success: bool
    action_id: str
    message: str = ""
    execution_result: Optional[Dict[str, Any]] = None


class ProactiveFeedItem(BaseModel):
    id: str
    title: str
    message: str
    severity: str
    action_type: str
    suggested_action: Dict[str, Any] = {}
    action_label: str = ""
    created_at: str
    expires_at: Optional[str] = None


class PlanTemplateResponse(BaseModel):
    name: str
    display_name: str
    description: str
    steps_count: int
    retry_policy: Dict[str, Any]


class MonitorTriggerResponse(BaseModel):
    success: bool
    events_count: int
    actions_created: int
    notifications_sent: int


@router.get("/pending/{company_id}", response_model=List[ActionResponse])
async def get_pending_actions(
    company_id: str,
    limit: int = Query(default=10, le=50),
):
    """Get pending proactive actions for a company."""
    try:
        from app.domains.automation.services.autonomous_agent_service import AutonomousAgentService
        service = AutonomousAgentService()
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


@router.get("/history/{company_id}", response_model=List[ActionResponse])
async def get_action_history(
    company_id: str,
    status: str = Query(default="accepted"),
    limit: int = Query(default=20, le=100),
):
    """Get action history (accepted/rejected) for a company."""
    try:
        from app.domains.automation.services.autonomous_agent_service import AutonomousAgentService
        service = AutonomousAgentService()
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
async def accept_action(action_id: str, request: AcceptRejectRequest):
    """Accept a proactive action suggestion."""
    try:
        from app.domains.automation.services.autonomous_agent_service import AutonomousAgentService
        service = AutonomousAgentService()
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
async def reject_action(action_id: str, request: AcceptRejectRequest):
    """Reject a proactive action suggestion."""
    try:
        from app.domains.automation.services.autonomous_agent_service import AutonomousAgentService
        service = AutonomousAgentService()
        result = await service.reject_action(action_id, request.user_id)
        
        return AcceptRejectResponse(
            success=result.get("success", False),
            action_id=action_id,
            message="Ação rejeitada" if result.get("success") else result.get("error", "Erro"),
        )
    except Exception as e:
        logger.error(f"Error rejecting action: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feed/{company_id}", response_model=List[ProactiveFeedItem])
async def get_proactive_feed(
    company_id: str,
    limit: int = Query(default=10, le=30),
):
    """
    Get proactive feed for chat integration.
    Returns pending actions formatted as chat-ready suggestions.
    """
    try:
        from app.domains.automation.services.autonomous_agent_service import AutonomousAgentService
        service = AutonomousAgentService()
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
async def trigger_pipeline_monitor(company_id: str):
    """
    Manually trigger pipeline monitor for a specific company.
    Useful for testing and admin purposes.
    """
    try:
        from app.domains.automation.services.pipeline_monitor import PipelineMonitor
        from app.domains.automation.services.event_action_connector import event_action_connector
        from app.core.database import async_session_factory
        
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


@router.get("/plan-templates", response_model=List[PlanTemplateResponse])
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
