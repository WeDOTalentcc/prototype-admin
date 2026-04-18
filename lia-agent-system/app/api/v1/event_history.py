"""Event history endpoint for SOX audit replay."""

from fastapi import APIRouter, Depends, Header, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN
from app.core.database import get_db

# Task #489 — UUID-or-digit constraint for dual-ID path params,
# preventing static sibling routes from being shadowed by
# item handlers (Task #455-class bug).
_DualId = Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)]

router = APIRouter(tags=["audit"])

@router.get("/candidates/{candidate_id}/event-history", response_model=None)
async def get_candidate_event_history(
    candidate_id: _DualId,
    from_sequence: int = 0,
    limit: int = 100,
    x_company_id: str | None = Header(None),
    db: AsyncSession = Depends(get_db),
):
    if not x_company_id:
        raise HTTPException(status_code=401, detail="X-Company-ID required")
    from app.shared.services.event_store_service import event_store_service
    events = await event_store_service.get_history(
        aggregate_type="candidate",
        aggregate_id=candidate_id,
        db=db,
        from_sequence=from_sequence,
        limit=min(limit, 500),
    )
    return {"candidate_id": candidate_id, "events": events, "total": len(events)}

# Task #489 — Keep collection-scoped routes ahead of item-scoped
# routes so a static sibling segment cannot be silently shadowed
# by an {*_id} handler (the Task #455 routing-shadowing bug).
from app.api.v1._path_patterns import reorder_collection_before_item as _reorder_collection_before_item  # noqa: E402

_reorder_collection_before_item(router)
