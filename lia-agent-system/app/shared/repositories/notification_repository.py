"""
Notification Repository - Database access for Notification model.
"""
import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy import update as sa_update

from app.services.notification_service import Notification
from app.shared.repositories.sqlalchemy_base import SQLAlchemyRepository

logger = logging.getLogger(__name__)


class NotificationRepository(SQLAlchemyRepository[Notification]):
    """Repository for Notification model with domain-specific queries."""
    
    model_class = Notification
    
    async def get_for_user(self, db, user_id: str, limit: int = 50,
                           include_read: bool = False) -> list[Notification]:
        """Get notifications for a specific user."""
        query = select(self.model_class).where(
            self.model_class.user_id == user_id
        )
        if not include_read:
            query = query.where(not self.model_class.is_read)
        query = query.order_by(self.model_class.created_at.desc())
        query = query.limit(limit)
        if hasattr(db, 'execute'):
            result = await db.execute(query)
            return list(result.scalars().all())
        return db.query(self.model_class).filter(
            self.model_class.user_id == user_id
        ).limit(limit).all()
    
    async def mark_as_read(self, db, notification_id: UUID) -> bool:
        """Mark a single notification as read."""
        query = select(self.model_class).where(
            self.model_class.id == str(notification_id)
        )
        if hasattr(db, 'execute'):
            result = await db.execute(query)
            notification = result.scalar_one_or_none()
        else:
            notification = db.query(self.model_class).filter(
                self.model_class.id == str(notification_id)
            ).first()
        if not notification:
            return False
        notification.is_read = True
        notification.read_at = datetime.utcnow()
        if hasattr(db, 'flush'):
            await db.flush()
        return True
    
    async def mark_all_read(self, db, user_id: str) -> int:
        """Mark all notifications as read for a user. Returns count updated."""
        stmt = (
            sa_update(self.model_class)
            .where(
                self.model_class.user_id == user_id,
                not self.model_class.is_read,
            )
            .values(is_read=True, read_at=datetime.utcnow())
        )
        if hasattr(db, 'execute'):
            result = await db.execute(stmt)
            await db.flush()
            return result.rowcount
        result = db.execute(stmt)
        return result.rowcount
    
    async def get_unread_count(self, db, user_id: str) -> int:
        """Get count of unread notifications for a user."""
        query = select(func.count()).select_from(self.model_class).where(
            self.model_class.user_id == user_id,
            not self.model_class.is_read,
        )
        if hasattr(db, 'execute'):
            result = await db.execute(query)
            return result.scalar() or 0
        return db.query(func.count(self.model_class.id)).filter(
            self.model_class.user_id == user_id,
            not self.model_class.is_read,
        ).scalar() or 0
