"""
CompanyBenefit Repository — data access layer for company-specific benefits.
Extracted from app/api/v1/company_benefits.py as part of Phase 2 refactor.
"""
import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company_benefit import DEFAULT_BRAZILIAN_BENEFITS, CompanyBenefit
from app.domains.job_creation.helpers.vacancy_vocab import (
    _norm,
    to_match_contract_key,
    to_match_seniority_key,
)
from app.shared.eligibility_matching import matches_department, matches_dimension_list, matches_subsidiaries

logger = logging.getLogger(__name__)


class CompanyBenefitRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_for_company(
        self,
        company_id: str,
        *,
        active_only: bool = True,
        category: str | None = None,
        search: str | None = None,
    ) -> list[CompanyBenefit]:
        query = select(CompanyBenefit).where(CompanyBenefit.company_id == company_id)
        if active_only:
            query = query.where(CompanyBenefit.is_active.is_(True))
        if category:
            query = query.where(CompanyBenefit.category == category)
        if search:
            term = f"%{search.lower()}%"
            query = query.where(
                or_(
                    func.lower(CompanyBenefit.name).like(term),
                    func.lower(CompanyBenefit.description).like(term),
                )
            )
        query = query.order_by(CompanyBenefit.order, CompanyBenefit.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_id(
        self,
        benefit_id: UUID,
        company_id: str | None = None,
    ) -> CompanyBenefit | None:
        """Get company-benefit by id. Multi-tenancy defense-in-depth via
        company_id filter quando passado (REGRA ZERO + harness B.1)."""
        # TENANT-EXEMPT: dynamic builder — CompanyBenefit.company_id == company_id
        # é appended conditionally below quando company_id passado.
        query = select(CompanyBenefit).where(CompanyBenefit.id == benefit_id)
        if company_id:
            query = query.where(CompanyBenefit.company_id == company_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_name(self, company_id: str, name: str) -> CompanyBenefit | None:
        result = await self.db.execute(
            select(CompanyBenefit).where(
                CompanyBenefit.company_id == company_id,
                CompanyBenefit.name == name,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_name_ci(self, company_id: str, name: str) -> CompanyBenefit | None:
        """Match case-insensitive por nome (dedup do promote-back vaga->catalogo)."""
        if not name:
            return None
        result = await self.db.execute(
            select(CompanyBenefit).where(
                CompanyBenefit.company_id == company_id,
                func.lower(CompanyBenefit.name) == name.strip().lower(),
            )
        )
        return result.scalars().first()

    @staticmethod
    def _matches_dimension_list(
        benefit_values: list | None, vaga_key: str, key_fn
    ) -> bool:
        """Delega ao util compartilhado (app.shared.eligibility_matching)."""
        return matches_dimension_list(benefit_values, vaga_key, key_fn)

    @staticmethod
    def _matches_department(departments: dict | None, vaga_department: str | None) -> bool:
        """Delega ao util compartilhado (app.shared.eligibility_matching)."""
        return matches_department(departments, vaga_department)

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
    ) -> list[tuple[CompanyBenefit, bool]]:
        """Lista beneficios ativos da empresa com flag `matches_vaga` por item.

        Nao remove os nao-compativeis (a vaga exibe o catalogo inteiro agrupado
        por categoria; compativeis vem pre-marcados). matches_vaga = AND de todas
        as dimensoes informadas (5a dimensao: subsidiary adicionada 2026-06-18).
        ADR-001: filtro vive no repo, nao na API.
        """
        benefits = await self.list_for_company(company_id, active_only=active_only)
        sen_key = to_match_seniority_key(seniority_level) if seniority_level else ""
        con_key = to_match_contract_key(contract_type) if contract_type else ""
        out: list[tuple[CompanyBenefit, bool]] = []
        for b in benefits:
            matches = (
                self._matches_dimension_list(b.seniority_levels, sen_key, to_match_seniority_key)
                and self._matches_dimension_list(b.contract_types, con_key, to_match_contract_key)
                and self._matches_department(b.departments, department)
                and matches_subsidiaries(
                    getattr(b, "subsidiaries", None) or [],
                    subsidiary,
                    subsidiary_cnpj,
                )
            )
            out.append((b, matches))
        return out

    async def create(self, company_id: str, data: dict) -> CompanyBenefit:
        benefit = CompanyBenefit(company_id=company_id, **data)
        self.db.add(benefit)
        await self.db.flush()
        await self.db.refresh(benefit)
        return benefit

    async def update(self, benefit: CompanyBenefit, data: dict) -> CompanyBenefit:
        data["updated_at"] = datetime.utcnow()
        for key, value in data.items():
            setattr(benefit, key, value)
        await self.db.flush()
        await self.db.refresh(benefit)
        return benefit

    async def soft_delete(self, benefit: CompanyBenefit) -> None:
        benefit.is_active = False
        benefit.updated_at = datetime.utcnow()

    async def hard_delete(self, benefit: CompanyBenefit) -> None:
        await self.db.delete(benefit)

    async def count_for_company(self, company_id: str) -> int:
        result = await self.db.execute(
            select(func.count(CompanyBenefit.id)).where(
                CompanyBenefit.company_id == company_id
            )
        )
        return result.scalar() or 0

    async def seed_defaults(self, company_id: str) -> int:
        created = 0
        for bdata in DEFAULT_BRAZILIAN_BENEFITS:
            if not await self.get_by_name(company_id, bdata["name"]):
                self.db.add(CompanyBenefit(company_id=company_id, **bdata))
                created += 1
        return created
