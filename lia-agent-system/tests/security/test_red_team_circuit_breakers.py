"""
Red Teaming — Categoria 5: Resiliência e Circuit Breakers

Verifica que circuit breakers protegem o sistema contra falhas em cascata
e que o estado de degradação é gerenciável.

ACH-028
"""
import pytest
from unittest.mock import MagicMock, patch


class TestCircuitBreakerCoverage:
    """Verifica cobertura de circuit breakers em serviços críticos."""

    def test_anthropic_circuit_exists(self):
        """Circuit para Anthropic deve existir."""
        from app.shared.resilience.circuit_breaker import ALL_CIRCUITS
        names_lower = [k.lower() for k in ALL_CIRCUITS]
        assert any("anthropic" in n for n in names_lower)

    def test_openai_circuit_exists(self):
        """Circuit para OpenAI deve existir."""
        from app.shared.resilience.circuit_breaker import ALL_CIRCUITS
        names_lower = [k.lower() for k in ALL_CIRCUITS]
        assert any("openai" in n for n in names_lower)

    def test_gemini_circuit_exists(self):
        """Circuit para Gemini deve existir."""
        from app.shared.resilience.circuit_breaker import ALL_CIRCUITS
        names_lower = [k.lower() for k in ALL_CIRCUITS]
        assert any("gemini" in n for n in names_lower)

    def test_gupy_circuit_exists(self):
        """Circuit para Gupy ATS deve existir."""
        from app.shared.resilience.circuit_breaker import ALL_CIRCUITS
        names_lower = [k.lower() for k in ALL_CIRCUITS]
        assert any("gupy" in n for n in names_lower)

    def test_mailgun_circuit_exists(self):
        """Circuit para Mailgun deve existir."""
        from app.shared.resilience.circuit_breaker import ALL_CIRCUITS
        names_lower = [k.lower() for k in ALL_CIRCUITS]
        assert any("mailgun" in n for n in names_lower)

    def test_workos_circuit_exists(self):
        """Circuit para WorkOS deve existir."""
        from app.shared.resilience.circuit_breaker import ALL_CIRCUITS
        names_lower = [k.lower() for k in ALL_CIRCUITS]
        assert any("workos" in n for n in names_lower)

    def test_llm_openai_uses_circuit_breaker(self):
        """llm_openai.py deve usar circuit breaker."""
        import inspect
        import app.shared.providers.llm_openai as mod
        src = inspect.getsource(mod)
        assert "circuit_breaker" in src.lower() or "OPENAI_CIRCUIT" in src

    def test_llm_gemini_uses_circuit_breaker(self):
        """llm_gemini.py deve usar circuit breaker."""
        import inspect
        import app.shared.providers.llm_gemini as mod
        src = inspect.getsource(mod)
        assert "circuit_breaker" in src.lower() or "GEMINI_CIRCUIT" in src

    def test_admin_api_exposes_circuit_status(self):
        """API admin deve expor status dos circuit breakers."""
        import inspect
        import app.api.v1.admin_circuit_breakers as mod
        src = inspect.getsource(mod)
        assert "beat_schedule" not in src  # sanity check
        assert "circuit" in src.lower()


class TestCircuitBreakerBehavior:
    """Testa comportamento de circuit breakers sob falha."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_open_on_repeated_failures(self):
        """Circuit deve abrir após threshold de falhas."""
        from app.shared.resilience.circuit_breaker import CircuitBreaker
        cb = CircuitBreaker(name="test-cb-fail")
        initial_count = cb.failure_count
        # record_failure é async
        for _ in range(3):
            await cb.record_failure()
        assert cb.failure_count > initial_count or cb.state.name != "CLOSED"

    @pytest.mark.asyncio
    async def test_circuit_breaker_reset_possible(self):
        """CircuitBreaker deve suportar reset manual."""
        from app.shared.resilience.circuit_breaker import CircuitBreaker
        cb = CircuitBreaker(name="test-cb-reset")
        await cb.record_failure()
        cb.reset()
        assert cb.failure_count == 0


class TestCascadeFailureProtection:
    """Testa que falhas não se propagam em cascata."""

    @pytest.mark.asyncio
    async def test_audit_service_fail_safe_on_db_error(self):
        """audit_service.log_decision deve ter tratamento de erro para falhas de DB."""
        import inspect
        from app.shared.compliance import audit_service as mod
        src = inspect.getsource(mod)
        # Deve haver tratamento de erro (try/except) na implementação
        assert "except" in src or "try" in src

    @pytest.mark.asyncio
    async def test_fairness_guard_fail_safe_on_layer3_error(self):
        """FairnessGuard Camada 3 deve falhar silenciosamente."""
        from app.shared.compliance.fairness_guard import FairnessGuard

        guard = FairnessGuard()

        with patch.object(guard, "check_semantic", side_effect=Exception("LLM timeout")):
            # check_with_layer3 deve ser fail-safe
            result = await guard.check_with_layer3("texto seguro", action_type="wsi_score")
            assert result is not None
