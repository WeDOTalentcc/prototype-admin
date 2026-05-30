"""Event history endpoint for SOX audit replay."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.shared.security.require_company_id import require_company_id
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

router = APIRouter(tags=["audit"])

@router.get("/candidates/{candidate_id}/event-history", response_model=None)
async def get_candidate_event_history(
    candidate_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    from_sequence: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(require_company_id),
):
    # multi-tenancy: company_id vem do JWT via require_company_id (canonical)
    from app.shared.services.event_store_service import event_store_service
    events = await event_store_service.get_history(
        aggregate_type="candidate",
        aggregate_id=candidate_id,
        db=db,
        from_sequence=from_sequence,
        limit=min(limit, 500),
    )
    return {"candidate_id": candidate_id, "events": events, "total": len(events)}

reorder_collection_before_item(router)
