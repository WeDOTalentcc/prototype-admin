"""
Repository for Compliance Health Check domain.

Encapsulates all database access for:
- ComplianceHealthCheckItem
- ComplianceHealthCheckHistory
- ComplianceControlLibrary (read-only, for sync)
"""
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.health_check import (
    DEFAULT_HEALTH_CHECK_ITEMS,
    ComplianceHealthCheckHistory,
    ComplianceHealthCheckItem,
)
from app.models.observability import ComplianceControlLibrary


class HealthCheckRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------ #
    # Read methods                                                         #
    # ------------------------------------------------------------------ #

    async def get_all_items(self):
        """Return all health check items (no filters)."""
        query = select(ComplianceHealthCheckItem)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def list_items(
        self,
        framework=None,
        status_filter=None,
        category=None,
        priority=None,
        overdue_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ):
        """List items with optional filters and pagination. Returns (items, total)."""
        conditions = []
        if framework:
            conditions.append(ComplianceHealthCheckItem.framework == framework)
        if status_filter:
            conditions.append(ComplianceHealthCheckItem.status == status_filter)
        if category:
            conditions.append(ComplianceHealthCheckItem.category.ilike(f"%{category}%"))
        if priority:
            conditions.append(ComplianceHealthCheckItem.priority == priority)
        if overdue_only:
            conditions.append(ComplianceHealthCheckItem.next_review_date < datetime.utcnow())

        query = select(ComplianceHealthCheckItem).order_by(
            ComplianceHealthCheckItem.framework,
            ComplianceHealthCheckItem.category,
            ComplianceHealthCheckItem.req_id,
        )
        if conditions:
            query = query.where(and_(*conditions))
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        items = result.scalars().all()

        count_query = select(func.count(ComplianceHealthCheckItem.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        return items, total

    async def list_items_for_export(self, framework=None, status_filter=None):
        """Return items ordered for export (no pagination)."""
        conditions = []
        if framework:
            conditions.append(ComplianceHealthCheckItem.framework == framework)
        if status_filter:
            conditions.append(ComplianceHealthCheckItem.status == status_filter)

        query = select(ComplianceHealthCheckItem).order_by(
            ComplianceHealthCheckItem.framework,
            ComplianceHealthCheckItem.category,
            ComplianceHealthCheckItem.req_id,
        )
        if conditions:
            query = query.where(and_(*conditions))

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_item_by_req_id(self, req_id: str):
        """Return a single item by its req_id, or None."""
        query = select(ComplianceHealthCheckItem).where(
            ComplianceHealthCheckItem.req_id == req_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def item_exists_by_req_id(self, req_id: str) -> bool:
        """Return True if an item with the given req_id already exists."""
        result = await self.db.execute(
            select(ComplianceHealthCheckItem).where(
                ComplianceHealthCheckItem.req_id == req_id
            )
        )
        return result.scalar_one_or_none() is not None

    async def get_item_history(self, item_id: UUID):
        """Return all history records for an item, newest first."""
        query = (
            select(ComplianceHealthCheckHistory)
            .where(ComplianceHealthCheckHistory.item_id == item_id)
            .order_by(desc(ComplianceHealthCheckHistory.created_at))
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    # ------------------------------------------------------------------ #
    # Write methods                                                        #
    # ------------------------------------------------------------------ #

    async def create_item(
        self,
        framework: str,
        category: str,
        req_id: str,
        requirement: str,
        evidence=None,
        gap_observation=None,
        status: str = "not_checked",
        priority: str = "medium",
        review_frequency: str = "monthly",
        evidence_details=None,
    ) -> ComplianceHealthCheckItem:
        """Create and persist a new health check item."""
        item = ComplianceHealthCheckItem(
            framework=framework,
            category=category,
            req_id=req_id,
            requirement=requirement,
            evidence=evidence,
            gap_observation=gap_observation,
            status=status,
            priority=priority,
            review_frequency=review_frequency,
            evidence_details=evidence_details,
        )
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def add_item_no_commit(self, item: ComplianceHealthCheckItem):
        """Stage an item for insertion without committing (batch use)."""
        self.db.add(item)

    async def mark_item_checked(
        self,
        item: ComplianceHealthCheckItem,
        checked_by_id=None,
        checked_by_name=None,
        check_comments=None,
        next_review_date=None,
    ) -> ComplianceHealthCheckItem:
        """Update last_checked_at and optional fields, then commit."""
        item.last_checked_at = datetime.utcnow()

        if checked_by_id:
            try:
                item.checked_by_id = UUID(checked_by_id)
            except ValueError:
                pass

        if checked_by_name:
            item.checked_by_name = checked_by_name

        if check_comments:
            item.check_comments = check_comments

        if next_review_date:
            item.next_review_date = next_review_date
        elif not item.next_review_date:
            freq_days = {
                "weekly": 7,
                "monthly": 30,
                "quarterly": 90,
                "annual": 365,
            }
            days = freq_days.get(item.review_frequency, 30)
            item.next_review_date = datetime.utcnow() + timedelta(days=days)

        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def update_item_status(
        self,
        item: ComplianceHealthCheckItem,
        new_status: str,
        gap_observation=None,
        changed_by_id=None,
        changed_by_name=None,
        comments=None,
    ) -> ComplianceHealthCheckItem:
        """Update status with optional history tracking, then commit."""
        old_status = item.status

        if old_status != new_status:
            history = ComplianceHealthCheckHistory(
                item_id=item.id,
                old_status=old_status,
                new_status=new_status,
                changed_by_id=UUID(changed_by_id) if changed_by_id else None,
                changed_by_name=changed_by_name,
                comments=comments,
            )
            self.db.add(history)

        item.status = new_status

        if gap_observation is not None:
            item.gap_observation = gap_observation

        await self.db.commit()
        await self.db.refresh(item)
        return item

    # ------------------------------------------------------------------ #
    # Seed / sync                                                          #
    # ------------------------------------------------------------------ #

    async def seed_default_items(self):
        """Seed DEFAULT_HEALTH_CHECK_ITEMS, skipping existing req_ids. Returns (created, skipped)."""
        created_count = 0
        skipped_count = 0

        for item_data in DEFAULT_HEALTH_CHECK_ITEMS:
            existing = await self.get_item_by_req_id(item_data["req_id"])
            if existing:
                skipped_count += 1
                continue
            item = ComplianceHealthCheckItem(**item_data)
            self.db.add(item)
            created_count += 1

        await self.db.commit()
        return created_count, skipped_count

    async def sync_from_control_library(self, framework_mapping: dict):
        """Import controls from ComplianceControlLibrary, skipping existing. Returns (created, skipped)."""
        created_count = 0
        skipped_count = 0

        library_query = select(ComplianceControlLibrary)
        library_result = await self.db.execute(library_query)
        library_controls = library_result.scalars().all()

        for control in library_controls:
            mapped_framework = framework_mapping.get(control.framework, control.framework)

            existing = await self.get_item_by_req_id(control.control_id)
            if existing:
                skipped_count += 1
                continue

            evidence_list = control.evidence_requirements or []
            evidence_str = ", ".join(evidence_list) if evidence_list else None
            priority = "critical" if control.is_mandatory else "medium"

            item = ComplianceHealthCheckItem(
                framework=mapped_framework,
                category=control.control_category or "General",
                req_id=control.control_id,
                requirement=control.control_name,
                evidence=evidence_str,
                evidence_details=control.implementation_guidance,
                priority=priority,
                review_frequency="monthly",
                status="not_checked",
            )
            self.db.add(item)
            created_count += 1

        await self.db.commit()
        return created_count, skipped_count

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    async def commit(self):
        await self.db.commit()

    async def rollback(self):
        await self.db.rollback()
