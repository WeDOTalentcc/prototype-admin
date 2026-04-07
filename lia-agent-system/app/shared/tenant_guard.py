"""
TenantGuard — Secure company_id resolution for FastAPI endpoints.

REPLACES all insecure get_company_id_from_header functions.

The old pattern trusted X-Company-ID header blindly:
    company_id = request.headers.get("X-Company-ID")  # INSECURE

The new pattern uses the JWT-validated company_id from request.state:
    company_id = request.state.company_id  # Set by AuthEnforcementMiddleware

If X-Company-ID header is present, it MUST match the JWT's company_id
(already enforced by AuthEnforcementMiddleware).
"""
import logging

from fastapi import Header, HTTPException, Query, Request, status

logger = logging.getLogger(__name__)


def get_verified_company_id(
    request: Request,
    x_company_id: str | None = Header(None, alias="X-Company-ID"),
    company_id: str | None = Query(None),
) -> str:
    """
    Get company_id from the VERIFIED JWT context (request.state).

    Falls back to header/query param ONLY if they match the JWT.
    Returns 401 if no company_id can be resolved.
    Returns 403 if header/query company_id doesn't match JWT.
    """
    # Primary source: JWT-validated company_id from AuthEnforcementMiddleware
    jwt_company = getattr(request.state, "company_id", None)

    # Secondary source: header or query param
    requested_company = x_company_id or company_id

    if jwt_company:
        if requested_company and requested_company != jwt_company:
            logger.warning(
                f"[TenantGuard] CROSS-TENANT blocked: JWT={jwt_company}, "
                f"requested={requested_company}, path={request.url.path}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: company mismatch"
            )
        return jwt_company

    # Fallback for development mode only — when AuthEnforcementMiddleware allows through
    # In production, JWT must always be present; non-JWT resolution is blocked.
    import os
    is_production = os.getenv("ENVIRONMENT", "development").lower() in ("production", "staging")

    if is_production and not jwt_company:
        logger.warning(
            f"[TenantGuard] Production: rejected non-JWT company resolution "
            f"for path={request.url.path}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required: JWT with company context is mandatory"
        )

    if requested_company:
        logger.debug(f"[TenantGuard] Dev mode: using header/query company_id: {requested_company}")
        return requested_company

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Company ID required (authenticate or provide X-Company-ID)"
    )
