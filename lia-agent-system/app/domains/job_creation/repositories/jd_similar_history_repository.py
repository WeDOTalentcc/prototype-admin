"""JdSimilarHistoryRepository — Sprint B Phase 1.

ADR-001: Repository pattern. Único lugar onde queries SQL contra
`jd_similar_history` rodam.

Multi-tenancy: `company_id` é obrigatório em toda operação. Fail-closed.
Threshold: find_similar_jds retorna [] se company tem < 10 JDs em histórico.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.jd_similar_history import JD_EMBEDDING_DIM, JdSimilarHistory

logger = logging.getLogger(__name__)


# ── Thresholds ──────────────────────────────────────────────────────────────
JD_SIMILAR_MIN_HISTORY = 10
DEFAULT_LIMIT = 3
DEFAULT_MIN_SIMILARITY = 0.7


class JdSimilarHistoryRepository:
    """CRUD + similarity search para JdSimilarHistory."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Validations ─────────────────────────────────────────────────────────

    @staticmethod
    def _require_company_id(company_id: str) -> None:
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy enforcement)")

    @staticmethod
    def _validate_embedding(embedding: list[float] | None) -> None:
        if embedding is None:
            return
        if len(embedding) != JD_EMBEDDING_DIM:
            raise ValueError(
                f"Embedding must have {JD_EMBEDDING_DIM} dimensions, "
                f"got {len(embedding)}. Use OpenAI text-embedding-3-small.",
            )

    # ── Read ────────────────────────────────────────────────────────────────

    async def get_by_id(
        self, record_id: UUID, company_id: str
    ) -> JdSimilarHistory | None:
        """Lookup by id, scoped to company (multi-tenancy fail-closed).

        Returns None if record doesn't exist OR belongs to another company
        — cross-tenant access reads as 'not found' for read ops (SPEC D3).
        Raises ValueError if company_id is empty.

        Sprint B Phase 1, gap C5.
        """
        self._require_company_id(company_id)
        stmt = select(JdSimilarHistory).where(
            JdSimilarHistory.id == record_id,
            JdSimilarHistory.company_id == company_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def count_for_company(self, company_id: str) -> int:
        self._require_company_id(company_id)
        stmt = select(func.count(JdSimilarHistory.id)).where(
            JdSimilarHistory.company_id == company_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def find_similar_jds(
        self,
        company_id: str,
        embedding: list[float],
        min_similarity: float = DEFAULT_MIN_SIMILARITY,
        limit: int = DEFAULT_LIMIT,
        department: str | None = None,
    ) -> list[dict[str, Any]]:
        """Returns top-N JDs similar to `embedding` for `company_id`.

        Returns [] when company has < JD_SIMILAR_MIN_HISTORY entries (fail-open silencioso).
        Multi-tenancy: query filtra por company_id; multi-tenancy garantido.
        """
        self._require_company_id(company_id)
        self._validate_embedding(embedding)

        total = await self.count_for_company(company_id)
        if total < JD_SIMILAR_MIN_HISTORY:
            logger.debug(
                "[JdSimilarHistory] company %s has %d JDs (<%d threshold), skipping",
                company_id, total, JD_SIMILAR_MIN_HISTORY,
            )
            return []

        # pgvector cosine similarity: 1 - (a <=> b). Operator <=> is cosine distance.
        # Convert distance to similarity: similarity = 1 - distance.
        cosine_distance = JdSimilarHistory.jd_embedding.cosine_distance(embedding)
        similarity = (1 - cosine_distance).label("similarity")

        conditions = [
            JdSimilarHistory.company_id == company_id,
            JdSimilarHistory.jd_embedding.is_not(None),
        ]
        if department:
            conditions.append(JdSimilarHistory.department == department)

        stmt = (
            select(JdSimilarHistory, similarity)
            .where(and_(*conditions))
            .order_by(cosine_distance.asc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        rows = result.all()

        out: list[dict[str, Any]] = []
        for row, sim_score in rows:
            if sim_score is not None and sim_score < min_similarity:
                continue
            out.append({
                "id": str(row.id),
                "title": row.title_normalized,
                "department": row.department,
                "seniority_level": row.seniority_level,
                "was_filled": row.was_filled,
                "time_to_fill_days": row.time_to_fill_days,
                "candidates_count": row.candidates_count,
                "similarity": float(sim_score) if sim_score is not None else None,
            })
        return out

    # ── Write ───────────────────────────────────────────────────────────────

    async def record_jd(
        self,
        company_id: str,
        job_id: str,
        title_normalized: str,
        jd_enriched: dict[str, Any],
        embedding: list[float],
        seniority_level: str | None = None,
        department: str | None = None,
    ) -> JdSimilarHistory:
        """Inserts new JD record. Fail-closed em company_id ausente."""
        self._require_company_id(company_id)
        self._validate_embedding(embedding)

        record = JdSimilarHistory(
            company_id=company_id,
            job_id=job_id,
            title_normalized=title_normalized,
            jd_enriched_json=jd_enriched,
            jd_embedding=embedding,
            seniority_level=seniority_level,
            department=department,
            was_filled=False,
            candidates_count=0,
            reused_count=0,
        )
        self.db.add(record)
        await self.db.commit()
        # Refresh para popular id se driver não preencheu
        try:
            await self.db.refresh(record)
        except Exception:  # pragma: no cover — refresh é best-effort em testes
            pass
        return record

    async def mark_filled(
        self,
        record_id: UUID,
        company_id: str,
        time_to_fill_days: int,
        candidates_count: int,
    ) -> None:
        """Marca JD como preenchida (vaga fechou). Atualiza outcome stats.

        Multi-tenancy fail-closed (Sprint B Phase 1, gap C5):
        - Raises ValueError if company_id is empty.
        - Raises ValueError if record_id belongs to another company
          (cross-tenant write attempt).
        """
        self._require_company_id(company_id)
        # Ownership check: SELECT FOR ownership before UPDATE
        owner_stmt = select(JdSimilarHistory.company_id).where(
            JdSimilarHistory.id == record_id
        )
        owner_result = await self.db.execute(owner_stmt)
        owner = owner_result.scalar_one_or_none()
        if owner is None or str(owner) != str(company_id):
            raise ValueError(
                f"company_id mismatch or record not found: "
                f"record {record_id} cannot be modified by company {company_id}"
            )

        stmt = (
            update(JdSimilarHistory)
            .where(
                JdSimilarHistory.id == record_id,
                JdSimilarHistory.company_id == company_id,
            )
            .values(
                was_filled=True,
                time_to_fill_days=time_to_fill_days,
                candidates_count=candidates_count,
                updated_at=datetime.utcnow(),
            )
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def find_id_by_job(self, company_id: str, job_id: str):
        """Lookup record id pelo job_id no scope de uma company (multi-tenancy)."""
        self._require_company_id(company_id)
        stmt = (
            select(JdSimilarHistory.id)
            .where(JdSimilarHistory.company_id == company_id)
            .where(JdSimilarHistory.job_id == job_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def increment_reuse(self, record_id: UUID, company_id: str) -> None:
        """Incrementa contador de reuso quando recruiter reaproveita JD.

        Multi-tenancy fail-closed (Sprint B Phase 1, gap C5):
        - Raises ValueError if company_id is empty or doesn't own record.
        """
        self._require_company_id(company_id)
        owner_stmt = select(JdSimilarHistory.company_id).where(
            JdSimilarHistory.id == record_id
        )
        owner_result = await self.db.execute(owner_stmt)
        owner = owner_result.scalar_one_or_none()
        if owner is None or str(owner) != str(company_id):
            raise ValueError(
                f"company_id mismatch or record not found: "
                f"record {record_id} cannot be reused by company {company_id}"
            )

        stmt = (
            update(JdSimilarHistory)
            .where(
                JdSimilarHistory.id == record_id,
                JdSimilarHistory.company_id == company_id,
            )
            .values(
                reused_count=JdSimilarHistory.reused_count + 1,
                last_reused_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        )
        await self.db.execute(stmt)
        await self.db.commit()
