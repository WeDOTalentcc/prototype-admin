"""
LearningConfirmationService — Skill and responsibility confirmation/query operations.

Extracted from LearningHubService (Sprint 5).
Handles: record_skill_confirmation, record_skill_rejection,
         record_responsibility_confirmation, record_agent_feedback,
         get_company_skills, get_company_responsibilities,
         get_skills_without_duplicates, get_learning_context,
         update_pattern, _calculate_confidence, and pattern helpers.

ADR-001 refactor: SQL/select() moved to CompanyLearningRepository.
"""
import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.company_learning import (
    AgentFeedback,
    CompanyPattern,
    CompanyResponsibility,
    CompanySkill,
    LearningSource,
)

from app.domains.analytics.repositories.company_learning_repository import (
    CompanyLearningRepository,
)

logger = logging.getLogger(__name__)

PROMOTION_THRESHOLD = 3
PATTERN_CONFIDENCE_THRESHOLDS = {"high": 10, "medium": 5, "low": 1}


@dataclass
class ConfirmationResult:
    success: bool
    item_id: str | None
    is_new: bool
    times_confirmed: int
    is_promoted: bool
    message: str


@dataclass
class LearningContext:
    company_skills: list[dict[str, Any]]
    company_responsibilities: list[dict[str, Any]]
    patterns: dict[str, Any]
    success_rate: dict[str, float]


def _calculate_confidence(sample_size: int) -> str:
    if sample_size >= PATTERN_CONFIDENCE_THRESHOLDS["high"]:
        return "high"
    if sample_size >= PATTERN_CONFIDENCE_THRESHOLDS["medium"]:
        return "medium"
    return "low"


class LearningConfirmationService:
    """Handles confirmation/rejection of skills, responsibilities, and agent feedback."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)

    # ------------------------------------------------------------------ #
    # Skills                                                               #
    # ------------------------------------------------------------------ #

    async def record_skill_confirmation(
        self,
        db: AsyncSession,
        company_id: str,
        skill_name: str,
        skill_type: str = "technical",
        role: str | None = None,
        seniority: str | None = None,
        source: str = LearningSource.WIZARD_CONFIRMED.value,
        created_by: str | None = None,
    ) -> ConfirmationResult:
        try:
            repo = CompanyLearningRepository(db)
            existing = await repo.find_skill_by_normalized_name(company_id, skill_name)

            if existing:
                existing.times_confirmed += 1
                existing.last_used_at = datetime.utcnow()

                if role and role not in (existing.roles_associated or []):
                    roles = existing.roles_associated or []
                    roles.append(role)
                    existing.roles_associated = roles

                if seniority and seniority not in (existing.seniority_levels or []):
                    levels = existing.seniority_levels or []
                    levels.append(seniority)
                    existing.seniority_levels = levels

                threshold = existing.promotion_threshold or PROMOTION_THRESHOLD
                if existing.times_confirmed >= threshold and not existing.is_promoted:
                    existing.is_promoted = True
                    existing.confidence_score = min(
                        1.0, (existing.confidence_score or 0.5) + 0.2
                    )

                await db.commit()
                return ConfirmationResult(
                    success=True,
                    item_id=str(existing.id),
                    is_new=False,
                    times_confirmed=existing.times_confirmed,
                    is_promoted=existing.is_promoted,
                    message=f"Skill '{skill_name}' confirmada ({existing.times_confirmed}x)",
                )
            else:
                new_skill = CompanySkill(
                    company_id=company_id,
                    skill_name=skill_name,
                    skill_type=skill_type,
                    times_confirmed=1,
                    source=source,
                    roles_associated=[role] if role else [],
                    seniority_levels=[seniority] if seniority else [],
                    created_by=created_by,
                    last_used_at=datetime.utcnow(),
                )
                db.add(new_skill)
                await db.commit()
                await db.refresh(new_skill)
                return ConfirmationResult(
                    success=True,
                    item_id=str(new_skill.id),
                    is_new=True,
                    times_confirmed=1,
                    is_promoted=False,
                    message=f"Nova skill '{skill_name}' registrada",
                )

        except Exception as exc:
            self.logger.error(f"Error recording skill confirmation: {exc}")
            await db.rollback()
            return ConfirmationResult(
                success=False,
                item_id=None,
                is_new=False,
                times_confirmed=0,
                is_promoted=False,
                message=f"Erro ao registrar skill: {exc}",
            )

    async def record_skill_rejection(
        self, db: AsyncSession, company_id: str, skill_name: str
    ) -> bool:
        try:
            repo = CompanyLearningRepository(db)
            existing = await repo.find_skill_by_normalized_name(company_id, skill_name)
            if existing:
                existing.times_rejected += 1
                if existing.times_rejected > existing.times_confirmed * 2:
                    existing.confidence_score = max(
                        0.1, existing.confidence_score - 0.1
                    )
                await db.commit()
            return True
        except Exception as exc:
            try:
                await db.rollback()
            except Exception:
                pass
            self.logger.error(f"Error recording skill rejection: {exc}")
            return False

    async def get_company_skills(
        self,
        db: AsyncSession,
        company_id: str,
        role: str | None = None,
        seniority: str | None = None,
        only_promoted: bool = False,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        try:
            repo = CompanyLearningRepository(db)
            skills = await repo.list_skills_for_company(
                company_id=company_id,
                only_promoted=only_promoted,
                limit=limit,
            )

            skill_list = []
            for s in skills:
                if role and s.roles_associated and role.lower() not in [
                    r.lower() for r in s.roles_associated
                ]:
                    continue
                skill_list.append(
                    {
                        "name": s.skill_name,
                        "type": s.skill_type,
                        "category": s.category,
                        "times_confirmed": s.times_confirmed,
                        "is_promoted": s.is_promoted,
                        "confidence": s.confidence_score,
                        "source": "company_learned",
                    }
                )
            return skill_list[:limit]
        except Exception as exc:
            self.logger.error(f"Error getting company skills: {exc}")
            return []

    async def get_skills_without_duplicates(
        self,
        db: AsyncSession,
        company_id: str,
        role: str | None = None,
        exclude_already_selected: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        try:
            repo = CompanyLearningRepository(db)
            skills = await repo.list_skills_with_role_filter(
                company_id=company_id, role=role
            )

            exclude_set = {s.lower() for s in (exclude_already_selected or [])}
            seen: set = set()
            unique = []
            for skill in skills:
                name_lower = skill.skill_name.lower()
                if name_lower not in seen and name_lower not in exclude_set:
                    seen.add(name_lower)
                    unique.append(
                        {
                            "id": str(skill.id),
                            "name": skill.skill_name,
                            "type": skill.skill_type,
                            "times_confirmed": skill.times_confirmed,
                            "is_promoted": skill.is_promoted,
                            "confidence": skill.confidence_score,
                        }
                    )
            return unique
        except Exception as exc:
            self.logger.error(f"Error getting skills without duplicates: {exc}")
            return []

    # ------------------------------------------------------------------ #
    # Responsibilities                                                     #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _hash_description(description: str) -> str:
        normalized = description.strip().lower()[:500]
        return hashlib.sha256(normalized.encode()).hexdigest()[:32]

    async def record_responsibility_confirmation(
        self,
        db: AsyncSession,
        company_id: str,
        description: str,
        category: str | None = None,
        role: str | None = None,
        seniority: str | None = None,
        source: str = LearningSource.WIZARD_CONFIRMED.value,
        created_by: str | None = None,
    ) -> ConfirmationResult:
        try:
            desc_hash = self._hash_description(description)
            repo = CompanyLearningRepository(db)
            existing = await repo.find_responsibility_by_hash(company_id, desc_hash)

            if existing:
                existing.times_confirmed += 1
                existing.last_used_at = datetime.utcnow()
                if role and role not in (existing.roles_associated or []):
                    existing.roles_associated = (existing.roles_associated or []) + [role]
                threshold = existing.promotion_threshold or PROMOTION_THRESHOLD
                if existing.times_confirmed >= threshold and not existing.is_promoted:
                    existing.is_promoted = True
                await db.commit()
                return ConfirmationResult(
                    success=True,
                    item_id=str(existing.id),
                    is_new=False,
                    times_confirmed=existing.times_confirmed,
                    is_promoted=existing.is_promoted,
                    message=f"Responsabilidade confirmada ({existing.times_confirmed}x)",
                )
            else:
                new_resp = CompanyResponsibility(
                    company_id=company_id,
                    description=description,
                    description_hash=desc_hash,
                    category=category,
                    times_confirmed=1,
                    source=source,
                    roles_associated=[role] if role else [],
                    created_by=created_by,
                    last_used_at=datetime.utcnow(),
                )
                db.add(new_resp)
                await db.commit()
                await db.refresh(new_resp)
                return ConfirmationResult(
                    success=True,
                    item_id=str(new_resp.id),
                    is_new=True,
                    times_confirmed=1,
                    is_promoted=False,
                    message="Nova responsabilidade registrada",
                )
        except Exception as exc:
            self.logger.error(f"Error recording responsibility confirmation: {exc}")
            await db.rollback()
            return ConfirmationResult(
                success=False,
                item_id=None,
                is_new=False,
                times_confirmed=0,
                is_promoted=False,
                message=f"Erro ao registrar responsabilidade: {exc}",
            )

    async def get_company_responsibilities(
        self,
        db: AsyncSession,
        company_id: str,
        role: str | None = None,
        only_promoted: bool = False,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        try:
            repo = CompanyLearningRepository(db)
            responsibilities = await repo.list_responsibilities_for_company(
                company_id=company_id, only_promoted=only_promoted, limit=limit
            )

            resp_list = []
            for r in responsibilities:
                if role and r.roles_associated and role.lower() not in [
                    rl.lower() for rl in r.roles_associated
                ]:
                    continue
                resp_list.append(
                    {
                        "description": r.description,
                        "category": r.category,
                        "times_confirmed": r.times_confirmed,
                        "is_promoted": r.is_promoted,
                        "confidence": r.confidence_score,
                        "source": "company_learned",
                    }
                )
            return resp_list[:limit]
        except Exception as exc:
            self.logger.error(f"Error getting company responsibilities: {exc}")
            return []

    # ------------------------------------------------------------------ #
    # Agent feedback                                                       #
    # ------------------------------------------------------------------ #

    async def record_agent_feedback(
        self,
        db: AsyncSession,
        company_id: str,
        agent_name: str,
        action_type: str,
        accepted: bool,
        suggested_value: Any = None,
        actual_value: Any = None,
        job_id: str | None = None,
        candidate_id: str | None = None,
        context: dict | None = None,
        feedback_reason: str | None = None,
        created_by: str | None = None,
    ) -> bool:
        try:
            from uuid import UUID

            feedback = AgentFeedback(
                company_id=company_id,
                job_id=UUID(job_id) if job_id else None,
                candidate_id=UUID(candidate_id) if candidate_id else None,
                agent_name=agent_name,
                action_type=action_type,
                suggested_value=suggested_value,
                actual_value=actual_value,
                accepted=accepted,
                context=context,
                feedback_reason=feedback_reason,
                created_by=created_by,
            )
            db.add(feedback)
            await db.commit()
            self.logger.info(
                f"Agent feedback recorded: {agent_name}/{action_type} "
                f"accepted={accepted} company={company_id}"
            )
            return True
        except Exception as exc:
            self.logger.error(f"Error recording agent feedback: {exc}")
            await db.rollback()
            return False

    # ------------------------------------------------------------------ #
    # Patterns and context                                                 #
    # ------------------------------------------------------------------ #

    async def update_pattern(
        self,
        db: AsyncSession,
        company_id: str,
        pattern_type: str,
        pattern_key: str,
        pattern_value: Any,
        sample_size: int = 1,
    ) -> bool:
        try:
            repo = CompanyLearningRepository(db)
            existing = await repo.find_pattern(company_id, pattern_type, pattern_key)

            if existing:
                existing.pattern_value = pattern_value
                existing.sample_size = sample_size
                existing.confidence = _calculate_confidence(sample_size)
                existing.last_calculated_at = datetime.utcnow()
            else:
                db.add(
                    CompanyPattern(
                        company_id=company_id,
                        pattern_type=pattern_type,
                        pattern_key=pattern_key,
                        pattern_value=pattern_value,
                        sample_size=sample_size,
                        confidence=_calculate_confidence(sample_size),
                    )
                )
            await db.commit()
            return True
        except Exception as exc:
            self.logger.error(f"Error updating pattern: {exc}")
            await db.rollback()
            return False

    async def _get_company_patterns(
        self, db: AsyncSession, company_id: str
    ) -> dict[str, Any]:
        try:
            repo = CompanyLearningRepository(db)
            patterns = await repo.list_patterns_for_company(company_id)
            return {
                f"{p.pattern_type}_{p.pattern_key}": {
                    "value": p.pattern_value,
                    "confidence": p.confidence,
                    "sample_size": p.sample_size,
                }
                for p in patterns
            }
        except Exception:
            return {}

    async def _get_success_rates(
        self, db: AsyncSession, company_id: str
    ) -> dict[str, float]:
        try:
            repo = CompanyLearningRepository(db)
            outcomes = await repo.get_outcome_counts_grouped(company_id)
            total = sum(o.count for o in outcomes)
            if total == 0:
                return {"fill_rate": 0.0, "cancel_rate": 0.0}
            return {
                f"{o.outcome.value if hasattr(o.outcome, 'value') else o.outcome}_rate": o.count / total
                for o in outcomes
            }
        except Exception:
            return {}

    async def get_learning_context(
        self,
        db: AsyncSession,
        company_id: str,
        role: str | None = None,
        seniority: str | None = None,
    ) -> LearningContext:
        skills = await self.get_company_skills(
            db, company_id, role=role, seniority=seniority, limit=15
        )
        responsibilities = await self.get_company_responsibilities(
            db, company_id, role=role, limit=10
        )
        patterns = await self._get_company_patterns(db, company_id)
        success_rate = await self._get_success_rates(db, company_id)
        return LearningContext(
            company_skills=skills,
            company_responsibilities=responsibilities,
            patterns=patterns,
            success_rate=success_rate,
        )


learning_confirmation_service = LearningConfirmationService()
