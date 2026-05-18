"""Centralized Anthropic client factory (Task #1166).

Single canonical entry point for constructing Anthropic SDK / LangChain
``ChatAnthropic`` clients. Every call routes through the
``install_llm_guards()`` monkey-patches in
``app.shared.llm_bootstrap`` (PII strip, audit log, tenant key + proxy
``base_url`` injection — see Task #1164 Bug D).

Why a helper at all when the bootstrap already monkey-patches the
constructors?
  - The monkey-patch only covers the three SDK entry points
    ``anthropic.Anthropic``, ``anthropic.AsyncAnthropic`` and
    ``langchain_anthropic.ChatAnthropic``. Any future code that
    bypasses those (e.g. raw ``httpx``, a new SDK shape, or a forked
    LangChain wrapper) silently bypasses the proxy too.
  - Centralizing construction here lets us add an AST sentinel
    (``tests/integration/llm/test_anthropic_centralized_t_1166.py``)
    that forbids direct ``ChatAnthropic(...)`` / ``Anthropic(...)`` /
    ``AsyncAnthropic(...)`` construction inside
    ``app/domains/job_creation/``. New callsites in the wizard domain
    are forced to go through this module, where the proxy contract is
    documented and tested.

The helper itself does NOT re-implement the bootstrap contract — it
relies on the monkey-patches. It exists primarily as a stable seam:
one place to evolve the contract (e.g. attach LangSmith metadata,
swap to ``init_chat_model``) without grepping the wizard graph.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.shared.llm_models import CANONICAL_HAIKU_MODEL

if TYPE_CHECKING:  # pragma: no cover — typing only
    from anthropic import Anthropic as _Anthropic
    from anthropic import AsyncAnthropic as _AsyncAnthropic
    from langchain_anthropic import ChatAnthropic as _ChatAnthropic


def get_chat_anthropic(
    *,
    model: str | None = None,
    api_key: str | None = None,
    **kwargs: Any,
) -> "_ChatAnthropic":
    """Build a ``langchain_anthropic.ChatAnthropic`` via the canonical seam.

    The ``llm_bootstrap`` monkey-patch on ``anthropic.Anthropic`` (which
    ``ChatAnthropic`` instantiates internally) takes care of injecting
    ``AI_INTEGRATIONS_ANTHROPIC_BASE_URL`` over LangChain's default
    ``"https://api.anthropic.com"`` (Task #1164 Bug D).

    Args:
        model: LangChain model identifier. Defaults to the canonical
            Haiku model when omitted so callers don't accidentally hit
            an unconfigured default.
        api_key: optional explicit tenant key. When omitted the
            bootstrap pulls from ``AI_INTEGRATIONS_ANTHROPIC_API_KEY`` /
            ``ANTHROPIC_API_KEY``.
        **kwargs: forwarded verbatim to ``ChatAnthropic``.
    """
    from langchain_anthropic import ChatAnthropic

    if model is None:
        model = CANONICAL_HAIKU_MODEL
    if api_key is not None:
        kwargs.setdefault("api_key", api_key)
    kwargs.setdefault("model", model)
    return ChatAnthropic(**kwargs)


def get_anthropic_client(
    *,
    api_key: str | None = None,
    **kwargs: Any,
) -> "_Anthropic":
    """Build a sync ``anthropic.Anthropic`` client via the canonical seam."""
    from anthropic import Anthropic

    if api_key is not None:
        kwargs.setdefault("api_key", api_key)
    return Anthropic(**kwargs)


def get_async_anthropic_client(
    *,
    api_key: str | None = None,
    **kwargs: Any,
) -> "_AsyncAnthropic":
    """Build an async ``anthropic.AsyncAnthropic`` client via the canonical seam."""
    from anthropic import AsyncAnthropic

    if api_key is not None:
        kwargs.setdefault("api_key", api_key)
    return AsyncAnthropic(**kwargs)


__all__ = [
    "get_chat_anthropic",
    "get_anthropic_client",
    "get_async_anthropic_client",
]
