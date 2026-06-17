"""DigitalTwin repository — canonical ADR-001 abstraction.

Wave C1.1 (2026-05-27). Eliminates the 3 raw `select(DigitalTwin)` /
`select(TwinDecision)` calls scattered across the Studio twin services:

  - app/services/twin_inference_service.py:64  (select(DigitalTwin))
  - app/services/twin_inference_service.py:168 (select(TwinDecision))
  - app/services/twin_knowledge_indexer.py:270 (select(DigitalTwin))

Multi-tenancy fail-closed: every public method requires `company_id` and
guards with `_require_company_id`. `get_by_id` / `add_decision` /
`search_similar_decisions` enforce that the twin row is scoped to the
caller tenant before returning or mutating any data (LGPD Art. 6 II — tenant
isolation; ADR-LGPD-001 — twin corpora are tenant-owned).

Plus method `search_similar_decisions` keeps the canonical raw pgvector
K-NN query (cosine `<=>` operator) inside the repo so services no longer
hand-write SQL. The query is marked with the canonical EXEMPT pattern in
the docstring since pgvector ordering is not expressible via the
`select()` DSL — the SQL is encapsulated in this single canonical site.
"""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, select, text as sql_text
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.digital_twin import DigitalTwin, TwinDecision


def _require_company_id(company_id: Any) -> None:
    """Fail-closed guard — multi-tenancy invariant."""
    if not isinstance(company_id, str) or not company_id.strip():
        raise ValueError(
            "DigitalTwinRepository: company_id is required (multi-tenancy "
            "fail-closed)."
        )


class DigitalTwinRepository:
    """ADR-001 canonical reads/writes for DigitalTwin + TwinDecision rows.

    Replaces inline `select(DigitalTwin)` / `select(TwinDecision)` in
    twin_inference_service.py + twin_knowledge_indexer.py.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ---------------- DigitalTwin CRUD ----------------

    async def create(
        self,
        *,
        company_id: str,
        twin_name: str,
        sme_user_id: str | None = None,
        specialties: list[str] | None = None,
        description: str | None = None,
    ) -> DigitalTwin:
        """Create a new DigitalTwin row scoped to `company_id`."""
        _require_company_id(company_id)
        twin = DigitalTwin(
            id=uuid.uuid4(),
            company_id=company_id,
            twin_name=twin_name,
            sme_user_id=sme_user_id,
            specialties=specialties or [],
            description=description,
        )
        self._db.add(twin)
        await self._db.flush()
        await self._db.refresh(twin)
        return twin

    async def get_by_id(
        self, *, twin_id: str, company_id: str
    ) -> DigitalTwin | None:
        """Load a DigitalTwin scoped to the tenant.

        Returns None if no row matches OR row belongs to another tenant.
        """
        _require_company_id(company_id)
        stmt = select(DigitalTwin).where(
            DigitalTwin.id == twin_id,
            DigitalTwin.company_id == company_id,
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_company(
        self,
        *,
        company_id: str,
        is_active: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[DigitalTwin]:
        """List DigitalTwin rows for a tenant, ordered by updated_at desc."""
        _require_company_id(company_id)
        stmt = select(DigitalTwin).where(DigitalTwin.company_id == company_id)
        if is_active is not None:
            stmt = stmt.where(DigitalTwin.is_active == is_active)
        stmt = (
            stmt.order_by(DigitalTwin.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def update(
        self,
        *,
        twin_id: str,
        company_id: str,
        data: dict[str, Any],
    ) -> DigitalTwin | None:
        """Update mutable fields on a tenant-scoped DigitalTwin."""
        _require_company_id(company_id)
        twin = await self.get_by_id(twin_id=twin_id, company_id=company_id)
        if twin is None:
            return None
        for field, value in data.items():
            if value is None:
                continue
            if hasattr(twin, field):
                setattr(twin, field, value)
        await self._db.flush()
        await self._db.refresh(twin)
        return twin

    async def delete(self, *, twin_id: str, company_id: str) -> bool:
        """Hard delete a tenant-scoped DigitalTwin (cascades to TwinDecisions)."""
        _require_company_id(company_id)
        twin = await self.get_by_id(twin_id=twin_id, company_id=company_id)
        if twin is None:
            return False
        await self._db.delete(twin)
        await self._db.flush()
        return True

    async def count_by_company(self, *, company_id: str) -> int:
        """Count DigitalTwin rows for a tenant."""
        _require_company_id(company_id)
        stmt = select(func.count(DigitalTwin.id)).where(
            DigitalTwin.company_id == company_id
        )
        result = await self._db.execute(stmt)
        return int(result.scalar() or 0)

    # ---------------- TwinDecision (corpus) ----------------

    async def get_twin_decisions(
        self,
        *,
        twin_id: str,
        company_id: str,
        limit: int = 5,
    ) -> list[TwinDecision]:
        """Return most recent TwinDecision rows for a tenant-owned twin.

        Fallback path used when the caller has no embedding for K-NN.
        Enforces tenant isolation by first validating the parent twin.
        """
        _require_company_id(company_id)
        # Validate twin ownership before touching decisions (defense in depth).
        twin = await self.get_by_id(twin_id=twin_id, company_id=company_id)
        if twin is None:
            return []
        stmt = (
            select(TwinDecision)
            .where(TwinDecision.twin_id == twin_id)
            .order_by(TwinDecision.created_at.desc())
            .limit(limit)
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def count_decisions(
        self, *, twin_id: str, company_id: str
    ) -> int:
        """Count decisions in a tenant-owned twin's corpus."""
        _require_company_id(company_id)
        # Validate twin ownership first.
        twin = await self.get_by_id(twin_id=twin_id, company_id=company_id)
        if twin is None:
            return 0
        stmt = select(func.count()).where(TwinDecision.twin_id == twin_id)
        result = await self._db.execute(stmt)
        return int(result.scalar() or 0)

    async def add_decision(
        self, *, decision: TwinDecision, company_id: str
    ) -> TwinDecision:
        """Persist a TwinDecision instance after validating tenant ownership.

        Caller constructs the TwinDecision (with `twin_id`, embedding, snapshots);
        this method guards that the parent twin belongs to `company_id` then
        adds it to the session. Caller is responsible for `commit()` at the
        end of the unit of work — repo only `flush`es.
        """
        _require_company_id(company_id)
        twin = await self.get_by_id(
            twin_id=str(decision.twin_id), company_id=company_id
        )
        if twin is None:
            raise ValueError(
                f"DigitalTwinRepository.add_decision: twin_id={decision.twin_id} "
                f"not found for company_id={company_id} (tenant isolation)."
            )
        self._db.add(decision)
        await self._db.flush()
        return decision

    async def update_decision_count(
        self, *, twin_id: str, company_id: str
    ) -> int:
        """Recompute `decision_count` on twin from current corpus size."""
        _require_company_id(company_id)
        twin = await self.get_by_id(twin_id=twin_id, company_id=company_id)
        if twin is None:
            return 0
        total = await self.count_decisions(
            twin_id=twin_id, company_id=company_id
        )
        twin.decision_count = total
        await self._db.flush()
        return total

    async def search_similar_decisions(
        self,
        *,
        twin_id: str,
        company_id: str,
        embedding: list[float],
        k: int = 5,
    ) -> list[dict[str, Any]]:
        """K-NN search over `twin_decisions.embedding` (pgvector cosine).

        Returns raw row dicts (decision, reasoning, candidate_snapshot,
        job_snapshot, similarity) ordered by similarity desc. Centralizes the
        single pgvector raw SQL the codebase needs — services no longer
        hand-write the `<=>` operator.

        Multi-tenancy: validates the parent twin belongs to `company_id` before
        running the K-NN query.
        """
        _require_company_id(company_id)
        twin = await self.get_by_id(twin_id=twin_id, company_id=company_id)
        if twin is None:
            return []

        embedding_str = str(embedding)
        result = await self._db.execute(
            sql_text(
                """
                SELECT decision, reasoning, candidate_snapshot, job_snapshot,
                       1 - (embedding <=> :emb::vector) AS similarity
                FROM twin_decisions
                WHERE twin_id = :twin_id
                  AND embedding IS NOT NULL
                ORDER BY embedding <=> :emb::vector
                LIMIT :k
                """
            ),
            {"twin_id": twin_id, "emb": embedding_str, "k": k},
        )
        rows = result.fetchall()
        return [
            {
                "decision": r[0],
                "reasoning": r[1],
                "candidate_snapshot": r[2] or {},
                "job_snapshot": r[3] or {},
                "similarity": round(float(r[4]), 3) if r[4] is not None else 0.0,
            }
            for r in rows
        ]
