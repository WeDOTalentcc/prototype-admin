"""
Notifications API endpoints.

Provides endpoints for:
- Listing notifications (bell/in-app)
- Chat queue notifications
- Marking as read
- Dismissing notifications
- Getting notification summary
- Multi-channel notification sending
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.dependencies import get_notifications_repo
from app.repositories.notifications_repository import NotificationsRepository
from app.services.notification_service import (
    NotificationChannel,
    NotificationType,
    ProactiveNotificationType,
)
from app.domains.communication.services.email_service import EmailService, get_email_service
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item
from app.core.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/notifications", tags=["notifications"])


class CreateNotificationRequest(WeDoBaseModel):
    """Request model for creating a notification."""
    user_id: str
    title: str
    message: str | None = None
    notification_type: str = "info"
    category: str | None = None
    source_agent: str | None = None
    related_job_id: str | None = None
    related_candidate_id: str | None = None
    action_url: str | None = None
    action_label: str | None = None


class MultiChannelNotificationRequest(WeDoBaseModel):
    """Request model for sending multi-channel notifications."""
    user_id: str
    title: str
    message: str
    channels: list[str] = ["chat", "bell"]
    notification_type: str = "info"
    proactive_type: str | None = None
    priority: str = "normal"
    data: dict | None = None
    related_job_id: str | None = None
    related_candidate_id: str | None = None
    suggested_actions: list[str] | None = None
    thread_id: str | None = None


class MarkDeliveredRequest(WeDoBaseModel):
    """Request model for marking chat notifications as delivered."""
    notification_ids: list[str]


class RecruiterActionNotificationRequest(WeDoBaseModel):
    """Request model for sending recruiter notifications about job actions."""
    recruiter_ids: list[str]
    action: str  # pause, activate, unpublish, etc.
    job_titles: list[str]
    job_ids: list[str]
    channels: list[str] = ["bell"]  # email, teams, bell
    reason: str | None = None
    cancelled_screenings: bool = False
    cancelled_interviews: bool = False
    cancelled_tests: bool = False
    notified_candidates_count: int = 0
    performed_by: str | None = None


class TechnicalRequirement(BaseModel):
    name: str
    level: str
    required: bool = False

class BehavioralCompetency(BaseModel):
    name: str
    weight: str

class Language(BaseModel):
    name: str
    level: str

class SalaryRange(BaseModel):
    min: float | None = None
    max: float | None = None
    currency: str = "BRL"

class InterviewStageNotification(BaseModel):
    stageName: str
    order: int
    sla: int | None = None

class PublishingPlatforms(BaseModel):
    linkedin: bool = False
    indeed: bool = False
    website: bool = False

class JobCreatedNotificationRequest(WeDoBaseModel):
    """Request model for sending job created notifications (workplan format)."""
    job_id: str
    job_title: str
    department: str | None = None
    location: str | None = None
    work_model: str | None = None
    seniority_level: str | None = None
    job_description: str
    technical_requirements: list[TechnicalRequirement] = []
    behavioral_competencies: list[BehavioralCompetency] = []
    languages: list[Language] = []
    salary_range: SalaryRange | None = None
    benefits: list[str] = []
    deadline_screening: str
    deadline_shortlist: str
    deadline_closing: str
    interview_stages: list[InterviewStageNotification] = []
    publishing_platforms: PublishingPlatforms
    urgency_level: int = 3
    is_confidential: bool = False
    is_affirmative: bool = False
    recruiter_email: str
    recruiter_name: str | None = None
    manager_email: str | None = None
    manager_name: str | None = None
    channels: list[str] = ["email", "teams"]


@router.get("", response_model=None)
async def get_notifications(
    user_id: str = "default_user",
    unread_only: bool = False,
    category: str | None = None,
    notification_type: str | None = None,
    limit: int = 50,
    offset: int = 0,
    repo: NotificationsRepository = Depends(get_notifications_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get notifications for a user.
    """
    try:
        result = await repo.get_notifications(
            user_id=user_id,
            unread_only=unread_only,
            category=category,
            notification_type=notification_type,
            limit=limit,
            offset=offset,
        )
        return {
            "success": True,
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary", response_model=None)
async def get_notification_summary(
    user_id: str = "default_user",
    repo: NotificationsRepository = Depends(get_notifications_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get notification summary for header badge.
    """
    try:
        summary = await repo.get_notification_summary(user_id)
        return {
            "success": True,
            "data": summary
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting notification summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=None)
async def create_notification(
    request: CreateNotificationRequest,
    repo: NotificationsRepository = Depends(get_notifications_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Create a new notification.
    """
    try:
        notification_type_enum = NotificationType(request.notification_type) if request.notification_type in [t.value for t in NotificationType] else NotificationType.INFO

        notification = await repo.create_notification(
            user_id=request.user_id,
            title=request.title,
            message=request.message,
            notification_type=notification_type_enum,
            category=request.category,
            source_agent=request.source_agent,
            related_job_id=request.related_job_id,
            related_candidate_id=request.related_candidate_id,
            action_url=request.action_url,
            action_label=request.action_label,
        )
        return {
            "success": True,
            "data": notification
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{notification_id}/read", response_model=None)
async def mark_notification_as_read(
    notification_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    user_id: str = "default_user",
    repo: NotificationsRepository = Depends(get_notifications_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Mark a notification as read.
    """
    try:
        success = await repo.mark_as_read(notification_id, user_id)
        if success:
            return {"success": True, "message": "Notifica\u00e7\u00e3o marcada como lida"}
        else:
            raise HTTPException(status_code=404, detail="Notifica\u00e7\u00e3o n\u00e3o encontrada")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/read-all", response_model=None)
async def mark_all_as_read(
    user_id: str = "default_user",
    category: str | None = None,
    repo: NotificationsRepository = Depends(get_notifications_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Mark all notifications as read for a user.
    """
    try:
        count = await repo.mark_all_as_read(user_id, category)
        return {
            "success": True,
            "message": f"{count} notifica\u00e7\u00f5es marcadas como lidas"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking all as read: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{notification_id}/dismiss", response_model=None)
async def dismiss_notification(
    notification_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    user_id: str = "default_user",
    repo: NotificationsRepository = Depends(get_notifications_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Dismiss a notification.
    """
    try:
        success = await repo.dismiss_notification(notification_id, user_id)
        if success:
            return {"success": True, "message": "Notifica\u00e7\u00e3o descartada"}
        else:
            raise HTTPException(status_code=404, detail="Notifica\u00e7\u00e3o n\u00e3o encontrada")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error dismissing notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recruiter-action", response_model=None)
async def send_recruiter_action_notification(
    request: RecruiterActionNotificationRequest,
    repo: NotificationsRepository = Depends(get_notifications_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Send notifications to recruiters about job actions (pause, activate, unpublish, etc.).
    Supports multiple channels: email, teams, bell.
    """
    if not request.recruiter_ids:
        raise HTTPException(status_code=400, detail="recruiter_ids is required")
    if not request.job_titles or not request.job_ids:
        raise HTTPException(status_code=400, detail="job_titles and job_ids are required")
    if len(request.job_titles) != len(request.job_ids):
        raise HTTPException(status_code=400, detail="job_titles and job_ids must have the same length")

    try:
        action_labels = {
            "pause": "pausada",
            "activate": "reativada",
            "unpublish": "despublicada",
            "publish": "publicada",
            "close": "encerrada",
            "assign": "atribu\u00edda"
        }
        action_label = action_labels.get(request.action, request.action)

        jobs_text = ", ".join(request.job_titles[:3])
        if len(request.job_titles) > 3:
            jobs_text += f" e mais {len(request.job_titles) - 3}"

        title = f"Vaga {action_label}: {jobs_text}"

        message_parts = [f"A(s) vaga(s) {jobs_text} foi(ram) {action_label}."]

        if request.reason:
            message_parts.append(f"Motivo: {request.reason}")

        actions_taken = []
        if request.cancelled_screenings:
            actions_taken.append("tria\u00e7ens canceladas")
        if request.cancelled_interviews:
            actions_taken.append("entrevistas desmarcadas")
        if request.cancelled_tests:
            actions_taken.append("testes cancelados")

        if actions_taken:
            message_parts.append(f"Ações executadas: {', '.join(actions_taken)}.")

        if request.notified_candidates_count > 0:
            message_parts.append(f"{request.notified_candidates_count} candidato(s) notificado(s).")

        if request.performed_by:
            message_parts.append(f"A\u00e7\u00e3o realizada por: {request.performed_by}")

        message = " ".join(message_parts)

        channel_map = {
            "email": NotificationChannel.EMAIL,
            "teams": NotificationChannel.TEAMS,
            "bell": NotificationChannel.BELL
        }
        channels = [channel_map[c] for c in request.channels if c in channel_map]

        if not channels:
            channels = [NotificationChannel.BELL]

        results = []
        for recruiter_id in request.recruiter_ids:
            result = await repo.send_multi_channel_notification(
                user_id=recruiter_id,
                title=title,
                message=message,
                channels=channels,
                notification_type=NotificationType.INFO,
                priority="normal",
                data={
                    "action": request.action,
                    "job_ids": request.job_ids,
                    "job_titles": request.job_titles,
                    "reason": request.reason,
                    "cancelled_screenings": request.cancelled_screenings,
                    "cancelled_interviews": request.cancelled_interviews,
                    "cancelled_tests": request.cancelled_tests,
                    "notified_candidates_count": request.notified_candidates_count
                },
                related_job_id=request.job_ids[0] if request.job_ids else None,
            )
            results.append({"recruiter_id": recruiter_id, "result": result})

        return {
            "success": True,
            "message": f"Notifica\u00e7\u00e3o enviada para {len(request.recruiter_ids)} recrutador(es)",
            "data": {
                "notifications_sent": len(results),
                "channels": request.channels,
                "results": results
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending recruiter action notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/unread-count", response_model=None)
async def get_unread_count(
    user_id: str = "default_user",
    repo: NotificationsRepository = Depends(get_notifications_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get the count of unread notifications for the bell badge.
    """
    try:
        summary = await repo.get_notification_summary(user_id)
        return {
            "success": True,
            "data": {
                "unread_count": summary["unread_count"],
                "urgent_count": summary.get("urgent_count", 0)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting unread count: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat", response_model=None)
async def get_chat_notifications(
    user_id: str = "default_user",
    thread_id: str | None = None,
    undelivered_only: bool = True,
    limit: int = 20,
    repo: NotificationsRepository = Depends(get_notifications_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get pending chat notifications for inline display in chat.
    """
    try:
        result = await repo.get_chat_notifications(
            user_id=user_id,
            thread_id=thread_id,
            undelivered_only=undelivered_only,
            limit=limit,
        )
        return {
            "success": True,
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/{notification_id}/delivered", response_model=None)
async def mark_chat_notification_delivered(
    notification_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    user_id: str = "default_user",
    repo: NotificationsRepository = Depends(get_notifications_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Mark a single chat notification as delivered.
    """
    try:
        success = await repo.mark_chat_notification_delivered(notification_id, user_id)
        if success:
            return {"success": True, "message": "Notifica\u00e7\u00e3o marcada como entregue"}
        else:
            raise HTTPException(status_code=404, detail="Notifica\u00e7\u00e3o n\u00e3o encontrada")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking chat notification as delivered: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/delivered", response_model=None)
async def mark_chat_notifications_delivered(
    request: MarkDeliveredRequest,
    user_id: str = "default_user",
    repo: NotificationsRepository = Depends(get_notifications_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Mark multiple chat notifications as delivered.
    """
    try:
        count = await repo.mark_chat_notifications_delivered(request.notification_ids, user_id)
        return {
            "success": True,
            "message": f"{count} notifica\u00e7\u00f5es marcadas como entregues"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking chat notifications as delivered: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send", response_model=None)
async def send_multi_channel_notification(
    request: MultiChannelNotificationRequest,
    repo: NotificationsRepository = Depends(get_notifications_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Send a notification to multiple channels (chat, bell, teams).
    """
    try:
        channels = []
        for ch in request.channels:
            try:
                channels.append(NotificationChannel(ch))
            except ValueError:
                pass

        if not channels:
            channels = [NotificationChannel.CHAT, NotificationChannel.BELL]

        notification_type_enum = NotificationType.INFO
        if request.notification_type:
            try:
                notification_type_enum = NotificationType(request.notification_type)
            except ValueError:
                pass

        proactive_type_enum = None
        if request.proactive_type:
            try:
                proactive_type_enum = ProactiveNotificationType(request.proactive_type)
            except ValueError:
                pass

        result = await repo.send_multi_channel_notification(
            user_id=request.user_id,
            title=request.title,
            message=request.message,
            channels=channels,
            notification_type=notification_type_enum,
            proactive_type=proactive_type_enum,
            priority=request.priority,
            data=request.data,
            related_job_id=request.related_job_id,
            related_candidate_id=request.related_candidate_id,
            suggested_actions=request.suggested_actions,
            thread_id=request.thread_id,
        )

        return {
            "success": True,
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending multi-channel notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/proactive", response_model=None)
async def send_proactive_notification(
    user_id: str,
    proactive_type: str,
    title: str,
    message: str,
    data: dict | None = None,
    related_job_id: str | None = None,
    related_candidate_id: str | None = None,
    suggested_actions: list[str] | None = None,
    priority: str = "normal",
    repo: NotificationsRepository = Depends(get_notifications_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Send a proactive notification (convenience endpoint).
    Automatically sends to both chat and bell channels.
    """
    try:
        proactive_type_enum = None
        try:
            proactive_type_enum = ProactiveNotificationType(proactive_type)
        except ValueError:
            pass

        if not proactive_type_enum:
            raise HTTPException(status_code=400, detail=f"Invalid proactive_type: {proactive_type}")

        result = await repo.send_proactive_notification(
            user_id=user_id,
            proactive_type=proactive_type_enum,
            title=title,
            message=message,
            data=data,
            related_job_id=related_job_id,
            related_candidate_id=related_candidate_id,
            suggested_actions=suggested_actions,
            priority=priority,
        )

        return {
            "success": True,
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending proactive notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class ProactiveAlertCheckRequest(WeDoBaseModel):
    """Request model for triggering proactive alert check."""
    user_id: str


class UpdateThresholdRequest(WeDoBaseModel):
    """Request model for updating alert thresholds."""
    condition: str
    threshold_config: dict


@router.post("/proactive/check", response_model=None)
async def trigger_proactive_check(
    request: ProactiveAlertCheckRequest,
    repo: NotificationsRepository = Depends(get_notifications_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Trigger a proactive alert check for a user.

    This checks all conditions (pipeline, productivity, communication,
    predictive, system) and sends notifications for any triggered alerts.
    """
    try:
        triggered_alerts = await repo.check_proactive_conditions(
            user_id=request.user_id,
            company_id=company_id,
        )

        return {
            "success": True,
            "data": {
                "alerts_triggered": len(triggered_alerts),
                "alerts": [
                    {
                        "condition": (cond.value if hasattr(cond := alert.get("condition"), "value") else cond) if (cond := alert.get("condition")) is not None else None,
                        "category": (cat.value if hasattr(cat := alert.get("category"), "value") else cat) if (cat := alert.get("category")) is not None else None,
                        "title": alert.get("title"),
                        "severity": (sev.value if hasattr(sev := alert.get("severity"), "value") else str(sev)) if (sev := alert.get("severity")) is not None else None
                    }
                    for alert in triggered_alerts
                ]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering proactive check: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/proactive/history", response_model=None)
async def get_proactive_alert_history(
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get history of proactive actions/alerts for this company.
    B3 — reads from proactive_actions table (persistent, survives restart).
    """
    try:
        from lia_models.background_jobs import ProactiveAction
        from sqlalchemy import select, desc, cast, String as SAString

        stmt = (
            select(ProactiveAction)
            .where(cast(ProactiveAction.company_id, SAString) == str(company_id))
            .order_by(desc(ProactiveAction.created_at))
            .limit(limit)
        )
        result = await db.execute(stmt)
        actions = result.scalars().all()
        return {
            "success": True,
            "data": [a.to_dict() for a in actions],
            "count": len(actions),
            "source": "db",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting proactive alert history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/proactive/thresholds", response_model=None)
async def update_alert_threshold(
    request: UpdateThresholdRequest, 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Update threshold configuration for an alert condition.

    This allows customizing when alerts are triggered for
    each specific condition.
    """
    try:
        from app.domains.automation.services.proactive_alert_service import AlertCondition, proactive_alert_service

        try:
            condition = AlertCondition(request.condition)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid condition: {request.condition}. Valid conditions are: {[c.value for c in AlertCondition]}"
            )

        proactive_alert_service.update_threshold(condition, request.threshold_config)

        return {
            "success": True,
            "message": f"Threshold updated for {request.condition}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating threshold: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/proactive/thresholds", response_model=None)
async def get_alert_thresholds(company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get all alert threshold configurations.

    Returns the current configuration for all alert conditions
    including thresholds, cooldowns, and severity levels.
    """
    try:
        from app.domains.automation.services.proactive_alert_service import AlertCondition, ThresholdConfig

        thresholds = {}
        for condition in AlertCondition:
            config = ThresholdConfig.get_threshold(condition)
            thresholds[condition.value] = config

        return {
            "success": True,
            "data": thresholds
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting thresholds: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/job-created", response_model=None)
async def send_job_created_notification(
    request: JobCreatedNotificationRequest,
    email_svc: EmailService = Depends(get_email_service),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Send job created notification to recruiter and manager.

    Sends notification in workplan format with all job details including:
    - Job title, department, location
    - Technical requirements and behavioral competencies
    - Interview stages with SLAs
    - Deadlines (screening, shortlist, closing)
    - Publishing platforms

    Channels: email and/or teams
    Recipients: recruiter (required) and manager/hiring manager (optional)
    """
    try:
        from datetime import datetime

        from app.domains.communication.services.teams_service import teams_service

        notifications_sent = {
            "recruiter": {"email": False, "teams": False},
            "manager": {"email": False, "teams": False}
        }
        errors = []

        urgency_labels = {1: "Muito Baixa", 2: "Baixa", 3: "M\u00e9dia", 4: "Alta", 5: "Urgente"}
        urgency_label = urgency_labels.get(request.urgency_level, "M\u00e9dia")

        tech_reqs_list = "\n".join([
            f"  • {r.name} ({r.level})" + (" - Obrigatório" if r.required else "")
            for r in request.technical_requirements
        ]) if request.technical_requirements else "  Nenhum definido"

        competencies_list = "\n".join([
            f"  \u2022 {c.name} (Peso: {c.weight})"
            for c in request.behavioral_competencies
        ]) if request.behavioral_competencies else "  Nenhum definido"

        languages_list = ", ".join([
            f"{l.name} ({l.level})" for l in request.languages
        ]) if request.languages else "N\u00e3o especificado"

        benefits_list = ", ".join(request.benefits) if request.benefits else "A definir"

        stages_list = "\n".join([
            f"  {s.order}. {s.stageName}" + (f" (SLA: {s.sla} dias)" if s.sla else "")
            for s in request.interview_stages
        ]) if request.interview_stages else "  Pipeline padr\u00e3o"

        platforms = []
        if request.publishing_platforms.linkedin:
            platforms.append("LinkedIn")
        if request.publishing_platforms.indeed:
            platforms.append("Indeed")
        if request.publishing_platforms.website:
            platforms.append("Website")
        platforms_text = ", ".join(platforms) if platforms else "Nenhuma"

        salary_text = "A definir"
        if request.salary_range:
            if request.salary_range.min and request.salary_range.max:
                salary_text = f"R$ {request.salary_range.min:,.0f} - R$ {request.salary_range.max:,.0f}"
            elif request.salary_range.min:
                salary_text = f"A partir de R$ {request.salary_range.min:,.0f}"
            elif request.salary_range.max:
                salary_text = f"At\u00e9 R$ {request.salary_range.max:,.0f}"

        created_at_str = datetime.now().strftime('%d/%m/%Y às %H:%M')
        confidential_tag = '🔒 Vaga Confidencial' if request.is_confidential else ''
        affirmative_tag = '🌈 Vaga Afirmativa' if request.is_affirmative else ''
        manager_line = f'Gestor: {request.manager_name or request.manager_email}' if request.manager_email else ''

        workplan_content = f"""
\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
\ud83d\udccb WORKPLAN - NOVA VAGA CRIADA
\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

\ud83c\udfaf INFORMA\u00c7\u00d5ES GERAIS
\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
T\u00edtulo:           {request.job_title}
\u00c1rea/Departamento: {request.department or 'A definir'}
Localiza\u00e7\u00e3o:       {request.location or 'A definir'}
Modelo de Trabalho: {request.work_model or 'A definir'}
Senioridade:       {request.seniority_level or 'A definir'}
Urg\u00eancia:          {urgency_label}
{confidential_tag}
{affirmative_tag}

\ud83d\udcb0 REMUNERA\u00c7\u00c3O
\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
Faixa Salarial:    {salary_text}
Benef\u00edcios:        {benefits_list}

\ud83d\udee0\ufe0f REQUISITOS T\u00c9CNICOS
\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
{tech_reqs_list}

\ud83c\udfa5 COMPET\u00caNCIAS COMPORTAMENTAIS
\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
{competencies_list}

\ud83c\udf10 IDIOMAS
\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
{languages_list}

\ud83d\udcc5 CRONOGRAMA E PRAZOS
\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
Prazo Triagem:     {request.deadline_screening}
Prazo Shortlist:   {request.deadline_shortlist}
Prazo Fechamento:  {request.deadline_closing}

\ud83d\udd04 ETAPAS DO PROCESSO
\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
{stages_list}

\ud83d\udce2 PUBLICA\u00c7\u00c3O
\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
Plataformas:       {platforms_text}

\ud83d\udcdd DESCRI\u00c7\u00c3O DA VAGA
\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
{request.job_description}

\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
ID da Vaga: {request.job_id}
Criado em: {created_at_str}
Recrutador: {request.recruiter_name or request.recruiter_email}
{manager_line}
\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
"""

        email_subject = f"\ud83d\ude80 Nova Vaga Criada: {request.job_title} | {request.department or 'Empresa'}"
        teams_title = f"\ud83d\udccb Nova Vaga: {request.job_title}"

        recipients = []
        if request.recruiter_email:
            recipients.append({
                "email": request.recruiter_email,
                "name": request.recruiter_name,
                "role": "recruiter"
            })
        if request.manager_email:
            recipients.append({
                "email": request.manager_email,
                "name": request.manager_name,
                "role": "manager"
            })

        for recipient in recipients:
            role = recipient["role"]

            if "email" in request.channels:
                try:
                    html_content = f"""
                    <html>
                    <body style="font-family: Open Sans, Arial, sans-serif; line-height: 1.6; color: #333;">
                        <div style="max-width: 700px; margin: 0 auto; padding: 20px;">
                            <div style="background: linear-gradient(135deg, #60BED1 0%, #4A9BA8 100%); padding: 20px; border-radius: 8px 8px 0 0;">
                                <h1 style="color: white; margin: 0; font-size: 24px;">
                                    \ud83d\ude80 Nova Vaga Criada
                                </h1>
                                <p style="color: rgba(255,255,255,0.9); margin: 5px 0 0 0;">
                                    {request.job_title}
                                </p>
                            </div>
                            <div style="background: #f9fafb; padding: 20px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px;">
                                <pre style="font-family: Courier New, monospace; font-size: 13px; background: white; padding: 20px; border-radius: 4px; overflow-x: auto; white-space: pre-wrap; border: 1px solid #e5e7eb;">{workplan_content}</pre>
                                <div style="margin-top: 20px; text-align: center;">
                                    <a href="https://lia.wedotalent.com/jobs/{request.job_id}"
                                       style="display: inline-block; background: #60BED1; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: 600;">
                                        Ver Vaga no LIA
                                    </a>
                                </div>
                            </div>
                            <p style="color: #6b7280; font-size: 12px; text-align: center; margin-top: 20px;">
                                Este \u00e9 um email autom\u00e1tico do LIA - Sistema de Recrutamento Inteligente
                            </p>
                        </div>
                    </body>
                    </html>
                    """

                    await email_svc.send_email(
                        to_email=recipient["email"],
                        subject=email_subject,
                        html_content=html_content,
                        text_content=workplan_content
                    )
                    notifications_sent[role]["email"] = True
                    # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
                    logger.info(f"\ud83d\udce7 Email sent to {role}: {recipient['email']}")
                except Exception as e:
                    error_msg = f"Failed to send email to {role} ({recipient['email']}): {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)

            if "teams" in request.channels:
                try:
                    # Resolve per-tenant webhook URL so DB-configured URL drives delivery
                    # when TEAMS_WEBHOOK_URL env var is absent (T-1337).
                    _resolved_teams_url: str | None = None
                    try:
                        from app.api.v1.integrations import _get_tenant_teams_webhook_url
                        _resolved_teams_url, _ = await _get_tenant_teams_webhook_url(company_id, db)
                    except Exception as _url_err:
                        logger.debug("Could not resolve per-tenant Teams URL: %s", _url_err)
                    await teams_service.send_message(
                        user_email=recipient["email"],
                        title=teams_title,
                        message=workplan_content,
                        action_url=f"https://lia.wedotalent.com/jobs/{request.job_id}",
                        action_label="Ver Vaga",
                        webhook_url=_resolved_teams_url,
                    )
                    notifications_sent[role]["teams"] = True
                    # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
                    logger.info(f"\ud83d\udce8 Teams message sent to {role}: {recipient['email']}")
                except Exception as e:
                    error_msg = f"Failed to send Teams message to {role} ({recipient['email']}): {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)

        success = any([
            notifications_sent["recruiter"]["email"],
            notifications_sent["recruiter"]["teams"],
            notifications_sent["manager"]["email"],
            notifications_sent["manager"]["teams"]
        ])

        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"\ud83d\udcec Job created notification sent: {request.job_title} - Results: {notifications_sent}")

        return {
            "success": success,
            "notifications_sent": notifications_sent,
            "errors": errors if errors else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending job created notification: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

reorder_collection_before_item(router)
