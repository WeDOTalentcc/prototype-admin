"""
Automation Service - Communication automation execution engine.

This service handles:
1. Triggering automations based on events
2. Evaluating conditions for automation rules
3. Executing actions (email, whatsapp, tasks, notifications)
4. Logging execution history for auditing
"""
import logging
import os
import time
import uuid
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.domains.automation.repositories.communication_automation_repository import (
    CommunicationAutomationRepository,
)
from app.domains.candidates.repositories.candidate_repository import CandidateRepository
from app.domains.job_management.repositories.job_vacancy_crud_repository import (
    JobVacancyCRUDRepository,
)
from app.services.notification_service import NotificationService
from lia_models.automation import ActionType, AutomationExecutionLog, CommunicationAutomation
from lia_models.task import Task, TaskPriority, TaskType

logger = logging.getLogger(__name__)

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT.lower() == "production"


class AutomationService:
    """
    Service for managing and executing communication automations.
    """
    
    def __init__(self):
        self.notification_service = NotificationService()
        self._email_service = None
        self._whatsapp_service = None
    
    @property
    def email_service(self):
        """Lazy load EmailService to avoid circular imports."""
        if self._email_service is None:
            from app.domains.communication.services.email_service import EmailService
            self._email_service = EmailService()
        return self._email_service
    
    @property
    def whatsapp_service(self):
        """Lazy load WhatsAppService to avoid circular imports."""
        if self._whatsapp_service is None:
            from app.domains.communication.services.whatsapp_service import WhatsAppService
            self._whatsapp_service = WhatsAppService()
        return self._whatsapp_service
    
    async def _validate_candidate_exists(
        self,
        candidate_id: str | None,
        db: AsyncSession
    ) -> bool:
        """Validate that a candidate exists before executing actions."""
        if not candidate_id:
            return True
        
        try:
            candidate = await CandidateRepository(db).get_by_id_str(str(candidate_id))
            if not candidate:
                logger.warning(f"⚠️ Candidate not found: {candidate_id}")
                return False
            return True
        except Exception as e:
            logger.error(f"Error validating candidate {candidate_id}: {e}")
            return False
    
    async def _validate_vacancy_exists(
        self,
        vacancy_id: str | None,
        db: AsyncSession
    ) -> bool:
        """Validate that a vacancy exists before executing actions."""
        if not vacancy_id:
            return True
        
        try:
            vacancy = await JobVacancyCRUDRepository(db).get_vacancy_by_id(vacancy_id)
            if not vacancy:
                logger.warning(f"⚠️ Vacancy not found: {vacancy_id}")
                return False
            return True
        except Exception as e:
            logger.error(f"Error validating vacancy {vacancy_id}: {e}")
            return False
    
    async def trigger_automation(
        self,
        trigger_type: str,
        trigger_data: dict[str, Any],
        company_id: str,
        db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """
        Execute automations based on a trigger event.
        
        Args:
            trigger_type: Type of trigger (e.g., 'candidate_stage_changed')
            trigger_data: Data associated with the trigger event
            company_id: Company ID for multi-tenancy
            db: Optional database session
            
        Returns:
            Summary of executed automations
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            automations = await CommunicationAutomationRepository(
                db
            ).list_active_for_trigger(company_id, trigger_type)

            executed = []
            skipped = []
            errors = []
            
            for automation in automations:
                try:
                    if not await self._check_cooldown(automation, db):
                        skipped.append({
                            "automation_id": str(automation.id),
                            "name": automation.name,
                            "reason": "cooldown_active"
                        })
                        continue
                    
                    conditions_met = await self.evaluate_conditions(
                        automation.conditions or [],
                        trigger_data
                    )
                    
                    if not conditions_met:
                        skipped.append({
                            "automation_id": str(automation.id),
                            "name": automation.name,
                            "reason": "conditions_not_met"
                        })
                        continue
                    
                    start_time = time.time()
                    action_result = await self.execute_action(
                        automation.action_type,
                        automation.action_config or {},
                        trigger_data,
                        company_id,
                        db
                    )
                    execution_time_ms = int((time.time() - start_time) * 1000)
                    
                    await self._log_execution(
                        automation_id=automation.id,
                        company_id=company_id,
                        trigger_event=trigger_type,
                        trigger_data=trigger_data,
                        action_executed=automation.action_type,
                        action_result=action_result,
                        status="success",
                        execution_time_ms=execution_time_ms,
                        candidate_id=trigger_data.get("candidate_id"),
                        vacancy_id=trigger_data.get("vacancy_id"),
                        db=db
                    )
                    
                    automation.last_executed_at = datetime.utcnow()
                    automation.execution_count = str(int(automation.execution_count or "0") + 1)
                    
                    executed.append({
                        "automation_id": str(automation.id),
                        "name": automation.name,
                        "action": automation.action_type,
                        "result": action_result
                    })
                    
                except Exception as e:
                    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                    logger.error(f"Error executing automation {automation.id}: {e}")
                    
                    await self._log_execution(
                        automation_id=automation.id,
                        company_id=company_id,
                        trigger_event=trigger_type,
                        trigger_data=trigger_data,
                        action_executed=automation.action_type,
                        action_result={},
                        status="error",
                        error_message=str(e),
                        candidate_id=trigger_data.get("candidate_id"),
                        vacancy_id=trigger_data.get("vacancy_id"),
                        db=db
                    )
                    
                    errors.append({
                        "automation_id": str(automation.id),
                        "name": automation.name,
                        "error": str(e)
                    })
            
            await db.commit()
            
            return {
                "trigger_type": trigger_type,
                "executed_at": datetime.utcnow().isoformat(),
                "automations_executed": len(executed),
                "automations_skipped": len(skipped),
                "errors": len(errors),
                "details": {
                    "executed": executed,
                    "skipped": skipped,
                    "errors": errors
                }
            }
            
        except Exception:
            try:
                await db.rollback()
            except Exception:
                pass
            raise
        finally:
            if should_close:
                await db.close()
    
    async def evaluate_conditions(
        self,
        conditions: list[dict[str, Any]],
        trigger_data: dict[str, Any]
    ) -> bool:
        """
        Evaluate if all conditions are satisfied for automation execution.
        
        Args:
            conditions: List of condition objects with field, operator, value
            trigger_data: Event data to evaluate against
            
        Returns:
            True if all conditions are met, False otherwise
        """
        if not conditions:
            return True
        
        for condition in conditions:
            field = condition.get("field")
            operator = condition.get("operator", "equals")
            expected_value = condition.get("value")
            
            if not field:
                continue
            
            actual_value = trigger_data.get(field)
            
            if operator == "equals":
                if actual_value != expected_value:
                    return False
            elif operator == "not_equals":
                if actual_value == expected_value:
                    return False
            elif operator == "contains":
                if expected_value not in str(actual_value or ""):
                    return False
            elif operator == "not_contains":
                if expected_value in str(actual_value or ""):
                    return False
            elif operator == "in":
                if actual_value not in (expected_value or []):
                    return False
            elif operator == "not_in":
                if actual_value in (expected_value or []):
                    return False
            elif operator == "greater_than":
                try:
                    if float(actual_value or 0) <= float(expected_value or 0):
                        return False
                except (TypeError, ValueError):
                    return False
            elif operator == "less_than":
                try:
                    if float(actual_value or 0) >= float(expected_value or 0):
                        return False
                except (TypeError, ValueError):
                    return False
            elif operator == "exists":
                if actual_value is None:
                    return False
            elif operator == "not_exists":
                if actual_value is not None:
                    return False
        
        return True
    
    async def execute_action(
        self,
        action_type: str,
        action_config: dict[str, Any],
        trigger_data: dict[str, Any],
        company_id: str,
        db: AsyncSession
    ) -> dict[str, Any]:
        """
        Execute an automation action.
        
        Args:
            action_type: Type of action to execute
            action_config: Configuration for the action
            trigger_data: Data from the trigger event
            company_id: Company ID
            db: Database session
            
        Returns:
            Result of the action execution
        """
        try:
            candidate_id = trigger_data.get("candidate_id")
            vacancy_id = trigger_data.get("vacancy_id")
            
            if candidate_id:
                candidate_exists = await self._validate_candidate_exists(candidate_id, db)
                if not candidate_exists:
                    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                    logger.warning(f"⚠️ [AUTOMATION] Skipping action {action_type} - candidate not found: {candidate_id}")
                    return {
                        "action": action_type,
                        "status": "skipped",
                        "reason": "candidate_not_found",
                        "candidate_id": candidate_id
                    }
            
            if vacancy_id:
                vacancy_exists = await self._validate_vacancy_exists(vacancy_id, db)
                if not vacancy_exists:
                    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                    logger.warning(f"⚠️ [AUTOMATION] Skipping action {action_type} - vacancy not found: {vacancy_id}")
                    return {
                        "action": action_type,
                        "status": "skipped",
                        "reason": "vacancy_not_found",
                        "vacancy_id": vacancy_id
                    }
            
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.info(f"🤖 [AUTOMATION] Executing action: {action_type} for company: {company_id}")
            
            if action_type == ActionType.SEND_EMAIL.value or action_type == "send_email":
                return await self._execute_send_email(action_config, trigger_data, company_id, db)
            
            elif action_type == ActionType.SEND_WHATSAPP.value or action_type == "send_whatsapp":
                return await self._execute_send_whatsapp(action_config, trigger_data, company_id, db)
            
            elif action_type == ActionType.CREATE_TASK.value or action_type == "create_task":
                return await self._execute_create_task(action_config, trigger_data, company_id, db)
            
            elif action_type == ActionType.NOTIFY_RECRUITER.value or action_type == "notify_recruiter":
                return await self._execute_notify_recruiter(action_config, trigger_data, company_id, db)
            
            elif action_type == ActionType.NOTIFY_MANAGER.value or action_type == "notify_manager":
                return await self._execute_notify_manager(action_config, trigger_data, company_id, db)
            
            elif action_type == ActionType.LOG_ACTIVITY.value or action_type == "log_activity":
                return await self._execute_log_activity(action_config, trigger_data, company_id)
            
            else:
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.warning(f"Unknown action type: {action_type}")
                return {"status": "unknown_action", "action_type": action_type}
                
        except Exception as e:
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.error(f"❌ [AUTOMATION] Error executing action {action_type}: {e}", exc_info=True)
            raise
    
    async def _execute_send_email(
        self,
        config: dict[str, Any],
        trigger_data: dict[str, Any],
        company_id: str,
        db: AsyncSession
    ) -> dict[str, Any]:
        """Execute send email action using EmailService."""
        template_id = config.get("template_id")
        recipient_email = trigger_data.get("candidate_email") or config.get("to_email")
        recipient_name = trigger_data.get("candidate_name") or config.get("to_name", "Candidato")
        subject = config.get("subject", "Mensagem automática")
        
        if not recipient_email:
            logger.warning("⚠️ [AUTOMATION] No recipient email provided for send_email action")
            return {
                "action": "send_email",
                "status": "failed",
                "error": "no_recipient_email"
            }
        
        logger.info(f"📧 [AUTOMATION] with template {template_id}")
        
        try:
            template_variables = {
                "candidate_name": trigger_data.get("candidate_name", "Candidato"),
                "job_title": trigger_data.get("vacancy_title", trigger_data.get("job_title", "")),
                "company_name": trigger_data.get("company_name", ""),
                "recruiter_name": trigger_data.get("recruiter_name", ""),
                **config.get("variables", {})
            }
            
            if template_id:
                result = await self.email_service.send_template_email(
                    template_id=template_id,
                    to_email=recipient_email,
                    to_name=recipient_name,
                    variables=template_variables,
                    company_id=company_id,
                    db=db
                )
            else:
                body_html = config.get("body_html", "")
                body_text = config.get("body_text", "")
                
                for key, value in template_variables.items():
                    if value:
                        body_html = body_html.replace(f"{{{{{key}}}}}", str(value))
                        body_text = body_text.replace(f"{{{{{key}}}}}", str(value))
                        subject = subject.replace(f"{{{{{key}}}}}", str(value))
                
                result = await self.email_service.send_email(
                    to_email=recipient_email,
                    to_name=recipient_name,
                    subject=subject,
                    body_html=body_html,
                    body_text=body_text
                )
            
            if result.get("success"):
                logger.info("✅ [AUTOMATION] Email sent successfully")
                return {
                    "action": "send_email",
                    "status": "sent",
                    "recipient_email": recipient_email,
                    "recipient_name": recipient_name,
                    "template_id": template_id,
                    "message_id": result.get("message_id")
                }
            else:
                logger.warning(f"⚠️ [AUTOMATION] Email sending failed: {result.get('error')}")
                return {
                    "action": "send_email",
                    "status": "failed",
                    "recipient_email": recipient_email,
                    "error": result.get("error", "Unknown error")
                }
                
        except Exception as e:
            logger.error(f"❌ [AUTOMATION] Error sending email: {e}", exc_info=True)
            return {
                "action": "send_email",
                "status": "error",
                "recipient_email": recipient_email,
                "error": str(e)
            }
    
    async def _execute_send_whatsapp(
        self,
        config: dict[str, Any],
        trigger_data: dict[str, Any],
        company_id: str,
        db: AsyncSession
    ) -> dict[str, Any]:
        """Execute send WhatsApp action using WhatsAppService."""
        template_name = config.get("template_name")
        recipient_phone = trigger_data.get("candidate_phone") or config.get("to_phone")
        recipient_name = trigger_data.get("candidate_name") or config.get("to_name", "Candidato")
        message = config.get("message", "")
        
        if not recipient_phone:
            logger.warning("⚠️ [AUTOMATION] No recipient phone provided for send_whatsapp action")
            return {
                "action": "send_whatsapp",
                "status": "failed",
                "error": "no_recipient_phone"
            }
        
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"📱 [AUTOMATION] Sending WhatsApp to {recipient_phone} with template {template_name}")
        
        try:
            template_data = {
                "candidate_name": trigger_data.get("candidate_name", "Candidato"),
                "job_title": trigger_data.get("vacancy_title", trigger_data.get("job_title", "")),
                "company_name": trigger_data.get("company_name", ""),
                "recruiter_name": trigger_data.get("recruiter_name", ""),
                **config.get("variables", {})
            }
            
            if template_name:
                result = await self.whatsapp_service.send_template(
                    to_phone=recipient_phone,
                    template_name=template_name,
                    template_data=template_data,
                    metadata={
                        "company_id": company_id,
                        "candidate_id": trigger_data.get("candidate_id"),
                        "automation": True
                    }
                )
            else:
                for key, value in template_data.items():
                    if value and message:
                        message = message.replace(f"{{{{{key}}}}}", str(value))
                
                result = await self.whatsapp_service.send_message(
                    to_phone=recipient_phone,
                    message=message,
                    metadata={
                        "company_id": company_id,
                        "candidate_id": trigger_data.get("candidate_id"),
                        "automation": True
                    }
                )
            
            if result.success:
                # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
                logger.info(f"✅ [AUTOMATION] WhatsApp sent successfully to {recipient_phone}")
                return {
                    "action": "send_whatsapp",
                    "status": "sent",
                    "recipient_phone": recipient_phone,
                    "recipient_name": recipient_name,
                    "template_name": template_name,
                    "message_id": result.message_id,
                    "provider_status": result.status.value
                }
            else:
                logger.warning(f"⚠️ [AUTOMATION] WhatsApp sending failed: {result.error}")
                return {
                    "action": "send_whatsapp",
                    "status": "failed",
                    "recipient_phone": recipient_phone,
                    "error": result.error or "Unknown error",
                    "error_code": result.error_code
                }
                
        except Exception as e:
            # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
            logger.error(f"❌ [AUTOMATION] Error sending WhatsApp to {recipient_phone}: {e}", exc_info=True)
            return {
                "action": "send_whatsapp",
                "status": "error",
                "recipient_phone": recipient_phone,
                "error": str(e)
            }
    
    async def _execute_create_task(
        self,
        config: dict[str, Any],
        trigger_data: dict[str, Any],
        company_id: str,
        db: AsyncSession
    ) -> dict[str, Any]:
        """Execute create task action."""
        task_title = config.get("title", "Tarefa automática")
        task_description = config.get("description", "")
        task_type_str = config.get("task_type", "general")
        priority_str = config.get("priority", "medium")
        
        task_title = task_title.replace("{{candidate_name}}", trigger_data.get("candidate_name", "Candidato"))
        task_title = task_title.replace("{{vacancy_title}}", trigger_data.get("vacancy_title", "Vaga"))
        
        task_description = task_description.replace("{{candidate_name}}", trigger_data.get("candidate_name", ""))
        task_description = task_description.replace("{{vacancy_title}}", trigger_data.get("vacancy_title", ""))
        
        try:
            task_type = TaskType(task_type_str) if task_type_str in [t.value for t in TaskType] else TaskType.GENERAL
        except ValueError:
            task_type = TaskType.GENERAL
            
        try:
            priority = TaskPriority(priority_str) if priority_str in [p.value for p in TaskPriority] else TaskPriority.MEDIUM
        except ValueError:
            priority = TaskPriority.MEDIUM
        
        task = Task(
            title=task_title,
            description=task_description,
            task_type=task_type,
            priority=priority,
            created_by_agent="automation_service",
            is_automated=True,
            company_id=company_id,
            related_job_id=trigger_data.get("vacancy_id"),
            related_candidate_id=trigger_data.get("candidate_id"),
            context={"automation_trigger": trigger_data}
        )
        
        db.add(task)
        
        logger.info(f"📋 [AUTOMATION] Created task: {task_title}")
        
        return {
            "action": "create_task",
            "status": "created",
            "task_title": task_title,
            "task_type": task_type.value,
            "priority": priority.value
        }
    
    async def _execute_notify_recruiter(
        self,
        config: dict[str, Any],
        trigger_data: dict[str, Any],
        company_id: str,
        db: AsyncSession
    ) -> dict[str, Any]:
        """Execute notify recruiter action."""
        notification_title = config.get("title", "Notificação automática")
        notification_message = config.get("message", "")
        
        notification_title = notification_title.replace("{{candidate_name}}", trigger_data.get("candidate_name", "Candidato"))
        notification_message = notification_message.replace("{{candidate_name}}", trigger_data.get("candidate_name", ""))
        
        recruiter_id = trigger_data.get("recruiter_id") or config.get("recruiter_id")
        
        logger.info(f"🔔 [AUTOMATION] Notifying recruiter {recruiter_id}: {notification_title}")
        
        return {
            "action": "notify_recruiter",
            "status": "sent",
            "recruiter_id": recruiter_id,
            "title": notification_title,
            "message": notification_message
        }
    
    async def _execute_notify_manager(
        self,
        config: dict[str, Any],
        trigger_data: dict[str, Any],
        company_id: str,
        db: AsyncSession
    ) -> dict[str, Any]:
        """Execute notify manager action."""
        notification_title = config.get("title", "Notificação automática")
        notification_message = config.get("message", "")
        
        manager_id = trigger_data.get("manager_id") or config.get("manager_id")
        
        logger.info(f"🔔 [AUTOMATION] Notifying manager {manager_id}: {notification_title}")
        
        return {
            "action": "notify_manager",
            "status": "sent",
            "manager_id": manager_id,
            "title": notification_title,
            "message": notification_message
        }
    
    async def _execute_log_activity(
        self,
        config: dict[str, Any],
        trigger_data: dict[str, Any],
        company_id: str
    ) -> dict[str, Any]:
        """Execute log activity action."""
        activity_type = config.get("activity_type", "automation")
        activity_description = config.get("description", "Ação automática executada")
        
        logger.info(f"📝 [AUTOMATION] Logging activity: {activity_type}")
        
        return {
            "action": "log_activity",
            "status": "logged",
            "activity_type": activity_type,
            "description": activity_description
        }
    
    async def _check_cooldown(
        self,
        automation: CommunicationAutomation,
        db: AsyncSession
    ) -> bool:
        """Check if automation cooldown period has passed."""
        cooldown_minutes = int(automation.cooldown_minutes or "0")
        
        if cooldown_minutes <= 0:
            return True
        
        if not automation.last_executed_at:
            return True
        
        cooldown_end = automation.last_executed_at + timedelta(minutes=cooldown_minutes)
        return datetime.utcnow() >= cooldown_end
    
    async def _log_execution(
        self,
        automation_id: uuid.UUID,
        company_id: str,
        trigger_event: str,
        trigger_data: dict[str, Any],
        action_executed: str,
        action_result: dict[str, Any],
        status: str,
        execution_time_ms: int = 0,
        error_message: str = None,
        candidate_id: str = None,
        vacancy_id: str = None,
        db: AsyncSession = None
    ) -> None:
        """Log automation execution for audit."""
        log_entry = AutomationExecutionLog(
            automation_id=automation_id,
            company_id=company_id,
            trigger_event=trigger_event,
            trigger_data=trigger_data,
            candidate_id=candidate_id,
            vacancy_id=vacancy_id,
            action_executed=action_executed,
            action_result=action_result,
            status=status,
            error_message=error_message,
            execution_time_ms=str(execution_time_ms)
        )
        
        if db:
            db.add(log_entry)
    
    async def list_automations(
        self,
        company_id: str,
        is_active: bool | None = None,
        trigger_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
        db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """List automations for a company."""
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            page = await CommunicationAutomationRepository(db).list_paginated(
                company_id,
                is_active=is_active,
                trigger_type=trigger_type,
                limit=limit,
                offset=offset,
            )
            return {
                "automations": [a.to_dict() for a in page["automations"]],
                "total": page["total"],
                "limit": page["limit"],
                "offset": page["offset"],
            }

        finally:
            if should_close:
                await db.close()
    
    async def get_automation(
        self,
        automation_id: str,
        company_id: str,
        db: AsyncSession | None = None
    ) -> CommunicationAutomation | None:
        """Get a single automation by ID."""
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            return await CommunicationAutomationRepository(db).get_by_id_for_company(
                automation_id, company_id
            )

        finally:
            if should_close:
                await db.close()
    
    async def create_automation(
        self,
        company_id: str,
        name: str,
        trigger_type: str,
        action_type: str,
        trigger_config: dict[str, Any] = None,
        action_config: dict[str, Any] = None,
        conditions: list[dict[str, Any]] = None,
        description: str = None,
        is_active: bool = True,
        priority: str = "normal",
        cooldown_minutes: int = 0,
        created_by: str = None,
        db: AsyncSession | None = None
    ) -> CommunicationAutomation:
        """Create a new automation."""
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            automation = CommunicationAutomation(
                company_id=company_id,
                name=name,
                description=description,
                trigger_type=trigger_type,
                trigger_config=trigger_config or {},
                action_type=action_type,
                action_config=action_config or {},
                conditions=conditions or [],
                is_active=is_active,
                priority=priority,
                cooldown_minutes=str(cooldown_minutes),
                created_by=created_by
            )
            
            db.add(automation)
            await db.commit()
            await db.refresh(automation)
            
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.info(f"✅ Created automation: {name} (trigger: {trigger_type}, action: {action_type})")
            
            return automation
            
        except Exception:
            try:
                await db.rollback()
            except Exception:
                pass
            raise
        finally:
            if should_close:
                await db.close()
    
    async def update_automation(
        self,
        automation_id: str,
        company_id: str,
        updates: dict[str, Any],
        updated_by: str = None,
        db: AsyncSession | None = None
    ) -> CommunicationAutomation | None:
        """Update an existing automation."""
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            automation = await self.get_automation(automation_id, company_id, db)
            
            if not automation:
                return None
            
            allowed_fields = [
                "name", "description", "trigger_type", "trigger_config",
                "action_type", "action_config", "conditions", "is_active",
                "priority", "cooldown_minutes"
            ]
            
            for field, value in updates.items():
                if field in allowed_fields:
                    if field == "cooldown_minutes":
                        setattr(automation, field, str(value))
                    else:
                        setattr(automation, field, value)
            
            automation.updated_by = updated_by
            automation.updated_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(automation)
            
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.info(f"✅ Updated automation: {automation.name}")
            
            return automation
            
        except Exception:
            try:
                await db.rollback()
            except Exception:
                pass
            raise
        finally:
            if should_close:
                await db.close()
    
    async def delete_automation(
        self,
        automation_id: str,
        company_id: str,
        db: AsyncSession | None = None
    ) -> bool:
        """Delete an automation."""
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            automation = await self.get_automation(automation_id, company_id, db)
            
            if not automation:
                return False
            
            await db.delete(automation)
            await db.commit()
            
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.info(f"🗑️ Deleted automation: {automation.name}")
            
            return True
            
        except Exception:
            try:
                await db.rollback()
            except Exception:
                pass
            raise
        finally:
            if should_close:
                await db.close()
    
    async def test_automation(
        self,
        automation_id: str,
        company_id: str,
        test_data: dict[str, Any] = None,
        db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """Test an automation without actually executing actions."""
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            automation = await self.get_automation(automation_id, company_id, db)
            
            if not automation:
                return {
                    "success": False,
                    "error": "Automation not found"
                }
            
            test_trigger_data = test_data or {
                "candidate_id": "test-candidate-123",
                "candidate_name": "João Silva (Teste)",
                "candidate_email": "teste@exemplo.com",
                "candidate_phone": "+5511999999999",
                "vacancy_id": "test-vacancy-123",
                "vacancy_title": "Desenvolvedor (Teste)",
                "stage": "screening",
                "previous_stage": "new"
            }
            
            conditions_met = await self.evaluate_conditions(
                automation.conditions or [],
                test_trigger_data
            )
            
            cooldown_ok = await self._check_cooldown(automation, db)
            
            would_execute = conditions_met and cooldown_ok and automation.is_active
            
            return {
                "success": True,
                "automation": automation.to_dict(),
                "test_data": test_trigger_data,
                "evaluation": {
                    "is_active": automation.is_active,
                    "conditions_met": conditions_met,
                    "cooldown_ok": cooldown_ok,
                    "would_execute": would_execute
                },
                "simulated_action": {
                    "action_type": automation.action_type,
                    "action_config": automation.action_config
                } if would_execute else None
            }
            
        finally:
            if should_close:
                await db.close()
    
    async def get_execution_logs(
        self,
        company_id: str,
        automation_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
        db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """Get execution logs for automations."""
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            page = await CommunicationAutomationRepository(db).list_execution_logs(
                company_id,
                automation_id=automation_id,
                limit=limit,
                offset=offset,
            )
            return {
                "logs": [log.to_dict() for log in page["logs"]],
                "total": page["total"],
                "limit": page["limit"],
                "offset": page["offset"],
            }

        finally:
            if should_close:
                await db.close()
    
    def get_ai_suggestions(
        self,
        transition_data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Get AI-powered suggestions for actions based on stage transition.
        
        Args:
            transition_data: Dict containing:
                - from_stage: Previous stage name
                - to_stage: New stage name
                - from_sub_status: Previous sub-status (optional)
                - to_sub_status: New sub-status (optional)
                - candidate_id: Candidate ID (optional)
                - vacancy_id: Vacancy ID (optional)
        
        Returns:
            List of suggestion dicts with:
                - action_type: Type of suggested action
                - confidence_score: 0-1 score indicating confidence
                - recommended: Boolean indicating if this is strongly recommended
                - message_template_id: Optional template ID for the action
                - description: Human-readable description of the suggestion
        """
        to_stage = (transition_data.get("to_stage") or "").lower()
        from_stage = (transition_data.get("from_stage") or "").lower()
        (transition_data.get("to_sub_status") or "").lower()
        
        suggestions = []
        
        if to_stage == "screening":
            suggestions.append({
                "action_type": "triagem_wsi",
                "confidence_score": 0.95,
                "recommended": True,
                "message_template_id": None,
                "description": "Iniciar triagem WSI automatizada para o candidato",
                "priority": 1
            })
            suggestions.append({
                "action_type": "send_email",
                "confidence_score": 0.8,
                "recommended": True,
                "message_template_id": "screening_invite",
                "description": "Enviar email de convite para triagem",
                "priority": 2
            })
        
        elif to_stage.startswith("interview"):
            suggestions.append({
                "action_type": "agendar_entrevista",
                "confidence_score": 0.92,
                "recommended": True,
                "message_template_id": None,
                "description": "Agendar entrevista com o candidato",
                "priority": 1
            })
            suggestions.append({
                "action_type": "send_email",
                "confidence_score": 0.85,
                "recommended": True,
                "message_template_id": "interview_scheduled",
                "description": "Enviar email de confirmação de entrevista",
                "priority": 2
            })
            if "manager" in to_stage:
                suggestions.append({
                    "action_type": "notify_manager",
                    "confidence_score": 0.88,
                    "recommended": True,
                    "message_template_id": None,
                    "description": "Notificar gestor sobre a entrevista agendada",
                    "priority": 3
                })
        
        elif to_stage in ["long_list", "short_list"]:
            suggestions.append({
                "action_type": "send_email",
                "confidence_score": 0.9,
                "recommended": True,
                "message_template_id": "shortlist_approval",
                "description": "Enviar email de aprovação para próxima fase",
                "priority": 1
            })
            suggestions.append({
                "action_type": "notify_recruiter",
                "confidence_score": 0.75,
                "recommended": False,
                "message_template_id": None,
                "description": "Notificar recrutador sobre adição à lista",
                "priority": 2
            })
            if to_stage == "short_list":
                suggestions.append({
                    "action_type": "notify_manager",
                    "confidence_score": 0.85,
                    "recommended": True,
                    "message_template_id": None,
                    "description": "Notificar gestor sobre candidato na shortlist",
                    "priority": 3
                })
        
        elif to_stage.startswith("rejected") or "rejected" in to_stage:
            suggestions.append({
                "action_type": "send_email",
                "confidence_score": 0.95,
                "recommended": True,
                "message_template_id": "rejection_feedback",
                "description": "Enviar email de feedback de reprovação",
                "priority": 1
            })
            suggestions.append({
                "action_type": "log_activity",
                "confidence_score": 0.7,
                "recommended": False,
                "message_template_id": None,
                "description": "Registrar motivo da reprovação para analytics",
                "priority": 2
            })
        
        elif to_stage == "offer":
            suggestions.append({
                "action_type": "send_email",
                "confidence_score": 0.95,
                "recommended": True,
                "message_template_id": "offer_proposal",
                "description": "Enviar email com proposta de emprego",
                "priority": 1
            })
            suggestions.append({
                "action_type": "create_task",
                "confidence_score": 0.8,
                "recommended": True,
                "message_template_id": None,
                "description": "Criar tarefa de follow-up para proposta",
                "priority": 2
            })
            suggestions.append({
                "action_type": "notify_recruiter",
                "confidence_score": 0.85,
                "recommended": True,
                "message_template_id": None,
                "description": "Notificar recrutador sobre envio de proposta",
                "priority": 3
            })
        
        elif to_stage == "hired":
            suggestions.append({
                "action_type": "send_email",
                "confidence_score": 0.98,
                "recommended": True,
                "message_template_id": "welcome_email",
                "description": "Enviar email de boas-vindas ao novo colaborador",
                "priority": 1
            })
            suggestions.append({
                "action_type": "notify_recruiter",
                "confidence_score": 0.9,
                "recommended": True,
                "message_template_id": None,
                "description": "Notificar recrutador sobre contratação concluída",
                "priority": 2
            })
            suggestions.append({
                "action_type": "log_activity",
                "confidence_score": 0.85,
                "recommended": True,
                "message_template_id": None,
                "description": "Registrar contratação para métricas e analytics",
                "priority": 3
            })
        
        elif to_stage == "sourcing":
            suggestions.append({
                "action_type": "send_email",
                "confidence_score": 0.8,
                "recommended": False,
                "message_template_id": "sourcing_outreach",
                "description": "Enviar email de primeiro contato",
                "priority": 1
            })
        
        suggestions.sort(key=lambda x: (not x["recommended"], -x["confidence_score"], x.get("priority", 99)))
        
        logger.debug(
            f"🤖 [AI_SUGGESTIONS] Generated {len(suggestions)} suggestions for transition "
            f"{from_stage} → {to_stage}"
        )
        
        return suggestions


automation_service = AutomationService()


def get_automation_service() -> AutomationService:
    return automation_service
