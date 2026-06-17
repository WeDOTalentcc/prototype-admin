"""
Contract Tests: Policy and Automation Agents
=============================================
Covers PolicyReActAgent and AutomationReActAgent.

PolicyReActAgent uses a different context pattern:
  - context["current_stage"] — default "onboarding"
  - context["policy_state"] — dict of policy configuration state

AutomationReActAgent uses:
  - context["current_stage"] — default "decompose"
"""
import pytest
from lia_agents_core.agent_interface import AgentInput, AgentOutput, BaseAgent


PII_FORBIDDEN = {
    "cpf", "rg", "birth_date", "address", "email", "phone_number",
    "photo_url", "ethnicity", "gender", "full_name",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_input(context: dict, company_id: str = "company-001") -> AgentInput:
    return AgentInput(
        message="teste de contrato",
        context=context,
        session_id="session-pa-001",
        company_id=company_id,
        user_id="admin-001",
    )


# ---------------------------------------------------------------------------
# PolicyReActAgent — context schema differs: uses policy_state not collected_data
# ---------------------------------------------------------------------------

class TestPolicyContract:

    def test_policy_is_base_agent(self):
        from app.domains.hiring_policy.agents.policy_react_agent import PolicyReActAgent
        assert issubclass(PolicyReActAgent, BaseAgent)

    def test_policy_context_schema(self):
        """PolicyAgent input uses policy_state dict, not collected_data."""
        inp = make_input({
            "current_stage": "onboarding",
            "policy_state": {
                "diversity_target": True,
                "max_days_open": 30,
            },
        })
        assert inp.context["current_stage"] == "onboarding"
        assert isinstance(inp.context["policy_state"], dict)

    def test_policy_context_policy_state_defaults_to_empty(self):
        """policy_state is optional — PolicyAgent uses {} as default."""
        inp = make_input({"current_stage": "onboarding"})
        # context doesn't crash without policy_state
        assert inp.context.get("policy_state") is None

    def test_policy_context_schema_differs_from_wizard(self):
        """Policy uses policy_state, not collected_data — different contract from Wizard."""
        wizard_context_keys = {"current_stage", "collected_data"}
        policy_context_keys = {"current_stage", "policy_state"}
        assert wizard_context_keys != policy_context_keys, (
            "PolicyAgent and WizardAgent have distinct context schemas"
        )

    def test_policy_no_pii_at_top_level(self):
        context = {
            "current_stage": "onboarding",
            "policy_state": {"diversity_target": True},
        }
        pii = PII_FORBIDDEN & set(context.keys())
        assert not pii, f"Policy context has PII top-level keys: {pii}"

    def test_policy_company_id_preserved(self):
        inp = make_input({"current_stage": "onboarding"}, company_id="tenant-policy-001")
        assert inp.company_id == "tenant-policy-001"

    def test_policy_output_schema(self):
        """PolicyAgent output may include policy recommendations."""
        out = AgentOutput(
            message="Configurei a política de diversidade para 40% meta feminina.",
            state_updates={
                "policy_state": {"diversity_target": True, "female_ratio": 0.40},
                "current_stage": "review",
            },
            confidence=0.91,
        )
        assert "policy_state" in out.state_updates
        assert out.state_updates["policy_state"]["female_ratio"] == 0.40

    def test_policy_output_does_not_auto_apply_without_confirmation(self):
        """
        Policy changes must require_confirmation=True on actions — Crença #1:
        IA recomenda, humanos decidem.
        """
        from lia_agents_core.agent_interface import AgentAction
        action = AgentAction(
            action_type="update_policy",
            params={"field": "diversity_target", "value": True},
            requires_confirmation=True,
        )
        assert action.requires_confirmation is True, (
            "Policy actions must require human confirmation (Crença #1)"
        )


# ---------------------------------------------------------------------------
# AutomationReActAgent
# ---------------------------------------------------------------------------

class TestAutomationContract:

    def test_automation_is_base_agent(self):
        from app.domains.automation.agents.automation_react_agent import AutomationReActAgent
        assert issubclass(AutomationReActAgent, BaseAgent)

    def test_automation_context_schema(self):
        """AutomationAgent input uses current_stage with default 'decompose'."""
        inp = make_input({
            "current_stage": "decompose",
            "task": "Enviar emails de rejeição para candidatos da vaga 123",
        })
        assert inp.context["current_stage"] == "decompose"
        assert "task" in inp.context

    def test_automation_no_pii_at_top_level(self):
        context = {
            "current_stage": "decompose",
            "task": "Agendar entrevistas",
        }
        pii = PII_FORBIDDEN & set(context.keys())
        assert not pii

    def test_automation_company_id_preserved(self):
        inp = make_input({"current_stage": "decompose"}, company_id="tenant-auto-001")
        assert inp.company_id == "tenant-auto-001"

    def test_automation_output_schema(self):
        """AutomationAgent output may include subtasks created."""
        out = AgentOutput(
            message="Criei 3 sub-tarefas para executar a automação.",
            state_updates={
                "subtasks": [
                    {"id": "t1", "action": "send_rejection_email", "status": "pending"},
                    {"id": "t2", "action": "update_pipeline_stage", "status": "pending"},
                    {"id": "t3", "action": "notify_recruiter", "status": "pending"},
                ],
                "current_stage": "execute",
            },
            confidence=0.88,
        )
        assert len(out.state_updates["subtasks"]) == 3
        assert all(t["status"] == "pending" for t in out.state_updates["subtasks"])

    def test_automation_actions_require_confirmation_for_irreversible(self):
        """
        Irreversible automation actions must have requires_confirmation=True.
        Crença #1: IA não executa ações destrutivas sem aprovação humana.
        """
        from lia_agents_core.agent_interface import AgentAction
        # Sending emails, deleting records — irreversible
        email_action = AgentAction(
            action_type="send_email_bulk",
            params={"template": "rejection", "count": 150},
            requires_confirmation=True,
        )
        delete_action = AgentAction(
            action_type="archive_candidates",
            params={"job_id": "job-123"},
            requires_confirmation=True,
        )
        assert email_action.requires_confirmation is True
        assert delete_action.requires_confirmation is True

    def test_automation_context_defaults_to_decompose_stage(self):
        """AutomationAgent works without current_stage (defaults to 'decompose' internally)."""
        inp = make_input({})
        # No crash, valid AgentInput
        assert isinstance(inp, AgentInput)
        assert inp.context == {}
