"""TDD tests for Fase C.1 — studio_scope_extension.py

Tests:
1. domain "talent_analysis" maps to scope "talent_funnel"
2. domain "interview_analysis" maps to scope "in_job"
3. domain "job_creation" (not a Studio domain) → no Studio tools
4. cache invalidation — after invalidate, next call rebuilds cache
5. two agents covering same scope → tools merged, no duplicates
6. first_party tools have no installation check (always available)
7. get_studio_covered_domains() returns expected domains
8. get_studio_covered_scopes() returns expected scope values

Run: python3 -m pytest tests/unit/test_studio_scope_extension.py -v --no-cov
"""
from __future__ import annotations

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers to build fake CustomAgent-like objects (no DB)
# ---------------------------------------------------------------------------

def _make_agent(name: str, domains: list[str], allowed_tools: list[str], status: str = "active"):
    agent = MagicMock()
    agent.name = name
    agent.domains = domains
    agent.allowed_tools = allowed_tools
    agent.status = status
    return agent


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestStudioDomainToScopeMapping:
    """Test 1 & 2: domain mappings are correct."""

    def test_talent_analysis_maps_to_talent_funnel(self):
        from app.orchestrator.studio_scope_extension import _STUDIO_DOMAIN_TO_SCOPE
        assert _STUDIO_DOMAIN_TO_SCOPE["talent_analysis"] == "talent_funnel"
        assert _STUDIO_DOMAIN_TO_SCOPE["skill_gap"] == "talent_funnel"
        assert _STUDIO_DOMAIN_TO_SCOPE["candidate_nurture"] == "talent_funnel"

    def test_interview_analysis_maps_to_in_job(self):
        from app.orchestrator.studio_scope_extension import _STUDIO_DOMAIN_TO_SCOPE
        assert _STUDIO_DOMAIN_TO_SCOPE["interview_analysis"] == "in_job"
        assert _STUDIO_DOMAIN_TO_SCOPE["bias_detection"] == "in_job"
        assert _STUDIO_DOMAIN_TO_SCOPE["interview_feedback"] == "in_job"

    def test_market_intelligence_maps_to_job_table(self):
        from app.orchestrator.studio_scope_extension import _STUDIO_DOMAIN_TO_SCOPE
        assert _STUDIO_DOMAIN_TO_SCOPE["market_intelligence"] == "job_table"
        assert _STUDIO_DOMAIN_TO_SCOPE["workforce_planning"] == "job_table"


class TestGetStudioCoveredDomains:
    """Test 7: get_studio_covered_domains() returns expected domain names."""

    def test_covered_domains_includes_talent_domains(self):
        from app.orchestrator.studio_scope_extension import get_studio_covered_domains
        domains = get_studio_covered_domains()
        assert "talent_analysis" in domains
        assert "skill_gap" in domains
        assert "interview_analysis" in domains

    def test_covered_domains_does_not_include_arbitrary_domain(self):
        from app.orchestrator.studio_scope_extension import get_studio_covered_domains
        domains = get_studio_covered_domains()
        # "job_creation" is not a Studio first-party domain
        assert "job_creation" not in domains


class TestGetStudioCoveredScopes:
    """Test 8: get_studio_covered_scopes() returns expected PromptScope values."""

    def test_covered_scopes_has_all_three_prompt_scopes(self):
        from app.orchestrator.studio_scope_extension import get_studio_covered_scopes
        scopes = get_studio_covered_scopes()
        assert "talent_funnel" in scopes
        assert "in_job" in scopes
        assert "job_table" in scopes


class TestCacheInvalidation:
    """Test 4: after invalidate_studio_scope_cache(), cache is None (rebuilt on next call)."""

    def test_invalidate_clears_cache(self):
        from app.orchestrator import studio_scope_extension as ext

        # Manually set cache to a non-None value
        ext._STUDIO_SCOPE_CACHE = {"talent_funnel": ["analyze_skill_gaps"]}
        assert ext._STUDIO_SCOPE_CACHE is not None

        ext.invalidate_studio_scope_cache()
        assert ext._STUDIO_SCOPE_CACHE is None

    def test_get_snapshot_after_invalidate_returns_none(self):
        from app.orchestrator import studio_scope_extension as ext
        from app.orchestrator.studio_scope_extension import (
            get_studio_scope_cache_snapshot,
            invalidate_studio_scope_cache,
        )
        ext._STUDIO_SCOPE_CACHE = {"talent_funnel": ["tool_a"]}
        invalidate_studio_scope_cache()
        assert get_studio_scope_cache_snapshot() is None


class TestBuildScopeCache:
    """Test _build_scope_cache directly with mock agents."""

    @pytest.mark.asyncio
    async def test_talent_analysis_domain_populates_talent_funnel(self):
        from app.orchestrator.studio_scope_extension import _build_scope_cache

        fake_agent = _make_agent(
            name="TalentIntelAgent",
            domains=["talent_analysis", "skill_gap"],
            allowed_tools=["analyze_skill_gaps", "predict_candidate_success"],
        )

        mock_repo = AsyncMock()
        mock_repo.list_first_party_agents.return_value = [fake_agent]
        mock_db = MagicMock()

        with patch(
            "app.orchestrator.studio_scope_extension.CustomAgentRepository",
            return_value=mock_repo,
        ):
            cache = await _build_scope_cache(mock_db)

        assert "talent_funnel" in cache
        assert "analyze_skill_gaps" in cache["talent_funnel"]
        assert "predict_candidate_success" in cache["talent_funnel"]

    @pytest.mark.asyncio
    async def test_job_creation_domain_not_in_cache(self):
        """Test 3: domain 'job_creation' is not a Studio domain → no tools added."""
        from app.orchestrator.studio_scope_extension import _build_scope_cache

        # Simulate an agent with a domain not in _STUDIO_DOMAIN_TO_SCOPE
        fake_agent = _make_agent(
            name="UnknownDomainAgent",
            domains=["job_creation"],  # not in _STUDIO_DOMAIN_TO_SCOPE
            allowed_tools=["some_tool"],
        )

        mock_repo = AsyncMock()
        mock_repo.list_first_party_agents.return_value = [fake_agent]
        mock_db = MagicMock()

        with patch(
            "app.orchestrator.studio_scope_extension.CustomAgentRepository",
            return_value=mock_repo,
        ):
            cache = await _build_scope_cache(mock_db)

        # "job_creation" is not in _STUDIO_DOMAIN_TO_SCOPE so it falls to "global"
        # Crucially it is NOT added to "talent_funnel" or "in_job"
        assert "talent_funnel" not in cache or "some_tool" not in cache.get("talent_funnel", [])
        assert "in_job" not in cache or "some_tool" not in cache.get("in_job", [])

    @pytest.mark.asyncio
    async def test_two_agents_same_scope_tools_merged_no_duplicates(self):
        """Test 5: two first-party agents covering same scope merge tools, no dups."""
        from app.orchestrator.studio_scope_extension import _build_scope_cache

        agent_a = _make_agent(
            name="AgentA",
            domains=["talent_analysis"],
            allowed_tools=["analyze_skill_gaps", "shared_tool"],
        )
        agent_b = _make_agent(
            name="AgentB",
            domains=["skill_gap"],
            allowed_tools=["recommend_upskilling", "shared_tool"],  # shared_tool duplicate
        )

        mock_repo = AsyncMock()
        mock_repo.list_first_party_agents.return_value = [agent_a, agent_b]
        mock_db = MagicMock()

        with patch(
            "app.orchestrator.studio_scope_extension.CustomAgentRepository",
            return_value=mock_repo,
        ):
            cache = await _build_scope_cache(mock_db)

        talent_tools = cache.get("talent_funnel", [])
        assert "analyze_skill_gaps" in talent_tools
        assert "recommend_upskilling" in talent_tools
        # No duplicate shared_tool
        assert talent_tools.count("shared_tool") == 1

    @pytest.mark.asyncio
    async def test_first_party_tools_no_installation_check(self):
        """Test 6: first_party tools are returned without installation check."""
        from app.orchestrator.studio_scope_extension import _build_scope_cache

        # Agent with no company_id (first_party) — verify cache builds without error
        fake_agent = _make_agent(
            name="GlobalAgent",
            domains=["talent_analysis"],
            allowed_tools=["analyze_skill_gaps"],
        )
        fake_agent.company_id = None  # TENANT-FREE

        mock_repo = AsyncMock()
        mock_repo.list_first_party_agents.return_value = [fake_agent]
        mock_db = MagicMock()

        with patch(
            "app.orchestrator.studio_scope_extension.CustomAgentRepository",
            return_value=mock_repo,
        ):
            # Should not raise — no company_id check
            cache = await _build_scope_cache(mock_db)

        assert "talent_funnel" in cache
        assert "analyze_skill_gaps" in cache["talent_funnel"]


class TestGetStudioToolsForScope:
    """Test get_studio_tools_for_scope with mock agents (cache reset per test)."""

    @pytest.mark.asyncio
    async def test_returns_tools_for_talent_funnel(self):
        from app.orchestrator import studio_scope_extension as ext
        from app.orchestrator.studio_scope_extension import get_studio_tools_for_scope

        ext._STUDIO_SCOPE_CACHE = None  # reset
        fake_agent = _make_agent(
            name="TalentIntelAgent",
            domains=["talent_analysis"],
            allowed_tools=["analyze_skill_gaps"],
        )
        mock_repo = AsyncMock()
        mock_repo.list_first_party_agents.return_value = [fake_agent]
        mock_db = MagicMock()

        with patch(
            "app.orchestrator.studio_scope_extension.CustomAgentRepository",
            return_value=mock_repo,
        ):
            tools = await get_studio_tools_for_scope("talent_funnel", mock_db)

        assert "analyze_skill_gaps" in tools
        ext._STUDIO_SCOPE_CACHE = None  # cleanup

    @pytest.mark.asyncio
    async def test_returns_empty_for_unknown_scope(self):
        from app.orchestrator import studio_scope_extension as ext
        from app.orchestrator.studio_scope_extension import get_studio_tools_for_scope

        ext._STUDIO_SCOPE_CACHE = {"talent_funnel": ["tool_a"]}
        mock_db = MagicMock()

        tools = await get_studio_tools_for_scope("nonexistent_scope", mock_db)
        assert tools == []
        ext._STUDIO_SCOPE_CACHE = None  # cleanup

    @pytest.mark.asyncio
    async def test_fail_open_on_exception(self):
        """Fail-open: returns [] on any error, does not propagate exception."""
        from app.orchestrator import studio_scope_extension as ext
        from app.orchestrator.studio_scope_extension import get_studio_tools_for_scope

        ext._STUDIO_SCOPE_CACHE = None  # force rebuild

        mock_repo = AsyncMock()
        mock_repo.list_first_party_agents.side_effect = RuntimeError("DB gone")
        mock_db = MagicMock()

        with patch(
            "app.orchestrator.studio_scope_extension.CustomAgentRepository",
            return_value=mock_repo,
        ):
            tools = await get_studio_tools_for_scope("talent_funnel", mock_db)

        # Fail-open: no exception raised, empty list returned
        assert tools == []
        ext._STUDIO_SCOPE_CACHE = None  # cleanup
