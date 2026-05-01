"""
StudioNotificationService — Thin wrapper around the existing notification
infrastructure to dispatch Studio agent events as in-app notifications.

Reuses libs/messaging/lia_messaging/notification_service.NotificationService
which already supports:
  - In-app/bell notifications (persisted in DB)
  - Multi-channel delivery (chat, bell, teams, email)
  - Action URLs and labels for click-through
  - source_agent and metadata for filtering

This service is non-blocking: any failure is logged but does not break
the calling operation (execute, deployment, approval).
"""
import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# Event types (mirrored in P2.5b webhooks for consistency)
EVENT_AGENT_EXECUTION_COMPLETED = "agent.execution.completed"
EVENT_AGENT_DEPLOYMENT_CREATED = "agent.deployment.created"
EVENT_AGENT_APPROVAL_REQUESTED = "agent.approval.requested"
EVENT_AGENT_APPROVAL_REVIEWED = "agent.approval.reviewed"


class StudioNotificationService:
    """Dispatches Studio events to internal notification channels."""

    async def notify_execution_completed(
        self,
        db: AsyncSession,
        user_id: str,
        agent_id: str,
        agent_name: str,
        candidates_processed: int = 0,
        execution_time_ms: int = 0,
    ) -> None:
        """Notify recruiter that an agent finished executing."""
        try:
            from libs.messaging.lia_messaging.notification_service import (
                notification_service, NotificationType,
            )
            await notification_service.create_notification(
                user_id=user_id,
                title=f"Agent '{agent_name}' concluiu execucao",
                message=(
                    f"Processados: {candidates_processed} item(s) em {execution_time_ms}ms"
                    if candidates_processed > 0 else
                    f"Execucao concluida em {execution_time_ms}ms"
                ),
                notification_type=NotificationType.INFO,
                category="agent_studio",
                source_agent=agent_name,
                source_trigger=EVENT_AGENT_EXECUTION_COMPLETED,
                action_url=f"/agent-studio?agent={agent_id}",
                action_label="Ver agente",
                channels=["bell"],
                metadata={"agent_id": agent_id, "event": EVENT_AGENT_EXECUTION_COMPLETED},
                db=db,
            )
        except Exception as exc:
            logger.warning("[StudioNotif] execution_completed failed: %s", exc)

    async def notify_deployment_created(
        self,
        db: AsyncSession,
        user_id: str,
        agent_id: str,
        agent_name: str,
        target_type: str,
        target_name: Optional[str] = None,
    ) -> None:
        """Notify creator that agent was deployed to target."""
        try:
            from libs.messaging.lia_messaging.notification_service import (
                notification_service, NotificationType,
            )
            target_label = {
                "job": "vaga",
                "talent_pool": "banco de talentos",
                "pipeline_stage": "etapa do pipeline",
                "candidate_list": "lista de candidatos",
            }.get(target_type, target_type)

            await notification_service.create_notification(
                user_id=user_id,
                title=f"Agent '{agent_name}' vinculado",
                message=f"Agora ativo na {target_label}: {target_name or '(sem nome)'}",
                notification_type=NotificationType.SUCCESS,
                category="agent_studio",
                source_agent=agent_name,
                source_trigger=EVENT_AGENT_DEPLOYMENT_CREATED,
                action_url=f"/agent-studio?agent={agent_id}",
                action_label="Ver vinculo",
                channels=["bell"],
                metadata={
                    "agent_id": agent_id,
                    "target_type": target_type,
                    "event": EVENT_AGENT_DEPLOYMENT_CREATED,
                },
                db=db,
            )
        except Exception as exc:
            logger.warning("[StudioNotif] deployment_created failed: %s", exc)

    async def notify_approval_requested(
        self,
        db: AsyncSession,
        admin_user_ids: list[str],
        agent_id: str,
        agent_name: str,
        requested_by: str,
    ) -> None:
        """Notify ALL admins that an approval is pending."""
        try:
            from libs.messaging.lia_messaging.notification_service import (
                notification_service, NotificationType,
            )
            for admin_id in admin_user_ids:
                await notification_service.create_notification(
                    user_id=admin_id,
                    title=f"Aprovacao pendente: '{agent_name}'",
                    message=f"Solicitada por {requested_by}. Revise antes de ativar.",
                    notification_type=NotificationType.ACTION_REQUIRED,
                    category="agent_studio",
                    source_agent=agent_name,
                    source_trigger=EVENT_AGENT_APPROVAL_REQUESTED,
                    action_url="/agent-studio",
                    action_label="Revisar",
                    channels=["bell"],
                    metadata={
                        "agent_id": agent_id,
                        "requested_by": requested_by,
                        "event": EVENT_AGENT_APPROVAL_REQUESTED,
                    },
                    db=db,
                )
        except Exception as exc:
            logger.warning("[StudioNotif] approval_requested failed: %s", exc)

    async def notify_approval_reviewed(
        self,
        db: AsyncSession,
        creator_user_id: str,
        agent_id: str,
        agent_name: str,
        action: str,
        reviewer_id: str,
        review_notes: Optional[str] = None,
    ) -> None:
        """Notify creator that admin approved/rejected their agent."""
        try:
            from libs.messaging.lia_messaging.notification_service import (
                notification_service, NotificationType,
            )
            is_approved = action == "approve"
            await notification_service.create_notification(
                user_id=creator_user_id,
                title=(
                    f"Agent '{agent_name}' aprovado" if is_approved
                    else f"Agent '{agent_name}' rejeitado"
                ),
                message=(
                    f"Revisado por {reviewer_id}."
                    + (f" Notas: {review_notes}" if review_notes else "")
                ),
                notification_type=(
                    NotificationType.SUCCESS if is_approved
                    else NotificationType.WARNING
                ),
                category="agent_studio",
                source_agent=agent_name,
                source_trigger=EVENT_AGENT_APPROVAL_REVIEWED,
                action_url=f"/agent-studio?agent={agent_id}",
                action_label="Ver agent",
                channels=["bell"],
                metadata={
                    "agent_id": agent_id,
                    "action": action,
                    "reviewer_id": reviewer_id,
                    "event": EVENT_AGENT_APPROVAL_REVIEWED,
                },
                db=db,
            )
        except Exception as exc:
            logger.warning("[StudioNotif] approval_reviewed failed: %s", exc)


studio_notification_service = StudioNotificationService()


async def get_company_admin_ids(db: AsyncSession, company_id: str) -> list[str]:
    """Get all admin user IDs for a company (used by approval_requested)."""
    try:
        from sqlalchemy import select, and_
        from app.auth.models import User, UserRole
        result = await db.execute(
            select(User.id).where(
                and_(
                    User.company_id == company_id,
                    User.role == UserRole.admin,
                    User.is_active == True,
                )
            )
        )
        return [str(uid) for uid in result.scalars().all()]
    except Exception as exc:
        logger.warning("[StudioNotif] get_company_admin_ids failed: %s", exc)
        return []
