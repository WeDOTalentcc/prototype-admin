"""
FastAPI dependency for RailsAdapter.

Injects a RailsAdapter instance with:
- DB session from get_db
- Rails token from request.state (set by AuthEnforcementMiddleware)
- Auto-closes on request completion

Usage:
    from app.services.rails_adapter_dependency import get_rails_adapter
    from app.domains.integrations_hub.services.rails_adapter import RailsAdapter

    @router.get("/candidates/{id}")
    async def get_candidate(
        id: str,
        adapter: RailsAdapter = Depends(get_rails_adapter),
    ):
        return await adapter.get_candidate(id)
"""
import logging
from collections.abc import AsyncGenerator

from fastapi import Depends, Request
from lia_config.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.integrations_hub.services.rails_adapter import RailsAdapter

logger = logging.getLogger(__name__)


async def get_rails_adapter(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> AsyncGenerator[RailsAdapter, None]:
    """
    FastAPI dependency: yields a RailsAdapter with DB + Rails token.

    The adapter tries Rails first (if RAILS_API_URL is configured),
    falls back to local DB otherwise.
    """
    getattr(request.state, "token_payload", {})
    token_str = request.headers.get("Authorization", "").replace("Bearer ", "") or None

    adapter = RailsAdapter(db=db, rails_token=token_str)
    try:
        yield adapter
    finally:
        await adapter.close()
