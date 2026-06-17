"""
Harness sensor: validates that domain agents inject page context into system prompts.
P1-4 regression prevention.
"""
import pytest

AGENTS_REQUIRING_CONTEXT = [
    ("app.domains.recruiter_assistant.agents.talent_funnel_react_agent",
     "talent_funnel_react_agent.py"),
    ("app.domains.recruiter_assistant.agents.kanban_react_agent",
     "kanban_react_agent.py"),
    ("app.domains.recruiter_assistant.agents.jobs_mgmt_react_agent",
     "jobs_mgmt_react_agent.py"),
    ("app.domains.sourcing.agents.sourcing_react_agent",
     "sourcing_react_agent.py"),
]

@pytest.mark.parametrize("module_path,label", AGENTS_REQUIRING_CONTEXT)
def test_agent_module_references_view_context(module_path, label):
    """Agent source must reference view_context_from_context (context injection)."""
    import importlib.util
    spec = importlib.util.find_spec(module_path)
    if spec is None:
        pytest.skip(f"Module {module_path} not found")
    with open(spec.origin) as f:
        source = f.read()
    assert "view_context_from_context" in source, (
        f"GHOST: {label} does NOT call view_context_from_context. "
        f"Page context (which vaga/candidato is open) is never injected into agent prompt. "
        f"Fix: add view_context_from_context(ctx) in _get_runtime_domain_instructions(). "
        f"See recruiter_copilot_react_agent.py for the canonical pattern."
    )
