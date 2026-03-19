"""
Policy Helper — Central utility for accessing CompanyHiringPolicy.

All agents and services should use get_company_policy() to get the policy
for a company. Returns defaults if no policy is configured.
"""
import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.company_hiring_policy import (
    CompanyHiringPolicy,
    ALL_DEFAULTS,
    PIPELINE_RULES_DEFAULTS,
    SCHEDULING_RULES_DEFAULTS,
    COMMUNICATION_RULES_DEFAULTS,
    SCREENING_RULES_DEFAULTS,
    AUTOMATION_RULES_DEFAULTS,
)

logger = logging.getLogger(__name__)

_policy_cache: Dict[str, Dict[str, Any]] = {}


def _get_defaults_dict() -> Dict[str, Any]:
    return {
        "id": None,
        "company_id": None,
        "pipeline_rules": PIPELINE_RULES_DEFAULTS.copy(),
        "scheduling_rules": SCHEDULING_RULES_DEFAULTS.copy(),
        "communication_rules": COMMUNICATION_RULES_DEFAULTS.copy(),
        "screening_rules": SCREENING_RULES_DEFAULTS.copy(),
        "automation_rules": AUTOMATION_RULES_DEFAULTS.copy(),
        "pipeline_templates": [],
        "learned_patterns": [],
        "setup_progress": 0,
        "setup_completed_at": None,
    }


async def get_company_policy(
    company_id: str,
    db: Optional[AsyncSession] = None,
    use_cache: bool = True
) -> Dict[str, Any]:
    """
    Get the hiring policy for a company.
    Returns defaults if no policy exists.
    """
    if use_cache and company_id in _policy_cache:
        return _policy_cache[company_id]

    if db is None:
        from app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            return await _fetch_policy(company_id, session, use_cache)
    else:
        return await _fetch_policy(company_id, db, use_cache)


async def _fetch_policy(
    company_id: str,
    db: AsyncSession,
    use_cache: bool
) -> Dict[str, Any]:
    try:
        result = await db.execute(
            select(CompanyHiringPolicy).where(
                CompanyHiringPolicy.company_id == company_id
            )
        )
        policy = result.scalar_one_or_none()

        if policy:
            policy_dict = policy.to_dict()
        else:
            policy_dict = _get_defaults_dict()
            policy_dict["company_id"] = company_id

        if use_cache:
            _policy_cache[company_id] = policy_dict

        return policy_dict
    except Exception as e:
        logger.error(f"Error fetching policy for {company_id}: {e}")
        defaults = _get_defaults_dict()
        defaults["company_id"] = company_id
        return defaults


def invalidate_policy_cache(company_id: str):
    """Invalidate cached policy for a company."""
    _policy_cache.pop(company_id, None)


def invalidate_all_cache():
    """Clear entire policy cache."""
    _policy_cache.clear()


def get_policy_rule(policy: Dict[str, Any], block: str, key: str, default=None):
    """Get a specific rule from a policy dict with fallback to defaults."""
    block_data = policy.get(block, {})
    if block_data and key in block_data:
        return block_data[key]
    block_defaults = ALL_DEFAULTS.get(block, {})
    if isinstance(block_defaults, dict):
        return block_defaults.get(key, default)
    return default
