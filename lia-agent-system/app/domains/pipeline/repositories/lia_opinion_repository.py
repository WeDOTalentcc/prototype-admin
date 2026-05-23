"""LiaOpinionRepository — ADR-001 canonical.

WSI/LIA scores por candidato no contexto do Pipeline Transition Agent.
Migrado de pipeline_tool_registry.py: _wrap_get_candidate_wsi_scores.
Multi-tenancy fail-closed via _require_company_id.

Schema source of truth: libs/models/lia_models/lia_opinion.py
Tabela: lia_opinions — tem company_id nativo.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class LiaOpinionRepository:
    """Repository canonical com multi-tenancy fail-closed."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    @staticmethod
    def _require_company_id(company_id: str) -> None:
        if not company_id:
            raise ValueError("company_id is required — multi-tenancy fail-closed")

    async def get_by_candidate(
        self,
        candidate_id: str,
        company_id: str,
        job_id: Optional[str] = None,
        limit: int = 5,
    ) -> list[dict]:
        """Retorna LIA opinions para um candidato (filtrado por tenant). Fail-closed.

        Args:
            candidate_id: UUID do candidato.
            company_id: UUID do tenant (fail-closed).
            job_id: UUID da vaga (opcional — filtra por vaga específica).
            limit: máximo de registros retornados (default 5).
        """
        self._require_company_id(company_id)

        query = """
            SELECT lo.id, lo.score, lo.wsi_score, lo.opinion_type, lo.source,
                   lo.recommendation, lo.technical_analysis, lo.behavioral_analysis,
                   lo.strengths, lo.concerns, lo.gaps,
                   lo.created_at
            FROM lia_opinions lo
            WHERE lo.candidate_id = :cid
              AND lo.company_id = :company_id
        """
        params: dict = {"cid": candidate_id, "company_id": company_id}

        if job_id:
            query += " AND lo.job_vacancy_id = :jid"
            params["jid"] = job_id

        query += " ORDER BY lo.created_at DESC LIMIT :limit"
        params["limit"] = limit

        result = await self.db.execute(text(query), params)
        rows = result.mappings().all()

        scores = []
        for row in rows:
            score_data = dict(row)
            for k, v in score_data.items():
                if isinstance(v, datetime):
                    score_data[k] = v.isoformat()
            scores.append(score_data)

        return scores
