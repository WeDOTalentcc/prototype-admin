"""Task #1164 — Bug D sentinel (extends Task #1161 Bug A).

Garante que ``_inject_anthropic_env`` em ``app/shared/llm_bootstrap.py``
**SOBRESCREVE** o ``base_url`` default que ``langchain_anthropic.ChatAnthropic``
injeta automaticamente nos kwargs do SDK Anthropic.

Root cause (Task #1164):
    ``ChatAnthropic._client_params`` sempre faz
    ``base_url=self.anthropic_api_url``, com o default vindo de
    ``from_env(["ANTHROPIC_API_URL", "ANTHROPIC_BASE_URL"], default="https://api.anthropic.com")``.
    Quando o env var não está setado, kwargs chega no patch do SDK com
    ``base_url="https://api.anthropic.com"`` — a fix de Task #1161 Bug A
    (``if base_url and "base_url" not in kwargs:``) pulava a injeção e
    o cliente batia direto na API pública (401 com a wrapper key do
    modelfarm).

Sentinela offline: usa monkeypatch de env vars + ``anthropic.Anthropic.__init__``
para registrar kwargs sem fazer HTTP. Não depende de rede, DB ou Redis.
"""
from __future__ import annotations

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


def _apply_patch(monkeypatch, base_url: str | None, default_key: str = "fallback-key"):
    if base_url is not None:
        monkeypatch.setenv("AI_INTEGRATIONS_ANTHROPIC_BASE_URL", base_url)
    else:
        monkeypatch.delenv("AI_INTEGRATIONS_ANTHROPIC_BASE_URL", raising=False)
    monkeypatch.setenv("AI_INTEGRATIONS_ANTHROPIC_API_KEY", default_key)
    from app.shared import llm_bootstrap
    llm_bootstrap._patch_anthropic()


def test_base_url_overridden_when_kwargs_has_anthropic_default(monkeypatch):
    """Bug D real case: ``ChatAnthropic`` passa ``base_url="https://api.anthropic.com"``
    explícito → o patch DEVE sobrescrever pelo proxy do modelfarm."""
    proxy_url = "http://localhost:1106/modelfarm/anthropic"
    _apply_patch(monkeypatch, base_url=proxy_url)

    import anthropic
    captured: dict = {}

    def _spy(self, *args, **kwargs):
        captured.update(kwargs)
        self.api_key = kwargs.get("api_key")

    monkeypatch.setattr(anthropic.Anthropic, "__init__", _spy)
    _apply_patch(monkeypatch, base_url=proxy_url)

    # Simula a chamada do ChatAnthropic._client (LangChain wrapper):
    # kwargs já vêm com base_url="https://api.anthropic.com" populado.
    anthropic.Anthropic(api_key="tenant-key", base_url="https://api.anthropic.com")

    assert captured.get("api_key") == "tenant-key", (
        "Patch não pode sobrescrever api_key quando o callsite passou explícito"
    )
    assert captured.get("base_url") == proxy_url, (
        "Bug D regression: base_url do proxy DEVE substituir o default "
        "'https://api.anthropic.com' que ChatAnthropic auto-popula em kwargs."
    )


def test_base_url_overridden_when_kwargs_has_anthropic_default_with_trailing_slash(monkeypatch):
    """Trailing slash variant — match deve ser robusto."""
    proxy_url = "http://localhost:1106/modelfarm/anthropic"
    _apply_patch(monkeypatch, base_url=proxy_url)

    import anthropic
    captured: dict = {}

    def _spy(self, *args, **kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(anthropic.Anthropic, "__init__", _spy)
    _apply_patch(monkeypatch, base_url=proxy_url)

    anthropic.Anthropic(base_url="https://api.anthropic.com/")

    assert captured.get("base_url") == proxy_url


def test_explicit_non_default_base_url_is_preserved(monkeypatch):
    """Se o caller passa um base_url DIFERENTE do default Anthropic, respeita."""
    proxy_url = "http://localhost:1106/modelfarm/anthropic"
    _apply_patch(monkeypatch, base_url=proxy_url)

    import anthropic
    captured: dict = {}

    def _spy(self, *args, **kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(anthropic.Anthropic, "__init__", _spy)
    _apply_patch(monkeypatch, base_url=proxy_url)

    explicit = "https://my-custom-anthropic-mirror.example.com"
    anthropic.Anthropic(base_url=explicit)

    assert captured.get("base_url") == explicit, (
        "Caller passou base_url explícito não-default → patch NÃO deve sobrescrever."
    )


def test_helper_detects_default_anthropic_base_urls():
    """Cobertura runtime do helper ``_is_default_anthropic_base_url``."""
    from app.shared.llm_bootstrap import _is_default_anthropic_base_url

    assert _is_default_anthropic_base_url("https://api.anthropic.com") is True
    assert _is_default_anthropic_base_url("https://api.anthropic.com/") is True
    assert _is_default_anthropic_base_url("http://localhost:1106/modelfarm/anthropic") is False
    assert _is_default_anthropic_base_url("https://my-mirror.example.com") is False
    assert _is_default_anthropic_base_url(None) is False
    assert _is_default_anthropic_base_url("") is False


def test_inject_helper_overrides_default_anthropic_base_url():
    """AST assertion: ``_inject_anthropic_env`` consulta
    ``_is_default_anthropic_base_url`` para decidir override.

    Garante que ninguém regenere o bug removendo a verificação de
    default-URL e voltando ao ``"base_url" not in kwargs`` puro.
    """
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

    body_src = ast.unparse(inject_fn)
    assert "_is_default_anthropic_base_url" in body_src, (
        "Bug D regression: _inject_anthropic_env DEVE chamar "
        "_is_default_anthropic_base_url para detectar o default que "
        "ChatAnthropic auto-popula em kwargs e poder sobrescrevê-lo."
    )
