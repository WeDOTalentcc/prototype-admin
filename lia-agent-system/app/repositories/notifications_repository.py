"""
NotificationsRepository — session-in-constructor pattern.
Covers all DB operations needed by app/api/v1/notifications.py.
"""
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.notification_service import (
    NotificationChannel,
    NotificationType,
    ProactiveNotificationType,
    notification_service,
)

logger = logging.getLogger(__name__)


class NotificationsRepository:
    """Repository that wraps NotificationService, providing a db session."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        category: Optional[str] = None,
        notification_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        return await notification_service.get_notifications(
            user_id=user_id,
            unread_only=unread_only,
            category=category,
            notification_type=notification_type,
            limit=limit,
            offset=offset,
            db=self.db,
        )

    async def get_notification_summary(self, user_id: str) -> Dict[str, Any]:
        return await notification_service.get_notification_summary(user_id, self.db)

    async def create_notification(
        self,
        user_id: str,
        title: str,
        message: Optional[str] = None,
        notification_type: NotificationType = NotificationType.INFO,
        category: Optional[str] = None,
        source_agent: Optional[str] = None,
        related_job_id: Optional[str] = None,
        related_candidate_id: Optional[str] = None,
        action_url: Optional[str] = None,
        action_label: Optional[str] = None,
    ) -> Dict[str, Any]:
        return await notification_service.create_notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            category=category,
            source_agent=source_agent,
            related_job_id=related_job_id,
            related_candidate_id=related_candidate_id,
            action_url=action_url,
            action_label=action_label,
            db=self.db,
        )

    async def mark_as_read(self, notification_id: str, user_id: str) -> bool:
        return await notification_service.mark_as_read(notification_id, user_id, self.db)

    async def mark_all_as_read(self, user_id: str, category: Optional[str] = None) -> int:
        return await notification_service.mark_all_as_read(user_id, category, self.db)

    async def dismiss_notification(self, notification_id: str, user_id: str) -> bool:
        return await notification_service.dismiss_notification(notification_id, user_id, self.db)

    async def get_chat_notifications(
        self,
        user_id: str,
        thread_id: Optional[str] = None,
        undelivered_only: bool = True,
        limit: int = 20,
    ) -> Dict[str, Any]:
        return await notification_service.get_chat_notifications(
            user_id=user_id,
            thread_id=thread_id,
            undelivered_only=undelivered_only,
            limit=limit,
            db=self.db,
        )

    async def mark_chat_notification_delivered(
        self, notification_id: str, user_id: str
    ) -> bool:
        return await notification_service.mark_chat_notification_delivered(
            notification_id, user_id, self.db
        )

    async def mark_chat_notifications_delivered(
        self, notification_ids: List[str], user_id: str
    ) -> int:
        return await notification_service.mark_chat_notifications_delivered(
            notification_ids, user_id, self.db
        )

    async def send_multi_channel_notification(
        self,
        user_id: str,
        title: str,
        message: str,
        channels: List[NotificationChannel],
        notification_type: NotificationType = NotificationType.INFO,
        proactive_type: Optional[ProactiveNotificationType] = None,
        priority: str = "normal",
        data: Optional[Dict[str, Any]] = None,
        related_job_id: Optional[str] = None,
        related_candidate_id: Optional[str] = None,
        suggested_actions: Optional[List[str]] = None,
        thread_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return await notification_service.send_multi_channel_notification(
            user_id=user_id,
            title=title,
            message=message,
            channels=channels,
            notification_type=notification_type,
            proactive_type=proactive_type,
            priority=priority,
            data=data,
            related_job_id=related_job_id,
            related_candidate_id=related_candidate_id,
            suggested_actions=suggested_actions,
            thread_id=thread_id,
            db=self.db,
        )

    async def send_proactive_notification(
        self,
        user_id: str,
        proactive_type: ProactiveNotificationType,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        related_job_id: Optional[str] = None,
        related_candidate_id: Optional[str] = None,
        suggested_actions: Optional[List[str]] = None,
        priority: str = "normal",
    ) -> Dict[str, Any]:
        return await notification_service.send_proactive_notification(
            user_id=user_id,
            proactive_type=proactive_type,
            title=title,
            message=message,
            data=data,
            related_job_id=related_job_id,
            related_candidate_id=related_candidate_id,
            suggested_actions=suggested_actions,
            priority=priority,
            db=self.db,
        )

    async def check_proactive_conditions(
        self, user_id: str, company_id: str
    ) -> List[Dict[str, Any]]:
        from app.domains.automation.services.proactive_alert_service import proactive_alert_service
        return await proactive_alert_service.check_all_conditions(
            user_id=user_id,
            company_id=company_id,
            db=self.db,
        )
