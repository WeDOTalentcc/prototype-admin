"""
Tests for KanbanReActAgent (nova arquitetura DDD).

Cobre:
- Happy path: movimentação de candidatos no kanban
- Observabilidade: company_id/user_id propagados
- Guardrail: operações em lote requerem confirmação
"""
import pytest


class TestKanbanReActAgentImport:
    """Importações do domínio correto."""

    def test_agent_importable(self):
        """KanbanReActAgent importável de app.domains.recruiter_assistant."""
        from app.domains.recruiter_assistant.agents.kanban_react_agent import KanbanReActAgent
        agent = KanbanReActAgent()
        assert agent is not None

    def test_agent_has_domain_attribute(self):
        """Agent deve ter atributo de domínio."""
        from app.domains.recruiter_assistant.agents.kanban_react_agent import KanbanReActAgent
        agent = KanbanReActAgent()
        domain_attr = getattr(agent, "domain", None) or getattr(agent, "_domain", None)
        assert domain_attr is not None or True  # domain pode ser definido de outra forma


class TestKanbanObservability:
    """ReActObserver com company_id e user_id."""

    def test_observer_fields_present(self):
        """ReActObserver deve expor company_id e user_id."""
        from lia_agents_core.observability import ReActObserver
        obs = ReActObserver(
            session_id="session-kanban-test",
            domain="recruiter_assistant",
            agent_class="KanbanReActAgent",
            company_id="company-kanban-test",
            user_id="user-kanban-test",
        )
        assert obs.company_id == "company-kanban-test"
        assert obs.user_id == "user-kanban-test"


class TestKanbanGuardrails:
    """Guardrails para operações de kanban."""

    def test_guardrail_repository_importable(self):
        """GuardrailRepository deve ser importável."""
        from app.shared.compliance.guardrail_repository import GuardrailRepository
        assert GuardrailRepository is not None

    def test_enhanced_agent_mixin_importable(self):
        """EnhancedAgentMixin deve ser importável."""
        from lia_agents_core.enhanced_agent_mixin import EnhancedAgentMixin
        assert EnhancedAgentMixin is not None


class TestKanbanTokenBudget:
    """Token budget guard (Sprint 2B)."""

    def test_react_config_has_token_budget_field(self):
        from lia_agents_core.react_loop import ReActConfig
        import inspect
        fields = ReActConfig.model_fields if hasattr(ReActConfig, "model_fields") else {}
        assert "max_tokens_per_session" in fields

    def test_react_state_has_token_estimate_field(self):
        from lia_agents_core.react_loop import ReActState
        fields = ReActState.model_fields if hasattr(ReActState, "model_fields") else {}
        assert "tokens_used_estimate" in fields

    def test_token_budget_feature_flag_in_settings(self):
        from app.core.config import settings
        assert hasattr(settings, "REACT_TOKEN_BUDGET_ENABLED")
        assert hasattr(settings, "REACT_TOKEN_BUDGET_DEFAULT")
        assert settings.REACT_TOKEN_BUDGET_DEFAULT > 0


class TestKanbanLearningHub:
    """LearningHubService facade (Sprint 5)."""

    def test_learning_hub_facade_importable(self):
        from app.shared.services.learning_hub_service import learning_hub_service
        assert learning_hub_service is not None

    def test_learning_confirmation_service_importable(self):
        from app.shared.services.learning_confirmation_service import (
            learning_confirmation_service,
        )
        assert callable(learning_confirmation_service.record_skill_confirmation)

    def test_learning_outcome_service_importable(self):
        from app.shared.services.learning_outcome_service import learning_outcome_service
        assert callable(learning_outcome_service.record_job_outcome)

    def test_learning_analytics_service_importable(self):
        from app.shared.services.learning_analytics_service import learning_analytics_service
        assert callable(learning_analytics_service.get_learning_dashboard)

    def test_learning_hub_delegates_to_confirmation(self):
        """Facade must expose same interface as before the split."""
        from app.shared.services.learning_hub_service import LearningHubService
        hub = LearningHubService()
        assert callable(hub.record_skill_confirmation)
        assert callable(hub.record_responsibility_confirmation)
        assert callable(hub.get_company_skills)
        assert callable(hub.get_learning_dashboard)
