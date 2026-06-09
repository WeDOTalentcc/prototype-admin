"""Sensor: simetria dos ui tools (open_ui + apply_table_state) em todos os
caminhos conversacionais — least-privilege + anti-ghost.

Cobre: helpers, categoria INTERFACE, grants explicitos por agente, e scoping
federado (tool_catalog) — open_ui universal, apply_table_state so na surface
com ponte (talent_funnel).
"""
from __future__ import annotations

import inspect


def test_helpers_return_expected_tools():
    from app.domains.recruiter_assistant.agents.ui_tool_registry import (
        get_open_ui_tools,
        get_table_state_tools,
    )
    assert [t.name for t in get_open_ui_tools()] == ["open_ui"]
    assert [t.name for t in get_table_state_tools()] == ["apply_table_state", "select_rows"]


def test_both_ui_tools_category_interface():
    from app.tools.categories import category_for_tool, ToolCategory
    assert category_for_tool("open_ui") == ToolCategory.INTERFACE
    assert category_for_tool("apply_table_state") == ToolCategory.INTERFACE


def test_open_ui_granted_to_conversational_agents():
    # grant explicito (least-privilege): cada agente conversacional de dados
    # referencia get_open_ui_tools no _get_tools.
    cases = [
        "app.domains.recruiter_assistant.agents.talent_funnel_react_agent",
        "app.domains.recruiter_assistant.agents.kanban_react_agent",
        "app.domains.recruiter_assistant.agents.jobs_mgmt_react_agent",
        "app.domains.cv_screening.agents.pipeline_react_agent",
        "app.domains.sourcing.agents.sourcing_react_agent",
        "app.domains.talent_pool.agents.talent_pool_agent",
    ]
    import importlib
    for mod_path in cases:
        mod = importlib.import_module(mod_path)
        src = inspect.getsource(mod)
        assert "get_open_ui_tools()" in src, f"{mod_path} sem grant open_ui"


def test_apply_table_state_only_agents_with_fe_bridge():
    # anti-ghost: apply_table_state so onde a surface tem ponte FE.
    # Pontes ativas: candidates (talent_funnel), jobs (jobs_mgmt), kanban
    # (kanban_react_agent), recrutar (pipeline_react_agent via pipeline-overview-
    # page.tsx), talent_pool (talent_pool_agent via TalentPoolPage.tsx).
    # Sem ponte: sourcing (ainda sem tabela FE).
    import importlib
    for mod_path in (
        "app.domains.recruiter_assistant.agents.talent_funnel_react_agent",
        "app.domains.recruiter_assistant.agents.jobs_mgmt_react_agent",
        "app.domains.recruiter_assistant.agents.kanban_react_agent",
        "app.domains.cv_screening.agents.pipeline_react_agent",
        "app.domains.talent_pool.agents.talent_pool_agent",
    ):
        mod = importlib.import_module(mod_path)
        assert "get_table_state_tools()" in inspect.getsource(mod), (
            f"{mod_path} deveria ter apply_table_state (surface com ponte FE ativa)"
        )
    for mod_path in (
        "app.domains.sourcing.agents.sourcing_react_agent",
    ):
        mod = importlib.import_module(mod_path)
        assert "get_table_state_tools()" not in inspect.getsource(mod), (
            f"{mod_path} NAO deve ter apply_table_state (sem ponte FE = ghost)"
        )


def test_federated_scoping_talent_funnel_has_both():
    # Q4: sob scoping dinamico, talent_funnel inclui open_ui + apply_table_state.
    from app.shared.tool_catalog import get_scoped_tool_definitions
    names = {getattr(t, "name", None) for t in get_scoped_tool_definitions("talent_funnel")}
    assert "open_ui" in names
    assert "apply_table_state" in names


def test_federated_scoping_open_ui_universal_apply_table_scoped():
    # open_ui em _GLOBAL_ESSENTIALS => presente em TODO escopo. apply_table_state
    # so nos escopos com ponte FE (talent_funnel + job_table), NAO em in_job.
    from app.shared.tool_catalog import get_scoped_tool_definitions
    jt = {getattr(t, "name", None) for t in get_scoped_tool_definitions("job_table")}
    assert "open_ui" in jt and "apply_table_state" in jt, "job_table tem ponte (Vagas)"
    ij = {getattr(t, "name", None) for t in get_scoped_tool_definitions("in_job")}
    assert "open_ui" in ij and "apply_table_state" in ij, "in_job tem ponte (Kanban)"
    gl = {getattr(t, "name", None) for t in get_scoped_tool_definitions("global")}
    assert "open_ui" in gl, "open_ui universal"
    assert "apply_table_state" not in gl, "global sem surface de tabela = sem ponte"
