"""
Contract tests — Rails Sync API (`/api/v1/rails-sync/*`).

Locks the wire format consumed by the Rails ATS so changes that drift the
shape (or strip provenance fields) fail in CI rather than in production.

Covered:
- Pydantic schemas in ``libs/schemas/ats`` instantiate with documented shapes.
- All four endpoints in ``app/api/v1/rails_sync.py`` declare a
  ``response_model`` (ADR-005).
- Controller does not perform direct ``db.execute`` (ADR-001) — all DB access
  flows through ``RailsSyncRepository``.
"""
from __future__ import annotations

import inspect
from datetime import datetime, timezone
from pathlib import Path

import pytest

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


# ──────────────────────────────────────────────────────────────────────────
# Schema shape contracts
# ──────────────────────────────────────────────────────────────────────────


def _now() -> datetime:
    return datetime.now(timezone.utc)


class TestRailsSyncSchemas:
    def test_candidate_enrichment_minimum_fields(self):
        payload = CandidateEnrichmentResponse(
            candidate_id="abc",
            synced_at=_now(),
        )
        data = payload.model_dump()
        assert data["source"] == "fastapi"
        assert data["candidate_id"] == "abc"
        assert "wsi" in data and "ai_insights" in data

    def test_candidate_enrichment_full_payload_roundtrip(self):
        payload = CandidateEnrichmentResponse(
            candidate_id="cand-1",
            name="Ada",
            email="ada@example.com",
            status="active",
            wsi=CandidateWSIData(wsi_score=0.91, screening_result={"ok": True}),
            ai_insights=CandidateAIInsights(
                ai_summary="strong",
                skills_extracted=["python"],
                has_embedding=True,
            ),
            synced_at=_now(),
        )
        roundtrip = CandidateEnrichmentResponse.model_validate(payload.model_dump())
        assert roundtrip.wsi.wsi_score == 0.91
        assert roundtrip.ai_insights.has_embedding is True

    def test_job_intelligence_defaults(self):
        payload = JobIntelligenceResponse(job_id="job-1", synced_at=_now())
        assert isinstance(payload.sourcing_data, JobSourcingData)
        assert isinstance(payload.saturation, JobSaturationData)
        assert payload.sourcing_data.channels == []

    def test_compliance_status_envelope(self):
        now = _now()
        payload = ComplianceStatusResponse(
            audit=ComplianceAuditBlock(last_check=now),
            platform_stats=ComplianceStatsBlock(total_candidates=42, total_jobs=7),
            lgpd=ComplianceLGPDBlock(),
            synced_at=now,
        )
        data = payload.model_dump()
        assert data["lgpd"]["status"] == "compliant"
        assert data["platform_stats"]["total_candidates"] == 42
        assert data["audit"]["fairness_guard_active"] is True

    def test_bulk_sync_request_size_bounds(self):
        # min length
        with pytest.raises(Exception):
            BulkSyncCandidatesRequest(candidate_ids=[])
        # max length
        with pytest.raises(Exception):
            BulkSyncCandidatesRequest(candidate_ids=[str(i) for i in range(51)])
        # happy path
        req = BulkSyncCandidatesRequest(candidate_ids=["a", "b"])
        assert req.candidate_ids == ["a", "b"]

    def test_bulk_sync_response_shape(self):
        payload = BulkSyncCandidatesResponse(
            total_requested=2,
            total_found=1,
            total_missing=1,
            enrichments=[
                CandidateEnrichmentItem(
                    candidate_id="a",
                    wsi=CandidateWSIData(wsi_score=0.5),
                ),
            ],
            missing_ids=["b"],
            synced_at=_now(),
        )
        data = payload.model_dump()
        assert data["total_requested"] == 2
        assert data["enrichments"][0]["wsi"]["wsi_score"] == 0.5
        assert data["missing_ids"] == ["b"]


# ──────────────────────────────────────────────────────────────────────────
# Controller architectural contracts (ADR-001, ADR-005)
# ──────────────────────────────────────────────────────────────────────────


class TestRailsSyncControllerArchitecture:
    def test_every_endpoint_declares_response_model(self):
        from app.api.v1.rails_sync import router

        offenders: list[str] = []
        for route in router.routes:
            # APIRoute has response_model; non-API routes (mounts, ws) do not.
            response_model = getattr(route, "response_model", "MISSING")
            if response_model in (None, "MISSING"):
                offenders.append(getattr(route, "path", str(route)))
        assert not offenders, (
            f"rails-sync endpoints missing response_model (ADR-005): {offenders}"
        )

    def test_no_direct_db_execute_in_controller(self):
        """ADR-001 — controllers must delegate to repositories."""
        controller_path = (
            Path(__file__).resolve().parents[2]
            / "app" / "api" / "v1" / "rails_sync.py"
        )
        source = controller_path.read_text(encoding="utf-8")
        # `db.execute(` is the canonical anti-pattern; allow comments mentioning it.
        offenders = [
            line for line in source.splitlines()
            if "db.execute(" in line and not line.lstrip().startswith("#")
        ]
        assert not offenders, (
            "rails_sync.py must delegate DB access to RailsSyncRepository "
            f"(ADR-001). Offending lines: {offenders}"
        )

    def test_rails_sync_repository_is_importable(self):
        from app.domains.ats_integration.repositories.rails_sync_repository import (
            RailsSyncRepository,
        )
        assert inspect.isclass(RailsSyncRepository)
        # All public methods are awaitable
        public = [
            name for name, _ in inspect.getmembers(RailsSyncRepository)
            if not name.startswith("_")
        ]
        assert "get_candidate" in public
        assert "list_candidates_by_ids" in public
        assert "count_candidates" in public
        assert "count_jobs" in public
        assert "count_email_templates" in public

    def test_every_endpoint_excludes_none_for_wire_compat(self):
        """Legacy controller emitted sparse dicts (omitted absent fields).
        New routes must keep that behaviour via response_model_exclude_none=True
        so the Rails consumer never sees brand-new `null` keys."""
        from app.api.v1.rails_sync import router

        offenders: list[str] = []
        for route in router.routes:
            if not getattr(route, "response_model", None):
                continue
            if not getattr(route, "response_model_exclude_none", False):
                offenders.append(getattr(route, "path", str(route)))
        assert not offenders, (
            "rails-sync endpoints must set response_model_exclude_none=True to "
            f"preserve legacy sparse-payload wire format: {offenders}"
        )

    def test_bulk_sync_uses_request_object_for_legacy_400_contract(self):
        """The bulk endpoint must read raw request and raise 400 (not 422) for
        invalid bodies — the Rails consumer depends on the legacy 400 contract."""
        controller_path = (
            Path(__file__).resolve().parents[2]
            / "app" / "api" / "v1" / "rails_sync.py"
        )
        source = controller_path.read_text(encoding="utf-8")
        # bulk endpoint must take Request, not BulkSyncCandidatesRequest as body
        assert "request: Request," in source, (
            "bulk_sync_candidates must accept Request to preserve 400 error contract"
        )
        # Must explicitly raise 400 for body shape errors
        assert 'status_code=400, detail="Invalid JSON body"' in source
        assert 'status_code=400, detail="candidate_ids is required"' in source
