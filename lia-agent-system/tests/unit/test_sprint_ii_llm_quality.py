"""
Sprint II — LLM Quality Tests.

Tests cover:
1. TestInteractionPatterns — word sets and prompt blocks
2. TestAntiSycophancyInPrompts — all 7 system prompts have anti-sycophancy
3. TestChainOfThoughtInPrompts — 6 prompts have <thought> marker
4. TestFewShotExamples — 9 system prompts have ## Exemplos section with 4+ scenarios
5. TestNegationDetectionInPrompts — 8 prompts have negation detection block
6. TestConfidenceInAgents — confidence is not None / not hardcoded 0.85 generically
"""
import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# I. TestInteractionPatterns
# ---------------------------------------------------------------------------

class TestInteractionPatterns:
    """Verifica que interaction_patterns.py contém os conjuntos e blocos esperados."""

    def test_negation_words_exist_and_nonempty(self):
        from app.shared.prompts.interaction_patterns import NEGATION_WORDS
        assert isinstance(NEGATION_WORDS, (set, frozenset))
        assert len(NEGATION_WORDS) >= 5
        assert "não" in NEGATION_WORDS or "nao" in NEGATION_WORDS

    def test_confirmation_words_exist_and_nonempty(self):
        from app.shared.prompts.interaction_patterns import CONFIRMATION_WORDS
        assert isinstance(CONFIRMATION_WORDS, (set, frozenset))
        assert len(CONFIRMATION_WORDS) >= 5
        assert "sim" in CONFIRMATION_WORDS

    def test_negation_detection_block_exists_and_has_content(self):
        from app.shared.prompts.interaction_patterns import NEGATION_DETECTION_BLOCK
        assert isinstance(NEGATION_DETECTION_BLOCK, str)
        assert len(NEGATION_DETECTION_BLOCK) > 50
        assert "negação" in NEGATION_DETECTION_BLOCK.lower() or "negacao" in NEGATION_DETECTION_BLOCK.lower() or "Negação" in NEGATION_DETECTION_BLOCK

    def test_chain_of_thought_block_exists_and_has_thought_tag(self):
        from app.shared.prompts.interaction_patterns import CHAIN_OF_THOUGHT_BLOCK
        assert isinstance(CHAIN_OF_THOUGHT_BLOCK, str)
        assert len(CHAIN_OF_THOUGHT_BLOCK) > 50
        assert "<thought>" in CHAIN_OF_THOUGHT_BLOCK

    def test_anti_sycophancy_block_exists_and_has_rule(self):
        from app.shared.prompts.interaction_patterns import ANTI_SYCOPHANCY_BLOCK
        assert isinstance(ANTI_SYCOPHANCY_BLOCK, str)
        assert len(ANTI_SYCOPHANCY_BLOCK) > 50
        assert "sycophancy" in ANTI_SYCOPHANCY_BLOCK.lower() or "NUNCA" in ANTI_SYCOPHANCY_BLOCK

    def test_negation_words_contains_key_terms(self):
        from app.shared.prompts.interaction_patterns import NEGATION_WORDS
        key_terms = {"cancelar", "espera", "volta"}
        assert len(key_terms & NEGATION_WORDS) >= 2

    def test_confirmation_words_contains_key_terms(self):
        from app.shared.prompts.interaction_patterns import CONFIRMATION_WORDS
        key_terms = {"sim", "ok", "confirmo"}
        assert len(key_terms & CONFIRMATION_WORDS) >= 2


# ---------------------------------------------------------------------------
# II. TestAntiSycophancyInPrompts
# ---------------------------------------------------------------------------

class TestAntiSycophancyInPrompts:
    """Verifica que os 7 system prompts contêm bloco anti-sycophancy."""

    def _get_prompt(self, module_path: str, func_name: str, **kwargs) -> str:
        """Helper para importar e executar função de prompt."""
        import importlib
        mod = importlib.import_module(module_path)
        func = getattr(mod, func_name)
        return func(**kwargs)

    def test_talent_has_anti_sycophancy(self):
        prompt = self._get_prompt(
            "app.domains.recruiter_assistant.agents.talent_system_prompt",
            "get_talent_system_prompt",
            stage="discovery",
            context={},
        )
        assert "sycophancy" in prompt.lower() or "NUNCA concorde" in prompt or "Anti-Sycophancy" in prompt

    def test_kanban_has_anti_sycophancy(self):
        prompt = self._get_prompt(
            "app.domains.recruiter_assistant.agents.kanban_system_prompt",
            "get_kanban_system_prompt",
            stage="pipeline_overview",
            context={},
        )
        assert "sycophancy" in prompt.lower() or "NUNCA concorde" in prompt or "Anti-Sycophancy" in prompt

    def test_jobs_mgmt_has_anti_sycophancy(self):
        prompt = self._get_prompt(
            "app.domains.recruiter_assistant.agents.jobs_mgmt_system_prompt",
            "get_jobs_mgmt_system_prompt",
            stage="overview",
            context={},
        )
        assert "sycophancy" in prompt.lower() or "NUNCA concorde" in prompt or "Anti-Sycophancy" in prompt

    def test_automation_has_anti_sycophancy(self):
        prompt = self._get_prompt(
            "app.domains.automation.agents.automation_system_prompt",
            "get_automation_system_prompt",
        )
        assert "sycophancy" in prompt.lower() or "NUNCA concorde" in prompt or "Anti-Sycophancy" in prompt

    def test_ats_integration_has_anti_sycophancy(self):
        prompt = self._get_prompt(
            "app.domains.ats_integration.agents.ats_integration_system_prompt",
            "get_ats_integration_system_prompt",
        )
        assert "sycophancy" in prompt.lower() or "NUNCA concorde" in prompt or "Anti-Sycophancy" in prompt

    def test_policy_has_anti_sycophancy(self):
        prompt = self._get_prompt(
            "app.domains.hiring_policy.agents.policy_system_prompt",
            "get_policy_system_prompt",
        )
        assert "sycophancy" in prompt.lower() or "NUNCA concorde" in prompt or "Anti-Sycophancy" in prompt

    def test_analytics_has_anti_sycophancy(self):
        prompt = self._get_prompt(
            "app.domains.analytics.agents.analytics_system_prompt",
            "get_analytics_system_prompt",
        )
        assert "sycophancy" in prompt.lower() or "NUNCA concorde" in prompt or "Anti-Sycophancy" in prompt


# ---------------------------------------------------------------------------
# III. TestChainOfThoughtInPrompts
# ---------------------------------------------------------------------------

class TestChainOfThoughtInPrompts:
    """Verifica que 6 prompts contêm o marcador <thought> de chain-of-thought."""

    def _get_prompt(self, module_path: str, func_name: str, **kwargs) -> str:
        import importlib
        mod = importlib.import_module(module_path)
        func = getattr(mod, func_name)
        return func(**kwargs)

    def test_analytics_has_thought_tag(self):
        prompt = self._get_prompt(
            "app.domains.analytics.agents.analytics_system_prompt",
            "get_analytics_system_prompt",
        )
        assert "<thought>" in prompt

    def test_communication_has_thought_tag(self):
        prompt = self._get_prompt(
            "app.domains.communication.agents.communication_system_prompt",
            "get_communication_system_prompt",
        )
        assert "<thought>" in prompt

    def test_automation_has_thought_tag(self):
        prompt = self._get_prompt(
            "app.domains.automation.agents.automation_system_prompt",
            "get_automation_system_prompt",
        )
        assert "<thought>" in prompt

    def test_ats_integration_has_thought_tag(self):
        prompt = self._get_prompt(
            "app.domains.ats_integration.agents.ats_integration_system_prompt",
            "get_ats_integration_system_prompt",
        )
        assert "<thought>" in prompt

    def test_talent_has_thought_tag(self):
        prompt = self._get_prompt(
            "app.domains.recruiter_assistant.agents.talent_system_prompt",
            "get_talent_system_prompt",
            stage="discovery",
            context={},
        )
        assert "<thought>" in prompt

    def test_kanban_has_thought_tag(self):
        prompt = self._get_prompt(
            "app.domains.recruiter_assistant.agents.kanban_system_prompt",
            "get_kanban_system_prompt",
            stage="pipeline_overview",
            context={},
        )
        assert "<thought>" in prompt


# ---------------------------------------------------------------------------
# IV. TestFewShotExamples
# ---------------------------------------------------------------------------

class TestFewShotExamples:
    """Verifica que 9 system prompts têm seção ## Exemplos com pelo menos 4 cenários."""

    def _get_prompt(self, module_path: str, func_name: str, **kwargs) -> str:
        import importlib
        mod = importlib.import_module(module_path)
        func = getattr(mod, func_name)
        return func(**kwargs)

    def _count_scenarios(self, prompt: str) -> int:
        """Conta quantos cenários existem no prompt."""
        return prompt.count("**Cenário ")

    def _check_exemplos_section(self, prompt: str) -> bool:
        return "## Exemplos" in prompt

    def test_talent_has_exemplos_section(self):
        prompt = self._get_prompt(
            "app.domains.recruiter_assistant.agents.talent_system_prompt",
            "get_talent_system_prompt",
            stage="discovery",
            context={},
        )
        assert self._check_exemplos_section(prompt)
        assert self._count_scenarios(prompt) >= 4

    def test_kanban_has_exemplos_section(self):
        prompt = self._get_prompt(
            "app.domains.recruiter_assistant.agents.kanban_system_prompt",
            "get_kanban_system_prompt",
            stage="pipeline_overview",
            context={},
        )
        assert self._check_exemplos_section(prompt)
        assert self._count_scenarios(prompt) >= 4

    def test_jobs_mgmt_has_exemplos_section(self):
        prompt = self._get_prompt(
            "app.domains.recruiter_assistant.agents.jobs_mgmt_system_prompt",
            "get_jobs_mgmt_system_prompt",
            stage="overview",
            context={},
        )
        assert self._check_exemplos_section(prompt)
        assert self._count_scenarios(prompt) >= 4

    def test_analytics_has_exemplos_section(self):
        prompt = self._get_prompt(
            "app.domains.analytics.agents.analytics_system_prompt",
            "get_analytics_system_prompt",
        )
        assert self._check_exemplos_section(prompt)
        assert self._count_scenarios(prompt) >= 4

    def test_communication_has_exemplos_section(self):
        prompt = self._get_prompt(
            "app.domains.communication.agents.communication_system_prompt",
            "get_communication_system_prompt",
        )
        assert self._check_exemplos_section(prompt)
        assert self._count_scenarios(prompt) >= 4

    def test_automation_has_exemplos_section(self):
        prompt = self._get_prompt(
            "app.domains.automation.agents.automation_system_prompt",
            "get_automation_system_prompt",
        )
        assert self._check_exemplos_section(prompt)
        assert self._count_scenarios(prompt) >= 4

    def test_ats_integration_has_exemplos_section(self):
        prompt = self._get_prompt(
            "app.domains.ats_integration.agents.ats_integration_system_prompt",
            "get_ats_integration_system_prompt",
        )
        assert self._check_exemplos_section(prompt)
        assert self._count_scenarios(prompt) >= 4

    def test_policy_has_exemplos_section(self):
        prompt = self._get_prompt(
            "app.domains.hiring_policy.agents.policy_system_prompt",
            "get_policy_system_prompt",
        )
        assert self._check_exemplos_section(prompt)
        assert self._count_scenarios(prompt) >= 4

    def test_sourcing_has_exemplos_section(self):
        from app.domains.sourcing.agents.sourcing_system_prompt import get_sourcing_system_prompt
        prompt = get_sourcing_system_prompt(stage="search-criteria", context={})
        assert self._check_exemplos_section(prompt)
        assert self._count_scenarios(prompt) >= 4


# ---------------------------------------------------------------------------
# V. TestNegationDetectionInPrompts
# ---------------------------------------------------------------------------

class TestNegationDetectionInPrompts:
    """Verifica que 8 prompts contêm o bloco de detecção de negação."""

    def _get_prompt(self, module_path: str, func_name: str, **kwargs) -> str:
        import importlib
        mod = importlib.import_module(module_path)
        func = getattr(mod, func_name)
        return func(**kwargs)

    def _has_negation_block(self, prompt: str) -> bool:
        return (
            "Detecção de Negação" in prompt
            or "Deteccao de Negacao" in prompt
            or "negação explícita" in prompt.lower()
            or "negacao explicita" in prompt.lower()
            or "CANCELE a ação" in prompt
        )

    def test_sourcing_has_negation_detection(self):
        from app.domains.sourcing.agents.sourcing_system_prompt import get_sourcing_system_prompt
        prompt = get_sourcing_system_prompt(stage="search-criteria", context={})
        assert self._has_negation_block(prompt)

    def test_talent_has_negation_detection(self):
        prompt = self._get_prompt(
            "app.domains.recruiter_assistant.agents.talent_system_prompt",
            "get_talent_system_prompt",
            stage="discovery",
            context={},
        )
        assert self._has_negation_block(prompt)

    def test_kanban_has_negation_detection(self):
        prompt = self._get_prompt(
            "app.domains.recruiter_assistant.agents.kanban_system_prompt",
            "get_kanban_system_prompt",
            stage="pipeline_overview",
            context={},
        )
        assert self._has_negation_block(prompt)

    def test_jobs_mgmt_has_negation_detection(self):
        prompt = self._get_prompt(
            "app.domains.recruiter_assistant.agents.jobs_mgmt_system_prompt",
            "get_jobs_mgmt_system_prompt",
            stage="overview",
            context={},
        )
        assert self._has_negation_block(prompt)

    def test_analytics_has_negation_detection(self):
        prompt = self._get_prompt(
            "app.domains.analytics.agents.analytics_system_prompt",
            "get_analytics_system_prompt",
        )
        assert self._has_negation_block(prompt)

    def test_communication_has_negation_detection(self):
        prompt = self._get_prompt(
            "app.domains.communication.agents.communication_system_prompt",
            "get_communication_system_prompt",
        )
        assert self._has_negation_block(prompt)

    def test_automation_has_negation_detection(self):
        prompt = self._get_prompt(
            "app.domains.automation.agents.automation_system_prompt",
            "get_automation_system_prompt",
        )
        assert self._has_negation_block(prompt)

    def test_ats_integration_has_negation_detection(self):
        prompt = self._get_prompt(
            "app.domains.ats_integration.agents.ats_integration_system_prompt",
            "get_ats_integration_system_prompt",
        )
        assert self._has_negation_block(prompt)


# ---------------------------------------------------------------------------
# VI. TestConfidenceInAgents
# ---------------------------------------------------------------------------

class TestConfidenceInAgents:
    """Verifica que confidence não é None e não é hardcoded 0.85 genérico nos agentes."""

    def _make_state_with_tools(self) -> dict:
        """Retorna um estado LangGraph simulado com tool calls."""
        msg_with_tool = MagicMock()
        msg_with_tool.content = "Resultado da análise"
        msg_with_tool.tool_calls = [{"name": "search_candidates"}]
        msg_with_tool.tool_call_id = None
        return {"messages": [msg_with_tool]}

    def _make_state_without_tools(self) -> dict:
        """Retorna um estado LangGraph simulado sem tool calls."""
        msg = MagicMock()
        msg.content = "Resposta sem ferramenta"
        msg.tool_calls = []
        msg.tool_call_id = None
        return {"messages": [msg]}

    def _make_state_with_error(self) -> dict:
        """Retorna um estado com erro."""
        return {"messages": [], "error": "Some error occurred"}

    def _call_state_to_output(self, AgentClass, state, context_dict):
        """Helper que instancia via __new__ sem chamar __init__ e chama _state_to_output."""
        agent = AgentClass.__new__(AgentClass)
        input_mock = MagicMock()
        input_mock.context = context_dict
        return agent._state_to_output(state, input_mock)

    def test_talent_confidence_not_none(self):
        from app.domains.recruiter_assistant.agents.talent_react_agent import TalentReActAgent
        output = self._call_state_to_output(
            TalentReActAgent,
            self._make_state_with_tools(),
            {"current_stage": "discovery", "collected_data": {}},
        )
        assert output.confidence is not None
        assert 0.0 <= output.confidence <= 1.0

    def test_talent_confidence_lower_on_error(self):
        from app.domains.recruiter_assistant.agents.talent_react_agent import TalentReActAgent
        output = self._call_state_to_output(
            TalentReActAgent,
            self._make_state_with_error(),
            {"current_stage": "discovery", "collected_data": {}},
        )
        assert output.confidence is not None
        assert output.confidence <= 0.5

    def test_kanban_confidence_not_none(self):
        from app.domains.recruiter_assistant.agents.kanban_react_agent import KanbanReActAgent
        output = self._call_state_to_output(
            KanbanReActAgent,
            self._make_state_with_tools(),
            {"current_stage": "pipeline_overview", "collected_data": {}},
        )
        assert output.confidence is not None
        assert 0.0 <= output.confidence <= 1.0

    def test_analytics_confidence_not_none(self):
        from app.domains.analytics.agents.analytics_react_agent import AnalyticsReActAgent
        output = self._call_state_to_output(
            AnalyticsReActAgent,
            self._make_state_with_tools(),
            {},
        )
        assert output.confidence is not None
        assert 0.0 <= output.confidence <= 1.0

    def test_analytics_confidence_lower_on_error(self):
        from app.domains.analytics.agents.analytics_react_agent import AnalyticsReActAgent
        output = self._call_state_to_output(
            AnalyticsReActAgent,
            self._make_state_with_error(),
            {},
        )
        assert output.confidence is not None
        assert output.confidence <= 0.5

    def test_communication_confidence_not_none(self):
        from app.domains.communication.agents.communication_react_agent import CommunicationReActAgent
        output = self._call_state_to_output(
            CommunicationReActAgent,
            self._make_state_with_tools(),
            {},
        )
        assert output.confidence is not None
        assert 0.0 <= output.confidence <= 1.0

    def test_policy_confidence_not_none(self):
        from app.domains.hiring_policy.agents.policy_react_agent import PolicyReActAgent
        output = self._call_state_to_output(
            PolicyReActAgent,
            self._make_state_with_tools(),
            {"current_stage": "onboarding", "policy_state": {}},
        )
        assert output.confidence is not None
        assert 0.0 <= output.confidence <= 1.0

    def test_jobs_mgmt_confidence_not_none(self):
        from app.domains.recruiter_assistant.agents.jobs_mgmt_react_agent import JobsManagementReActAgent
        output = self._call_state_to_output(
            JobsManagementReActAgent,
            self._make_state_with_tools(),
            {"current_stage": "overview", "collected_data": {}},
        )
        assert output.confidence is not None
        assert 0.0 <= output.confidence <= 1.0
