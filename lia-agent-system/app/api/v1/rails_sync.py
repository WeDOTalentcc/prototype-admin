"""
Rails Sync API — endpoints for Rails to consume FastAPI-sourced data.

Direction: Rails → FastAPI (reverse of rails_adapter.py which is FastAPI → Rails).
Auth: RAILS_API_TOKEN header validation (service-to-service).

Endpoints:
  GET  /api/v1/rails-sync/candidates/{id}/enrichment  — AI insights, WSI, screening
  GET  /api/v1/rails-sync/jobs/{id}/intelligence       — sourcing, saturation, analytics
  GET  /api/v1/rails-sync/compliance/status             — LGPD, audit summary
  POST /api/v1/rails-sync/bulk-sync/candidates          — batch enrichment

Architecture:
  - All persistence access goes through ``RailsSyncRepository`` (ADR-001).
  - All responses declare ``response_model`` from ``libs/schemas/ats`` (ADR-005).
"""
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.ats_integration.repositories.rails_sync_repository import (
    RailsSyncRepository,
)
from libs.schemas.ats import (
    BulkSyncCandidatesRequest,
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


def get_rails_sync_repo(db: AsyncSession = Depends(get_db)) -> RailsSyncRepository:
    return RailsSyncRepository(db)


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ──────────────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────────────


@router.get(
    "/candidates/{candidate_id}/enrichment",
    response_model=CandidateEnrichmentResponse,
    response_model_exclude_none=True,
)
async def get_candidate_enrichment(
    candidate_id: str,
    token: str = Depends(verify_rails_token),
    repo: RailsSyncRepository = Depends(get_rails_sync_repo),
) -> CandidateEnrichmentResponse:
    _check_rate_limit()
    _audit_log("candidates.enrichment", {"candidate_id": candidate_id})

    candidate = await repo.get_candidate(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    wsi = CandidateWSIData(
        wsi_score=getattr(candidate, "wsi_score", None),
        wsi_report=getattr(candidate, "wsi_report", None),
        screening_result=getattr(candidate, "screening_result", None),
    )
    ai_insights = CandidateAIInsights(
        ai_summary=getattr(candidate, "ai_summary", None),
        skills_extracted=getattr(candidate, "skills_extracted", None),
        has_embedding=(
            True if getattr(candidate, "embedding_vector", None) is not None else None
        ),
    )

    return CandidateEnrichmentResponse(
        candidate_id=candidate_id,
        name=getattr(candidate, "name", None),
        email=getattr(candidate, "email", None),
        status=getattr(candidate, "status", None),
        wsi=wsi,
        ai_insights=ai_insights,
        synced_at=_now(),
    )


@router.get(
    "/jobs/{job_id}/intelligence",
    response_model=JobIntelligenceResponse,
    response_model_exclude_none=True,
)
async def get_job_intelligence(
    job_id: str,
    token: str = Depends(verify_rails_token),
    repo: RailsSyncRepository = Depends(get_rails_sync_repo),
) -> JobIntelligenceResponse:
    _check_rate_limit()
    _audit_log("jobs.intelligence", {"job_id": job_id})

    job = await repo.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobIntelligenceResponse(
        job_id=job_id,
        title=getattr(job, "title", None),
        status=getattr(job, "status", None),
        company_id=getattr(job, "company_id", None),
        sourcing_data=JobSourcingData(
            channels=getattr(job, "sourcing_channels", None) or [],
        ),
        saturation=JobSaturationData(
            market_available=getattr(job, "market_candidates", None),
            saturation_score=getattr(job, "saturation_score", None),
        ),
        synced_at=_now(),
    )


@router.get(
    "/compliance/status",
    response_model=ComplianceStatusResponse,
    response_model_exclude_none=True,
)
async def get_compliance_status(
    token: str = Depends(verify_rails_token),
    repo: RailsSyncRepository = Depends(get_rails_sync_repo),
) -> ComplianceStatusResponse:
    _check_rate_limit()
    _audit_log("compliance.status", {})

    total_candidates = await repo.count_candidates()
    total_jobs = await repo.count_jobs()
    total_templates = await repo.count_email_templates()

    now = _now()
    return ComplianceStatusResponse(
        lgpd=ComplianceLGPDBlock(),
        platform_stats=ComplianceStatsBlock(
            total_candidates=total_candidates,
            total_jobs=total_jobs,
            total_email_templates=total_templates,
        ),
        audit=ComplianceAuditBlock(last_check=now),
        synced_at=now,
    )


@router.post(
    "/bulk-sync/candidates",
    response_model=BulkSyncCandidatesResponse,
    response_model_exclude_none=True,
)
async def bulk_sync_candidates(
    request: Request,
    token: str = Depends(verify_rails_token),
    repo: RailsSyncRepository = Depends(get_rails_sync_repo),
) -> BulkSyncCandidatesResponse:
    _check_rate_limit()

    # Preserve legacy 400-with-message error contract instead of FastAPI's
    # default 422 for body validation. Rails ATS depends on the 400 codes.
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

    try:
        payload = BulkSyncCandidatesRequest(candidate_ids=[str(c) for c in candidate_ids])
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    candidate_ids = payload.candidate_ids
    _audit_log("bulk-sync.candidates", {"count": len(candidate_ids)})

    candidates = await repo.list_candidates_by_ids(candidate_ids)
    found_ids = {str(getattr(c, "id", "")) for c in candidates}

    enrichments = [
        CandidateEnrichmentItem(
            candidate_id=str(getattr(c, "id", "")),
            name=getattr(c, "name", None),
            email=getattr(c, "email", None),
            status=getattr(c, "status", None),
            wsi=CandidateWSIData(
                wsi_score=getattr(c, "wsi_score", None),
                screening_result=getattr(c, "screening_result", None),
            ),
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
        synced_at=_now(),
    )
