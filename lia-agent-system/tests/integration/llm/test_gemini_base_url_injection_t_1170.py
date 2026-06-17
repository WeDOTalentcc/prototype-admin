"""Task #1170 — sentinel for the Gemini modelfarm-proxy injection.

Mirrors ``test_anthropic_base_url_injection_t_1164.py``. Guarantees that
``create_tracked_llm`` (the canonical chat-model factory) routes Gemini
calls through ``AI_INTEGRATIONS_GEMINI_BASE_URL`` when that env var is
set, instead of letting the wrapper key from
``AI_INTEGRATIONS_GEMINI_API_KEY`` hit ``generativelanguage.googleapis.com``
directly (which returns ``400 API_KEY_INVALID`` and is what caused the
``jd_enrichment`` node in the wizard graph to fall back to the canned
"qualidade estimada: 20%" reply on every turn).

Offline by design: monkeypatches env vars + ``langchain_google_genai``
constructor to capture kwargs without touching the network.
"""
from __future__ import annotations

import sys
import types

import pytest


@pytest.fixture
def fake_chat_google(monkeypatch):
    """Install a stub for ``langchain_google_genai.ChatGoogleGenerativeAI``.

    The real class pulls in google-api-core / grpc; we only need to verify
    which kwargs the factory passes in.
    """
    captured: dict = {}

    class _Stub:
        def __init__(self, *args, **kwargs):
            captured.clear()
            captured.update(kwargs)
            captured["_args"] = args

    module = types.ModuleType("langchain_google_genai")
    module.ChatGoogleGenerativeAI = _Stub
    monkeypatch.setitem(sys.modules, "langchain_google_genai", module)
    return captured


def _force_gemini_chain(monkeypatch):
    """Force ``create_tracked_llm`` down the Gemini branch deterministically."""
    from app.shared.providers import llm_factory

    def _fake_chain(_tenant):
        return "gemini", ["gemini"], {}

    monkeypatch.setattr(llm_factory, "_resolve_provider_chain", _fake_chain)


def test_create_tracked_llm_injects_gemini_base_url(monkeypatch, fake_chat_google):
    """Bug #1170 root cause: ``AI_INTEGRATIONS_GEMINI_BASE_URL`` must reach
    ``ChatGoogleGenerativeAI`` so the wrapper key hits the modelfarm proxy
    instead of api.googleapis.com."""
    monkeypatch.setenv("AI_INTEGRATIONS_GEMINI_API_KEY", "wrapper-key")
    monkeypatch.setenv(
        "AI_INTEGRATIONS_GEMINI_BASE_URL", "http://localhost:1106/modelfarm/gemini"
    )
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    _force_gemini_chain(monkeypatch)

    from app.shared.providers.llm_factory import create_tracked_llm

    create_tracked_llm(temperature=0.3, service_name="JdEnrichmentService")

    assert fake_chat_google.get("google_api_key") == "wrapper-key", (
        "Factory must pass the wrapper key when GEMINI_API_KEY/GOOGLE_API_KEY "
        "are unset."
    )
    assert (
        fake_chat_google.get("base_url") == "http://localhost:1106/modelfarm/gemini"
    ), (
        "Bug #1170 regression: AI_INTEGRATIONS_GEMINI_BASE_URL must be passed "
        "to ChatGoogleGenerativeAI so the wrapper key is sent to the proxy "
        "instead of generativelanguage.googleapis.com."
    )
    assert fake_chat_google.get("transport") == "rest", (
        "Bug #1170 regression: when the modelfarm proxy URL is set the factory "
        "must pin transport='rest' on ChatGoogleGenerativeAI — the proxy is "
        "HTTP only and the default gRPC transport hangs against it."
    )


def test_wrapper_key_wins_over_stale_gemini_key_when_proxy_is_set(monkeypatch):
    """If the proxy URL is set, the wrapper key must beat a stale
    ``GEMINI_API_KEY`` from a previous direct-Google setup. Otherwise the
    factory ends up sending a real Google key to the proxy (or worse, a
    proxy key to Google) and both endpoints reject it."""
    monkeypatch.setenv("GEMINI_API_KEY", "stale-direct-google-key")
    monkeypatch.setenv("AI_INTEGRATIONS_GEMINI_API_KEY", "wrapper-key")
    monkeypatch.setenv(
        "AI_INTEGRATIONS_GEMINI_BASE_URL", "http://localhost:1106/modelfarm/gemini"
    )

    from app.shared.providers.llm_factory import _resolve_provider_api_key

    assert _resolve_provider_api_key("gemini") == "wrapper-key"


def test_direct_google_key_wins_when_proxy_is_unset(monkeypatch):
    """No proxy configured → keep legacy behaviour (direct GEMINI_API_KEY)."""
    monkeypatch.setenv("GEMINI_API_KEY", "direct-google-key")
    monkeypatch.setenv("AI_INTEGRATIONS_GEMINI_API_KEY", "wrapper-key")
    monkeypatch.delenv("AI_INTEGRATIONS_GEMINI_BASE_URL", raising=False)

    from app.shared.providers.llm_factory import _resolve_provider_api_key

    assert _resolve_provider_api_key("gemini") == "direct-google-key"


def test_resolve_provider_base_url_helper_exists():
    """Helper must exist + return None when no proxy is configured."""
    from app.shared.providers.llm_factory import _resolve_provider_base_url

    assert callable(_resolve_provider_base_url)


def test_create_tracked_llm_gemini_branch_calls_base_url_resolver():
    """AST guard: the Gemini branch in ``create_tracked_llm`` must consult
    ``_resolve_provider_base_url`` so nobody silently drops the proxy URL
    injection while refactoring the factory."""
    import ast
    import inspect

    from app.shared.providers import llm_factory

    src = inspect.getsource(llm_factory.create_tracked_llm)
    tree = ast.parse(src)
    text = ast.unparse(tree)

    assert "_resolve_provider_base_url" in text, (
        "Bug #1170 regression: create_tracked_llm must call "
        "_resolve_provider_base_url('gemini') to forward "
        "AI_INTEGRATIONS_GEMINI_BASE_URL into ChatGoogleGenerativeAI."
    )
