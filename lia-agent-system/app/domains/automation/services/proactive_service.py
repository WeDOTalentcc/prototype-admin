"""
Proactive Service for LIA.
Handles proactive notifications, briefings, and recruiter assistance.
"""
import logging
from datetime import datetime
from enum import Enum, StrEnum
from typing import Any

from app.templates.communication_templates import RecruiterNotificationTemplates

logger = logging.getLogger(__name__)

_event_dispatcher = None


def get_event_dispatcher():
    """Lazy load EventDispatcher to avoid circular imports."""
    global _event_dispatcher
    if _event_dispatcher is None:
        from app.services.event_dispatcher import event_dispatcher
        _event_dispatcher = event_dispatcher
    return _event_dispatcher


class NotificationPriority(StrEnum):
    """Notification priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationType(StrEnum):
    """Types of proactive notifications."""
    DAILY_BRIEFING = "daily_briefing"
    END_OF_DAY = "end_of_day"
    INTERVIEW_REMINDER = "interview_reminder"
    APPROVAL_NEEDED = "approval_needed"
    SCREENING_COMPLETED = "screening_completed"
    CANDIDATE_EXPIRED = "candidate_expired"
    VOLUME_ALERT = "volume_alert"
    CRITICAL_ALERT = "critical_alert"
    WEEKLY_DIGEST = "weekly_digest"


class ProactiveService:
    """
    Service for proactive LIA behavior.
    - Morning briefings
    - End-of-day summaries
    - Interview reminders
    - Approval requests
    - Status updates
    """
    
    def __init__(self):
        self.pending_notifications: list[dict[str, Any]] = []
        self.notification_history: list[dict[str, Any]] = []
        self.recruiter_preferences: dict[str, Any] = {
            "briefing_time": "09:00",
            "end_of_day_time": "18:00",
            "interview_reminder_minutes": 30,
            "preferred_channel": "teams"
        }
    
    async def generate_daily_briefing(
        self,
        recruiter_id: str,
        recruiter_name: str
    ) -> dict[str, Any]:
        """
        Generate morning briefing for recruiter.
        Called proactively at configured time.
        """
        logger.info(f"📅 Generating daily briefing for {recruiter_name}")
        
        briefing_data = await self._gather_briefing_data(recruiter_id)
        
        pending_interviews = briefing_data.get("pending_interviews", 0)
        pending_approvals = briefing_data.get("pending_approvals", 0)
        active_screenings = briefing_data.get("active_screenings", 0)
        candidates_to_contact = briefing_data.get("candidates_to_contact", 0)
        today_tasks = briefing_data.get("today_tasks", [])
        
        message = RecruiterNotificationTemplates.daily_briefing(
            recruiter_name=recruiter_name,
            pending_interviews=pending_interviews,
            pending_approvals=pending_approvals,
            active_screenings=active_screenings,
            candidates_to_contact=candidates_to_contact,
            today_tasks=today_tasks
        )
        
        notification = {
            "type": NotificationType.DAILY_BRIEFING,
            "priority": NotificationPriority.MEDIUM,
            "recruiter_id": recruiter_id,
            "title": "Briefing Diário",
            "message": message,
            "data": briefing_data,
            "created_at": datetime.utcnow().isoformat(),
            "channel": self.recruiter_preferences["preferred_channel"]
        }
        
        await self._send_notification(notification)
        
        return notification
    
    async def generate_end_of_day_summary(
        self,
        recruiter_id: str,
        recruiter_name: str
    ) -> dict[str, Any]:
        """
        Generate end-of-day summary for recruiter.
        Reviews what was accomplished and pending items.
        """
        logger.info(f"🌙 Generating end-of-day summary for {recruiter_name}")
        
        summary_data = await self._gather_day_summary(recruiter_id)
        
        interviews_completed = summary_data.get("interviews_completed", 0)
        candidates_screened = summary_data.get("candidates_screened", 0)
        approvals_given = summary_data.get("approvals_given", 0)
        pending_items = summary_data.get("pending_items", [])
        
        message = RecruiterNotificationTemplates.end_of_day_summary(
            recruiter_name=recruiter_name,
            interviews_completed=interviews_completed,
            candidates_screened=candidates_screened,
            approvals_given=approvals_given,
            pending_items=pending_items
        )
        
        notification = {
            "type": NotificationType.END_OF_DAY,
            "priority": NotificationPriority.LOW,
            "recruiter_id": recruiter_id,
            "title": "Resumo do Dia",
            "message": message,
            "data": summary_data,
            "created_at": datetime.utcnow().isoformat(),
            "channel": self.recruiter_preferences["preferred_channel"]
        }
        
        await self._send_notification(notification)
        
        return notification
    
    async def send_interview_reminder(
        self,
        recruiter_id: str,
        recruiter_name: str,
        candidate_name: str,
        interview_time: datetime,
        interview_link: str
    ) -> dict[str, Any]:
        """
        Send interview reminder to recruiter.
        Called before scheduled interview.
        """
        logger.info(f"🔔 Sending interview reminder to {recruiter_name}")
        
        message = RecruiterNotificationTemplates.interview_reminder(
            recruiter_name=recruiter_name,
            candidate_name=candidate_name,
            interview_time=interview_time,
            interview_link=interview_link
        )
        
        notification = {
            "type": NotificationType.INTERVIEW_REMINDER,
            "priority": NotificationPriority.HIGH,
            "recruiter_id": recruiter_id,
            "title": f"Lembrete: Entrevista com {candidate_name}",
            "message": message,
            "data": {
                "candidate_name": candidate_name,
                "interview_time": interview_time.isoformat(),
                "interview_link": interview_link
            },
            "requires_confirmation": True,
            "created_at": datetime.utcnow().isoformat(),
            "channel": self.recruiter_preferences["preferred_channel"]
        }
        
        await self._send_notification(notification)
        
        return notification
    
    async def request_approval(
        self,
        recruiter_id: str,
        approval_type: str,
        title: str,
        description: str,
        items: list[dict[str, Any]],
        job_id: str | None = None
    ) -> dict[str, Any]:
        """
        Proactively request approval from recruiter.
        Used for candidate profiles, contacts, actions.
        """
        logger.info(f"⚠️ Requesting approval: {title}")
        
        action_items = [item.get("description", str(item)) for item in items]
        
        message = RecruiterNotificationTemplates.approval_needed(
            title=title,
            description=description,
            action_items=action_items
        )
        
        notification = {
            "type": NotificationType.APPROVAL_NEEDED,
            "priority": NotificationPriority.HIGH,
            "recruiter_id": recruiter_id,
            "title": title,
            "message": message,
            "data": {
                "approval_type": approval_type,
                "items": items,
                "job_id": job_id
            },
            "requires_action": True,
            "action_options": ["approve", "reject", "review"],
            "created_at": datetime.utcnow().isoformat(),
            "channel": self.recruiter_preferences["preferred_channel"]
        }
        
        await self._send_notification(notification)
        
        return notification
    
    async def notify_screening_completed(
        self,
        recruiter_id: str,
        candidate_name: str,
        job_title: str,
        wsi_score: float,
        passed: bool,
        strengths: list[str],
        development_areas: list[str],
        session_id: str,
        candidate_id: str | None = None,
        vacancy_id: str | None = None,
        company_id: str | None = None,
        wsi_scores: dict[str, float] | None = None,
        dispatch_event: bool = True,
        hiring_manager_name: str | None = None,
        department: str | None = None,
        confidence: float | None = None,
        wsi_classification: str | None = None
    ) -> dict[str, Any]:
        """
        Notify recruiter that a screening was completed.
        Includes WSI score and structured report with tier information.
        
        Also dispatches screening-completed event to automation handlers.
        """
        logger.info(f"🎯 Notifying screening completed for {candidate_name}")
        
        tier = self._get_tier_from_wsi(wsi_score)
        
        message = RecruiterNotificationTemplates.screening_completed(
            candidate_name=candidate_name,
            job_title=job_title,
            wsi_score=wsi_score,
            passed=passed,
            strengths=strengths,
            development_areas=development_areas,
            candidate_id=candidate_id,
            vacancy_id=vacancy_id,
            hiring_manager_name=hiring_manager_name,
            department=department,
            confidence=confidence,
            wsi_classification=wsi_classification
        )
        
        if tier == "A":
            action_options = ["schedule_now", "approve", "view_report"]
        elif tier == "B":
            action_options = ["approve", "schedule", "view_report"]
        elif tier == "C":
            action_options = ["view_report", "compare_candidates", "review"]
        else:
            action_options = ["view_report", "archive", "send_feedback"]
        
        notification = {
            "type": NotificationType.SCREENING_COMPLETED,
            "priority": NotificationPriority.HIGH if tier in ["A", "B"] else NotificationPriority.MEDIUM,
            "recruiter_id": recruiter_id,
            "title": f"Triagem Concluída - {candidate_name}",
            "message": message,
            "data": {
                "candidate_id": candidate_id,
                "candidate_name": candidate_name,
                "vacancy_id": vacancy_id,
                "job_title": job_title,
                "wsi_score": wsi_score,
                "tier": tier,
                "wsi_classification": wsi_classification,
                "passed": passed,
                "strengths": strengths,
                "development_areas": development_areas,
                "session_id": session_id,
                "hiring_manager_name": hiring_manager_name,
                "department": department,
                "confidence": confidence
            },
            "requires_action": True,
            "action_options": action_options,
            "created_at": datetime.utcnow().isoformat(),
            "channel": self.recruiter_preferences["preferred_channel"]
        }
        
        await self._send_notification(notification)
        
        if dispatch_event and candidate_id and vacancy_id and company_id:
            try:
                dispatcher = get_event_dispatcher()
                await dispatcher.on_screening_completed(
                    candidate_id=candidate_id,
                    vacancy_id=vacancy_id,
                    company_id=company_id,
                    wsi_scores=wsi_scores or {},
                    screening_type="wsi",
                    passed=passed,
                    wsi_score=wsi_score,
                    candidate_name=candidate_name,
                    job_title=job_title,
                    session_id=session_id
                )
            except Exception as e:
                logger.warning(f"⚠️ Failed to dispatch screening-completed event: {e}")
        
        return notification
    
    @staticmethod
    def _get_tier_from_wsi(wsi_score: float) -> str:
        """Calculate candidate tier (A/B/C/D) based on WSI score."""
        if wsi_score >= 4.0:
            return "A"
        elif wsi_score >= 3.0:
            return "B"
        elif wsi_score >= 2.0:
            return "C"
        else:
            return "D"
    
    async def send_critical_alert(
        self,
        recruiter_id: str,
        alert_type: str,
        message: str,
        action_required: str
    ) -> dict[str, Any]:
        """
        Send critical alert that needs immediate attention.
        """
        logger.warning(f"🚨 Critical alert: {alert_type}")
        
        formatted_message = RecruiterNotificationTemplates.critical_alert(
            alert_type=alert_type,
            message=message,
            action_required=action_required
        )
        
        notification = {
            "type": NotificationType.CRITICAL_ALERT,
            "priority": NotificationPriority.CRITICAL,
            "recruiter_id": recruiter_id,
            "title": f"ALERTA: {alert_type}",
            "message": formatted_message,
            "data": {
                "alert_type": alert_type,
                "original_message": message,
                "action_required": action_required
            },
            "requires_action": True,
            "created_at": datetime.utcnow().isoformat(),
            "channel": self.recruiter_preferences["preferred_channel"]
        }
        
        await self._send_notification(notification)
        
        return notification
    
    async def check_expired_screenings(self, job_id: str) -> list[dict[str, Any]]:
        """
        Check for expired screening sessions and notify.
        Called periodically to identify candidates who didn't complete screening.
        """
        expired_candidates: list[dict[str, Any]] = []
        return expired_candidates
    
    async def organize_agenda(
        self,
        recruiter_id: str,
        date: datetime | None = None
    ) -> dict[str, Any]:
        """
        Help organize recruiter's agenda for a day.
        Suggests optimal scheduling and priorities.
        """
        target_date = date or datetime.utcnow()
        
        agenda = {
            "date": target_date.strftime("%Y-%m-%d"),
            "interviews": [],
            "tasks": [],
            "suggested_priorities": [],
            "time_blocks": []
        }
        
        return agenda
    
    async def _gather_briefing_data(self, recruiter_id: str) -> dict[str, Any]:
        """Gather data for daily briefing."""
        return {
            "pending_interviews": 0,
            "pending_approvals": 0,
            "active_screenings": 0,
            "candidates_to_contact": 0,
            "today_tasks": [
                "Revisar candidatos pendentes",
                "Aprovar perfis para contato",
                "Verificar triagens em andamento"
            ]
        }
    
    async def _gather_day_summary(self, recruiter_id: str) -> dict[str, Any]:
        """Gather data for end-of-day summary."""
        return {
            "interviews_completed": 0,
            "candidates_screened": 0,
            "approvals_given": 0,
            "pending_items": []
        }
    
    async def _create_bell_notification(self, notification: dict[str, Any]) -> bool:
        from lia_messaging.notification_service import (
            NotificationChannel,
            notification_service,
        )
        from lia_messaging.notification_service import (
            NotificationType as MsgNT,
        )

        type_map = {
            "critical_alert": MsgNT.URGENT,
            NotificationType.CRITICAL_ALERT: MsgNT.URGENT,
        }
        notif_type_raw = notification.get("type", "")
        notif_type_str = notif_type_raw.value if hasattr(notif_type_raw, "value") else str(notif_type_raw)
        msg_type = type_map.get(notif_type_raw, type_map.get(notif_type_str, MsgNT.INFO))

        category_map = {
            "critical_alert": "system",
            "daily_briefing": "productivity",
            "end_of_day": "productivity",
            "interview_reminder": "pipeline",
            "screening_completed": "pipeline",
            "pipeline_stagnation": "pipeline",
        }
        category = category_map.get(notif_type_str, "system")

        try:
            await notification_service.create_notification(
                user_id=notification.get("recruiter_id", "default_user"),
                title=notification.get("title", ""),
                message=notification.get("message", ""),
                notification_type=msg_type,
                category=category,
                source_agent="proactive_service",
                channels=[NotificationChannel.BELL.value],
            )
            return True
        except Exception:
            logger.warning("Bell notification creation failed", exc_info=True)
            return False

    async def _send_notification(self, notification: dict[str, Any]) -> bool:
        """
        Send notification via configured channel.
        Currently supports Teams and internal chat.
        """
        channel = notification.get("channel", "teams")
        
        self.notification_history.append(notification)

        await self._create_bell_notification(notification)
        
        if channel == "teams":
            return await self._send_via_teams(notification)
        else:
            return await self._send_via_chat(notification)
    
    async def _send_via_teams(self, notification: dict[str, Any]) -> bool:
        """Send notification via Microsoft Teams."""
        logger.info(f"📤 Sending notification via Teams: {notification.get('title')}")
        return True
    
    async def _send_via_chat(self, notification: dict[str, Any]) -> bool:
        """Send notification via internal chat."""
        logger.info(f"💬 Sending notification via Chat: {notification.get('title')}")
        return True
    
    def get_pending_notifications(self, recruiter_id: str) -> list[dict[str, Any]]:
        """Get pending notifications for recruiter."""
        return [
            n for n in self.pending_notifications
            if n.get("recruiter_id") == recruiter_id
        ]
    
    def get_notification_history(
        self,
        recruiter_id: str,
        limit: int = 50
    ) -> list[dict[str, Any]]:
        """Get notification history for recruiter."""
        history = [
            n for n in self.notification_history
            if n.get("recruiter_id") == recruiter_id
        ]
        return history[-limit:]


proactive_service = ProactiveService()
