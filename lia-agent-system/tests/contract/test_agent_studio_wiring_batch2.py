"""Contract tests: Talent Intelligence + Workforce wired into Agent Studio.

Validates tool registries, domain_tool_loaders entries, and migration syntax.
"""
import ast
import importlib
import inspect
import pathlib

import pytest


class TestTalentIntelligenceToolRegistry:

    def test_registry_returns_15_tools(self):
        from app.domains.talent_intelligence.tools.registry import (
            get_talent_intelligence_tools,
        )
        tools = get_talent_intelligence_tools()
        assert len(tools) == 15

    def test_tool_names_complete(self):
        from app.domains.talent_intelligence.tools.registry import (
            get_talent_intelligence_tools,
        )
        expected = {
            "infer_related_skills", "get_skill_adjacencies", "analyze_skill_gaps",
            "map_candidate_skills_to_ontology", "match_internal_candidates",
            "forecast_hiring_needs", "analyze_interview_recording",
            "detect_interview_bias", "generate_interview_opinion",
            "generate_candidate_feedback", "compare_interview_performance",
            "create_nurture_sequence", "get_engagement_metrics",
            "suggest_reengagement", "get_market_intelligence",
        }
        actual = {t.name for t in get_talent_intelligence_tools()}
        assert actual == expected

    def test_all_tools_callable(self):
        from app.domains.talent_intelligence.tools.registry import (
            get_talent_intelligence_tools,
        )
        for tool in get_talent_intelligence_tools():
            assert callable(tool.function), f"{tool.name} not callable"

    def test_loader_in_custom_agent_runtime(self):
        from app.domains.agent_studio.platform_tools_loader import (
            get_domain_tool_loaders,
        )
        loaders = get_domain_tool_loaders()
        assert "talent_intelligence" in loaders
        assert "get_talent_intelligence_tools" in loaders["talent_intelligence"]


class TestWorkforceToolRegistry:

    def test_registry_returns_1_tool(self):
        from app.domains.workforce.agents.workforce_tool_registry import (
            get_workforce_tools,
        )
        tools = get_workforce_tools()
        assert len(tools) == 1

    def test_tool_name(self):
        from app.domains.workforce.agents.workforce_tool_registry import (
            get_workforce_tools,
        )
        assert get_workforce_tools()[0].name == "get_workforce_plan_summary"

    def test_tool_callable(self):
        from app.domains.workforce.agents.workforce_tool_registry import (
            get_workforce_tools,
        )
        assert callable(get_workforce_tools()[0].function)

    def test_loader_in_custom_agent_runtime(self):
        from app.domains.agent_studio.platform_tools_loader import (
            get_domain_tool_loaders,
        )
        loaders = get_domain_tool_loaders()
        assert "workforce" in loaders
        assert "get_workforce_tools" in loaders["workforce"]


class TestBatch2MigrationSyntax:

    @pytest.mark.parametrize("filename,expected_down", [
        ("275_seed_talent_intelligence_agent_studio.py", "274_seed_ii_agent_studio"),
        ("276_seed_workforce_agent_studio.py", "275_seed_ti_agent_studio"),
    ])
    def test_migration_valid(self, filename, expected_down):
        path = pathlib.Path(f"alembic/versions/{filename}")
        assert path.exists(), f"{filename} not found"
        src = path.read_text()
        tree = ast.parse(src)

        func_names = {
            n.name for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        assert "upgrade" in func_names
        assert "downgrade" in func_names

        revisions = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id in ("revision", "down_revision"):
                        if isinstance(node.value, ast.Constant):
                            revisions[target.id] = node.value.value
        assert revisions.get("down_revision") == expected_down


class TestDomainToolLoadersComplete:
    """Verify all 3 Agent Studio Development domains are wired."""

    def test_all_three_domains_in_loaders(self):
        from app.domains.agent_studio.platform_tools_loader import (
            get_domain_tool_loaders,
        )
        loaders = get_domain_tool_loaders()
        for domain in ["interview_intelligence", "talent_intelligence", "workforce"]:
            assert domain in loaders, f"{domain} missing from domain_tool_loaders"
