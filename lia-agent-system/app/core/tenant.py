import logging

logger = logging.getLogger(__name__)

_INVALID_TENANT_VALUES = frozenset({
    "default", "demo_company", "unknown",
    "00000000-0000-0000-0000-000000000000",
    "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
})


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


# Backward-compat: fixed UUID used as demo tenant in seed/test data.
DEMO_COMPANY_UUID: str = "00000000-0000-4000-a000-000000000001"  # O.1: align with CANONICAL_DEMO_UUID (was v7-invalid a1b2c3d4...)
