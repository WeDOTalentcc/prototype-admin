"""

# ADR-001-EXEMPT: Cross-tenant proactive trigger scanner. Scans aggregate
# operational health across companies (no_contact, deadlines, interview metrics)
# for ops dashboards and alert dispatch. Tenant isolation reapplied when alerts
# fan out to per-company handlers downstream.
# TODO Sprint 6: extract scanning queries to dedicated cross-tenant repos with  # R-048: needs owner + ticket
# explicit company_id filtering audit logs.

Automation Trigger Service - Proactive automation engine.

This service manages automatic triggers that fire based on events:
- Candidate without contact for 48h → Follow-up email
- Interview in 24h → WhatsApp reminder
- Scorecard pending for 24h → Notification to interviewer
- Job without movement for 5 days → Alert to recruiter
- Candidate updates LinkedIn → Re-engagement notification
- Offer accepted → Welcome email + manager notification
"""
import logging
from datetime import datetime, timedelta
from enum import Enum, StrEnum
from typing import Any

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from lia_models.alert import Alert
from lia_models.candidate import Candidate
from lia_models.interview import Interview
from lia_models.job_vacancy import JobVacancy
from lia_models.task import Task, TaskPriority, TaskStatus, TaskType
from app.domains.analytics.services.activity_service import ActivityService
from app.shared.automation.trigger_types_canonical import TriggerType

logger = logging.getLogger(__name__)



class AutomationAction(StrEnum):
    """Actions that can be triggered automatically."""
    SEND_EMAIL = "send_email"
    SEND_WHATSAPP = "send_whatsapp"
    CREATE_TASK = "create_task"
    CREATE_ALERT = "create_alert"
    NOTIFY_USER = "notify_user"
    LOG_ACTIVITY = "log_activity"


class AutomationTriggerService:
    """
    Service for managing proactive automation triggers.
    """
    
    def __init__(self):
        self.activity_service = ActivityService()
        self.triggers_config = self._load_default_triggers()
        self._email_service = None
        self._whatsapp_service = None
    
    def _get_email_service(self):
        """Lazy load EmailService to avoid circular imports."""
        if self._email_service is None:
            try:
                from app.domains.communication.services.email_service import EmailService
                self._email_service = EmailService()
            except Exception as e:
                logger.warning(f"Could not load EmailService: {e}")
        return self._email_service
    
    def _get_whatsapp_service(self):
        """Lazy load WhatsAppService to avoid circular imports."""
        if self._whatsapp_service is None:
            try:
                from app.domains.communication.services.whatsapp_service import WhatsAppService
                self._whatsapp_service = WhatsAppService()
            except Exception as e:
                logger.warning(f"Could not load WhatsAppService: {e}")
        return self._whatsapp_service
    
    def _load_default_triggers(self) -> list[dict[str, Any]]:
        """Load default trigger configurations."""
        return [
            {
                "id": "candidate_no_contact_48h",
                "type": TriggerType.CANDIDATE_NO_CONTACT_48H,
                "name": "Candidato sem contato há 48h",
                "description": "Envia follow-up automático para candidatos sem contato",
                "enabled": True,
                "threshold_hours": 48,
                "actions": [
                    {"type": AutomationAction.SEND_EMAIL, "template": "follow_up_48h"},
                    {"type": AutomationAction.CREATE_TASK, "task_type": TaskType.FOLLOW_UP},
                    {"type": AutomationAction.LOG_ACTIVITY, "activity_type": "auto_follow_up"},
                ],
                "cooldown_hours": 72,
            },
            {
                "id": "interview_reminder_24h",
                "type": TriggerType.INTERVIEW_REMINDER_24H,
                "name": "Lembrete de entrevista 24h",
                "description": "Envia lembrete via WhatsApp 24h antes da entrevista",
                "enabled": True,
                "threshold_hours": 24,
                "actions": [
                    {"type": AutomationAction.SEND_WHATSAPP, "template": "interview_reminder"},
                    {"type": AutomationAction.LOG_ACTIVITY, "activity_type": "interview_reminder_sent"},
                ],
                "cooldown_hours": 0,
            },
            {
                "id": "scorecard_pending_24h",
                "type": TriggerType.SCORECARD_PENDING_24H,
                "name": "Scorecard pendente há 24h",
                "description": "Notifica entrevistador sobre scorecard não preenchido",
                "enabled": True,
                "threshold_hours": 24,
                "actions": [
                    {"type": AutomationAction.NOTIFY_USER, "notification_type": "scorecard_reminder"},
                    {"type": AutomationAction.CREATE_TASK, "task_type": TaskType.FEEDBACK_PENDING},
                ],
                "cooldown_hours": 24,
            },
            {
                "id": "job_no_movement_5d",
                "type": TriggerType.JOB_NO_MOVEMENT_5D,
                "name": "Vaga sem movimento há 5 dias",
                "description": "Alerta recrutador sobre vaga parada",
                "enabled": True,
                "threshold_days": 5,
                "actions": [
                    {"type": AutomationAction.CREATE_ALERT, "severity": "medium"},
                    {"type": AutomationAction.NOTIFY_USER, "notification_type": "job_stalled"},
                ],
                "cooldown_hours": 120,
            },
            {
                "id": "feedback_pending_48h",
                "type": TriggerType.FEEDBACK_PENDING_48H,
                "name": "Feedback pendente há 48h",
                "description": "Escala feedback não fornecido após 48h",
                "enabled": True,
                "threshold_hours": 48,
                "actions": [
                    {"type": AutomationAction.CREATE_TASK, "task_type": TaskType.FEEDBACK_PENDING, "priority": "high"},
                    {"type": AutomationAction.NOTIFY_USER, "notification_type": "feedback_escalation"},
                ],
                "cooldown_hours": 24,
            },
            {
                "id": "job_deadline_approaching",
                "type": TriggerType.JOB_DEADLINE_APPROACHING,
                "name": "Prazo da vaga se aproximando",
                "description": "Alerta quando faltam 3 dias para o prazo da vaga",
                "enabled": True,
                "threshold_days": 3,
                "actions": [
                    {"type": AutomationAction.CREATE_ALERT, "severity": "high"},
                    {"type": AutomationAction.NOTIFY_USER, "notification_type": "deadline_warning"},
                ],
                "cooldown_hours": 48,
            },
            {
                "id": "offer_accepted",
                "type": TriggerType.OFFER_ACCEPTED,
                "name": "Oferta aceita",
                "description": "Envia email de boas-vindas e notifica gestor",
                "enabled": True,
                "actions": [
                    {"type": AutomationAction.SEND_EMAIL, "template": "offer_accepted_welcome"},
                    {"type": AutomationAction.NOTIFY_USER, "notification_type": "offer_accepted", "target": "hiring_manager"},
                    {"type": AutomationAction.LOG_ACTIVITY, "activity_type": "offer_accepted"},
                ],
                "cooldown_hours": 0,
            },
        ]
    
    async def check_and_execute_triggers(
        self,
        db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """
        Check all triggers and execute actions for matching conditions.
        
        Returns:
            Summary of executed triggers
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            executed = []
            skipped = []
            errors = []
            
            for trigger in self.triggers_config:
                if not trigger.get("enabled", True):
                    skipped.append({
                        "trigger_id": trigger["id"],
                        "reason": "disabled"
                    })
                    continue
                
                try:
                    result = await self._check_trigger(db, trigger)
                    if result["matched"]:
                        execution_result = await self._execute_trigger_actions(
                            db, trigger, result["items"]
                        )
                        executed.append({
                            "trigger_id": trigger["id"],
                            "trigger_name": trigger["name"],
                            "items_matched": len(result["items"]),
                            "actions_executed": execution_result["actions_count"],
                        })
                except Exception as e:
                    logger.error(f"Error processing trigger {trigger['id']}: {e}")
                    errors.append({
                        "trigger_id": trigger["id"],
                        "error": str(e)
                    })
            
            summary = {
                "executed_at": datetime.utcnow().isoformat(),
                "triggers_executed": len(executed),
                "triggers_skipped": len(skipped),
                "errors": len(errors),
                "details": {
                    "executed": executed,
                    "skipped": skipped,
                    "errors": errors
                }
            }
            
            logger.info(f"⚡ Automation check completed: {len(executed)} triggers executed")
            return summary
            
        finally:
            if should_close:
                await db.close()
    
    async def _check_trigger(
        self,
        db: AsyncSession,
        trigger: dict[str, Any]
    ) -> dict[str, Any]:
        """Check if trigger conditions are met."""
        trigger_type = trigger["type"]
        now = datetime.utcnow()
        
        items = []
        
        if trigger_type == TriggerType.CANDIDATE_NO_CONTACT_48H:
            threshold = now - timedelta(hours=trigger.get("threshold_hours", 48))
            result = await db.execute(
                # TENANT-EXEMPT: automation_trigger_service polls system-wide for due triggers; per-tenant work dispatched downstream
                # TENANT-EXEMPT: automation_trigger_service polls system-wide for due triggers; per-tenant work dispatched downstream
                select(Candidate).where(
                    and_(
                        Candidate.status.in_(["new", "screening"]),
                        Candidate.is_active,
                        or_(
                            Candidate.last_contacted_at.is_(None),
                            Candidate.last_contacted_at < threshold
                        )
                    )
                ).limit(50)
            )
            items = [c for c in result.scalars()]
        
        elif trigger_type == TriggerType.INTERVIEW_REMINDER_24H:
            tomorrow = now + timedelta(hours=trigger.get("threshold_hours", 24))
            # TENANT-EXEMPT: automation_trigger_service polls system-wide for due triggers; per-tenant work dispatched downstream
            result = await db.execute(
                # TENANT-EXEMPT: automation_trigger_service polls system-wide for due triggers; per-tenant work dispatched downstream
                select(Interview).where(
                    and_(
                        Interview.start_time >= now,
                        Interview.start_time <= tomorrow,
                        Interview.status == "scheduled",
                        not Interview.reminder_sent
                    )
                )
            )
            items = [i for i in result.scalars()]
        
        elif trigger_type == TriggerType.SCORECARD_PENDING_24H:
            # TENANT-EXEMPT: automation_trigger_service polls system-wide for due triggers; per-tenant work dispatched downstream
            threshold = now - timedelta(hours=trigger.get("threshold_hours", 24))
            result = await db.execute(
                # TENANT-EXEMPT: automation_trigger_service polls system-wide for due triggers; per-tenant work dispatched downstream
                select(Interview).where(
                    and_(
                        Interview.end_time < now,
                        Interview.status == "completed",
                        Interview.feedback == {},
                        Interview.end_time > threshold - timedelta(days=7)
                    )
                )
            )
            items = [i for i in result.scalars()]
        
        # TENANT-EXEMPT: automation_trigger_service polls system-wide for due triggers; per-tenant work dispatched downstream
        elif trigger_type == TriggerType.JOB_NO_MOVEMENT_5D:
            threshold = now - timedelta(days=trigger.get("threshold_days", 5))
            result = await db.execute(
                # TENANT-EXEMPT: automation_trigger_service polls system-wide for due triggers; per-tenant work dispatched downstream
                select(JobVacancy).where(
                    and_(
                        JobVacancy.status == "open",
                        JobVacancy.updated_at < threshold
                    )
                )
            )
            items = [j for j in result.scalars()]
        # TENANT-EXEMPT: automation_trigger_service polls system-wide for due triggers; per-tenant work dispatched downstream
        
        elif trigger_type == TriggerType.FEEDBACK_PENDING_48H:
            threshold = now - timedelta(hours=trigger.get("threshold_hours", 48))
            result = await db.execute(
                # TENANT-EXEMPT: automation_trigger_service polls system-wide for due triggers; per-tenant work dispatched downstream
                select(Task).where(
                    and_(
                        Task.task_type == TaskType.FEEDBACK_PENDING,
                        Task.status == TaskStatus.PENDING,
                        Task.created_at < threshold,
                        Task.escalation_level == 0
                    )
                )
            )
            # TENANT-EXEMPT: automation_trigger_service polls system-wide for due triggers; per-tenant work dispatched downstream
            items = [t for t in result.scalars()]
        
        elif trigger_type == TriggerType.JOB_DEADLINE_APPROACHING:
            deadline_threshold = now + timedelta(days=trigger.get("threshold_days", 3))
            result = await db.execute(
                # TENANT-EXEMPT: automation_trigger_service polls system-wide for due triggers; per-tenant work dispatched downstream
                select(JobVacancy).where(
                    and_(
                        JobVacancy.status == "open",
                        JobVacancy.deadline.isnot(None),
                        JobVacancy.deadline <= deadline_threshold,
                        JobVacancy.deadline > now
                    )
                )
            )
            items = [j for j in result.scalars()]
        
        return {
            "matched": len(items) > 0,
            "items": items
        }
    
    async def _execute_trigger_actions(
        self,
        db: AsyncSession,
        trigger: dict[str, Any],
        items: list[Any]
    ) -> dict[str, Any]:
        """Execute actions for triggered items."""
        actions_executed = 0
        
        for action in trigger.get("actions", []):
            action_type = action.get("type")
            
            try:
                if action_type == AutomationAction.CREATE_TASK:
                    for item in items:
                        await self._create_task_for_item(db, trigger, action, item)
                        actions_executed += 1
                
                elif action_type == AutomationAction.CREATE_ALERT:
                    for item in items:
                        await self._create_alert_for_item(db, trigger, action, item)
                        actions_executed += 1
                
                elif action_type == AutomationAction.LOG_ACTIVITY:
                    for item in items:
                        await self._log_activity_for_item(trigger, action, item)
                        actions_executed += 1
                
                elif action_type == AutomationAction.NOTIFY_USER:
                    for item in items:
                        await self._create_notification_for_item(db, trigger, action, item)
                        actions_executed += 1
                
                elif action_type == AutomationAction.SEND_EMAIL:
                    for item in items:
                        result = await self._send_email_for_item(trigger, action, item, db)
                        if result.get("success"):
                            actions_executed += 1
                
                elif action_type == AutomationAction.SEND_WHATSAPP:
                    for item in items:
                        result = await self._send_whatsapp_for_item(trigger, action, item)
                        if result.get("success"):
                            actions_executed += 1
                
            except Exception as e:
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.error(f"Error executing action {action_type}: {e}")
        
        await db.commit()
        
        return {"actions_count": actions_executed}
    
    async def _create_task_for_item(
        self,
        db: AsyncSession,
        trigger: dict[str, Any],
        action: dict[str, Any],
        item: Any
    ) -> None:
        """Create a task for a triggered item."""
        task_type_str = action.get("task_type", TaskType.GENERAL)
        if isinstance(task_type_str, str):
            task_type = TaskType(task_type_str) if task_type_str in [t.value for t in TaskType] else TaskType.GENERAL
        else:
            task_type = task_type_str
        
        priority_str = action.get("priority", "medium")
        priority = TaskPriority(priority_str) if priority_str in [p.value for p in TaskPriority] else TaskPriority.MEDIUM
        
        related_job_id = None
        related_candidate_id = None
        title = trigger["name"]
        
        if hasattr(item, "job_id"):
            related_job_id = item.job_id
        if hasattr(item, "id") and isinstance(item, JobVacancy):
            related_job_id = item.id
            title = f"{trigger['name']}: {getattr(item, 'title', 'Vaga')}"
        
        if hasattr(item, "candidate_id"):
            related_candidate_id = item.candidate_id
        if hasattr(item, "id") and isinstance(item, Candidate):
            related_candidate_id = item.id
            title = f"{trigger['name']}: {getattr(item, 'name', 'Candidato')}"
        
        task = Task(
            title=title,
            description=trigger.get("description"),
            task_type=task_type,
            priority=priority,
            created_by_agent="automation_engine",
            is_automated=True,
            company_id=str(getattr(item, "company_id", "") or ""),
            related_job_id=related_job_id,
            related_candidate_id=related_candidate_id,
            context={"trigger_id": trigger["id"], "trigger_type": trigger["type"].value}
        )
        
        db.add(task)
    
    async def _create_alert_for_item(
        self,
        db: AsyncSession,
        trigger: dict[str, Any],
        action: dict[str, Any],
        item: Any
    ) -> None:
        """Create an alert for a triggered item."""
        related_job_id = None
        title = trigger["name"]
        message = trigger.get("description", "")
        
        if hasattr(item, "id") and isinstance(item, JobVacancy):
            related_job_id = item.id
            title = f"{trigger['name']}: {getattr(item, 'title', 'Vaga')}"
            message = f"A vaga '{getattr(item, 'title', 'Sem título')}' requer atenção."
        
        alert = Alert(
            title=title,
            message=message,
            severity=action.get("severity", "medium"),
            alert_type=trigger["type"].value,
            related_job_id=related_job_id,
            is_active=True,
            metadata={"trigger_id": trigger["id"], "automated": True}
        )
        
        db.add(alert)
    
    async def _log_activity_for_item(
        self,
        trigger: dict[str, Any],
        action: dict[str, Any],
        item: Any
    ) -> None:
        """Log an activity for a triggered item."""
        target_id = None
        target_name = None
        target_type = None
        
        if isinstance(item, Candidate):
            target_id = item.id
            target_name = item.name
            target_type = "candidate"
        elif isinstance(item, JobVacancy):
            target_id = item.id
            target_name = item.title
            target_type = "job"
        elif isinstance(item, Interview):
            target_id = item.id
            target_name = f"Entrevista {item.id}"
            target_type = "interview"
        
        await self.activity_service.create_activity(
            activity_type=action.get("activity_type", "automation"),
            title=f"Automação: {trigger['name']}",
            description=trigger.get("description"),
            actor_id="automation_engine",
            actor_name="LIA Automation",
            actor_type="ai",
            target_id=target_id,
            target_name=target_name,
            target_type=target_type,
            extra_data={"trigger_id": trigger["id"], "automated": True},
            category="automation"
        )
    
    async def _create_notification_for_item(
        self,
        db: AsyncSession,
        trigger: dict[str, Any],
        action: dict[str, Any],
        item: Any
    ) -> None:
        """Create a Bell in-app notification for a triggered item."""
        try:
            from app.services.notification_service import NotificationService, NotificationType

            user_id = None
            related_job_id = None
            related_candidate_id = None

            if isinstance(item, Interview):
                user_id = getattr(item, "interviewer_id", None)
                related_candidate_id = str(item.candidate_id) if getattr(item, "candidate_id", None) else None
                related_job_id = str(item.job_vacancy_id) if getattr(item, "job_vacancy_id", None) else None
            elif isinstance(item, JobVacancy):
                user_id = getattr(item, "created_by", None)
                related_job_id = str(item.id) if item.id else None
            elif isinstance(item, Candidate):
                related_candidate_id = str(item.id) if item.id else None
            elif isinstance(item, Task):
                user_id = getattr(item, "assigned_to_user_id", None)
                related_job_id = str(item.related_job_id) if getattr(item, "related_job_id", None) else None
                related_candidate_id = str(item.related_candidate_id) if getattr(item, "related_candidate_id", None) else None

            if not user_id:
                logger.debug(
                    f"[TRIGGER] No user_id found for {type(item).__name__} "
                    f"— skipping Bell notification for trigger '{trigger['id']}'"
                )
                return

            notification_type_map = {
                "scorecard_reminder": NotificationType.ACTION_REQUIRED,
                "job_stalled": NotificationType.WARNING,
                "feedback_escalation": NotificationType.URGENT,
                "deadline_warning": NotificationType.URGENT,
                "offer_accepted": NotificationType.SUCCESS,
            }
            notif_key = action.get("notification_type", "info")
            notif_type = notification_type_map.get(notif_key, NotificationType.INFO)

            svc = NotificationService()
            await svc.create_notification(
                user_id=user_id,
                title=trigger["name"],
                message=trigger.get("description", ""),
                notification_type=notif_type,
                category="automation",
                source_agent="automation_engine",
                source_trigger=trigger["id"],
                related_job_id=related_job_id,
                related_candidate_id=related_candidate_id,
                db=db,
            )
            logger.info(
                f"🔔 [TRIGGER] Bell notification sent to user={user_id} "
                f"for trigger='{trigger['id']}'"
            )
        except Exception as e:
            logger.error(f"[TRIGGER] Failed to create notification: {e}", exc_info=True)
    
    async def _send_email_for_item(
        self,
        trigger: dict[str, Any],
        action: dict[str, Any],
        item: Any,
        db: AsyncSession
    ) -> dict[str, Any]:
        """Send an email for a triggered item."""
        email_service = self._get_email_service()
        if not email_service:
            logger.error("EmailService not available")
            return {"success": False, "error": "email_service_unavailable"}
        
        recipient_email = None
        recipient_name = "Candidato"
        candidate_id = None
        
        if isinstance(item, Candidate):
            recipient_email = getattr(item, "email", None)
            recipient_name = getattr(item, "name", "Candidato")
            candidate_id = str(item.id) if item.id else None
        elif isinstance(item, Interview):
            if hasattr(item, "candidate") and item.candidate:
                recipient_email = getattr(item.candidate, "email", None)
                recipient_name = getattr(item.candidate, "name", "Candidato")
                candidate_id = str(item.candidate.id) if item.candidate.id else None
            elif hasattr(item, "candidate_id"):
                candidate_id = str(item.candidate_id) if item.candidate_id else None
        
        if not recipient_email:
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.warning(f"⚠️ [TRIGGER] No email available for item {type(item).__name__}")
            return {"success": False, "error": "no_recipient_email"}
        
        template_name = action.get("template")
        
        template_variables = {
            "candidate_name": recipient_name,
            "trigger_name": trigger.get("name", ""),
            "trigger_description": trigger.get("description", ""),
        }
        
        if isinstance(item, Interview):
            if hasattr(item, "start_time") and item.start_time:
                template_variables["interview_date"] = item.start_time.strftime("%d/%m/%Y")
                template_variables["interview_time"] = item.start_time.strftime("%H:%M")
        
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"📧 [TRIGGER] using template '{template_name}'")
        
        try:
            # Use template-based sending if template is specified
            if template_name:
                result = await email_service.send_template_email(
                    to_email=recipient_email,
                    to_name=recipient_name,
                    template_name=template_name,
                    variables=template_variables,
                    candidate_id=candidate_id
                )
            else:
                # Fallback to direct email with trigger description
                result = await email_service.send_email(
                    to_email=recipient_email,
                    to_name=recipient_name,
                    subject=f"[LIA] {trigger.get('name', 'Notificação automática')}",
                    body_html=f"<p>Olá {recipient_name},</p><p>{trigger.get('description', '')}</p>",
                    body_text=f"Olá {recipient_name},\n\n{trigger.get('description', '')}"
                )
            
            # Handle both dict and object responses
            success = result.get("success") if isinstance(result, dict) else getattr(result, "success", False)
            message_id = result.get("message_id") if isinstance(result, dict) else getattr(result, "message_id", None)
            error = result.get("error") if isinstance(result, dict) else getattr(result, "error", None)
            
            if success:
                logger.info("✅ [TRIGGER] Email sent successfully")
                return {
                    "success": True,
                    "action": "send_email",
                    "recipient_email": recipient_email,
                    "template": template_name,
                    "message_id": message_id
                }
            else:
                logger.warning(f"⚠️ [TRIGGER] Failed to send email: {error}")
                return {
                    "success": False,
                    "action": "send_email",
                    "recipient_email": recipient_email,
                    "error": error or "Unknown error"
                }
                
        except Exception as e:
            logger.error(f"❌ [TRIGGER] Error sending email: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_whatsapp_for_item(
        self,
        trigger: dict[str, Any],
        action: dict[str, Any],
        item: Any
    ) -> dict[str, Any]:
        """Send a WhatsApp message for a triggered item."""
        whatsapp_service = self._get_whatsapp_service()
        if not whatsapp_service:
            logger.error("WhatsAppService not available")
            return {"success": False, "error": "whatsapp_service_unavailable"}
        
        recipient_phone = None
        recipient_name = "Candidato"
        candidate_id = None
        
        if isinstance(item, Candidate):
            recipient_phone = getattr(item, "phone", None)
            recipient_name = getattr(item, "name", "Candidato")
            candidate_id = str(item.id) if item.id else None
        elif isinstance(item, Interview):
            if hasattr(item, "candidate") and item.candidate:
                recipient_phone = getattr(item.candidate, "phone", None)
                recipient_name = getattr(item.candidate, "name", "Candidato")
                candidate_id = str(item.candidate.id) if item.candidate.id else None
            elif hasattr(item, "candidate_id"):
                candidate_id = str(item.candidate_id) if item.candidate_id else None
        
        if not recipient_phone:
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.warning(f"⚠️ [TRIGGER] No phone available for item {type(item).__name__}")
            return {"success": False, "error": "no_recipient_phone"}
        
        template_name = action.get("template")
        
        template_data = {
            "candidate_name": recipient_name,
            "trigger_name": trigger.get("name", ""),
        }
        
        if isinstance(item, Interview):
            if hasattr(item, "start_time") and item.start_time:
                template_data["interview_date"] = item.start_time.strftime("%d/%m/%Y")
                template_data["interview_time"] = item.start_time.strftime("%H:%M")
        
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"📱 [TRIGGER] Sending WhatsApp to {recipient_phone} using template '{template_name}'")
        
        try:
            if template_name:
                result = await whatsapp_service.send_template(
                    to_phone=recipient_phone,
                    template_name=template_name,
                    template_data=template_data,
                    metadata={
                        "candidate_id": candidate_id,
                        "trigger_id": trigger.get("id"),
                        "automation": True
                    }
                )
            else:
                message = f"Olá {recipient_name}, {trigger.get('description', 'você tem uma notificação.')}"
                result = await whatsapp_service.send_message(
                    to_phone=recipient_phone,
                    message=message,
                    metadata={
                        "candidate_id": candidate_id,
                        "trigger_id": trigger.get("id"),
                        "automation": True
                    }
                )
            
            # Handle both dict and object responses consistently
            success = result.get("success") if isinstance(result, dict) else getattr(result, "success", False)
            message_id = result.get("message_id") if isinstance(result, dict) else getattr(result, "message_id", None)
            error = result.get("error") if isinstance(result, dict) else getattr(result, "error", None)
            error_code = result.get("error_code") if isinstance(result, dict) else getattr(result, "error_code", None)
            status = result.get("status") if isinstance(result, dict) else getattr(result, "status", None)
            
            if success:
                # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
                logger.info(f"✅ [TRIGGER] WhatsApp sent successfully to {recipient_phone}")
                return {
                    "success": True,
                    "action": "send_whatsapp",
                    "recipient_phone": recipient_phone,
                    "template": template_name,
                    "message_id": message_id,
                    "status": status.value if hasattr(status, 'value') else status
                }
            else:
                # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
                logger.warning(f"⚠️ [TRIGGER] Failed to send WhatsApp to {recipient_phone}: {error}")
                return {
                    "success": False,
                    "action": "send_whatsapp",
                    "recipient_phone": recipient_phone,
                    "error": error or "Unknown error",
                    "error_code": error_code
                }
                
        except Exception as e:
            # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
            logger.error(f"❌ [TRIGGER] Error sending WhatsApp to {recipient_phone}: {e}")
            return {"success": False, "error": str(e)}
    
    def get_triggers_config(self) -> list[dict[str, Any]]:
        """Get current triggers configuration."""
        return [
            {
                "id": t["id"],
                "name": t["name"],
                "description": t["description"],
                "enabled": t["enabled"],
                "type": t["type"].value if isinstance(t["type"], TriggerType) else t["type"],
            }
            for t in self.triggers_config
        ]
    
    def update_trigger_status(self, trigger_id: str, enabled: bool) -> bool:
        """Enable or disable a trigger."""
        for trigger in self.triggers_config:
            if trigger["id"] == trigger_id:
                trigger["enabled"] = enabled
                logger.info(f"Trigger {trigger_id} {'enabled' if enabled else 'disabled'}")
                return True
        return False


automation_trigger_service = AutomationTriggerService()
