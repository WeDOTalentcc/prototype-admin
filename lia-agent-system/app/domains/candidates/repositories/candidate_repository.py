"""
CandidateRepository — session-in-constructor pattern.
Covers all DB operations needed by app/api/v1/candidates.py.
"""
import logging
import unicodedata
import uuid
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import defer, selectinload

from lia_models.candidate import (
    Candidate,
    CandidateSearch,
    ViewedCandidate,
)

logger = logging.getLogger(__name__)

# Colunas JSON/TEXT pesadas que a LISTAGEM enxuta (GET /candidates sem `full=1`)
# NÃO consome. Evitar trazê-las do Postgres reduz o tempo de list em p95 com
# limit=20, pois economiza I/O + TOAST fetch + serialização no driver.
# Permanecem disponíveis por padrão em GET /candidates/{id} (consulta separada).
_SLIM_LIST_DEFERRED_COLUMNS = (
    "resume_text",
    "cover_letter",
    "work_history",
    "pearch_insights",
    "lia_insights",
    "additional_data",
    "past_locations",
    "diversity_documents",
    "personal_emails",
    "business_emails",
    "phone_types",
    "company_keywords",
    "preferred_channels",
    "channel_opt_out",
    "languages",
    "notes",
    "self_introduction",
)


class CandidateRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Basic CRUD ──────────────────────────────────────────────────────────

    async def get_by_id(self, candidate_id: UUID) -> Candidate | None:
        result = await self.db.execute(
            select(Candidate).where(Candidate.id == candidate_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_str(self, candidate_id: str) -> Candidate | None:
        return await self.get_by_id(uuid.UUID(candidate_id))

    async def get_by_email(self, email: str) -> Candidate | None:
        """
        Look up a candidate by email using the SHA-256 hash index.

        Rows written after migration 060 have email=None and email_hash set.
        Rows written before still have plaintext email; the OR clause handles
        the transition period until pii.backfill_encrypt_existing completes.
        """
        from app.shared.encryption.encrypted_field_mixin import _sha256_hash
        from sqlalchemy import or_
        email_hash = _sha256_hash(email)
        result = await self.db.execute(
            select(Candidate).where(
                or_(
                    Candidate.email_hash == email_hash,
                    Candidate._email_raw == email,  # transition: pre-migration rows with plaintext
                )
            )
        )
        return result.scalar_one_or_none()

    def _build_list_filters(
        self,
        query,
        search: str | None = None,
        status: str | None = None,
        source: str | None = None,
        seniority: str | None = None,
        ids: list[str] | None = None,
    ):
        if ids:
            query = query.where(Candidate.id.in_(ids))

        if search:
            from sqlalchemy import and_
            normalized = unicodedata.normalize("NFKD", search).encode("ASCII", "ignore").decode("ASCII")
            tokens = [t for t in normalized.lower().split() if len(t) >= 2]
            if tokens:
                token_conditions = []
                for token in tokens:
                    term = f"%{token}%"
                    token_conditions.append(
                        or_(
                            func.lower(func.unaccent(Candidate.name)).like(term),
                            func.lower(func.unaccent(Candidate.current_title)).like(term),
                            func.lower(func.unaccent(Candidate.current_company)).like(term),
                            func.lower(func.unaccent(Candidate.location_city)).like(term),
                            func.lower(func.unaccent(Candidate.location_state)).like(term),
                            func.lower(func.unaccent(func.array_to_string(Candidate.technical_skills, " "))).like(term),
                        )
                    )
                query = query.where(and_(*token_conditions))

        if status:
            query = query.where(Candidate.status == status)

        if source:
            query = query.where(Candidate.source == source)

        if seniority:
            query = query.where(func.lower(Candidate.seniority_level) == seniority.lower())

        return query

    async def count_candidates(
        self,
        search: str | None = None,
        status: str | None = None,
        source: str | None = None,
        seniority: str | None = None,
        ids: list[str] | None = None,
    ) -> int:
        query = select(func.count(Candidate.id)).where(Candidate.is_active)
        query = self._build_list_filters(query, search=search, status=status, source=source, seniority=seniority, ids=ids)
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def list_candidates(
        self,
        search: str | None = None,
        status: str | None = None,
        source: str | None = None,
        seniority: str | None = None,
        ids: list[str] | None = None,
        skip: int = 0,
        limit: int = 50,
        sort_by: str | None = None,
        sort_order: str | None = None,
        slim: bool = False,
    ) -> list[Candidate]:
        """
        Lista candidatos paginados ordenados por `sort_by` (default: created_at DESC).

        Parâmetros chave:
          - slim: quando True, pede ao Postgres para NÃO trazer as colunas JSON/TEXT
            pesadas listadas em `_SLIM_LIST_DEFERRED_COLUMNS`. Use para o hot path
            da listagem do /candidates onde o UI consome só campos leves. Índice
            composto `(is_active, created_at DESC)` (migration 081) garante que
            o `ORDER BY created_at DESC` não provoque sort in-memory.
        """
        query = select(Candidate).where(Candidate.is_active)
        query = self._build_list_filters(query, search=search, status=status, source=source, seniority=seniority, ids=ids)

        if slim:
            # defer(*cols) diz ao SQLAlchemy para excluir essas colunas do SELECT;
            # o acesso posterior aos atributos dispararia uma consulta adicional
            # (N+1) — por isso o serializer light (`_serialize_candidate_light`)
            # foi desenhado para não tocar nessas colunas.
            query = query.options(
                *(defer(getattr(Candidate, col)) for col in _SLIM_LIST_DEFERRED_COLUMNS)
            )

        allowed_sort_fields = {
            "created_at": Candidate.created_at,
            "updated_at": Candidate.updated_at,
            "name": Candidate.name,
            "lia_score": Candidate.lia_score,
            "current_title": Candidate.current_title,
            "status": Candidate.status,
        }
        sort_col = allowed_sort_fields.get(sort_by, Candidate.created_at)
        if sort_order == "asc":
            query = query.order_by(sort_col.asc())
        else:
            query = query.order_by(sort_col.desc())

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def search_local(
        self,
        filters: Any,
    ) -> tuple[list[Candidate], int]:
        """
        Full structured local search used by /search/local endpoint.
        Returns (candidates, total_count).
        """
        query = select(Candidate).where(Candidate.is_active == filters.is_active)

        if filters.query:
            normalized = unicodedata.normalize("NFKD", filters.query).encode("ASCII", "ignore").decode("ASCII")
            term = f"%{normalized.lower()}%"
            query = query.where(
                or_(
                    func.lower(func.unaccent(Candidate.name)).like(term),
                    func.lower(func.unaccent(Candidate.current_title)).like(term),
                    func.lower(func.unaccent(Candidate.resume_text)).like(term),
                    func.lower(func.unaccent(func.array_to_string(Candidate.technical_skills, ","))).like(term),
                )
            )

        if filters.required_skills:
            for skill in filters.required_skills:
                query = query.where(
                    func.array_to_string(Candidate.technical_skills, ",").ilike(f"%{skill}%")
                )

        if filters.seniority_levels:
            query = query.where(Candidate.seniority_level.in_(filters.seniority_levels))

        if filters.min_years_experience is not None:
            query = query.where(Candidate.years_of_experience >= filters.min_years_experience)
        if filters.max_years_experience is not None:
            query = query.where(Candidate.years_of_experience <= filters.max_years_experience)

        if filters.locations:
            loc_conds = []
            for loc in filters.locations:
                loc_conds.append(
                    or_(
                        Candidate.location_city.ilike(f"%{loc}%"),
                        Candidate.location_country.ilike(f"%{loc}%"),
                    )
                )
            query = query.where(or_(*loc_conds))

        if filters.remote_only:
            query = query.where(Candidate.is_remote)

        if filters.min_salary is not None:
            query = query.where(Candidate.desired_salary_max >= filters.min_salary)
        if filters.max_salary is not None:
            query = query.where(Candidate.desired_salary_min <= filters.max_salary)

        if filters.statuses:
            query = query.where(Candidate.status.in_(filters.statuses))

        if filters.sources:
            query = query.where(Candidate.source.in_(filters.sources))

        if filters.tags:
            for tag in filters.tags:
                query = query.where(
                    func.array_to_string(Candidate.tags, ",").ilike(f"%{tag}%")
                )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar() or 0

        # Paginate
        query = query.offset(filters.offset).limit(filters.limit)
        result = await self.db.execute(query)
        candidates = list(result.scalars().all())

        return candidates, total_count

    async def create(self, candidate: Candidate) -> Candidate:
        self.db.add(candidate)
        await self.db.commit()
        await self.db.refresh(candidate)
        return candidate

    async def update(self, candidate: Candidate) -> Candidate:
        await self.db.commit()
        await self.db.refresh(candidate)
        return candidate

    async def soft_delete(self, candidate: Candidate) -> None:
        candidate.is_active = False
        candidate.updated_at = datetime.utcnow()
        await self.db.commit()

    # ── Relations ───────────────────────────────────────────────────────────

    async def get_with_experiences(self, candidate_id: UUID) -> Candidate | None:
        result = await self.db.execute(
            select(Candidate)
            .options(
                selectinload(Candidate.experiences),
                selectinload(Candidate.education_records),
            )
            .where(Candidate.id == candidate_id)
        )
        return result.scalar_one_or_none()

    # ── CandidateSearch (analytics) ─────────────────────────────────────────

    async def record_search(self, search_record: CandidateSearch) -> CandidateSearch:
        self.db.add(search_record)
        await self.db.commit()
        await self.db.refresh(search_record)
        return search_record

    # ── ViewedCandidate ─────────────────────────────────────────────────────

    async def get_viewed(self, candidate_id: str, user_id: str) -> ViewedCandidate | None:
        result = await self.db.execute(
            select(ViewedCandidate).where(
                ViewedCandidate.candidate_id == candidate_id,
                ViewedCandidate.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def upsert_viewed(
        self,
        candidate_id: str,
        user_id: str,
        source: str | None = None,
    ) -> tuple[ViewedCandidate, bool]:
        """
        Returns (record, created).
        created=True if a new record was inserted, False if updated.
        """
        existing = await self.get_viewed(candidate_id, user_id)
        if existing:
            existing.viewed_at = datetime.utcnow()
            if source:
                existing.source = source
            await self.db.commit()
            await self.db.refresh(existing)
            return existing, False
        else:
            viewed = ViewedCandidate(
                id=uuid.uuid4(),
                candidate_id=candidate_id,
                user_id=user_id,
                source=source,
            )
            self.db.add(viewed)
            await self.db.commit()
            await self.db.refresh(viewed)
            return viewed, True

    async def delete_viewed(self, candidate_id: str, user_id: str) -> bool:
        record = await self.get_viewed(candidate_id, user_id)
        if not record:
            return False
        await self.db.delete(record)
        await self.db.commit()
        return True

    async def list_viewed(
        self, user_id: str, skip: int = 0, limit: int = 100
    ) -> tuple[list[ViewedCandidate], int]:
        query = (
            select(ViewedCandidate)
            .where(ViewedCandidate.user_id == user_id)
            .order_by(ViewedCandidate.viewed_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        items = list(result.scalars().all())

        count_result = await self.db.execute(
            select(func.count(ViewedCandidate.id)).where(ViewedCandidate.user_id == user_id)
        )
        total = count_result.scalar() or 0
        return items, total
