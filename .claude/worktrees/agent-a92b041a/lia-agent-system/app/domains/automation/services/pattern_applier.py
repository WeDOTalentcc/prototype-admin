"""
Pattern Applier Service - Applies detected patterns to improve suggestions.

Provides fast lookups for:
- Adjusted field suggestions based on cached correction patterns
- Promoted skills for a company/context
- Success profile hints (avg time-to-fill, common skills, etc.)

Gracefully degrades when no patterns exist (returns None/empty).
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.models.intelligence_layer import PatternCache, CorrectionPattern, SuccessProfile
from app.models.company_learning import CompanySkill

logger = logging.getLogger(__name__)


class PatternApplier:
    """
    Applies detected patterns to improve wizard suggestions.
    
    All methods return None or empty lists when no patterns exist,
    allowing callers to use patterns opportunistically.
    """

    SKILL_PROMOTION_THRESHOLD = 5

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    async def get_adjusted_suggestions(
        self,
        company_id: str,
        field_name: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get adjusted value for a field based on cached correction patterns.
        
        Args:
            company_id: Company identifier
            field_name: Field to get adjustments for (e.g. salary_range, seniority)
            context: Optional dict with role, seniority, department
            
        Returns:
            Dictionary with adjustment info or None if no patterns exist
        """
        ctx = context or {}
        role = ctx.get("role")
        seniority = ctx.get("seniority")
        department = ctx.get("department")

        try:
            async with async_session_factory() as db:
                conditions = [
                    PatternCache.company_id == company_id,
                    PatternCache.pattern_type == "correction",
                    PatternCache.expires_at > datetime.utcnow(),
                ]

                if field_name:
                    conditions.append(
                        PatternCache.pattern_key.ilike(f"%{field_name}%")
                    )

                query = (
                    select(PatternCache)
                    .where(and_(*conditions))
                    .order_by(PatternCache.confidence.desc())
                )
                result = await db.execute(query)
                cached = list(result.scalars().all())

                if not cached:
                    return None

                best = None
                best_specificity = -1

                for pattern in cached:
                    data = pattern.pattern_data or {}
                    specificity = 0

                    if seniority and data.get("seniority"):
                        if data["seniority"].lower() == seniority.lower():
                            specificity += 2
                        else:
                            continue

                    if specificity > best_specificity:
                        best_specificity = specificity
                        best = pattern

                if not best:
                    best = cached[0]

                return {
                    "field": field_name,
                    "pattern_key": best.pattern_key,
                    "adjustment": best.pattern_data,
                    "confidence": best.confidence,
                    "sample_size": best.sample_size,
                    "calculated_at": best.calculated_at.isoformat() if best.calculated_at else None,
                }

        except Exception as e:
            self.logger.error(f"Error getting adjusted suggestions: {e}")
            return None

    async def get_promoted_skills(
        self,
        company_id: str,
        job_title: Optional[str] = None,
        department: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get promoted skills for a company, optionally filtered by context.
        
        Returns skills that have been confirmed >= threshold times
        and are marked as promoted.
        """
        try:
            async with async_session_factory() as db:
                conditions = [
                    CompanySkill.company_id == company_id,
                    CompanySkill.is_promoted == True,
                ]

                query = (
                    select(CompanySkill)
                    .where(and_(*conditions))
                    .order_by(CompanySkill.times_confirmed.desc())
                )
                result = await db.execute(query)
                skills = list(result.scalars().all())

                if not skills:
                    return []

                promoted = []
                for skill in skills:
                    roles = skill.roles_associated or []
                    if job_title and roles:
                        title_lower = job_title.lower()
                        if not any(title_lower in r.lower() or r.lower() in title_lower for r in roles):
                            continue

                    promoted.append({
                        "skill_name": skill.skill_name,
                        "skill_type": skill.skill_type,
                        "category": skill.category,
                        "times_confirmed": skill.times_confirmed,
                        "times_used_in_jobs": skill.times_used_in_jobs,
                        "times_in_successful_hires": skill.times_in_successful_hires,
                        "confidence_score": skill.confidence_score,
                        "roles_associated": skill.roles_associated,
                        "seniority_levels": skill.seniority_levels,
                    })

                return promoted

        except Exception as e:
            self.logger.error(f"Error getting promoted skills: {e}")
            return []

    async def get_success_profile_hints(
        self,
        company_id: str,
        role: Optional[str] = None,
        seniority: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get hints from success profiles for a given context.
        
        Returns aggregated info like avg time-to-fill, common skills,
        satisfaction scores, etc.
        """
        try:
            async with async_session_factory() as db:
                conditions = [
                    SuccessProfile.company_id == company_id,
                ]

                if seniority:
                    conditions.append(
                        or_(
                            SuccessProfile.seniority == seniority.lower(),
                            SuccessProfile.seniority == None,
                        )
                    )

                if role:
                    conditions.append(
                        or_(
                            SuccessProfile.role_family.ilike(f"%{role}%"),
                            SuccessProfile.role_family == None,
                        )
                    )

                query = (
                    select(SuccessProfile)
                    .where(and_(*conditions))
                    .order_by(SuccessProfile.sample_size.desc())
                    .limit(5)
                )
                result = await db.execute(query)
                profiles = list(result.scalars().all())

                if not profiles:
                    return None

                best = profiles[0]

                return {
                    "avg_time_to_fill_days": best.avg_time_to_fill_days,
                    "avg_salary": best.avg_salary,
                    "salary_range_min": best.salary_range_min,
                    "salary_range_max": best.salary_range_max,
                    "common_skills": best.common_skills or [],
                    "common_requirements": best.common_requirements or [],
                    "preferred_work_model": best.preferred_work_model,
                    "avg_satisfaction_score": best.avg_satisfaction_score,
                    "sample_size": best.sample_size,
                    "seniority": best.seniority,
                    "role_family": best.role_family,
                }

        except Exception as e:
            self.logger.error(f"Error getting success profile hints: {e}")
            return None


pattern_applier = PatternApplier()
