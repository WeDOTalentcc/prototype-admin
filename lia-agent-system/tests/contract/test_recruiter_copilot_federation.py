"""Sensor canonical (2026-06-03) — chat global FEDERADO (recruiter_copilot).

Pina o fix do bug "chat global cego" (transcript Paulo 2026-06-03):
- recruiter_assistant resolvia pra UM agente de pagina (talent/kanban) sem
  list_jobs -> "liste minhas vagas" confabulava "nenhuma vaga".
- Agora resolve pro agente FEDERADO recruiter_copilot, que tem leitura de
  vagas + candidatos + pipeline e acoes de escrita (HITL).
"""
import pytest


def test_federation_includes_jobs_and_candidates_read_tools():
    from app.domains.recruiter_assistant.agents.recruiter_copilot_tool_registry import (
        get_recruiter_copilot_tool_names,
    )
    names = set(get_recruiter_copilot_tool_names())
    for required in (
        "list_jobs", "view_job_details", "list_candidates",
        "search_candidates", "view_candidate_profile",
    ):
        assert required in names, f"{required!r} ausente no set federado: {names}"


def test_federation_includes_write_actions():
    from app.domains.recruiter_assistant.agents.recruiter_copilot_tool_registry import (
        get_recruiter_copilot_tool_names,
    )
    names = set(get_recruiter_copilot_tool_names())
    assert "batch_move_candidates" in names
    assert "pause_job" in names


def test_copilot_agent_registered():
    from app.api.v1.agent_chat_ws import _ensure_agents_loaded
    from app.shared.agents.agent_registry import AgentRegistry
    _ensure_agents_loaded()
    assert AgentRegistry().is_registered("recruiter_copilot"), (
        "recruiter_copilot nao registrado no AgentRegistry — confira o import "
        "em agent_chat_ws._ensure_agents_loaded e o @register_agent."
    )


def test_recruiter_assistant_domain_resolves_to_copilot():
    """O bug: recruiter_assistant resolvia pra talent/kanban (sem list_jobs).
    Agora deve resolver pro agente federado recruiter_copilot."""
    from app.api.v1.agent_chat_ws import _ensure_agents_loaded
    from app.shared.agents.agent_registry import AgentRegistry
    from app.domains.workflow import DomainWorkflow
    _ensure_agents_loaded()
    wf = DomainWorkflow()
    resolved = wf._resolve_agent_domain("recruiter_assistant", "quick_question")
    assert resolved == "recruiter_copilot", (
        f"recruiter_assistant resolveu pra {resolved!r} (esperado "
        f"'recruiter_copilot'). Confira _DOMAIN_TO_AGENT em workflow.py."
    )
    assert AgentRegistry().is_registered(resolved)


def test_copilot_agent_exposes_federated_tools():
    from app.api.v1.agent_chat_ws import _ensure_agents_loaded
    from app.shared.agents.agent_registry import AgentRegistry
    _ensure_agents_loaded()
    agent = AgentRegistry().get_instance("recruiter_copilot")
    assert agent is not None, "get_instance('recruiter_copilot') retornou None"
    tools = set(agent.available_tools)
    assert "list_jobs" in tools, f"list_jobs ausente: {tools}"
    assert "list_candidates" in tools, f"list_candidates ausente: {tools}"
