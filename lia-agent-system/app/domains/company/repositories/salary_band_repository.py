"""SalaryBand Repository — faixa salarial canonica por nivel.

ADR-001: toda query no repo, nunca na API/service. Multi-tenant fail-closed:
todo metodo publico exige company_id. Espelha o estilo de
CompensationComponentRepository.
"""
import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.salary_band import SalaryBand
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
        self, company_id: str, *, active_only: bool = True
    ) -> list[SalaryBand]:
        self._require_company_id(company_id)
        query = select(SalaryBand).where(SalaryBand.company_id == company_id)
        if active_only:
            query = query.where(SalaryBand.is_active.is_(True))
        query = query.order_by(SalaryBand.order, SalaryBand.level)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, band_id: UUID, company_id: str) -> SalaryBand | None:
        self._require_company_id(company_id)
        result = await self.db.execute(
            select(SalaryBand).where(
                SalaryBand.id == band_id, SalaryBand.company_id == company_id
            )
        )
        return result.scalar_one_or_none()

    async def get_by_level(self, company_id: str, level: str) -> SalaryBand | None:
        self._require_company_id(company_id)
        result = await self.db.execute(
            select(SalaryBand).where(
                SalaryBand.company_id == company_id,
                SalaryBand.level == level,
                SalaryBand.is_active.is_(True),
            )
        )
        return result.scalars().first()

    async def get_band_map(self, company_id: str) -> dict[str, dict]:
        """{level_id: {min, mid, max, currency}} — consumido pelo motor de calculo
        (compensation_resolution_service) e pelo default de salary_range da vaga."""
        bands = await self.list_for_company(company_id, active_only=True)
        return {
            b.level: {"min": b.min, "mid": b.mid, "max": b.max, "currency": b.currency}
            for b in bands
        }

    async def replace_all(self, company_id: str, bands: list[dict]) -> list[SalaryBand]:
        """Substitui o conjunto de bandas da empresa (UI de Configuracoes salva a
        tabela inteira). Upsert por nivel; niveis ausentes no payload sao removidos."""
        self._require_company_id(company_id)
        existing = await self.list_for_company(company_id, active_only=False)
        by_level = {b.level: b for b in existing}
        incoming_levels = set()

        for raw in bands:
            level = (raw.get("level") or "").strip()
            if not level:
                continue
            incoming_levels.add(level)
            data = {
                "level": level,
                "label": raw.get("label") or label_for(level),
                "min": raw.get("min"),
                "mid": raw.get("mid"),
                "max": raw.get("max"),
                "currency": raw.get("currency") or "BRL",
                "order": raw.get("order", order_for(level)),
                "is_active": True,
                "updated_at": datetime.utcnow(),
            }
            band = by_level.get(level)
            if band is None:
                self.db.add(SalaryBand(company_id=company_id, **data))
            else:
                for k, v in data.items():
                    setattr(band, k, v)

        # remove niveis nao presentes no payload
        for level, band in by_level.items():
            if level not in incoming_levels:
                await self.db.delete(band)

        await self.db.flush()
        return await self.list_for_company(company_id, active_only=True)

    async def count_for_company(self, company_id: str) -> int:
        self._require_company_id(company_id)
        result = await self.db.execute(
            select(func.count(SalaryBand.id)).where(SalaryBand.company_id == company_id)
        )
        return result.scalar() or 0
