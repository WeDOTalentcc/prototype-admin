"""
TenantContextService — contexto rico por tenant para personalização da LIA.
Injeta nome, setor, nível de autonomia e estado atual no contexto do orquestrador.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


@dataclass
class TenantContext:
    company_id: str
    company_name: str
    sector: str
    open_vacancies: int
    autonomy_level: str  # "high" | "medium" | "low"
    plan: str

    def to_prompt_snippet(self) -> str:
        return (
            f"Você está assistindo **{self.company_name}**, empresa do setor "
            f"**{self.sector}** com **{self.open_vacancies}** vagas abertas. "
            f"Nível de autonomia configurado: **{self.autonomy_level}**. "
            f"Plano: {self.plan}."
        )


class TenantContextService:
    """Busca contexto rico do tenant para personalizar respostas da LIA."""

    async def get_context(self, company_id: str, db: AsyncSession) -> TenantContext:
        """Retorna contexto do tenant. Fail-safe: retorna defaults se falhar."""
        try:
            from lia_models.company import Company
            from lia_models.job_vacancy import JobVacancy

            result = await db.execute(
                select(Company).where(Company.id == company_id)
            )
            company = result.scalar_one_or_none()

            open_count_result = await db.execute(
                select(func.count()).select_from(JobVacancy).where(
                    JobVacancy.company_id == company_id,
                    JobVacancy.status == "open",
                )
            )
            open_vacancies = open_count_result.scalar() or 0

            # Determinar nível de autonomia via PolicyEngine
            autonomy_level = "medium"
            try:
                from app.services.policy_engine_service import PolicyEngineService
                policy_svc = PolicyEngineService()
                policy = await policy_svc.get_active_policy(company_id, db)
                if policy:
                    autonomy_level = getattr(policy, "autonomy_level", "medium")
            except Exception:
                pass

            if company:
                return TenantContext(
                    company_id=company_id,
                    company_name=getattr(company, "name", "sua empresa"),
                    sector=getattr(company, "sector", "geral"),
                    open_vacancies=open_vacancies,
                    autonomy_level=autonomy_level,
                    plan=getattr(company, "plan", "standard"),
                )
        except Exception as exc:
            logger.debug("[TenantContextService] fallback defaults: %s", exc)

        return TenantContext(
            company_id=company_id,
            company_name="sua empresa",
            sector="geral",
            open_vacancies=0,
            autonomy_level="medium",
            plan="standard",
        )
