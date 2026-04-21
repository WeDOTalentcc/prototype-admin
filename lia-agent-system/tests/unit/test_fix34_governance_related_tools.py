"""
FIX 3 + FIX 4 - governance_tags and related_tools.

TDD Red tests:
- ToolDefinition has governance_tags and related_tools fields
- sync_descriptions_from_yaml() populates both from YAML
- ToolExecutor returns HITL-required result when requires_hitl tag present
- (FIX 4) agentic_loop.py exposes a helper to get related tool suggestions
"""
import pytest


class TestToolDefinitionFields:
    """FIX 3/4: ToolDefinition must expose governance_tags and related_tools."""

    def test_tool_definition_has_governance_tags_field(self):
        from app.tools.registry import ToolDefinition
        tool = ToolDefinition(
            name="t_test",
            description="test",
            parameters_schema={},
            handler=lambda: None,
        )
        assert hasattr(tool, "governance_tags"), "ToolDefinition must have governance_tags"
        assert tool.governance_tags == [], "Default should be empty list"

    def test_tool_definition_has_related_tools_field(self):
        from app.tools.registry import ToolDefinition
        tool = ToolDefinition(
            name="t_test2",
            description="test",
            parameters_schema={},
            handler=lambda: None,
        )
        assert hasattr(tool, "related_tools"), "ToolDefinition must have related_tools"
        assert tool.related_tools == [], "Default should be empty list"


class TestSyncPopulatesGovernanceAndRelated:
    """FIX 3/4: sync_descriptions_from_yaml must also populate new fields."""

    def test_sync_populates_governance_tags_from_yaml(self):
        """After sync, at least some tools must have governance_tags populated.

        FIX 34 v2 (2026-04-21): force clear + initialize_tools so
        sync_descriptions_from_yaml ALWAYS runs. Previously the conditional
        guard `if not tool_registry.list_tools()` skipped the sync path when
        other tests had pre-registered tools via their own register_*() calls
        (which don't invoke YAML sync). YAML has 105 tools with governance_tags
        declared — sync is the producer; test isolation was the bug.
        """
        from app.tools import initialize_tools
        from app.tools.registry import tool_registry

        # FIX 34 v2: full reinit so sync_descriptions_from_yaml runs regardless
        # of what prior tests left in the registry.
        tool_registry.clear()
        initialize_tools()

        tools_with_governance = [
            t for t in tool_registry._tools.values()
            if getattr(t, "governance_tags", [])
        ]
        assert len(tools_with_governance) >= 5, (
            f"At least 5 tools should have governance_tags after sync, found "
            f"{len(tools_with_governance)}. Check tool_registry_metadata.yaml "
            f"declares governance_tags for core tools."
        )

    def test_sync_populates_related_tools_from_yaml(self):
        """FIX 34 v2: same isolation fix as governance_tags test."""
        from app.tools import initialize_tools
        from app.tools.registry import tool_registry

        # FIX 34 v2: clear + reinit for clean sync
        tool_registry.clear()
        initialize_tools()

        tools_with_related = [
            t for t in tool_registry._tools.values()
            if getattr(t, "related_tools", [])
        ]
        assert len(tools_with_related) >= 5, (
            f"At least 5 tools should have related_tools after sync, found "
            f"{len(tools_with_related)}. Check tool_registry_metadata.yaml "
            f"declares related_tools for core tools."
        )


class TestExecutorEnforcesHITL:
    """FIX 3: Executor must respect requires_hitl governance tag."""

    @pytest.mark.asyncio
    async def test_executor_flags_requires_hitl_tool(self):
        """A tool marked requires_hitl should produce an HITL-flagged result."""
        from app.tools.registry import ToolDefinition, ToolRegistry
        from app.tools.executor import ToolExecutor

        async def dummy_handler(**kwargs):
            return {"status": "ok"}

        registry = ToolRegistry()
        tool = ToolDefinition(
            name="hitl_test_tool",
            description="A tool requiring HITL",
            parameters_schema={"type": "object", "properties": {}},
            handler=dummy_handler,
            governance_tags=["requires_hitl"],
        )
        registry.register(tool)

        executor = ToolExecutor(registry=registry)
        result = await executor.execute(
            tool_name="hitl_test_tool",
            parameters={},
            agent_type="orchestrator",
        )
        # Result must signal HITL — either via result.requires_confirmation
        # or via metadata in result.result
        is_hitl = (
            (result.result or {}).get("requires_hitl") is True
            or (result.result or {}).get("status") == "pending_hitl_confirmation"
            or result.error and "hitl" in str(result.error).lower()
        )
        assert is_hitl, (
            f"Tool with requires_hitl must signal HITL confirmation, got: {result.to_dict()}"
        )


class TestAgenticLoopRelatedTools:
    """FIX 4: related_tools should surface as suggestions."""

    def test_registry_exposes_related_tools(self):
        """ToolRegistry must have a method to get related tools for a name."""
        from app.tools.registry import ToolDefinition, ToolRegistry

        async def dummy(**k):
            return {"ok": True}

        registry = ToolRegistry()
        registry.register(ToolDefinition(
            name="tool_a",
            description="A",
            parameters_schema={},
            handler=dummy,
            related_tools=["tool_b", "tool_c"],
        ))
        registry.register(ToolDefinition(
            name="tool_b", description="B", parameters_schema={}, handler=dummy,
        ))
        registry.register(ToolDefinition(
            name="tool_c", description="C", parameters_schema={}, handler=dummy,
        ))

        tool_a = registry.get_tool("tool_a")
        assert tool_a.related_tools == ["tool_b", "tool_c"]
