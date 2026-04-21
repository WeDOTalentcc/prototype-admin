"""
FIX 5 — Wizard tools should be enriched with YAML descriptions.

Tests that sync_descriptions_from_yaml() also covers the wizard registry
(separate ToolDefinition class from lia_agents_core).
"""
import pytest


class TestWizardToolsSync:
    def test_wizard_tools_importable(self):
        from app.domains.job_management.agents.wizard_tool_registry import TOOL_DEFINITIONS
        assert len(TOOL_DEFINITIONS) > 0

    def test_sync_also_enriches_wizard_tools(self):
        """At least 1 wizard tool should have USE WHEN: after initialize_tools()."""
        from app.tools import initialize_tools
        from app.domains.job_management.agents.wizard_tool_registry import TOOL_DEFINITIONS

        initialize_tools()

        enriched = [
            t for t in TOOL_DEFINITIONS
            if "USE WHEN" in (t.description or "")
        ]
        assert len(enriched) >= 3, (
            f"Esperado ao menos 3 wizard tools com USE WHEN: após sync, encontrado {len(enriched)}. "
            f"Nomes: {[t.name for t in TOOL_DEFINITIONS]}"
        )

    def test_wizard_tool_save_job_draft_enriched(self):
        """save_job_draft is in YAML — must be enriched after sync."""
        from app.tools import initialize_tools
        from app.domains.job_management.agents.wizard_tool_registry import TOOL_DEFINITIONS

        initialize_tools()

        save_draft = next(
            (t for t in TOOL_DEFINITIONS if t.name == "save_job_draft"), None
        )
        if save_draft is None:
            pytest.skip("save_job_draft not in wizard TOOL_DEFINITIONS")
        assert "USE WHEN" in save_draft.description or "DO NOT USE WHEN" in save_draft.description, (
            f"save_job_draft description not enriched: {save_draft.description[:200]}"
        )
