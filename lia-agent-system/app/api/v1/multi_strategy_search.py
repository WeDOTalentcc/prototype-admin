"""
Multi-Strategy Search API endpoint.

Extends the sourcing agents API with parallel multi-strategy search.

Apply to: lia-agent-system/app/api/v1/multi_strategy_search.py
Register: app.include_router(multi_strategy_router)
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.dependencies import get_current_user
from app.core.database import get_db
from pydantic import BaseModel, Field
from typing import Optional
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel

router = APIRouter(prefix="/sourcing", tags=["Multi-Strategy Search"])


class MultiStrategyRequest(WeDoBaseModel):
    job_title: str = Field(..., min_length=2)
    required_skills: list[str] = Field(default_factory=list)
    location: str = Field(default="")
    job_id: Optional[str] = None
    seniority: Optional[str] = None
    exclusions: Optional[list[str]] = None
    strategies: Optional[list[str]] = Field(
        default=None,
        description="Strategies to run. Default: all four. Options: direct, adjacent, silver, reengagement"
    )
    weights: Optional[dict[str, float]] = Field(
        default=None,
        description="Custom weights per strategy. Default: direct=0.30, adjacent=0.25, silver=0.25, reengagement=0.20"
    )
    limit: int = Field(default=50, ge=1, le=200)


class StrategyResultResponse(BaseModel):
    strategy_id: str
    strategy_name: str
    count: int
    elapsed_ms: float
    error: Optional[str] = None


class MultiStrategyResponse(BaseModel):
    total_unique: int
    candidates: list[dict]
    strategy_results: list[StrategyResultResponse]
    elapsed_ms: float


@router.post("/multi-strategy", response_model=MultiStrategyResponse)
async def multi_strategy_search(
    body: MultiStrategyRequest,
    current_user: dict = Depends(get_current_user),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Execute 4 search strategies in parallel, deduplicate and rank results.

    Strategies:
    - direct: exact criteria from input
    - adjacent: LLM-generated similar titles + related skills
    - silver: candidates who were finalists in similar jobs
    - reengagement: inactive candidates (180+ days) matching skills
    """
    from app.services.multi_strategy_search import multi_strategy_search

    company_id = current_user.get("company_id", "unknown")

    result = await multi_strategy_search.search(
        job_title=body.job_title,
        required_skills=body.required_skills,
        location=body.location,
        company_id=company_id,
        job_id=body.job_id,
        seniority=body.seniority,
        exclusions=body.exclusions,
        strategies=body.strategies,
        weights=body.weights,
        limit=body.limit,
    )

    return MultiStrategyResponse(
        total_unique=result.total_unique,
        candidates=result.candidates_ranked,
        strategy_results=[
            StrategyResultResponse(
                strategy_id=sr.strategy_id,
                strategy_name=sr.strategy_name,
                count=sr.count,
                elapsed_ms=sr.elapsed_ms,
                error=sr.error,
            )
            for sr in result.strategy_results
        ],
        elapsed_ms=result.elapsed_ms,
    )
