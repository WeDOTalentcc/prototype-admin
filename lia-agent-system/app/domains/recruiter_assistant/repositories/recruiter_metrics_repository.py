"""RecruiterMetricsRepository — canonical pipeline metrics queries (W1-004-B piloto).

W1-004-B (2026-05-23) do MASTER_PLAN.md. Extrai SQL inline de
`app/domains/recruiter_assistant/agents/kanban_tool_registry.py` para repo
canonical (ADR-001 Repository Pattern).

Pre-audit confirmou 13 SQL inline blocks em kanban_tool_registry.py. Este
repo cobre o piloto canonical: `get_pipeline_benchmarks` tool function.
Outros 12 blocks ficam em backlog (próxima sprint, mesmo pattern).

Multi-tenancy fail-closed via `_require_company_id` em todo método público.
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class RecruiterMetricsRepository:
    """Repository canonical para pipeline metrics queries no recruiter_assistant.

    Métodos canonical:
    - `avg_days_per_stage_for_vacancy` — per-vacancy stage breakdown
    - `avg_days_per_stage_for_company` — cross-vacancy company average

    Usage:
        from app.domains.recruiter_assistant.repositories.recruiter_metrics_repository import (
            RecruiterMetricsRepository,
        )
        async with AsyncSessionLocal() as session:
            repo = RecruiterMetricsRepository(session)
            per_stage = await repo.avg_days_per_stage_for_vacancy(
                vacancy_id=vid, company_id=cid
            )
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _require_company_id(company_id: Any) -> str:
        """Multi-tenancy fail-closed gate (ADR-001 + REGRA 6)."""
        if not company_id:
            raise ValueError(
                "company_id is required (multi-tenancy fail-closed). "
                "RecruiterMetricsRepository never accepts cross-tenant queries."
            )
        return str(company_id)

    async def avg_days_per_stage_for_vacancy(
        self,
        *,
        vacancy_id: str,
        company_id: str,
    ) -> dict[str, dict[str, Any]]:
        """Average days per stage para uma vacancy específica (per-tenant).

        Args:
            vacancy_id: UUID da vaga.
            company_id: tenant uuid (REQUIRED, fail-closed).

        Returns:
            dict[stage_name -> {"avg_days": float, "candidates": int}]
        """
        company_id = self._require_company_id(company_id)
        if not vacancy_id:
            raise ValueError("vacancy_id is required")

        result = await self.db.execute(
            text(
                "SELECT stage, "
                "AVG(EXTRACT(EPOCH FROM (updated_at - created_at)) / 86400) AS avg_days, "
                "COUNT(*) AS candidates "
                "FROM vacancy_candidates "
                "WHERE vacancy_id = :vid AND company_id = :cid "
                "GROUP BY stage"
            ),
            {"vid": vacancy_id, "cid": company_id},
        )
        return {
            row["stage"]: {
                "avg_days": round(float(row["avg_days"] or 0), 1),
                "candidates": int(row["candidates"]),
            }
            for row in result.mappings()
        }

    async def avg_days_per_stage_for_company(
        self,
        *,
        company_id: str,
    ) -> dict[str, dict[str, Any]]:
        """Average days per stage agregado em TODAS as vagas do company.

        Args:
            company_id: tenant uuid (REQUIRED, fail-closed).

        Returns:
            dict[stage_name -> {"avg_days": float, "candidates": int}]
        """
        company_id = self._require_company_id(company_id)

        result = await self.db.execute(
            text(
                "SELECT vc.stage, "
                "AVG(EXTRACT(EPOCH FROM (vc.updated_at - vc.created_at)) / 86400) AS avg_days, "
                "COUNT(*) AS candidates "
                "FROM vacancy_candidates vc "
                "JOIN job_vacancies jv ON jv.id = vc.vacancy_id "
                "WHERE jv.company_id = :cid "
                "GROUP BY vc.stage"
            ),
            {"cid": company_id},
        )
        return {
            row["stage"]: {
                "avg_days": round(float(row["avg_days"] or 0), 1),
                "candidates": int(row["candidates"]),
            }
            for row in result.mappings()
        }
