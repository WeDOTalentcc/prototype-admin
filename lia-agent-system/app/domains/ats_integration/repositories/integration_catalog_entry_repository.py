"""
IntegrationCatalogEntryRepository — ADR-001 canonical.

Audit 2026-05-20 Sprint 4 (catalogos dinamicos).
Multi-tenancy fail-closed via _require_company_id helper.
Soft-delete canonical via deleted_at.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.integration_catalog_entry import IntegrationCatalogEntry


class IntegrationCatalogEntryRepository:
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
        category: str | None = None,
    ) -> list[IntegrationCatalogEntry]:
        """List active entries: company customs + master (canonical scope).

        Returns master items (visible to all tenants) + customs of this tenant.
        Excludes deleted by default.
        Optional category filter (JSONB ->>).
        """
        cid = self._require_company_id(company_id)
        # TENANT-EXEMPT: marketplace pattern — scope_filter abaixo aplica or_(is_master, company_id);
        # _require_company_id gate fail-closed garante company_id válido. Audit 2026-05-22.
        stmt = select(IntegrationCatalogEntry)

        scope_filter = IntegrationCatalogEntry.company_id == cid
        if include_master:
            scope_filter = or_(
                IntegrationCatalogEntry.is_master_template.is_(True),
                IntegrationCatalogEntry.company_id == cid,
            )

        stmt = stmt.where(scope_filter)
        if not include_deleted:
            stmt = stmt.where(IntegrationCatalogEntry.deleted_at.is_(None))
        if category:
            # JSONB ->> 'category' = :category
            stmt = stmt.where(
                IntegrationCatalogEntry.data["category"].astext == category
            )
        stmt = stmt.order_by(IntegrationCatalogEntry.created_at.desc())

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(
        self, entry_id: uuid.UUID, company_id: str
    ) -> IntegrationCatalogEntry | None:
        """Get entry by id — only if master OR belongs to company (canonical scope)."""
        cid = self._require_company_id(company_id)
        stmt = select(IntegrationCatalogEntry).where(
            and_(
                IntegrationCatalogEntry.id == entry_id,
                or_(
                    IntegrationCatalogEntry.is_master_template.is_(True),
                    IntegrationCatalogEntry.company_id == cid,
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
    ) -> IntegrationCatalogEntry:
        """Create new custom entry for the company (canonical scope)."""
        cid = self._require_company_id(company_id)
        entry = IntegrationCatalogEntry(
            id=uuid.uuid4(),
            company_id=cid,
            is_master_template=False,
            parent_template_id=parent_template_id,
            data=data,
            created_by=created_by,
        )
        self.db.add(entry)
        await self.db.flush()
        return entry

    async def update(
        self,
        entry_id: uuid.UUID,
        company_id: str,
        data: dict[str, Any],
    ) -> IntegrationCatalogEntry | None:
        """Update existing custom entry (master immutable canonical).

        Returns None if not found OR if master (immutable) OR cross-tenant.
        """
        cid = self._require_company_id(company_id)
        entry = await self.get_by_id(entry_id, cid)
        if not entry or entry.is_master_template:
            return None
        if entry.company_id != cid:
            return None
        entry.data = data
        entry.updated_at = datetime.utcnow()
        await self.db.flush()
        return entry

    async def soft_delete(
        self, entry_id: uuid.UUID, company_id: str
    ) -> bool:
        """Soft-delete (canonical LGPD audit). Returns True on success."""
        cid = self._require_company_id(company_id)
        entry = await self.get_by_id(entry_id, cid)
        if not entry or entry.is_master_template:
            return False
        if entry.company_id != cid:
            return False
        entry.deleted_at = datetime.utcnow()
        await self.db.flush()
        return True

    async def customize_master(
        self,
        master_id: uuid.UUID,
        company_id: str,
        created_by: str | None = None,
        overrides: dict[str, Any] | None = None,
    ) -> IntegrationCatalogEntry | None:
        """Customize a master entry — cópia total canonical A1.

        Snapshot canonical B1 (não sincroniza com master após criação).
        """
        cid = self._require_company_id(company_id)
        # TENANT-EXEMPT: master template lookup — is_master_template=True garante so masters globais (marketplace);
        # cid validado acima por _require_company_id; usado pra criar copia tenant-scoped logo abaixo. Audit 2026-05-22.
        master_stmt = select(IntegrationCatalogEntry).where(
            and_(
                IntegrationCatalogEntry.id == master_id,
                IntegrationCatalogEntry.is_master_template.is_(True),
                IntegrationCatalogEntry.deleted_at.is_(None),
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
