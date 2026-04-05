"""
Tenant-scoped session ID generation.

Multi-tenancy: all session IDs are prefixed with company_id
to ensure tenant isolation and traceability.

Usage:
    from app.shared.tenant_session import create_session_id
    session_id = create_session_id(company_id)
"""
import uuid


def create_session_id(company_id: str) -> str:
    """Create a tenant-scoped session ID.

    Format: {company_id}:{uuid4}

    This ensures:
    1. Sessions are traceable to a specific tenant
    2. Session IDs from different tenants never collide
    3. Tenant can be extracted from session_id without DB lookup
    """
    return f"{company_id}:{uuid.uuid4()}"


def extract_company_id(session_id: str) -> str:
    """Extract company_id from a tenant-scoped session ID.

    Returns empty string for legacy session IDs without prefix.
    """
    if ":" in session_id:
        return session_id.split(":", 1)[0]
    return ""
