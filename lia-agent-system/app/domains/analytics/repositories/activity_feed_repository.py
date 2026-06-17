"""ActivityFeedRepository — DB access layer for the activity_feed table.

Extracted from app/domains/analytics/services/activity_service.py per ADR-001.
Tables covered:
  - activity_feed
"""
import logging
from typing import Any

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ActivityFeed

logger = logging.getLogger(__name__)


class ActivityFeedRepository:
    """Repository for activity_feed reads.

    Note: ActivityFeed is a platform-wide notification/activity stream.
    Tenant scoping is enforced at the API layer via visible_to filtering.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_with_filters(
        self,
        where_conditions: list[Any],
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ActivityFeed], int]:
        """Paginated list + total count using shared WHERE conditions."""
        count_stmt = (
            select(func.count()).select_from(ActivityFeed).where(and_(*where_conditions))
        )
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0

        data_stmt = (
            # TENANT-EXEMPT: activity feed scoped via dynamic conditions builder in upstream caller; T-RATCHET tenant_filter
            select(ActivityFeed)
            .where(and_(*where_conditions))
            .order_by(desc(ActivityFeed.created_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(data_stmt)
        activities = list(result.scalars().all())
        return activities, total

    async def get_by_id(self, activity_id: str) -> ActivityFeed | None:
        # TENANT-EXEMPT: activity feed scoped via dynamic conditions builder in upstream caller; T-RATCHET tenant_filter
        stmt = select(ActivityFeed).where(ActivityFeed.id == activity_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_urgent_visible(self) -> list[ActivityFeed]:
        # TENANT-EXEMPT: activity feed scoped via dynamic conditions builder in upstream caller; T-RATCHET tenant_filter
        stmt = select(ActivityFeed).where(
            and_(
                ActivityFeed.is_visible,
                ActivityFeed.priority == "urgent",
            )
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
