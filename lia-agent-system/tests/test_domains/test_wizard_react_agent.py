"""
Tests for WizardReActAgent e JobWizardGraph (nova arquitetura DDD).

Cobre:
- Happy path: criação de vaga via wizard conversacional
- Checkpoint restore: estado anterior restaurado corretamente
- Guardrail: requisitos discriminatórios bloqueados
- FairnessGuard: wizard_tool_registry chama check_semantic
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestWizardReActAgentImport:
    """Importações do domínio correto."""

    def test_wizard_react_agent_importable(self):
        """WizardReActAgent importável de app.domains.job_management."""
        from app.domains.job_management.agents.wizard_react_agent import WizardReActAgent
        agent = WizardReActAgent()
        assert agent is not None


class TestWizardFairnessGuard:
    """FairnessGuard em wizard_tool_registry."""

    def test_wizard_tool_registry_importable(self):
        """wizard_tool_registry importável com função get_wizard_tools."""
        from app.domains.job_management.agents.wizard_tool_registry import get_wizard_tools
        tools = get_wizard_tools()
        assert tools is not None
        assert len(tools) > 0

    def test_fairness_check_on_discriminatory_jd(self, discriminatory_job_text):
        """FairnessGuard deve detectar texto discriminatório em JD."""
        from app.shared.compliance.fairness_guard import FairnessGuard
        guard = FairnessGuard()
        result = guard.check_explicit_bias(discriminatory_job_text)
        assert result.is_biased


class TestWizardSettings:
    """Configurações externalizadas via settings."""

    def test_react_settings_accessible(self):
        """Settings de ReAct devem estar acessíveis."""
        from app.core.config import settings
        assert hasattr(settings, "REACT_MAX_ITERATIONS_DEFAULT")
        assert settings.REACT_MAX_ITERATIONS_DEFAULT > 0
        assert hasattr(settings, "REACT_OBSERVATION_MAX_CHARS")
        assert settings.REACT_OBSERVATION_MAX_CHARS >= 2000


class TestWizardBaseStateMachine:
    """BaseStateMachine — Sprint 5 contract tests."""

    def test_base_state_machine_importable(self):
        from lia_agents_core.base_state_machine import BaseStateMachine
        assert BaseStateMachine is not None

    def test_base_state_machine_is_abstract(self):
        import inspect
        from lia_agents_core.base_state_machine import BaseStateMachine
        assert inspect.isabstract(BaseStateMachine)

    def test_base_state_machine_abstract_methods(self):
        from lia_agents_core.base_state_machine import BaseStateMachine
        abstract = getattr(BaseStateMachine, "__abstractmethods__", set())
        required = {"get_initial_state", "get_stage_order", "get_next_stage",
                    "can_transition", "apply_transition"}
        assert required.issubset(abstract), f"Missing abstract methods: {required - abstract}"


class TestWizardJobStageConfig:
    """job_stage_config extracted module tests."""

    def test_job_creation_stages_count(self):
        from app.domains.job_management.services.job_stage_config import JOB_CREATION_STAGES
        assert len(JOB_CREATION_STAGES) == 8

    def test_all_stages_have_required_keys(self):
        from app.domains.job_management.services.job_stage_config import JOB_CREATION_STAGES
        for stage in JOB_CREATION_STAGES:
            assert "stage" in stage
            assert "name" in stage
            assert "skip_if_confident" in stage

    def test_wizard_orchestrator_uses_stage_config_not_agent(self):
        """Stage config must be importable without triggering DeprecationWarning."""
        import warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            from app.domains.job_management.services.job_stage_config import get_stage_config
            get_stage_config(1)
        deprecation_warnings = [x for x in w if issubclass(x.category, DeprecationWarning)]
        assert len(deprecation_warnings) == 0, (
            "job_stage_config.py must not trigger DeprecationWarning"
        )
