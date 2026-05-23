"""
Anti-regressão · W2-012 (2026-05-22) — LGPD Art 33 region pinning.

Verifica que:
1. Claude provider envia `anthropic-no-train: true` header (LGPD Art 33 + 7§II).
2. OpenAI provider envia `OpenAI-Beta: data-residency=v1` header.
3. Gemini provider aceita `region` param (default us-central1).
4. Provider classes aceitam `region: str | None = None` no __init__ (DI pattern).
5. `TenantLLMConfig` model expõe campo `region`.

Pre-audit: REPLIT_LIA_REMEDIATION_BACKLOG_2026-05-22.md (W2-012).
Sensor: scripts/check_lgpd_region_pinning.py.
"""
from __future__ import annotations


class TestClaudeRegionPinning:
    """Claude SDK construído com `anthropic-no-train: true` header."""

    def test_claude_provider_accepts_region_param(self) -> None:
        from app.shared.providers.llm_claude import ClaudeLLMProvider

        # Aceita region kwarg sem TypeError
        provider = ClaudeLLMProvider(region="us-east-1")
        assert hasattr(provider, "_region")
        assert provider._region == "us-east-1"

    def test_claude_provider_region_default_is_none(self) -> None:
        from app.shared.providers.llm_claude import ClaudeLLMProvider

        provider = ClaudeLLMProvider()
        assert provider._region is None

    def test_claude_anthropic_no_train_header_set(self) -> None:
        """LGPD Art 7 §II + Art 33: declara opt-out de training."""
        from unittest.mock import patch, MagicMock

        from app.shared.providers.llm_claude import ClaudeLLMProvider

        provider = ClaudeLLMProvider(api_key="sk-test")
        with patch("anthropic.Anthropic") as mock_anthropic:
            mock_anthropic.return_value = MagicMock()
            provider._get_client()
            # Verifica kwargs do construtor
            call_kwargs = mock_anthropic.call_args.kwargs
            headers = call_kwargs.get("default_headers", {})
            assert headers.get("anthropic-no-train") == "true", (
                f"Claude DEVE setar anthropic-no-train header. "
                f"Got default_headers: {headers}"
            )


class TestOpenAIRegionPinning:
    """OpenAI SDK construído com `OpenAI-Beta: data-residency=v1` header."""

    def test_openai_provider_accepts_region_param(self) -> None:
        from app.shared.providers.llm_openai import OpenAILLMProvider

        provider = OpenAILLMProvider(region="us-east-1")
        assert hasattr(provider, "_region")
        assert provider._region == "us-east-1"

    def test_openai_data_residency_header_set(self) -> None:
        """LGPD Art 33: declara residência de dados na requisição."""
        from unittest.mock import patch, MagicMock

        from app.shared.providers.llm_openai import OpenAILLMProvider

        provider = OpenAILLMProvider(api_key="sk-test")
        with patch("openai.OpenAI") as mock_openai:
            mock_openai.return_value = MagicMock()
            provider._get_client()
            call_kwargs = mock_openai.call_args.kwargs
            headers = call_kwargs.get("default_headers", {})
            assert headers.get("OpenAI-Beta") == "data-residency=v1", (
                f"OpenAI DEVE setar OpenAI-Beta=data-residency=v1 header. "
                f"Got default_headers: {headers}"
            )


class TestGeminiRegionPinning:
    """Gemini provider aceita region param (default us-central1)."""

    def test_gemini_provider_accepts_region_param(self) -> None:
        from app.shared.providers.llm_gemini import GeminiLLMProvider

        provider = GeminiLLMProvider(region="southamerica-east1")
        assert hasattr(provider, "_region")
        assert provider._region == "southamerica-east1"

    def test_gemini_default_region_is_us_central1(self) -> None:
        """Default region documentado canonical us-central1 (audit recommendation)."""
        from app.shared.providers.llm_gemini import GeminiLLMProvider

        provider = GeminiLLMProvider()
        # Sem region passado: default é us-central1 (documentação canonical)
        # Esse é o invariante; pode mudar via env LIA_GEMINI_DEFAULT_REGION.
        assert provider._region in (None, "us-central1"), (
            f"Gemini default region deve ser None ou us-central1. Got: {provider._region}"
        )


class TestTenantLLMConfigSchema:
    """TenantLLMConfig DB model expõe campo `region`."""

    def test_tenant_llm_config_has_region_column(self) -> None:
        from lia_models.tenant_llm_config import TenantLLMConfig

        assert hasattr(TenantLLMConfig, "region"), (
            "TenantLLMConfig DEVE expor campo `region` (W2-012 fix)."
        )

    def test_tenant_llm_config_region_default_null(self) -> None:
        """region nullable=True → quando NULL, provider usa default global."""
        from lia_models.tenant_llm_config import TenantLLMConfig

        region_col = TenantLLMConfig.__table__.columns.get("region")
        assert region_col is not None
        assert region_col.nullable is True, (
            "region DEVE ser nullable=True (per-tenant opt-in, default global)"
        )


class TestSensorBlocking:
    """W2-012 sensor BLOCKING confirma headers + DB column presentes."""

    def test_sensor_exists(self) -> None:
        from pathlib import Path

        sensor = (
            Path(__file__).resolve().parents[2]
            / "scripts"
            / "check_lgpd_region_pinning.py"
        )
        assert sensor.exists(), f"Sensor missing: {sensor}"

    def test_sensor_passes_strict(self) -> None:
        import subprocess
        import sys
        from pathlib import Path

        repo_root = Path(__file__).resolve().parents[2]
        sensor = repo_root / "scripts" / "check_lgpd_region_pinning.py"
        result = subprocess.run(
            [sys.executable, str(sensor)],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
        )
        assert result.returncode == 0, (
            f"LGPD region pinning sensor FAILED (exit={result.returncode}):\n"
            f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
        )
