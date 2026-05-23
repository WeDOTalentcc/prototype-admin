"""RecruiterMetricsRepository — canonical pipeline metrics queries (W1-004-B).

W1-004-B (2026-05-23) do MASTER_PLAN.md. Extrai SQL inline de
`app/domains/recruiter_assistant/agents/kanban_tool_registry.py` para repo
canonical (ADR-001 Repository Pattern).

Pre-audit confirmou 11 SQL inline blocks em kanban_tool_registry.py. Este
repo cobre:
 - Piloto: `get_pipeline_benchmarks` (avg_days_per_stage_*)
 - W1-004-B sprint: métricas de stage, bottlenecks, bulk update

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
    - `avg_days_per_stage_for_vacancy`     — per-vacancy stage breakdown
    - `avg_days_per_stage_for_company`     — cross-vacancy company average
    - `count_candidates_per_stage`         — stage counts + hired count
    - `get_stage_metrics`                  — métricas de um stage específico
    - `get_stage_bottleneck_metrics`       — bottlenecks por stage
    - `bulk_update_candidate_stage`        — bulk UPDATE de stage

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

    async def count_candidates_per_stage(
        self,
        *,
        vacancy_id: str,
        company_id: str,
    ) -> dict[str, Any]:
        """Contagem de candidatos por stage (excl. rejected) + hired count.

        Usado por _wrap_get_pipeline_summary para substituir os dois blocos SQL
        inline (stages por status + hired count).

        Args:
            vacancy_id: UUID da vaga (string vazia = todas as vagas).
            company_id: tenant uuid (REQUIRED, fail-closed).

        Returns:
            dict com:
              "per_stage": dict[stage -> int]
              "hired_count": int
        """
        company_id = self._require_company_id(company_id)

        stage_result = await self.db.execute(
            text("""
                SELECT stage, COUNT(*) AS cnt
                FROM vacancy_candidates
                WHERE (:vid = '' OR vacancy_id::text = :vid)
                  AND company_id = :cid
                  AND status != 'rejected'
                GROUP BY stage ORDER BY cnt DESC
            """),
            {"vid": vacancy_id, "cid": company_id},
        )
        per_stage = {row["stage"]: int(row["cnt"]) for row in stage_result.mappings()}

        hired_result = await self.db.execute(
            text("""
                SELECT COUNT(*) AS cnt FROM vacancy_candidates
                WHERE (:vid = '' OR vacancy_id::text = :vid)
                  AND company_id = :cid
                  AND stage ILIKE '%contrat%'
            """),
            {"vid": vacancy_id, "cid": company_id},
        )
        hired = int((hired_result.mappings().first() or {}).get("cnt", 0))

        return {"per_stage": per_stage, "hired_count": hired}

    async def get_stage_metrics(
        self,
        *,
        stage: str,
        vacancy_id: str,
        company_id: str,
    ) -> dict[str, Any]:
        """Métricas de um stage específico: count, avg_days, avg_score, bottleneck_risk.

        Usado por _wrap_get_stage_metrics para substituir o bloco SQL inline.

        Args:
            stage: nome do stage (partial match via ILIKE).
            vacancy_id: UUID da vaga (string vazia = todas as vagas).
            company_id: tenant uuid (REQUIRED, fail-closed).

        Returns:
            dict com candidate_count, avg_time_days, avg_lia_score, bottleneck_risk.
        """
        company_id = self._require_company_id(company_id)

        result = await self.db.execute(
            text("""
                SELECT COUNT(*) AS cnt,
                       AVG(EXTRACT(EPOCH FROM (NOW() - updated_at)) / 86400) AS avg_days,
                       AVG(lia_score) AS avg_score
                FROM vacancy_candidates
                WHERE stage ILIKE :stage_val
                  AND (:vid = '' OR vacancy_id::text = :vid)
                  AND company_id = :cid
            """),
            {"stage_val": f"%{stage}%", "vid": vacancy_id, "cid": company_id},
        )
        data = result.mappings().first() or {}
        count = int(data.get("cnt") or 0)
        avg_days = round(float(data.get("avg_days") or 0), 1)
        avg_score = round(float(data.get("avg_score") or 0), 1)
        bottleneck_risk = "high" if avg_days > 14 else ("medium" if avg_days > 7 else "low")
        return {
            "candidate_count": count,
            "avg_time_days": avg_days,
            "avg_lia_score": avg_score,
            "bottleneck_risk": bottleneck_risk,
        }

    async def get_stage_bottleneck_metrics(
        self,
        *,
        vacancy_id: str,
        company_id: str,
    ) -> list[dict[str, Any]]:
        """Identifica bottlenecks no pipeline (avg_days + stagnant count) por stage.

        Usado por _wrap_identify_bottlenecks para substituir o bloco SQL inline.
        Retorna TODOS os stages com metrics; o caller filtra pelo threshold.

        Args:
            vacancy_id: UUID da vaga (string vazia = todas as vagas).
            company_id: tenant uuid (REQUIRED, fail-closed).

        Returns:
            list de dicts: [{"stage", "candidate_count", "avg_days", "stagnant_count"}]
        """
        company_id = self._require_company_id(company_id)

        result = await self.db.execute(
            text("""
                SELECT stage,
                       COUNT(*) AS cnt,
                       AVG(EXTRACT(EPOCH FROM (NOW() - updated_at)) / 86400) AS avg_days,
                       COUNT(*) FILTER (WHERE updated_at < NOW() - INTERVAL '14 days') AS stagnant
                FROM vacancy_candidates
                WHERE (:vid = '' OR vacancy_id::text = :vid)
                  AND company_id = :cid
                  AND status != 'rejected'
                GROUP BY stage
                ORDER BY avg_days DESC
            """),
            {"vid": vacancy_id, "cid": company_id},
        )
        rows = []
        for row in result.mappings():
            rows.append({
                "stage": row["stage"],
                "candidate_count": int(row["cnt"] or 0),
                "avg_days": round(float(row["avg_days"] or 0), 1),
                "stagnant_count": int(row["stagnant"] or 0),
            })
        return rows

    async def bulk_update_candidate_stage(
        self,
        *,
        vacancy_id: str,
        company_id: str,
        candidate_ids: list[str],
        new_stage: str,
    ) -> int:
        """Bulk UPDATE de stage para múltiplos candidatos. Retorna rowcount atualizado.

        Multi-tenancy: o WHERE filtra por company_id + vacancy_id para garantir
        que nenhum candidato de outro tenant seja atualizado.

        Args:
            vacancy_id: UUID da vaga (string vazia = todas as vagas do company).
            company_id: tenant uuid (REQUIRED, fail-closed).
            candidate_ids: lista de UUIDs de candidatos.
            new_stage: nome do stage de destino.

        Returns:
            int — número de rows atualizadas.
        """
        company_id = self._require_company_id(company_id)
        if not candidate_ids:
            raise ValueError("candidate_ids is required and must not be empty")
        if not new_stage:
            raise ValueError("new_stage is required")

        result = await self.db.execute(
            text("""
                UPDATE vacancy_candidates
                SET stage = :stage, updated_at = NOW()
                WHERE candidate_id = ANY(:ids::uuid[])
                  AND (:vid = '' OR vacancy_id::text = :vid)
                  AND company_id = :cid
            """),
            {"stage": new_stage, "ids": candidate_ids, "vid": vacancy_id, "cid": company_id},
        )
        await self.db.commit()
        return result.rowcount
