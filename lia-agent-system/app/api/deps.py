"""API dependencies — compatibility shim for rh_dashboard imports."""
from fastapi import Request


async def get_current_company_id(request: Request) -> str:
    """Extract company_id from authenticated request state."""
    company_id = getattr(request.state, "company_id", "") or ""
    return str(company_id) if company_id else ""
