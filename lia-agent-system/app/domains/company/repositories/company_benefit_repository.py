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
        """True se o beneficio se aplica ao valor da vaga nesta dimensao.
        Regra: lista vazia/None = aplica a todos; 'all' = curinga; senao casa
        pelo token normalizado (key_fn) ignorando EN/PT, caixa e acentos."""
        if not benefit_values:
            return True
        if any((v or "").strip().lower() == "all" for v in benefit_values):
            return True
        if not vaga_key:
            return True  # vaga nao informou a dimensao -> nao restringe
        return any(key_fn(v) == vaga_key for v in benefit_values)

    @staticmethod
    def _matches_department(departments: dict | None, vaga_department: str | None) -> bool:
        """departments e um dict {nome_dept: bool}. Aplica a todos se vazio ou
        sem chave ativa; 'all' ativo = curinga; senao casa o dept da vaga."""
        if not departments or not any(departments.values()):
            return True
        if departments.get("all"):
            return True
        if not vaga_department:
            return True
        target = _norm(vaga_department)
        return any(enabled and _norm(k) == target for k, enabled in departments.items())

    async def list_matching(
        self,
        company_id: str,
        *,
        seniority_level: str | None = None,
        department: str | None = None,
        contract_type: str | None = None,
        active_only: bool = True,
    ) -> list[tuple[CompanyBenefit, bool]]:
        """Lista beneficios ativos da empresa com flag `matches_vaga` por item.

        Nao remove os nao-compativeis (a vaga exibe o catalogo inteiro agrupado
        por categoria; compativeis vem pre-marcados). matches_vaga = AND de todas
        as dimensoes informadas. ADR-001: filtro vive no repo, nao na API.
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
