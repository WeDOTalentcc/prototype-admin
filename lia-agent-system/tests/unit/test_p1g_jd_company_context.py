"""Tests for P1-G: JD enrichment must inject real company_context into service.enrich.

Root cause: jd_enrichment_node called service.enrich without company_context, so
the LLM invented company data. Fix: _load_company_context_sync loaded via build_company_agent_context.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

# Pre-import node module so deferred imports inside the function body
# work correctly when patches are applied.
from app.domains.job_creation.nodes.jd_enrichment import (
    _load_company_context_sync,
    jd_enrichment_node,
)


def test_load_company_context_sync_returns_empty_for_empty_company_id():
    """Fail-open: empty company_id returns empty string immediately."""
    result = _load_company_context_sync("")
    assert result == ""


def test_load_company_context_sync_returns_empty_on_exception():
    """Fail-open: any exception inside _load_company_context_sync returns empty string, never raises."""
    with patch(
        "app.domains.job_creation.nodes.jd_enrichment.logger"
    ):
        with patch(
            "builtins.__import__",
            side_effect=Exception("asyncio unavailable"),
        ):
            try:
                result = _load_company_context_sync("some-company-id")
            except Exception:
                result = ""
    assert result == ""


def test_load_company_context_sync_returns_empty_on_build_exception():
    """Fail-open: build_company_agent_context raising returns empty string."""
    async def fake_build_raises(company_id, db, **kwargs):
        raise RuntimeError("DB connection failed")

    with patch(
        "app.shared.services.lia_agent_context_builder.build_company_agent_context",
        side_effect=fake_build_raises,
    ), patch(
        "app.core.database.AsyncSessionLocal",
    ) as mock_session:
        mock_db = AsyncMock()
        mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
        mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

        result = _load_company_context_sync("test-company-id")

    assert result == ""


def _make_minimal_state(company_id="test-company-id"):
    """Minimal state that bypasses all early-exit guards and reaches service.enrich.

    Key flags:
    - intake_approved=True + parsed_title + parsed_seniority -> _has_structured_intake=True -> skips classifier
    - jd_enriched=None -> falls into the else branch that calls service.enrich
    """
    return {
        "company_id": company_id,
        "jd_raw": "Engenheiro de Software Pleno responsavel por desenvolvimento de sistemas.",
        "raw_input": "",
        "user_query": "",
        "parsed_title": "Engenheiro de Software",
        "parsed_seniority": "Pleno",
        "parsed_department": "Engenharia",
        "intake_approved": True,
        "jd_enriched": None,
        "stage_history": [],
        "current_stage": "intake",
        "messages": [],
        "right_panel_form": None,
        "attached_file_text": None,
    }


def test_jd_enrichment_node_passes_company_context_to_service_enrich():
    """company_context must be forwarded to service.enrich - never left empty when company_id is present."""
    fake_company_ctx = "Empresa: ACME Corp\nValores: inovacao"
    captured_kwargs = {}

    mock_enriched = MagicMock()
    mock_enriched.title = "Engenheiro de Software"
    mock_enriched.summary = "Buscamos engenheiro."
    mock_enriched.responsibilities = []
    mock_enriched.requirements = []
    mock_enriched.nice_to_have = []
    mock_enriched.benefits = []
    mock_enriched.work_model = None
    mock_enriched.employment_type = None

    def fake_enrich(**kwargs):
        captured_kwargs.update(kwargs)
        return (mock_enriched, 75.0, [])

    mock_service = MagicMock()
    mock_service.enrich.side_effect = fake_enrich

    # _get_jd_service is imported inside jd_enrichment_node via deferred
    # .
    # Patching  intercepts that lookup at call time.
    with patch(
        "app.domains.job_creation.nodes.jd_enrichment._load_company_context_sync",
        return_value=fake_company_ctx,
    ), patch(
        "app.domains.job_creation.graph._get_jd_service",
        return_value=mock_service,
    ):
        state = _make_minimal_state("test-company-id")

        try:
            jd_enrichment_node(state)
        except Exception:
            pass

    assert "company_context" in captured_kwargs, (
        "service.enrich was called WITHOUT company_context -- P1-G regression! "
        "captured_kwargs keys={}".format(list(captured_kwargs.keys()))
    )
    assert captured_kwargs["company_context"] == fake_company_ctx, (
        "Expected company_context={}, got {}".format(
            fake_company_ctx, captured_kwargs.get("company_context")
        )
    )


def test_jd_enrichment_node_does_not_pass_company_context_when_company_id_missing():
    """When state has no company_id, company_context should be empty (fail-open)."""
    captured_kwargs = {}

    mock_enriched = MagicMock()
    mock_enriched.title = "Engenheiro de Software"
    mock_enriched.summary = "ok"
    mock_enriched.responsibilities = []
    mock_enriched.requirements = []
    mock_enriched.nice_to_have = []
    mock_enriched.benefits = []
    mock_enriched.work_model = None
    mock_enriched.employment_type = None

    def fake_enrich(**kwargs):
        captured_kwargs.update(kwargs)
        return (mock_enriched, 60.0, [])

    mock_service = MagicMock()
    mock_service.enrich.side_effect = fake_enrich

    with patch(
        "app.domains.job_creation.nodes.jd_enrichment._load_company_context_sync",
        return_value="",
    ) as mock_load, patch(
        "app.domains.job_creation.graph._get_jd_service",
        return_value=mock_service,
    ):
        state = _make_minimal_state(company_id="")

        try:
            jd_enrichment_node(state)
        except Exception:
            pass

    mock_load.assert_called_once_with("")
    if "company_context" in captured_kwargs:
        assert captured_kwargs["company_context"] == "", (
            "Expected empty company_context for missing company_id, got {}".format(
                captured_kwargs["company_context"]
            )
        )
