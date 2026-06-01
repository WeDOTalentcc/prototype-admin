"""
Policy Helper — Central utility for accessing CompanyHiringPolicy.

SOURCE OF TRUTH for policy data access. All agents and services should use
get_company_policy() to get the policy for a company. Returns defaults if
no policy is configured.

ARCHITECTURE — Two complementary modules:
  - THIS FILE (policy_helper.py): Core data access — get_company_policy(),
    get_policy_rule(), cache invalidation. Import this for service/agent use.
  - app.shared.policy_middleware: FastAPI dependency wrappers —
    get_policy_from_request() (resolves company_id from headers/query/path),
    resolve_policy_value() (override > policy > default). Import for endpoints.
"""
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company_hiring_policy import (
    ALL_DEFAULTS,
    AUTOMATION_RULES_DEFAULTS,
    COMMUNICATION_RULES_DEFAULTS,
    PIPELINE_RULES_DEFAULTS,
    SCHEDULING_RULES_DEFAULTS,
    SCREENING_RULES_DEFAULTS,
    CompanyHiringPolicy,
)

logger = logging.getLogger(__name__)

_policy_cache: dict[str, dict[str, Any]] = {}


def _get_defaults_dict() -> dict[str, Any]:
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
    db: AsyncSession | None = None,
    use_cache: bool = True
) -> dict[str, Any]:
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
) -> dict[str, Any]:
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


def get_policy_rule(policy: dict[str, Any], block: str, key: str, default=None):
    """Get a specific rule from a policy dict with fallback to defaults."""
    block_data = policy.get(block, {})
    if block_data and key in block_data:
        return block_data[key]
    block_defaults = ALL_DEFAULTS.get(block, {})
    if isinstance(block_defaults, dict):
        return block_defaults.get(key, default)
    return default


# ---------------------------------------------------------------------------
# P0.b — Read-path defensive coercion (anti-corruption, defense in depth)
# ---------------------------------------------------------------------------
# Even after P0.a blocks new bad writes and P0.c sanitizes existing rows, gate
# consumers must never trust raw JSON truthiness. The narrative UI corruption
# stored the string "Não" in boolean gate slots; ``"Não"`` is Python-truthy, so
# ``if rules.get("auto_screening"):`` silently turned automations ON. These
# coercers make every gate read fail safe (coerce, fall back to default), never
# crash. Pair with get_policy_rule() or apply directly on a block value.

_COERCE_TRUE_TOKENS = {
    "sim", "true", "1", "yes", "on", "verdadeiro",
    "habilitado", "habilitada", "ativo", "ativa", "ativado", "ativada",
}
_COERCE_FALSE_TOKENS = {
    "não", "nao", "false", "0", "no", "off", "falso",
    "desabilitado", "desabilitada", "inativo", "inativa", "desativado", "desativada",
    "não definido", "nao definido", "",
}


def coerce_bool(value: Any, default: bool = False) -> bool:
    """Coerce a possibly-corrupted policy value to bool. Never raises.

    "Não"/"não definido"/0 -> False; "Sim"/1/True -> True; unknown -> default.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        token = value.strip().lower()
        if token in _COERCE_TRUE_TOKENS:
            return True
        if token in _COERCE_FALSE_TOKENS:
            return False
    return default


def coerce_int(value: Any, default: int = 0) -> int:
    """Coerce a possibly-corrupted policy value to int. Never raises."""
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        s = value.strip()
        if s.lstrip("-").isdigit():
            return int(s)
    return default


def get_policy_bool(policy: dict[str, Any], block: str, key: str, default: bool = False) -> bool:
    """Read a boolean gate from a policy dict with corruption-safe coercion."""
    return coerce_bool(get_policy_rule(policy, block, key, default), default)


def get_policy_int(policy: dict[str, Any], block: str, key: str, default: int = 0) -> int:
    """Read an int field from a policy dict with corruption-safe coercion."""
    return coerce_int(get_policy_rule(policy, block, key, default), default)
