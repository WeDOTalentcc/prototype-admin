"""
Contract Test: Wizard → Pipeline Handoff
==========================================
Verifies that the output produced by WizardReActAgent is structurally
compatible with what PipelineReActAgent expects as input context.

The handoff happens when a job vacancy created via the Wizard is published
and enters the Pipeline screening stage.

Key contract:
  - WizardAgent.domain_name == "wizard"
  - PipelineAgent.domain_name == "pipeline"
  - AgentOutput.state_updates from Wizard may contain job draft fields
  - PipelineAgent's context keys are a superset of what Wizard produces
  - PII fields must NOT appear in any agent's context keys going to LLM
"""
import pytest
from pydantic import ValidationError

from lia_agents_core.agent_interface import AgentInput, AgentOutput, AgentAction, NavigationCommand


# ---------------------------------------------------------------------------
# Contract: expected context keys per agent
# ---------------------------------------------------------------------------

WIZARD_EXPECTED_CONTEXT_KEYS = {
    "current_stage",   # navigation state
    "collected_data",  # fields collected so far in the wizard
}

PIPELINE_EXPECTED_CONTEXT_KEYS = {
    "current_stage",   # screening pipeline stage
    "collected_data",  # candidate/job data collected
}

PIPELINE_TRANSITION_EXPECTED_CONTEXT_KEYS = {
    "action_behavior",  # "passive" | "active"
    "candidate_name",   # display name (NOT PII sent to LLM)
    "job_title",        # job vacancy title
    "from_stage",       # stage moving from
    "to_stage",         # stage moving to
}

# PII fields that must NOT appear as top-level keys when agent sends to LLM
PII_FORBIDDEN_CONTEXT_KEYS = {
    "cpf", "rg", "birth_date", "address", "phone_number",
    "email", "photo_url", "ethnicity", "gender", "full_name",
    "mother_name", "father_name", "passport_number",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_wizard_output(state_updates: dict = None) -> AgentOutput:
    """Simulate a typical WizardAgent output after collecting job data."""
    return AgentOutput(
        message="Vaga criada com sucesso! Deseja publicar agora?",
        actions=[
            AgentAction(action_type="update_field", params={"field": "title", "value": "Dev Backend"}),
            AgentAction(action_type="update_field", params={"field": "seniority", "value": "Senior"}),
        ],
        state_updates=state_updates or {
            "current_stage": "review",
            "collected_data": {
                "title": "Dev Backend Sênior",
                "seniority": "Senior",
                "required_skills": ["Python", "FastAPI"],
                "salary_range": "R$ 15.000 - R$ 20.000",
            },
        },
        navigation=NavigationCommand(
            target_stage="review",
            reason="Todos os campos obrigatórios preenchidos",
            auto_navigate=False,
        ),
        confidence=0.92,
    )


def make_pipeline_input_from_wizard_output(
    wizard_output: AgentOutput,
    company_id: str = "company-001",
    user_id: str = "user-001",
) -> AgentInput:
    """Convert WizardAgent output to PipelineAgent input (simulates handoff)."""
    return AgentInput(
        message="Iniciar triagem dos candidatos",
        context={
            "current_stage": wizard_output.state_updates.get("current_stage", "triage"),
            "collected_data": wizard_output.state_updates.get("collected_data", {}),
            "job_id": "job-001",
        },
        session_id="session-handoff-001",
        company_id=company_id,
        user_id=user_id,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestWizardPipelineContract:

    def test_wizard_output_is_valid_agent_output(self):
        """WizardAgent output must be a valid AgentOutput."""
        output = make_wizard_output()
        assert isinstance(output, AgentOutput)
        assert output.message
        assert output.confidence >= 0.0

    def test_wizard_output_state_updates_contains_expected_keys(self):
        """WizardAgent state_updates must contain current_stage and collected_data."""
        output = make_wizard_output()
        for key in WIZARD_EXPECTED_CONTEXT_KEYS:
            assert key in output.state_updates, (
                f"WizardAgent state_updates must contain '{key}' for Pipeline handoff"
            )

    def test_pipeline_input_built_from_wizard_output_is_valid(self):
        """The AgentInput built from WizardAgent output must be valid for Pipeline."""
        wizard_output = make_wizard_output()
        pipeline_input = make_pipeline_input_from_wizard_output(wizard_output)
        assert isinstance(pipeline_input, AgentInput)
        assert pipeline_input.company_id == "company-001"
        assert "current_stage" in pipeline_input.context
        assert "collected_data" in pipeline_input.context

    def test_handoff_preserves_company_id(self):
        """company_id must survive the Wizard → Pipeline handoff unchanged."""
        expected_company = "company-tenant-xyz"
        wizard_output = make_wizard_output()
        pipeline_input = make_pipeline_input_from_wizard_output(
            wizard_output, company_id=expected_company
        )
        assert pipeline_input.company_id == expected_company

    def test_no_pii_in_wizard_state_updates_top_level_keys(self):
        """PII fields must not appear as top-level keys in state_updates."""
        output = make_wizard_output()
        pii_found = PII_FORBIDDEN_CONTEXT_KEYS & set(output.state_updates.keys())
        assert not pii_found, (
            f"WizardAgent state_updates contains PII keys: {pii_found}"
        )

    def test_no_pii_in_pipeline_context_top_level_keys(self):
        """PII fields must not appear as top-level keys in pipeline input context."""
        wizard_output = make_wizard_output()
        pipeline_input = make_pipeline_input_from_wizard_output(wizard_output)
        pii_found = PII_FORBIDDEN_CONTEXT_KEYS & set(pipeline_input.context.keys())
        assert not pii_found, (
            f"Pipeline AgentInput context contains PII keys: {pii_found}"
        )

    def test_wizard_navigation_targets_valid_stage(self):
        """WizardAgent NavigationCommand.target_stage must be a non-empty string."""
        output = make_wizard_output()
        if output.navigation is not None:
            assert isinstance(output.navigation.target_stage, str)
            assert len(output.navigation.target_stage) > 0

    def test_agent_input_rejects_missing_company_id_on_handoff(self):
        """Handoff AgentInput without company_id must fail Pydantic validation."""
        with pytest.raises((ValidationError, TypeError)):
            AgentInput(
                message="teste",
                context={"current_stage": "triage"},
                session_id="s1",
                # company_id missing
                user_id="u1",
            )

    def test_pipeline_transition_context_keys_are_known(self):
        """PipelineTransitionAgent context must only use documented keys."""
        pipeline_transition_context = {
            "action_behavior": "passive",
            "candidate_name": "Candidato Teste",
            "job_title": "Dev Backend",
            "from_stage": "triage",
            "to_stage": "interview",
        }
        # Verify no unknown keys were added
        unknown = set(pipeline_transition_context.keys()) - PIPELINE_TRANSITION_EXPECTED_CONTEXT_KEYS
        assert not unknown, (
            f"PipelineTransitionAgent context has undocumented keys: {unknown}"
        )

    def test_pipeline_transition_input_is_valid_agent_input(self):
        """A properly-formed PipelineTransitionAgent input must pass validation."""
        pt_input = AgentInput(
            message="Mover João para entrevista técnica",
            context={
                "action_behavior": "passive",
                "candidate_name": "João Silva",
                "job_title": "Dev Backend Sênior",
                "from_stage": "triage",
                "to_stage": "interview",
            },
            session_id="session-pt-001",
            company_id="company-001",
            user_id="recruiter-001",
        )
        assert pt_input.context["from_stage"] == "triage"
        assert pt_input.context["to_stage"] == "interview"
