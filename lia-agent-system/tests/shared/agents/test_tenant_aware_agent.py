"""Unit tests — TenantAwareAgentMixin (T-A canonical infra)."""
from __future__ import annotations

import os
from typing import Any

import pytest

from app.shared.agents.tenant_aware_agent import (
    TenantAwareAgentMixin,
    get_tenant_context_metrics,
    is_tenant_strict_mode,
    reset_tenant_context_metrics,
)
from app.shared.exceptions.tenant_errors import MissingTenantContextError


# ----------------------------------------------------------------------
# Test doubles
# ----------------------------------------------------------------------

class _FakeAgentInput:
    """Minimal AgentInput stand-in (avoids pulling lia_agents_core in unit tests)."""

    def __init__(
        self,
        company_id: str | None = "00000000-0000-4000-a000-000000000001",
        context: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.company_id = company_id  # type: ignore[assignment]
        self.context: dict[str, Any] = context if context is not None else {}
        self.metadata: dict[str, Any] = metadata if metadata is not None else {}
        self.message = "hello"
        self.session_id = "sess-1"
        self.user_id = "user-1"
        self.conversation_history: list = []


class _FakeBase:
    """Stand-in for LangGraphReActBase — captures what got passed."""

    last_input: _FakeAgentInput | None = None

    def _get_system_prompt(self, input: _FakeAgentInput) -> str:  # noqa: A002
        type(self).last_input = input
        return f"PROMPT|snippet={input.context.get('tenant_context_snippet', '')}"


class _Agent(TenantAwareAgentMixin, _FakeBase):
    domain_name = "wizard"


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _reset_metrics_and_env(monkeypatch):
    reset_tenant_context_metrics()
    monkeypatch.delenv("LIA_AGENT_TENANT_STRICT", raising=False)
    monkeypatch.setenv("APP_ENV", "development")
    yield
    reset_tenant_context_metrics()


# ----------------------------------------------------------------------
# is_tenant_strict_mode
# ----------------------------------------------------------------------

class TestStrictModeFlag:
    def test_default_dev_is_fail_open(self, monkeypatch):
        monkeypatch.setenv("APP_ENV", "development")
        assert is_tenant_strict_mode() is False

    @pytest.mark.parametrize("env", ["production", "prod", "staging", "STAGING"])
    def test_default_prod_like_is_fail_closed(self, monkeypatch, env):
        monkeypatch.setenv("APP_ENV", env)
        assert is_tenant_strict_mode() is True

    @pytest.mark.parametrize("raw", ["1", "true", "TRUE", "yes", "on"])
    def test_explicit_truthy_overrides_env(self, monkeypatch, raw):
        monkeypatch.setenv("APP_ENV", "development")
        monkeypatch.setenv("LIA_AGENT_TENANT_STRICT", raw)
        assert is_tenant_strict_mode() is True

    @pytest.mark.parametrize("raw", ["0", "false", "no", "off"])
    def test_explicit_falsy_overrides_env(self, monkeypatch, raw):
        monkeypatch.setenv("APP_ENV", "production")
        monkeypatch.setenv("LIA_AGENT_TENANT_STRICT", raw)
        assert is_tenant_strict_mode() is False


# ----------------------------------------------------------------------
# _get_system_prompt — fast path: snippet already injected
# ----------------------------------------------------------------------

class TestSystemPromptHook:
    def test_uses_existing_snippet_records_hit(self):
        agent = _Agent()
        inp = _FakeAgentInput(context={"tenant_context_snippet": "Você está atendendo Acme Corp."})
        prompt = agent._get_system_prompt(inp)
        assert "Acme Corp" in prompt
        assert get_tenant_context_metrics()["wizard"]["hit"] == 1

    def test_renders_snippet_from_tenant_context_object(self):
        class _Tctx:
            def to_prompt_snippet(self) -> str:
                return "Você está atendendo Beta Inc."

        agent = _Agent()
        inp = _FakeAgentInput(context={"tenant_context": _Tctx()})
        prompt = agent._get_system_prompt(inp)
        assert "Beta Inc" in prompt
        # snippet foi persistido pro próximo turno
        assert inp.context["tenant_context_snippet"] == "Você está atendendo Beta Inc."
        assert get_tenant_context_metrics()["wizard"]["miss"] == 1

    def test_fail_open_in_dev_returns_empty_snippet(self, monkeypatch):
        monkeypatch.setenv("APP_ENV", "development")
        agent = _Agent()
        inp = _FakeAgentInput(context={})
        prompt = agent._get_system_prompt(inp)
        assert "snippet=" in prompt and "Acme" not in prompt
        assert get_tenant_context_metrics()["wizard"]["fail_open"] == 1

    def test_fail_closed_in_prod_raises_missing_tenant_context(self, monkeypatch):
        monkeypatch.setenv("APP_ENV", "production")
        agent = _Agent()
        inp = _FakeAgentInput(context={})
        with pytest.raises(MissingTenantContextError) as exc:
            agent._get_system_prompt(inp)
        assert exc.value.details["agent"] == "wizard"
        assert exc.value.details["tenant_source"] == "system_prompt_hook"
        assert get_tenant_context_metrics()["wizard"]["fail_closed"] == 1

    def test_strict_override_forces_fail_closed_even_in_dev(self, monkeypatch):
        monkeypatch.setenv("APP_ENV", "development")

        class _StrictAgent(_Agent):
            tenant_strict_override = True

        agent = _StrictAgent()
        inp = _FakeAgentInput(context={})
        with pytest.raises(MissingTenantContextError):
            agent._get_system_prompt(inp)


# ----------------------------------------------------------------------
# _get_tenant_context_snippet — async API
# ----------------------------------------------------------------------

@pytest.mark.asyncio
class TestAsyncSnippet:
    async def test_returns_existing_snippet(self):
        agent = _Agent()
        inp = _FakeAgentInput(context={"tenant_context_snippet": "X"})
        snippet = await agent._get_tenant_context_snippet(inp)
        assert snippet == "X"

    async def test_invalid_company_id_dev_returns_empty(self, monkeypatch):
        monkeypatch.setenv("APP_ENV", "development")
        agent = _Agent()
        inp = _FakeAgentInput(company_id="default", context={})
        snippet = await agent._get_tenant_context_snippet(inp)
        assert snippet == ""
        assert get_tenant_context_metrics()["wizard"]["fail_open"] == 1

    async def test_invalid_company_id_prod_raises(self, monkeypatch):
        monkeypatch.setenv("APP_ENV", "production")
        agent = _Agent()
        inp = _FakeAgentInput(company_id="default", context={})
        with pytest.raises(MissingTenantContextError):
            await agent._get_tenant_context_snippet(inp)


# ----------------------------------------------------------------------
# Metrics
# ----------------------------------------------------------------------

def test_metrics_are_keyed_by_agent_domain_name():
    agent = _Agent()
    inp = _FakeAgentInput(context={"tenant_context_snippet": "X"})
    agent._get_system_prompt(inp)
    snapshot = get_tenant_context_metrics()
    assert "wizard" in snapshot
    assert snapshot["wizard"]["hit"] == 1
    assert snapshot["wizard"]["miss"] == 0


def test_reset_clears_counters():
    agent = _Agent()
    inp = _FakeAgentInput(context={"tenant_context_snippet": "X"})
    agent._get_system_prompt(inp)
    reset_tenant_context_metrics()
    assert get_tenant_context_metrics() == {}


class TestStrictOverrideSafety:
    """T-A R-2: tenant_strict_override só pode FORÇAR strict (True), nunca enfraquecer."""

    def test_override_true_forces_strict_in_dev(self, monkeypatch):
        monkeypatch.setenv("APP_ENV", "development")
        monkeypatch.delenv("LIA_AGENT_TENANT_STRICT", raising=False)

        class _Agent(TenantAwareAgentMixin, _FakeBase):
            domain_name = "force_strict_agent"
            tenant_strict_override = True

        agent = _Agent()
        assert agent._is_strict() is True

    def test_override_none_defers_to_env(self, monkeypatch):
        monkeypatch.setenv("APP_ENV", "production")
        monkeypatch.delenv("LIA_AGENT_TENANT_STRICT", raising=False)

        class _Agent(TenantAwareAgentMixin, _FakeBase):
            domain_name = "defer_agent"
            tenant_strict_override = None

        agent = _Agent()
        assert agent._is_strict() is True  # prod default

    def test_override_false_raises_runtime_error(self, monkeypatch):
        """Bypass silencioso por subclasse é proibido — usar env LIA_AGENT_TENANT_STRICT."""
        monkeypatch.setenv("APP_ENV", "development")

        class _BadAgent(TenantAwareAgentMixin, _FakeBase):
            domain_name = "bad_agent"
            tenant_strict_override = False  # type: ignore[assignment]

        agent = _BadAgent()
        with pytest.raises(RuntimeError) as exc:
            agent._is_strict()
        assert "LIA_AGENT_TENANT_STRICT" in str(exc.value)

    def test_override_truthy_non_true_raises(self, monkeypatch):
        class _WeirdAgent(TenantAwareAgentMixin, _FakeBase):
            domain_name = "weird"
            tenant_strict_override = 1  # type: ignore[assignment]

        agent = _WeirdAgent()
        with pytest.raises(RuntimeError):
            agent._is_strict()
