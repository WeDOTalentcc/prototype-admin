"""
Testes unitários para tool scope_config (Sprint H — coverage gate 40%).

Cobertura:
  - PromptScope enum values
  - get_tools_for_scope: scopes válidos, scope inválido, tipos query/action/all
  - filter_tools_by_scope: lista de tools filtrada por scope
  - is_tool_allowed_in_scope: tool permitida vs não permitida
  - get_scope_system_prompt_addition: conteúdo do prompt, scope sem descrição
  - SCOPE_INTENT_MAPPING: resolução de tool → scope
"""
import pytest

pytestmark = pytest.mark.easy

from app.tools.scope_config import (
    PromptScope,
    get_tools_for_scope,
    filter_tools_by_scope,
    is_tool_allowed_in_scope,
    get_scope_system_prompt_addition,
    SCOPE_INTENT_MAPPING,
    FUNNEL_QUERY_TOOLS,
    FUNNEL_ACTION_TOOLS,
    VACANCY_QUERY_TOOLS,
    VACANCY_ACTION_TOOLS,
    IN_JOB_QUERY_TOOLS,
    IN_JOB_ACTION_TOOLS,
    GLOBAL_TOOLS,
)


# ---------------------------------------------------------------------------
# PromptScope enum
# ---------------------------------------------------------------------------

class TestPromptScope:

    def test_all_scopes_defined(self):
        scopes = {s.value for s in PromptScope}
        assert "talent_funnel" in scopes
        assert "job_table" in scopes
        assert "in_job" in scopes
        assert "global" in scopes

    def test_scope_is_string_enum(self):
        assert isinstance(PromptScope.TALENT_FUNNEL, str)


# ---------------------------------------------------------------------------
# get_tools_for_scope
# ---------------------------------------------------------------------------

class TestGetToolsForScope:

    def test_talent_funnel_all_includes_query_and_action(self):
        tools = get_tools_for_scope(PromptScope.TALENT_FUNNEL, "all")
        assert "search_candidates" in tools      # query
        assert "add_candidate_to_vacancy" in tools  # action

    def test_talent_funnel_query_only(self):
        query_tools = get_tools_for_scope(PromptScope.TALENT_FUNNEL, "query")
        assert "search_candidates" in query_tools
        assert "add_candidate_to_vacancy" not in query_tools

    def test_talent_funnel_action_only(self):
        action_tools = get_tools_for_scope(PromptScope.TALENT_FUNNEL, "action")
        assert "add_candidate_to_vacancy" in action_tools
        assert "search_candidates" not in action_tools

    def test_job_table_all(self):
        tools = get_tools_for_scope(PromptScope.JOB_TABLE, "all")
        assert "search_jobs" in tools
        assert "create_job" in tools

    def test_in_job_all(self):
        tools = get_tools_for_scope(PromptScope.IN_JOB, "all")
        assert "update_candidate_stage" in tools
        assert "schedule_interview" in tools

    def test_global_has_generate_report(self):
        tools = get_tools_for_scope(PromptScope.GLOBAL, "all")
        assert "generate_report" in tools

    def test_invalid_scope_returns_empty_set(self):
        tools = get_tools_for_scope("non_existent_scope", "all")  # type: ignore
        assert tools == set()

    def test_invalid_tool_type_falls_back_to_all(self):
        tools = get_tools_for_scope(PromptScope.TALENT_FUNNEL, "unknown_type")
        all_tools = get_tools_for_scope(PromptScope.TALENT_FUNNEL, "all")
        assert tools == all_tools

    def test_all_equals_union_of_query_and_action(self):
        query = get_tools_for_scope(PromptScope.TALENT_FUNNEL, "query")
        action = get_tools_for_scope(PromptScope.TALENT_FUNNEL, "action")
        all_tools = get_tools_for_scope(PromptScope.TALENT_FUNNEL, "all")
        assert all_tools == query | action


# ---------------------------------------------------------------------------
# filter_tools_by_scope
# ---------------------------------------------------------------------------

class TestFilterToolsByScope:

    def test_filters_allowed_tools(self):
        tools = [
            {"name": "search_candidates"},
            {"name": "create_job"},  # not in TALENT_FUNNEL
            {"name": "get_candidate_stats"},
        ]
        filtered = filter_tools_by_scope(tools, PromptScope.TALENT_FUNNEL)
        names = {t["name"] for t in filtered}
        assert "search_candidates" in names
        assert "get_candidate_stats" in names
        assert "create_job" not in names

    def test_empty_list_returns_empty(self):
        assert filter_tools_by_scope([], PromptScope.IN_JOB) == []

    def test_all_filtered_when_none_match(self):
        tools = [{"name": "non_existent_tool"}]
        filtered = filter_tools_by_scope(tools, PromptScope.TALENT_FUNNEL)
        assert filtered == []

    def test_tools_without_name_field_excluded(self):
        tools = [{"id": "t1"}, {"name": "search_candidates"}]
        filtered = filter_tools_by_scope(tools, PromptScope.TALENT_FUNNEL)
        assert len(filtered) == 1
        assert filtered[0]["name"] == "search_candidates"


# ---------------------------------------------------------------------------
# is_tool_allowed_in_scope
# ---------------------------------------------------------------------------

class TestIsToolAllowedInScope:

    def test_search_candidates_in_talent_funnel(self):
        assert is_tool_allowed_in_scope("search_candidates", PromptScope.TALENT_FUNNEL) is True

    def test_search_candidates_not_in_job_table(self):
        # search_candidates belongs to TALENT_FUNNEL, not JOB_TABLE
        assert is_tool_allowed_in_scope("search_candidates", PromptScope.JOB_TABLE) is False

    def test_create_job_in_job_table(self):
        assert is_tool_allowed_in_scope("create_job", PromptScope.JOB_TABLE) is True

    def test_update_candidate_stage_in_in_job(self):
        assert is_tool_allowed_in_scope("update_candidate_stage", PromptScope.IN_JOB) is True

    def test_nonexistent_tool_returns_false(self):
        assert is_tool_allowed_in_scope("fake_tool", PromptScope.TALENT_FUNNEL) is False

    def test_generate_report_in_global(self):
        assert is_tool_allowed_in_scope("generate_report", PromptScope.GLOBAL) is True


# ---------------------------------------------------------------------------
# get_scope_system_prompt_addition
# ---------------------------------------------------------------------------

class TestGetScopeSystemPromptAddition:

    def test_talent_funnel_has_capabilities(self):
        prompt = get_scope_system_prompt_addition(PromptScope.TALENT_FUNNEL)
        assert "Funil de Talentos" in prompt
        assert "PODE fazer" in prompt
        assert "NÃO PODE fazer" in prompt

    def test_job_table_has_content(self):
        prompt = get_scope_system_prompt_addition(PromptScope.JOB_TABLE)
        assert "Tabela de Vagas" in prompt
        assert len(prompt) > 50

    def test_in_job_has_content(self):
        prompt = get_scope_system_prompt_addition(PromptScope.IN_JOB)
        assert "Dentro da Vaga" in prompt

    def test_scope_without_description_returns_empty(self):
        # GLOBAL has no entry in SCOPE_DESCRIPTIONS
        result = get_scope_system_prompt_addition(PromptScope.GLOBAL)
        assert result == ""

    def test_unknown_scope_returns_empty(self):
        result = get_scope_system_prompt_addition("nonexistent")  # type: ignore
        assert result == ""


# ---------------------------------------------------------------------------
# SCOPE_INTENT_MAPPING
# ---------------------------------------------------------------------------

class TestScopeIntentMapping:

    def test_search_candidates_maps_to_talent_funnel(self):
        assert SCOPE_INTENT_MAPPING["search_candidates"] == PromptScope.TALENT_FUNNEL

    def test_create_job_maps_to_job_table(self):
        assert SCOPE_INTENT_MAPPING["create_job"] == PromptScope.JOB_TABLE

    def test_update_candidate_stage_maps_to_in_job(self):
        assert SCOPE_INTENT_MAPPING["update_candidate_stage"] == PromptScope.IN_JOB

    def test_mapping_covers_all_scopes(self):
        scopes_present = set(SCOPE_INTENT_MAPPING.values())
        assert PromptScope.TALENT_FUNNEL in scopes_present
        assert PromptScope.JOB_TABLE in scopes_present
        assert PromptScope.IN_JOB in scopes_present
