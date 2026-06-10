"""
Notification Service - Intelligent notification management.

This service manages notifications for recruiters including:
- Push browser notifications
- In-app notifications (bell)
- Chat inline notifications
- Teams integration
- Email notifications
- Notification preferences
- Notification history
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Column, String, Text, DateTime, Boolean, JSON, Integer, select, and_, desc, func
import logging
import uuid
from enum import Enum

from lia_config.database import Base, AsyncSessionLocal

logger = logging.getLogger(__name__)


class NotificationType(str, Enum):
    """Types of notifications - priority/severity."""
    URGENT = "urgent"
    ACTION_REQUIRED = "action_required"
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"


class ProactiveNotificationType(str, Enum):
    """Specific proactive notification types."""
    CANDIDATES_ADDED = "candidates_added"
    CALIBRATION_NEEDED = "calibration_needed"
    GOAL_REACHED = "goal_reached"
    EXPAND_TO_GLOBAL = "expand_to_global"
    LOW_ADHERENCE_APPLICANT = "low_adherence_applicant"
    MORNING_BRIEFING = "morning_briefing"
    AFTERNOON_SUMMARY = "afternoon_summary"
    APPROVAL_REQUEST = "approval_request"
    SCREENING_COMPLETED = "screening_completed"
    INTERVIEW_REMINDER = "interview_reminder"
    VACANCY_EXPIRING = "vacancy_expiring"
    NEW_APPLICATION = "new_application"
    TASK_ASSIGNED = "task_assigned"
    WEEKLY_DIGEST = "weekly_digest"


class NotificationChannel(str, Enum):
    """Notification delivery channels."""
    CHAT = "chat"
    BELL = "bell"
    TEAMS = "teams"
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    IN_APP = "in_app"
    PUSH = "push"


class Notification(Base):
    """Notification model for bell/in-app notifications."""
    __tablename__ = "notifications"
    __table_args__ = {"extend_existing": True}
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=True)
    
    notification_type = Column(String(50), default="info")
    proactive_type = Column(String(50), nullable=True)
    category = Column(String(50), nullable=True)
    priority = Column(String(20), default="normal")
    
    source_agent = Column(String(50), nullable=True)
    source_trigger = Column(String(100), nullable=True)
    
    related_job_id = Column(String, nullable=True)
    related_candidate_id = Column(String, nullable=True)
    related_task_id = Column(String, nullable=True)
    
    action_url = Column(String(500), nullable=True)
    action_label = Column(String(100), nullable=True)
    
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)
    
    is_dismissed = Column(Boolean, default=False)
    dismissed_at = Column(DateTime, nullable=True)
    
    channels = Column(JSON, default=list)
    channels_sent = Column(JSON, default=list)
    extra_data = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "message": self.message,
            "notification_type": self.notification_type,
            "proactive_type": self.proactive_type,
            "category": self.category,
            "priority": self.priority,
            "source_agent": self.source_agent,
            "source_trigger": self.source_trigger,
            "related_job_id": self.related_job_id,
            "related_candidate_id": self.related_candidate_id,
            "related_task_id": self.related_task_id,
            "action_url": self.action_url,
            "action_label": self.action_label,
            "is_read": self.is_read,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "is_dismissed": self.is_dismissed,
            "channels": self.channels,
            "channels_sent": self.channels_sent,
            "extra_data": self.extra_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


class ChatNotification(Base):
    """Chat inline notification model - messages that appear in the chat interface."""
    __tablename__ = "chat_notifications"
    __table_args__ = {"extend_existing": True}
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    thread_id = Column(String, nullable=True)
    
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    
    notification_type = Column(String(50), default="info")
    proactive_type = Column(String(50), nullable=True)
    priority = Column(String(20), default="normal")
    
    related_job_id = Column(String, nullable=True)
    related_candidate_id = Column(String, nullable=True)
    
    suggested_actions = Column(JSON, default=list)
    extra_data = Column(JSON, default=dict)
    
    is_delivered = Column(Boolean, default=False)
    delivered_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "thread_id": self.thread_id,
            "title": self.title,
            "message": self.message,
            "notification_type": self.notification_type,
            "proactive_type": self.proactive_type,
            "priority": self.priority,
            "related_job_id": self.related_job_id,
            "related_candidate_id": self.related_candidate_id,
            "suggested_actions": self.suggested_actions,
            "extra_data": self.extra_data,
            "is_delivered": self.is_delivered,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class NotificationService:
    """
    Service for managing notifications.
    """
    
    async def create_notification(
        self,
        user_id: str,
        title: str,
        message: Optional[str] = None,
        notification_type: NotificationType = NotificationType.INFO,
        category: Optional[str] = None,
        source_agent: Optional[str] = None,
        source_trigger: Optional[str] = None,
        related_job_id: Optional[str] = None,
        related_candidate_id: Optional[str] = None,
        related_task_id: Optional[str] = None,
        action_url: Optional[str] = None,
        action_label: Optional[str] = None,
        channels: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        expires_in_hours: Optional[int] = None,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        Create a new notification.
        
        Args:
            user_id: Target user ID
            title: Notification title
            message: Optional detailed message
            notification_type: Type of notification
            category: Category (e.g., 'interview', 'task', 'alert')
            source_agent: Agent that generated the notification
            source_trigger: Trigger that caused the notification
            related_job_id: Related job vacancy ID
            related_candidate_id: Related candidate ID
            related_task_id: Related task ID
            action_url: URL for action button
            action_label: Label for action button
            channels: Delivery channels
            metadata: Additional metadata
            expires_in_hours: Hours until notification expires
            db: Database session
            
        Returns:
            Created notification data
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            expires_at = None
            if expires_in_hours:
                expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
            
            notification = Notification(
                user_id=user_id,
                title=title,
                message=message,
                notification_type=notification_type.value if isinstance(notification_type, NotificationType) else notification_type,
                category=category,
                source_agent=source_agent,
                source_trigger=source_trigger,
                related_job_id=related_job_id,
                related_candidate_id=related_candidate_id,
                related_task_id=related_task_id,
                action_url=action_url,
                action_label=action_label,
                channels=channels or [NotificationChannel.IN_APP.value],
                extra_data=metadata or {},
                expires_at=expires_at
            )
            
            db.add(notification)
            await db.commit()
            await db.refresh(notification)
            
            logger.info(f"🔔 Notification created for user {user_id}: {title}")
            
            return notification.to_dict()
            
        finally:
            if should_close:
                await db.close()
    
    async def get_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        category: Optional[str] = None,
        notification_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        Get notifications for a user.
        
        Args:
            user_id: User ID
            unread_only: Only return unread notifications
            category: Filter by category
            notification_type: Filter by type
            limit: Maximum number of notifications
            offset: Offset for pagination
            db: Database session
            
        Returns:
            List of notifications with metadata
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            conditions = [
                Notification.user_id == user_id,
                Notification.is_dismissed == False
            ]
            
            now = datetime.utcnow()
            conditions.append(
                (Notification.expires_at.is_(None)) | (Notification.expires_at > now)
            )
            
            if unread_only:
                conditions.append(Notification.is_read == False)
            
            if category:
                conditions.append(Notification.category == category)
            
            if notification_type:
                conditions.append(Notification.notification_type == notification_type)
            
            result = await db.execute(
                select(Notification)
                .where(and_(*conditions))
                .order_by(desc(Notification.created_at))
                .limit(limit)
                .offset(offset)
            )
            
            notifications = [n.to_dict() for n in result.scalars()]
            
            unread_count_result = await db.execute(
                select(Notification)
                .where(and_(
                    Notification.user_id == user_id,
                    Notification.is_read == False,
                    Notification.is_dismissed == False
                ))
            )
            unread_count = len(list(unread_count_result.scalars()))
            
            urgent_count_result = await db.execute(
                select(Notification)
                .where(and_(
                    Notification.user_id == user_id,
                    Notification.notification_type == NotificationType.URGENT.value,
                    Notification.is_read == False,
                    Notification.is_dismissed == False
                ))
            )
            urgent_count = len(list(urgent_count_result.scalars()))
            
            return {
                "notifications": notifications,
                "total": len(notifications),
                "unread_count": unread_count,
                "urgent_count": urgent_count,
                "has_more": len(notifications) == limit
            }
            
        finally:
            if should_close:
                await db.close()
    
    async def mark_as_read(
        self,
        notification_id: str,
        user_id: str,
        db: Optional[AsyncSession] = None
    ) -> bool:
        """Mark a notification as read."""
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            result = await db.execute(
                select(Notification).where(
                    and_(
                        Notification.id == notification_id,
                        Notification.user_id == user_id
                    )
                )
            )
            notification = result.scalar_one_or_none()
            
            if notification:
                notification.is_read = True
                notification.read_at = datetime.utcnow()
                await db.commit()
                return True
            
            return False
            
        finally:
            if should_close:
                await db.close()
    
    async def mark_all_as_read(
        self,
        user_id: str,
        category: Optional[str] = None,
        db: Optional[AsyncSession] = None
    ) -> int:
        """Mark all notifications as read for a user."""
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            conditions = [
                Notification.user_id == user_id,
                Notification.is_read == False
            ]
            
            if category:
                conditions.append(Notification.category == category)
            
            result = await db.execute(
                select(Notification).where(and_(*conditions))
            )
            notifications = list(result.scalars())
            
            now = datetime.utcnow()
            for notification in notifications:
                notification.is_read = True
                notification.read_at = now
            
            await db.commit()
            
            return len(notifications)
            
        finally:
            if should_close:
                await db.close()
    
    async def dismiss_notification(
        self,
        notification_id: str,
        user_id: str,
        db: Optional[AsyncSession] = None
    ) -> bool:
        """Dismiss a notification."""
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            result = await db.execute(
                select(Notification).where(
                    and_(
                        Notification.id == notification_id,
                        Notification.user_id == user_id
                    )
                )
            )
            notification = result.scalar_one_or_none()
            
            if notification:
                notification.is_dismissed = True
                notification.dismissed_at = datetime.utcnow()
                await db.commit()
                return True
            
            return False
            
        finally:
            if should_close:
                await db.close()
    
    async def get_notification_summary(
        self,
        user_id: str,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """Get notification summary for header badge."""
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            now = datetime.utcnow()
            
            base_conditions = [
                Notification.user_id == user_id,
                Notification.is_read == False,
                Notification.is_dismissed == False,
                (Notification.expires_at.is_(None)) | (Notification.expires_at > now)
            ]
            
            unread_result = await db.execute(
                select(Notification).where(and_(*base_conditions))
            )
            unread = list(unread_result.scalars())
            
            urgent_count = sum(1 for n in unread if n.notification_type == NotificationType.URGENT.value)
            action_count = sum(1 for n in unread if n.notification_type == NotificationType.ACTION_REQUIRED.value)
            
            return {
                "unread_count": len(unread),
                "urgent_count": urgent_count,
                "action_required_count": action_count,
                "show_badge": len(unread) > 0,
                "badge_type": "urgent" if urgent_count > 0 else ("action" if action_count > 0 else "info")
            }
            
        finally:
            if should_close:
                await db.close()
    
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
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        Envia notificação para múltiplos canais.
        
        Args:
            user_id: Target user ID
            title: Notification title
            message: Detailed message
            channels: List of channels to send to (CHAT, BELL, TEAMS)
            notification_type: Type/severity (INFO, SUCCESS, WARNING, etc)
            proactive_type: Specific proactive notification type
            priority: Priority level (low, normal, high, urgent)
            data: Additional data/metadata
            related_job_id: Related job vacancy ID
            related_candidate_id: Related candidate ID
            suggested_actions: List of suggested actions for chat
            thread_id: Thread ID for chat context
            db: Database session
            
        Returns:
            {
                "notification_id": "...",
                "sent_to": ["chat", "bell"],
                "failed": [],
                "created_at": "..."
            }
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        notification_id = str(uuid.uuid4())
        results = {
            "notification_id": notification_id,
            "sent_to": [],
            "failed": [],
            "created_at": datetime.utcnow().isoformat()
        }
        
        try:
            for channel in channels:
                try:
                    if channel == NotificationChannel.CHAT:
                        await self._send_to_chat(
                            user_id=user_id,
                            title=title,
                            message=message,
                            notification_type=notification_type,
                            proactive_type=proactive_type,
                            priority=priority,
                            data=data,
                            related_job_id=related_job_id,
                            related_candidate_id=related_candidate_id,
                            suggested_actions=suggested_actions,
                            thread_id=thread_id,
                            db=db
                        )
                        results["sent_to"].append(channel.value)
                        logger.info(f"💬 Chat notification sent to user {user_id}")
                    
                    elif channel == NotificationChannel.BELL or channel == NotificationChannel.IN_APP:
                        await self._send_to_bell(
                            user_id=user_id,
                            title=title,
                            message=message,
                            notification_type=notification_type,
                            proactive_type=proactive_type,
                            priority=priority,
                            data=data,
                            related_job_id=related_job_id,
                            related_candidate_id=related_candidate_id,
                            db=db
                        )
                        results["sent_to"].append(channel.value)
                        logger.info(f"🔔 Bell notification sent to user {user_id}")
                    
                    elif channel == NotificationChannel.TEAMS:
                        await self._send_to_teams(
                            user_id=user_id,
                            title=title,
                            message=message,
                            notification_type=notification_type,
                            data=data
                        )
                        results["sent_to"].append(channel.value)
                        logger.info(f"📱 Teams notification sent to user {user_id}")
                    
                    elif channel == NotificationChannel.EMAIL:
                        # Guard: system:-prefixed user_ids are service accounts with no
                        # real DB row. The UUID lookup would raise "invalid UUID 'system:...'
                        # length must be between 32..36" (30 occurrences in logs). Skip email
                        # for service accounts silently -- they have no inbox.
                        if isinstance(user_id, str) and user_id.startswith("system:"):
                            logger.debug(
                                "Skipping email channel for service-account user_id '%s'",
                                user_id,
                            )
                            continue
                        recipient_email = data.get("recipient_email") if data else None
                        if not recipient_email:
                            from app.core.database import AsyncSessionLocal as DBSession
                            from app.auth.models import User
                            async with DBSession() as temp_db:
                                from sqlalchemy import select as sql_select
                                user_result = await temp_db.execute(
                                    sql_select(User).where(User.id == user_id)
                                )
                                user = user_result.scalar_one_or_none()
                                if user:
                                    recipient_email = user.email
                        
                        if recipient_email:
                            await self._send_to_email(
                                recipient_email=recipient_email,
                                title=title,
                                message=message,
                                notification_type=notification_type,
                                data=data
                            )
                            results["sent_to"].append(channel.value)
                            logger.info(f"📧 Email notification sent to {recipient_email}")
                        else:
                            logger.warning(f"No email found for user {user_id}, skipping email channel")

                    elif channel == NotificationChannel.WHATSAPP:
                        # P0-2 (auditoria Configuracoes): canal WhatsApp de alertas
                        # internos. User nao possui telefone hoje; envia SO se um
                        # recipient_phone vier em data. NUNCA ignorar em silencio
                        # (REGRA 4): loga aviso + marca failed. Future-proof p/ quando
                        # houver coleta de telefone do recrutador.
                        recipient_phone = data.get("recipient_phone") if data else None
                        if recipient_phone:
                            try:
                                from app.domains.communication.services.whatsapp_service import (
                                    WhatsAppService,
                                )
                                _wa = WhatsAppService()
                                await _wa.send_message(
                                    to_phone=recipient_phone,
                                    message=f"{title}\n\n{message}",
                                )
                                results["sent_to"].append(channel.value)
                                logger.info(f"WhatsApp alert sent to {recipient_phone}")
                            except Exception as _wa_exc:
                                logger.error(f"WhatsApp alert send failed: {_wa_exc}")
                                results["failed"].append({"channel": channel.value, "error": str(_wa_exc)})
                        else:
                            logger.warning(
                                "WhatsApp alert solicitado mas recrutador sem telefone "
                                "(User sem campo phone); canal ignorado para user %s. "
                                "Habilitar exige coleta de telefone do recrutador.",
                                user_id,
                            )
                            results["failed"].append({
                                "channel": channel.value,
                                "error": "no recipient_phone (recruiter phone not collected)",
                            })
                        
                except Exception as e:
                    logger.error(f"Failed to send to channel {channel}: {e}")
                    results["failed"].append({
                        "channel": channel.value,
                        "error": str(e)
                    })
            
            return results
            
        finally:
            if should_close:
                await db.close()
    
    async def _send_to_chat(
        self,
        user_id: str,
        title: str,
        message: str,
        notification_type: NotificationType,
        proactive_type: Optional[ProactiveNotificationType] = None,
        priority: str = "normal",
        data: Optional[Dict[str, Any]] = None,
        related_job_id: Optional[str] = None,
        related_candidate_id: Optional[str] = None,
        suggested_actions: Optional[List[str]] = None,
        thread_id: Optional[str] = None,
        db: Optional[AsyncSession] = None
    ):
        """Adiciona notificação à fila de mensagens do chat."""
        chat_notification = ChatNotification(
            user_id=user_id,
            thread_id=thread_id,
            title=title,
            message=message,
            notification_type=notification_type.value if isinstance(notification_type, NotificationType) else notification_type,
            proactive_type=proactive_type.value if isinstance(proactive_type, ProactiveNotificationType) else proactive_type,
            priority=priority,
            related_job_id=related_job_id,
            related_candidate_id=related_candidate_id,
            suggested_actions=suggested_actions or [],
            extra_data=data or {}
        )
        
        db.add(chat_notification)
        await db.commit()
        await db.refresh(chat_notification)
        
        return chat_notification.to_dict()
    
    async def _send_to_bell(
        self,
        user_id: str,
        title: str,
        message: str,
        notification_type: NotificationType,
        proactive_type: Optional[ProactiveNotificationType] = None,
        priority: str = "normal",
        data: Optional[Dict[str, Any]] = None,
        related_job_id: Optional[str] = None,
        related_candidate_id: Optional[str] = None,
        db: Optional[AsyncSession] = None
    ):
        """Adiciona notificação ao contador do sino (in-app)."""
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type.value if isinstance(notification_type, NotificationType) else notification_type,
            proactive_type=proactive_type.value if isinstance(proactive_type, ProactiveNotificationType) else proactive_type,
            priority=priority,
            related_job_id=related_job_id,
            related_candidate_id=related_candidate_id,
            channels=[NotificationChannel.BELL.value],
            channels_sent=[NotificationChannel.BELL.value],
            extra_data=data or {}
        )
        
        db.add(notification)
        await db.commit()
        await db.refresh(notification)
        
        return notification.to_dict()
    
    async def _send_to_teams(
        self,
        user_id: str,
        title: str,
        message: str,
        notification_type: NotificationType,
        data: Optional[Dict[str, Any]] = None
    ):
        """Send notification to Teams channel with adaptive card support."""
        try:
            from app.domains.communication.services.teams_service import teams_service

            # E2 (2026-06-09): resolve webhook PER-TENANT. Antes send_adaptive_card/
            # send_message eram chamados sem webhook_url -> caíam no global
            # TEAMS_WEBHOOK_URL -> alerta de uma empresa ia pro canal Teams de
            # outra (gap multi-tenant). company_id vem em data (propagado no E1).
            webhook_url = None
            _company_id = data.get("company_id") if data else None
            if _company_id:
                from app.core.database import AsyncSessionLocal
                from app.domains.communication.services.teams_service import (
                    resolve_tenant_teams_webhook_url,
                )
                async with AsyncSessionLocal() as _wh_db:
                    webhook_url, _wh_src = await resolve_tenant_teams_webhook_url(
                        _company_id, _wh_db
                    )
            
            actions = data.get("actions", []) if data else []
            
            if actions:
                card_actions = []
                for action in actions:
                    card_actions.append({
                        "type": "Action.OpenUrl",
                        "title": action.get("label", "Ver"),
                        "url": action.get("url", "")
                    })
                
                adaptive_card = {
                    "type": "message",
                    "attachments": [{
                        "contentType": "application/vnd.microsoft.card.adaptive",
                        "content": {
                            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                            "type": "AdaptiveCard",
                            "version": "1.4",
                            "body": [
                                {
                                    "type": "TextBlock",
                                    "text": title,
                                    "weight": "bolder",
                                    "size": "medium"
                                },
                                {
                                    "type": "TextBlock",
                                    "text": message,
                                    "wrap": True
                                }
                            ],
                            "actions": card_actions
                        }
                    }]
                }
                
                if data and data.get("wsi_score"):
                    adaptive_card["attachments"][0]["content"]["body"].insert(1, {
                        "type": "FactSet",
                        "facts": [
                            {"title": "Score WSI", "value": f"{data['wsi_score']:.1f}/5.0"},
                            {"title": "Candidato", "value": data.get("candidate_name", "N/A")},
                            {"title": "Cargo", "value": data.get("job_title", "N/A")}
                        ]
                    })
                
                await teams_service.send_adaptive_card(adaptive_card, webhook_url=webhook_url)
                logger.info(f"Teams adaptive card sent for user {user_id}: {title}")
            else:
                await teams_service.send_message(
                    text=message,
                    title=title,
                    webhook_url=webhook_url
                )
                logger.info(f"Teams simple message sent for user {user_id}: {title}")
            
        except Exception as e:
            logger.error(f"Error sending Teams notification: {e}")
            raise
    
    async def _send_to_email(
        self,
        recipient_email: str,
        title: str,
        message: str,
        notification_type: NotificationType,
        data: Optional[Dict[str, Any]] = None
    ):
        """Send notification via email using Resend provider."""
        try:
            from app.domains.communication.services.email_service import EmailService

            email_service = EmailService()

            job_title = data.get("job_title", "") if data else ""
            candidates_added = data.get("candidates_added", 0) if data else 0
            action_url = data.get("action_url", "") if data else ""
            notification_id = data.get("notification_id", "") if data else ""
            company_id = data.get("company_id", "") if data else ""

            html_body = f"""
<html>
<body style="font-family: 'Open Sans', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
    <div style="background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%); padding: 30px; border-radius: 12px 12px 0 0;">
        <h1 style="color: #00d4aa; margin: 0; font-size: 24px;">🎯 {title}</h1>
    </div>

    <div style="background: #ffffff; padding: 30px; border: 1px solid #e5e5e5;">
        <p style="font-size: 16px; margin-bottom: 20px;">{message}</p>

        {"<div style='background: #f0fdf4; border-left: 4px solid #00d4aa; padding: 15px; margin: 20px 0;'><strong>📊 Resumo:</strong><br>• Candidatos adicionados: " + str(candidates_added) + "<br>• Vaga: " + job_title + "</div>" if candidates_added else ""}

        {f'<a href="{action_url}" style="display: inline-block; background: #00d4aa; color: #000; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: 600; margin-top: 15px;">Ver Pipeline</a>' if action_url else ""}
    </div>

    <div style="background: #f5f5f5; padding: 20px; border-radius: 0 0 12px 12px; text-align: center;">
        <p style="color: #666; font-size: 12px; margin: 0;">
            LIA - Learning Intelligence Assistant<br>
            Plataforma de Recrutamento Inteligente
        </p>
    </div>
</body>
</html>
"""

            # ── Email Tracking (COMP-7) ──────────────────────────────────────────
            # Injeta pixel de abertura + envolve action_url com redirect rastreado.
            # Fail-safe: tracking nunca bloqueia envio.
            # LGPD Art. 7 VI: base legal = interesse legítimo.
            try:
                from app.domains.communication.services.email_tracking_service import email_tracking_service
                _track_notif_id = notification_id or title[:64]
                _track_company_id = company_id or "platform"
                _token = email_tracking_service.generate_tracking_token(
                    notification_id=_track_notif_id,
                    company_id=_track_company_id,
                    recipient_email=recipient_email,
                )
                html_body = email_tracking_service.inject_pixel_and_links(
                    html_body=html_body,
                    token=_token,
                    action_url=action_url or None,
                )
                # Persiste token em background (não bloqueia envio)
                import asyncio
                from app.core.database import AsyncSessionLocal
                async def _persist_token():
                    try:
                        async with AsyncSessionLocal() as _db:
                            await email_tracking_service.create_tracking_token(
                                db=_db,
                                notification_id=_track_notif_id,
                                company_id=_track_company_id,
                                recipient_email=recipient_email,
                            )
                            await _db.commit()
                    except Exception:
                        pass  # fail-safe: token perdido não impede envio
                asyncio.ensure_future(_persist_token())
            except Exception as _te:
                logger.debug("[EmailTracking] tracking inject failed (non-blocking): %s", _te)
            # ────────────────────────────────────────────────────────────────────

            text_body = f"""
{title}

{message}

{"Candidatos adicionados: " + str(candidates_added) if candidates_added else ""}
{"Vaga: " + job_title if job_title else ""}

{action_url if action_url else ""}

---
LIA - Learning Intelligence Assistant
Plataforma de Recrutamento Inteligente
"""

            success = await email_service._send_email_provider(
                to_email=recipient_email,
                subject=title,
                body_html=html_body,
                body_text=text_body.strip()
            )

            if success:
                logger.info(f"📧 Email sent successfully to {recipient_email}")
            else:
                logger.error(f"Failed to send email to {recipient_email}")
                raise Exception("Email sending failed")

        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
            raise
    
    async def get_chat_notifications(
        self,
        user_id: str,
        thread_id: Optional[str] = None,
        undelivered_only: bool = True,
        limit: int = 20,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """Get pending chat notifications for inline display."""
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            conditions = [ChatNotification.user_id == user_id]
            
            if thread_id:
                conditions.append(ChatNotification.thread_id == thread_id)
            
            if undelivered_only:
                conditions.append(ChatNotification.is_delivered == False)
            
            result = await db.execute(
                select(ChatNotification)
                .where(and_(*conditions))
                .order_by(desc(ChatNotification.created_at))
                .limit(limit)
            )
            
            notifications = [n.to_dict() for n in result.scalars()]
            
            return {
                "notifications": notifications,
                "total": len(notifications),
                "has_pending": len(notifications) > 0
            }
            
        finally:
            if should_close:
                await db.close()
    
    async def mark_chat_notification_delivered(
        self,
        notification_id: str,
        user_id: str,
        db: Optional[AsyncSession] = None
    ) -> bool:
        """Mark a chat notification as delivered."""
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            result = await db.execute(
                select(ChatNotification).where(
                    and_(
                        ChatNotification.id == notification_id,
                        ChatNotification.user_id == user_id
                    )
                )
            )
            notification = result.scalar_one_or_none()
            
            if notification:
                notification.is_delivered = True
                notification.delivered_at = datetime.utcnow()
                await db.commit()
                return True
            
            return False
            
        finally:
            if should_close:
                await db.close()
    
    async def mark_chat_notifications_delivered(
        self,
        notification_ids: List[str],
        user_id: str,
        db: Optional[AsyncSession] = None
    ) -> int:
        """Mark multiple chat notifications as delivered."""
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            result = await db.execute(
                select(ChatNotification).where(
                    and_(
                        ChatNotification.id.in_(notification_ids),
                        ChatNotification.user_id == user_id,
                        ChatNotification.is_delivered == False
                    )
                )
            )
            notifications = list(result.scalars())
            
            now = datetime.utcnow()
            for notification in notifications:
                notification.is_delivered = True
                notification.delivered_at = now
            
            await db.commit()
            
            return len(notifications)
            
        finally:
            if should_close:
                await db.close()
    
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
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        Convenience method to send proactive notifications to both chat and bell.
        """
        channels = [NotificationChannel.CHAT, NotificationChannel.BELL]
        
        notification_type = NotificationType.INFO
        if proactive_type in [ProactiveNotificationType.GOAL_REACHED, ProactiveNotificationType.SCREENING_COMPLETED]:
            notification_type = NotificationType.SUCCESS
        elif proactive_type in [ProactiveNotificationType.CALIBRATION_NEEDED, ProactiveNotificationType.VACANCY_EXPIRING]:
            notification_type = NotificationType.WARNING
        elif proactive_type == ProactiveNotificationType.APPROVAL_REQUEST:
            notification_type = NotificationType.ACTION_REQUIRED
        
        return await self.send_multi_channel_notification(
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
            db=db
        )
    
    @staticmethod
    def _get_tier_from_wsi(wsi_score: float) -> str:
        """
        Calculate candidate tier (A/B/C/D) based on WSI score.
        
        WSI Scale (0-5):
        - A: 4.0-5.0 (Excelente)
        - B: 3.0-3.9 (Bom)
        - C: 2.0-2.9 (Adequado)
        - D: 0.0-1.9 (Insuficiente)
        """
        if wsi_score >= 4.0:
            return "A"
        elif wsi_score >= 3.0:
            return "B"
        elif wsi_score >= 2.0:
            return "C"
        else:
            return "D"
    
    @staticmethod
    def _get_tier_recommendation(tier: str, passed: bool) -> str:
        """Get recommendation text based on tier."""
        recommendations = {
            "A": "Candidato excepcional - Priorizar para entrevista imediata",
            "B": "Bom candidato - Recomendado para próxima etapa",
            "C": "Candidato adequado - Avaliar com outros candidatos",
            "D": "Candidato não atende requisitos mínimos - Considerar arquivar"
        }
        return recommendations.get(tier, "Avaliação pendente")
    
    async def notify_recruiter_screening_completed(
        self,
        db: AsyncSession,
        recruiter_id: str,
        candidate_id: str,
        candidate_name: str,
        vacancy_id: str,
        vacancy_title: str,
        company_id: str,
        passed: bool,
        wsi_score: float,
        suggested_stage: str,
        confidence: float,
        channels: Optional[List[str]] = None,
        hiring_manager_name: Optional[str] = None,
        department: Optional[str] = None,
        wsi_classification: Optional[str] = None
    ) -> str:
        """
        Create notification for recruiter about screening completion.
        
        Args:
            db: Database session
            recruiter_id: ID of the recruiter to notify
            candidate_id: ID of the candidate who completed screening
            candidate_name: Name of the candidate
            vacancy_id: ID of the job vacancy
            vacancy_title: Title of the job vacancy
            company_id: Company ID for context
            passed: Whether the candidate passed screening
            wsi_score: WSI score (0-5 scale)
            suggested_stage: Suggested next stage for the candidate
            confidence: Confidence score for the recommendation (0-1)
            channels: Optional list of channels to send to (defaults to ["bell", "email"])
            hiring_manager_name: Optional name of the hiring manager for the vacancy
            department: Optional department name
            wsi_classification: Optional WSI classification text (e.g., "Excelente", "Bom")
            
        Returns:
            Notification ID
        """
        tier = self._get_tier_from_wsi(wsi_score)
        tier_recommendation = self._get_tier_recommendation(tier, passed)
        
        if passed:
            recommendation = f"Aprovado - Sugerido: {suggested_stage}"
            action_label = "Aprovar transição"
        else:
            recommendation = "Não aprovado - Revisão recomendada"
            action_label = "Ver detalhes"
        
        title = f"Triagem concluída: {candidate_name}"
        
        message_lines = [
            f"📋 Vaga: {vacancy_title} (ID: {vacancy_id[:8]}...)",
            f"👤 Candidato: {candidate_name} (ID: {candidate_id[:8]}...)",
        ]
        
        if hiring_manager_name:
            message_lines.append(f"👔 Gestor: {hiring_manager_name}")
        
        if department:
            message_lines.append(f"🏢 Departamento: {department}")
        
        message_lines.extend([
            "",
            f"📊 Score WSI: {wsi_score:.1f}/5 | Tier: {tier}",
            f"🎯 Confiança: {confidence:.0%}",
            f"💡 Recomendação: {tier_recommendation}"
        ])
        
        if wsi_classification:
            message_lines.insert(-1, f"📈 Classificação: {wsi_classification}")
        
        message = "\n".join(message_lines)
        
        action_url = f"/funil-de-talentos/candidato/{candidate_id}?job={vacancy_id}"
        
        notification_channels = channels or [NotificationChannel.BELL.value, NotificationChannel.EMAIL.value]
        channel_enums = [
            NotificationChannel(ch) if isinstance(ch, str) else ch 
            for ch in notification_channels
        ]
        
        if tier == "A":
            suggested_actions = [
                "Aprovar",
                "Agendar Entrevista",
                "Ver Detalhes"
            ]
        elif tier == "B":
            suggested_actions = [
                "Aprovar",
                "Ver Detalhes",
                "Agendar Entrevista"
            ]
        elif tier == "C":
            suggested_actions = [
                "Ver Detalhes",
                "Comparar Candidatos",
                "Revisar Manualmente"
            ]
        else:
            suggested_actions = [
                "Ver Detalhes",
                "Arquivar Candidato",
                "Enviar Feedback"
            ]
        
        extra_data = {
            "candidate_name": candidate_name,
            "candidate_id": candidate_id,
            "vacancy_id": vacancy_id,
            "vacancy_title": vacancy_title,
            "company_id": company_id,
            "passed": passed,
            "wsi_score": wsi_score,
            "tier": tier,
            "wsi_classification": wsi_classification,
            "suggested_stage": suggested_stage,
            "confidence": confidence,
            "recommendation": recommendation,
            "tier_recommendation": tier_recommendation,
            "hiring_manager_name": hiring_manager_name,
            "department": department
        }
        
        result = await self.send_multi_channel_notification(
            user_id=recruiter_id,
            title=title,
            message=message,
            channels=channel_enums,
            notification_type=NotificationType.SUCCESS if passed else NotificationType.WARNING,
            proactive_type=ProactiveNotificationType.SCREENING_COMPLETED,
            priority="high" if tier in ["A", "B"] else "normal",
            data=extra_data,
            related_job_id=vacancy_id,
            related_candidate_id=candidate_id,
            suggested_actions=suggested_actions,
            db=db
        )
        
        logger.info(
            f"🎯 Screening completed notification sent to recruiter {recruiter_id} "
            f"for candidate {candidate_name} (passed={passed}, score={wsi_score}, tier={tier})"
        )
        
        return result.get("notification_id", "")


async def notify_recruiter_screening_completed(
    db: AsyncSession,
    recruiter_id: str,
    candidate_id: str,
    candidate_name: str,
    vacancy_id: str,
    vacancy_title: str,
    company_id: str,
    passed: bool,
    wsi_score: float,
    suggested_stage: str,
    confidence: float,
    channels: Optional[List[str]] = None,
    hiring_manager_name: Optional[str] = None,
    department: Optional[str] = None,
    wsi_classification: Optional[str] = None
) -> str:
    """
    Standalone helper function for screening completed notifications.
    Delegates to NotificationService instance.
    
    Args:
        db: Database session
        recruiter_id: ID of the recruiter to notify
        candidate_id: ID of the candidate who completed screening
        candidate_name: Name of the candidate
        vacancy_id: ID of the job vacancy
        vacancy_title: Title of the job vacancy
        company_id: Company ID for context
        passed: Whether the candidate passed screening
        wsi_score: WSI score (0-5 scale)
        suggested_stage: Suggested next stage for the candidate
        confidence: Confidence score for the recommendation (0-1)
        channels: Optional list of channels to send to
        hiring_manager_name: Optional name of the hiring manager for the vacancy
        department: Optional department name
        wsi_classification: Optional WSI classification text
    """
    return await notification_service.notify_recruiter_screening_completed(
        db=db,
        recruiter_id=recruiter_id,
        candidate_id=candidate_id,
        candidate_name=candidate_name,
        vacancy_id=vacancy_id,
        vacancy_title=vacancy_title,
        company_id=company_id,
        passed=passed,
        wsi_score=wsi_score,
        suggested_stage=suggested_stage,
        confidence=confidence,
        channels=channels,
        hiring_manager_name=hiring_manager_name,
        department=department,
        wsi_classification=wsi_classification
    )


notification_service = NotificationService()


def get_notification_service() -> "NotificationService":
    return notification_service
