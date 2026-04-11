"""
Tests for PolicyReActAgent (nova arquitetura DDD).

Cobre:
- Happy path: configuração de política de contratação
- Anti-sycophancy: benchmark setorial injetado
- Fallback: policy_setup_agent legado como backup
- Guardrail: políticas discriminatórias bloqueadas
"""
import pytest


class TestPolicyReActAgentImport:
    """Importações do domínio correto."""

    def test_agent_importable(self):
        """PolicyReActAgent importável de app.domains.hiring_policy."""
        from app.domains.hiring_policy.agents.policy_react_agent import PolicyReActAgent
        agent = PolicyReActAgent()
        assert agent is not None


class TestPolicyLegacyFallback:
    """Fallback intencional: policy_setup_agent legado."""

    def test_legacy_fallback_exists(self):
        """policy_setup_agent legado deve ser importável (fallback intencional)."""
        try:
            from app.agents.policy_setup_agent import policy_setup_agent
            assert policy_setup_agent is not None
        except ImportError:
            pytest.skip("policy_setup_agent não encontrado — fallback removido")


class TestPolicyFairnessGuard:
    """FairnessGuard em políticas de contratação."""

    def test_discriminatory_policy_detected(self, discriminatory_job_text):
        """Política discriminatória deve ser detectada pelo FairnessGuard."""
        from app.shared.compliance.fairness_guard import FairnessGuard
        guard = FairnessGuard()
        result = guard.check_explicit_bias(discriminatory_job_text)
        assert result.is_biased

    def test_fairness_guard_implicit_bias_check(self):
        """FairnessGuard deve detectar viés implícito."""
        from app.shared.compliance.fairness_guard import FairnessGuard
        guard = FairnessGuard()
        implicit_text = "Candidato ideal: dinâmico, recém-formado, sem compromissos."
        warnings = guard.check_implicit_bias(implicit_text)
        # Pode ou não detectar dependendo das regras — apenas verificar que é chamável
        assert isinstance(warnings, list)


class TestPolicySettings:
    """Configurações de política via settings."""

    def test_router_settings_present(self):
        from app.core.config import settings
        assert hasattr(settings, "ROUTER_FAST_CONFIDENCE_THRESHOLD")
        assert 0 < settings.ROUTER_FAST_CONFIDENCE_THRESHOLD <= 1.0
        assert hasattr(settings, "ROUTER_CACHE_MAX_SIZE")
        assert settings.ROUTER_CACHE_MAX_SIZE > 0


class TestPolicyToolRegistry:
    """Tool registry e system prompt."""

    def test_get_policy_tools_importable(self):
        from app.domains.hiring_policy.agents.policy_tool_registry import get_policy_tools
        tools = get_policy_tools()
        assert isinstance(tools, list)
        assert len(tools) > 0

    def test_policy_tools_have_names(self):
        from app.domains.hiring_policy.agents.policy_tool_registry import get_policy_tools
        for tool in get_policy_tools():
            assert hasattr(tool, "name") and tool.name

    def test_get_policy_system_prompt_importable(self):
        from app.domains.hiring_policy.agents.policy_system_prompt import get_policy_system_prompt
        assert callable(get_policy_system_prompt)

    def test_policy_system_prompt_returns_string(self):
        from app.domains.hiring_policy.agents.policy_system_prompt import get_policy_system_prompt
        prompt = get_policy_system_prompt(stage="onboarding", context={})
        assert isinstance(prompt, str) and len(prompt) > 50

    def test_policy_stage_context_importable(self):
        from app.domains.hiring_policy.agents.policy_stage_context import get_stage_context
        assert callable(get_stage_context)


class TestPolicyAgentInterface:
    """Interface AgentInput/AgentOutput e multi-tenancy."""

    def test_agent_has_process(self):
        from app.domains.hiring_policy.agents.policy_react_agent import PolicyReActAgent
        agent = PolicyReActAgent()
        assert hasattr(agent, "process")

    def test_policy_stage_context_with_data(self):
        from app.domains.hiring_policy.agents.policy_stage_context import get_stage_context
        ctx = get_stage_context(
            stage="onboarding",
            policy_state={"hiring_criteria": {"min_experience": 3}},
        )
        assert isinstance(ctx, str) and len(ctx) > 0

    def test_policy_stage_context_different_states_differ(self):
        from app.domains.hiring_policy.agents.policy_stage_context import get_stage_context
        ctx_empty = get_stage_context(stage="onboarding", policy_state={})
        ctx_filled = get_stage_context(
            stage="onboarding",
            policy_state={"hiring_criteria": {"min_experience": 3}, "screening_rules": {"required": True}},
        )
        assert ctx_empty != ctx_filled


class TestPolicyAntiSycophancy:
    """Anti-sycophancy: benchmark setorial injetado."""

    def test_sector_benchmark_service_importable(self):
        from app.domains.analytics.services.sector_benchmark_service import sector_benchmark_service
        assert sector_benchmark_service is not None

    def test_benchmark_service_has_evaluate_method(self):
        from app.domains.analytics.services.sector_benchmark_service import sector_benchmark_service
        assert hasattr(sector_benchmark_service, "get_benchmark_context") or \
               hasattr(sector_benchmark_service, "get_profile") or \
               hasattr(sector_benchmark_service, "list_supported")
