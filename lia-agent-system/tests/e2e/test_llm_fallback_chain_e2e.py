"""
Testes E2E — LLM Fallback Chain.

Valida o comportamento da cadeia de fallback do LLMProviderFactory:
  claude → gemini → openai

Cenários cobertos:
1. Provider primário (claude) falha → fallback para gemini OK
2. Provider primário e gemini falham → fallback para openai OK
3. Todos os providers falham → Exception clara com detalhes
4. Circuit breaker aberto em claude → bypass direto para gemini
5. Circuit breaker aberto em claude e gemini → bypass para openai
6. Fallback registra log de aviso quando ativado

Camada: E2E com mocks de providers (sem chamadas reais a APIs externas).
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.shared.resilience.circuit_breaker import CircuitBreakerError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_provider_response(text: str) -> MagicMock:
    """Cria um mock de LLMResponse com atributo .text."""
    resp = MagicMock()
    resp.text = text
    return resp


def _make_failing_provider(exc: Exception):
    """Cria um mock de provider que lança exceção."""
    provider = MagicMock()
    provider.generate = AsyncMock(side_effect=exc)
    provider.generate_with_system = AsyncMock(side_effect=exc)
    return provider


def _make_ok_provider(text: str = "resposta ok"):
    """Cria um mock de provider que responde com sucesso."""
    provider = MagicMock()
    provider.generate = AsyncMock(return_value=_make_provider_response(text))
    provider.generate_with_system = AsyncMock(return_value=_make_provider_response(text))
    return provider


# ---------------------------------------------------------------------------
# Cenário 1 — Primário falha, fallback para gemini
# ---------------------------------------------------------------------------

class TestFallbackChainClaudeFailsGeminiOk:

    @pytest.mark.asyncio
    async def test_fallback_from_claude_to_gemini(self):
        """Quando claude falha, generate_with_fallback usa gemini."""
        claude_provider = _make_failing_provider(RuntimeError("Claude API error"))
        gemini_provider = _make_ok_provider("resposta do gemini")
        openai_provider = _make_ok_provider("resposta do openai")

        providers = {
            "claude": claude_provider,
            "gemini": gemini_provider,
            "openai": openai_provider,
        }

        with patch("app.shared.providers.llm_factory.LLMProviderFactory.get", side_effect=lambda name: providers[name]):
            from app.shared.providers.llm_factory import LLMProviderFactory
            result = await LLMProviderFactory.generate_with_fallback("prompt teste")

        assert result == "resposta do gemini"

    @pytest.mark.asyncio
    async def test_fallback_logs_warning_when_primary_fails(self, caplog):
        """Fallback para gemini deve gerar log de aviso."""
        import logging
        claude_provider = _make_failing_provider(RuntimeError("Claude API error"))
        gemini_provider = _make_ok_provider("resposta do gemini")
        openai_provider = _make_ok_provider("resposta do openai")

        providers = {
            "claude": claude_provider,
            "gemini": gemini_provider,
            "openai": openai_provider,
        }

        with patch("app.shared.providers.llm_factory.LLMProviderFactory.get", side_effect=lambda name: providers[name]):
            with caplog.at_level(logging.WARNING, logger="app.shared.providers.llm_factory"):
                from app.shared.providers.llm_factory import LLMProviderFactory
                await LLMProviderFactory.generate_with_fallback("prompt teste")

        assert any("fallback" in rec.message.lower() for rec in caplog.records)

    @pytest.mark.asyncio
    async def test_fallback_returns_first_successful_provider(self):
        """generate_with_fallback retorna o texto do primeiro provider que funcionar."""
        claude_provider = _make_failing_provider(ValueError("timeout"))
        gemini_provider = _make_ok_provider("resposta GEMINI")
        openai_provider = _make_ok_provider("resposta OPENAI — não deve ser chamado")

        providers = {
            "claude": claude_provider,
            "gemini": gemini_provider,
            "openai": openai_provider,
        }

        with patch("app.shared.providers.llm_factory.LLMProviderFactory.get", side_effect=lambda name: providers[name]):
            from app.shared.providers.llm_factory import LLMProviderFactory
            result = await LLMProviderFactory.generate_with_fallback("prompt")

        assert result == "resposta GEMINI"
        openai_provider.generate.assert_not_called()


# ---------------------------------------------------------------------------
# Cenário 2 — Primário e gemini falham, fallback para openai
# ---------------------------------------------------------------------------

class TestFallbackChainClaudeAndGeminiFailOpenAIOk:

    @pytest.mark.asyncio
    async def test_fallback_from_claude_and_gemini_to_openai(self):
        """Quando claude e gemini falham, generate_with_fallback usa openai."""
        claude_provider = _make_failing_provider(RuntimeError("Claude down"))
        gemini_provider = _make_failing_provider(RuntimeError("Gemini down"))
        openai_provider = _make_ok_provider("resposta do openai")

        providers = {
            "claude": claude_provider,
            "gemini": gemini_provider,
            "openai": openai_provider,
        }

        with patch("app.shared.providers.llm_factory.LLMProviderFactory.get", side_effect=lambda name: providers[name]):
            from app.shared.providers.llm_factory import LLMProviderFactory
            result = await LLMProviderFactory.generate_with_fallback("prompt teste")

        assert result == "resposta do openai"

    @pytest.mark.asyncio
    async def test_all_providers_attempted_when_two_fail(self):
        """Todos os providers são tentados antes de desistir."""
        claude_provider = _make_failing_provider(RuntimeError("Claude down"))
        gemini_provider = _make_failing_provider(RuntimeError("Gemini down"))
        openai_provider = _make_ok_provider("openai ok")

        providers = {
            "claude": claude_provider,
            "gemini": gemini_provider,
            "openai": openai_provider,
        }

        with patch("app.shared.providers.llm_factory.LLMProviderFactory.get", side_effect=lambda name: providers[name]):
            from app.shared.providers.llm_factory import LLMProviderFactory
            await LLMProviderFactory.generate_with_fallback("prompt")

        claude_provider.generate.assert_called_once()
        gemini_provider.generate.assert_called_once()
        openai_provider.generate.assert_called_once()


# ---------------------------------------------------------------------------
# Cenário 3 — Todos os providers falham
# ---------------------------------------------------------------------------

class TestFallbackChainAllFail:

    @pytest.mark.asyncio
    async def test_all_providers_fail_raises_exception(self):
        """Quando todos os providers falham, Exception é levantada com detalhes."""
        claude_provider = _make_failing_provider(RuntimeError("Claude error"))
        gemini_provider = _make_failing_provider(RuntimeError("Gemini error"))
        openai_provider = _make_failing_provider(RuntimeError("OpenAI error"))

        providers = {
            "claude": claude_provider,
            "gemini": gemini_provider,
            "openai": openai_provider,
        }

        with patch("app.shared.providers.llm_factory.LLMProviderFactory.get", side_effect=lambda name: providers[name]):
            from app.shared.providers.llm_factory import LLMProviderFactory
            with pytest.raises(Exception) as exc_info:
                await LLMProviderFactory.generate_with_fallback("prompt teste")

        error_msg = str(exc_info.value)
        assert "All LLM providers failed" in error_msg
        assert "claude" in error_msg
        assert "gemini" in error_msg
        assert "openai" in error_msg

    @pytest.mark.asyncio
    async def test_all_providers_fail_exception_includes_individual_errors(self):
        """Exception inclui detalhes de cada falha individual."""
        claude_provider = _make_failing_provider(ValueError("timeout_claude"))
        gemini_provider = _make_failing_provider(ValueError("timeout_gemini"))
        openai_provider = _make_failing_provider(ValueError("timeout_openai"))

        providers = {
            "claude": claude_provider,
            "gemini": gemini_provider,
            "openai": openai_provider,
        }

        with patch("app.shared.providers.llm_factory.LLMProviderFactory.get", side_effect=lambda name: providers[name]):
            from app.shared.providers.llm_factory import LLMProviderFactory
            with pytest.raises(Exception) as exc_info:
                await LLMProviderFactory.generate_with_fallback("prompt")

        error_msg = str(exc_info.value)
        assert "timeout_claude" in error_msg or "ValueError" in error_msg


# ---------------------------------------------------------------------------
# Cenário 4 — Circuit breaker aberto em claude
# ---------------------------------------------------------------------------

class TestFallbackChainCircuitBreakerOpen:

    @pytest.mark.asyncio
    async def test_circuit_open_claude_bypasses_to_gemini(self):
        """Circuit breaker aberto em claude é tratado como falha e gemini é usado."""
        cb_error = CircuitBreakerError("claude", retry_after=25.0)
        claude_provider = _make_failing_provider(cb_error)
        gemini_provider = _make_ok_provider("resposta gemini via circuit bypass")
        openai_provider = _make_ok_provider("openai — não deve ser usado")

        providers = {
            "claude": claude_provider,
            "gemini": gemini_provider,
            "openai": openai_provider,
        }

        with patch("app.shared.providers.llm_factory.LLMProviderFactory.get", side_effect=lambda name: providers[name]):
            from app.shared.providers.llm_factory import LLMProviderFactory
            result = await LLMProviderFactory.generate_with_fallback("prompt")

        assert result == "resposta gemini via circuit bypass"
        openai_provider.generate.assert_not_called()

    @pytest.mark.asyncio
    async def test_circuit_open_logs_retry_after(self, caplog):
        """Circuit breaker aberto em claude deve logar retry_after."""
        import logging
        cb_error = CircuitBreakerError("claude", retry_after=30.0)
        claude_provider = _make_failing_provider(cb_error)
        gemini_provider = _make_ok_provider("gemini ok")
        openai_provider = _make_ok_provider("openai ok")

        providers = {
            "claude": claude_provider,
            "gemini": gemini_provider,
            "openai": openai_provider,
        }

        with patch("app.shared.providers.llm_factory.LLMProviderFactory.get", side_effect=lambda name: providers[name]):
            with caplog.at_level(logging.WARNING, logger="app.shared.providers.llm_factory"):
                from app.shared.providers.llm_factory import LLMProviderFactory
                await LLMProviderFactory.generate_with_fallback("prompt")

        assert any("circuit" in rec.message.lower() for rec in caplog.records)

    @pytest.mark.asyncio
    async def test_circuit_open_claude_and_gemini_uses_openai(self):
        """Circuit breaker aberto em claude e gemini → openai usado como último fallback."""
        claude_cb_error = CircuitBreakerError("claude", retry_after=25.0)
        gemini_cb_error = CircuitBreakerError("gemini", retry_after=15.0)

        claude_provider = _make_failing_provider(claude_cb_error)
        gemini_provider = _make_failing_provider(gemini_cb_error)
        openai_provider = _make_ok_provider("openai como último recurso")

        providers = {
            "claude": claude_provider,
            "gemini": gemini_provider,
            "openai": openai_provider,
        }

        with patch("app.shared.providers.llm_factory.LLMProviderFactory.get", side_effect=lambda name: providers[name]):
            from app.shared.providers.llm_factory import LLMProviderFactory
            result = await LLMProviderFactory.generate_with_fallback("prompt")

        assert result == "openai como último recurso"

    @pytest.mark.asyncio
    async def test_circuit_open_errors_included_in_final_exception(self):
        """Quando todos os circuits estão abertos, Exception inclui retry_after de cada circuit."""
        cb_errors = [
            CircuitBreakerError("claude", retry_after=25.0),
            CircuitBreakerError("gemini", retry_after=15.0),
            CircuitBreakerError("openai", retry_after=10.0),
        ]

        provider_names = ["claude", "gemini", "openai"]
        providers = {
            name: _make_failing_provider(err)
            for name, err in zip(provider_names, cb_errors)
        }

        with patch("app.shared.providers.llm_factory.LLMProviderFactory.get", side_effect=lambda name: providers[name]):
            from app.shared.providers.llm_factory import LLMProviderFactory
            with pytest.raises(Exception) as exc_info:
                await LLMProviderFactory.generate_with_fallback("prompt")

        error_msg = str(exc_info.value)
        assert "circuit open" in error_msg
        assert "claude" in error_msg
        assert "gemini" in error_msg
        assert "openai" in error_msg


# ---------------------------------------------------------------------------
# Cenário 5 — generate_with_fallback com system prompt
# ---------------------------------------------------------------------------

class TestFallbackChainWithSystemPrompt:

    @pytest.mark.asyncio
    async def test_fallback_uses_generate_with_system_when_system_provided(self):
        """Quando system prompt é passado, generate_with_system é chamado."""
        claude_provider = _make_failing_provider(RuntimeError("Claude down"))
        gemini_provider = _make_ok_provider("resposta com system prompt")
        openai_provider = _make_ok_provider("openai")

        providers = {
            "claude": claude_provider,
            "gemini": gemini_provider,
            "openai": openai_provider,
        }

        with patch("app.shared.providers.llm_factory.LLMProviderFactory.get", side_effect=lambda name: providers[name]):
            from app.shared.providers.llm_factory import LLMProviderFactory
            result = await LLMProviderFactory.generate_with_fallback(
                "prompt", system="Você é um recrutador especialista."
            )

        assert result == "resposta com system prompt"
        gemini_provider.generate_with_system.assert_called_once()

    @pytest.mark.asyncio
    async def test_fallback_without_system_calls_generate(self):
        """Sem system prompt, generate() é chamado (não generate_with_system)."""
        claude_provider = _make_failing_provider(RuntimeError("Claude down"))
        gemini_provider = _make_ok_provider("resposta sem system")
        openai_provider = _make_ok_provider("openai")

        providers = {
            "claude": claude_provider,
            "gemini": gemini_provider,
            "openai": openai_provider,
        }

        with patch("app.shared.providers.llm_factory.LLMProviderFactory.get", side_effect=lambda name: providers[name]):
            from app.shared.providers.llm_factory import LLMProviderFactory
            await LLMProviderFactory.generate_with_fallback("prompt sem system")

        gemini_provider.generate.assert_called_once()
        gemini_provider.generate_with_system.assert_not_called()


# ---------------------------------------------------------------------------
# Cenário 6 — Ordem de fallback verificada
# ---------------------------------------------------------------------------

class TestFallbackOrder:

    @pytest.mark.asyncio
    async def test_fallback_order_is_claude_gemini_openai(self):
        """A ordem de fallback deve sempre ser: claude → gemini → openai."""
        call_order = []

        def _make_tracking_provider(name: str) -> MagicMock:
            async def _tracked(*args, **kwargs):
                call_order.append(name)
                raise RuntimeError(f"{name} fail")

            provider = MagicMock()
            provider.generate = AsyncMock(side_effect=_tracked)
            provider.generate_with_system = AsyncMock(side_effect=_tracked)
            return provider

        providers = {
            "claude": _make_tracking_provider("claude"),
            "gemini": _make_tracking_provider("gemini"),
            "openai": _make_tracking_provider("openai"),
        }

        with patch("app.shared.providers.llm_factory.LLMProviderFactory.get", side_effect=lambda name: providers[name]):
            from app.shared.providers.llm_factory import LLMProviderFactory
            with pytest.raises(Exception):
                await LLMProviderFactory.generate_with_fallback("prompt")

        assert call_order == ["claude", "gemini", "openai"], (
            f"Ordem de fallback incorreta: {call_order}"
        )
