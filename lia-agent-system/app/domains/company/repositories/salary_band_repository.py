"""SalaryBand Repository — faixa salarial canonica GRANULAR (catalogo).

ADR-001: query no repo. Multi-tenant fail-closed. Mesmo padrao de
CompensationComponentRepository: multiplas faixas por nivel, casadas por escopo
(level + contrato/departamento/area/filial). Reusa app.shared.eligibility_matching.
"""
import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.salary_band import SalaryBand
from app.domains.job_creation.helpers.vacancy_vocab import (
    _norm,
    to_match_contract_key,
    to_match_seniority_key,
)
from app.shared.eligibility_matching import (
    matches_area,
    matches_department,
    matches_dimension_list,
    matches_subsidiaries,
)
from app.shared.seniority_levels import label_for, order_for

logger = logging.getLogger(__name__)


class SalaryBandRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _require_company_id(company_id: str) -> str:
        if not company_id or company_id in ("default", "unknown"):
            raise ValueError("SalaryBandRepository: company_id obrigatorio (multi-tenancy fail-closed)")
        return company_id

    async def list_for_company(
        self, company_id: str, *, active_only: bool = True, level: str | None = None
    ) -> list[SalaryBand]:
        self._require_company_id(company_id)
        query = select(SalaryBand).where(SalaryBand.company_id == company_id)
        if active_only:
            query = query.where(SalaryBand.is_active.is_(True))
        if level:
            query = query.where(SalaryBand.level == level)
        query = query.order_by(SalaryBand.order, SalaryBand.level)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, band_id: UUID, company_id: str) -> SalaryBand | None:
        self._require_company_id(company_id)
        result = await self.db.execute(
            select(SalaryBand).where(SalaryBand.id == band_id, SalaryBand.company_id == company_id)
        )
        return result.scalar_one_or_none()

    async def create(self, company_id: str, data: dict) -> SalaryBand:
        self._require_company_id(company_id)
        if not data.get("label") and data.get("level"):
            data["label"] = label_for(data["level"])
        if data.get("order") is None and data.get("level"):
            data["order"] = order_for(data["level"])
        band = SalaryBand(company_id=company_id, **data)
        self.db.add(band)
        await self.db.flush()
        await self.db.refresh(band)
        return band

    async def update(self, band: SalaryBand, data: dict) -> SalaryBand:
        data["updated_at"] = datetime.utcnow()
        for k, v in data.items():
            setattr(band, k, v)
        await self.db.flush()
        await self.db.refresh(band)
        return band

    async def soft_delete(self, band: SalaryBand) -> None:
        band.is_active = False
        band.updated_at = datetime.utcnow()

    async def count_for_company(self, company_id: str) -> int:
        self._require_company_id(company_id)
        result = await self.db.execute(
            select(func.count(SalaryBand.id)).where(SalaryBand.company_id == company_id)
        )
        return result.scalar() or 0

    def _scope_specificity(self, b: SalaryBand) -> int:
        """Numero de dimensoes de escopo preenchidas — usado p/ preferir a faixa
        mais especifica num empate de nivel."""
        score = 0
        if b.contract_types:
            score += 1
        if b.departments and any((b.departments or {}).values()):
            score += 1
        if b.area:
            score += 1
        if b.subsidiaries:
            score += 1
        return score

    async def match_band(
        self,
        company_id: str,
        *,
        seniority_level: str,
        department: str | None = None,
        contract_type: str | None = None,
        area: str | None = None,
        subsidiary: str | None = None,
        subsidiary_cnpj: str | None = None,
    ) -> SalaryBand | None:
        """Melhor faixa que casa (nivel + escopo) para um contexto de vaga.
        Prefere a mais especifica; empate -> menor order."""
        self._require_company_id(company_id)
        bands = await self.list_for_company(company_id, active_only=True)
        sen_key = to_match_seniority_key(seniority_level) if seniority_level else ""
        con_key = to_match_contract_key(contract_type) if contract_type else ""
        area_key = _norm(area) if area else ""
        matched = [
            b for b in bands
            if to_match_seniority_key(b.level) == sen_key
            and matches_dimension_list(b.contract_types, con_key, to_match_contract_key)
            and matches_department(b.departments, department)
            and matches_dimension_list(b.area, area_key, _norm)
            and matches_subsidiaries(b.subsidiaries, subsidiary, subsidiary_cnpj)
        ]
        if not matched:
            return None
        matched.sort(key=lambda b: (-self._scope_specificity(b), b.order or 0))
        return matched[0]

    async def get_band_map(self, company_id: str) -> dict[str, dict]:
        """{level: faixa-base} p/ o preview do modal de verba (sem contexto de vaga).
        Base = a faixa do nivel com menos escopo (mais ampla); empate -> menor order."""
        bands = await self.list_for_company(company_id, active_only=True)
        by_level: dict[str, SalaryBand] = {}
        for b in sorted(bands, key=lambda b: (self._scope_specificity(b), b.order or 0)):
            if b.level not in by_level:  # primeira (mais ampla) vence
                by_level[b.level] = b
        return {
            lvl: {"min": b.min, "mid": b.mid, "max": b.max, "currency": b.currency}
            for lvl, b in by_level.items()
        }

    async def seed_defaults(self, company_id: str) -> int:
        self._require_company_id(company_id)
        existing = await self.list_for_company(company_id, active_only=True)
        if existing:
            return 0
        defaults = [
            {"level": "junior", "min": 4000, "mid": 6000, "max": 8000},
            {"level": "pleno", "min": 7000, "mid": 9500, "max": 12000},
            {"level": "senior", "min": 11000, "mid": 14000, "max": 17000},
        ]
        created = 0
        for d in defaults:
            self.db.add(SalaryBand(
                company_id=company_id, label=label_for(d["level"]),
                order=order_for(d["level"]), currency="BRL", **d,
            ))
            created += 1
        return created
