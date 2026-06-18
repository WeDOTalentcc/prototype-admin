"""
TDD Red tests for P2-3: Wizard tool scope — wizard-only tools must NOT be accessible
to the orchestrator agent.
These tests FAIL until allowed_agents is properly configured per tool category.
"""
import pytest

WIZARD_ONLY_TOOLS = ["save_job_draft", "validate_job_fields", "get_job_suggestions"]
GLOBALLY_USEFUL = [
    "search_salary_benchmark",
    "get_intelligent_salary",
    "get_intelligent_skills",
    "get_company_config",
]


def test_wizard_only_tools_not_accessible_to_orchestrator():
    """Wizard-only tools must NOT have 'orchestrator' in allowed_agents."""
    from app.tools import initialize_tools
    from app.tools.registry import tool_registry
    initialize_tools()
    for name in WIZARD_ONLY_TOOLS:
        td = tool_registry.get_tool(name)
        if td is None:
            continue  # not yet registered — skip
        allowed = getattr(td, "allowed_agents", None) or []
        assert "orchestrator" not in allowed, (
            f"[P2-3] {name} has 'orchestrator' in allowed_agents — "
            "wizard-only tools must be restricted to wizard agents only. "
            "Remove 'orchestrator' from allowed_agents in register_job_wizard_tools()."
        )


def test_globally_useful_wizard_tools_keep_orchestrator():
    """Read/intelligence wizard tools SHOULD remain accessible to orchestrator."""
    from app.tools import initialize_tools
    from app.tools.registry import tool_registry
    initialize_tools()
    for name in GLOBALLY_USEFUL:
        td = tool_registry.get_tool(name)
        if td is None:
            continue
        allowed = getattr(td, "allowed_agents", None) or []
        assert "orchestrator" in allowed, (
            f"[P2-3] {name} should have 'orchestrator' in allowed_agents "
            "(useful for global chat). Do not restrict this tool."
        )
