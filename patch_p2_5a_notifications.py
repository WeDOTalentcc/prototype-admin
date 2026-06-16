#!/usr/bin/env python3
"""
P2.5a: Internal Notifications for Studio Events

Hooks the existing notification_service into Studio events:
  1. agent.execution.completed → bell + chat
  2. agent.deployment.created → bell
  3. agent.approval.requested → bell to admins
  4. agent.approval.reviewed → bell to creator
"""
import os

BASE_BE = "/home/runner/workspace/lia-agent-system"


def write_file(rel, content):
    full = os.path.join(BASE_BE, rel)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(content)
    print(f"  CREATED: {rel}")


def read_file(rel):
    with open(os.path.join(BASE_BE, rel)) as f:
        return f.read()


def patch_file(rel, old, new, label=""):
    full = os.path.join(BASE_BE, rel)
    content = read_file(rel)
    if old not in content:
        print(f"  SKIP: {label}")
        return False
    content = content.replace(old, new, 1)
    with open(full, "w") as f:
        f.write(content)
    print(f"  OK: {label}")
    return True


# ============================================================
# 1. Studio Notification Service (thin wrapper)
# ============================================================
print("\n=== 1. StudioNotificationService ===")
write_file("app/services/studio_notification_service.py", '''"""
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
            from lia_messaging.notification_service import (
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
            from lia_messaging.notification_service import (
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
            from lia_messaging.notification_service import (
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
            from lia_messaging.notification_service import (
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
''')


# ============================================================
# 2. Hook in execute_custom_agent
# ============================================================
print("\n=== 2. Hook in /execute ===")
patch_file(
    "app/api/v1/custom_agents.py",
    '''        await db.commit()

        tool_calls = [a.params.get("tool", "") for a in (output.actions or [])]''',
    '''        await db.commit()

        # P2.5a: Internal notification (non-blocking)
        try:
            from app.services.studio_notification_service import studio_notification_service
            await studio_notification_service.notify_execution_completed(
                db=db,
                user_id=str(current_user.id),
                agent_id=str(agent.id),
                agent_name=agent.name,
                candidates_processed=1,
                execution_time_ms=elapsed_ms,
            )
            await db.commit()
        except Exception as _notif_err:
            logger.warning("[StudioNotif] execute notify failed: %s", _notif_err)

        tool_calls = [a.params.get("tool", "") for a in (output.actions or [])]''',
    "hook execute notification",
)


# ============================================================
# 3. Hook in deployment creation
# ============================================================
print("\n=== 3. Hook in /deployments POST ===")
patch_file(
    "app/api/v1/agent_deployments.py",
    '''        await db.commit()
        return DeploymentResponse(**deployment.to_dict())
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        logger.error("Error creating deployment: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create deployment")''',
    '''        await db.commit()

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

        return DeploymentResponse(**deployment.to_dict())
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        logger.error("Error creating deployment: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create deployment")''',
    "hook deployment notification",
)


# ============================================================
# 4. Hook in approval request (notify admins)
# ============================================================
print("\n=== 4. Hook in approval request + review ===")
patch_file(
    "app/api/v1/agent_approvals.py",
    '''        approval = await agent_approval_service.request_approval(
            db=db,
            agent_id=agent_id,
            company_id=current_user.company_id,
            requested_by=str(current_user.id),
        )
        await db.commit()
        return ApprovalResponse(**approval.to_dict())''',
    '''        approval = await agent_approval_service.request_approval(
            db=db,
            agent_id=agent_id,
            company_id=current_user.company_id,
            requested_by=str(current_user.id),
        )
        await db.commit()

        # P2.5a: Notify all admins (non-blocking)
        try:
            from app.services.studio_notification_service import (
                studio_notification_service, get_company_admin_ids,
            )
            from sqlalchemy import select as _sel
            from lia_models.custom_agent import CustomAgent as _CA
            _agent_res = await db.execute(_sel(_CA).where(_CA.id == agent_id))
            _agent = _agent_res.scalar_one_or_none()
            if _agent:
                _admin_ids = await get_company_admin_ids(db, current_user.company_id)
                if _admin_ids:
                    await studio_notification_service.notify_approval_requested(
                        db=db,
                        admin_user_ids=_admin_ids,
                        agent_id=str(_agent.id),
                        agent_name=_agent.name,
                        requested_by=str(current_user.id),
                    )
                    await db.commit()
        except Exception as _notif_err:
            logger.warning("[StudioNotif] approval request notify failed: %s", _notif_err)

        return ApprovalResponse(**approval.to_dict())''',
    "hook approval request notification",
)

# Hook in review (notify creator of decision)
patch_file(
    "app/api/v1/agent_approvals.py",
    '''        approval = await agent_approval_service.review(
            db=db,
            approval_id=approval_id,
            company_id=current_user.company_id,
            reviewer_id=str(current_user.id),
            action=body.action,
            notes=body.notes,
        )
        await db.commit()
        return ApprovalResponse(**approval.to_dict())''',
    '''        approval = await agent_approval_service.review(
            db=db,
            approval_id=approval_id,
            company_id=current_user.company_id,
            reviewer_id=str(current_user.id),
            action=body.action,
            notes=body.notes,
        )
        await db.commit()

        # P2.5a: Notify creator of decision (non-blocking)
        try:
            from app.services.studio_notification_service import studio_notification_service
            from sqlalchemy import select as _sel
            from lia_models.custom_agent import CustomAgent as _CA
            _agent_res = await db.execute(_sel(_CA).where(_CA.id == approval.agent_id))
            _agent = _agent_res.scalar_one_or_none()
            if _agent and approval.requested_by:
                await studio_notification_service.notify_approval_reviewed(
                    db=db,
                    creator_user_id=approval.requested_by,
                    agent_id=str(_agent.id),
                    agent_name=_agent.name,
                    action=body.action,
                    reviewer_id=str(current_user.id),
                    review_notes=body.notes,
                )
                await db.commit()
        except Exception as _notif_err:
            logger.warning("[StudioNotif] approval review notify failed: %s", _notif_err)

        return ApprovalResponse(**approval.to_dict())''',
    "hook approval review notification",
)


# ============================================================
# VERIFY
# ============================================================
import ast
print("\n=== Verify ===")
for f in [
    "app/services/studio_notification_service.py",
    "app/api/v1/custom_agents.py",
    "app/api/v1/agent_deployments.py",
    "app/api/v1/agent_approvals.py",
]:
    try:
        ast.parse(read_file(f))
        print(f"  OK: {f}")
    except SyntaxError as e:
        print(f"  ERROR: {f}: {e}")

print("\nP2.5a Internal Notifications complete!")
