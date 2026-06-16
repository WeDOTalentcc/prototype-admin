"""Contract tests — multi-tenancy fail-closed in job_management touchpoints.

Locks the canonical pattern enforced 2026-05-22 (ratchet job_management module):
- rails_sync endpoints + conversational JobDraft helpers MUST include explicit
  ``company_id == company_id`` filter in addition to Postgres RLS at session level.
- TENANT-EXEMPT markers MUST stay within sensor window for known-safe queries
  (system-wide warm-ups, cross-domain aggregators).

Strategy: AST-level structural assertions (cheap, deterministic, no DB fixtures).
Cross-tenant DB integration tests live separately in test_multi_tenant_isolation_contract.

References:
- CLAUDE.md REGRA #1 multi-tenancy (company_id from JWT, never payload)
- scripts/check_query_has_tenant_filter.py B.1 sensor
"""
from __future__ import annotations

import ast
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text()


def _has_company_id_in_where(source: str, fn_name: str) -> bool:
    """Return True if function fn_name has a ``.where(... company_id ...)``."""
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == fn_name:
            body_src = ast.unparse(node)
            return "company_id" in body_src and "Candidate.company_id" in body_src or "JobVacancy.company_id" in body_src or "JobDraft.company_id" in body_src
    return False


# ──────────────────────────────────────────────────────────────────────────
# rails_sync.py — service-to-service endpoints must filter by company_id
# ──────────────────────────────────────────────────────────────────────────


class TestRailsSyncTenantIsolation:
    """rails_sync endpoints carry company_id via Depends(require_company_id);
    queries must use it as explicit WHERE filter.

    Canonical refactor 2026-05-22: SQL moved from controller to
    RailsSyncRepository (ADR-001). Sensors now grep BOTH layers:
    - Controller: must CALL the tenant-scoped repo method (e.g.
      get_candidate_for_company), proving company_id flows through.
    - Repository: must execute the WHERE filter explicitly.
    """

    def test_get_candidate_enrichment_filters_company(self):
        controller_src = _read("app/api/v1/rails_sync.py")
        repo_src = _read("app/domains/ats_integration/repositories/rails_sync_repository.py")

        # Controller must delegate to tenant-scoped repo method (ADR-001).
        assert "get_candidate_for_company(candidate_id, company_id)" in controller_src, (
            "rails_sync.py:get_candidate_enrichment MUST call "
            "RailsSyncRepository.get_candidate_for_company(candidate_id, company_id) "
            "(ADR-001 + multi-tenancy fail-closed)"
        )
        # Repository must enforce the WHERE clause.
        assert "Candidate.company_id == company_id" in repo_src, (
            "RailsSyncRepository.get_candidate_for_company MUST filter Candidate "
            "by company_id (multi-tenancy fail-closed, defense-in-depth on top of RLS)"
        )

    def test_get_job_intelligence_filters_company(self):
        controller_src = _read("app/api/v1/rails_sync.py")
        repo_src = _read("app/domains/ats_integration/repositories/rails_sync_repository.py")

        # Controller must delegate to tenant-scoped repo method.
        assert "get_job_for_company(job_id, company_id)" in controller_src, (
            "rails_sync.py:get_job_intelligence MUST call "
            "RailsSyncRepository.get_job_for_company(job_id, company_id)"
        )
        assert "JobVacancy.company_id == company_id" in repo_src, (
            "RailsSyncRepository.get_job_for_company MUST filter JobVacancy by company_id"
        )

    def test_bulk_sync_candidates_filters_company(self):
        controller_src = _read("app/api/v1/rails_sync.py")
        repo_src = _read("app/domains/ats_integration/repositories/rails_sync_repository.py")

        # Controller must delegate to tenant-scoped bulk repo method.
        assert "list_candidates_by_ids_for_company(candidate_ids, company_id)" in controller_src, (
            "rails_sync.py:bulk_sync_candidates MUST call "
            "RailsSyncRepository.list_candidates_by_ids_for_company(candidate_ids, company_id)"
        )
        # Repository must filter Candidate by company_id in BOTH single + bulk paths.
        assert repo_src.count("Candidate.company_id == company_id") >= 2, (
            "RailsSyncRepository: both single-candidate and bulk-sync queries must "
            "filter by company_id (count >= 2 expected)"
        )


# ──────────────────────────────────────────────────────────────────────────
# conversational.py — JobDraft queries must filter by company_id
# ──────────────────────────────────────────────────────────────────────────


class TestConversationalJobDraftIsolation:
    """JobDraft is tenant-scoped; user/recruiter_id filter alone is insufficient."""

    def test_active_draft_helper_takes_company_id(self):
        src = _read("app/api/v1/lia_assistant/conversational.py")
        # Helper signature now requires company_id
        assert "_get_active_draft_for_user(" in src
        assert "company_id: str" in src, (
            "conversational._get_active_draft_for_user MUST accept company_id parameter "
            "(canonical signature change 2026-05-22)"
        )

    def test_all_jobdraft_queries_filter_company(self):
        src = _read("app/api/v1/lia_assistant/conversational.py")
        # Expect company_id filter in all 3 JobDraft select sites
        needle = "JobDraft.company_id == company_id"
        count = src.count(needle)
        assert count >= 3, (
            f"conversational.py: all 3 JobDraft.select sites must include "
            f"{needle} (found {count})"
        )


# ──────────────────────────────────────────────────────────────────────────
# EXEMPT markers must stay within sensor window
# ──────────────────────────────────────────────────────────────────────────


class TestTenantExemptWindowCompliance:
    """EXEMPT marker pattern only works within 5-line window above the select call.
    This ratchet sprint moved markers closer to the queries."""

    def test_embedding_cache_warmup_has_local_marker(self):
        src = _read("app/domains/ai/services/embedding_cache_service.py")
        # The select(JobVacancy) for warm-up needs TENANT-EXEMPT marker within 5 lines above
        lines = src.split("\n")
        for i, line in enumerate(lines):
            if "select(JobVacancy)" in line and "limit(100)" in "\n".join(lines[i:i+5]):
                window = "\n".join(lines[max(0, i-5):i])
                assert "TENANT-EXEMPT" in window or "ADR-001-EXEMPT" in window, (
                    f"embedding_cache_service.py:{i+1} select(JobVacancy) warm-up MUST have "
                    f"TENANT-EXEMPT marker within 5 lines above"
                )
                return
        pytest.fail("Could not locate the warm-up select(JobVacancy) in embedding_cache_service.py")

    def test_bulk_actions_get_job_vacancy_has_marker(self):
        src = _read("app/domains/bulk_actions/repositories/bulk_actions_repository.py")
        lines = src.split("\n")
        for i, line in enumerate(lines):
            if "async def get_job_vacancy_by_id" in line:
                window = "\n".join(lines[i:i+10])
                assert "TENANT-EXEMPT" in window, (
                    "bulk_actions_repository.get_job_vacancy_by_id MUST carry TENANT-EXEMPT "
                    "marker explaining RLS-via-get_tenant_db contract"
                )
                return
        pytest.fail("Could not locate get_job_vacancy_by_id in bulk_actions_repository.py")
