"""
Task #317 — Smoke tests for A3/A4 compliance audit:

- A3 / interview_scheduling: ``InterviewGraph`` is reachable via the
  YAML-driven flat agent registry and the prompt path resolves to an
  existing file.
- A4 / wsi_interview: same expectations for ``WSIInterviewGraph``.
- Composition (not inheritance): both graphs propagate
  ``state['company_id']`` into ``tenant_llm_context`` so downstream
  LLM consumers (``get_provider_for_tenant`` etc.) honour Choose Your AI.
"""
import os

import pytest


REGISTRY_YAML = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "app",
    "agents_registry.yaml",
)


def _reload_registry():
    from lia_agents_core import react_agent_registry as rr
    rr._flat_registry.clear()
    return rr.reload_from_yaml(REGISTRY_YAML)


@pytest.mark.parametrize("agent_name", ["interview_scheduling", "wsi_interview"])
def test_registry_resolves_interview_graphs(agent_name):
    """A3/A4 — ambos os grafos aparecem em agents_registry.yaml e resolvem."""
    from lia_agents_core import react_agent_registry as rr

    loaded = _reload_registry()
    assert agent_name in loaded, f"{agent_name} ausente do registry: {loaded}"

    entry = rr.get(agent_name)
    assert entry is not None
    assert entry.get("enabled", True) is True
    assert entry["domain"] == agent_name
    assert entry["class_path"].endswith(("InterviewGraph", "WSIInterviewGraph"))


@pytest.mark.parametrize(
    "agent_name,expected_suffix",
    [
        ("interview_scheduling", "interview_graph.InterviewGraph"),
        ("wsi_interview", "wsi_interview_graph.WSIInterviewGraph"),
    ],
)
def test_registry_class_path_imports(agent_name, expected_suffix):
    """class_path no YAML deve apontar para uma classe que de fato importa."""
    import importlib

    from lia_agents_core import react_agent_registry as rr
    _reload_registry()
    entry = rr.get(agent_name)
    assert entry["class_path"].endswith(expected_suffix)

    module_path, _, cls_name = entry["class_path"].rpartition(".")
    mod = importlib.import_module(module_path)
    cls = getattr(mod, cls_name)
    assert callable(cls), f"{cls_name} não é instanciável"


@pytest.mark.parametrize(
    "agent_name",
    ["interview_scheduling", "wsi_interview"],
)
def test_registry_system_prompt_path_exists(agent_name):
    """O system_prompt_path declarado no YAML deve existir no repositório."""
    from lia_agents_core import react_agent_registry as rr

    _reload_registry()
    entry = rr.get(agent_name)
    prompt_path = entry.get("system_prompt_path")
    assert prompt_path, f"{agent_name} sem system_prompt_path"

    repo_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    abs_path = os.path.join(repo_root, prompt_path)
    assert os.path.isfile(abs_path), f"prompt ausente: {abs_path}"


def test_wsi_tenant_scope_sets_and_resets_contextvar(monkeypatch):
    """A4 — _wsi_tenant_scope ativa o tenant_llm_context durante a execução."""
    from app.middleware.auth_enforcement import _current_company_id
    from app.domains.cv_screening.agents.wsi_interview_graph import _wsi_tenant_scope

    # Garante que começamos limpos
    _current_company_id.set("")
    assert _current_company_id.get("") == ""

    seen = {}
    with _wsi_tenant_scope("tenant-xyz"):
        seen["inside"] = _current_company_id.get("")
    seen["outside"] = _current_company_id.get("")

    assert seen["inside"] == "tenant-xyz"
    assert seen["outside"] == ""


def test_interview_graph_invoke_propagates_tenant(monkeypatch):
    """A3 — _invoke_langgraph deve setar o tenant antes de invocar o grafo."""
    import asyncio

    from app.middleware.auth_enforcement import _current_company_id
    from app.domains.interview_scheduling.agents.interview_graph import InterviewGraph

    _current_company_id.set("")
    captured = {}

    class _FakeCompiled:
        async def ainvoke(self, state, config=None):
            captured["tenant"] = _current_company_id.get("")
            # Simula resposta minimalista do grafo
            return {"workflow_data": {"confidence_score": 0.8}}

    g = InterviewGraph()
    g._compiled = _FakeCompiled()

    state = {
        "session_id": "sess-1",
        "company_id": "tenant-abc",
        "user_id": "u",
        "message": "hi",
        "workflow_data": {},
    }
    asyncio.run(g._invoke_langgraph(state))

    assert captured["tenant"] == "tenant-abc"
    # Após retorno, contextvar foi restaurado
    assert _current_company_id.get("") == ""
