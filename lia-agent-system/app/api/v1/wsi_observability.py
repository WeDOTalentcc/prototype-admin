"""
WSI Observability API - Read-Only Endpoints for WSI Screening Metrics.

CRITICAL: All endpoints are READ-ONLY. No modifications to WSI configuration.
"""
import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.analytics.services.wsi_observability import wsi_observability_service
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/wsi-observability",
    tags=["wsi-observability"],
)


@router.get("/{company_id}/correlation", response_model=None)
async def get_score_outcome_correlation(
    company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    return await wsi_observability_service.get_score_vs_outcome_correlation(company_id, db)


@router.get("/{company_id}/block-accuracy", response_model=None)
async def get_block_accuracy(
    company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    return await wsi_observability_service.get_block_accuracy(company_id, db)


@router.get("/{company_id}/distribution", response_model=None)
async def get_score_distribution(
    company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    return await wsi_observability_service.get_score_distribution(company_id, db)


@router.get("/{company_id}/threshold-analysis", response_model=None)
async def get_threshold_analysis(
    company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    return await wsi_observability_service.get_threshold_analysis(company_id, db)


@router.get("/{company_id}/summary", response_model=None)
async def get_observability_summary(
    company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    return await wsi_observability_service.get_observability_summary(company_id, db)

reorder_collection_before_item(router)
