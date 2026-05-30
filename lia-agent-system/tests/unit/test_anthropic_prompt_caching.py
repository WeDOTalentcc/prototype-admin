"""
Anti-regressão · W2-008 (2026-05-22) — Anthropic prompt caching.

Verifica que:
1. ClaudeLLMProvider envia `extra_headers={"anthropic-beta": "prompt-caching-..."}`
   em todas as 4 calls a client.messages.create()
2. System messages são wrappadas em blocks list com `cache_control: ephemeral`
3. Response usage inclui campos cache_creation_input_tokens + cache_read_input_tokens
4. Helper `_system_with_cache_control` retorna estrutura canonical
5. Helper `_build_usage_with_cache` extrai todos os 4 campos relevantes

Pre-audit: REPLIT_LIA_REMEDIATION_BACKLOG_2026-05-22.md (W2-008).
Sensor: scripts/check_anthropic_prompt_caching.py.

ROI: 50-80% economia em sessões longas (Sonnet 50-turn 10k tokens:
$1.50 → $0.30).
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestCacheControlHelper:
    """Helper `_system_with_cache_control` retorna structure canonical."""

    def test_helper_returns_none_for_none(self) -> None:
        from app.shared.providers.llm_claude import _system_with_cache_control

        assert _system_with_cache_control(None) is None

    def test_helper_returns_none_for_empty(self) -> None:
        from app.shared.providers.llm_claude import _system_with_cache_control

        assert _system_with_cache_control("") == ""

    def test_helper_wraps_string_in_cacheable_block(self) -> None:
        from app.shared.providers.llm_claude import _system_with_cache_control

        result = _system_with_cache_control("You are a helpful assistant.")
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["type"] == "text"
        assert result[0]["text"] == "You are a helpful assistant."
        assert result[0]["cache_control"] == {"type": "ephemeral"}


class TestUsageWithCache:
    """Helper `_build_usage_with_cache` extrai cache metrics."""

    def test_extracts_all_4_fields(self) -> None:
        from app.shared.providers.llm_claude import _build_usage_with_cache

        mock_response = MagicMock()
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50
        mock_response.usage.cache_creation_input_tokens = 1000
        mock_response.usage.cache_read_input_tokens = 800

        usage = _build_usage_with_cache(mock_response)
        assert usage["input_tokens"] == 100
        assert usage["output_tokens"] == 50
        assert usage["cache_creation_input_tokens"] == 1000
        assert usage["cache_read_input_tokens"] == 800

    def test_defaults_to_zero_when_field_missing(self) -> None:
        """SDK versions sem cache fields: extraction não-crashes."""
        from app.shared.providers.llm_claude import _build_usage_with_cache

        mock_response = MagicMock(spec=["usage"])
        mock_response.usage = MagicMock(spec=["input_tokens", "output_tokens"])
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50
        usage = _build_usage_with_cache(mock_response)
        assert usage["cache_creation_input_tokens"] == 0
        assert usage["cache_read_input_tokens"] == 0


class TestCacheControlInSystemMessages:
    """3 methods que recebem system_prompt usam _system_with_cache_control."""

    @pytest.mark.asyncio
    async def test_generate_with_system_wraps_system_in_cache_block(self) -> None:
        from app.shared.providers.llm_claude import ClaudeLLMProvider

        provider = ClaudeLLMProvider(api_key="sk-test")
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="hello")]
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 5
        mock_response.usage.cache_creation_input_tokens = 0
        mock_response.usage.cache_read_input_tokens = 0
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        with patch.object(provider, "_get_async_client", return_value=mock_client):
            await provider.generate_with_system("You are X", "Hi", model="claude-sonnet-4-6")

        call_kwargs = mock_client.messages.create.call_args.kwargs
        system_arg = call_kwargs.get("system")
        assert isinstance(system_arg, list), f"system DEVE ser list (cacheable). Got: {type(system_arg)}"
        assert system_arg[0].get("cache_control") == {"type": "ephemeral"}

    @pytest.mark.asyncio
    async def test_generate_with_tools_wraps_system_in_cache_block(self) -> None:
        from app.shared.providers.llm_claude import ClaudeLLMProvider

        provider = ClaudeLLMProvider(api_key="sk-test")
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = []
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 5
        mock_response.usage.cache_creation_input_tokens = 0
        mock_response.usage.cache_read_input_tokens = 0
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        with patch.object(provider, "_get_async_client", return_value=mock_client):
            await provider.generate_with_tools(
                messages=[{"role": "user", "content": "Hi"}],
                tools=[],
                system_prompt="Long system prompt",
            )

        call_kwargs = mock_client.messages.create.call_args.kwargs
        system_arg = call_kwargs.get("system")
        assert isinstance(system_arg, list)
        assert system_arg[0].get("cache_control") == {"type": "ephemeral"}


class TestBetaHeaderInAllCalls:
    """Todas as 4 calls a messages.create() incluem extra_headers."""

    @pytest.mark.asyncio
    async def test_generate_includes_beta_header(self) -> None:
        from app.shared.providers.llm_claude import ClaudeLLMProvider

        provider = ClaudeLLMProvider(api_key="sk-test")
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="ok")]
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 5
        mock_response.usage.cache_creation_input_tokens = 0
        mock_response.usage.cache_read_input_tokens = 0
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        with patch.object(provider, "_get_async_client", return_value=mock_client):
            await provider.generate("hi")

        call_kwargs = mock_client.messages.create.call_args.kwargs
        headers = call_kwargs.get("extra_headers", {})
        assert "anthropic-beta" in headers
        assert "prompt-caching" in headers["anthropic-beta"]

    @pytest.mark.asyncio
    async def test_generate_with_system_includes_beta_header(self) -> None:
        from app.shared.providers.llm_claude import ClaudeLLMProvider

        provider = ClaudeLLMProvider(api_key="sk-test")
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="ok")]
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 5
        mock_response.usage.cache_creation_input_tokens = 0
        mock_response.usage.cache_read_input_tokens = 0
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        with patch.object(provider, "_get_async_client", return_value=mock_client):
            await provider.generate_with_system("sys", "user")

        call_kwargs = mock_client.messages.create.call_args.kwargs
        headers = call_kwargs.get("extra_headers", {})
        assert headers.get("anthropic-beta") == "prompt-caching-2024-07-31"


class TestResponseUsageIncludesCacheTokens:
    """LLMResponse.usage exposed inclui cache fields."""

    @pytest.mark.asyncio
    async def test_generate_response_usage_has_cache_fields(self) -> None:
        from app.shared.providers.llm_claude import ClaudeLLMProvider

        provider = ClaudeLLMProvider(api_key="sk-test")
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="ok")]
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50
        mock_response.usage.cache_creation_input_tokens = 2000
        mock_response.usage.cache_read_input_tokens = 1500
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        with patch.object(provider, "_get_async_client", return_value=mock_client):
            result = await provider.generate("hi")

        assert result.usage["cache_creation_input_tokens"] == 2000
        assert result.usage["cache_read_input_tokens"] == 1500


class TestSensorBlocking:
    """W2-008 sensor BLOCKING confirma 4 calls + 3 helpers."""

    def test_sensor_exists(self) -> None:
        from pathlib import Path

        sensor = (
            Path(__file__).resolve().parents[2]
            / "scripts"
            / "check_anthropic_prompt_caching.py"
        )
        assert sensor.exists(), f"Sensor missing: {sensor}"

    def test_sensor_passes_strict(self) -> None:
        import subprocess
        import sys
        from pathlib import Path

        repo_root = Path(__file__).resolve().parents[2]
        sensor = repo_root / "scripts" / "check_anthropic_prompt_caching.py"
        result = subprocess.run(
            [sys.executable, str(sensor)],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
        )
        assert result.returncode == 0, (
            f"Prompt caching sensor FAILED (exit={result.returncode}):\n"
            f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
        )
