"""W2-011 · TDD tests · DeepSeek provider opt-in canonical wire.

Verifica:
1. DeepSeekLLMProvider class importável + canonical interface.
2. LLMProviderFactory registra "deepseek".
3. /test endpoint aceita provider="deepseek".
4. /providers endpoint inclui deepseek com models + opt_in_only flag.
5. Migration 182 inseriu master template em integration_catalog_entries.
6. Circuit breaker DEEPSEEK_CIRCUIT existe.
7. AI_PROVIDER_IDS no frontend inclui "deepseek".

Skip se sem DATABASE_URL (testes integração precisam Postgres real).
Sensor anti-regressão: scripts/check_deepseek_provider_wired.py
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import pytest


def _get_async_database_url():
    from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

    url = os.environ.get("DATABASE_URL", "")
    if not url:
        return None
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and "+asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if "+asyncpg" not in url:
        return None
    parts = urlsplit(url)
    drop = {"sslmode", "sslrootcert", "sslcert", "sslkey", "channel_binding"}
    new_qs = [(k, v) for k, v in parse_qsl(parts.query) if k not in drop]
    url = urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urlencode(new_qs), parts.fragment)
    )
    return url


def test_provider_class_importable():
    """W2-011 · DeepSeekLLMProvider deve ser importável + ABC interface."""
    from app.shared.providers.llm_deepseek import DeepSeekLLMProvider
    from app.shared.providers.llm_provider import LLMProviderABC

    assert issubclass(DeepSeekLLMProvider, LLMProviderABC)
    p = DeepSeekLLMProvider(api_key="test", region=None)
    assert p.provider_name == "deepseek"
    assert p.default_model == "deepseek-chat"


def test_provider_init_accepts_region():
    """W2-011 · constructor canonical (api_key, region) — uniformity W2-012-B."""
    from app.shared.providers.llm_deepseek import DeepSeekLLMProvider

    p = DeepSeekLLMProvider(api_key="test", region="any-region")
    # Region armazenado mesmo que DeepSeek não suporte (uniformity)
    assert p._region == "any-region"


def test_factory_registry_has_deepseek():
    """W2-011 · LLMProviderFactory deve listar 'deepseek'."""
    from app.shared.providers.llm_factory import LLMProviderFactory

    assert "deepseek" in LLMProviderFactory.available_providers()


def test_factory_instantiates_deepseek():
    """W2-011 · LLMProviderFactory.get('deepseek') retorna DeepSeekLLMProvider."""
    from app.shared.providers.llm_deepseek import DeepSeekLLMProvider
    from app.shared.providers.llm_factory import LLMProviderFactory

    LLMProviderFactory.clear()
    instance = LLMProviderFactory.get("deepseek")
    assert isinstance(instance, DeepSeekLLMProvider)


def test_circuit_breaker_exists():
    """W2-011 · DEEPSEEK_CIRCUIT deve existir em circuit_breaker.py."""
    from app.shared.resilience.circuit_breaker import DEEPSEEK_CIRCUIT

    assert DEEPSEEK_CIRCUIT is not None
    assert DEEPSEEK_CIRCUIT.name == "deepseek"


def test_circuit_breaker_in_provider_map():
    """W2-011 · DEEPSEEK_CIRCUIT mapeado para nome 'deepseek' no dict."""
    # Smoke check via source text (não temos getter público)
    src = (
        Path(__file__).resolve().parents[2]
        / "app"
        / "shared"
        / "resilience"
        / "circuit_breaker.py"
    ).read_text()
    assert '"deepseek": DEEPSEEK_CIRCUIT' in src


def test_llm_config_test_endpoint_branch():
    """W2-011 · /test endpoint deve ter elif request.provider == 'deepseek'."""
    src = (
        Path(__file__).resolve().parents[2]
        / "app"
        / "api"
        / "v1"
        / "llm_config.py"
    ).read_text()
    assert 'elif request.provider == "deepseek":' in src
    assert 'base_url="https://api.deepseek.com/v1"' in src


def test_llm_config_providers_endpoint_lists_deepseek():
    """W2-011 · /providers endpoint deve listar deepseek com models + opt_in_only."""
    src = (
        Path(__file__).resolve().parents[2]
        / "app"
        / "api"
        / "v1"
        / "llm_config.py"
    ).read_text()
    assert '"id": "deepseek"' in src
    assert '"deepseek-chat"' in src
    assert '"deepseek-reasoner"' in src
    assert '"opt_in_only": True' in src


@pytest.mark.asyncio
async def test_master_template_seeded_in_db():
    """W2-011 · Migration 182 inseriu master template DeepSeek."""
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    url = _get_async_database_url()
    if not url:
        pytest.skip("DATABASE_URL not available")

    engine = create_async_engine(url, future=True)
    sm = async_sessionmaker(engine, expire_on_commit=False)
    async with sm() as session:
        result = await session.execute(
            text(
                "SELECT data FROM integration_catalog_entries "
                "WHERE is_master_template=true AND data->>'provider' = 'deepseek'"
            )
        )
        row = result.first()
        assert row is not None, "Migration 182 deveria ter inserido master template DeepSeek"
        data = row[0]
        if isinstance(data, str):
            import json
            data = json.loads(data)
        assert data["provider"] == "deepseek"
        assert data["category"] == "ai_models"
        assert "DEEPSEEK_API_KEY" in data["metadata"]["config_fields"]
        assert data["metadata"]["opt_in_only"] is True
    await engine.dispose()


def test_frontend_ai_provider_ids_includes_deepseek():
    """W2-011 · plataforma-lia AI_PROVIDER_IDS deve incluir 'deepseek'."""
    # Encontra path do plataforma-lia relativo ao test
    repo_root = Path(__file__).resolve().parents[3]
    candidate = repo_root / "plataforma-lia" / "src" / "components" / "settings" / "integrations" / "IntegrationDetailDrawer.tsx"
    if not candidate.exists():
        pytest.skip(f"plataforma-lia path not found: {candidate}")
    src = candidate.read_text(encoding="utf-8")
    # Match AI_PROVIDER_IDS array literal with deepseek
    pattern = re.compile(r'AI_PROVIDER_IDS\s*=\s*\[[^\]]*"deepseek"[^\]]*\]')
    assert pattern.search(src), "AI_PROVIDER_IDS must include 'deepseek'"


def test_not_in_default_fallback_order():
    """W2-011 · deepseek NÃO deve estar em FALLBACK_ORDER default (opt-in only)."""
    from app.shared.providers.llm_factory import FALLBACK_ORDER

    assert "deepseek" not in FALLBACK_ORDER, (
        "DeepSeek deve ser opt-in only (tenant ativa explicitamente via primary_provider "
        "ou custom fallback_order). NÃO deve estar em FALLBACK_ORDER default."
    )


# --- W2-011 gap P1 fix: cascade router deepseek routing ---


def test_provider_for_model_deepseek_routing():
    """_provider_for_model deve retornar 'deepseek' para modelos deepseek-* (gap P1)."""
    from app.orchestrator.routing.llm_cascade import LLMCascadeRouter

    assert LLMCascadeRouter._provider_for_model("deepseek-chat") == "deepseek"
    assert LLMCascadeRouter._provider_for_model("deepseek-coder") == "deepseek"
    assert LLMCascadeRouter._provider_for_model("deepseek-r1") == "deepseek"
    assert LLMCascadeRouter._provider_for_model("DeepSeek-V3") == "deepseek"


def test_provider_for_model_deepseek_no_regression():
    """Outros providers não devem regredir após adição da branch deepseek."""
    from app.orchestrator.routing.llm_cascade import LLMCascadeRouter

    assert LLMCascadeRouter._provider_for_model("gemini-pro") == "gemini"
    assert LLMCascadeRouter._provider_for_model("gemini-1.5-flash") == "gemini"
    assert LLMCascadeRouter._provider_for_model("gpt-4o") == "openai"
    assert LLMCascadeRouter._provider_for_model("gpt-3.5-turbo") == "openai"
    assert LLMCascadeRouter._provider_for_model("openai-o1") == "openai"
    assert LLMCascadeRouter._provider_for_model("claude-3-opus") == "claude"
    assert LLMCascadeRouter._provider_for_model("claude-3-5-sonnet") == "claude"


def test_llm_provider_literal_includes_deepseek():
    """LLMProvider Literal deve incluir 'deepseek' (type safety W2-011)."""
    import typing
    from app.domains.ai.services.llm import LLMProvider

    args = typing.get_args(LLMProvider)
    assert "deepseek" in args, f"'deepseek' not in LLMProvider: {args}"
    # Providers originais não devem ter sido removidos
    assert "claude" in args
    assert "openai" in args
    assert "gemini" in args
