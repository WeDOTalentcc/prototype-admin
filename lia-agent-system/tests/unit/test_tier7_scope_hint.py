"""TDD tests for Fase C.2 — Tier 7 dual-mode + ScopeHint

Verifies:
  Test 1 (P0): ScopeHint dataclass structure and immutability
  Test 2 (P0): CustomAgentRepository.list_active_for_context: tenant wins over first_party
  Test 3 (P0): CustomAgentRepository.list_active_for_context: first_party fallback when no tenant
  Test 4 (P0): get_scoped_tool_definitions augments with Studio tools when scope covered
  Test 5 (P0): get_scoped_tool_definitions does NOT add Studio tools when scope not covered
  Test 6 (P1): ScopeHint is NOT a RouteResult (type safety)
  Test 7 (P1): list_active_for_context returns empty when domain not covered
  Test 8 (P2): studio_scope_extension get_studio_covered_domains includes expected domains

Run: python3 -m pytest tests/unit/test_tier7_scope_hint.py tests/unit/test_studio_scope_extension.py -v --no-cov
"""
from __future__ import annotations

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Test 1: ScopeHint dataclass fields and defaults
# ---------------------------------------------------------------------------

def test_scope_hint_fields_and_defaults():
    """P0: ScopeHint has domain, source, tools fields with correct defaults."""
    from app.orchestrator.routing.scope_hint import ScopeHint

    hint = ScopeHint(domain="talent_analysis", source="studio_first_party")
    assert hint.domain == "talent_analysis"
    assert hint.source == "studio_first_party"
    assert hint.tools == []  # default_factory

    hint2 = ScopeHint(
        domain="interview_analysis",
        source="studio_deployment",
        tools=["analyze_interview", "detect_bias"],
    )
    assert hint2.domain == "interview_analysis"
    assert hint2.source == "studio_deployment"
    assert "analyze_interview" in hint2.tools


def test_scope_hint_is_dataclass():
    """P0: ScopeHint must be a dataclass (no BaseModel dependency)."""
    import dataclasses
    from app.orchestrator.routing.scope_hint import ScopeHint
    assert dataclasses.is_dataclass(ScopeHint)


# ---------------------------------------------------------------------------
# Test 2: Repository list_active_for_context — tenant wins over first_party
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_active_for_context_tenant_wins():
    """P0: When company_id matches a custom agent, it wins over first_party global."""
    from app.domains.agent_studio.repositories.custom_agent_repository import CustomAgentRepository

    tenant_agent = MagicMock()
    tenant_agent.name = "TenantSpecificAgent"

    mock_db = AsyncMock()

    call_count = [0]
    async def fake_execute(stmt):
        call_count[0] += 1
        result = MagicMock()
        result.scalars.return_value.all.return_value = [tenant_agent]
        return result

    mock_db.execute = fake_execute

    repo = CustomAgentRepository(mock_db)
    results = await repo.list_active_for_context(
        company_id="company-xyz",
        domain="talent_analysis",
        include_first_party=True,
    )

    assert results == [tenant_agent]
    assert call_count[0] == 1, "Must only query once — tenant wins, no fp fallback"
    assert results[0].name == "TenantSpecificAgent"


# ---------------------------------------------------------------------------
# Test 3: Repository list_active_for_context — first_party fallback
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_active_for_context_first_party_fallback():
    """P0: When no tenant agent matches, first_party global is returned as fallback."""
    from app.domains.agent_studio.repositories.custom_agent_repository import CustomAgentRepository

    fp_agent = MagicMock()
    fp_agent.name = "TalentIntelAgent"

    mock_db = AsyncMock()
    call_count = [0]

    async def fake_execute(stmt):
        call_count[0] += 1
        result = MagicMock()
        if call_count[0] == 1:
            # First call: tenant query — returns empty
            result.scalars.return_value.all.return_value = []
        else:
            # Second call: first_party fallback — returns fp_agent
            result.scalars.return_value.all.return_value = [fp_agent]
        return result

    mock_db.execute = fake_execute

    repo = CustomAgentRepository(mock_db)
    results = await repo.list_active_for_context(
        company_id="company-xyz",
        domain="talent_analysis",
        include_first_party=True,
    )

    assert results == [fp_agent]
    assert call_count[0] == 2, "Should execute twice: tenant first, then fp fallback"
    assert results[0].name == "TalentIntelAgent"


# ---------------------------------------------------------------------------
# Test 4: get_scoped_tool_definitions augments with Studio tools
# ---------------------------------------------------------------------------

def test_scoped_tool_defs_augmented_with_studio_tools():
    """P0: When Studio cache has tools for the scope, get_scoped_tool_definitions
    includes them (without duplicating existing tools from base registries)."""
    from app.orchestrator.studio_scope_extension import invalidate_studio_scope_cache

    # Build a fake ToolDefinition
    fake_td = MagicMock()
    fake_td.name = "studio_talent_scorer"

    # Patch: studio covered scopes includes "talent_funnel"
    # Patch: snapshot has studio tool for talent_funnel
    # Patch: _load_sources returns one registry with different tool
    base_td = MagicMock()
    base_td.name = "search_candidates"

    with patch("app.orchestrator.studio_scope_extension.get_studio_covered_scopes",
               return_value={"talent_funnel"}), \
         patch("app.orchestrator.studio_scope_extension.get_studio_scope_cache_snapshot",
               return_value={"talent_funnel": ["studio_talent_scorer"]}), \
         patch("app.shared.tool_catalog._REGISTRY_SCOPE",
               {"talent": {"talent_funnel"}}), \
         patch("app.shared.tool_catalog._load_sources",
               return_value={"talent": [base_td, fake_td]}), \
         patch("app.shared.tool_catalog._GLOBAL_ESSENTIALS", set()):

        from app.shared.tool_catalog import get_scoped_tool_definitions
        result = get_scoped_tool_definitions("talent_funnel")
        names = [getattr(td, "name", None) for td in result]
        assert "search_candidates" in names
        assert "studio_talent_scorer" in names


# ---------------------------------------------------------------------------
# Test 5: get_scoped_tool_definitions does NOT add Studio tools for uncovered scope
# ---------------------------------------------------------------------------

def test_scoped_tool_defs_no_studio_augmentation_for_uncovered_scope():
    """P0: When scope is NOT in studio covered scopes, no Studio tools are added."""
    base_td = MagicMock()
    base_td.name = "list_jobs"

    with patch("app.orchestrator.studio_scope_extension.get_studio_covered_scopes",
               return_value={"talent_funnel"}), \
         patch("app.orchestrator.studio_scope_extension.get_studio_scope_cache_snapshot",
               return_value={"talent_funnel": ["studio_talent_scorer"]}), \
         patch("app.shared.tool_catalog._REGISTRY_SCOPE",
               {"jobs_mgmt": {"job_table"}}), \
         patch("app.shared.tool_catalog._load_sources",
               return_value={"jobs_mgmt": [base_td]}), \
         patch("app.shared.tool_catalog._GLOBAL_ESSENTIALS", set()):

        from app.shared.tool_catalog import get_scoped_tool_definitions
        result = get_scoped_tool_definitions("job_table")
        names = [getattr(td, "name", None) for td in result]
        assert "list_jobs" in names
        assert "studio_talent_scorer" not in names


# ---------------------------------------------------------------------------
# Test 6: ScopeHint is NOT a RouteResult (type safety)
# ---------------------------------------------------------------------------

def test_scope_hint_not_route_result():
    """P1: ScopeHint and RouteResult are distinct types — isinstance guard works."""
    from app.orchestrator.routing.scope_hint import ScopeHint
    from app.orchestrator.routing.cascaded_router import RouteResult

    hint = ScopeHint(domain="talent_analysis", source="studio_first_party")
    assert isinstance(hint, ScopeHint)
    assert not isinstance(hint, RouteResult)

    route = RouteResult(domain_id="talent_funnel", confidence=0.9, source="fast_router")
    assert isinstance(route, RouteResult)
    assert not isinstance(route, ScopeHint)


# ---------------------------------------------------------------------------
# Test 7: list_active_for_context returns empty when domain not covered
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_active_for_context_empty_when_no_match():
    """P1: No agents match the domain -> returns empty list."""
    from app.domains.agent_studio.repositories.custom_agent_repository import CustomAgentRepository

    mock_db = AsyncMock()

    async def fake_execute(stmt):
        result = MagicMock()
        result.scalars.return_value.all.return_value = []
        return result

    mock_db.execute = fake_execute

    repo = CustomAgentRepository(mock_db)
    results = await repo.list_active_for_context(
        company_id="company-xyz",
        domain="unmapped_domain_xyz",
        include_first_party=True,
    )

    assert results == []


# ---------------------------------------------------------------------------
# Test 8: get_studio_covered_domains has expected Studio domains
# ---------------------------------------------------------------------------

def test_studio_covered_domains_has_expected_domains():
    """P2: The static domain map includes the TalentIntelAgent and InterviewAnalysisAgent domains."""
    from app.orchestrator.studio_scope_extension import get_studio_covered_domains

    domains = get_studio_covered_domains()
    assert "talent_analysis" in domains
    assert "skill_gap" in domains
    assert "interview_analysis" in domains
    assert "bias_detection" in domains
