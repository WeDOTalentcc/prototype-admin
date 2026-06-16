from datetime import datetime
"""
Recruiter Profiles API endpoints.
Manages recruiter personalization profiles, preferences, and settings.
"""
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_or_demo, get_user_company_id
from app.auth.models import User
from app.core.database import get_db, get_tenant_db
from app.shared.services.recruiter_personalization_service import recruiter_personalization_service
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel

from app.services.cache.context_cache import get_context_cache


router = APIRouter()
logger = logging.getLogger(__name__)


class RecruiterProfileResponse(BaseModel):
    id: str
    recruiter_id: str
    company_id: str
    total_jobs_created: int = 0
    total_corrections_made: int = 0
    avg_completion_time_seconds: float | None = None
    preferred_seniorities: list[str] = Field(default_factory=list)
    preferred_departments: list[str] = Field(default_factory=list)
    wizard_mode: str = "standard"
    experience_level: str = "beginner"
    profile_version: int = 1


# DUPLICATE_OF_INTENT: app/schemas/recruiter_profile.py:147 — handler-side personalization update with simpler field set (Sprint Q.4: M-bucket pending field-naming alignment)
class PersonalizationSettingsUpdate(WeDoBaseModel):
    personalization_enabled: bool | None = None
    data_collection_consent: bool | None = None
    show_personalization_indicators: bool | None = None
    allow_behavior_learning: bool | None = None
    preferred_language: str | None = None


class PersonalizationSettingsResponse(BaseModel):
    recruiter_id: str
    personalization_enabled: bool = True
    data_collection_consent: bool = True
    show_personalization_indicators: bool = True
    allow_behavior_learning: bool = True
    preferred_language: str = "pt-BR"


class FieldPreferenceResponse(BaseModel):
    field_name: str
    correction_count: int = 0
    correction_rate: float = 0.0
    typical_value: str | None = None
    avg_time_on_field_seconds: float | None = None
    skip_rate: float = 0.0


class PersonalizedThresholdsResponse(BaseModel):
    base_threshold: float
    adjusted_threshold: float
    field_adjustments: dict[str, float] = {}
    experience_adjustment: float = 0.0


class RecordEventRequest(WeDoBaseModel):
    event_type: str
    field_name: str | None = None
    original_value: Any | None = None
    new_value: Any | None = None
    metadata: dict[str, Any] | None = None
    session_id: str | None = None
    job_draft_id: str | None = None


@router.get("/me", response_model=RecruiterProfileResponse)
async def get_my_profile(
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user_or_demo),

company_id: str = Depends(require_company_id)):
    """
    Get the current recruiter's personalization profile.
    
    Creates a new profile if one doesn't exist.
    """
    company_id = get_user_company_id(current_user)
    try:
        profile = await recruiter_personalization_service.get_or_create_profile(
            db, str(current_user.id), company_id
        )
        
        return RecruiterProfileResponse(
            id=str(profile.id),
            recruiter_id=profile.recruiter_id,
            company_id=profile.company_id,
            total_jobs_created=profile.total_jobs_created or 0,
            total_corrections_made=profile.total_corrections_made or 0,
            avg_completion_time_seconds=profile.avg_completion_time_seconds,
            preferred_seniorities=profile.preferred_seniorities or [],
            preferred_departments=profile.preferred_departments or [],
            wizard_mode=profile.wizard_mode or "standard",
            experience_level=profile.experience_level or "beginner",
            profile_version=profile.profile_version or 1,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recruiter profile: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving profile")


@router.get("/me/settings", response_model=PersonalizationSettingsResponse)
async def get_my_settings(
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Get the current recruiter's personalization settings.
    
    LGPD-compliant settings for data collection and display preferences.
    """
    try:
        settings = await recruiter_personalization_service.get_or_create_settings(
            db, str(current_user.id)
        )
        
        return PersonalizationSettingsResponse(
            recruiter_id=settings.recruiter_id,
            personalization_enabled=settings.personalization_enabled,
            data_collection_consent=settings.data_collection_consent,
            show_personalization_indicators=settings.show_personalization_indicators,
            allow_behavior_learning=settings.allow_behavior_learning,
            preferred_language=settings.preferred_language or "pt-BR",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting settings: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving settings")


@router.patch("/me/settings", response_model=PersonalizationSettingsResponse)
async def update_my_settings(
    request: PersonalizationSettingsUpdate,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Update personalization settings.
    
    Allows users to control data collection and personalization behavior.
    """
    try:
        settings = await recruiter_personalization_service.update_settings(
            db,
            str(current_user.id),
            personalization_enabled=request.personalization_enabled,
            data_collection_consent=request.data_collection_consent,
            show_personalization_indicators=request.show_personalization_indicators,
            allow_behavior_learning=request.allow_behavior_learning,
            preferred_language=request.preferred_language,
        )
        
        return PersonalizationSettingsResponse(
            recruiter_id=settings.recruiter_id,
            personalization_enabled=settings.personalization_enabled,
            data_collection_consent=settings.data_collection_consent,
            show_personalization_indicators=settings.show_personalization_indicators,
            allow_behavior_learning=settings.allow_behavior_learning,
            preferred_language=settings.preferred_language or "pt-BR",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        raise HTTPException(status_code=500, detail="Error updating settings")


@router.get("/me/field-preferences", response_model=list[FieldPreferenceResponse])
async def get_my_field_preferences(
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user_or_demo),

company_id: str = Depends(require_company_id)):
    """
    Get field-specific preferences for the current recruiter.
    
    Shows which fields are often corrected and typical values used.
    """
    company_id = get_user_company_id(current_user)
    try:
        profile = await recruiter_personalization_service.get_or_create_profile(
            db, str(current_user.id), company_id
        )
        
        preferences = await recruiter_personalization_service.get_field_preferences(
            db, profile.id
        )
        
        return [
            FieldPreferenceResponse(
                field_name=p.field_name,
                correction_count=p.correction_count or 0,
                correction_rate=p.correction_rate or 0.0,
                typical_value=p.typical_value,
                avg_time_on_field_seconds=p.avg_time_on_field_seconds,
                skip_rate=p.skip_rate or 0.0,
            )
            for p in preferences
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting field preferences: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving field preferences")


@router.get("/me/thresholds", response_model=PersonalizedThresholdsResponse)
async def get_personalized_thresholds(
    base_threshold: float = 0.7,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user_or_demo),

company_id: str = Depends(require_company_id)):
    """
    Get personalized confidence thresholds for the wizard.
    
    Returns adjusted thresholds based on recruiter experience and history.
    """
    company_id = get_user_company_id(current_user)
    try:
        thresholds = await recruiter_personalization_service.calculate_personalized_thresholds(
            db, str(current_user.id), company_id, base_threshold
        )
        
        return PersonalizedThresholdsResponse(
            base_threshold=base_threshold,
            adjusted_threshold=thresholds.get("adjusted_threshold", base_threshold),
            field_adjustments=thresholds.get("field_adjustments", {}),
            experience_adjustment=thresholds.get("experience_adjustment", 0.0),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting thresholds: {e}")
        raise HTTPException(status_code=500, detail="Error calculating thresholds")


@router.post("/me/events", response_model=None)
async def record_personalization_event(
    request: RecordEventRequest,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user_or_demo),

company_id: str = Depends(require_company_id)):
    """
    Record a personalization event for learning.
    
    Events like field corrections, time spent, values selected are used
    to improve personalization over time.
    """
    company_id = get_user_company_id(current_user)
    try:
        settings = await recruiter_personalization_service.get_or_create_settings(
            db, str(current_user.id)
        )
        
        if not settings.data_collection_consent or not settings.allow_behavior_learning:
            return {"recorded": False, "reason": "Data collection not consented"}
        
        event = await recruiter_personalization_service.record_event(
            db,
            recruiter_id=str(current_user.id),
            company_id=company_id,
            event_type=request.event_type,
            field_name=request.field_name,
            original_value=request.original_value,
            new_value=request.new_value,
            metadata=request.metadata,
            session_id=request.session_id,
            job_draft_id=request.job_draft_id,
        )
        
        return {"recorded": True, "event_id": str(event.id)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording event: {e}")
        raise HTTPException(status_code=500, detail="Error recording event")


@router.post("/me/recalculate", response_model=None)
async def recalculate_profile(
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user_or_demo),

company_id: str = Depends(require_company_id)):
    """
    Trigger a recalculation of the recruiter's profile.
    
    Updates statistics and preferences based on recent activity.
    """
    company_id = get_user_company_id(current_user)
    try:
        profile = await recruiter_personalization_service.recalculate_profile(
            db, str(current_user.id), company_id
        )
        
        return {
            "recalculated": True,
            "profile_version": profile.profile_version,
            "experience_level": profile.experience_level,
            "wizard_mode": profile.wizard_mode,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recalculating profile: {e}")
        raise HTTPException(status_code=500, detail="Error recalculating profile")


@router.delete("/me/data", response_model=None)
async def delete_my_personalization_data(
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Delete all personalization data for the current recruiter.
    
    LGPD compliance: users can request deletion of their personalization data.
    """
    try:
        await recruiter_personalization_service.delete_all_data(
            db, str(current_user.id)
        )
        
        return {"deleted": True, "message": "All personalization data has been deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting data: {e}")
        raise HTTPException(status_code=500, detail="Error deleting personalization data")


# ── GAP-06-001/002 — ContextCache TTL endpoints ─────────────────────────

class RecruiterContextResponse(BaseModel):
    recruiter_id: str
    company_id: str
    experience_level: str
    wizard_mode: str
    source: str  # "cache" | "fresh"
    cached_at: str | None = None


class DashboardStatsResponse(BaseModel):
    total_jobs_created: int
    total_corrections_made: int
    experience_level: str
    source: str


@router.get("/me/context", response_model=RecruiterContextResponse)
async def get_recruiter_context(
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user_or_demo),
    company_id: str = Depends(require_company_id),
):
    """
    Recruiter context snapshot — user, company, role.
    TTL: 5 minutes. Invalidated on stage transitions and writes.
    """
    recruiter_id = str(current_user.id)
    cache_key = f"recruiter:{recruiter_id}:context"

    try:
        cache = await get_context_cache()
        cached = await cache.get_with_ttl(cache_key, ttl_seconds=300)
        if cached:
            return RecruiterContextResponse(**cached, source="cache")
    except Exception as e:
        logger.warning("[ContextCache] get failed, falling back to fresh: %s", e)

    profile = await recruiter_personalization_service.get_or_create_profile(
        db, recruiter_id, get_user_company_id(current_user)
    )

    ctx = {
        "recruiter_id": recruiter_id,
        "company_id": company_id,
        "experience_level": profile.experience_level or "beginner",
        "wizard_mode": profile.wizard_mode or "standard",
        "cached_at": datetime.utcnow().isoformat(),
    }

    try:
        cache = await get_context_cache()
        await cache.set_with_ttl(cache_key, ctx, ttl_seconds=300)
    except Exception as e:
        logger.warning("[ContextCache] set failed (non-fatal): %s", e)

    return RecruiterContextResponse(**ctx, source="fresh")


@router.get("/me/dashboard-stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user_or_demo),
    company_id: str = Depends(require_company_id),
):
    """
    Dashboard stats — totals from recruiter profile.
    TTL: 5 minutes. Invalidated on profile recalculation.
    """
    recruiter_id = str(current_user.id)
    cache_key = f"recruiter:{recruiter_id}:dashboard:stats"

    try:
        cache = await get_context_cache()
        cached = await cache.get_with_ttl(cache_key, ttl_seconds=300)
        if cached:
            return DashboardStatsResponse(**cached, source="cache")
    except Exception as e:
        logger.warning("[ContextCache] get failed, falling back to fresh: %s", e)

    profile = await recruiter_personalization_service.get_or_create_profile(
        db, recruiter_id, get_user_company_id(current_user)
    )

    stats = {
        "total_jobs_created": profile.total_jobs_created or 0,
        "total_corrections_made": profile.total_corrections_made or 0,
        "experience_level": profile.experience_level or "beginner",
    }

    try:
        cache = await get_context_cache()
        await cache.set_with_ttl(cache_key, stats, ttl_seconds=300)
    except Exception as e:
        logger.warning("[ContextCache] set failed (non-fatal): %s", e)

    return DashboardStatsResponse(**stats, source="fresh")
