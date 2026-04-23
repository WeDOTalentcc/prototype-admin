import logging
import os

logger = logging.getLogger(__name__)

DEMO_COMPANY_UUID = "00000000-0000-4000-a000-000000000001"

# Dev/staging company_id aliases → mapped to DEMO_COMPANY_UUID in non-prod.
# Add here when a new dev/staging environment uses a different ID format.
# In production, WorkOS org IDs map directly — do NOT add prod IDs here.
DEMO_COMPANY_LEGACY_ALIASES = frozenset({
    "demo_company",
    "37",                                    # Rails integer ID in Replit dev
    "a1b2c3d4-e5f6-7890-abcd-ef1234567890",  # Staging placeholder UUID
})

_INVALID_TENANT_VALUES = frozenset({
    "default", "demo_company", "unknown",
    "00000000-0000-0000-0000-000000000000",
    # Note: "a1b2c3d4-..." removed from INVALID — it's a valid dev alias above
})


def _dev_environment() -> bool:
    """Non-production gate aligned with the canonical APP_ENV config.

    Prefers ``APP_ENV`` (the app's source-of-truth via ``app.core.config.settings``),
    then falls back to legacy ``ENVIRONMENT`` / ``NODE_ENV`` for backward compat.
    """
    candidates = []
    try:
        from app.core.config import settings as _settings
        for attr in ("APP_ENV", "ENVIRONMENT"):
            val = getattr(_settings, attr, None)
            if val:
                candidates.append(val)
    except Exception:
        pass
    for var in ("APP_ENV", "ENVIRONMENT", "NODE_ENV"):
        val = os.getenv(var)
        if val:
            candidates.append(val)
    # If ANY source explicitly declares production, treat as production.
    for env in candidates:
        if str(env).lower() in {"production", "prod"}:
            return False
    return True


def normalize_demo_company_id(company_id: str | None, *, context: str = "") -> str | None:
    """Map legacy demo_company string to the canonical demo UUID.

    Only rewrites in non-production. Returns the input unchanged otherwise.
    """
    if not company_id:
        return company_id
    if company_id in DEMO_COMPANY_LEGACY_ALIASES and _dev_environment():
        logger.warning(
            "[tenant] Legacy demo company_id %r mapped to canonical UUID %s%s. "
            "Token/data should be refreshed.",
            company_id, DEMO_COMPANY_UUID,
            f" ({context})" if context else "",
        )
        return DEMO_COMPANY_UUID
    return company_id


def resolve_tenant_id(company_id: str | None, *, context: str = "") -> str:
    if not company_id or company_id in _INVALID_TENANT_VALUES:
        raise ValueError(
            f"Valid company_id is required{' for ' + context if context else ''}. "
            f"Received: {company_id!r}"
        )
    return company_id


def resolve_tenant_id_lenient(company_id: str | None, *, fallback: str = "unknown") -> str:
    if not company_id or company_id in _INVALID_TENANT_VALUES:
        logger.warning(
            "Invalid or missing company_id %r in non-critical path, using fallback %r",
            company_id, fallback,
        )
        return fallback
    return company_id
