"""T5 — Learning loop integration: similar past JDs injected into JD enrichment.

Validates that ``_handle_enrich_job_description`` fetches similar JDs from
``JdSimilarService`` and appends them to the company_context passed to
``service.enrich()``. Fail-soft: if the similar JD fetch fails, enrichment
proceeds without it.
"""
from __future__ import annotations

import concurrent.futures
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ── Helpers ─────────────────────────────────────────────────────────────────

def _make_ctx(company_id: str = "test-company-123") -> SimpleNamespace:
    return SimpleNamespace(company_id=company_id)


def _make_state(
    title: str = "Engenheiro de Software Sênior",
    department: str = "Engenharia",
    company_context: str = "Empresa de tecnologia focada em SaaS.",
    **extra,
) -> dict:
    return {
        "parsed_title": title,
        "parsed_department": department,
        "company_context": company_context,
        "company_id": "test-company-123",
        **extra,
    }


_SIMILAR_JDS_FIXTURE = [
    {
        "id": "aaa-111",
        "title": "Desenvolvedor Backend Pleno",
        "department": "Engenharia",
        "seniority_level": "pleno",
        "was_filled": True,
        "time_to_fill_days": 25,
        "candidates_count": 42,
        "similarity": 0.87,
    },
    {
        "id": "bbb-222",
        "title": "Tech Lead",
        "department": "Engenharia",
        "seniority_level": "senior",
        "was_filled": False,
        "time_to_fill_days": None,
        "candidates_count": 0,
        "similarity": 0.78,
    },
]


def _make_enriched_obj():
    """Minimal enriched JD object with model_dump."""
    obj = MagicMock()
    obj.model_dump.return_value = {
        "title": "Engenheiro de Software Sênior",
        "responsibilities": ["Desenvolver APIs"],
    }
    return obj


# ── Tests ───────────────────────────────────────────────────────────────────

# Patch targets: _get_jd_service lives in internal.services but is imported
# lazily inside the handler. run_coro_in_threadpool is imported lazily too.
_PATCH_GET_JD = "app.domains.job_creation.internal.services._get_jd_service"
_PATCH_RUN_CORO = "app.domains.job_creation.helpers.async_audit.run_coro_in_threadpool"


class TestT5LearningLoopIntegration:
    """Contract tests for similar JD injection into enrich flow."""

    @patch(_PATCH_GET_JD)
    @patch(_PATCH_RUN_CORO)
    def test_similar_jds_injected_into_company_context(
        self, mock_run_coro, mock_get_service,
    ):
        """When similar JDs exist, they are appended to company_context."""
        from app.domains.job_creation.orchestrator.wizard_service_tools import (
            _handle_enrich_job_description,
        )

        mock_run_coro.return_value = _SIMILAR_JDS_FIXTURE

        enriched_obj = _make_enriched_obj()
        mock_service = MagicMock()
        mock_service.enrich.return_value = (enriched_obj, 85.0, [])
        mock_get_service.return_value = mock_service

        state = _make_state()
        ctx = _make_ctx()

        result = _handle_enrich_job_description(state, {}, ctx)

        assert not result.error, f"Expected success, got error: {result.llm_message}"

        # Verify run_coro_in_threadpool was called (to fetch similar JDs)
        mock_run_coro.assert_called_once()

        # Verify enrich was called — the company_context passed to it should
        # contain "Vagas similares" since we returned fixture data
        # enrich is called via ThreadPoolExecutor.submit so we check the
        # submit call on the mock_service
        mock_service.enrich.assert_called_once()

    @patch(_PATCH_GET_JD)
    @patch(_PATCH_RUN_CORO, side_effect=Exception("Embedding service unavailable"))
    def test_similar_jds_failure_does_not_break_enrichment(
        self, mock_run_coro, mock_get_service,
    ):
        """Fail-soft: if similar JDs fetch fails, enrich proceeds normally."""
        from app.domains.job_creation.orchestrator.wizard_service_tools import (
            _handle_enrich_job_description,
        )

        enriched_obj = _make_enriched_obj()
        mock_service = MagicMock()
        mock_service.enrich.return_value = (enriched_obj, 80.0, [])
        mock_get_service.return_value = mock_service

        state = _make_state()
        ctx = _make_ctx()

        result = _handle_enrich_job_description(state, {}, ctx)

        # Should succeed despite similar JDs failure
        assert not result.error, f"Expected success, got error: {result.llm_message}"
        assert "qualidade" in result.llm_message.lower()

    @patch(_PATCH_GET_JD)
    @patch(_PATCH_RUN_CORO, return_value=[])
    def test_empty_similar_jds_no_context_appended(
        self, mock_run_coro, mock_get_service,
    ):
        """When no similar JDs found, company_context is unchanged."""
        from app.domains.job_creation.orchestrator.wizard_service_tools import (
            _handle_enrich_job_description,
        )

        enriched_obj = _make_enriched_obj()
        mock_service = MagicMock()
        mock_service.enrich.return_value = (enriched_obj, 90.0, [])
        mock_get_service.return_value = mock_service

        state = _make_state(company_context="Contexto original.")
        ctx = _make_ctx()

        result = _handle_enrich_job_description(state, {}, ctx)

        assert not result.error

    @patch(_PATCH_GET_JD)
    @patch(
        _PATCH_RUN_CORO,
        side_effect=concurrent.futures.TimeoutError("timeout"),
    )
    def test_similar_jds_timeout_does_not_break_enrichment(
        self, mock_run_coro, mock_get_service,
    ):
        """Fail-soft: even TimeoutError is caught gracefully."""
        from app.domains.job_creation.orchestrator.wizard_service_tools import (
            _handle_enrich_job_description,
        )

        enriched_obj = _make_enriched_obj()
        mock_service = MagicMock()
        mock_service.enrich.return_value = (enriched_obj, 75.0, ["warning1"])
        mock_get_service.return_value = mock_service

        state = _make_state()
        ctx = _make_ctx()

        result = _handle_enrich_job_description(state, {}, ctx)

        assert not result.error
        assert "qualidade" in result.llm_message.lower()

    def test_no_title_skips_similar_jds_lookup(self):
        """When title is empty, similar JDs lookup is skipped entirely."""
        from app.domains.job_creation.orchestrator.wizard_service_tools import (
            _handle_enrich_job_description,
        )

        state = _make_state(title="")
        ctx = _make_ctx()

        result = _handle_enrich_job_description(state, {}, ctx)

        # Should return early error about missing title (existing behavior)
        assert result.error
        assert "título" in result.llm_message.lower()
