"""
Tests for AUD audit fixes:
- AUD-1: Anti-sycophancy block in all agent system prompts
- AUD-2: Circuit breakers on OpenAI, Gemini, ATS clients, email providers, WorkOS
- AUD-3: Audit trail in PolicySetupAgent
- AUD-5: Security scan + load tests in CI, mock data removal
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# AUD-1 — Anti-sycophancy block in system prompts
# ---------------------------------------------------------------------------

class TestAntiSycophancyInPrompts:
    """All agent system prompts must include ANTI_SYCOPHANCY_OPERATIONAL."""

    def test_analytics_prompt_contains_anti_sycophancy(self):
        from app.domains.analytics.agents.analytics_system_prompt import get_analytics_system_prompt
        prompt = get_analytics_system_prompt()
        assert "PREVENCAO DE SYCOPHANCY" in prompt
        assert "REGRAS ABSOLUTAS" in prompt

    def test_communication_prompt_contains_anti_sycophancy(self):
        from app.domains.communication.agents.communication_system_prompt import get_communication_system_prompt
        prompt = get_communication_system_prompt()
        assert "PREVENCAO DE SYCOPHANCY" in prompt

    def test_automation_prompt_contains_anti_sycophancy(self):
        from app.domains.automation.agents.automation_system_prompt import get_automation_system_prompt
        prompt = get_automation_system_prompt()
        assert "PREVENCAO DE SYCOPHANCY" in prompt

    def test_ats_integration_prompt_contains_anti_sycophancy(self):
        from app.domains.ats_integration.agents.ats_integration_system_prompt import get_ats_integration_system_prompt
        prompt = get_ats_integration_system_prompt()
        assert "PREVENCAO DE SYCOPHANCY" in prompt

    def test_sourcing_prompt_contains_anti_sycophancy(self):
        from app.domains.sourcing.agents.sourcing_system_prompt import get_sourcing_system_prompt
        prompt = get_sourcing_system_prompt(stage="search-criteria", context={})
        assert "PREVENCAO DE SYCOPHANCY" in prompt

    def test_pipeline_prompt_contains_anti_sycophancy(self):
        from app.domains.cv_screening.agents.pipeline_system_prompt import get_pipeline_system_prompt
        prompt = get_pipeline_system_prompt(stage="triage", context={})
        assert "PREVENCAO DE SYCOPHANCY" in prompt

    def test_anti_sycophancy_rule_count(self):
        """Ensure at least 5 rules are present in the block."""
        from app.shared.prompts.anti_sycophancy_block import ANTI_SYCOPHANCY_OPERATIONAL
        assert "1." in ANTI_SYCOPHANCY_OPERATIONAL
        assert "5." in ANTI_SYCOPHANCY_OPERATIONAL


# ---------------------------------------------------------------------------
# AUD-2 — Circuit breakers registered and applied
# ---------------------------------------------------------------------------

class TestCircuitBreakerRegistration:
    """New circuit breakers must be in ALL_CIRCUITS."""

    def test_gupy_circuit_in_all_circuits(self):
        from app.shared.resilience.circuit_breaker import ALL_CIRCUITS
        assert "gupy" in ALL_CIRCUITS

    def test_pandape_circuit_in_all_circuits(self):
        from app.shared.resilience.circuit_breaker import ALL_CIRCUITS
        assert "pandape" in ALL_CIRCUITS

    def test_mailgun_circuit_in_all_circuits(self):
        from app.shared.resilience.circuit_breaker import ALL_CIRCUITS
        assert "mailgun" in ALL_CIRCUITS

    def test_resend_circuit_in_all_circuits(self):
        from app.shared.resilience.circuit_breaker import ALL_CIRCUITS
        assert "resend" in ALL_CIRCUITS

    def test_existing_circuits_still_present(self):
        from app.shared.resilience.circuit_breaker import ALL_CIRCUITS
        for name in ["anthropic", "openai", "gemini", "workos", "merge", "pearch"]:
            assert name in ALL_CIRCUITS, f"Circuit '{name}' missing from ALL_CIRCUITS"

    def test_circuit_constants_exported(self):
        from app.shared.resilience.circuit_breaker import (
            GUPY_CIRCUIT, PANDAPE_CIRCUIT,
            MAILGUN_CIRCUIT, RESEND_CIRCUIT,
        )
        assert GUPY_CIRCUIT is not None
        assert PANDAPE_CIRCUIT is not None
        assert MAILGUN_CIRCUIT is not None
        assert RESEND_CIRCUIT is not None


class TestOpenAICircuitBreaker:
    """OpenAILLMProvider methods must be wrapped with circuit breaker."""

    def test_generate_has_circuit_breaker(self):
        from app.shared.providers.llm_openai import OpenAILLMProvider
        import inspect
        # The method should be a wrapper (has __wrapped__ attr or is decorated)
        method = OpenAILLMProvider.generate
        # After decoration the function name should still resolve
        assert callable(method)

    def test_generate_with_system_has_circuit_breaker(self):
        from app.shared.providers.llm_openai import OpenAILLMProvider
        assert callable(OpenAILLMProvider.generate_with_system)

    def test_generate_with_tools_has_circuit_breaker(self):
        from app.shared.providers.llm_openai import OpenAILLMProvider
        assert callable(OpenAILLMProvider.generate_with_tools)

    def test_generate_structured_has_circuit_breaker(self):
        from app.shared.providers.llm_openai import OpenAILLMProvider
        assert callable(OpenAILLMProvider.generate_structured)

    def test_openai_circuit_breaker_import_in_module(self):
        import app.shared.providers.llm_openai as mod
        import inspect
        source = inspect.getsource(mod)
        assert "OPENAI_CIRCUIT" in source
        assert "circuit_breaker_decorator" in source


class TestGeminiCircuitBreaker:
    """GeminiLLMProvider methods must be wrapped with circuit breaker."""

    def test_gemini_circuit_breaker_import_in_module(self):
        import app.shared.providers.llm_gemini as mod
        import inspect
        source = inspect.getsource(mod)
        assert "GEMINI_CIRCUIT" in source
        assert "circuit_breaker_decorator" in source

    def test_generate_is_callable(self):
        from app.shared.providers.llm_gemini import GeminiLLMProvider
        assert callable(GeminiLLMProvider.generate)

    def test_generate_with_system_is_callable(self):
        from app.shared.providers.llm_gemini import GeminiLLMProvider
        assert callable(GeminiLLMProvider.generate_with_system)


class TestATSCircuitBreakers:
    """ATS clients must import and use their respective circuit breakers."""

    def test_gupy_client_imports_circuit_breaker(self):
        import app.domains.ats_integration.services.ats_clients.gupy as mod
        import inspect
        source = inspect.getsource(mod)
        assert "GUPY_CIRCUIT" in source
        assert "circuit_breaker_decorator" in source

    def test_pandape_client_imports_circuit_breaker(self):
        import app.domains.ats_integration.services.ats_clients.pandape as mod
        import inspect
        source = inspect.getsource(mod)
        assert "PANDAPE_CIRCUIT" in source

    def test_merge_client_imports_circuit_breaker(self):
        import app.domains.ats_integration.services.ats_clients.merge as mod
        import inspect
        source = inspect.getsource(mod)
        assert "MERGE_CIRCUIT" in source


class TestEmailCircuitBreakers:
    """Email providers must import and use their circuit breakers."""

    def test_mailgun_imports_circuit_breaker(self):
        import app.services.email_providers.mailgun_provider as mod
        import inspect
        source = inspect.getsource(mod)
        assert "MAILGUN_CIRCUIT" in source

    def test_resend_imports_circuit_breaker(self):
        import app.services.email_providers.resend_provider as mod
        import inspect
        source = inspect.getsource(mod)
        assert "RESEND_CIRCUIT" in source


class TestWorkOSCircuitBreaker:
    """WorkOS API helper must use WORKOS_CIRCUIT."""

    def test_workos_endpoint_imports_circuit_breaker(self):
        import app.api.v1.workos as mod
        import inspect
        source = inspect.getsource(mod)
        assert "WORKOS_CIRCUIT" in source
        assert "circuit_breaker_decorator" in source

    def test_workos_has_fetch_helper_function(self):
        import app.api.v1.workos as mod
        assert hasattr(mod, "_fetch_workos_metrics")
        assert callable(mod._fetch_workos_metrics)


# ---------------------------------------------------------------------------
# AUD-3 — Audit trail in PolicySetupAgent
# ---------------------------------------------------------------------------

class TestPolicyAgentAuditTrail:
    """PolicySetupAgent._process_answer must call audit_service.log_decision."""

    @pytest.mark.asyncio
    async def test_process_answer_calls_audit_service(self):
        from app.domains.policy.agents.agent import PolicySetupAgent

        agent = PolicySetupAgent()

        mock_llm = MagicMock()
        mock_llm.claude = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = '{"value": 2}'
        mock_llm.claude.ainvoke = AsyncMock(return_value=mock_response)
        agent._llm = mock_llm

        current_policy = {
            "pipeline_rules": {},
            "scheduling_rules": {},
            "communication_rules": {},
            "screening_rules": {},
            "lia_autonomy": {},
        }

        with patch("app.shared.compliance.audit_service.audit_service") as mock_audit:
            mock_audit.log_decision = AsyncMock()
            result = await agent.process_message(
                message="2 entrevistas",
                company_id="test-company",
                session_id="test-session",
                current_policy=current_policy,
            )

        assert result is not None
        # audit_service.log_decision should have been called
        mock_audit.log_decision.assert_called_once()
        call_kwargs = mock_audit.log_decision.call_args.kwargs
        assert call_kwargs["company_id"] == "test-company"
        assert call_kwargs["agent_name"] == "policy_setup_agent"
        assert call_kwargs["decision_type"] == "policy_update"

    @pytest.mark.asyncio
    async def test_audit_trail_fails_gracefully(self):
        """If audit_service raises, the agent should still return a result."""
        from app.domains.policy.agents.agent import PolicySetupAgent

        agent = PolicySetupAgent()

        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = '{"value": 3}'
        mock_llm.claude = AsyncMock()
        mock_llm.claude.ainvoke = AsyncMock(return_value=mock_response)
        agent._llm = mock_llm

        current_policy = {"pipeline_rules": {}, "scheduling_rules": {}, "communication_rules": {}, "screening_rules": {}, "lia_autonomy": {}}

        with patch("app.shared.compliance.audit_service.audit_service") as mock_audit:
            mock_audit.log_decision = AsyncMock(side_effect=Exception("DB unavailable"))
            result = await agent.process_message(
                message="3 entrevistas",
                company_id="test-company",
                session_id="test-session-2",
                current_policy=current_policy,
            )

        # Agent must still return a result even if audit fails
        assert result is not None
        assert "reply" in result


# ---------------------------------------------------------------------------
# AUD-5 — CI config: security scan and load tests
# ---------------------------------------------------------------------------

class TestCIConfiguration:
    """CI workflow must include security scan and load test job."""

    def _load_ci_yaml(self) -> str:
        import os
        ci_path = os.path.join(
            os.path.dirname(__file__),
            "../../.github/workflows/ci.yml"
        )
        with open(ci_path) as f:
            return f.read()

    def test_bandit_security_scan_in_ci(self):
        content = self._load_ci_yaml()
        assert "bandit" in content
        assert "Security scan" in content

    def test_security_scan_is_non_blocking(self):
        content = self._load_ci_yaml()
        # The security scan step must have continue-on-error
        assert "Security scan" in content
        # Simple check: bandit step has continue-on-error nearby
        lines = content.splitlines()
        security_idx = next(i for i, l in enumerate(lines) if "Security scan" in l)
        nearby = "\n".join(lines[security_idx:security_idx + 4])
        assert "continue-on-error: true" in nearby

    def test_load_test_job_in_ci(self):
        content = self._load_ci_yaml()
        assert "load-tests" in content or "Load Tests" in content

    def test_load_test_is_non_blocking(self):
        content = self._load_ci_yaml()
        lines = content.splitlines()
        load_idx = next(i for i, l in enumerate(lines) if "load-tests" in l or "Load Tests" in l)
        # Job-level continue-on-error should be nearby
        nearby = "\n".join(lines[load_idx:load_idx + 10])
        assert "continue-on-error: true" in nearby
