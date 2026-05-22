"""
WebhookEventTypeRepository — ADR-001 canonical.

Audit 2026-05-20 Sprint 5 (catalogos dinamicos).
Multi-tenancy fail-closed via _require_company_id helper.
Soft-delete canonical via deleted_at.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.webhook_event_type import WebhookEventType


class WebhookEventTypeRepository:
    """Repository canonical com multi-tenancy fail-closed."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    @staticmethod
    def _require_company_id(company_id: str | None) -> str:
        if not company_id:
            raise ValueError(
                "company_id is required (tenant isolation canonical)"
            )
        return company_id

    async def list_for_company(
        self,
        company_id: str,
        include_master: bool = True,
        include_deleted: bool = False,
    ) -> list[WebhookEventType]:
        """List active event types: company customs + master (canonical scope).

        Returns master items (visible to all tenants) + customs of this tenant.
        Excludes deleted by default.
        """
        cid = self._require_company_id(company_id)
        # TENANT-EXEMPT: scope_filter ALWAYS includes WebhookEventType.company_id == cid
        # (with optional OR is_master_template for canonical master templates visible
        # cross-tenant). Sensor cannot statically trace the conditional filter.
        stmt = select(WebhookEventType)

        scope_filter = WebhookEventType.company_id == cid
        if include_master:
            scope_filter = or_(
                WebhookEventType.is_master_template.is_(True),
                WebhookEventType.company_id == cid,
            )

        stmt = stmt.where(scope_filter)
        if not include_deleted:
            stmt = stmt.where(WebhookEventType.deleted_at.is_(None))
        stmt = stmt.order_by(WebhookEventType.created_at.desc())

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(
        self, event_type_id: uuid.UUID, company_id: str
    ) -> WebhookEventType | None:
        """Get event type by id — only if master OR belongs to company."""
        cid = self._require_company_id(company_id)
        stmt = select(WebhookEventType).where(
            and_(
                WebhookEventType.id == event_type_id,
                or_(
                    WebhookEventType.is_master_template.is_(True),
                    WebhookEventType.company_id == cid,
                ),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_custom(
        self,
        company_id: str,
        data: dict[str, Any],
        created_by: str | None = None,
        parent_template_id: uuid.UUID | None = None,
    ) -> WebhookEventType:
        """Create new custom event type for the company (canonical scope)."""
        cid = self._require_company_id(company_id)
        record = WebhookEventType(
            id=uuid.uuid4(),
            company_id=cid,
            is_master_template=False,
            parent_template_id=parent_template_id,
            data=data,
            created_by=created_by,
        )
        self.db.add(record)
        await self.db.flush()
        return record

    async def update(
        self,
        event_type_id: uuid.UUID,
        company_id: str,
        data: dict[str, Any],
    ) -> WebhookEventType | None:
        """Update existing custom event type (master immutable canonical).

        Returns None if not found OR if master (immutable) OR cross-tenant.
        """
        cid = self._require_company_id(company_id)
        record = await self.get_by_id(event_type_id, cid)
        if not record or record.is_master_template:
            return None
        if record.company_id != cid:
            return None
        record.data = data
        record.updated_at = datetime.utcnow()
        await self.db.flush()
        return record

    async def soft_delete(
        self, event_type_id: uuid.UUID, company_id: str
    ) -> bool:
        """Soft-delete (canonical LGPD audit). Returns True on success."""
        cid = self._require_company_id(company_id)
        record = await self.get_by_id(event_type_id, cid)
        if not record or record.is_master_template:
            return False
        if record.company_id != cid:
            return False
        record.deleted_at = datetime.utcnow()
        await self.db.flush()
        return True

    async def customize_master(
        self,
        master_id: uuid.UUID,
        company_id: str,
        created_by: str | None = None,
        overrides: dict[str, Any] | None = None,
    ) -> WebhookEventType | None:
        """Customize a master event type — cópia total canonical A1.

        Snapshot canonical B1 (não sincroniza com master após criação).
        """
        cid = self._require_company_id(company_id)
        # TENANT-EXEMPT: master templates are canonical cross-tenant resources
        # (is_master_template=True). Customization clone written under `cid` below
        # via create_custom() applies tenant isolation on the new record.
        master_stmt = select(WebhookEventType).where(
            and_(
                WebhookEventType.id == master_id,
                WebhookEventType.is_master_template.is_(True),
                WebhookEventType.deleted_at.is_(None),
            )
        )
        master_result = await self.db.execute(master_stmt)
        master = master_result.scalar_one_or_none()
        if not master:
            return None

        new_data = dict(master.data) if master.data else {}
        if overrides:
            new_data.update(overrides)

        return await self.create_custom(
            company_id=cid,
            data=new_data,
            created_by=created_by,
            parent_template_id=master.id,
        )

    async def counts(self, company_id: str) -> dict[str, int]:
        """Return (master_count, custom_count, total) for the company canonical scope."""
        cid = self._require_company_id(company_id)
        all_items = await self.list_for_company(cid, include_master=True)
        master_count = sum(1 for x in all_items if x.is_master_template)
        custom_count = sum(1 for x in all_items if not x.is_master_template)
        return {
            "master_count": master_count,
            "custom_count": custom_count,
            "total": master_count + custom_count,
        }
