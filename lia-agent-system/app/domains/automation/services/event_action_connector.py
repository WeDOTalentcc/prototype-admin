"""
EventActionConnector - Connects PipelineMonitor events to actions.

Flow:
PipelineMonitor events → EventActionConnector → ProactiveAlertService (notifications)
                                               → AutonomousAgentService (ProactiveActions)
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)


class EventActionConnector:
    """
    Connects pipeline events to the alert and action systems.
    Receives events from PipelineMonitor, creates notifications and ProactiveActions.
    """

    def __init__(self):
        self._alert_service = None
        self._autonomous_service = None
        self._notification_service = None

    def _get_alert_service(self):
        if self._alert_service is None:
            try:
                from app.domains.automation.services.proactive_alert_service import ProactiveAlertService
                self._alert_service = ProactiveAlertService()
            except Exception as e:
                logger.warning(f"Could not load ProactiveAlertService: {e}")
        return self._alert_service

    def _get_autonomous_service(self):
        if self._autonomous_service is None:
            try:
                from app.domains.automation.services.autonomous_agent_service import AutonomousAgentService
                self._autonomous_service = AutonomousAgentService()
            except Exception as e:
                logger.warning(f"Could not load AutonomousAgentService: {e}")
        return self._autonomous_service

    def _get_notification_service(self):
        if self._notification_service is None:
            try:
                from app.services.notification_service import NotificationService
                self._notification_service = NotificationService()
            except Exception as e:
                logger.warning(f"Could not load NotificationService: {e}")
        return self._notification_service

    async def process_events(self, events: list[Any]) -> dict[str, int]:
        """
        Process a batch of PipelineEvents.
        Creates ProactiveActions and sends notifications for each.
        Returns counts of actions created and notifications sent.
        """
        stats = {"actions_created": 0, "notifications_sent": 0, "errors": 0}

        for event in events:
            try:
                action_created = await self._create_action_from_event(event)
                if action_created:
                    stats["actions_created"] += 1

                notification_sent = await self._send_notification_for_event(event)
                if notification_sent:
                    stats["notifications_sent"] += 1
            except Exception as e:
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.error(f"Error processing event {event.event_type}: {e}")
                stats["errors"] += 1

        logger.info(
            f"EventActionConnector processed {len(events)} events: "
            f"{stats['actions_created']} actions, {stats['notifications_sent']} notifications, "
            f"{stats['errors']} errors"
        )
        return stats

    async def _create_action_from_event(self, event) -> bool:
        """Create a ProactiveAction from a PipelineEvent."""
        service = self._get_autonomous_service()
        if not service:
            return False

        try:
            severity_to_priority = {
                "urgent": "high",
                "warning": "normal",
                "info": "low",
            }
            priority = severity_to_priority.get(event.severity, "normal")

            auto_executable = event.suggested_action in [
                "send_batch_rejection", "request_feedback"
            ]

            await service.create_proactive_action(
                company_id=event.company_id,
                action_type=f"pipeline_event:{event.event_type.value}",
                title=event.title,
                description=event.message,
                suggested_action={
                    "handler": event.suggested_action,
                    "params": event.data,
                },
                priority=priority,
                related_job_id=event.vacancy_id,
                related_candidate_id=event.candidate_id,
                trigger_reason=f"pipeline_monitor:{event.event_type.value}",
                auto_executable=auto_executable,
                expires_in_hours=24,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create action from event: {e}")
            return False

    async def _send_notification_for_event(self, event) -> bool:
        """Send a notification for a PipelineEvent."""
        service = self._get_notification_service()
        if not service:
            return False

        try:
            from app.services.notification_service import NotificationType
            severity_map = {
                "urgent": NotificationType.URGENT,
                "warning": NotificationType.WARNING,
                "info": NotificationType.INFO,
            }
            notification_type = severity_map.get(event.severity, NotificationType.INFO)

            await service.create_notification(
                user_id=f"system:{event.company_id}",
                title=event.title,
                message=event.message,
                notification_type=notification_type,
                category="pipeline_monitor",
                metadata={
                    "event_type": event.event_type.value,
                    "suggested_action": event.suggested_action,
                    "action_label": event.action_label,
                    "data": event.data,
                    "candidate_id": event.candidate_id,
                    "vacancy_id": event.vacancy_id,
                    "company_id": event.company_id,
                },
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send notification for event: {e}")
            return False


event_action_connector = EventActionConnector()
