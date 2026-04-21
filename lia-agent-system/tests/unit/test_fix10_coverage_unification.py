"""
FIX 10 — wizard YAML coverage + requires_confirmation unification.

G4: 5 wizard tools missing from YAML must have entries.
G6: DomainAction.requires_confirmation must be queryable via a unified resolver.
"""
import pytest


class TestFix10WizardYamlCoverage:
    def test_all_wizard_tools_have_yaml_entries(self):
        """G4: Every wizard TOOL_DEFINITION must have a YAML entry."""
        from app.domains.job_management.agents.wizard_tool_registry import TOOL_DEFINITIONS
        from app.tools.tool_registry_loader import load_tool_metadata
        metadata = load_tool_metadata()
        missing = [t.name for t in TOOL_DEFINITIONS if t.name not in metadata]
        assert not missing, f"Wizard tools missing YAML entries: {missing}"

    def test_wizard_only_tools_have_when_to_use(self):
        """G4: The 5 new wizard-only entries must have when_to_use."""
        from app.tools.tool_registry_loader import load_tool_metadata
        metadata = load_tool_metadata()
        wizard_only = [
            "extract_job_requirements",
            "create_job_draft",
            "validate_job_requirements",
            "get_salary_benchmarks",
            "check_job_draft_health",
        ]
        for tool_name in wizard_only:
            assert tool_name in metadata, f"{tool_name} not in YAML"
            meta = metadata[tool_name]
            assert meta.get("when_to_use"), f"{tool_name} missing when_to_use"
            assert meta.get("when_not_to_use"), f"{tool_name} missing when_not_to_use"


class TestFix10RequiresConfirmationUnified:
    def test_resolver_exists(self):
        """G6: A helper must exist that resolves requires_confirmation from both sources."""
        from app.orchestrator.action_executor.intents_config import resolve_requires_confirmation
        assert callable(resolve_requires_confirmation)

    def test_resolver_returns_intent_value_when_intent_known(self):
        """G6: Intent-level value takes precedence (it has more context)."""
        from app.orchestrator.action_executor.intents_config import resolve_requires_confirmation
        # mover_candidato intent → requires_confirmation: True in intents_config
        assert resolve_requires_confirmation("mover_candidato", "move_candidate") is True

    def test_resolver_falls_back_to_domain_action(self):
        """G6: When intent unknown, fall back to DomainAction.requires_confirmation."""
        from app.orchestrator.action_executor.intents_config import resolve_requires_confirmation
        # send_email has DomainAction.requires_confirmation=True in communication/actions.py
        # If intent is unknown, should fall back to DomainAction.
        result = resolve_requires_confirmation(intent=None, action_id="send_email")
        assert result is True, f"send_email DomainAction.requires_confirmation=True, got {result}"

    def test_resolver_returns_false_for_safe_action(self):
        """G6: Actions with requires_confirmation=False stay safe."""
        from app.orchestrator.action_executor.intents_config import resolve_requires_confirmation
        # list_jobs has requires_confirmation=False (default) in DomainAction
        result = resolve_requires_confirmation(intent=None, action_id="list_jobs")
        assert result is False
