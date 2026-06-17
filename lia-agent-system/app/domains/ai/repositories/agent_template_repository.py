"""
AgentTemplate Repository — data access layer for AI agent templates.
Extracted from app/api/v1/agent_templates.py as part of Phase 2 refactor.
"""
import logging
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class AgentTemplateRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_model(self):
        """Lazy-import to avoid circular deps."""
        from lia_models.agent_template import AgentTemplate
        return AgentTemplate

    async def list_templates(
        self,
        *,
        company_id: str | None = None,
        category: str | None = None,
        agent_type: str | None = None,
        is_active: bool | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list, int]:
        AgentTemplate = await self._get_model()
        # TENANT-EXEMPT: dynamic builder — filter via or_(company_id, is_global) aplicado abaixo
        # quando company_id is not None. Sensor AST não traça filter em statement separado.
        q = select(AgentTemplate)
        if company_id is not None:
            q = q.where(
                or_(AgentTemplate.company_id == company_id, AgentTemplate.is_global.is_(True))
            )
        if category:
            q = q.where(AgentTemplate.category == category)
        if agent_type:
            q = q.where(AgentTemplate.agent_type == agent_type)
        if is_active is not None:
            q = q.where(AgentTemplate.is_active == is_active)
        if search:
            p = f"%{search}%"
            q = q.where(
                or_(AgentTemplate.name.ilike(p), AgentTemplate.description.ilike(p))
            )
        q = q.order_by(AgentTemplate.name).limit(limit).offset(offset)
        result = await self.db.execute(q)
        items = list(result.scalars().all())

        cq = select(func.count(AgentTemplate.id))
        # reapply filters for count
        if company_id is not None:
            cq = cq.where(
                or_(AgentTemplate.company_id == company_id, AgentTemplate.is_global.is_(True))
            )
        if category:
            cq = cq.where(AgentTemplate.category == category)
        if agent_type:
            cq = cq.where(AgentTemplate.agent_type == agent_type)
        if is_active is not None:
            cq = cq.where(AgentTemplate.is_active == is_active)
        if search:
            cq = cq.where(
                or_(AgentTemplate.name.ilike(p), AgentTemplate.description.ilike(p))
            )
        total = (await self.db.execute(cq)).scalar() or 0
        return items, total

    async def get_by_id(
        self,
        template_id: UUID,
        company_id: str | None = None,
    ) -> object | None:
        """Lookup AgentTemplate por id.

        Sprint B.1 tail (2026-05-22): company_id agora suportado pra restringir
        ao tenant + global marketplace (company_id IS NULL).

        - company_id=None (legacy/admin): retorna qualquer template (NÃO usar pra clientes).
        - company_id=<uuid>: retorna apenas templates do tenant OU public WeDO (company_id IS NULL = marketplace global).
        """
        AgentTemplate = await self._get_model()
        from sqlalchemy import or_
        if company_id is not None:
            # TENANT-EXEMPT: filter explícito via OR — public templates (company_id IS NULL = WeDO marketplace global) + tenant customs; sensor AST não infere or_(...)
            result = await self.db.execute(
                select(AgentTemplate).where(
                    AgentTemplate.id == template_id,
                    or_(
                        AgentTemplate.company_id == company_id,
                        AgentTemplate.company_id.is_(None),
                    ),
                )
            )
        else:
            # TENANT-EXEMPT: admin/legacy lookup sem tenant gate — caller verifica acesso (audit 2026-05-22)
            result = await self.db.execute(
                select(AgentTemplate).where(AgentTemplate.id == template_id)
            )
        return result.scalar_one_or_none()

    async def create(self, data: dict) -> object:
        AgentTemplate = await self._get_model()
        t = AgentTemplate(**data)
        self.db.add(t)
        await self.db.flush()
        await self.db.refresh(t)
        return t

    async def update(self, template, data: dict) -> object:
        for key, value in data.items():
            setattr(template, key, value)
        await self.db.flush()
        await self.db.refresh(template)
        return template

    async def soft_delete(self, template) -> None:
        template.is_active = False
        await self.db.flush()

    async def hard_delete(self, template) -> None:
        await self.db.delete(template)
        await self.db.flush()
