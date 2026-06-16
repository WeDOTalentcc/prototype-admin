"""AgentTemplateCatalog repository — ADR-001 canonical.

Zero SQL inline (sensor `check_no_sql_inline_in_services.py`).
Reads expostas pra catálogo global (company_id NULL). Mutations gated por
UserRole.wedotalent_admin no endpoint.
"""
from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class AgentTemplateCatalogRepository:
    """Repository pra agent_template_catalog.

    Convenções:
    - reads filtram `is_active=True` por default (override via parâmetro)
    - mutations devem ser chamadas apenas após gate de role no endpoint
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_model(self):
        """Lazy import — evita ciclo durante boot."""
        from lia_models.agent_template_catalog import AgentTemplateCatalog
        return AgentTemplateCatalog

    async def _get_category_model(self):
        from lia_models.agent_template_catalog import AgentCategory
        return AgentCategory

    async def _get_sector_model(self):
        from lia_models.agent_template_catalog import AgentSector
        return AgentSector

    async def list(
        self,
        *,
        category: str | None = None,
        sector: str | None = None,
        active_only: bool = True,
    ) -> list:
        """List templates do catálogo global.

        TENANT-EXEMPT: catálogo global hoje (V1) — company_id NULL.
        Pagamento gate seria no endpoint, não no repo (Sprint 1 QuotaMeter).
        """
        AgentTemplateCatalog = await self._get_model()
        q = select(AgentTemplateCatalog)
        if active_only:
            q = q.where(AgentTemplateCatalog.is_active.is_(True))
        if category and category != "all":
            q = q.where(AgentTemplateCatalog.category_id == category)
        if sector:
            q = q.where(AgentTemplateCatalog.sector_id == sector)
        q = q.order_by(
            AgentTemplateCatalog.sort_order,
            AgentTemplateCatalog.name,
        )
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def get_by_id(self, template_id: UUID) -> object | None:
        """Lookup por UUID — caller deve aplicar gate de role se for mutation."""
        AgentTemplateCatalog = await self._get_model()
        # TENANT-EXEMPT: catálogo global V1 (company_id NULL); gate de write
        # no endpoint via require_wedotalent_admin
        result = await self.db.execute(
            select(AgentTemplateCatalog).where(AgentTemplateCatalog.id == template_id)
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> object | None:
        AgentTemplateCatalog = await self._get_model()
        # TENANT-EXEMPT: slug é único globalmente no catálogo seed V1
        result = await self.db.execute(
            select(AgentTemplateCatalog).where(AgentTemplateCatalog.slug == slug)
        )
        return result.scalar_one_or_none()

    async def create(self, data: dict, *, company_id: str | None = None) -> object:
        """Insert template novo. company_id forwarded (NULL = global).

        Caller (endpoint) já validou role wedotalent_admin.
        """
        AgentTemplateCatalog = await self._get_model()
        payload = dict(data)
        payload["company_id"] = company_id
        obj = AgentTemplateCatalog(**payload)
        self.db.add(obj)
        await self.db.flush()
        await self.db.refresh(obj)
        return obj

    async def update(self, template, data: dict) -> object:
        for key, value in data.items():
            setattr(template, key, value)
        await self.db.flush()
        await self.db.refresh(template)
        return template

    async def delete(self, template) -> None:
        """Soft delete via is_active=False (preserva auditabilidade)."""
        template.is_active = False
        await self.db.flush()

    async def list_categories(self, active_only: bool = True) -> list:
        AgentCategory = await self._get_category_model()
        q = select(AgentCategory)
        if active_only:
            q = q.where(AgentCategory.is_active.is_(True))
        q = q.order_by(AgentCategory.sort_order, AgentCategory.label_pt)
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def list_sectors(self, active_only: bool = True) -> list:
        AgentSector = await self._get_sector_model()
        q = select(AgentSector)
        if active_only:
            q = q.where(AgentSector.is_active.is_(True))
        q = q.order_by(AgentSector.sort_order, AgentSector.label_pt)
        result = await self.db.execute(q)
        return list(result.scalars().all())
