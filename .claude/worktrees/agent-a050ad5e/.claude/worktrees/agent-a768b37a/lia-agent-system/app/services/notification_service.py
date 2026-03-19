"""Backwards-compatibility shim — real implementation in libs/messaging."""
from lia_messaging.notification_service import (  # noqa: F401
    NotificationType,
    ProactiveNotificationType,
    NotificationChannel,
    Notification,
    ChatNotification,
    NotificationService,
    notification_service,
)
