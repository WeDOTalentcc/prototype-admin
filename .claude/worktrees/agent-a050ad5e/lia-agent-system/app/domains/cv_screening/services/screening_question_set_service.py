import hashlib
import json
import logging
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.models.screening_question_set import ScreeningQuestionSet
from app.shared.policy_middleware import get_policy_for_company, resolve_policy_value

logger = logging.getLogger(__name__)


class ScreeningQuestionSetService:

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    async def inject_policy_defaults(
        self,
        db: AsyncSession,
        company_id: str,
        questions: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
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
        questions: List[Dict[str, Any]],
        source: str,
        created_by: Optional[str] = None,
        block_distribution: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
        company_id: Optional[str] = None,
    ) -> ScreeningQuestionSet:
        questions_hash = self._calculate_questions_hash(questions)

        result = await db.execute(text("""
            SELECT id, job_vacancy_id, version, questions_hash, questions_snapshot,
                   questions_count, block_distribution, metadata, source, created_by,
                   is_active, difficulty_coefficient, created_at, updated_at
            FROM screening_question_sets
            WHERE job_vacancy_id = :job_vacancy_id AND is_active = TRUE
            LIMIT 1
        """), {"job_vacancy_id": job_vacancy_id})
        existing_row = result.fetchone()

        if company_id and not existing_row:
            questions = await self.inject_policy_defaults(db, company_id, questions)
            questions_hash = self._calculate_questions_hash(questions)

        if existing_row and existing_row[3] == questions_hash:
            logger.info(f"Question set hash unchanged for job {job_vacancy_id}, returning existing version {existing_row[2]}")
            qs = ScreeningQuestionSet()
            qs.id = existing_row[0]
            qs.job_vacancy_id = existing_row[1]
            qs.version = existing_row[2]
            qs.questions_hash = existing_row[3]
            qs.questions_snapshot = existing_row[4]
            qs.questions_count = existing_row[5]
            qs.block_distribution = existing_row[6]
            qs.extra_metadata = existing_row[7]
            qs.source = existing_row[8]
            qs.created_by = existing_row[9]
            qs.is_active = existing_row[10]
            qs.difficulty_coefficient = existing_row[11]
            qs.created_at = existing_row[12]
            qs.updated_at = existing_row[13]
            return qs

        version_result = await db.execute(text("""
            SELECT MAX(version) FROM screening_question_sets
            WHERE job_vacancy_id = :job_vacancy_id
        """), {"job_vacancy_id": job_vacancy_id})
        max_version_row = version_result.fetchone()
        next_version = (max_version_row[0] or 0) + 1

        await db.execute(text("""
            UPDATE screening_question_sets
            SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
            WHERE job_vacancy_id = :job_vacancy_id AND is_active = TRUE
        """), {"job_vacancy_id": job_vacancy_id})

        difficulty_coefficient = self._calculate_difficulty_coefficient(questions)
        new_id = str(uuid.uuid4())
        now = datetime.utcnow()

        await db.execute(text("""
            INSERT INTO screening_question_sets (
                id, job_vacancy_id, version, questions_hash, questions_snapshot,
                questions_count, block_distribution, metadata, source, created_by,
                is_active, difficulty_coefficient, created_at, updated_at
            )
            VALUES (
                :id, :job_vacancy_id, :version, :questions_hash, :questions_snapshot::jsonb,
                :questions_count, :block_distribution::jsonb, :metadata::jsonb, :source, :created_by,
                TRUE, :difficulty_coefficient, :created_at, :updated_at
            )
        """), {
            "id": new_id,
            "job_vacancy_id": job_vacancy_id,
            "version": next_version,
            "questions_hash": questions_hash,
            "questions_snapshot": json.dumps(questions),
            "questions_count": len(questions),
            "block_distribution": json.dumps(block_distribution) if block_distribution else None,
            "metadata": json.dumps(metadata) if metadata else None,
            "source": source,
            "created_by": created_by,
            "difficulty_coefficient": difficulty_coefficient,
            "created_at": now,
            "updated_at": now,
        })

        try:
            await db.execute(text("""
                UPDATE job_vacancies
                SET screening_questions = :screening_questions::jsonb
                WHERE id = :job_vacancy_id
            """), {
                "job_vacancy_id": job_vacancy_id,
                "screening_questions": json.dumps(questions),
            })
        except Exception as e:
            logger.warning(f"Failed to update JobVacancy screening_questions cache for {job_vacancy_id}: {e}")

        await db.commit()

        logger.info(f"Saved question set v{next_version} for job {job_vacancy_id} (source={source}, count={len(questions)})")

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
        self, db: AsyncSession, job_vacancy_id: str
    ) -> Optional[ScreeningQuestionSet]:
        result = await db.execute(text("""
            SELECT id, job_vacancy_id, version, questions_hash, questions_snapshot,
                   questions_count, block_distribution, metadata, source, created_by,
                   is_active, difficulty_coefficient, created_at, updated_at
            FROM screening_question_sets
            WHERE job_vacancy_id = :job_vacancy_id AND is_active = TRUE
            LIMIT 1
        """), {"job_vacancy_id": job_vacancy_id})
        row = result.fetchone()

        if not row:
            return None

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

    async def get_by_version(
        self, db: AsyncSession, job_vacancy_id: str, version: int
    ) -> Optional[ScreeningQuestionSet]:
        result = await db.execute(text("""
            SELECT id, job_vacancy_id, version, questions_hash, questions_snapshot,
                   questions_count, block_distribution, metadata, source, created_by,
                   is_active, difficulty_coefficient, created_at, updated_at
            FROM screening_question_sets
            WHERE job_vacancy_id = :job_vacancy_id AND version = :version
            LIMIT 1
        """), {"job_vacancy_id": job_vacancy_id, "version": version})
        row = result.fetchone()

        if not row:
            return None

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

    async def list_versions(
        self, db: AsyncSession, job_vacancy_id: str
    ) -> List[Dict[str, Any]]:
        result = await db.execute(text("""
            SELECT id, version, source, questions_count, is_active, created_by, created_at
            FROM screening_question_sets
            WHERE job_vacancy_id = :job_vacancy_id
            ORDER BY version DESC
        """), {"job_vacancy_id": job_vacancy_id})
        rows = result.fetchall()

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
            for row in rows
        ]

    async def check_version_consistency(
        self, db: AsyncSession, job_vacancy_id: str
    ) -> Dict[str, Any]:
        active_result = await db.execute(text("""
            SELECT version FROM screening_question_sets
            WHERE job_vacancy_id = :job_vacancy_id AND is_active = TRUE
            LIMIT 1
        """), {"job_vacancy_id": job_vacancy_id})
        active_row = active_result.fetchone()
        current_version = active_row[0] if active_row else None

        total_result = await db.execute(text("""
            SELECT COUNT(*) FROM wsi_sessions
            WHERE job_vacancy_id = :job_vacancy_id AND status = 'completed'
        """), {"job_vacancy_id": job_vacancy_id})
        total_screened = total_result.fetchone()[0]

        if current_version is None:
            return {
                "current_version": None,
                "total_screened": total_screened,
                "screened_with_current": 0,
                "screened_with_older": 0,
                "older_versions_used": [],
                "has_inconsistency": False,
            }

        current_count_result = await db.execute(text("""
            SELECT COUNT(*) FROM wsi_sessions
            WHERE job_vacancy_id = :job_vacancy_id
              AND status = 'completed'
              AND question_set_version = :current_version
        """), {"job_vacancy_id": job_vacancy_id, "current_version": current_version})
        screened_with_current = current_count_result.fetchone()[0]

        older_result = await db.execute(text("""
            SELECT question_set_version, COUNT(*) as session_count
            FROM wsi_sessions
            WHERE job_vacancy_id = :job_vacancy_id
              AND status = 'completed'
              AND question_set_version IS NOT NULL
              AND question_set_version < :current_version
            GROUP BY question_set_version
            ORDER BY question_set_version DESC
        """), {"job_vacancy_id": job_vacancy_id, "current_version": current_version})
        older_rows = older_result.fetchall()

        older_versions_used = [
            {"version": row[0], "count": row[1]}
            for row in older_rows
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

    def _calculate_questions_hash(self, questions: List[Dict[str, Any]]) -> str:
        def sort_key(q: Dict[str, Any]) -> str:
            return q.get("text", q.get("question", ""))

        sorted_questions = sorted(questions, key=sort_key)
        serialized = json.dumps(sorted_questions, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def _calculate_difficulty_coefficient(self, questions: List[Dict[str, Any]]) -> float:
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
