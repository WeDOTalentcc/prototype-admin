"""
PolicyMiddleware — FastAPI dependency that injects CompanyHiringPolicy into request context.

Usage in endpoints:
    @router.get("/my-endpoint")
    async def my_endpoint(
        policy: dict = Depends(get_policy_from_request),
        db: AsyncSession = Depends(get_db)
    ):
        allowed_days = get_policy_rule(policy, "scheduling_rules", "allowed_days", ["mon","tue","wed","thu","fri"])
"""
import logging
from typing import Any

from fastapi import Depends, Header, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.shared.policy_helper import _get_defaults_dict, get_company_policy, get_policy_rule

logger = logging.getLogger(__name__)


async def get_policy_from_request(
    request: Request,
    x_company_id: str | None = Header(None, alias="x-company-id"),
    company_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    FastAPI dependency that resolves company_id and returns the hiring policy.
    
    Resolution order:
    1. x-company-id header
    2. company_id query parameter
    3. company_id from path parameters
    4. Falls back to defaults
    """
    resolved_company_id = (
        x_company_id
        or company_id
        or request.path_params.get("company_id")
    )

    # LIA-C07: Cross-check against JWT-verified company_id
    jwt_company_id = getattr(request.state, "company_id", None)
    if jwt_company_id and resolved_company_id and str(resolved_company_id) != str(jwt_company_id):
        logger.warning(
            "[LIA-C07] company_id mismatch: header=%s, jwt=%s. Using JWT value.",
            resolved_company_id, jwt_company_id
        )
        resolved_company_id = jwt_company_id
    elif jwt_company_id and not resolved_company_id:
        resolved_company_id = jwt_company_id

    if not resolved_company_id:
        logger.debug("No company_id found in request, returning defaults")
        return _get_defaults_dict()
    
    try:
        policy = await get_company_policy(resolved_company_id, db)
        logger.debug(f"Policy loaded for company {resolved_company_id}")
        return policy
    except Exception as e:
        logger.error(f"Error loading policy for {resolved_company_id}: {e}")
        return _get_defaults_dict()


async def get_policy_for_company(
    company_id: str,
    db: AsyncSession,
) -> dict[str, Any]:
    """
    Direct policy lookup for use in services (not as a dependency).
    Convenience wrapper around get_company_policy with error handling.
    """
    if not company_id:
        return _get_defaults_dict()
    
    try:
        return await get_company_policy(company_id, db)
    except Exception as e:
        logger.error(f"Error loading policy for {company_id}: {e}")
        return _get_defaults_dict()


def resolve_policy_value(
    policy: dict[str, Any],
    block: str,
    key: str,
    override: Any = None,
    default: Any = None,
) -> Any:
    """
    Resolve a policy value with explicit override support.
    
    Priority: explicit override > policy value > default
    
    Args:
        policy: Policy dict from get_company_policy
        block: Policy block name (e.g., "scheduling_rules")
        key: Rule key within the block
        override: Explicit override value (takes highest priority if not None)
        default: Default fallback value
    """
    if override is not None:
        return override
    return get_policy_rule(policy, block, key, default)


policy_depends = get_policy_from_request
