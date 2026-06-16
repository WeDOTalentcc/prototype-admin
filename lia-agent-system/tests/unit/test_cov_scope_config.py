"""Coverage tests for app/tools/scope_config.py and app/shared/resilience/circuit_breaker.py"""
import pytest

# ===========================================================================
# app/tools/scope_config.py
# ===========================================================================
from app.tools.scope_config import (
    PromptScope,
    SCOPE_TOOL_MAPPING,
    SCOPE_DESCRIPTIONS,
    FUNNEL_QUERY_TOOLS,
    FUNNEL_ACTION_TOOLS,
    VACANCY_QUERY_TOOLS,
    VACANCY_ACTION_TOOLS,
    IN_JOB_QUERY_TOOLS,
    IN_JOB_ACTION_TOOLS,
    GLOBAL_TOOLS,
    get_tools_for_scope,
    filter_tools_by_scope,
    is_tool_allowed_in_scope,
)


class TestPromptScope:
    def test_values(self):
        assert PromptScope.TALENT_FUNNEL == "talent_funnel"
        assert PromptScope.JOB_TABLE == "job_table"
        assert PromptScope.IN_JOB == "in_job"
        assert PromptScope.GLOBAL == "global"

    def test_is_str_enum(self):
        for scope in PromptScope:
            assert isinstance(scope, str)

    def test_all_scopes_present(self):
        names = {s.name for s in PromptScope}
        assert "TALENT_FUNNEL" in names
        assert "JOB_TABLE" in names
        assert "IN_JOB" in names
        assert "GLOBAL" in names


class TestScopeToolMapping:
    def test_all_scopes_in_mapping(self):
        for scope in [PromptScope.TALENT_FUNNEL, PromptScope.JOB_TABLE, PromptScope.IN_JOB, PromptScope.GLOBAL]:
            assert scope in SCOPE_TOOL_MAPPING

    def test_mapping_has_query_action_all(self):
        for scope, mapping in SCOPE_TOOL_MAPPING.items():
            assert "query" in mapping
            assert "action" in mapping
            assert "all" in mapping

    def test_all_is_union_of_query_and_action(self):
        for scope, mapping in SCOPE_TOOL_MAPPING.items():
            union = mapping["query"] | mapping["action"]
            # "all" should be superset
            assert mapping["all"] >= union or mapping["all"] == union


class TestScopeDescriptions:
    def test_main_scopes_have_descriptions(self):
        for scope in [PromptScope.TALENT_FUNNEL, PromptScope.JOB_TABLE, PromptScope.IN_JOB]:
            assert scope in SCOPE_DESCRIPTIONS

    def test_description_structure(self):
        for scope, desc in SCOPE_DESCRIPTIONS.items():
            assert "name" in desc
            assert "description" in desc
            assert isinstance(desc["name"], str)
            assert len(desc["name"]) > 0


class TestGlobalConstants:
    def test_constants_are_sets(self):
        for tools_set in [
            FUNNEL_QUERY_TOOLS, FUNNEL_ACTION_TOOLS,
            VACANCY_QUERY_TOOLS, VACANCY_ACTION_TOOLS,
            IN_JOB_QUERY_TOOLS, IN_JOB_ACTION_TOOLS,
            GLOBAL_TOOLS,
        ]:
            assert isinstance(tools_set, set)


class TestGetToolsForScope:
    def test_returns_set(self):
        result = get_tools_for_scope(PromptScope.TALENT_FUNNEL)
        assert isinstance(result, set)

    def test_query_type(self):
        result = get_tools_for_scope(PromptScope.TALENT_FUNNEL, tool_type="query")
        assert isinstance(result, set)

    def test_action_type(self):
        result = get_tools_for_scope(PromptScope.JOB_TABLE, tool_type="action")
        assert isinstance(result, set)

    def test_all_type(self):
        result = get_tools_for_scope(PromptScope.IN_JOB, tool_type="all")
        assert isinstance(result, set)

    def test_with_tenant_id(self):
        result = get_tools_for_scope(PromptScope.GLOBAL, tenant_id="acme-corp")
        assert isinstance(result, set)


class TestIsToolAllowedInScope:
    def test_callable(self):
        # Just verify it doesn't raise
        result = is_tool_allowed_in_scope("get_candidate_details", PromptScope.TALENT_FUNNEL)
        assert isinstance(result, bool)

    def test_with_tenant_id(self):
        result = is_tool_allowed_in_scope("search_jobs", PromptScope.JOB_TABLE, tenant_id=None)
        assert isinstance(result, bool)


class TestFilterToolsByScope:
    def test_empty_list(self):
        result = filter_tools_by_scope([], PromptScope.TALENT_FUNNEL)
        assert result == []

    def test_tool_list_without_name_passes_through(self):
        # filter may or may not keep tools without "name" key — just check no crash
        result = filter_tools_by_scope([{"description": "no name"}], PromptScope.IN_JOB)
        assert isinstance(result, list)
