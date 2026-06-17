"""Contract test (Sensor) — wrapper layer preserves tenant context.

REGRESSÃO 2026-05-24 — chat LIA mostrou `check_company_completeness FAILED 0.0ms`
e `search_jobs FAILED 0.0ms` (TypeError multiple values for _context) imediatamente
após Sprint 8 NS-2 (commit 06b199d4) ter passado a injetar `_context` em
`handler_kwargs` no `ToolExecutor`. 28 wrappers `_wrap_*` em `app/domains/*/tools/*.py`
seguiam pattern outdated `kwargs.pop("company_id")` + ignoravam `kwargs["_context"]`.

Resultado em produção:
- Wrappers .get() (sem .pop()): construíam SimpleNamespace empty, canonical raise
  ToolContextMissingError (`check_company_completeness` 4× no log).
- Wrappers .pop() + forward: `_context=ctx, **kwargs` causava
  TypeError "multiple values for keyword argument '_context'"
  (`search_jobs` 2× no log).

Fix canonical: `normalize_wrapper_kwargs` helper em `app/tools/context_helpers.py`
converge ambos os paths (executor vs tool_handler decorator).

Este teste é BLOCKING. Detecta regressão em 2 dimensões:
1. Path A — executor injeta _context → wrapper preserva company_id real
2. Path B — tool_handler decorator passa company_id como kwarg → wrapper
   sintetiza _context corretamente
"""
from __future__ import annotations

import inspect
import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch


# Inventário canonical (2026-05-24): wrappers globais em app/domains/*/tools/*.py
# que existem para mediar dispatch do Global ToolExecutor.
#
# Cada tupla: (module_path, wrapper_name, canonical_name)
GLOBAL_WRAPPERS = [
    # company_settings
    ("app.domains.company_settings.tools.import_tools",
     "_wrap_check_company_completeness_global", "check_company_completeness"),
    ("app.domains.company_settings.tools.import_tools",
     "_wrap_suggest_recruiting_policy", "suggest_recruiting_policy"),
    ("app.domains.company_settings.tools.import_tools",
     "_wrap_import_benefits_from_data", "import_benefits_from_data"),
    ("app.domains.company_settings.tools.import_tools",
     "_wrap_save_hiring_policy_global", "save_hiring_policy"),
    # job_management/query
    ("app.domains.job_management.tools.query_tools",
     "_wrap_search_jobs", "search_jobs"),
    ("app.domains.job_management.tools.query_tools",
     "_wrap_get_job_details", "get_job_details"),
    ("app.domains.job_management.tools.query_tools",
     "_wrap_get_job_velocity", "get_job_velocity"),
    ("app.domains.job_management.tools.query_tools",
     "_wrap_get_job_quality_metrics", "get_job_quality_metrics"),
    ("app.domains.job_management.tools.query_tools",
     "_wrap_get_job_benchmark", "get_job_benchmark"),
    # job_management/jobs
    ("app.domains.job_management.tools.job_tools",
     "_wrap_update_job", "update_job"),
    ("app.domains.job_management.tools.job_tools",
     "_wrap_pause_job", "pause_job"),
    ("app.domains.job_management.tools.job_tools",
     "_wrap_close_job", "close_job"),
    ("app.domains.job_management.tools.job_tools",
     "_wrap_publish_job", "publish_job"),
    # cv_screening
    ("app.domains.cv_screening.tools.candidate_tools",
     "_wrap_update_candidate_stage", "update_candidate_stage"),
    ("app.domains.cv_screening.tools.candidate_tools",
     "_wrap_add_candidate_to_vacancy", "add_candidate_to_vacancy"),
    ("app.domains.cv_screening.tools.candidate_tools",
     "_wrap_add_to_list", "add_to_list"),
    ("app.domains.cv_screening.tools.candidate_tools",
     "_wrap_wsi_screening", "wsi_screening"),
    ("app.domains.cv_screening.tools.candidate_tools",
     "_wrap_hide_candidate", "hide_candidate"),
    # sourcing/query
    ("app.domains.sourcing.tools.query_tools",
     "_wrap_search_candidates", "search_candidates"),
    ("app.domains.sourcing.tools.query_tools",
     "_wrap_get_candidate_details", "get_candidate_details"),
    ("app.domains.sourcing.tools.query_tools",
     "_wrap_get_candidate_stats", "get_candidate_stats"),
    ("app.domains.sourcing.tools.query_tools",
     "_wrap_get_candidate_history", "get_candidate_history"),
    ("app.domains.sourcing.tools.query_tools",
     "_wrap_get_talent_quality", "get_talent_quality"),
    ("app.domains.sourcing.tools.query_tools",
     "_wrap_get_talent_engagement", "get_talent_engagement"),
    ("app.domains.sourcing.tools.query_tools",
     "_wrap_get_talent_availability", "get_talent_availability"),
    ("app.domains.sourcing.tools.query_tools",
     "_wrap_get_diversity_metrics", "get_diversity_metrics"),
    ("app.domains.sourcing.tools.query_tools",
     "_wrap_get_market_benchmarks", "get_market_benchmarks"),
    # sourcing/enrichment
    ("app.domains.sourcing.tools.enrichment_tools",
     "_wrap_check_candidate_completeness", "check_candidate_completeness"),
    ("app.domains.sourcing.tools.enrichment_tools",
     "_wrap_enrich_candidate_linkedin", "enrich_candidate_linkedin"),
]


@pytest.mark.parametrize("module_path, wrapper_name, canonical_name", GLOBAL_WRAPPERS)
@pytest.mark.asyncio
async def test_wrapper_preserves_context_company_id_path_a(
    module_path: str, wrapper_name: str, canonical_name: str,
):
    """Path A: when executor injects `_context`, wrapper MUST forward it
    so canonical handler receives the real company_id."""
    import importlib
    module = importlib.import_module(module_path)
    wrapper = getattr(module, wrapper_name)

    expected_cid = "00000000-0000-4000-a000-000000000001"
    fake_context = SimpleNamespace(company_id=expected_cid, user_id="user-abc")

    with patch.object(module, canonical_name, new_callable=AsyncMock) as mock_canonical:
        mock_canonical.return_value = {"ok": True}
        await wrapper(_context=fake_context)

    assert mock_canonical.call_count == 1, (
        f"{wrapper_name} did not delegate to {canonical_name} exactly once"
    )
    passed_ctx = mock_canonical.call_args.kwargs.get("_context")
    assert passed_ctx is not None, (
        f"{wrapper_name} forgot to forward _context to {canonical_name}"
    )
    actual_cid = getattr(passed_ctx, "company_id", "")
    assert actual_cid == expected_cid, (
        f"{wrapper_name} CORRUPTED _context.company_id: "
        f"expected={expected_cid!r} got={actual_cid!r}. "
        f"Wrapper ignored kwargs['_context'] (Path A) and rebuilt from "
        f"empty kwargs.company_id."
    )


@pytest.mark.parametrize("module_path, wrapper_name, canonical_name", GLOBAL_WRAPPERS)
@pytest.mark.asyncio
async def test_wrapper_builds_context_from_kwargs_path_b(
    module_path: str, wrapper_name: str, canonical_name: str,
):
    """Path B: when tool_handler decorator passes company_id/user_id as
    kwargs (ContextVar injection), wrapper MUST synthesize a _context
    SimpleNamespace before delegating."""
    import importlib
    module = importlib.import_module(module_path)
    wrapper = getattr(module, wrapper_name)

    expected_cid = "00000000-0000-4000-a000-000000000002"

    with patch.object(module, canonical_name, new_callable=AsyncMock) as mock_canonical:
        mock_canonical.return_value = {"ok": True}
        await wrapper(company_id=expected_cid, user_id="u-1")

    passed_ctx = mock_canonical.call_args.kwargs.get("_context")
    assert passed_ctx is not None, (
        f"{wrapper_name} (Path B) did not synthesize _context for {canonical_name}"
    )
    actual_cid = getattr(passed_ctx, "company_id", "")
    assert actual_cid == expected_cid, (
        f"{wrapper_name} (Path B) corrupted company_id: "
        f"expected={expected_cid!r} got={actual_cid!r}"
    )
