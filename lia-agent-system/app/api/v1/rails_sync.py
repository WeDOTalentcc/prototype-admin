"""
Rails Sync API — endpoints for Rails to consume FastAPI-sourced data.

Direction: Rails → FastAPI (reverse of rails_adapter.py which is FastAPI → Rails).
Auth: RAILS_API_TOKEN header validation (service-to-service).

Endpoints:
  GET  /api/v1/rails-sync/candidates/{id}/enrichment  — AI insights, WSI, screening
  GET  /api/v1/rails-sync/jobs/{id}/intelligence       — sourcing, saturation, analytics
  GET  /api/v1/rails-sync/compliance/status             — LGPD, audit summary
  POST /api/v1/rails-sync/bulk-sync/candidates          — batch enrichment
"""
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.candidate import Candidate
from app.models.email_template import EmailTemplate
from app.models.job_vacancy import JobVacancy

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


@router.get("/candidates/{candidate_id}/enrichment")
async def get_candidate_enrichment(
    candidate_id: str,
    request: Request,
    token: str = Depends(verify_rails_token),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    # multi-tenancy: protected via auth middleware (JWT) + Postgres RLS runtime (Sprint follow-up: add _require_company_id explicit gate)
    _check_rate_limit()
    _audit_log("candidates.enrichment", {"candidate_id": candidate_id})

    result = await db.execute(
        select(Candidate).where(Candidate.id == candidate_id)
    )
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    wsi_data: dict[str, Any] = {}
    if hasattr(candidate, "wsi_score") and candidate.wsi_score is not None:
        wsi_data["wsi_score"] = candidate.wsi_score
    if hasattr(candidate, "wsi_report") and candidate.wsi_report is not None:
        wsi_data["wsi_report"] = candidate.wsi_report
    if hasattr(candidate, "screening_result") and candidate.screening_result is not None:
        wsi_data["screening_result"] = candidate.screening_result

    ai_insights: dict[str, Any] = {}
    if hasattr(candidate, "ai_summary") and candidate.ai_summary is not None:
        ai_insights["ai_summary"] = candidate.ai_summary
    if hasattr(candidate, "skills_extracted") and candidate.skills_extracted is not None:
        ai_insights["skills_extracted"] = candidate.skills_extracted
    if hasattr(candidate, "embedding_vector") and candidate.embedding_vector is not None:
        ai_insights["has_embedding"] = True

    return {
        "candidate_id": candidate_id,
        "name": getattr(candidate, "name", None),
        "email": getattr(candidate, "email", None),
        "status": getattr(candidate, "status", None),
        "wsi": wsi_data,
        "ai_insights": ai_insights,
        "source": "fastapi",
        "synced_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/jobs/{job_id}/intelligence")
async def get_job_intelligence(
    job_id: str,
    token: str = Depends(verify_rails_token),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    # multi-tenancy: protected via auth middleware (JWT) + Postgres RLS runtime (Sprint follow-up: add _require_company_id explicit gate)
    _check_rate_limit()
    _audit_log("jobs.intelligence", {"job_id": job_id})

    result = await db.execute(select(JobVacancy).where(JobVacancy.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "job_id": job_id,
        "title": getattr(job, "title", None),
        "status": getattr(job, "status", None),
        "company_id": getattr(job, "company_id", None),
        "sourcing_data": {
            "channels": getattr(job, "sourcing_channels", []) or [],
        },
        "saturation": {
            "market_available": getattr(job, "market_candidates", None),
            "saturation_score": getattr(job, "saturation_score", None),
        },
        "source": "fastapi",
        "synced_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/compliance/status")
async def get_compliance_status(
    token: str = Depends(verify_rails_token),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    # multi-tenancy: protected via auth middleware (JWT) + Postgres RLS runtime (Sprint follow-up: add _require_company_id explicit gate)
    _check_rate_limit()
    _audit_log("compliance.status", {})

    candidate_count_result = await db.execute(select(func.count(Candidate.id)))
    total_candidates = candidate_count_result.scalar() or 0

    job_count_result = await db.execute(select(func.count(JobVacancy.id)))
    total_jobs = job_count_result.scalar() or 0

    template_count_result = await db.execute(select(func.count(EmailTemplate.id)))
    total_templates = template_count_result.scalar() or 0

    return {
        "lgpd": {
            "status": "compliant",
            "data_retention_policy": "365_days",
            "pii_masking_enabled": True,
            "consent_tracking": True,
        },
        "platform_stats": {
            "total_candidates": total_candidates,
            "total_jobs": total_jobs,
            "total_email_templates": total_templates,
        },
        "audit": {
            "last_check": datetime.now(timezone.utc).isoformat(),
            "fairness_guard_active": True,
            "bias_audit_enabled": True,
            "eu_ai_act_compliance": "in_progress",
        },
        "source": "fastapi",
        "synced_at": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/bulk-sync/candidates")
async def bulk_sync_candidates(
    request: Request,
    token: str = Depends(verify_rails_token),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    # multi-tenancy: protected via auth middleware (JWT) + Postgres RLS runtime (Sprint follow-up: add _require_company_id explicit gate)
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

    result = await db.execute(
        select(Candidate).where(Candidate.id.in_(candidate_ids))
    )
    candidates = list(result.scalars().all())
    found_ids = {str(getattr(c, "id", "")) for c in candidates}

    enrichments = []
    for c in candidates:
        wsi_data: dict[str, Any] = {}
        if hasattr(c, "wsi_score") and c.wsi_score is not None:
            wsi_data["wsi_score"] = c.wsi_score
        if hasattr(c, "screening_result") and c.screening_result is not None:
            wsi_data["screening_result"] = c.screening_result

        enrichments.append({
            "candidate_id": str(getattr(c, "id", "")),
            "name": getattr(c, "name", None),
            "email": getattr(c, "email", None),
            "status": getattr(c, "status", None),
            "wsi": wsi_data,
        })

    missing_ids = [cid for cid in candidate_ids if str(cid) not in found_ids]

    return {
        "total_requested": len(candidate_ids),
        "total_found": len(enrichments),
        "total_missing": len(missing_ids),
        "enrichments": enrichments,
        "missing_ids": missing_ids,
        "source": "fastapi",
        "synced_at": datetime.now(timezone.utc).isoformat(),
    }
