"""Event history endpoint for SOX audit replay."""

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

router = APIRouter(tags=["audit"])

@router.get("/candidates/{candidate_id}/event-history", response_model=None)
async def get_candidate_event_history(
    candidate_id: str,
    from_sequence: int = 0,
    limit: int = 100,
    x_company_id: str | None = Header(None),
    db: AsyncSession = Depends(get_db),
):
    if not x_company_id:
        raise HTTPException(status_code=401, detail="X-Company-ID required")
    from app.services.event_store_service import event_store_service
    events = await event_store_service.get_history(
        aggregate_type="candidate",
        aggregate_id=candidate_id,
        db=db,
        from_sequence=from_sequence,
        limit=min(limit, 500),
    )
    return {"candidate_id": candidate_id, "events": events, "total": len(events)}
