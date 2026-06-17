"""
Canonical Pydantic contracts for the ATS integration boundary.

These schemas define the wire contracts between FastAPI (`lia-agent-system`)
and the Rails ATS (`ats-api-copia`). They are used as `response_model` on
`/api/v1/rails-sync/*` endpoints (ADR-005) and as serialization contracts
for any future ATS clients consumed via `ATSProviderFactory`.

Reference: docs/architecture/ARCHITECTURE.md §"ATS Integration Boundary".
"""
from .rails_sync import (
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

__all__ = [
    "BulkSyncCandidatesRequest",
    "BulkSyncCandidatesResponse",
    "CandidateAIInsights",
    "CandidateEnrichmentItem",
    "CandidateEnrichmentResponse",
    "CandidateWSIData",
    "ComplianceAuditBlock",
    "ComplianceLGPDBlock",
    "ComplianceStatsBlock",
    "ComplianceStatusResponse",
    "JobIntelligenceResponse",
    "JobSaturationData",
    "JobSourcingData",
]
