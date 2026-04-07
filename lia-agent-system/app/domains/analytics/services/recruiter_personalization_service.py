"""
Recruiter Personalization Service - Personalizes wizard experience per recruiter.

This service enables personalized wizard experience based on:
- Individual recruiter correction history
- Field-specific preferences
- Communication style preferences
- Custom confidence thresholds

When a recruiter has 10+ jobs created, personalization becomes available
with custom defaults, thresholds, and flow adaptations.
"""
import logging
import statistics
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.feedback_learning import WizardFeedback
from lia_models.recruiter_profile import (
    PersonalizationSettings,
    ProfileCalculationLog,
    RecruiterFieldPreference,
    RecruiterProfile,
)
from app.services.confidence_policy_service import ConfidenceThresholds

logger = logging.getLogger(__name__)


MIN_JOBS_FOR_PERSONALIZATION = 10
PROFILE_RECALCULATION_HOURS = 24


@dataclass
class PersonalizedThresholds:
    """Personalized confidence thresholds for a recruiter."""
    base_thresholds: ConfidenceThresholds
    field_overrides: dict[str, float] = dataclass_field(default_factory=dict)
    reason: str = "default"


@dataclass
class WizardFlowConfig:
    """Configuration for personalized wizard flow."""
    show_detailed_explanations: bool = True
    skip_optional_confirmations: bool = False
    auto_expand_sections: bool = True
    suggest_jd_import: bool = False
    highlight_often_corrected: bool = True
    pre_select_preferences: bool = True


@dataclass
class PersonalizedDefaults:
    """Personalized default values for wizard."""
    seniority: str | None = None
    department: str | None = None
    work_model: str | None = None
    salary_adjustment: float = 1.0
    suggested_skills: list[str] = dataclass_field(default_factory=list)


@dataclass
class PersonalizationContext:
    """Full personalization context for a recruiter."""
    recruiter_id: str
    is_new_user: bool = True
    personalization_level: str = "none"
    profile: RecruiterProfile | None = None
    settings: PersonalizationSettings | None = None
    flow_config: WizardFlowConfig = dataclass_field(default_factory=WizardFlowConfig)
    thresholds: PersonalizedThresholds = dataclass_field(
        default_factory=lambda: PersonalizedThresholds(base_thresholds=ConfidenceThresholds())
    )
    defaults: PersonalizedDefaults = dataclass_field(default_factory=PersonalizedDefaults)
    field_preferences: dict[str, RecruiterFieldPreference] = dataclass_field(default_factory=dict)


class RecruiterPersonalizationService:
    """
    Personalizes wizard experience per recruiter.
    
    Features:
    - Profile management (create, update, calculate)
    - Event tracking for learning
    - Personalized thresholds per field
    - Flow configuration based on preferences
    - Default value personalization
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def get_or_create_profile(
        self,
        db: AsyncSession,
        recruiter_id: str,
        company_id: str
    ) -> RecruiterProfile:
        """Get existing profile or create a new one."""
        query = select(RecruiterProfile).where(
            RecruiterProfile.recruiter_id == recruiter_id
        )
        result = await db.execute(query)
        profile = result.scalar_one_or_none()
        
        if not profile:
            profile = RecruiterProfile(
                recruiter_id=recruiter_id,
                company_id=company_id,
            )
            db.add(profile)
            await db.flush()
        
        return profile
    
    async def get_personalization_context(
        self,
        db: AsyncSession,
        recruiter_id: str,
        company_id: str
    ) -> PersonalizationContext:
        """
        Build full personalization context for a recruiter.
        
        Returns personalization data including profile, settings,
        thresholds, and flow configuration.
        """
        context = PersonalizationContext(recruiter_id=recruiter_id)
        
        try:
            profile = await self.get_or_create_profile(db, recruiter_id, company_id)
            context.profile = profile
            
            settings_query = select(PersonalizationSettings).where(
                PersonalizationSettings.recruiter_id == recruiter_id
            )
            settings_result = await db.execute(settings_query)
            context.settings = settings_result.scalar_one_or_none()
            
            if context.settings and not context.settings.enable_personalization:  # type: ignore
                context.personalization_level = "disabled"
                return context
            
            total_jobs = profile.total_jobs_created  # type: ignore
            if total_jobs is None or total_jobs < MIN_JOBS_FOR_PERSONALIZATION:
                context.is_new_user = True
                context.personalization_level = "minimal"
                return context
            
            context.is_new_user = False
            context.personalization_level = "full" if total_jobs >= 30 else "partial"
            
            prefs_query = select(RecruiterFieldPreference).where(
                RecruiterFieldPreference.recruiter_id == recruiter_id
            )
            prefs_result = await db.execute(prefs_query)
            for pref in prefs_result.scalars():
                context.field_preferences[str(pref.field_name)] = pref  # type: ignore
            
            context.flow_config = self._build_flow_config(profile)
            context.thresholds = self._build_thresholds(profile, context.field_preferences)
            context.defaults = self._build_defaults(profile)
            
            return context
            
        except Exception as e:
            self.logger.error(f"Error building personalization context: {e}")
            return context
    
    def _build_flow_config(self, profile: RecruiterProfile) -> WizardFlowConfig:
        """Build flow configuration from profile."""
        return WizardFlowConfig(
            show_detailed_explanations=bool(profile.prefers_detailed_explanations),  # type: ignore
            skip_optional_confirmations=bool(profile.prefers_quick_flow),  # type: ignore
            auto_expand_sections=not bool(profile.prefers_quick_flow),  # type: ignore
            suggest_jd_import=bool(profile.uses_jd_import),  # type: ignore
            highlight_often_corrected=True,
            pre_select_preferences=True,
        )
    
    def _build_thresholds(
        self,
        profile: RecruiterProfile,
        field_preferences: dict[str, RecruiterFieldPreference]
    ) -> PersonalizedThresholds:
        """Build personalized thresholds from profile and field preferences."""
        base = ConfidenceThresholds()
        
        if profile.prefers_quick_flow:  # type: ignore
            base = ConfidenceThresholds(
                silent_apply=0.80,
                apply_notify=0.65,
                ask_user=0.45
            )
        
        custom = profile.custom_confidence_thresholds  # type: ignore
        if custom:
            if "silent_apply" in custom:
                base.silent_apply = custom["silent_apply"]
            if "apply_notify" in custom:
                base.apply_notify = custom["apply_notify"]
            if "ask_user" in custom:
                base.ask_user = custom["ask_user"]
        
        field_overrides = {}
        for field_name, pref in field_preferences.items():
            if pref.personal_confidence_threshold:  # type: ignore
                field_overrides[field_name] = float(pref.personal_confidence_threshold)  # type: ignore
            elif pref.times_seen and pref.times_corrected:  # type: ignore
                correction_rate = pref.times_corrected / pref.times_seen  # type: ignore
                if correction_rate > 0.5:
                    field_overrides[field_name] = 0.90
                elif correction_rate < 0.2:
                    field_overrides[field_name] = 0.70
        
        return PersonalizedThresholds(
            base_thresholds=base,
            field_overrides=field_overrides,
            reason="personalized" if field_overrides else "profile_based"
        )
    
    def _build_defaults(self, profile: RecruiterProfile) -> PersonalizedDefaults:
        """Build personalized defaults from profile."""
        defaults = PersonalizedDefaults()
        
        preferred_seniorities = profile.preferred_seniorities  # type: ignore
        if preferred_seniorities and len(preferred_seniorities) == 1:
            defaults.seniority = preferred_seniorities[0]
        
        preferred_departments = profile.preferred_departments  # type: ignore
        if preferred_departments and len(preferred_departments) == 1:
            defaults.department = preferred_departments[0]
        
        salary_percentile = profile.typical_salary_percentile  # type: ignore
        if salary_percentile:
            if salary_percentile > 70:
                defaults.salary_adjustment = 1.1
            elif salary_percentile < 30:
                defaults.salary_adjustment = 0.9
        
        return defaults
    
    async def record_event(
        self,
        db: AsyncSession,
        recruiter_id: str,
        company_id: str,
        event_type: str,
        field_name: str | None = None,
        job_id: UUID | None = None,
        suggested_value: Any = None,
        final_value: Any = None,
        context: dict[str, Any] | None = None,
        time_to_decision_ms: int | None = None
    ) -> dict[str, Any]:
        """
        Record a personalization event for learning.
        
        Event types:
        - field_suggested: A field suggestion was shown
        - field_accepted: Suggestion was accepted without change
        - field_corrected: Suggestion was corrected
        - step_skipped: Optional step was skipped
        - explanation_dismissed: Explanation was closed quickly
        - jd_imported: JD import feature was used
        
        Note: Events are tracked via WizardFeedback for persistence.
        """
        event_data = {
            "recruiter_id": recruiter_id,
            "company_id": company_id,
            "job_id": str(job_id) if job_id else None,
            "event_type": event_type,
            "field_name": field_name,
            "suggested_value": suggested_value,
            "final_value": final_value,
            "context": context or {},
            "time_to_decision_ms": time_to_decision_ms,
        }
        
        if field_name and event_type in ["field_accepted", "field_corrected"]:
            await self._update_field_preference(
                db, recruiter_id, field_name,
                accepted=(event_type == "field_accepted"),
                suggested_value=suggested_value,
                final_value=final_value
            )
        
        return event_data
    
    async def _update_field_preference(
        self,
        db: AsyncSession,
        recruiter_id: str,
        field_name: str,
        accepted: bool,
        suggested_value: Any = None,
        final_value: Any = None
    ) -> None:
        """Update field preference based on event."""
        query = select(RecruiterFieldPreference).where(
            and_(
                RecruiterFieldPreference.recruiter_id == recruiter_id,
                RecruiterFieldPreference.field_name == field_name
            )
        )
        result = await db.execute(query)
        pref = result.scalar_one_or_none()
        
        if not pref:
            pref = RecruiterFieldPreference(
                recruiter_id=recruiter_id,
                field_name=field_name,
            )
            db.add(pref)
        
        pref.times_seen = (pref.times_seen or 0) + 1  # type: ignore
        if accepted:
            pref.times_accepted = (pref.times_accepted or 0) + 1  # type: ignore
        else:
            pref.times_corrected = (pref.times_corrected or 0) + 1  # type: ignore
            
            if suggested_value is not None and final_value is not None:
                if field_name in ["salary_range", "salary_min", "salary_max"]:
                    try:
                        if isinstance(suggested_value, dict) and isinstance(final_value, dict):
                            sugg_mid = (suggested_value.get("min", 0) + suggested_value.get("max", 0)) / 2
                            final_mid = (final_value.get("min", 0) + final_value.get("max", 0)) / 2
                        else:
                            sugg_mid = float(suggested_value)
                            final_mid = float(final_value)
                        
                        if sugg_mid > 0:
                            magnitude = abs(final_mid - sugg_mid) / sugg_mid
                            direction = "increase" if final_mid > sugg_mid else "decrease"
                            
                            pref.typical_correction_direction = direction  # type: ignore
                            
                            existing_mag = pref.avg_correction_magnitude or 0  # type: ignore
                            times = pref.times_corrected or 1  # type: ignore
                            pref.avg_correction_magnitude = (  # type: ignore
                                (existing_mag * (times - 1) + magnitude) / times
                            )
                    except (ValueError, TypeError):
                        pass
        
        pref.last_interaction_at = datetime.utcnow()  # type: ignore
        await db.flush()
    
    async def recalculate_profile(
        self,
        db: AsyncSession,
        recruiter_id: str
    ) -> RecruiterProfile | None:
        """
        Recalculate recruiter profile from events and feedback.
        
        Analyzes all personalization events and wizard feedback
        to update the recruiter's profile with detected patterns.
        """
        try:
            profile_query = select(RecruiterProfile).where(
                RecruiterProfile.recruiter_id == recruiter_id
            )
            result = await db.execute(profile_query)
            profile = result.scalar_one_or_none()
            
            if not profile:
                return None
            
            previous_snapshot = {
                "preferred_seniorities": profile.preferred_seniorities or [],
                "preferred_departments": profile.preferred_departments or [],
                "correction_patterns": profile.correction_patterns or {},
            }
            
            feedback_query = select(WizardFeedback).where(
                WizardFeedback.user_id == recruiter_id
            )
            feedback_result = await db.execute(feedback_query)
            feedbacks = list(feedback_result.scalars().all())
            
            job_ids = set()
            seniorities: dict[str, int] = {}
            departments: dict[str, int] = {}
            field_corrections: dict[str, int] = {}
            field_totals: dict[str, int] = {}
            creation_times = []
            
            for fb in feedbacks:
                if fb.job_id:
                    job_ids.add(fb.job_id)
                
                ctx = fb.context or {}
                
                if ctx.get("seniority"):
                    sen = ctx["seniority"]
                    seniorities[sen] = seniorities.get(sen, 0) + 1
                
                if ctx.get("department"):
                    dep = ctx["department"]
                    departments[dep] = departments.get(dep, 0) + 1
                
                field_name = fb.field_name
                if field_name:
                    field_totals[field_name] = field_totals.get(field_name, 0) + 1
                    if fb.feedback_type == "correction":
                        field_corrections[field_name] = field_corrections.get(field_name, 0) + 1
                
                if fb.response_time_ms:
                    creation_times.append(fb.response_time_ms)
            
            profile.total_jobs_created = len(job_ids)
            
            if creation_times:
                profile.avg_completion_time_seconds = statistics.mean(creation_times) / 1000
            
            top_seniorities = sorted(seniorities.items(), key=lambda x: -x[1])[:3]
            profile.preferred_seniorities = [s[0] for s in top_seniorities]
            
            top_departments = sorted(departments.items(), key=lambda x: -x[1])[:3]
            profile.preferred_departments = [d[0] for d in top_departments]
            
            correction_rates = {}
            for field, total in field_totals.items():
                corrections = field_corrections.get(field, 0)
                rate = corrections / total if total > 0 else 0
                if rate > 0.1:
                    correction_rates[field] = rate
            
            profile.correction_patterns = correction_rates
            
            total_corrections = sum(field_corrections.values())
            sum(field_totals.values())
            profile.total_corrections_made = total_corrections
            
            quick_decisions = sum(
                1 for fb in feedbacks
                if fb.response_time_ms and fb.response_time_ms < 3000
            )
            if feedbacks and quick_decisions > len(feedbacks) * 0.6:
                profile.wizard_mode = "quick"
            else:
                profile.wizard_mode = "detailed"
            
            profile.last_activity_at = datetime.utcnow()
            
            log = ProfileCalculationLog(
                recruiter_profile_id=profile.id,
                trigger="recalculation",
                jobs_analyzed=len(job_ids),
                corrections_analyzed=total_corrections,
                outcomes_analyzed=0,
                changes_detected=[
                    {"seniorities": list(seniorities.keys())},
                    {"departments": list(departments.keys())},
                    {"corrections": list(correction_rates.keys())},
                ],
                previous_profile_snapshot=previous_snapshot,
                new_profile_snapshot={
                    "preferred_seniorities": profile.preferred_seniorities,
                    "preferred_departments": profile.preferred_departments,
                    "correction_patterns": profile.correction_patterns,
                },
            )
            db.add(log)
            
            await db.flush()
            
            return profile
            
        except Exception as e:
            self.logger.error(f"Error recalculating profile: {e}")
            return None
    
    async def update_settings(
        self,
        db: AsyncSession,
        recruiter_id: str,
        enable_personalization: bool | None = None,
        enable_learning: bool | None = None,
        learn_from_corrections: bool | None = None,
        show_personalization_indicators: bool | None = None,
        consent_version: str | None = None
    ) -> PersonalizationSettings:
        """Update personalization settings for a recruiter."""
        query = select(PersonalizationSettings).where(
            PersonalizationSettings.recruiter_id == recruiter_id
        )
        result = await db.execute(query)
        settings = result.scalar_one_or_none()
        
        if not settings:
            settings = PersonalizationSettings(recruiter_id=recruiter_id)
            db.add(settings)
        
        if enable_personalization is not None:
            settings.enable_personalization = enable_personalization  # type: ignore
        if enable_learning is not None:
            settings.enable_learning = enable_learning  # type: ignore
        if learn_from_corrections is not None:
            settings.learn_from_corrections = learn_from_corrections  # type: ignore
        if show_personalization_indicators is not None:
            settings.show_personalization_indicators = show_personalization_indicators  # type: ignore
        if consent_version is not None:
            settings.consent_version = consent_version  # type: ignore
            settings.consent_given_at = datetime.utcnow()  # type: ignore
        
        await db.flush()
        return settings
    
    async def get_personalization_summary(
        self,
        db: AsyncSession,
        recruiter_id: str
    ) -> dict[str, Any]:
        """Get a summary of personalization status for a recruiter."""
        query = select(RecruiterProfile).where(
            RecruiterProfile.recruiter_id == recruiter_id
        )
        result = await db.execute(query)
        profile = result.scalar_one_or_none()
        
        if not profile:
            return {
                "personalization_available": False,
                "reason": "No profile found",
                "jobs_created": 0,
                "jobs_needed": MIN_JOBS_FOR_PERSONALIZATION,
            }
        
        total_jobs = profile.total_jobs_created or 0  # type: ignore
        
        return {
            "personalization_available": total_jobs >= MIN_JOBS_FOR_PERSONALIZATION,
            "personalization_level": "full" if total_jobs >= 30 else ("partial" if total_jobs >= MIN_JOBS_FOR_PERSONALIZATION else "minimal"),
            "jobs_created": total_jobs,
            "jobs_needed": max(0, MIN_JOBS_FOR_PERSONALIZATION - total_jobs),
            "profile_last_calculated": profile.profile_calculated_at,  # type: ignore
            "preferred_seniorities": profile.preferred_seniorities,  # type: ignore
            "preferred_departments": profile.preferred_departments,  # type: ignore
            "fields_often_corrected": list(profile.fields_often_corrected.keys()) if profile.fields_often_corrected else [],  # type: ignore
            "uses_jd_import": profile.uses_jd_import,  # type: ignore
            "prefers_quick_flow": profile.prefers_quick_flow,  # type: ignore
        }


recruiter_personalization_service = RecruiterPersonalizationService()
