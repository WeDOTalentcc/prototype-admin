"""
OpinionsRepository — session-in-constructor pattern.
Covers all DB operations needed by app/api/v1/opinions.py.
"""
import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, desc, func, select, update, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job_vacancy import JobVacancy
from app.models.lia_opinion import LiaOpinion

logger = logging.getLogger(__name__)


class OpinionsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Job vacancy helper ─────────────────────────────────────────────────

    async def get_job_title(self, job_vacancy_id: UUID) -> str | None:
        result = await self.db.execute(
            select(JobVacancy.title).where(JobVacancy.id == job_vacancy_id)
        )
        return result.scalar_one_or_none()

    # ── Read ───────────────────────────────────────────────────────────────

    async def get_current_by_candidate(
        self, candidate_id: UUID, company_id: UUID | str
    ) -> list[LiaOpinion]:
        self._require_company_id(str(company_id))
        result = await self.db.execute(
            select(LiaOpinion).where(
                and_(
                    LiaOpinion.candidate_id == candidate_id,
                    LiaOpinion.company_id == company_id,
                    LiaOpinion.is_current,
                )
            ).order_by(desc(LiaOpinion.created_at))
        )
        return list(result.scalars().all())

    async def get_history_by_candidate(
        self, candidate_id: UUID, company_id: UUID | str
    ) -> list[LiaOpinion]:
        self._require_company_id(str(company_id))
        result = await self.db.execute(
            select(LiaOpinion).where(
                and_(
                    LiaOpinion.candidate_id == candidate_id,
                    LiaOpinion.company_id == company_id,
                )
            ).order_by(desc(LiaOpinion.created_at))
        )
        return list(result.scalars().all())

    async def list_with_filters(
        self,
        candidate_id: UUID,
        company_id: UUID | str,
        opinion_type: str | None = None,
        job_vacancy_id: UUID | None = None,
        include_history: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[LiaOpinion], int]:
        self._require_company_id(str(company_id))
        conditions = [
            LiaOpinion.candidate_id == candidate_id,
            LiaOpinion.company_id == company_id,
        ]

        if not include_history:
            conditions.append(LiaOpinion.is_current)

        if opinion_type:
            conditions.append(LiaOpinion.opinion_type == opinion_type)

        if job_vacancy_id:
            conditions.append(LiaOpinion.job_vacancy_id == job_vacancy_id)

        # Count total
        count_result = await self.db.execute(
            # TENANT-EXEMPT: query uses dynamic conditions=[Model.company_id==X, ...] builder; AST sensor cannot trace; T-RATCHET tenant_filter
            select(LiaOpinion).where(and_(*conditions))
        )
        total = len(count_result.scalars().all())

        # Paginated fetch
        result = await self.db.execute(
            # TENANT-EXEMPT: query uses dynamic conditions=[Model.company_id==X, ...] builder; AST sensor cannot trace; T-RATCHET tenant_filter
            select(LiaOpinion).where(and_(*conditions))
            .order_by(desc(LiaOpinion.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), total

    async def get_by_id(
        self, opinion_id: UUID, company_id: UUID | str
    ) -> LiaOpinion | None:
        self._require_company_id(str(company_id))
        result = await self.db.execute(
            select(LiaOpinion).where(
                and_(
                    LiaOpinion.id == opinion_id,
                    LiaOpinion.company_id == company_id,
                )
            )
        )
        return result.scalar_one_or_none()

    # ── Version helpers ────────────────────────────────────────────────────

    async def get_max_version_for_vacancy(
        self,
        candidate_id: UUID,
        job_vacancy_id: UUID,
        opinion_type: str,
        company_id: UUID | str,
    ) -> int | None:
        self._require_company_id(str(company_id))
        result = await self.db.execute(
            select(func.max(LiaOpinion.version)).where(
                and_(
                    LiaOpinion.candidate_id == candidate_id,
                    LiaOpinion.job_vacancy_id == job_vacancy_id,
                    LiaOpinion.opinion_type == opinion_type,
                    LiaOpinion.company_id == company_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_max_version_general(
        self,
        candidate_id: UUID,
        company_id: UUID | str,
    ) -> int | None:
        self._require_company_id(str(company_id))
        result = await self.db.execute(
            select(func.max(LiaOpinion.version)).where(
                and_(
                    LiaOpinion.candidate_id == candidate_id,
                    LiaOpinion.opinion_type == "general",
                    LiaOpinion.company_id == company_id,
                )
            )
        )
        return result.scalar_one_or_none()

    # ── Write ──────────────────────────────────────────────────────────────

    async def mark_vacancy_opinions_non_current(
        self,
        candidate_id: UUID,
        job_vacancy_id: UUID,
        opinion_type: str,
        company_id: UUID | str,
    ) -> None:
        self._require_company_id(str(company_id))
        await self.db.execute(
            update(LiaOpinion)
            .where(
                and_(
                    LiaOpinion.candidate_id == candidate_id,
                    LiaOpinion.job_vacancy_id == job_vacancy_id,
                    LiaOpinion.opinion_type == opinion_type,
                    LiaOpinion.company_id == company_id,
                    LiaOpinion.is_current,
                )
            )
            .values(is_current=False)
        )

    async def mark_general_opinions_non_current(
        self,
        candidate_id: UUID,
        company_id: UUID | str,
    ) -> None:
        self._require_company_id(str(company_id))
        await self.db.execute(
            update(LiaOpinion)
            .where(
                and_(
                    LiaOpinion.candidate_id == candidate_id,
                    LiaOpinion.opinion_type == "general",
                    LiaOpinion.company_id == company_id,
                    LiaOpinion.is_current,
                )
            )
            .values(is_current=False)
        )

    async def create(self, opinion: LiaOpinion) -> LiaOpinion:
        self.db.add(opinion)
        await self.db.commit()
        await self.db.refresh(opinion)
        return opinion

    async def update(self, opinion: LiaOpinion) -> LiaOpinion:
        await self.db.commit()
        await self.db.refresh(opinion)
        return opinion


    # ── Phase 2.5 / P1-LiaRepo + P1-Clobber methods ──────────────────────

    # Source priority for field-clobber guard (P1-Clobber fix).
    # text_screening < full_interview — never downgrade authority fields.
    _SOURCE_PRIORITY: dict[str, int] = {
        "cv_analysis": 0,
        "text_screening": 1,
        "full_interview": 2,
    }

    async def get_latest_for_candidate_company(
        self,
        candidate_id,
        company_id: str | UUID,
    ) -> "LiaOpinion | None":
        """P1-LiaRepo: most recent LiaOpinion for (candidate, company).

        Used by _record_bigfive_hire to read ocean_traits without inline
        SQL in the service (ADR-001 compliance).
        """
        self._require_company_id(str(company_id))
        result = await self.db.execute(
            select(LiaOpinion)
            .where(
                and_(
                    LiaOpinion.candidate_id == candidate_id,
                    LiaOpinion.company_id == str(company_id),
                )
            )
            .order_by(desc(LiaOpinion.created_at))
            .limit(1)
        )
        return result.scalars().first()

    async def get_latest_for_candidate_vacancy(
        self,
        candidate_id,
        vacancy_id,
        company_id: str | UUID,
    ) -> "LiaOpinion | None":
        """P1-LiaRepo: most recent is_current LiaOpinion for (candidate,
        vacancy, company).

        Used by upsert_ocean_opinion and _persist_lia_opinion_with_ocean.
        """
        self._require_company_id(str(company_id))
        result = await self.db.execute(
            select(LiaOpinion)
            .where(
                and_(
                    LiaOpinion.candidate_id == candidate_id,
                    LiaOpinion.job_vacancy_id == vacancy_id,
                    LiaOpinion.company_id == str(company_id),
                    LiaOpinion.is_current.is_(True),
                )
            )
            .order_by(desc(LiaOpinion.created_at))
            .limit(1)
        )
        return result.scalars().first()

    async def upsert_ocean_opinion(
        self,
        candidate_id,
        vacancy_id,
        company_id: str | UUID,
        ocean_traits: dict,
        overall_wsi: float,
        recommendation: str,
        summary: "str | None",
    ) -> "LiaOpinion":
        """P1-LiaRepo + P1-Clobber: upsert LiaOpinion(opinion_type='wsi')
        with OCEAN snapshot in behavioral_analysis['ocean_traits'].

        Field-clobber guard: source/wsi_score/recommendation are only
        overwritten when the existing source has SAME or LOWER priority
        than 'text_screening'. behavioral_analysis['ocean_traits'] is
        ALWAYS updated (new measurement data, not an authority field).

        Priority: cv_analysis(0) < text_screening(1) < full_interview(2).
        A full_interview opinion is never downgraded to text_screening.
        """
        self._require_company_id(str(company_id))
        from datetime import datetime as _dt

        existing = await self.get_latest_for_candidate_vacancy(
            candidate_id=candidate_id,
            vacancy_id=vacancy_id,
            company_id=company_id,
        )

        behavioral_blob: dict = {}
        if existing is not None:
            behavioral_blob = dict(existing.behavioral_analysis or {})
        # ocean_traits always updated (new measurement data)
        behavioral_blob["ocean_traits"] = ocean_traits

        if existing is not None:
            # P1-Clobber guard: only overwrite authority fields if new
            # source is NOT lower priority than existing.
            new_priority = self._SOURCE_PRIORITY.get("text_screening", 1)
            existing_priority = self._SOURCE_PRIORITY.get(
                existing.source or "cv_analysis", 0
            )
            existing.behavioral_analysis = behavioral_blob
            if new_priority >= existing_priority:
                existing.wsi_score = float(overall_wsi)
                existing.recommendation = recommendation
                existing.source = "text_screening"
            existing.updated_at = _dt.utcnow()
            return existing
        else:
            # P1-IsCurrentCoord: ensure only one is_current=True row per
            # (candidate, vacancy, opinion_type='wsi'). Without this, each
            # writer (screening, interview, etc.) can stack duplicate True rows.
            from uuid import UUID as _UUID

            def _to_uuid(v):
                if isinstance(v, _UUID):
                    return v
                try:
                    return _UUID(str(v))
                except (ValueError, AttributeError):
                    return v

            await self.mark_vacancy_opinions_non_current(
                candidate_id=_to_uuid(candidate_id),
                job_vacancy_id=_to_uuid(vacancy_id),
                opinion_type="wsi",
                company_id=_to_uuid(company_id),
            )
            from app.models.lia_opinion import LiaOpinion as _LiaOpinion
            opinion = _LiaOpinion(
                candidate_id=candidate_id,
                job_vacancy_id=vacancy_id,
                company_id=str(company_id),
                opinion_type="wsi",
                source="text_screening",
                wsi_score=float(overall_wsi),
                recommendation=recommendation,
                behavioral_analysis=behavioral_blob,
                summary=summary,
                is_current=True,
                version=1,
                created_by="screening_completed",
            )
            self.db.add(opinion)
            return opinion


    # ── WSI screening — atomic version handling (race-safe) ────────────────

    async def get_company_id_for_vacancy(self, job_vacancy_id: str) -> str | None:
        """Resolve company_id from a job vacancy id (multi-tenancy scoping helper).

        Returns the canonical str(company_id) for downstream gates, or None
        when the vacancy does not exist. Caller MUST handle the None case —
        downstream writes that depend on company_id must abort fail-closed.
        """
        if not job_vacancy_id:
            return None
        result = await self.db.execute(
            text("SELECT company_id FROM job_vacancies WHERE id = :vid LIMIT 1"),
            {"vid": job_vacancy_id},
        )
        row = result.fetchone()
        if row is None or row.company_id is None:
            return None
        return str(row.company_id)

    async def create_wsi_opinion_with_atomic_version(
        self,
        *,
        candidate_id: str,
        job_vacancy_id: str | None,
        company_id: str,
        score: float,
        wsi_score: float,
        archetype: str,
        recommendation: str,
        summary: str,
        score_breakdown: dict,
        strengths: list,
        concerns: list,
        gaps: list,
        matched_skills: list,
        missing_skills: list,
        next_steps: list,
    ) -> str:
        """Create a new WSI LiaOpinion with atomic version assignment.

        Race-condition safe: uses a single ``INSERT ... SELECT MAX(version)+1``
        statement so two concurrent writers cannot pick the same next version.

        Steps (single transaction, caller is responsible for commit):
          1) Archive previous current WSI opinions for this (candidate, vacancy, company).
          2) Atomically INSERT a new row computing ``COALESCE(MAX(version),0)+1``
             from the same matching scope inside the same statement.

        Multi-tenancy invariant: ``company_id`` MUST be provided (validated
        fail-closed via ``_require_company_id``). It MUST come from the JWT
        (``Depends(require_company_id)``) or from an authoritative
        repo-side lookup (e.g. ``get_company_id_for_vacancy``) — never
        from the request payload.

        Returns:
          The opinion ``id`` (UUID string) of the row just inserted.

        Why atomic SQL CTE (not SELECT-then-INSERT):
          ``SELECT MAX(version)+1`` followed by a separate ``INSERT`` opens
          a race window where two concurrent transactions read the same
          MAX and produce duplicate versions. Even with SERIALIZABLE
          isolation we would have to handle retries; the single-statement
          form below is atomic at the row level and works at READ COMMITTED.
        """
        self._require_company_id(company_id)
        if not candidate_id:
            raise ValueError("candidate_id required")

        import json as _json
        import uuid as _uuid

        opinion_id = str(_uuid.uuid4())

        # Step 1 — archive previous current WSI opinions for this scope.
        # Scope mirrors the version-MAX scope used in step 2 so the new
        # row is the only is_current=True row when we commit.
        await self.db.execute(
            text(self._ARCHIVE_WSI_OPINIONS_SQL),
            {
                "candidate_id": candidate_id,
                "company_id": company_id,
                "job_vacancy_id": job_vacancy_id,
            },
        )

        # Step 2 — atomic insert with version computed inside the same statement.
        # COALESCE(MAX(version), 0) + 1 is evaluated by the same statement
        # that performs the INSERT, eliminating the read-then-write race.
        await self.db.execute(
            text(self._INSERT_WSI_OPINION_ATOMIC_SQL),
            {
                "id": opinion_id,
                "candidate_id": candidate_id,
                "job_vacancy_id": job_vacancy_id,
                "company_id": company_id,
                "score": score,
                "wsi_score": wsi_score,
                "archetype": archetype,
                "recommendation": recommendation,
                "summary": summary,
                "score_breakdown": _json.dumps(score_breakdown or {}),
                "strengths": _json.dumps(strengths or []),
                "concerns": _json.dumps(concerns or []),
                "gaps": _json.dumps(gaps or []),
                "matched_skills": _json.dumps(matched_skills or []),
                "missing_skills": _json.dumps(missing_skills or []),
                "next_steps": _json.dumps(next_steps or []),
            },
        )

        return opinion_id

    # Internal SQL strings kept at module-method scope to avoid shadowing
    # by any caller-local `text` shadowing.
    _ARCHIVE_WSI_OPINIONS_SQL: str = """
        UPDATE lia_opinions
        SET is_current = false
        WHERE candidate_id = :candidate_id
          AND opinion_type = 'wsi'
          AND company_id = :company_id
          AND is_current = true
          AND (
            (CAST(:job_vacancy_id AS uuid) IS NULL AND job_vacancy_id IS NULL)
            OR job_vacancy_id = CAST(:job_vacancy_id AS uuid)
          )
    """

    _INSERT_WSI_OPINION_ATOMIC_SQL: str = """
        INSERT INTO lia_opinions (
            id, candidate_id, job_vacancy_id, company_id, opinion_type, source,
            score, wsi_score, archetype, recommendation, summary, score_breakdown,
            strengths, concerns, gaps, matched_skills, missing_skills,
            next_steps, is_current, version, created_at, updated_at
        )
        SELECT
            :id,
            :candidate_id,
            CAST(:job_vacancy_id AS uuid),
            CAST(:company_id AS varchar),
            'wsi',
            'wsi_screening',
            :score,
            :wsi_score,
            :archetype,
            :recommendation,
            :summary,
            CAST(:score_breakdown AS jsonb),
            CAST(:strengths AS jsonb),
            CAST(:concerns AS jsonb),
            CAST(:gaps AS jsonb),
            CAST(:matched_skills AS jsonb),
            CAST(:missing_skills AS jsonb),
            CAST(:next_steps AS jsonb),
            true,
            COALESCE((
                SELECT MAX(version)
                FROM lia_opinions
                WHERE candidate_id = :candidate_id
                  AND opinion_type = 'wsi'
                  AND company_id = :company_id
                  AND (
                    (CAST(:job_vacancy_id AS uuid) IS NULL AND job_vacancy_id IS NULL)
                    OR job_vacancy_id = CAST(:job_vacancy_id AS uuid)
                  )
            ), 0) + 1,
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
    """

    async def create_parecer_opinion(
        self,
        *,
        candidate_id: str,
        job_vacancy_id: str | None,
        company_id: str,
        score: float | None,
        recommendation: str | None,
        summary: str | None,
        score_breakdown: dict,
        strengths: list,
        concerns: list,
        gaps: list,
        matched_skills: list,
        missing_skills: list,
        next_steps: list,
    ) -> str:
        """Cria um parecer (LiaOpinion opinion_type='general') com versao atomica.

        Espelha create_wsi_opinion_with_atomic_version: arquiva os pareceres
        correntes do escopo (candidato, vaga, empresa) e insere a nova versao
        computando COALESCE(MAX(version),0)+1 no MESMO statement (race-safe).
        score_breakdown carrega a qualification_matrix + secoes do parecer.

        Multi-tenancy: company_id DEVE vir do JWT (Depends(require_company_id)),
        nunca do payload — validado fail-closed via _require_company_id.
        """
        self._require_company_id(company_id)
        if not candidate_id:
            raise ValueError("candidate_id required")

        import json as _json
        import uuid as _uuid

        opinion_id = str(_uuid.uuid4())

        await self.db.execute(
            text(self._ARCHIVE_PARECER_OPINIONS_SQL),
            {
                "candidate_id": candidate_id,
                "company_id": company_id,
                "job_vacancy_id": job_vacancy_id,
            },
        )
        await self.db.execute(
            text(self._INSERT_PARECER_OPINION_ATOMIC_SQL),
            {
                "id": opinion_id,
                "candidate_id": candidate_id,
                "job_vacancy_id": job_vacancy_id,
                "company_id": company_id,
                "score": score,
                "recommendation": recommendation,
                "summary": summary,
                "score_breakdown": _json.dumps(score_breakdown or {}),
                "strengths": _json.dumps(strengths or []),
                "concerns": _json.dumps(concerns or []),
                "gaps": _json.dumps(gaps or []),
                "matched_skills": _json.dumps(matched_skills or []),
                "missing_skills": _json.dumps(missing_skills or []),
                "next_steps": _json.dumps(next_steps or []),
            },
        )
        return opinion_id

    _ARCHIVE_PARECER_OPINIONS_SQL: str = """
        UPDATE lia_opinions
        SET is_current = false
        WHERE candidate_id = :candidate_id
          AND opinion_type = 'general'
          AND company_id = :company_id
          AND is_current = true
          AND (
            (CAST(:job_vacancy_id AS uuid) IS NULL AND job_vacancy_id IS NULL)
            OR job_vacancy_id = CAST(:job_vacancy_id AS uuid)
          )
    """

    _INSERT_PARECER_OPINION_ATOMIC_SQL: str = """
        INSERT INTO lia_opinions (
            id, candidate_id, job_vacancy_id, company_id, opinion_type, source,
            score, recommendation, summary, score_breakdown,
            strengths, concerns, gaps, matched_skills, missing_skills,
            next_steps, is_current, version, created_at, updated_at
        )
        SELECT
            :id, :candidate_id, CAST(:job_vacancy_id AS uuid), CAST(:company_id AS varchar), 'general', 'cv_analysis',
            :score, :recommendation, :summary, CAST(:score_breakdown AS jsonb),
            CAST(:strengths AS jsonb), CAST(:concerns AS jsonb), CAST(:gaps AS jsonb),
            CAST(:matched_skills AS jsonb), CAST(:missing_skills AS jsonb), CAST(:next_steps AS jsonb),
            true,
            COALESCE((
                SELECT MAX(version) FROM lia_opinions
                WHERE candidate_id = :candidate_id
                  AND opinion_type = 'general'
                  AND company_id = :company_id
                  AND (
                    (CAST(:job_vacancy_id AS uuid) IS NULL AND job_vacancy_id IS NULL)
                    OR job_vacancy_id = CAST(:job_vacancy_id AS uuid)
                  )
            ), 0) + 1,
            CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
    """

    @staticmethod
    def _require_company_id(company_id: str | None) -> None:
        """Multi-tenancy fail-closed guard (ADR-001 canonical anatomy)."""
        if not company_id:
            raise ValueError(
                "Multi-tenancy invariant: company_id required for OpinionsRepository write"
            )

    async def soft_delete(self, opinion: LiaOpinion) -> None:
        opinion.is_current = False
        await self.db.commit()
