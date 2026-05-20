"""
Bulk Job Import endpoint — onboarding use case.

POST /api/v1/jobs/bulk-import
  Imports historical job descriptions to seed the salary benchmark from day 1.
  company_id always from JWT (never from payload).
  Returns HTTP 207 if any individual JD failed.

GET  /api/v1/jobs/bulk-import/{batch_id}/status
  Polls import batch progress.
"""
from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.auth.dependencies import get_current_user, get_user_company_id
from app.auth.models import User
from app.core.database import get_db
from app.domains.job_management.services.jd_import_service import JDImportService
from lia_models.imported_job_description import ImportBatch, ImportStatus
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["bulk-import"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class JDItem(BaseModel):
    title: str
    department: str | None = None
    seniority: str | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    skills: list[str] = Field(default_factory=list)
    description: str | None = None
    external_id: str | None = None
    hiring_manager_email: str | None = None
    status: str | None = None


class BulkImportRequest(WeDoBaseModel):
    source: str = Field("spreadsheet", description="gupy | pandape | greenhouse | spreadsheet | manual_upload")
    jobs: list[JDItem] = Field(..., min_length=1, max_length=500)


class BatchItemStatus(BaseModel):
    index: int
    title: str
    status: str  # "ok" | "failed"
    error: str | None = None


class BulkImportResponse(BaseModel):
    batch_id: str
    total: int
    successful: int
    failed: int
    status: str
    items: list[BatchItemStatus] = Field(default_factory=list)


class BatchStatusResponse(BaseModel):
    batch_id: str
    status: str
    total_records: int
    processed_records: int
    successful_records: int
    failed_records: int
    started_at: str | None
    completed_at: str | None
    errors: list[dict] = Field(default_factory=list)


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post(
    "/bulk-import",
    summary="Import historical job descriptions (onboarding)",
    description=(
        "Imports historical JDs to seed the salary benchmark from day 1. "
        "Quality gate: only JDs with score >= 0.65 are used for learning. "
        "Returns HTTP 207 if any individual JD failed."
    ),
)
async def bulk_import_jobs(
    request: BulkImportRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
company_id: str = Depends(require_company_id)) -> JSONResponse:
    # company_id always from JWT — never from payload
    company_id: UUID = get_user_company_id(user)
    if not company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="company_id missing from token")

    jds_data = [j.model_dump(exclude_none=True) for j in request.jobs]
    # Rename "skills" key to "required_skills" so quality gate picks it up
    for jd in jds_data:
        if "skills" in jd:
            jd["required_skills"] = jd.pop("skills")

    service = JDImportService()
    batch = await service.import_batch_jds(
        db=db,
        company_id=company_id,
        jds_data=jds_data,
        source=request.source,
        created_by=str(user.id) if hasattr(user, "id") else None,
    )

    # Build per-item status list from batch errors
    error_map = {e.get("jd_title", ""): e.get("error", "unknown") for e in (batch.errors or [])}
    items = []
    for idx, jd in enumerate(request.jobs):
        err = error_map.get(jd.title)
        items.append(BatchItemStatus(
            index=idx,
            title=jd.title,
            status="failed" if err else "ok",
            error=err,
        ))

    resp = BulkImportResponse(
        batch_id=str(batch.id),
        total=batch.total_records,
        successful=batch.successful_records,
        failed=batch.failed_records,
        status=batch.status,
        items=items,
    )

    http_status = status.HTTP_207_MULTI_STATUS if batch.failed_records > 0 else status.HTTP_200_OK
    return JSONResponse(content=resp.model_dump(), status_code=http_status)


@router.get(
    "/bulk-import/{batch_id}/status",
    response_model=BatchStatusResponse,
    summary="Poll import batch status",
)
async def get_import_batch_status(
    batch_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
company_id: str = Depends(require_company_id)) -> BatchStatusResponse:
    company_id: UUID = get_user_company_id(user)

    result = await db.execute(
        select(ImportBatch).where(
            ImportBatch.id == batch_id,
            ImportBatch.company_id == company_id,  # tenant isolation
        )
    )
    batch = result.scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")

    return BatchStatusResponse(
        batch_id=str(batch.id),
        status=batch.status,
        total_records=batch.total_records,
        processed_records=batch.processed_records,
        successful_records=batch.successful_records,
        failed_records=batch.failed_records,
        started_at=batch.started_at.isoformat() if batch.started_at else None,
        completed_at=batch.completed_at.isoformat() if batch.completed_at else None,
        errors=batch.errors or [],
    )
