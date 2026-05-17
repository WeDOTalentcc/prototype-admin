"""Task #1161 — Bug A sentinel.

Garante que ``_patch_anthropic`` em ``app/shared/llm_bootstrap.py`` injeta
``base_url`` no SDK ``anthropic.Anthropic`` SEMPRE que
``AI_INTEGRATIONS_ANTHROPIC_BASE_URL`` está setada — inclusive quando o
callsite passou ``api_key`` explícito (caso real do ``ChatAnthropic`` do
LangChain, que constrói o cliente subjacente com ``Anthropic(api_key=tenant_key)``
e antes do fix bypassava o proxy modelfarm → 401 em dev/staging).

Sentinela offline: usa monkeypatch de env vars + ``anthropic.Anthropic.__init__``
para registrar kwargs sem fazer HTTP. Não depende de rede, DB ou Redis.
"""
from __future__ import annotations

import os
from unittest import mock

import pytest


@pytest.fixture(autouse=True)
def _reset_anthropic_patch():
    """Recarrega o SDK anthropic a cada teste para desfazer o monkeypatch."""
    import importlib
    import anthropic

    orig_init = anthropic.Anthropic.__init__
    orig_async_init = anthropic.AsyncAnthropic.__init__
    yield
    anthropic.Anthropic.__init__ = orig_init
    anthropic.AsyncAnthropic.__init__ = orig_async_init
    importlib.reload(anthropic)


def _apply_patch(monkeypatch, base_url: str | None, default_key: str | None = "fallback-key"):
    if base_url is not None:
        monkeypatch.setenv("AI_INTEGRATIONS_ANTHROPIC_BASE_URL", base_url)
    else:
        monkeypatch.delenv("AI_INTEGRATIONS_ANTHROPIC_BASE_URL", raising=False)
    if default_key is not None:
        monkeypatch.setenv("AI_INTEGRATIONS_ANTHROPIC_API_KEY", default_key)
    else:
        monkeypatch.delenv("AI_INTEGRATIONS_ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from app.shared import llm_bootstrap
    llm_bootstrap._patch_anthropic()


def test_base_url_injected_when_caller_passes_explicit_api_key(monkeypatch):
    """O caso real do bug: ChatAnthropic(api_key=...) → SDK não recebia base_url."""
    proxy_url = "https://modelfarm.local/anthropic"
    _apply_patch(monkeypatch, base_url=proxy_url)

    import anthropic
    captured: dict = {}

    real_orig = anthropic.Anthropic.__init__

    def _spy(self, *args, **kwargs):
        captured.update(kwargs)
        # Não chama __init__ real (precisa URL válida/rede). O patch já rodou
        # _inject_anthropic_env antes da chamada original.
        self.api_key = kwargs.get("api_key")
        self.base_url = kwargs.get("base_url")

    monkeypatch.setattr(anthropic.Anthropic, "__init__", _spy)
    # Re-aplica o patch DEPOIS do spy para que _inject_anthropic_env rode
    _apply_patch(monkeypatch, base_url=proxy_url)

    anthropic.Anthropic(api_key="tenant-explicit-key")

    assert captured.get("api_key") == "tenant-explicit-key", (
        "Patch não pode sobrescrever api_key quando o callsite passou explícito"
    )
    assert captured.get("base_url") == proxy_url, (
        "Bug A regression: base_url do proxy modelfarm DEVE ser injetado mesmo "
        "quando api_key foi passado explícito (ChatAnthropic callsite)."
    )


def test_base_url_injected_when_caller_passes_nothing(monkeypatch):
    """Caminho original já cobrado — mantém regressão dupla."""
    proxy_url = "https://modelfarm.local/anthropic"
    _apply_patch(monkeypatch, base_url=proxy_url)

    import anthropic
    captured: dict = {}

    def _spy(self, *args, **kwargs):
        captured.update(kwargs)
        self.api_key = kwargs.get("api_key")
        self.base_url = kwargs.get("base_url")

    monkeypatch.setattr(anthropic.Anthropic, "__init__", _spy)
    _apply_patch(monkeypatch, base_url=proxy_url)

    anthropic.Anthropic()

    assert captured.get("api_key") == "fallback-key"
    assert captured.get("base_url") == proxy_url


def test_base_url_noop_when_env_unset(monkeypatch):
    """Produção (sem env var) → não injeta base_url, deixa SDK usar default."""
    _apply_patch(monkeypatch, base_url=None)

    import anthropic
    captured: dict = {}

    def _spy(self, *args, **kwargs):
        # Captura kwargs sem tocar nos setters do SDK Anthropic — atribuir
        # ``self.base_url = None`` dispara TypeError no setter de URL real.
        captured.update(kwargs)

    monkeypatch.setattr(anthropic.Anthropic, "__init__", _spy)
    _apply_patch(monkeypatch, base_url=None)

    anthropic.Anthropic(api_key="prod-key")

    assert captured.get("api_key") == "prod-key"
    assert "base_url" not in captured or captured.get("base_url") is None, (
        "Sem AI_INTEGRATIONS_ANTHROPIC_BASE_URL, o patch NÃO deve injetar "
        "base_url (rota production usa default da Anthropic)"
    )


def test_inject_helper_uses_unconditional_base_url():
    """AST assertion: ``_inject_anthropic_env`` injeta ``base_url`` fora do
    bloco ``if 'api_key' not in kwargs`` — i.e., a injeção é incondicional
    em relação à presença de api_key."""
    import ast
    import inspect
    from app.shared import llm_bootstrap

    src = inspect.getsource(llm_bootstrap._patch_anthropic)
    tree = ast.parse(src)

    inject_fn = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "_inject_anthropic_env":
            inject_fn = node
            break
    assert inject_fn is not None, "_inject_anthropic_env helper precisa existir"

    # Encontra o sub-statement que faz kwargs['base_url'] = base_url
    base_url_assign = None
    for stmt in inject_fn.body:
        if isinstance(stmt, ast.If):
            test_src = ast.unparse(stmt.test)
            if "base_url" in test_src and "api_key" not in test_src:
                base_url_assign = stmt
                break

    assert base_url_assign is not None, (
        "Bug A regression: a injeção de base_url em _inject_anthropic_env "
        "DEVE estar em um bloco `if` cuja condição menciona apenas base_url, "
        "não estar aninhada dentro de `if 'api_key' not in kwargs`."
    )
