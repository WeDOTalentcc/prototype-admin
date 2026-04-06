"""Backwards-compatibility shim — real implementation in libs/messaging."""
from lia_messaging.notification_service import (  # noqa: F401
    ChatNotification,
    Notification,
    NotificationChannel,
    NotificationService,
    NotificationType,
    ProactiveNotificationType,
    notification_service,
)
