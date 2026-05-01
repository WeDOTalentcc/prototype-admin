"""
WSI Observability API - Read-Only Endpoints for WSI Screening Metrics.

CRITICAL: All endpoints are READ-ONLY. No modifications to WSI configuration.
"""
import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.analytics.services.wsi_observability import wsi_observability_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/wsi-observability",
    tags=["wsi-observability"],
)


@router.get("/{company_id}/correlation", response_model=None)
async def get_score_outcome_correlation(
    company_id: str,
    db: AsyncSession = Depends(get_db),
):
    return await wsi_observability_service.get_score_vs_outcome_correlation(company_id, db)


@router.get("/{company_id}/block-accuracy", response_model=None)
async def get_block_accuracy(
    company_id: str,
    db: AsyncSession = Depends(get_db),
):
    return await wsi_observability_service.get_block_accuracy(company_id, db)


@router.get("/{company_id}/distribution", response_model=None)
async def get_score_distribution(
    company_id: str,
    db: AsyncSession = Depends(get_db),
):
    return await wsi_observability_service.get_score_distribution(company_id, db)


@router.get("/{company_id}/threshold-analysis", response_model=None)
async def get_threshold_analysis(
    company_id: str,
    db: AsyncSession = Depends(get_db),
):
    return await wsi_observability_service.get_threshold_analysis(company_id, db)


@router.get("/{company_id}/summary", response_model=None)
async def get_observability_summary(
    company_id: str,
    db: AsyncSession = Depends(get_db),
):
    return await wsi_observability_service.get_observability_summary(company_id, db)
