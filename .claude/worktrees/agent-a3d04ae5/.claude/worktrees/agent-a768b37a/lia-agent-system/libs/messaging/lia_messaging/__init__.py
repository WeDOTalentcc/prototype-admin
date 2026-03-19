"""
lia-messaging — LIA notification and messaging services.

Exports:
    notification_service: NotificationService, notification_service singleton,
                          NotificationType, NotificationChannel, Notification model
    email: send_email
    teams: send_teams_message
    whatsapp: send_whatsapp_message
"""
from lia_messaging.email import send_email
from lia_messaging.teams import send_teams_message
from lia_messaging.whatsapp import send_whatsapp_message

__all__ = [
    "send_email",
    "send_teams_message",
    "send_whatsapp_message",
]
