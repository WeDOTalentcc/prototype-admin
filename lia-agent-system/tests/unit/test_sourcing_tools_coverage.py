"""Unit tests for app/domains/sourcing/tools — SOURCING_TOOLS registry and executor."""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch


class TestSourcingToolsData:
    def test_sourcing_tools_is_list(self):
        from app.domains.sourcing.tools import SOURCING_TOOLS
        assert isinstance(SOURCING_TOOLS, list)

    def test_sourcing_tools_not_empty(self):
        from app.domains.sourcing.tools import SOURCING_TOOLS
        assert len(SOURCING_TOOLS) >= 5

    def test_each_tool_has_tool_id(self):
        from app.domains.sourcing.tools import SOURCING_TOOLS
        for tool in SOURCING_TOOLS:
            assert "tool_id" in tool

    def test_each_tool_has_name(self):
        from app.domains.sourcing.tools import SOURCING_TOOLS
        for tool in SOURCING_TOOLS:
            assert "name" in tool

    def test_each_tool_has_description(self):
        from app.domains.sourcing.tools import SOURCING_TOOLS
        for tool in SOURCING_TOOLS:
            assert "description" in tool

    def test_each_tool_has_handler(self):
        from app.domains.sourcing.tools import SOURCING_TOOLS
        for tool in SOURCING_TOOLS:
            assert "handler" in tool

    def test_all_tool_ids_prefixed_sourcing(self):
        from app.domains.sourcing.tools import SOURCING_TOOLS
        for tool in SOURCING_TOOLS:
            assert tool["tool_id"].startswith("sourcing_")

    def test_search_candidates_exists(self):
        from app.domains.sourcing.tools import SOURCING_TOOLS
        ids = [t["tool_id"] for t in SOURCING_TOOLS]
        assert "sourcing_search_candidates" in ids

    def test_reject_candidate_exists(self):
        from app.domains.sourcing.tools import SOURCING_TOOLS
        ids = [t["tool_id"] for t in SOURCING_TOOLS]
        assert "sourcing_reject_candidate" in ids

    def test_handler_paths_have_dot(self):
        from app.domains.sourcing.tools import SOURCING_TOOLS
        for tool in SOURCING_TOOLS:
            assert "." in tool["handler"]


class TestGetToolById:
    def test_returns_tool_for_valid_id(self):
        from app.domains.sourcing.tools import _get_tool_by_id
        result = _get_tool_by_id("sourcing_search_candidates")
        assert result is not None
        assert result["tool_id"] == "sourcing_search_candidates"

    def test_returns_none_for_invalid_id(self):
        from app.domains.sourcing.tools import _get_tool_by_id
        assert _get_tool_by_id("nonexistent") is None

    def test_returns_none_for_empty_string(self):
        from app.domains.sourcing.tools import _get_tool_by_id
        assert _get_tool_by_id("") is None

    def test_returns_rank_candidates(self):
        from app.domains.sourcing.tools import _get_tool_by_id
        result = _get_tool_by_id("sourcing_rank_candidates")
        assert result is not None

    def test_returns_update_stage(self):
        from app.domains.sourcing.tools import _get_tool_by_id
        result = _get_tool_by_id("sourcing_update_candidate_stage")
        assert result is not None


class TestExecuteSourcingTool:
    def _make_context(self):
        ctx = MagicMock()
        ctx.company_id = "company-1"
        return ctx

    @pytest.mark.asyncio
    async def test_returns_error_status_for_unknown_tool(self):
        from app.domains.sourcing.tools import execute_sourcing_tool
        result = await execute_sourcing_tool("unknown_tool", {}, self._make_context())
        assert result.get("status") == "error" or result.get("success") is False

    @pytest.mark.asyncio
    async def test_error_includes_tool_id(self):
        from app.domains.sourcing.tools import execute_sourcing_tool
        result = await execute_sourcing_tool("unknown_xyz", {}, self._make_context())
        assert "unknown_xyz" in str(result)

    @pytest.mark.asyncio
    async def test_returns_error_on_import_failure(self):
        from app.domains.sourcing.tools import execute_sourcing_tool
        with patch("importlib.import_module", side_effect=ImportError("no module")):
            result = await execute_sourcing_tool("sourcing_search_candidates", {}, self._make_context())
        assert "error" in result

    @pytest.mark.asyncio
    async def test_successful_async_handler(self):
        from app.domains.sourcing.tools import execute_sourcing_tool, _get_tool_by_id

        async def mock_handler(*args, **kwargs):
            return {"status": "ok", "results": []}

        tool = _get_tool_by_id("sourcing_search_candidates")
        func_name = tool["handler"].rsplit(".", 1)[1]

        with patch("importlib.import_module") as mock_import:
            mock_module = MagicMock()
            setattr(mock_module, func_name, mock_handler)
            mock_import.return_value = mock_module
            result = await execute_sourcing_tool("sourcing_search_candidates", {}, self._make_context())

        assert result.get("status") in ("ok", "success") or "results" in result or "error" not in result

    @pytest.mark.asyncio
    async def test_returns_error_on_handler_exception(self):
        from app.domains.sourcing.tools import execute_sourcing_tool, _get_tool_by_id

        async def failing_handler(*args, **kwargs):
            raise RuntimeError("DB error")

        tool = _get_tool_by_id("sourcing_search_candidates")
        func_name = tool["handler"].rsplit(".", 1)[1]

        with patch("importlib.import_module") as mock_import:
            mock_module = MagicMock()
            setattr(mock_module, func_name, failing_handler)
            mock_import.return_value = mock_module
            result = await execute_sourcing_tool("sourcing_search_candidates", {}, self._make_context())

        assert "error" in result
