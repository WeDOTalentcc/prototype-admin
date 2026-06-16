"""CompensationComponent Repository — verbas variaveis item-centric.

Espelha CompanyBenefitRepository. Filtro de elegibilidade (list_matching) reusa
o util compartilhado app.shared.eligibility_matching (DRY) + vacancy_vocab match
keys (anti-drift EN<->PT). ADR-001: filtro no repo, nao na API.
"""
import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.compensation_component import (
    DEFAULT_BR_COMPENSATION_COMPONENTS,
    CompensationComponent,
)
from app.domains.job_creation.helpers.vacancy_vocab import (
    to_match_contract_key,
    to_match_seniority_key,
)
from app.shared.eligibility_matching import (
    matches_department,
    matches_dimension_list,
    matches_subsidiaries,
)

logger = logging.getLogger(__name__)


class CompensationComponentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_for_company(
        self,
        company_id: str,
        *,
        active_only: bool = True,
        kind: str | None = None,
        search: str | None = None,
    ) -> list[CompensationComponent]:
        query = select(CompensationComponent).where(
            CompensationComponent.company_id == company_id
        )
        if active_only:
            query = query.where(CompensationComponent.is_active.is_(True))
        if kind:
            query = query.where(CompensationComponent.kind == kind)
        if search:
            term = f"%{search.lower()}%"
            query = query.where(
                or_(
                    func.lower(CompensationComponent.name).like(term),
                    func.lower(CompensationComponent.description).like(term),
                )
            )
        query = query.order_by(CompensationComponent.order, CompensationComponent.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_id(
        self, component_id: UUID, company_id: str | None = None
    ) -> CompensationComponent | None:
        # TENANT-EXEMPT: company_id appended conditionally below (defense-in-depth).
        query = select(CompensationComponent).where(CompensationComponent.id == component_id)
        if company_id:
            query = query.where(CompensationComponent.company_id == company_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_name_ci(self, company_id: str, name: str) -> CompensationComponent | None:
        """Dedup case-insensitive por nome (promote-back vaga->catalogo)."""
        if not name:
            return None
        result = await self.db.execute(
            select(CompensationComponent).where(
                CompensationComponent.company_id == company_id,
                func.lower(CompensationComponent.name) == name.strip().lower(),
            )
        )
        return result.scalars().first()

    async def create(self, company_id: str, data: dict) -> CompensationComponent:
        component = CompensationComponent(company_id=company_id, **data)
        self.db.add(component)
        await self.db.flush()
        await self.db.refresh(component)
        return component

    async def update(self, component: CompensationComponent, data: dict) -> CompensationComponent:
        data["updated_at"] = datetime.utcnow()
        for key, value in data.items():
            setattr(component, key, value)
        await self.db.flush()
        await self.db.refresh(component)
        return component

    async def soft_delete(self, component: CompensationComponent) -> None:
        component.is_active = False
        component.updated_at = datetime.utcnow()

    async def hard_delete(self, component: CompensationComponent) -> None:
        await self.db.delete(component)

    async def count_for_company(self, company_id: str) -> int:
        result = await self.db.execute(
            select(func.count(CompensationComponent.id)).where(
                CompensationComponent.company_id == company_id
            )
        )
        return result.scalar() or 0

    async def seed_defaults(self, company_id: str) -> int:
        created = 0
        for cdata in DEFAULT_BR_COMPENSATION_COMPONENTS:
            if not await self.get_by_name_ci(company_id, cdata["name"]):
                self.db.add(CompensationComponent(company_id=company_id, **cdata))
                created += 1
        return created

    async def list_matching(
        self,
        company_id: str,
        *,
        seniority_level: str | None = None,
        department: str | None = None,
        contract_type: str | None = None,
        subsidiary: str | None = None,
        subsidiary_cnpj: str | None = None,
        active_only: bool = True,
    ) -> list[tuple[CompensationComponent, bool]]:
        """Lista componentes ativos com flag matches_vaga por item (AND das
        dimensoes informadas). Nao remove nao-compativeis (a vaga exibe o catalogo
        inteiro agrupado por tipo; compativeis vem pre-marcados)."""
        components = await self.list_for_company(company_id, active_only=active_only)
        sen_key = to_match_seniority_key(seniority_level) if seniority_level else ""
        con_key = to_match_contract_key(contract_type) if contract_type else ""
        out: list[tuple[CompensationComponent, bool]] = []
        for c in components:
            ok = (
                matches_dimension_list(c.seniority_levels, sen_key, to_match_seniority_key)
                and matches_dimension_list(c.contract_types, con_key, to_match_contract_key)
                and matches_department(c.departments, department)
                and matches_subsidiaries(c.subsidiaries, subsidiary, subsidiary_cnpj)
            )
            out.append((c, ok))
        return out
