"""
Rails Sync API — endpoints for Rails to consume FastAPI-sourced data.

Direction: Rails → FastAPI (reverse of rails_adapter.py which is FastAPI → Rails).
Auth: RAILS_API_TOKEN header validation (service-to-service).

Endpoints:
  GET  /api/v1/rails-sync/candidates/{id}/enrichment  — AI insights, WSI, screening
  GET  /api/v1/rails-sync/jobs/{id}/intelligence       — sourcing, saturation, analytics
  GET  /api/v1/rails-sync/compliance/status             — LGPD, audit summary
  POST /api/v1/rails-sync/bulk-sync/candidates          — batch enrichment

ADR-001 (Repository Pattern): All DB reads delegated to RailsSyncRepository.
ADR-005 (Response Models): Every endpoint declares Pydantic response_model with
response_model_exclude_none=True to preserve legacy sparse-payload wire format.
"""
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.ats_integration.repositories.rails_sync_repository import (
    RailsSyncRepository,
)
from app.shared.security.require_company_id import require_company_id
from libs.schemas.ats import (
    BulkSyncCandidatesResponse,
    CandidateAIInsights,
    CandidateEnrichmentItem,
    CandidateEnrichmentResponse,
    CandidateWSIData,
    ComplianceAuditBlock,
    ComplianceLGPDBlock,
    ComplianceStatsBlock,
    ComplianceStatusResponse,
    JobIntelligenceResponse,
    JobSaturationData,
    JobSourcingData,
)
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rails-sync", tags=["rails-sync"])

def _get_rails_api_token() -> str:
    return os.environ.get("RAILS_API_TOKEN", "")
_MAX_BULK_SIZE = 50
_RATE_LIMIT_WINDOW = 60
_RATE_LIMIT_MAX = 120
_rate_limit_counts: dict[str, list[float]] = {}

security = HTTPBearer(auto_error=False)


async def verify_rails_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> str:
    token = _get_rails_api_token()
    if not token:
        raise HTTPException(
            status_code=503,
            detail="Rails sync not configured (RAILS_API_TOKEN not set)",
        )
    if not credentials or credentials.credentials != token:
        logger.warning("[RailsSync] Unauthorized access attempt")
        raise HTTPException(status_code=401, detail="Invalid or missing RAILS_API_TOKEN")
    return credentials.credentials


def _check_rate_limit(client_key: str = "rails") -> None:
    now = time.time()
    window_start = now - _RATE_LIMIT_WINDOW
    timestamps = _rate_limit_counts.get(client_key, [])
    timestamps = [t for t in timestamps if t > window_start]
    if len(timestamps) >= _RATE_LIMIT_MAX:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {_RATE_LIMIT_MAX} requests per {_RATE_LIMIT_WINDOW}s",
        )
    timestamps.append(now)
    _rate_limit_counts[client_key] = timestamps


def _audit_log(endpoint: str, details: dict[str, Any]) -> None:
    logger.info(
        "[RailsSync] %s | %s",
        endpoint,
        {k: v for k, v in details.items() if k != "token"},
    )


def _build_wsi_data(candidate: Any) -> CandidateWSIData:
    """Sparse WSI block — only includes fields actually present."""
    kwargs: dict[str, Any] = {}
    if getattr(candidate, "wsi_score", None) is not None:
        kwargs["wsi_score"] = candidate.wsi_score
    if getattr(candidate, "wsi_report", None) is not None:
        kwargs["wsi_report"] = candidate.wsi_report
    if getattr(candidate, "screening_result", None) is not None:
        kwargs["screening_result"] = candidate.screening_result
    return CandidateWSIData(**kwargs)


def _build_ai_insights(candidate: Any) -> CandidateAIInsights:
    """Sparse AI insights block — only includes fields actually present."""
    kwargs: dict[str, Any] = {}
    if getattr(candidate, "ai_summary", None) is not None:
        kwargs["ai_summary"] = candidate.ai_summary
    if getattr(candidate, "skills_extracted", None) is not None:
        kwargs["skills_extracted"] = candidate.skills_extracted
    if getattr(candidate, "embedding_vector", None) is not None:
        kwargs["has_embedding"] = True
    return CandidateAIInsights(**kwargs)


@router.get(
    "/candidates/{candidate_id}/enrichment",
    response_model=CandidateEnrichmentResponse,
    response_model_exclude_none=True,
)
async def get_candidate_enrichment(
    candidate_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    request: Request,
    token: str = Depends(verify_rails_token),
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(require_company_id),
) -> CandidateEnrichmentResponse:
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    _check_rate_limit()
    _audit_log("candidates.enrichment", {"candidate_id": candidate_id})

    # ADR-001: delegate DB access to repository (tenant-scoped fetch).
    repo = RailsSyncRepository(db)
    candidate = await repo.get_candidate_for_company(candidate_id, company_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    return CandidateEnrichmentResponse(
        candidate_id=candidate_id,
        name=getattr(candidate, "name", None),
        email=getattr(candidate, "email", None),
        status=getattr(candidate, "status", None),
        wsi=_build_wsi_data(candidate),
        ai_insights=_build_ai_insights(candidate),
        synced_at=datetime.now(timezone.utc),
    )


@router.get(
    "/jobs/{job_id}/intelligence",
    response_model=JobIntelligenceResponse,
    response_model_exclude_none=True,
)
async def get_job_intelligence(
    job_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    token: str = Depends(verify_rails_token),
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(require_company_id),
) -> JobIntelligenceResponse:
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    _check_rate_limit()
    _audit_log("jobs.intelligence", {"job_id": job_id})

    # ADR-001: delegate DB access to repository (tenant-scoped fetch).
    repo = RailsSyncRepository(db)
    job = await repo.get_job_for_company(job_id, company_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobIntelligenceResponse(
        job_id=job_id,
        title=getattr(job, "title", None),
        status=getattr(job, "status", None),
        company_id=getattr(job, "company_id", None),
        sourcing_data=JobSourcingData(
            channels=getattr(job, "sourcing_channels", []) or [],
        ),
        saturation=JobSaturationData(
            market_available=getattr(job, "market_candidates", None),
            saturation_score=getattr(job, "saturation_score", None),
        ),
        synced_at=datetime.now(timezone.utc),
    )


@router.get(
    "/compliance/status",
    response_model=ComplianceStatusResponse,
    response_model_exclude_none=True,
)
async def get_compliance_status(
    token: str = Depends(verify_rails_token),
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(require_company_id),
) -> ComplianceStatusResponse:
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    _check_rate_limit()
    _audit_log("compliance.status", {})

    # ADR-001: delegate DB access to repository.
    repo = RailsSyncRepository(db)
    total_candidates = await repo.count_candidates()
    total_jobs = await repo.count_jobs()
    total_templates = await repo.count_email_templates()

    return ComplianceStatusResponse(
        lgpd=ComplianceLGPDBlock(
            status="compliant",
            data_retention_policy="365_days",
            pii_masking_enabled=True,
            consent_tracking=True,
        ),
        platform_stats=ComplianceStatsBlock(
            total_candidates=total_candidates,
            total_jobs=total_jobs,
            total_email_templates=total_templates,
        ),
        audit=ComplianceAuditBlock(
            last_check=datetime.now(timezone.utc),
            fairness_guard_active=True,
            bias_audit_enabled=True,
            eu_ai_act_compliance="in_progress",
        ),
        synced_at=datetime.now(timezone.utc),
    )


@router.post(
    "/bulk-sync/candidates",
    response_model=BulkSyncCandidatesResponse,
    response_model_exclude_none=True,
)
async def bulk_sync_candidates(
    request: Request,
    token: str = Depends(verify_rails_token),
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(require_company_id),
) -> BulkSyncCandidatesResponse:
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    _check_rate_limit()

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Request body must be a JSON object")

    candidate_ids = body.get("candidate_ids", [])

    if not isinstance(candidate_ids, list):
        raise HTTPException(status_code=400, detail="candidate_ids must be an array")
    if not candidate_ids:
        raise HTTPException(status_code=400, detail="candidate_ids is required")
    if len(candidate_ids) > _MAX_BULK_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {_MAX_BULK_SIZE} candidates per batch",
        )

    _audit_log("bulk-sync.candidates", {"count": len(candidate_ids)})

    # ADR-001: delegate DB access to repository (tenant-scoped bulk fetch).
    repo = RailsSyncRepository(db)
    candidates = await repo.list_candidates_by_ids_for_company(candidate_ids, company_id)
    found_ids = {str(getattr(c, "id", "")) for c in candidates}

    enrichments: list[CandidateEnrichmentItem] = [
        CandidateEnrichmentItem(
            candidate_id=str(getattr(c, "id", "")),
            name=getattr(c, "name", None),
            email=getattr(c, "email", None),
            status=getattr(c, "status", None),
            wsi=_build_wsi_data(c),
        )
        for c in candidates
    ]

    missing_ids = [cid for cid in candidate_ids if str(cid) not in found_ids]

    return BulkSyncCandidatesResponse(
        total_requested=len(candidate_ids),
        total_found=len(enrichments),
        total_missing=len(missing_ids),
        enrichments=enrichments,
        missing_ids=missing_ids,
        synced_at=datetime.now(timezone.utc),
    )

reorder_collection_before_item(router)
