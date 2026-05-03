"""
FastAPI dependency for RailsAdapter.

Injects a RailsAdapter instance with:
- DB session from get_db
- Rails token from request Authorization header (user JWT) or RAILS_API_TOKEN env var
- Auto-closes on request completion

Auth precedence:
  1. Authorization header from the incoming request (user JWT forwarded to Rails)
  2. RAILS_API_TOKEN env var (service-to-service token for internal calls)

Usage:
    from app.domains.integrations_hub.services.rails_adapter_dependency import get_rails_adapter
    from app.domains.integrations_hub.services.rails_adapter import RailsAdapter

    @router.get("/candidates/{id}")
    async def get_candidate(
        id: str,
        adapter: RailsAdapter = Depends(get_rails_adapter),
    ):
        return await adapter.get_candidate(id)
"""
import logging
import os
from collections.abc import AsyncGenerator

from fastapi import Depends, Request
from app.core.database import get_tenant_db
from lia_config.database import get_db  # noqa: F401  (kept for backward-compat re-exports)
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.integrations_hub.services.rails_adapter import RailsAdapter

logger = logging.getLogger(__name__)

_RAILS_API_TOKEN = os.environ.get("RAILS_API_TOKEN", "")


async def get_rails_adapter(
    request: Request,
    db: AsyncSession = Depends(get_tenant_db),
) -> AsyncGenerator[RailsAdapter, None]:
    """
    FastAPI dependency: yields a RailsAdapter with DB + Rails token.

    The adapter tries Rails first (if RAILS_API_URL is configured),
    falls back to local DB otherwise.

    Token selection:
      - User JWT from Authorization header takes priority (so user context is forwarded)
      - Falls back to RAILS_API_TOKEN env var for service-to-service calls
      - WeDOTalentATSClient also falls back to RAILS_API_TOKEN when no token is injected
    """
    bearer = request.headers.get("Authorization", "")
    user_token = bearer.replace("Bearer ", "").strip() if bearer.startswith("Bearer ") else None
    effective_token = user_token or _RAILS_API_TOKEN or None

    adapter = RailsAdapter(db=db, rails_token=effective_token)
    try:
        yield adapter
    finally:
        await adapter.close()
