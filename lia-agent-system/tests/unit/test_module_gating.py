"""Unit tests for module gating infrastructure."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.shared.module_gating import (
    TOOL_MODULE_MAP,
    PREMIUM_GATED_TOOLS,
    TASTING_TOOLS,
    MODULE_LABELS,
    build_degraded_response,
    build_beta_response,
    check_tool_module_access,
    require_module,
    _extract_tasting_data,
)


class TestToolModuleMap:
    def test_all_premium_tools_in_map(self):
        for tool in PREMIUM_GATED_TOOLS:
            assert tool in TOOL_MODULE_MAP, f"{tool} missing from TOOL_MODULE_MAP"

    def test_all_tasting_tools_in_map(self):
        for tool in TASTING_TOOLS:
            assert tool in TOOL_MODULE_MAP, f"{tool} missing from TOOL_MODULE_MAP"

    def test_no_tool_in_both_premium_and_tasting(self):
        overlap = PREMIUM_GATED_TOOLS & TASTING_TOOLS
        assert not overlap, f"Tools in both PREMIUM and TASTING: {overlap}"

    def test_all_modules_have_labels(self):
        modules = set(TOOL_MODULE_MAP.values())
        for mod in modules:
            assert mod in MODULE_LABELS, f"Module {mod} missing label"

    def test_expected_modules_present(self):
        expected = {
            "talent_intelligence_pro",
            "internal_mobility",
            "interview_intelligence",
            "workforce_planning",
            "candidate_nurture",
        }
        actual = set(TOOL_MODULE_MAP.values())
        assert expected == actual

    def test_expected_tool_count(self):
        assert len(TOOL_MODULE_MAP) == 15  # updated: 4 tools added post-v1


class TestBuildDegradedResponse:
    def test_returns_degraded_flag(self):
        resp = build_degraded_response("infer_related_skills", "talent_intelligence_pro")
        assert resp["is_degraded"] is True
        assert resp["module_active"] is False
        assert resp["module_required"] == "talent_intelligence_pro"
        assert resp["success"] is True

    def test_includes_module_label(self):
        resp = build_degraded_response("match_internal_candidates", "internal_mobility")
        assert resp["module_label"] == "Internal Mobility Suite"

    def test_partial_data_with_count(self):
        resp = build_degraded_response(
            "infer_related_skills",
            "talent_intelligence_pro",
            partial_data={"count": 7, "skills_preview": ["Python", "Java"]},
        )
        assert "7" in resp["message"]
        assert resp["data"]["count"] == 7

    def test_partial_data_without_count(self):
        resp = build_degraded_response(
            "infer_related_skills",
            "talent_intelligence_pro",
            partial_data={"preview": True},
        )
        assert "algumas" in resp["message"]

    def test_unknown_module_fallback(self):
        resp = build_degraded_response("some_tool", "unknown_module")
        assert resp["is_degraded"] is True
        assert "unknown_module" in resp["message"]


class TestBuildBetaResponse:
    def test_adds_beta_badge_to_message(self):
        result = {"success": True, "data": {}, "message": "Original"}
        resp = build_beta_response(result, "talent_intelligence_pro")
        assert "BETA" in resp["message"]
        assert resp["module_status"] == "beta"
        assert resp["module_label"] == "Talent Intelligence Pro"

    def test_no_message_key(self):
        result = {"success": True, "data": {}}
        resp = build_beta_response(result, "internal_mobility")
        assert resp["module_status"] == "beta"


class TestExtractTastingData:
    def test_skills_preview(self):
        data = {"data": {"skills": ["Python", "Java", "Go", "Rust", "C++"]}}
        result = _extract_tasting_data(data)
        assert result["preview"] is True
        assert len(result["skills_preview"]) == 3
        assert result["count"] == 5

    def test_candidates_preview(self):
        data = {"data": {"candidates": [
            {"name": "Alice", "match_score": 0.9},
            {"name": "Bob", "match_score": 0.8},
            {"name": "Charlie", "match_score": 0.7},
        ]}}
        result = _extract_tasting_data(data)
        assert len(result["candidates_preview"]) == 2
        assert result["count"] == 3

    def test_gaps_preview(self):
        data = {"data": {"gaps": ["Leadership", "Strategy"]}}
        result = _extract_tasting_data(data)
        assert result["gaps_count"] == 2
        assert result["top_gap"] == "Leadership"

    def test_empty_data(self):
        result = _extract_tasting_data({"other": "value"})
        assert result == {"preview": True}

    def test_metrics_preview(self):
        data = {"data": {"metrics": {"open_rate": 0.45, "click_rate": 0.12, "reply_rate": 0.08}}}
        result = _extract_tasting_data(data)
        assert len(result["metrics_preview"]) == 2
        assert result["count"] == 3

    def test_related_skills_key(self):
        data = {"data": {"related_skills": ["React", "Vue", "Angular", "Svelte"]}}
        result = _extract_tasting_data(data)
        assert len(result["skills_preview"]) == 3
        assert result["count"] == 4

    def test_matches_key_for_internal_mobility(self):
        data = {"data": {"matches": [
            {"name": "Ana", "score": 0.9},
            {"name": "Bob", "score": 0.8},
            {"name": "Carol", "score": 0.7},
        ]}}
        result = _extract_tasting_data(data)
        assert len(result["candidates_preview"]) == 2
        assert result["count"] == 3

    def test_missing_skills_key(self):
        data = {"data": {"missing_skills": ["Docker", "Kubernetes"]}}
        result = _extract_tasting_data(data)
        assert result["gaps_count"] == 2
        assert result["top_gap"] == "Docker"

    def test_market_snapshot(self):
        data = {"data": {"market_snapshot": {"avg_salary": 120000, "demand": "high", "growth": "12%", "extra": "x"}}}
        result = _extract_tasting_data(data)
        assert len(result["market_preview"]) == 3


class TestCheckToolModuleAccess:
    @pytest.mark.asyncio
    async def test_unmapped_tool_always_allowed(self):
        result = await check_tool_module_access("some_random_tool", "company1", MagicMock())
        assert result["allowed"] is True
        assert result["module_name"] is None

    @pytest.mark.asyncio
    async def test_beta_module_allowed(self):
        mock_service = AsyncMock()
        mock_service.get_module_status = AsyncMock(return_value="beta")
        with patch("app.domains.modules.services.module_service.module_service", mock_service):
            result = await check_tool_module_access("infer_related_skills", "company1", MagicMock())
        assert result["allowed"] is True
        assert result["status"] == "beta"

    @pytest.mark.asyncio
    async def test_active_module_allowed(self):
        mock_service = AsyncMock()
        mock_service.get_module_status = AsyncMock(return_value="active")
        with patch("app.domains.modules.services.module_service.module_service", mock_service):
            result = await check_tool_module_access("infer_related_skills", "company1", MagicMock())
        assert result["allowed"] is True
        assert result["status"] == "active"

    @pytest.mark.asyncio
    async def test_disabled_module_denied(self):
        mock_service = AsyncMock()
        mock_service.get_module_status = AsyncMock(return_value="disabled")
        with patch("app.domains.modules.services.module_service.module_service", mock_service):
            result = await check_tool_module_access("infer_related_skills", "company1", MagicMock())
        assert result["allowed"] is False
        assert result["status"] == "disabled"

    @pytest.mark.asyncio
    async def test_expired_module_denied(self):
        mock_service = AsyncMock()
        mock_service.get_module_status = AsyncMock(return_value="expired")
        with patch("app.domains.modules.services.module_service.module_service", mock_service):
            result = await check_tool_module_access("infer_related_skills", "company1", MagicMock())
        assert result["allowed"] is False

    @pytest.mark.asyncio
    async def test_not_provisioned_denied(self):
        mock_service = AsyncMock()
        mock_service.get_module_status = AsyncMock(return_value=None)
        with patch("app.domains.modules.services.module_service.module_service", mock_service):
            result = await check_tool_module_access("infer_related_skills", "company1", MagicMock())
        assert result["allowed"] is False
        assert result["status"] == "not_provisioned"

    @pytest.mark.asyncio
    async def test_premium_tool_flagged(self):
        mock_service = AsyncMock()
        mock_service.get_module_status = AsyncMock(return_value="disabled")
        with patch("app.domains.modules.services.module_service.module_service", mock_service):
            result = await check_tool_module_access("analyze_interview_recording", "company1", MagicMock())
        assert result["is_premium_gated"] is True

    @pytest.mark.asyncio
    async def test_tasting_tool_flagged(self):
        mock_service = AsyncMock()
        mock_service.get_module_status = AsyncMock(return_value="disabled")
        with patch("app.domains.modules.services.module_service.module_service", mock_service):
            result = await check_tool_module_access("infer_related_skills", "company1", MagicMock())
        assert result["is_tasting"] is True

    @pytest.mark.asyncio
    async def test_service_error_fallback_denies(self):
        with patch("app.domains.modules.services.module_service.module_service") as mock:
            mock.get_module_status = AsyncMock(side_effect=Exception("DB down"))
            result = await check_tool_module_access("infer_related_skills", "company1", MagicMock())
        assert result["allowed"] is False
        assert result["status"] == "error_fallback"


class TestRequireModuleDecorator:
    @pytest.mark.asyncio
    async def test_no_company_id_returns_degraded(self):
        @require_module("talent_intelligence_pro")
        async def my_tool(**kwargs):
            return {"success": True, "data": {"result": 42}, "message": "OK"}

        result = await my_tool(skill="Python")
        assert result["is_degraded"] is True
        assert result["module_required"] == "talent_intelligence_pro"

    @pytest.mark.asyncio
    async def test_beta_adds_badge(self):
        mock_service = AsyncMock()
        mock_service.get_module_status = AsyncMock(return_value="beta")

        @require_module("talent_intelligence_pro")
        async def infer_related_skills(**kwargs):
            return {"success": True, "data": {"skills": ["A"]}, "message": "Found skills"}

        with patch("app.domains.modules.services.module_service.module_service", mock_service):
            result = await infer_related_skills(company_id="c1", db=MagicMock())
        assert "BETA" in result["message"]
        assert result["module_status"] == "beta"

    @pytest.mark.asyncio
    async def test_premium_gated_returns_degraded(self):
        mock_service = AsyncMock()
        mock_service.get_module_status = AsyncMock(return_value="disabled")

        @require_module("interview_intelligence")
        async def analyze_interview_recording(**kwargs):
            return {"success": True, "data": {}, "message": "Should not reach"}

        with patch("app.domains.modules.services.module_service.module_service", mock_service):
            result = await analyze_interview_recording(company_id="c1", db=MagicMock())
        assert result["is_degraded"] is True
        assert result["module_required"] == "interview_intelligence"

    @pytest.mark.asyncio
    async def test_tasting_returns_partial_data(self):
        mock_service = AsyncMock()
        mock_service.get_module_status = AsyncMock(return_value="disabled")

        @require_module("talent_intelligence_pro")
        async def infer_related_skills(**kwargs):
            return {"success": True, "data": {"skills": ["A", "B", "C", "D"]}, "message": "OK"}

        with patch("app.domains.modules.services.module_service.module_service", mock_service):
            result = await infer_related_skills(company_id="c1", db=MagicMock())
        assert result["is_degraded"] is True
        assert "skills_preview" in result["data"]

    @pytest.mark.asyncio
    async def test_active_module_passes_through(self):
        mock_service = AsyncMock()
        mock_service.get_module_status = AsyncMock(return_value="active")

        @require_module("talent_intelligence_pro")
        async def infer_related_skills(**kwargs):
            return {"success": True, "data": {"skills": ["A"]}, "message": "Full result"}

        with patch("app.domains.modules.services.module_service.module_service", mock_service):
            result = await infer_related_skills(company_id="c1", db=MagicMock())
        assert result["success"] is True
        assert "module_status" not in result

    @pytest.mark.asyncio
    async def test_decorator_preserves_metadata(self):
        @require_module("talent_intelligence_pro")
        async def my_tool(**kwargs):
            return {}

        assert my_tool._module_gated == "talent_intelligence_pro"
        assert my_tool.__name__ == "my_tool"


class TestToolHandlerWithModule:
    @pytest.mark.asyncio
    async def test_tool_handler_module_param_stored(self):
        from app.shared.tool_handler import tool_handler

        @tool_handler("test_domain", module="talent_intelligence_pro")
        async def my_tool(**kwargs):
            return {"result": 1}

        assert my_tool._module_gated == "talent_intelligence_pro"

    @pytest.mark.asyncio
    async def test_tool_handler_no_module_works(self):
        from app.shared.tool_handler import tool_handler

        @tool_handler("test_domain")
        async def my_tool(**kwargs):
            return {"result": 1}

        result = await my_tool(company_id="c1")
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_tool_handler_module_beta_badge(self):
        from app.shared.tool_handler import tool_handler

        mock_service = AsyncMock()
        mock_service.get_module_status = AsyncMock(return_value="beta")

        @tool_handler("test_domain", module="talent_intelligence_pro")
        async def infer_related_skills(**kwargs):
            return {"skills": ["Python"]}

        with patch("app.domains.modules.services.module_service.module_service", mock_service):
            result = await infer_related_skills(company_id="c1", db=MagicMock())
        assert result["success"] is True
        assert result.get("module_status") == "beta"

    @pytest.mark.asyncio
    async def test_tool_handler_module_disabled_degrades(self):
        from app.shared.tool_handler import tool_handler

        mock_service = AsyncMock()
        mock_service.get_module_status = AsyncMock(return_value="disabled")

        @tool_handler("test_domain", module="interview_intelligence")
        async def analyze_interview_recording(**kwargs):
            return {"transcription": "should not appear"}

        with patch("app.domains.modules.services.module_service.module_service", mock_service):
            result = await analyze_interview_recording(company_id="c1", db=MagicMock())
        assert result["is_degraded"] is True

    @pytest.mark.asyncio
    async def test_tool_handler_require_company_without_db_returns_degraded(self):
        from app.shared.tool_handler import tool_handler

        @tool_handler("test_domain", module="talent_intelligence_pro")
        async def my_tool(**kwargs):
            return {"result": 1}

        result = await my_tool(company_id="c1")
        assert result["is_degraded"] is True
        assert result["module_required"] == "talent_intelligence_pro"

    @pytest.mark.asyncio
    async def test_tool_handler_no_require_company_without_db_returns_degraded(self):
        from app.shared.tool_handler import tool_handler

        @tool_handler("test_domain", require_company=False, module="talent_intelligence_pro")
        async def my_tool(**kwargs):
            return {"result": 1}

        result = await my_tool()
        assert result["is_degraded"] is True
        assert result["module_required"] == "talent_intelligence_pro"

    @pytest.mark.asyncio
    async def test_tool_handler_module_error_returns_degraded(self):
        from app.shared.tool_handler import tool_handler

        @tool_handler("test_domain", module="talent_intelligence_pro")
        async def infer_related_skills(**kwargs):
            return {"skills": ["Python"]}

        with patch("app.domains.modules.services.module_service.module_service") as mock:
            mock.get_module_status = AsyncMock(side_effect=Exception("DB down"))
            result = await infer_related_skills(company_id="c1", db=MagicMock())
        assert result["is_degraded"] is True
