"""Screening Question Set service — versioning, hashing, difficulty calc.

Sprint 6 ADR-001 cleanup: all SQL extracted to ScreeningQuestionSetRepository
(cv_screening/repositories/) and WsiRepository (voice/repositories/).
This service now contains ONLY business logic.
"""
import hashlib
import json
import logging
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.screening_question_set import ScreeningQuestionSet
from app.domains.cv_screening.repositories.screening_question_set_repository import (
    ScreeningQuestionSetRepository,
)
from app.domains.voice.repositories.wsi_repository import WsiRepository
from app.shared.policy_middleware import get_policy_for_company, resolve_policy_value

logger = logging.getLogger(__name__)


class ScreeningQuestionSetService:

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    async def inject_policy_defaults(
        self,
        db: AsyncSession,
        company_id: str,
        questions: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        try:
            policy = await get_policy_for_company(company_id, db)
            default_questions = resolve_policy_value(
                policy, "screening_rules", "default_screening_questions",
                override=None, default=[],
            )
        except Exception as e:
            logger.warning(f"Failed to load screening policy defaults for {company_id}: {e}")
            return questions

        if not default_questions:
            return questions

        existing_texts = {q.get("text", q.get("question", "")).strip().lower() for q in questions}

        merged = list(questions)
        for idx, q_text in enumerate(default_questions):
            if not isinstance(q_text, str) or not q_text.strip():
                continue
            if q_text.strip().lower() not in existing_texts:
                merged.append({
                    "id": f"company-default-{idx + 1}",
                    "text": q_text,
                    "category": "company",
                    "block_id": 2,
                    "source": "company_policy",
                    "question_type": "open",
                    "is_eliminatory": False,
                    "weight": 0.7,
                    "bloom_level": 2,
                    "dreyfus_stage": 2,
                })

        return merged

    async def save_question_set(
        self,
        db: AsyncSession,
        job_vacancy_id: str,
        questions: list[dict[str, Any]],
        source: str,
        created_by: str | None = None,
        block_distribution: dict | None = None,
        metadata: dict | None = None,
        company_id: str | None = None,
    ) -> ScreeningQuestionSet:
        repo = ScreeningQuestionSetRepository(db)
        questions_hash = self._calculate_questions_hash(questions)

        existing = await repo.get_active(job_vacancy_id)

        if company_id and existing is None:
            questions = await self.inject_policy_defaults(db, company_id, questions)
            questions_hash = self._calculate_questions_hash(questions)

        if existing is not None and existing.questions_hash == questions_hash:
            logger.info(
                f"Question set hash unchanged for job {job_vacancy_id}, "
                f"returning existing version {existing.version}"
            )
            return existing

        next_version = (await repo.get_max_version(job_vacancy_id)) + 1
        await repo.deactivate_active(job_vacancy_id)

        difficulty_coefficient = self._calculate_difficulty_coefficient(questions)
        now = datetime.utcnow()
        new_id = await repo.insert_set(
            job_vacancy_id=job_vacancy_id,
            version=next_version,
            questions_hash=questions_hash,
            questions=questions,
            questions_count=len(questions),
            block_distribution=block_distribution,
            metadata=metadata,
            source=source,
            created_by=created_by,
            difficulty_coefficient=difficulty_coefficient,
            now=now,
        )

        try:
            await repo.update_job_vacancy_screening_cache(job_vacancy_id, questions)
        except Exception as e:
            logger.warning(
                f"Failed to update JobVacancy screening_questions cache "
                f"for {job_vacancy_id}: {e}"
            )

        await db.commit()

        logger.info(
            f"Saved question set v{next_version} for job {job_vacancy_id} "
            f"(source={source}, count={len(questions)})"
        )

        # Build a fresh ORM instance to return (avoid extra SELECT after commit)
        import uuid
        qs = ScreeningQuestionSet()
        qs.id = uuid.UUID(new_id)
        qs.job_vacancy_id = job_vacancy_id
        qs.version = next_version
        qs.questions_hash = questions_hash
        qs.questions_snapshot = questions
        qs.questions_count = len(questions)
        qs.block_distribution = block_distribution
        qs.extra_metadata = metadata
        qs.source = source
        qs.created_by = created_by
        qs.is_active = True
        qs.difficulty_coefficient = difficulty_coefficient
        qs.created_at = now
        qs.updated_at = now
        return qs

    async def get_active_version(
        self, db: AsyncSession, job_vacancy_id: str,
    ) -> ScreeningQuestionSet | None:
        return await ScreeningQuestionSetRepository(db).get_active(job_vacancy_id)

    async def get_by_version(
        self, db: AsyncSession, job_vacancy_id: str, version: int,
    ) -> ScreeningQuestionSet | None:
        return await ScreeningQuestionSetRepository(db).get_by_version(
            job_vacancy_id, version,
        )

    async def list_versions(
        self, db: AsyncSession, job_vacancy_id: str,
    ) -> list[dict[str, Any]]:
        return await ScreeningQuestionSetRepository(db).list_versions_summary(
            job_vacancy_id,
        )

    async def check_version_consistency(
        self, db: AsyncSession, job_vacancy_id: str,
    ) -> dict[str, Any]:
        qs_repo = ScreeningQuestionSetRepository(db)
        wsi_repo = WsiRepository(db)

        current_version = await qs_repo.get_active_version_number(job_vacancy_id)
        total_screened = await wsi_repo.count_completed_sessions(job_vacancy_id)

        if current_version is None:
            return {
                "current_version": None,
                "total_screened": total_screened,
                "screened_with_current": 0,
                "screened_with_older": 0,
                "older_versions_used": [],
                "has_inconsistency": False,
            }

        screened_with_current = await wsi_repo.count_completed_sessions_at_version(
            job_vacancy_id, current_version,
        )
        older_pairs = await wsi_repo.get_older_versions_session_counts(
            job_vacancy_id, current_version,
        )

        older_versions_used = [
            {"version": v, "count": c} for v, c in older_pairs
        ]
        screened_with_older = sum(item["count"] for item in older_versions_used)

        return {
            "current_version": current_version,
            "total_screened": total_screened,
            "screened_with_current": screened_with_current,
            "screened_with_older": screened_with_older,
            "older_versions_used": older_versions_used,
            "has_inconsistency": screened_with_older > 0,
        }

    def _calculate_questions_hash(self, questions: list[dict[str, Any]]) -> str:
        def sort_key(q: dict[str, Any]) -> str:
            return q.get("text", q.get("question", ""))

        sorted_questions = sorted(questions, key=sort_key)
        serialized = json.dumps(sorted_questions, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def _calculate_difficulty_coefficient(self, questions: list[dict[str, Any]]) -> float:
        if not questions:
            return 0.0

        bloom_values = []
        dreyfus_values = []

        for q in questions:
            bloom = q.get("bloom_level")
            if bloom is not None:
                bloom_values.append(float(bloom))
            dreyfus = q.get("dreyfus_stage")
            if dreyfus is not None:
                dreyfus_values.append(float(dreyfus))

        avg_bloom = sum(bloom_values) / len(bloom_values) if bloom_values else 3.0
        avg_dreyfus = sum(dreyfus_values) / len(dreyfus_values) if dreyfus_values else 3.0

        normalized_bloom = (avg_bloom - 1) / 5.0
        normalized_dreyfus = (avg_dreyfus - 1) / 4.0

        coefficient = normalized_bloom * 0.6 + normalized_dreyfus * 0.4

        return round(max(0.0, min(1.0, coefficient)), 4)


screening_question_set_service = ScreeningQuestionSetService()


# FastAPI dependency injection factory
def get_screening_question_set_service() -> "ScreeningQuestionSetService":
    return screening_question_set_service
