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
from sqlalchemy.orm import selectinload

from app.models.candidate import (
    Candidate,
    CandidateSearch,
    ViewedCandidate,
)
from app.models.observability import ConsentRecord

logger = logging.getLogger(__name__)


class CandidateRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Basic CRUD ──────────────────────────────────────────────────────────

    async def get_by_id(
        self,
        candidate_id: UUID,
        company_id: str | None = None,
    ) -> Candidate | None:
        """Get candidate by id. Multi-tenancy defense-in-depth via company_id
        filter quando passado (REGRA ZERO + harness B.1 fail-closed)."""
        # TENANT-EXEMPT: dynamic builder — Candidate.company_id == company_id
        # é appended conditionally below quando company_id passado.
        query = select(Candidate).where(Candidate.id == candidate_id)
        if company_id:
            query = query.where(Candidate.company_id == company_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id_str(
        self,
        candidate_id: str,
        company_id: str | None = None,
    ) -> Candidate | None:
        return await self.get_by_id(uuid.UUID(candidate_id), company_id=company_id)

    async def list_by_ids(
        self,
        candidate_ids: list[str | UUID],
        company_id: str | None = None,
    ) -> list[Candidate]:
        """Return candidates whose ids are in the given list.

        Multi-tenancy defense-in-depth: pass company_id para filter explícito
        no query (recomendado para callers novos). Legacy callers podem omitir
        — Postgres RLS via get_tenant_db continua guardando.

        ADR-001 cross-domain read pattern: usado por candidate_comparison_service
        após caller validar tenant ownership.
        """
        if not candidate_ids:
            return []
        # TENANT-EXEMPT: dynamic builder — Candidate.company_id == company_id
        # é appended conditionally below quando company_id passado.
        query = select(Candidate).where(Candidate.id.in_(candidate_ids))
        if company_id:
            query = query.where(Candidate.company_id == company_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def find_experience_by_candidate_company_title(
        self,
        candidate_id: UUID | str,
        company_name: str,
        title: str,
    ):
        """Return CandidateExperience matching (candidate_id, company, title), or None.

        Used by enrichment service to dedupe before adding scraped experiences.
        """
        from app.models.candidate import CandidateExperience
        result = await self.db.execute(
            select(CandidateExperience).where(
                CandidateExperience.candidate_id == candidate_id,
                CandidateExperience.company_name == company_name,
                CandidateExperience.title == title,
            )
        )
        return result.scalar_one_or_none()

    async def find_education_by_candidate_institution(
        self,
        candidate_id: UUID | str,
        institution: str,
    ):
        """Return CandidateEducation matching (candidate_id, institution), or None.

        Used by enrichment service to dedupe before adding scraped education.
        """
        from app.models.candidate import CandidateEducation
        result = await self.db.execute(
            select(CandidateEducation).where(
                CandidateEducation.candidate_id == candidate_id,
                CandidateEducation.institution == institution,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_email(
        self,
        email: str,
        company_id: str | None = None,
    ) -> Candidate | None:
        """
        Look up a candidate by email using the SHA-256 hash index.

        Rows written after migration 060 have email=None and email_hash set.
        Rows written before still have plaintext email; the OR clause handles
        the transition period until pii.backfill_encrypt_existing completes.

        Multi-tenancy defense-in-depth: pass company_id quando caller souber
        (REGRA ZERO + harness B.1 fail-closed). Quando omitido, Postgres RLS
        via get_tenant_db continua filtrando.
        """
        from app.shared.encryption.encrypted_field_mixin import _sha256_hash
        from sqlalchemy import or_
        email_hash = _sha256_hash(email)
        # TENANT-EXEMPT: dynamic builder — Candidate.company_id == company_id
        # é appended conditionally below quando company_id passado.
        query = select(Candidate).where(
            or_(
                Candidate.email_hash == email_hash,
                Candidate._email_raw == email,  # transition: pre-migration rows with plaintext
            )
        )
        if company_id:
            query = query.where(Candidate.company_id == company_id)
        result = await self.db.execute(query)
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

    async def get_linkedin_url_by_id(self, candidate_id: UUID) -> str | None:
        """Return the candidate's stored LinkedIn URL (or None).

        Cheap projection used by reveal-contact endpoint. ADR-001 cross-domain
        read pattern — caller is responsible for tenant scoping (CreditsUsage
        lookup downstream gates by company_id).
        """
        result = await self.db.execute(
            select(Candidate.linkedin_url)
            .where(Candidate.id == candidate_id)
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def find_by_linkedin_slug(self, linkedin_slug: str) -> Candidate | None:
        """Find first candidate whose linkedin_url contains the given slug.

        Used by reveal-contact when the incoming candidate_id is a non-UUID
        document id and we need to map it to a real UUID. No tenancy filter —
        caller is responsible (this is best-effort identity resolution).
        """
        if not linkedin_slug:
            return None
        # TENANT-EXEMPT: cross-tenant identity resolution by design.
        # linkedin_url é unique-per-person, não per-tenant. Caller (reveal-contact)
        # gates downstream via CreditsUsage.company_id.
        result = await self.db.execute(
            select(Candidate)
            .where(Candidate.linkedin_url.ilike(f"%{linkedin_slug}%"))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_company_id_from_credits_usage(
        self, candidate_id: UUID
    ) -> str | None:
        """Return the company_id from the most recent CreditsUsage row for the
        candidate (or None).

        Used by reveal-contact to recover the originating company when a
        candidate is shared/searched outside a vacancy context. The first
        company that ever paid credits to surface this candidate is the
        canonical tenant for compliance accounting.
        """
        from lia_models.candidate import CreditsUsage

        result = await self.db.execute(
            select(CreditsUsage.company_id)
            .where(CreditsUsage.candidate_id == candidate_id)
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def count_candidates(
        self,
        search: str | None = None,
        status: str | None = None,
        source: str | None = None,
        seniority: str | None = None,
        ids: list[str] | None = None,
        company_id: str | None = None,
    ) -> int:
        """Count candidates with filters. Multi-tenancy defense-in-depth via
        company_id filter quando passado (REGRA ZERO + harness B.1)."""
        # TENANT-EXEMPT: dynamic builder — Candidate.company_id == company_id
        # é appended conditionally below quando company_id passado.
        query = select(func.count(Candidate.id)).where(Candidate.is_active)
        if company_id:
            query = query.where(Candidate.company_id == company_id)
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
        company_id: str | None = None,
    ) -> list[Candidate]:
        """List candidates with filters. Multi-tenancy defense-in-depth via
        company_id filter quando passado (REGRA ZERO + harness B.1)."""
        # TENANT-EXEMPT: dynamic builder — Candidate.company_id == company_id
        # é appended conditionally below quando company_id passado.
        query = select(Candidate).where(Candidate.is_active)
        if company_id:
            query = query.where(Candidate.company_id == company_id)
        query = self._build_list_filters(query, search=search, status=status, source=source, seniority=seniority, ids=ids)

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
        company_id: str | None = None,
    ) -> tuple[list[Candidate], int]:
        """
        Full structured local search used by /search/local endpoint.
        Returns (candidates, total_count).

        Multi-tenancy defense-in-depth: pass company_id para filter explícito
        no query (REGRA ZERO + harness B.1 fail-closed).
        """
        # TENANT-EXEMPT: dynamic builder — Candidate.company_id == company_id
        # é appended conditionally below quando company_id passado.
        query = select(Candidate).where(Candidate.is_active == filters.is_active)
        if company_id:
            query = query.where(Candidate.company_id == company_id)

        # LGPD Art. 18 - excluir candidatos com consent revogado para AI/automated
        # processing. Revoked = revoked_at IS NOT NULL OR is_active = False.
        # Cobre consent types ai_scoring + automated_decision + data_processing.
        revoked_consent_subq = (
            select(ConsentRecord.candidate_id)
            .where(
                ConsentRecord.consent_type.in_([
                    "ai_scoring",
                    "automated_decision",
                    "data_processing",
                ]),
                or_(
                    ConsentRecord.revoked_at.is_not(None),
                    ConsentRecord.is_active == False,  # noqa: E712
                ),
            )
            .scalar_subquery()
        )
        query = query.where(Candidate.id.notin_(revoked_consent_subq))

        # LGPD retention - excluir candidatos com erasure agendada ja vencida.
        query = query.where(
            or_(
                Candidate.scheduled_deletion_at.is_(None),
                Candidate.scheduled_deletion_at > datetime.utcnow(),
            )
        )

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

    async def list_paginated_no_tenant(
        self, limit: int = 30, offset: int = 0
    ) -> list[Candidate]:
        """Paginated list across all tenants — used by Rails-adapter local
        fallback only. Caller is responsible for any tenancy check.

        ADR-001 cross-domain read: integration layer fallback when Rails
        is unavailable; Rails owns tenancy at the API gateway.
        """
        # TENANT-EXEMPT: cross-tenant by design (Rails fallback). Tenancy
        # enforced upstream by Rails API gateway. Apenas usado quando Rails
        # indisponível, em caminho legacy.
        result = await self.db.execute(
            select(Candidate).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def list_active_not_blacklisted(
        self,
        limit: int = 50,
        company_id: str | None = None,
    ) -> list[Candidate]:
        """List active, non-blacklisted candidates up to the given limit.

        Used by app/domains/sourcing/services/sourcing_pipeline_service.py
        (Sprint Q2 ADR-001 cross-domain cleanup) for local sourcing match.

        Multi-tenancy defense-in-depth: pass company_id para filter explícito
        (REGRA ZERO + harness B.1 fail-closed).
        """
        from sqlalchemy import and_ as _and
        # TENANT-EXEMPT: dynamic builder — Candidate.company_id == company_id
        # é appended conditionally below quando company_id passado.
        query = (
            select(Candidate)
            .where(
                _and(
                    Candidate.is_active,
                    ~Candidate.is_blacklisted,
                )
            )
            .limit(limit)
        )
        if company_id:
            query = query.where(Candidate.company_id == company_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

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

    async def get_with_experiences(
        self,
        candidate_id: UUID,
        company_id: str | None = None,
    ) -> Candidate | None:
        """Get candidate with experiences + education preloaded.

        Multi-tenancy defense-in-depth: pass company_id (REGRA ZERO + harness B.1).
        """
        # TENANT-EXEMPT: dynamic builder — Candidate.company_id == company_id
        # é appended conditionally below quando company_id passado.
        query = (
            select(Candidate)
            .options(
                selectinload(Candidate.experiences),
                selectinload(Candidate.education_records),
            )
            .where(Candidate.id == candidate_id)
        )
        if company_id:
            query = query.where(Candidate.company_id == company_id)
        result = await self.db.execute(query)
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
            # RLS-EXEMPT: viewed_candidates has no company_id column and no RLS policy (per-user UX state — which cards the recruiter has opened)  WT-LEGACY-RLS-EXEMPT exp:2026-11-30
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


    # ── ADR-001 W1-004-B: methods migrated from talent_tool_registry ──────────

    @staticmethod
    def _require_company_id(company_id: str | None) -> str:
        """Fail-closed multi-tenancy gate. Raises if company_id is empty/None."""
        if not company_id:
            raise ValueError(
                "company_id is required (multi-tenancy invariant fail-closed)"
            )
        return company_id

    async def search_by_skills_and_experience(
        self,
        company_id: str,
        query: str = "",
        location: str = "",
        min_experience: int = 0,
        limit: int = 20,
    ) -> dict:
        """Search candidates by query text, location, and minimum experience.

        LGPD Art. 11 — dados sensiveis.
        `gender` e dado sensivel per LGPD Art. 11 caput. Acesso permitido
        por base legal: Art. 11 para2 I (consentimento explicito do titular) —
        consent coletado no onboarding do candidato (tabela consent_records,
        purpose='diversity_analytics').
        NAO usar `gender` para scoring/ranking. Use apenas para analytics
        de diversidade agregados (N >= 10, Art. 12 para1).

        Multi-tenancy: company_id validated via _require_company_id fail-closed.
        """
        from sqlalchemy import text as sa_text
        cid = self._require_company_id(company_id)
        rows = await self.db.execute(
            sa_text("""
                SELECT id, name, current_title, location_city, location_state,
                       technical_skills, years_of_experience, lia_score,
                       skills_match_percentage, status
                FROM candidates
                WHERE is_active = true
                  AND company_id = :company_id
                  AND (:query = ''
                       OR name ILIKE :qlike
                       OR current_title ILIKE :qlike
                       OR :query = ANY(technical_skills))
                  AND (:location = '' OR location_city ILIKE :lloc OR location_state ILIKE :lloc)
                  AND (years_of_experience IS NULL OR years_of_experience >= :min_exp)
                ORDER BY lia_score DESC NULLS LAST, created_at DESC
                LIMIT :lim
            """),
            {
                "company_id": cid,
                "query": query,
                "qlike": f"%{query}%",
                "location": location,
                "lloc": f"%{location}%",
                "min_exp": min_experience,
                "lim": limit,
            },
        )
        results = []
        for row in rows.mappings():
            results.append({
                "id": str(row["id"]),
                "name": row["name"],
                "current_title": row["current_title"],
                "location": f"{row['location_city'] or ''}, {row['location_state'] or ''}".strip(", "),
                "skills": row["technical_skills"] or [],
                "years_of_experience": row["years_of_experience"],
                "lia_score": row["lia_score"],
                "match_percentage": row["skills_match_percentage"],
                "status": row["status"],
            })

        count_row = await self.db.execute(
            sa_text("""
                SELECT COUNT(*) AS total FROM candidates
                WHERE is_active = true
                  AND company_id = :company_id
                  AND (:query = '' OR name ILIKE :qlike OR current_title ILIKE :qlike
                       OR :query = ANY(technical_skills))
                  AND (:location = '' OR location_city ILIKE :lloc OR location_state ILIKE :lloc)
                  AND (years_of_experience IS NULL OR years_of_experience >= :min_exp)
            """),
            {
                "company_id": cid,
                "query": query,
                "qlike": f"%{query}%",
                "location": location,
                "lloc": f"%{location}%",
                "min_exp": min_experience,
            },
        )
        total = int((count_row.mappings().first() or {}).get("total", len(results)))
        return {"results": results, "total": total}

    async def get_full_profile(
        self,
        candidate_id: str,
        company_id: str,
    ) -> dict | None:
        """Get full candidate profile including education records.

        LGPD Art. 11 — dados sensiveis.
        `gender` e dado sensivel per LGPD Art. 11 caput. Acesso permitido
        por base legal: Art. 11 para2 I (consentimento explicito do titular) —
        consent coletado no onboarding do candidato (tabela consent_records,
        purpose='diversity_analytics').
        NAO usar `gender` para scoring/ranking. Use apenas para analytics
        de diversidade agregados (N >= 10, Art. 12 para1).

        Multi-tenancy: company_id validated via _require_company_id fail-closed.
        """
        from sqlalchemy import text as sa_text
        cid = self._require_company_id(company_id)
        row = await self.db.execute(
            sa_text("""
                SELECT id, name, email, current_title, current_company,
                       seniority_level, years_of_experience,
                       technical_skills, soft_skills, certifications,
                       location_city, location_state, location_country,
                       lia_score, skills_match_percentage,
                       status, is_active, linkedin_url,
                       self_introduction, work_history, languages,
                       salary_expectation_clt, salary_expectation_pj,
                       work_model_preference, is_remote, willing_to_relocate,
                       gender, source
                FROM candidates
                WHERE id = :cid
                  AND company_id = :company_id
            """),
            {"cid": candidate_id, "company_id": cid},
        )
        data = row.mappings().first()
        if not data:
            return None

        edu_rows = await self.db.execute(
            sa_text("""
                SELECT institution, degree, field_of_study, start_date, end_date, is_completed
                FROM candidate_education
                WHERE candidate_id = :cid
                ORDER BY end_date DESC NULLS FIRST, start_date DESC NULLS FIRST
            """),
            {"cid": candidate_id},
        )
        education = []
        for r in edu_rows.mappings():
            # is_completed=False => curso em andamento => "atual"
            end_label = (r["end_date"] or "?") if r["is_completed"] else "atual"
            education.append({
                "institution": r["institution"],
                "degree": r["degree"],
                "field_of_study": r["field_of_study"],
                "period": f"{r['start_date'] or '?'} - {end_label}",
            })

        return {
            "candidate_id": str(data["id"]),
            "name": data["name"],
            "email": data["email"],
            "current_title": data["current_title"],
            "current_company": data["current_company"],
            "seniority_level": data["seniority_level"],
            "years_of_experience": data["years_of_experience"],
            "technical_skills": data["technical_skills"] or [],
            "soft_skills": data["soft_skills"] or [],
            "certifications": data["certifications"] or [],
            "location": f"{data['location_city'] or ''}, {data['location_country'] or ''}".strip(", "),
            "lia_score": data["lia_score"],
            "match_percentage": data["skills_match_percentage"],
            "status": data["status"],
            "linkedin_url": data["linkedin_url"],
            "summary": data["self_introduction"],
            "languages": data["languages"],
            "work_history": data["work_history"] or [],
            "education": education,
            "salary_expectation_clt": data["salary_expectation_clt"],
            "salary_expectation_pj": data["salary_expectation_pj"],
            "work_model": data["work_model_preference"],
            "is_remote": data["is_remote"],
            "willing_to_relocate": data["willing_to_relocate"],
            "gender": data["gender"],
            "source": data["source"],
            "profile_loaded": True,
        }

    async def list_for_recommendations(
        self,
        candidate_ids: list[str],
        company_id: str,
    ) -> list[dict]:
        """Get candidate score/status data for recommendation generation.

        Multi-tenancy: company_id validated via _require_company_id fail-closed.
        NAO incluir gender no retorno — nao e relevante para recomendacoes.
        """
        from sqlalchemy import text as sa_text
        cid = self._require_company_id(company_id)
        if not candidate_ids:
            return []
        rows = await self.db.execute(
            sa_text("""
                SELECT id, name, status, lia_score, skills_match_percentage,
                       last_contacted_at, last_activity_at
                FROM candidates
                WHERE id = ANY(:ids::uuid[])
                  AND company_id = :company_id
            """),
            {"ids": candidate_ids, "company_id": cid},
        )
        return [dict(r) for r in rows.mappings()]

    async def list_for_report(
        self,
        candidate_ids: list[str],
        company_id: str,
    ) -> list[dict]:
        """Get candidates for report generation (name, title, score, status).

        Multi-tenancy: company_id validated via _require_company_id fail-closed.
        """
        from sqlalchemy import text as sa_text
        cid = self._require_company_id(company_id)
        if not candidate_ids:
            return []
        rows = await self.db.execute(
            sa_text("""
                SELECT name, current_title, lia_score, skills_match_percentage, status
                FROM candidates
                WHERE id = ANY(:ids::uuid[])
                  AND company_id = :company_id
                ORDER BY lia_score DESC NULLS LAST
            """),
            {"ids": candidate_ids, "company_id": cid},
        )
        return [dict(r) for r in rows.mappings()]

    async def get_skill_set(
        self,
        candidate_id: str,
        company_id: str,
    ) -> set:
        """Get candidate technical skills as lowercase set.

        Multi-tenancy: company_id validated via _require_company_id fail-closed.
        """
        from sqlalchemy import text as sa_text
        cid = self._require_company_id(company_id)
        row = await self.db.execute(
            sa_text(
                "SELECT technical_skills FROM candidates "
                "WHERE id = :cid AND company_id = :company_id"
            ),
            {"cid": candidate_id, "company_id": cid},
        )
        data = row.mappings().first()
        return {s.lower() for s in ((data or {}).get("technical_skills") or [])}

    async def get_applications_summary(
        self,
        company_id: str,
        period_days: int = 30,
    ) -> dict:
        """Get application counts for report generation.

        Multi-tenancy: company_id validated via _require_company_id fail-closed.
        """
        from sqlalchemy import text as sa_text
        cid = self._require_company_id(company_id)
        row = await self.db.execute(
            sa_text("""
                SELECT
                    COUNT(*) AS total,
                    COUNT(*) FILTER (WHERE status = 'approved') AS approved,
                    COUNT(*) FILTER (WHERE status = 'rejected') AS rejected
                FROM applications
                WHERE company_id = :cid
                  AND created_at > NOW() - MAKE_INTERVAL(days => :days)
            """),
            {"cid": cid, "days": period_days},
        )
        data = row.mappings().first() or {}
        return {
            "total_applications": int(data.get("total") or 0),
            "approved": int(data.get("approved") or 0),
            "rejected": int(data.get("rejected") or 0),
        }

    # ── ADR-001 W1-004-C: new method migrated from outcome_learning_service ──

    async def get_candidate_with_job_context(
        self, candidate_id: str, company_id: str, job_id: str = None
    ) -> dict | None:
        """Candidato + contexto da vaga para outcome learning.

        Multi-tenancy: company_id validated via _require_company_id fail-closed.

        NOTE: f-string is safe here because job_join and SELECT fields are
        constructed internally from boolean flag — NOT from user input.
        SQL parameters use parameterized bindings (:cid, :company_id, :job_id).
        """
        from sqlalchemy import text as _text
        self._require_company_id(company_id)
        params = {"cid": candidate_id, "company_id": company_id}
        job_join = ""
        job_select = "NULL AS job_title, NULL AS job_id"
        if job_id:
            job_join = "LEFT JOIN job_vacancies jv ON jv.id::text = :job_id"
            job_select = "jv.title AS job_title, jv.id AS job_id"
            params["job_id"] = job_id
        result = await self.db.execute(
            _text(f"""
            SELECT c.id, c.name, c.email, c.company_id,
                   {job_select}
            FROM candidates c
            {job_join}
            WHERE c.id::text = :cid
              AND (c.company_id IS NULL OR c.company_id = :company_id)
            LIMIT 1
            """),
            params
        )
        row = result.mappings().fetchone()
        return dict(row) if row else None
