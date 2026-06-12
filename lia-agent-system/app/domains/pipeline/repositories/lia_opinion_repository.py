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
import uuid

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

    async def create_wsi_opinion(
        self,
        candidate_id: str,
        company_id: str,
        wsi_score: float,
        job_vacancy_id: Optional[str] = None,
        wsi_screening_id: Optional[str] = None,
        recommendation: Optional[str] = None,
    ) -> Optional[str]:
        """Cria LiaOpinion tipo 'wsi' após triagem conversacional. Multi-tenancy fail-closed.

        Args:
            candidate_id: UUID do candidato.
            company_id: UUID do tenant (fail-closed).
            wsi_score: Score na escala 0-100 (já convertido de 0-10).
            job_vacancy_id: UUID da vaga (opcional).
            wsi_screening_id: UUID da sessão WSI (opcional — para rastreio).
            recommendation: 'aprovado', 'aguardando' ou 'reprovado'.

        Returns:
            UUID do opinião criada, ou None em falha.
        """
        self._require_company_id(company_id)

        opinion_id = str(uuid.uuid4())
        await self.db.execute(
            text("""
                INSERT INTO lia_opinions
                    (id, candidate_id, opinion_type, source, job_vacancy_id,
                     wsi_screening_id, score, wsi_score, recommendation,
                     company_id, is_current, version, created_at, updated_at)
                VALUES
                    (:id, :candidate_id::uuid, 'wsi', 'text_screening',
                     :job_vacancy_id, :wsi_screening_id,
                     :score, :wsi_score, :recommendation,
                     :company_id, true, 1, NOW(), NOW())
            """),
            {
                "id": opinion_id,
                "candidate_id": str(candidate_id),
                "job_vacancy_id": str(job_vacancy_id) if job_vacancy_id else None,
                "wsi_screening_id": str(wsi_screening_id) if wsi_screening_id else None,
                "score": wsi_score,
                "wsi_score": wsi_score,
                "recommendation": recommendation,
                "company_id": str(company_id),
            },
        )
        return opinion_id

    async def update_behavioral_analysis(
        self,
        opinion_id: str,
        company_id: str,
        behavioral_analysis: dict,
    ) -> int:
        """2.4: persiste behavioral_analysis (OCEAN traits + behavioral scores) no LiaOpinion."""
        import json as _json
        self._require_company_id(company_id)
        result = await self.db.execute(
            text("""
                UPDATE lia_opinions
                SET behavioral_analysis = :ba::jsonb,
                    updated_at = NOW()
                WHERE id = :opinion_id
                  AND company_id = :company_id
            """),
            {
                "ba": _json.dumps(behavioral_analysis),
                "opinion_id": str(opinion_id),
                "company_id": str(company_id),
            },
        )
        return result.rowcount


