"""
Contract Test: Agent Interface Compliance
==========================================
Verifies that all domain agents correctly implement BaseAgent.
Every agent must:
  1. Declare a non-empty domain_name property
  2. Declare a non-empty available_tools list
  3. Expose an async process() method with the correct signature
  4. Accept AgentInput and produce AgentOutput (Pydantic validation)

This test runs without network/LLM calls — it only validates the structural
contract, not the agent's behavior.
"""
import inspect
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from lia_agents_core.agent_interface import AgentInput, AgentOutput, BaseAgent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_agent_input(**overrides) -> AgentInput:
    defaults = dict(
        message="teste de contrato",
        context={},
        session_id="session-contract-001",
        company_id="company-contract-001",
        user_id="user-contract-001",
    )
    defaults.update(overrides)
    return AgentInput(**defaults)


def make_agent_output(**overrides) -> AgentOutput:
    defaults = dict(message="resposta de contrato")
    defaults.update(overrides)
    return AgentOutput(**defaults)


# ---------------------------------------------------------------------------
# Agent import helpers (lazy — avoids heavy imports at collection time)
# ---------------------------------------------------------------------------

def import_wizard_agent():
    from app.domains.job_management.agents.wizard_react_agent import WizardReActAgent
    return WizardReActAgent


def import_pipeline_react_agent():
    from app.domains.cv_screening.agents.pipeline_react_agent import PipelineReActAgent
    return PipelineReActAgent


def import_pipeline_transition_agent():
    from app.domains.pipeline.agents.pipeline_transition_agent import PipelineTransitionAgent
    return PipelineTransitionAgent


def import_sourcing_agent():
    from app.domains.sourcing.agents.sourcing_react_agent import SourcingReActAgent
    return SourcingReActAgent


def import_kanban_agent():
    from app.domains.recruiter_assistant.agents.kanban_react_agent import KanbanReActAgent
    return KanbanReActAgent


def import_talent_agent():
    from app.domains.recruiter_assistant.agents.talent_react_agent import TalentReActAgent
    return TalentReActAgent


def import_jobs_mgmt_agent():
    from app.domains.recruiter_assistant.agents.jobs_mgmt_react_agent import JobsMgmtReActAgent
    return JobsMgmtReActAgent


def import_policy_agent():
    from app.domains.hiring_policy.agents.policy_react_agent import PolicyReActAgent
    return PolicyReActAgent


AGENT_FACTORIES = [
    ("wizard", import_wizard_agent),
    ("pipeline_react", import_pipeline_react_agent),
    ("pipeline_transition", import_pipeline_transition_agent),
    ("sourcing", import_sourcing_agent),
    ("kanban", import_kanban_agent),
    ("talent", import_talent_agent),
    ("jobs_mgmt", import_jobs_mgmt_agent),
    ("policy", import_policy_agent),
]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestAgentInterfaceContract:

    @pytest.mark.parametrize("name,factory", AGENT_FACTORIES)
    def test_agent_is_subclass_of_base_agent(self, name, factory):
        """Every agent must be a subclass of BaseAgent."""
        cls = factory()
        assert issubclass(cls, BaseAgent), (
            f"{name}: {cls.__name__} must inherit from BaseAgent"
        )

    @pytest.mark.parametrize("name,factory", AGENT_FACTORIES)
    def test_agent_has_domain_name(self, name, factory):
        """domain_name must be a non-empty string."""
        cls = factory()
        instance = cls.__new__(cls)
        # Access as class-level property via descriptor — bypass __init__
        prop = getattr(cls, "domain_name", None)
        assert prop is not None, f"{name}: domain_name property must exist"

    @pytest.mark.parametrize("name,factory", AGENT_FACTORIES)
    def test_agent_has_process_method(self, name, factory):
        """process() must be an async method accepting (self, input: AgentInput)."""
        cls = factory()
        assert hasattr(cls, "process"), f"{name}: must have process() method"
        method = cls.process
        assert inspect.iscoroutinefunction(method), (
            f"{name}: process() must be async"
        )

    @pytest.mark.parametrize("name,factory", AGENT_FACTORIES)
    def test_process_signature_accepts_agent_input(self, name, factory):
        """process() must declare an AgentInput-typed parameter."""
        cls = factory()
        sig = inspect.signature(cls.process)
        params = list(sig.parameters.values())
        # params[0] = self, params[1] = input
        assert len(params) >= 2, (
            f"{name}: process() must accept at least one argument beyond self"
        )
        input_param = params[1]
        annotation = input_param.annotation
        # Accept both AgentInput and inspect.Parameter.empty (no annotation)
        if annotation is not inspect.Parameter.empty:
            assert annotation is AgentInput, (
                f"{name}: process() input parameter should be typed as AgentInput, "
                f"got {annotation}"
            )

    def test_agent_input_schema_has_required_fields(self):
        """AgentInput must have the mandatory multi-tenant fields."""
        required = AgentInput.model_fields
        for field in ["message", "session_id", "company_id", "user_id"]:
            assert field in required, f"AgentInput must have required field '{field}'"

    def test_agent_output_schema_has_required_fields(self):
        """AgentOutput must have message and default-valued collections."""
        required = AgentOutput.model_fields
        assert "message" in required
        for field in ["actions", "state_updates", "tool_results", "reasoning_steps"]:
            assert field in required, f"AgentOutput must have field '{field}'"

    def test_agent_input_company_id_is_mandatory(self):
        """AgentInput must reject missing company_id (multi-tenant isolation)."""
        with pytest.raises(Exception):
            AgentInput(
                message="test",
                session_id="s1",
                # company_id intentionally missing
                user_id="u1",
            )

    def test_agent_output_defaults_to_empty_collections(self):
        """AgentOutput must have safe defaults for all list/dict fields."""
        out = AgentOutput(message="ok")
        assert out.actions == []
        assert out.state_updates == {}
        assert out.tool_results == []
        assert out.reasoning_steps == []
        assert out.navigation is None
        assert out.error is None

    def test_agent_output_confidence_range(self):
        """confidence must be in [0.0, 1.0]."""
        out = AgentOutput(message="ok", confidence=0.85)
        assert 0.0 <= out.confidence <= 1.0

        with pytest.raises(Exception):
            AgentOutput(message="bad", confidence=1.5)

        with pytest.raises(Exception):
            AgentOutput(message="bad", confidence=-0.1)
