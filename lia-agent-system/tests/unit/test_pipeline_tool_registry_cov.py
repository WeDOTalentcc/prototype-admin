"""
Coverage tests for app/domains/pipeline/agents/pipeline_tool_registry.py
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ── Tool wrapper functions ───────────────────────────────────────────────────

class TestWrapGetCandidateProfile:
    @pytest.mark.asyncio
    @pytest.mark.easy
    async def test_no_candidate_id(self):
        from app.domains.pipeline.agents.pipeline_tool_registry import _wrap_get_candidate_profile
        result = await _wrap_get_candidate_profile(company_id="test-company")
        assert result["success"] is False
        assert "obrigatório" in result["error"]

    @pytest.mark.asyncio
    @pytest.mark.easy
    async def test_candidate_not_found(self):
        from app.domains.pipeline.agents.pipeline_tool_registry import _wrap_get_candidate_profile
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = None
        mock_session.execute.return_value = mock_result
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("app.domains.pipeline.agents.pipeline_tool_registry.AsyncSessionLocal", return_value=mock_session):
            result = await _wrap_get_candidate_profile(candidate_id="c1")
        assert result["success"] is False

    @pytest.mark.asyncio
    @pytest.mark.easy
    async def test_candidate_found(self):
        from app.domains.pipeline.agents.pipeline_tool_registry import _wrap_get_candidate_profile
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = {
            "id": "c1", "name": "Ana", "email": "ana@test.com", "phone": None,
            "linkedin_url": None, "current_title": "Dev", "current_company": "Acme",
            "technical_skills": ["Python"], "soft_skills": [], "location_city": "SP",
            "location_state": "SP", "salary_expectation_clt": 15000,
            "salary_expectation_pj": None, "work_model_preference": "remote",
            "is_remote": True, "source": "linkedin", "resume_url": None,
        }
        mock_session.execute.return_value = mock_result
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("app.domains.pipeline.agents.pipeline_tool_registry.AsyncSessionLocal", return_value=mock_session):
            result = await _wrap_get_candidate_profile(candidate_id="c1", company_id="test-company")
        assert result["success"] is True
        assert result["profile"]["name"] == "Ana"


class TestWrapGetCandidateWsiScores:
    @pytest.mark.asyncio
    @pytest.mark.easy
    async def test_no_scores(self):
        from app.domains.pipeline.agents.pipeline_tool_registry import _wrap_get_candidate_wsi_scores
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = None
        mock_session.execute.return_value = mock_result
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("app.domains.pipeline.agents.pipeline_tool_registry.AsyncSessionLocal", return_value=mock_session):
            result = await _wrap_get_candidate_wsi_scores(candidate_id="c1", job_id="j1")
        assert isinstance(result, dict)
        assert "scores" in result or "success" in result


class TestWrapValidateTransition:
    @pytest.mark.asyncio
    @pytest.mark.easy
    async def test_missing_params(self):
        from app.domains.pipeline.agents.pipeline_tool_registry import _wrap_validate_transition
        result = await _wrap_validate_transition()
        assert isinstance(result, dict)
        assert "is_valid" in result or "success" in result


class TestWrapExtractPreferences:
    @pytest.mark.asyncio
    @pytest.mark.easy
    async def test_extract_with_text(self):
        from app.domains.pipeline.agents.pipeline_tool_registry import _wrap_extract_preferences
        with patch("app.domains.pipeline.agents.pipeline_tool_registry.AsyncSessionLocal") as mock_asl:
            mock_session = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=False)
            mock_asl.return_value = mock_session
            mock_result = MagicMock()
            mock_result.mappings.return_value.all.return_value = []
            mock_session.execute.return_value = mock_result
            result = await _wrap_extract_preferences(recruiter_message="Mover para entrevista")
        assert isinstance(result, dict)


# ── get_pipeline_transition_tools ────────────────────────────────────────────

class TestGetPipelineTransitionTools:
    @pytest.mark.easy
    def test_default_tools(self):
        from app.domains.pipeline.agents.pipeline_tool_registry import get_pipeline_transition_tools
        tools = get_pipeline_transition_tools(action_behavior="passive")
        assert isinstance(tools, list)

    @pytest.mark.easy
    def test_specific_tools(self):
        from app.domains.pipeline.agents.pipeline_tool_registry import get_pipeline_transition_tools, ALL_TOOLS
        if ALL_TOOLS:
            name = ALL_TOOLS[0].name
            tools = get_pipeline_transition_tools(allowed_tool_names=[name])
            assert len(tools) == 1

    @pytest.mark.easy
    def test_nonexistent_tool(self):
        from app.domains.pipeline.agents.pipeline_tool_registry import get_pipeline_transition_tools
        tools = get_pipeline_transition_tools(allowed_tool_names=["nonexistent_tool_xyz"])
        assert len(tools) == 0


# ── Module constants ─────────────────────────────────────────────────────────

class TestModuleConstants:
    @pytest.mark.easy
    def test_all_tools_defined(self):
        from app.domains.pipeline.agents.pipeline_tool_registry import ALL_TOOLS
        assert len(ALL_TOOLS) >= 10

    @pytest.mark.easy
    def test_tool_map(self):
        from app.domains.pipeline.agents.pipeline_tool_registry import _TOOL_MAP
        assert isinstance(_TOOL_MAP, dict)
        assert len(_TOOL_MAP) >= 10
