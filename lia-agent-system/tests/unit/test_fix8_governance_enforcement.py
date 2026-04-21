"""
FIX 8 — Full governance enforcement.

G1: Tools tagged with 'fairness_guard' must have text params checked by FairnessGuard
    before execution. Explicit bias (Layer 1 regex) blocks execution.

G2: ToolDefinition has side_effects field, populated from YAML metadata.
"""
import pytest


class TestSideEffectsField:
    """FIX 8 G2: side_effects field on ToolDefinition + YAML sync."""

    def test_tool_definition_has_side_effects_field(self):
        from app.tools.registry import ToolDefinition
        tool = ToolDefinition(
            name="t",
            description="d",
            parameters_schema={},
            handler=lambda: None,
        )
        assert hasattr(tool, "side_effects"), "ToolDefinition must have side_effects"
        assert tool.side_effects == [], "Default empty list"

    def test_sync_populates_side_effects_from_yaml(self):
        from app.tools import initialize_tools
        from app.tools.registry import tool_registry
        initialize_tools()
        tools_with = [t for t in tool_registry._tools.values() if t.side_effects]
        assert len(tools_with) >= 10, (
            f"At least 10 tools must have side_effects after sync, got {len(tools_with)}"
        )


class TestFairnessGuardEnforcement:
    """FIX 8 G1: executor must invoke FairnessGuard for tagged tools."""

    @pytest.mark.asyncio
    async def test_fairness_guard_blocks_biased_text_param(self):
        """A tool with fairness_guard tag must block execution when text param has explicit bias."""
        from app.tools.registry import ToolDefinition, ToolRegistry
        from app.tools.executor import ToolExecutor

        async def dummy_handler(**kwargs):
            return {"status": "should_not_execute"}

        registry = ToolRegistry()
        registry.register(ToolDefinition(
            name="fg_test_tool",
            description="Test tool",
            parameters_schema={
                "type": "object",
                "properties": {"query": {"type": "string"}},
            },
            handler=dummy_handler,
            governance_tags=["fairness_guard"],
        ))

        executor = ToolExecutor(registry=registry)
        # Query with explicit bias — FairnessGuard Layer 1 should catch it
        result = await executor.execute(
            tool_name="fg_test_tool",
            parameters={"query": "somente homens para essa vaga"},
            agent_type="orchestrator",
        )
        # Result must NOT be success=True with real handler output
        # It must be blocked by FairnessGuard
        assert not result.success or (
            result.result and result.result.get("blocked_by_fairness_guard")
        ), (
            f"FairnessGuard must block biased text, got: {result.to_dict()}"
        )

    @pytest.mark.asyncio
    async def test_fairness_guard_allows_neutral_text(self):
        """Tool with fairness_guard tag + neutral text executes normally."""
        from app.tools.registry import ToolDefinition, ToolRegistry
        from app.tools.executor import ToolExecutor

        async def dummy_handler(**kwargs):
            return {"status": "ok", "query": kwargs.get("query")}

        registry = ToolRegistry()
        registry.register(ToolDefinition(
            name="fg_neutral_tool",
            description="Test",
            parameters_schema={
                "type": "object",
                "properties": {"query": {"type": "string"}},
            },
            handler=dummy_handler,
            governance_tags=["fairness_guard"],
        ))

        executor = ToolExecutor(registry=registry)
        result = await executor.execute(
            tool_name="fg_neutral_tool",
            parameters={"query": "desenvolvedor Python senior com 5 anos de experiência"},
            agent_type="orchestrator",
        )
        assert result.success, f"Neutral query must pass FairnessGuard, got: {result.to_dict()}"

    @pytest.mark.asyncio
    async def test_tool_without_fairness_tag_skips_check(self):
        """Tool without fairness_guard tag executes normally even with biased text
        (because the tag is opt-in per YAML declaration)."""
        from app.tools.registry import ToolDefinition, ToolRegistry
        from app.tools.executor import ToolExecutor

        async def dummy_handler(**kwargs):
            return {"status": "ok"}

        registry = ToolRegistry()
        registry.register(ToolDefinition(
            name="no_fg_tool",
            description="Test",
            parameters_schema={
                "type": "object",
                "properties": {"query": {"type": "string"}},
            },
            handler=dummy_handler,
            governance_tags=[],  # no fairness_guard tag
        ))

        executor = ToolExecutor(registry=registry)
        result = await executor.execute(
            tool_name="no_fg_tool",
            parameters={"query": "somente homens"},  # would be blocked if tag set
            agent_type="orchestrator",
        )
        assert result.success, "Tool without fairness_guard tag must not trigger check"
