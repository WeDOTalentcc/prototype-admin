"""Contract tests: Interview Intelligence wired into Agent Studio.

Validates:
1. Tool registry returns 5 ToolDefinitions
2. domain_tool_loaders entry resolves
3. PLATFORM_TOOLS_REGISTRY has all 5 tools
4. Tool functions are callable (signature check)
5. Template seed migration is syntactically valid
"""
import importlib
import inspect

import pytest


class TestInterviewIntelligenceToolRegistry:
    """T1/T2: Tool registry returns correct ToolDefinitions."""

    def test_registry_returns_5_tools(self):
        from app.domains.interview_intelligence.tools.registry import (
            get_interview_intelligence_tools,
        )
        tools = get_interview_intelligence_tools()
        assert len(tools) == 5

    def test_tool_names_match_platform_registry(self):
        from app.domains.interview_intelligence.tools.registry import (
            get_interview_intelligence_tools,
        )
        expected = {
            "analyze_interview_recording",
            "detect_interview_bias",
            "compare_interview_performance",
            "generate_interview_opinion",
            "generate_candidate_feedback",
        }
        actual = {t.name for t in get_interview_intelligence_tools()}
        assert actual == expected

    def test_all_tools_have_callable_function(self):
        from app.domains.interview_intelligence.tools.registry import (
            get_interview_intelligence_tools,
        )
        for tool in get_interview_intelligence_tools():
            assert callable(tool.function), f"{tool.name} function not callable"

    def test_tool_functions_accept_kwargs(self):
        from app.domains.interview_intelligence.tools.registry import (
            get_interview_intelligence_tools,
        )
        for tool in get_interview_intelligence_tools():
            sig = inspect.signature(tool.function)
            param_names = list(sig.parameters.keys())
            has_kwargs = any(
                p.kind == inspect.Parameter.VAR_KEYWORD
                for p in sig.parameters.values()
            )
            assert has_kwargs, (
                f"{tool.name} must accept **kwargs for tool_handler compat"
            )


class TestDomainToolLoadersEntry:
    """T3: domain_tool_loaders has interview_intelligence entry."""

    def test_loader_path_importable(self):
        loader_path = "app.domains.interview_intelligence.tools.registry.get_interview_intelligence_tools"
        module_path, func_name = loader_path.rsplit(".", 1)
        mod = importlib.import_module(module_path)
        func = getattr(mod, func_name)
        assert callable(func)

    def test_loader_in_custom_agent_runtime(self):
        from app.domains.agent_studio.platform_tools_loader import (
            get_domain_tool_loaders,
        )
        loaders = get_domain_tool_loaders()
        assert "interview_intelligence" in loaders, (
            "domain_tool_loaders missing interview_intelligence entry"
        )

    def test_loader_returns_list(self):
        from app.domains.interview_intelligence.tools.registry import (
            get_interview_intelligence_tools,
        )
        result = get_interview_intelligence_tools()
        assert isinstance(result, list)
        assert len(result) > 0


class TestPlatformToolsRegistryAlignment:
    """Verify PLATFORM_TOOLS_REGISTRY has all 5 interview intelligence tools."""

    def test_all_tools_in_platform_registry(self):
        from app.domains.interview_intelligence.tools.registry import (
            get_interview_intelligence_tools,
        )
        from app.domains.agent_studio.platform_tools_loader import (
            get_platform_tools_registry,
        )
        registry = get_platform_tools_registry()
        tool_names = {t.name for t in get_interview_intelligence_tools()}
        missing = tool_names - set(registry.keys())
        assert not missing, f"Tools missing from PLATFORM_TOOLS_REGISTRY: {missing}"


class TestMigrationSyntax:
    """T5: Migration file is syntactically valid Python."""

    def test_migration_parses(self):
        import ast
        import pathlib

        path = pathlib.Path(
            "alembic/versions/274_seed_interview_intelligence_agent_studio.py"
        )
        assert path.exists(), "Migration file not found"
        src = path.read_text()
        ast.parse(src)

    def test_migration_has_upgrade_downgrade(self):
        import ast
        import pathlib

        src = pathlib.Path(
            "alembic/versions/274_seed_interview_intelligence_agent_studio.py"
        ).read_text()
        tree = ast.parse(src)
        func_names = {
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        assert "upgrade" in func_names
        assert "downgrade" in func_names

    def test_migration_revision_chain(self):
        import ast
        import pathlib

        src = pathlib.Path(
            "alembic/versions/274_seed_interview_intelligence_agent_studio.py"
        ).read_text()
        tree = ast.parse(src)
        revisions = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id in ("revision", "down_revision"):
                        if isinstance(node.value, ast.Constant):
                            revisions[target.id] = node.value.value
        assert "revision" in revisions
        assert "down_revision" in revisions
        assert revisions["down_revision"] == "273_create_role_scope_filters"
