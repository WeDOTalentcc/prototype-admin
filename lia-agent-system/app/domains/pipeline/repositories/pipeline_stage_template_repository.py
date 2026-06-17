"""
PipelineStageTemplateRepository — ADR-001 canonical.

Audit 2026-05-20 Sprint 2 (catalogos dinamicos).
Multi-tenancy fail-closed via _require_company_id helper.
Soft-delete canonical via deleted_at.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.pipeline_stage_template import PipelineStageTemplate


class PipelineStageTemplateRepository:
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
    ) -> list[PipelineStageTemplate]:
        """List active templates: company customs + master (canonical scope).

        Returns master items (visible to all tenants) + customs of this tenant.
        Excludes deleted by default. Ordered by data->>'order' (canonical) then
        created_at desc.
        """
        cid = self._require_company_id(company_id)
        stmt = select(PipelineStageTemplate)

        scope_filter = PipelineStageTemplate.company_id == cid
        if include_master:
            scope_filter = or_(
                PipelineStageTemplate.is_master_template.is_(True),
                PipelineStageTemplate.company_id == cid,
            )

        stmt = stmt.where(scope_filter)
        if not include_deleted:
            stmt = stmt.where(PipelineStageTemplate.deleted_at.is_(None))
        # Order primario por data->>order (canonical do funil), secundario por created_at desc
        stmt = stmt.order_by(PipelineStageTemplate.created_at.desc())

        result = await self.db.execute(stmt)
        items = list(result.scalars().all())
        # Sort em Python por data["order"] depois mantém created_at desc como tie-breaker
        items.sort(key=lambda x: (x.data or {}).get("order", 9999))
        return items

    async def get_by_id(
        self, template_id: uuid.UUID, company_id: str
    ) -> PipelineStageTemplate | None:
        """Get template by id — only if master OR belongs to company (canonical scope)."""
        cid = self._require_company_id(company_id)
        stmt = select(PipelineStageTemplate).where(
            and_(
                PipelineStageTemplate.id == template_id,
                or_(
                    PipelineStageTemplate.is_master_template.is_(True),
                    PipelineStageTemplate.company_id == cid,
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
    ) -> PipelineStageTemplate:
        """Create new custom template for the company (canonical scope)."""
        cid = self._require_company_id(company_id)
        template = PipelineStageTemplate(
            id=uuid.uuid4(),
            company_id=cid,
            is_master_template=False,
            parent_template_id=parent_template_id,
            data=data,
            created_by=created_by,
        )
        self.db.add(template)
        await self.db.flush()
        return template

    async def update(
        self,
        template_id: uuid.UUID,
        company_id: str,
        data: dict[str, Any],
    ) -> PipelineStageTemplate | None:
        """Update existing custom template (master immutable canonical).

        Returns None if not found OR if master (immutable) OR cross-tenant.
        """
        cid = self._require_company_id(company_id)
        template = await self.get_by_id(template_id, cid)
        if not template or template.is_master_template:
            return None
        if template.company_id != cid:
            return None
        template.data = data
        template.updated_at = datetime.utcnow()
        await self.db.flush()
        return template

    async def soft_delete(
        self, template_id: uuid.UUID, company_id: str
    ) -> bool:
        """Soft-delete (canonical LGPD audit). Returns True on success."""
        cid = self._require_company_id(company_id)
        template = await self.get_by_id(template_id, cid)
        if not template or template.is_master_template:
            return False
        if template.company_id != cid:
            return False
        template.deleted_at = datetime.utcnow()
        await self.db.flush()
        return True

    async def customize_master(
        self,
        master_id: uuid.UUID,
        company_id: str,
        created_by: str | None = None,
        overrides: dict[str, Any] | None = None,
    ) -> PipelineStageTemplate | None:
        """Customize a master template — copia total canonical A1.

        Snapshot canonical B1 (nao sincroniza com master apos criacao).
        """
        cid = self._require_company_id(company_id)
        master_stmt = select(PipelineStageTemplate).where(
            and_(
                PipelineStageTemplate.id == master_id,
                PipelineStageTemplate.is_master_template.is_(True),
                PipelineStageTemplate.deleted_at.is_(None),
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
