"""
Testes — Confidence Calibration nos 5 agentes (talent, kanban, jobs_mgmt, analytics, communication).

Verifica que:
1. ConfidencePolicyService é chamado em _state_to_output (caminho LangGraph nativo)
2. confidence_action é incluído no metadata do AgentOutput
3. Valores de confidence corretos geram ações corretas (APPLY_SILENT, APPLY_NOTIFY, ASK_USER)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.shared.services.confidence_policy_service import (
    ConfidenceAction,
    ConfidencePolicyService,
    ConfidenceThresholds,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_state(has_actions: bool = False, has_error: bool = False) -> dict:
    """Monta um MessagesState mínimo para _state_to_output."""
    msg = MagicMock()
    msg.content = "Resposta da LIA"
    msg.tool_call_id = None
    msg.tool_calls = [{"name": "search_candidates"}] if has_actions else []
    msg.type = "ai"
    return {
        "messages": [msg],
        "error": "erro simulado" if has_error else None,
    }


def _make_input(domain: str = "talent") -> MagicMock:
    inp = MagicMock()
    inp.context = {"current_stage": "discovery", "collected_data": {}}
    inp.session_id = "sess-test"
    inp.company_id = "company-test"
    inp.user_id = "user-test"
    inp.message = "lista os candidatos"
    return inp


# ---------------------------------------------------------------------------
# Testes de ConfidencePolicyService (unitários puros)
# ---------------------------------------------------------------------------

class TestConfidencePolicyServiceThresholds:
    """Verifica a lógica de thresholds do serviço."""

    def test_high_confidence_returns_apply_silent(self):
        svc = ConfidencePolicyService()
        action = svc.get_action_for_confidence(0.90)
        assert action == ConfidenceAction.APPLY_SILENT

    def test_medium_confidence_returns_apply_notify(self):
        svc = ConfidencePolicyService()
        action = svc.get_action_for_confidence(0.75)
        assert action == ConfidenceAction.APPLY_NOTIFY

    def test_low_confidence_returns_ask_user(self):
        svc = ConfidencePolicyService()
        action = svc.get_action_for_confidence(0.40)
        assert action == ConfidenceAction.ASK_USER

    def test_tool_called_confidence_is_apply_notify(self):
        """0.82 (tool chamada) deve ser APPLY_NOTIFY (>=0.70, <0.85)."""
        svc = ConfidencePolicyService()
        action = svc.get_action_for_confidence(0.82)
        assert action == ConfidenceAction.APPLY_NOTIFY

    def test_base_confidence_is_apply_notify(self):
        """0.75 (base) deve ser APPLY_NOTIFY."""
        svc = ConfidencePolicyService()
        action = svc.get_action_for_confidence(0.75)
        assert action == ConfidenceAction.APPLY_NOTIFY

    def test_error_confidence_is_ask_user(self):
        """0.40 (erro) deve ser ASK_USER."""
        svc = ConfidencePolicyService()
        action = svc.get_action_for_confidence(0.40)
        assert action == ConfidenceAction.ASK_USER


# ---------------------------------------------------------------------------
# Testes de integração: confidence_action no metadata dos agentes
# ---------------------------------------------------------------------------

class TestTalentAgentConfidenceCalibration:
    def test_state_to_output_includes_confidence_action_no_tools(self):
        from app.domains.recruiter_assistant.agents.talent_react_agent import TalentReActAgent
        agent = TalentReActAgent.__new__(TalentReActAgent)
        agent.domain_name = "talent"

        state = _make_state(has_actions=False, has_error=False)
        inp = _make_input("talent")

        output = agent._state_to_output(state, inp)

        assert "confidence_action" in output.metadata
        assert output.metadata["confidence_action"] == ConfidenceAction.APPLY_NOTIFY.value
        assert output.confidence == 0.75

    def test_state_to_output_tool_called_confidence(self):
        from app.domains.recruiter_assistant.agents.talent_react_agent import TalentReActAgent
        agent = TalentReActAgent.__new__(TalentReActAgent)
        agent.domain_name = "talent"

        state = _make_state(has_actions=True, has_error=False)
        inp = _make_input("talent")

        output = agent._state_to_output(state, inp)

        assert output.confidence == 0.82
        assert output.metadata["confidence_action"] == ConfidenceAction.APPLY_NOTIFY.value

    def test_state_to_output_error_confidence(self):
        from app.domains.recruiter_assistant.agents.talent_react_agent import TalentReActAgent
        agent = TalentReActAgent.__new__(TalentReActAgent)
        agent.domain_name = "talent"

        state = _make_state(has_actions=False, has_error=True)
        inp = _make_input("talent")

        output = agent._state_to_output(state, inp)

        assert output.confidence == 0.40
        assert output.metadata["confidence_action"] == ConfidenceAction.ASK_USER.value


class TestKanbanAgentConfidenceCalibration:
    def test_confidence_action_in_metadata(self):
        from app.domains.recruiter_assistant.agents.kanban_react_agent import KanbanReActAgent
        agent = KanbanReActAgent.__new__(KanbanReActAgent)
        agent.domain_name = "kanban"

        state = _make_state(has_actions=True)
        inp = _make_input("kanban")
        inp.context = {"current_stage": "overview", "collected_data": {}}

        output = agent._state_to_output(state, inp)

        assert "confidence_action" in output.metadata
        assert output.metadata["confidence_action"] in [a.value for a in ConfidenceAction]


class TestJobsMgmtAgentConfidenceCalibration:
    def test_confidence_action_in_metadata(self):
        from app.domains.recruiter_assistant.agents.jobs_mgmt_react_agent import JobsMgmtReActAgent
        agent = JobsMgmtReActAgent.__new__(JobsMgmtReActAgent)
        agent.domain_name = "jobs_mgmt"

        state = _make_state(has_actions=False)
        inp = _make_input("jobs_mgmt")
        inp.context = {"current_stage": "overview", "collected_data": {}}

        output = agent._state_to_output(state, inp)

        assert "confidence_action" in output.metadata


class TestAnalyticsAgentConfidenceCalibration:
    def test_confidence_action_in_metadata(self):
        from app.domains.analytics.agents.analytics_react_agent import AnalyticsReActAgent
        agent = AnalyticsReActAgent.__new__(AnalyticsReActAgent)
        agent.domain_name = "analytics"

        state = _make_state(has_actions=True)
        inp = _make_input("analytics")
        inp.context = {"current_stage": "analysis", "collected_data": {}}

        output = agent._state_to_output(state, inp)

        assert "confidence_action" in output.metadata
        assert output.confidence == 0.82


class TestCommunicationAgentConfidenceCalibration:
    def test_confidence_action_in_metadata(self):
        from app.domains.communication.agents.communication_react_agent import CommunicationReActAgent
        agent = CommunicationReActAgent.__new__(CommunicationReActAgent)
        agent.domain_name = "communication"

        state = _make_state(has_actions=False)
        inp = _make_input("communication")
        inp.context = {"current_stage": "outreach", "collected_data": {}}

        output = agent._state_to_output(state, inp)

        assert "confidence_action" in output.metadata
        assert output.metadata["confidence_action"] == ConfidenceAction.APPLY_NOTIFY.value


class TestATSIntegrationAgentConfidenceCalibration:
    def test_confidence_action_in_metadata(self):
        from app.domains.ats_integration.agents.ats_integration_react_agent import ATSIntegrationReActAgent
        agent = ATSIntegrationReActAgent.__new__(ATSIntegrationReActAgent)
        agent.domain_name = "ats_integration"

        state = _make_state(has_actions=True)
        inp = _make_input("ats_integration")
        inp.context = {"current_stage": "sync", "collected_data": {}}

        output = agent._state_to_output(state, inp)

        assert "confidence_action" in output.metadata
        assert output.confidence == 0.82


class TestAutomationAgentConfidenceCalibration:
    def test_confidence_action_in_metadata(self):
        from app.domains.automation.agents.automation_react_agent import AutomationReActAgent
        agent = AutomationReActAgent.__new__(AutomationReActAgent)
        agent.domain_name = "automation"

        state = _make_state(has_actions=False)
        inp = _make_input("automation")
        inp.context = {"current_stage": "planning", "collected_data": {}}

        output = agent._state_to_output(state, inp)

        assert "confidence_action" in output.metadata
        assert output.metadata["confidence_action"] == ConfidenceAction.APPLY_NOTIFY.value


class TestPolicyAgentLangGraphConfidenceCalibration:
    def test_state_to_output_includes_confidence_action(self):
        from app.domains.hiring_policy.agents.policy_react_agent import PolicyReActAgent
        agent = PolicyReActAgent.__new__(PolicyReActAgent)
        agent.domain_name = "policy"

        state = _make_state(has_actions=False)
        inp = _make_input("policy")
        inp.context = {"current_stage": "onboarding", "policy_state": {}}

        output = agent._state_to_output(state, inp)

        assert "confidence_action" in output.metadata
        assert output.metadata["confidence_action"] in [a.value for a in ConfidenceAction]
