"""
Credits API endpoints.
Manages user credit balance for paid features (e.g., Pearch AI global search).
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.candidate import CandidateSearch

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/credits", tags=["credits"])


class CreditBalanceResponse(BaseModel):
    """Response model for credit balance."""
    available_credits: int
    total_consumed: int
    total_searches: int
    last_updated: str | None = None


@router.get("/balance", response_model=CreditBalanceResponse)
async def get_credit_balance(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Get current credit balance for a user.
    
    Returns:
        - available_credits: Current available credits
        - total_consumed: Total credits consumed historically
        - total_searches: Number of global searches performed
        - last_updated: Timestamp of last credit update (optional)
    
    TODO: Implement real credit management system
    For now, returns mock data based on consumed credits from searches
    """
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        # Calculate total credits consumed from candidate_searches table
        result = await db.execute(
            select(
                func.coalesce(func.sum(CandidateSearch.credits_consumed), 0).label("total_consumed"),
                func.count(CandidateSearch.id).filter(CandidateSearch.used_global_search).label("global_searches")
            ).where(CandidateSearch.user_id == user_id)
        )
        
        row = result.first()
        total_consumed = int(row.total_consumed) if row else 0
        global_searches = int(row.global_searches) if row else 0
        
        # TODO: Replace with real credit system (billing, subscription, etc)
        # For now, mock initial balance of 100 credits
        initial_balance = 100
        available_credits = max(0, initial_balance - total_consumed)
        
        logger.info(f"💳 Credit balance for {user_id}: {available_credits} available ({total_consumed} consumed, {global_searches} searches)")
        
        return CreditBalanceResponse(
            available_credits=available_credits,
            total_consumed=total_consumed,
            total_searches=global_searches,
            last_updated=None  # TODO: Add when implementing real system
        )
        
    except Exception as e:
        logger.error(f"❌ Error fetching credit balance: {e}")
        # Return safe defaults on error
        return CreditBalanceResponse(
            available_credits=50,  # Fallback value
            total_consumed=0,
            total_searches=0
        )
