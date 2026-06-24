"""F4 + F5 — Expansão do agente federado recruiter_copilot (2026-06-09).

Testa que:
1. get_candidate_mutation_tools() retorna update_candidate_stage e reject_candidate
2. get_recruiter_copilot_tools() agora inclui as 3 novas ferramentas F4
3. O total de tools carregados é correto (20)
4. LIA_FEDERATED_PRIMARY flag habilita roteamento federated
"""
from __future__ import annotations

import asyncio
import os


def test_candidate_mutation_tools_getter():
    """get_candidate_mutation_tools retorna update_candidate_stage e reject_candidate."""
    from app.domains.cv_screening.tools.candidate_tools import get_candidate_mutation_tools
    tools = get_candidate_mutation_tools()
    names = {t.name for t in tools}
    assert "update_candidate_stage" in names, f"update_candidate_stage não encontrado: {names}"
    assert "reject_candidate" in names, f"reject_candidate não encontrado: {names}"
    assert len(tools) == 2, f"Esperado 2 tools, obteve {len(tools)}: {names}"


def test_candidate_mutation_tools_have_handlers():
    """Cada tool do getter tem handler callable (não None)."""
    from app.domains.cv_screening.tools.candidate_tools import get_candidate_mutation_tools
    for tool in get_candidate_mutation_tools():
        assert tool.handler is not None, f"{tool.name}: handler é None"
        assert callable(tool.handler), f"{tool.name}: handler não é callable"


def test_federated_spec_includes_f4_tools():
    """_FEDERATION_SPEC agora inclui update_candidate_stage, reject_candidate, close_job."""
    from app.domains.recruiter_assistant.agents.recruiter_copilot_tool_registry import (
        _FEDERATION_SPEC,
    )
    spec_map = {(src, name) for src, name in _FEDERATION_SPEC}
    assert ("cv_screening", "update_candidate_stage") in spec_map, "update_candidate_stage ausente do FEDERATION_SPEC"
    assert ("cv_screening", "reject_candidate") in spec_map, "reject_candidate ausente do FEDERATION_SPEC"
    assert ("jobs", "close_job") in spec_map, "close_job ausente do FEDERATION_SPEC"


def test_recruiter_copilot_tools_load_with_f4():
    """get_recruiter_copilot_tools carrega sem erro e inclui as 3 novas tools."""
    from app.domains.recruiter_assistant.agents.recruiter_copilot_tool_registry import (
        get_recruiter_copilot_tools,
    )
    tools = get_recruiter_copilot_tools()
    names = {t.name for t in tools}

    # Tools F4 adicionadas
    assert "update_candidate_stage" in names, "F4: update_candidate_stage ausente"
    assert "reject_candidate" in names, "F4: reject_candidate ausente"
    assert "close_job" in names, "F4: close_job ausente"

    # Tools anteriores ainda presentes (regressão)
    assert "batch_move_candidates" in names, "regressão: batch_move_candidates sumiu"
    assert "apply_table_state" in names, "regressão: apply_table_state sumiu"
    assert "open_ui" in names, "regressão: open_ui sumiu"
    assert "list_candidates" in names, "regressão: list_candidates sumiu"


def test_recruiter_copilot_total_tool_count():
    """Total de tools no recruiter_copilot deve ser exatamente 20 (17 anteriores + 3 F4)."""
    from app.domains.recruiter_assistant.agents.recruiter_copilot_tool_registry import (
        get_recruiter_copilot_tools,
    )
    tools = get_recruiter_copilot_tools()
    assert len(tools) == 20, (
        f"Esperado 20 tools (17 + 3 F4), obteve {len(tools)}: {[t.name for t in tools]}"
    )


def test_federated_primary_flag_controls_routing(monkeypatch):
    """federated_primary_enabled() retorna True quando LIA_FEDERATED_PRIMARY=1."""
    monkeypatch.setenv("LIA_FEDERATED_PRIMARY", "true")
    from app.tools.scope_config import federated_primary_enabled
    assert federated_primary_enabled() is True


def test_federated_scoping_implied_by_primary(monkeypatch):
    """federated_scoping_enabled() é True quando LIA_FEDERATED_PRIMARY=1."""
    monkeypatch.setenv("LIA_FEDERATED_PRIMARY", "true")
    from app.tools.scope_config import federated_scoping_enabled
    assert federated_scoping_enabled() is True
