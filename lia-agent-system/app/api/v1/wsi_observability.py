"""
WSI Observability API - Read-Only Endpoints for WSI Screening Metrics.

CRITICAL: All endpoints are READ-ONLY. No modifications to WSI configuration.
"""
import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.shared.observability.wsi_observability import wsi_observability_service
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN
from typing import Annotated
from fastapi import Path

# Task #489 — UUID-or-digit constraint for dual-ID path params,
# preventing static sibling routes from being shadowed by
# item handlers (Task #455-class bug).
_DualId = Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)]

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/wsi-observability",
    tags=["wsi-observability"],
)


@router.get("/{company_id}/correlation", response_model=None)
async def get_score_outcome_correlation(
    company_id: _DualId,
    db: AsyncSession = Depends(get_db),
):
    return await wsi_observability_service.get_score_vs_outcome_correlation(company_id, db)


@router.get("/{company_id}/block-accuracy", response_model=None)
async def get_block_accuracy(
    company_id: _DualId,
    db: AsyncSession = Depends(get_db),
):
    return await wsi_observability_service.get_block_accuracy(company_id, db)


@router.get("/{company_id}/distribution", response_model=None)
async def get_score_distribution(
    company_id: _DualId,
    db: AsyncSession = Depends(get_db),
):
    return await wsi_observability_service.get_score_distribution(company_id, db)


@router.get("/{company_id}/threshold-analysis", response_model=None)
async def get_threshold_analysis(
    company_id: _DualId,
    db: AsyncSession = Depends(get_db),
):
    return await wsi_observability_service.get_threshold_analysis(company_id, db)


@router.get("/{company_id}/summary", response_model=None)
async def get_observability_summary(
    company_id: _DualId,
    db: AsyncSession = Depends(get_db),
):
    return await wsi_observability_service.get_observability_summary(company_id, db)

# Task #489 — Keep collection-scoped routes ahead of item-scoped
# routes so a static sibling segment cannot be silently shadowed
# by an {*_id} handler (the Task #455 routing-shadowing bug).
from app.api.v1._path_patterns import reorder_collection_before_item as _reorder_collection_before_item  # noqa: E402

_reorder_collection_before_item(router)
