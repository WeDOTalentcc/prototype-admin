"""
Pydantic contracts for the Rails → FastAPI sync surface.

Endpoints covered (see `app/api/v1/rails_sync.py`):
  GET  /api/v1/rails-sync/candidates/{id}/enrichment
  GET  /api/v1/rails-sync/jobs/{id}/intelligence
  GET  /api/v1/rails-sync/compliance/status
  POST /api/v1/rails-sync/bulk-sync/candidates

All response schemas embed a `source: Literal["fastapi"]` and an ISO-8601
`synced_at` field so the Rails consumer can audit provenance.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


# ──────────────────────────────────────────────────────────────────────────
# Shared mixin
# ──────────────────────────────────────────────────────────────────────────


class _RailsSyncEnvelope(BaseModel):
    """Provenance fields stamped on every rails-sync response."""

    source: Literal["fastapi"] = "fastapi"
    synced_at: datetime


# ──────────────────────────────────────────────────────────────────────────
# Candidate enrichment
# ──────────────────────────────────────────────────────────────────────────


class CandidateWSIData(BaseModel):
    wsi_score: float | None = None
    wsi_report: dict[str, Any] | None = None
    screening_result: dict[str, Any] | None = None


class CandidateAIInsights(BaseModel):
    ai_summary: str | None = None
    skills_extracted: list[str] | dict[str, Any] | None = None
    has_embedding: bool | None = None


class CandidateEnrichmentResponse(_RailsSyncEnvelope):
    candidate_id: str
    name: str | None = None
    email: str | None = None
    status: str | None = None
    wsi: CandidateWSIData = Field(default_factory=CandidateWSIData)
    ai_insights: CandidateAIInsights = Field(default_factory=CandidateAIInsights)


# ──────────────────────────────────────────────────────────────────────────
# Job intelligence
# ──────────────────────────────────────────────────────────────────────────


class JobSourcingData(BaseModel):
    channels: list[str] = Field(default_factory=list)


class JobSaturationData(BaseModel):
    market_available: int | None = None
    saturation_score: float | None = None


class JobIntelligenceResponse(_RailsSyncEnvelope):
    job_id: str
    title: str | None = None
    status: str | None = None
    company_id: str | None = None
    sourcing_data: JobSourcingData = Field(default_factory=JobSourcingData)
    saturation: JobSaturationData = Field(default_factory=JobSaturationData)


# ──────────────────────────────────────────────────────────────────────────
# Compliance status
# ──────────────────────────────────────────────────────────────────────────


class ComplianceLGPDBlock(BaseModel):
    status: Literal["compliant", "in_progress", "non_compliant"] = "compliant"
    data_retention_policy: str = "365_days"
    pii_masking_enabled: bool = True
    consent_tracking: bool = True


class ComplianceStatsBlock(BaseModel):
    total_candidates: int = 0
    total_jobs: int = 0
    total_email_templates: int = 0


class ComplianceAuditBlock(BaseModel):
    last_check: datetime
    fairness_guard_active: bool = True
    bias_audit_enabled: bool = True
    eu_ai_act_compliance: Literal["compliant", "in_progress", "not_started"] = "in_progress"


class ComplianceStatusResponse(_RailsSyncEnvelope):
    lgpd: ComplianceLGPDBlock = Field(default_factory=ComplianceLGPDBlock)
    platform_stats: ComplianceStatsBlock = Field(default_factory=ComplianceStatsBlock)
    audit: ComplianceAuditBlock


# ──────────────────────────────────────────────────────────────────────────
# Bulk sync
# ──────────────────────────────────────────────────────────────────────────


class BulkSyncCandidatesRequest(BaseModel):
    candidate_ids: list[str] = Field(..., min_length=1, max_length=50)


class CandidateEnrichmentItem(BaseModel):
    candidate_id: str
    name: str | None = None
    email: str | None = None
    status: str | None = None
    wsi: CandidateWSIData = Field(default_factory=CandidateWSIData)


class BulkSyncCandidatesResponse(_RailsSyncEnvelope):
    total_requested: int
    total_found: int
    total_missing: int
    enrichments: list[CandidateEnrichmentItem]
    missing_ids: list[str]
