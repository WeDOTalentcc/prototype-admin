"""Repository for screening_question_sets versioning lifecycle.

Sprint 6 ADR-001 follow-up — extracts 15 raw SQL queries from:
- app/domains/cv_screening/services/screening_question_set_service.py (12 queries)
- app/domains/cv_screening/services/score_normalization_service.py (3 queries)

Cross-domain wsi_sessions queries (4 of the 15) live in voice/wsi_repository.py
since they touch a different table; that repo gets companion methods added in
the same Sprint 6 commit.

Multi-tenancy note: screening_question_sets has no `company_id` column directly;
tenant scope is enforced via `job_vacancy_id` FK to job_vacancies (which is RLS-
protected — see migration 121 T3 batch). Callers are responsible for ensuring
the `job_vacancy_id` belongs to the requesting tenant via the JobVacancy lookup
chain. The repo therefore does NOT call `_require_company_id` directly; this is
a documented exemption (data model dictates).
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.screening_question_set import ScreeningQuestionSet


class ScreeningQuestionSetRepository:
    """DB access for screening_question_sets (versioning lifecycle).

    Pattern: each public method takes plain Python args and returns
    ORM-mapped objects or simple dicts. SQL stays here; business logic
    (hashing, difficulty calculation, version diff) stays in the service.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # Helpers (private)
    # ------------------------------------------------------------------
    @staticmethod
    def _row_to_model(row) -> ScreeningQuestionSet:
        """Map full 14-column row → ScreeningQuestionSet ORM instance."""
        qs = ScreeningQuestionSet()
        qs.id = row[0]
        qs.job_vacancy_id = row[1]
        qs.version = row[2]
        qs.questions_hash = row[3]
        qs.questions_snapshot = row[4]
        qs.questions_count = row[5]
        qs.block_distribution = row[6]
        qs.extra_metadata = row[7]
        qs.source = row[8]
        qs.created_by = row[9]
        qs.is_active = row[10]
        qs.difficulty_coefficient = row[11]
        qs.created_at = row[12]
        qs.updated_at = row[13]
        return qs

    _FULL_COLS = (
        "id, job_vacancy_id, version, questions_hash, questions_snapshot, "
        "questions_count, block_distribution, metadata, source, created_by, "
        "is_active, difficulty_coefficient, created_at, updated_at"
    )

    # ------------------------------------------------------------------
    # Read methods
    # ------------------------------------------------------------------
    async def get_active(self, job_vacancy_id: str) -> ScreeningQuestionSet | None:
        """Return the currently-active question set for a job, or None."""
        result = await self.db.execute(
            text(f"""
                SELECT {self._FULL_COLS}
                FROM screening_question_sets
                WHERE job_vacancy_id = :job_vacancy_id AND is_active = TRUE
                LIMIT 1
            """),
            {"job_vacancy_id": job_vacancy_id},
        )
        row = result.fetchone()
        return self._row_to_model(row) if row else None

    async def get_by_version(
        self, job_vacancy_id: str, version: int,
    ) -> ScreeningQuestionSet | None:
        """Fetch a specific version of the question set."""
        result = await self.db.execute(
            text(f"""
                SELECT {self._FULL_COLS}
                FROM screening_question_sets
                WHERE job_vacancy_id = :job_vacancy_id AND version = :version
                LIMIT 1
            """),
            {"job_vacancy_id": job_vacancy_id, "version": version},
        )
        row = result.fetchone()
        return self._row_to_model(row) if row else None

    async def get_max_version(self, job_vacancy_id: str) -> int:
        """Return MAX(version) for a job, or 0 if none exist."""
        result = await self.db.execute(
            text("""
                SELECT MAX(version) FROM screening_question_sets
                WHERE job_vacancy_id = :job_vacancy_id
            """),
            {"job_vacancy_id": job_vacancy_id},
        )
        row = result.fetchone()
        return (row[0] or 0) if row else 0

    async def get_active_version_number(self, job_vacancy_id: str) -> int | None:
        """Return just the version number of the active set, or None.

        Cheaper than `get_active()` when only the version is needed
        (used by check_version_consistency).
        """
        result = await self.db.execute(
            text("""
                SELECT version FROM screening_question_sets
                WHERE job_vacancy_id = :job_vacancy_id AND is_active = TRUE
                LIMIT 1
            """),
            {"job_vacancy_id": job_vacancy_id},
        )
        row = result.fetchone()
        return row[0] if row else None

    async def list_versions_summary(self, job_vacancy_id: str) -> list[dict[str, Any]]:
        """Lightweight summary list (id/version/source/count/active/created)."""
        result = await self.db.execute(
            text("""
                SELECT id, version, source, questions_count, is_active, created_by, created_at
                FROM screening_question_sets
                WHERE job_vacancy_id = :job_vacancy_id
                ORDER BY version DESC
            """),
            {"job_vacancy_id": job_vacancy_id},
        )
        return [
            {
                "id": str(row[0]),
                "version": row[1],
                "source": row[2],
                "questions_count": row[3],
                "is_active": row[4],
                "created_by": row[5],
                "created_at": row[6].isoformat() if row[6] else None,
            }
            for row in result.fetchall()
        ]

    async def get_version_coefficients(
        self, job_vacancy_id: str,
    ) -> dict[int | None, float | None]:
        """Map of {version → difficulty_coefficient} for normalization."""
        result = await self.db.execute(
            text("""
                SELECT version, difficulty_coefficient
                FROM screening_question_sets
                WHERE job_vacancy_id = :job_vacancy_id
                ORDER BY version
            """),
            {"job_vacancy_id": job_vacancy_id},
        )
        return {row[0]: row[1] for row in result.fetchall()}

    async def get_versions_with_metadata(
        self, job_vacancy_id: str,
    ) -> list[tuple]:
        """List of (version, coef, count, source, is_active) tuples for context display."""
        result = await self.db.execute(
            text("""
                SELECT version, difficulty_coefficient, questions_count, source, is_active
                FROM screening_question_sets
                WHERE job_vacancy_id = :job_vacancy_id
                ORDER BY version DESC
            """),
            {"job_vacancy_id": job_vacancy_id},
        )
        return list(result.fetchall())

    # ------------------------------------------------------------------
    # Write methods
    # ------------------------------------------------------------------
    async def deactivate_active(self, job_vacancy_id: str) -> None:
        """Mark all currently-active sets for a job as inactive (pre-insert)."""
        await self.db.execute(
            text("""
                UPDATE screening_question_sets
                SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
                WHERE job_vacancy_id = :job_vacancy_id AND is_active = TRUE
            """),
            {"job_vacancy_id": job_vacancy_id},
        )

    async def insert_set(
        self,
        *,
        job_vacancy_id: str,
        version: int,
        questions_hash: str,
        questions: list[dict[str, Any]],
        questions_count: int,
        block_distribution: dict | None,
        metadata: dict | None,
        source: str,
        created_by: str | None,
        difficulty_coefficient: float,
        now: datetime | None = None,
    ) -> str:
        """Insert a new version row; returns the generated UUID string."""
        new_id = str(uuid.uuid4())
        ts = now or datetime.utcnow()
        await self.db.execute(
            # RLS-EXEMPT: screening_question_sets — transitive isolation (migration 118)
            text("""
                INSERT INTO screening_question_sets (
                    id, job_vacancy_id, version, questions_hash, questions_snapshot,
                    questions_count, block_distribution, metadata, source, created_by,
                    is_active, difficulty_coefficient, created_at, updated_at
                ) VALUES (
                    :id, :job_vacancy_id, :version, :questions_hash,
                    :questions_snapshot::jsonb,
                    :questions_count, :block_distribution::jsonb, :metadata::jsonb,
                    :source, :created_by,
                    TRUE, :difficulty_coefficient, :created_at, :updated_at
                )
            """),
            {
                "id": new_id,
                "job_vacancy_id": job_vacancy_id,
                "version": version,
                "questions_hash": questions_hash,
                "questions_snapshot": json.dumps(questions),
                "questions_count": questions_count,
                "block_distribution": json.dumps(block_distribution) if block_distribution else None,
                "metadata": json.dumps(metadata) if metadata else None,
                "source": source,
                "created_by": created_by,
                "difficulty_coefficient": difficulty_coefficient,
                "created_at": ts,
                "updated_at": ts,
            },
        )
        return new_id

    async def update_job_vacancy_screening_cache(
        self, job_vacancy_id: str, questions: list[dict[str, Any]],
    ) -> None:
        """Best-effort sync of `job_vacancies.screening_questions` JSONB cache.

        This writes to a different table (job_vacancies) but is kept here
        because it's a side-effect of save_question_set; callers wrap in
        try/except (fail-open).
        """
        await self.db.execute(
            text("""
                UPDATE job_vacancies
                SET screening_questions = :screening_questions::jsonb
                WHERE id = :job_vacancy_id
            """),
            {
                "job_vacancy_id": job_vacancy_id,
                "screening_questions": json.dumps(questions),
            },
        )
