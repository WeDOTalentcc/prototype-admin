"""
Feature Flag Service - Granular control of platform functionality.

Provides feature toggles for:
- Gradual rollouts of new features
- A/B testing capabilities
- Per-company feature control
- Global feature switches
"""
import logging
import random
from datetime import datetime
from typing import Any

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company_learning import FeatureFlag

logger = logging.getLogger(__name__)


class FeatureFlagService:
    """
    Service for managing feature flags.
    
    Features can be:
    - Global (company_id = None): Apply to all companies
    - Per-company: Apply only to specific company
    - Rollout-based: Enable for X% of requests
    """
    
    DEFAULT_FLAGS = {
        "learning_hub_enabled": {
            "description": "Enable unified learning hub functionality",
            "category": "learning",
            "default": True
        },
        "outcome_learning_enabled": {
            "description": "Enable outcome-based learning when jobs close",
            "category": "learning",
            "default": True
        },
        "stage_feedback_enabled": {
            "description": "Enable stage-by-stage feedback collection",
            "category": "learning",
            "default": True
        },
        "skills_deduplication_enabled": {
            "description": "Enable skills deduplication between stages",
            "category": "wizard",
            "default": True
        },
        "analytics_dashboard_enabled": {
            "description": "Enable learning analytics dashboard",
            "category": "analytics",
            "default": True
        },
        "ai_suggestions_enhanced": {
            "description": "Enable enhanced AI suggestions with learning context",
            "category": "ai",
            "default": True
        },
        "empty_field_notifications": {
            "description": "Enable empty field notifications in wizard",
            "category": "wizard",
            "default": True
        },
        "field_toggles_enabled": {
            "description": "Enable LIA field toggles system",
            "category": "wizard",
            "default": True
        },
        "ENABLE_AUTO_SCREENING": {
            "description": "Enable automatic candidate screening",
            "category": "automation",
            "default": False
        },
        "ENABLE_AUTO_SCHEDULING": {
            "description": "Enable automatic interview scheduling",
            "category": "automation",
            "default": False
        },
        "ENABLE_AUTO_STAGE_ADVANCE": {
            "description": "Enable automatic pipeline stage advancement",
            "category": "automation",
            "default": False
        },
        "CREW_DELEGATION_ENABLED": {
            "description": "Enable CrewAI-style multi-agent delegation on AgentBus",
            "category": "agents",
            "default": True
        },
        "voice_screening_v2_enabled": {
            "description": "Sprint 3.5 W4-1 V2: Voice channel in CustomAgentRuntime (Agent Studio custom agents using voice). Off by default — per-tenant rollout.",
            "category": "voice",
            "default": False
        },
    }
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._cache: dict[str, dict[str, Any]] = {}
        self._cache_ttl = 300
        self._cache_updated: dict[str, datetime] = {}
    
    async def is_enabled(
        self,
        db: AsyncSession,
        flag_key: str,
        company_id: str | None = None
    ) -> bool:
        """
        Check if a feature flag is enabled.
        
        Priority:
        1. Per-company flag (if exists)
        2. Global flag (company_id = None)
        3. Default value from DEFAULT_FLAGS
        """
        try:
            company_flag = None
            if company_id:
                company_stmt = select(FeatureFlag).where(
                    and_(
                        FeatureFlag.flag_key == flag_key,
                        FeatureFlag.company_id == company_id
                    )
                )
                result = await db.execute(company_stmt)
                company_flag = result.scalar_one_or_none()
            
            if company_flag:
                return self._evaluate_flag(company_flag)
            
            global_stmt = select(FeatureFlag).where(
                and_(
                    FeatureFlag.flag_key == flag_key,
                    FeatureFlag.company_id is None
                )
            )
            result = await db.execute(global_stmt)
            global_flag = result.scalar_one_or_none()
            
            if global_flag:
                return self._evaluate_flag(global_flag)
            
            default = self.DEFAULT_FLAGS.get(flag_key, {}).get("default", False)
            return default
            
        except Exception as e:
            self.logger.error(f"Error checking flag {flag_key}: {e}")
            return self.DEFAULT_FLAGS.get(flag_key, {}).get("default", False)
    
    def _evaluate_flag(self, flag: FeatureFlag) -> bool:
        """Evaluate a flag considering rollout percentage and expiry."""
        if flag.expires_at and flag.expires_at < datetime.utcnow():
            return False
        
        if not flag.is_enabled:
            return False
        
        if flag.rollout_percentage < 100:
            return random.randint(1, 100) <= flag.rollout_percentage
        
        return True
    
    async def set_flag(
        self,
        db: AsyncSession,
        flag_key: str,
        is_enabled: bool,
        company_id: str | None = None,
        rollout_percentage: int = 100,
        description: str | None = None,
        category: str | None = None,
        metadata: dict[str, Any] | None = None,
        expires_at: datetime | None = None,
        created_by: str | None = None
    ) -> dict[str, Any]:
        """Set or update a feature flag."""
        try:
            stmt = select(FeatureFlag).where(
                and_(
                    FeatureFlag.flag_key == flag_key,
                    FeatureFlag.company_id == company_id if company_id else FeatureFlag.company_id is None
                )
            )
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if existing:
                existing.is_enabled = is_enabled
                existing.rollout_percentage = rollout_percentage
                if description:
                    existing.description = description
                if category:
                    existing.category = category
                if metadata:
                    existing.flag_metadata = metadata
                if expires_at:
                    existing.expires_at = expires_at
                flag = existing
            else:
                default_info = self.DEFAULT_FLAGS.get(flag_key, {})
                flag = FeatureFlag(
                    flag_key=flag_key,
                    company_id=company_id,
                    is_enabled=is_enabled,
                    rollout_percentage=rollout_percentage,
                    description=description or default_info.get("description"),
                    category=category or default_info.get("category", "general"),
                    flag_metadata=metadata or {},
                    expires_at=expires_at,
                    created_by=created_by
                )
                db.add(flag)
            
            await db.commit()
            
            return {
                "success": True,
                "flag_id": str(flag.id),
                "flag_key": flag_key,
                "is_enabled": is_enabled,
                "company_id": company_id,
                "rollout_percentage": rollout_percentage
            }
        except Exception as e:
            self.logger.error(f"Error setting flag {flag_key}: {e}")
            await db.rollback()
            return {"success": False, "error": str(e)}
    
    async def get_all_flags(
        self,
        db: AsyncSession,
        company_id: str | None = None,
        category: str | None = None
    ) -> list[dict[str, Any]]:
        """Get all flags for a company, merged with defaults."""
        try:
            # TENANT-EXEMPT: governance service operates on system-wide policy enforcement, not per-tenant data rows
            # TENANT-EXEMPT: governance service operates on system-wide policy enforcement, not per-tenant data rows
            stmt = select(FeatureFlag)
            if company_id:
                stmt = stmt.where(
                    or_(
                        FeatureFlag.company_id == company_id,
                        FeatureFlag.company_id is None
                    )
                )
            else:
                stmt = stmt.where(FeatureFlag.company_id is None)
            
            if category:
                stmt = stmt.where(FeatureFlag.category == category)
            
            result = await db.execute(stmt)
            db_flags = result.scalars().all()
            
            db_flag_dict = {}
            for f in db_flags:
                key = f"{f.flag_key}_{f.company_id or 'global'}"
                db_flag_dict[key] = f
            
            all_flags = []
            
            for flag_key, info in self.DEFAULT_FLAGS.items():
                if category and info.get("category") != category:
                    continue
                
                company_key = f"{flag_key}_{company_id}" if company_id else None
                global_key = f"{flag_key}_global"
                
                if company_id and company_key in db_flag_dict:
                    f = db_flag_dict[company_key]
                    all_flags.append(self._flag_to_dict(f, is_overridden=True))
                elif global_key in db_flag_dict:
                    f = db_flag_dict[global_key]
                    all_flags.append(self._flag_to_dict(f, is_overridden=False))
                else:
                    all_flags.append({
                        "flag_key": flag_key,
                        "is_enabled": info.get("default", False),
                        "description": info.get("description"),
                        "category": info.get("category", "general"),
                        "is_default": True,
                        "is_overridden": False,
                        "rollout_percentage": 100
                    })
            
            return all_flags
            
        except Exception as e:
            self.logger.error(f"Error getting flags: {e}")
            return []
    
    def _flag_to_dict(self, flag: FeatureFlag, is_overridden: bool = False) -> dict[str, Any]:
        """Convert flag model to dictionary."""
        return {
            "id": str(flag.id),
            "flag_key": flag.flag_key,
            "company_id": flag.company_id,
            "is_enabled": flag.is_enabled,
            "rollout_percentage": flag.rollout_percentage,
            "description": flag.description,
            "category": flag.category,
            "metadata": flag.flag_metadata,
            "expires_at": flag.expires_at.isoformat() if flag.expires_at else None,
            "is_default": False,
            "is_overridden": is_overridden
        }
    
    async def delete_flag(
        self,
        db: AsyncSession,
        flag_key: str,
        company_id: str | None = None
    ) -> bool:
        """Delete a flag override (reverts to default)."""
        try:
            stmt = select(FeatureFlag).where(
                and_(
                    FeatureFlag.flag_key == flag_key,
                    FeatureFlag.company_id == company_id if company_id else FeatureFlag.company_id is None
                )
            )
            result = await db.execute(stmt)
            flag = result.scalar_one_or_none()
            
            if flag:
                await db.delete(flag)
                await db.commit()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error deleting flag {flag_key}: {e}")
            await db.rollback()
            return False


feature_flag_service = FeatureFlagService()


# FastAPI dependency injection factory — returns singleton (cache must be shared)
def get_feature_flag_service() -> FeatureFlagService:
    return feature_flag_service
