"""
Q4.1 Sandbox dry-run — contract/unit tests for CustomAgentRuntime dry_run mode.

Pins canonical behavior (audit Phase 2.5 Q4, 2026-05-29):

* execute() accepts ``dry_run`` keyword param (default False) — signature contract.
* In dry_run, WRITE tools (PLATFORM_TOOLS_REGISTRY[name]=="write") are intercepted:
  the real side-effecting fn is NOT called; a mock success + "WOULD execute" is
  returned and recorded in the would-do buffer.
* In dry_run, READ tools run normally (real data feeds real reasoning).
* When NOT dry_run, write tools execute the real fn (regression sentinel).
* Multi-tenancy: company_id from ContextVar is injected into tool kwargs even in
  dry_run (the read tools still need it; fail-closed not weakened).
* _state_to_output surfaces metadata["dry_run"] + metadata["would_do_actions"].

Run: pytest tests/api/test_agent_dry_run.py -o addopts="" -v
"""
from __future__ import annotations

import inspect
from unittest.mock import MagicMock

import pytest

from app.domains.agent_studio import custom_agent_runtime as car
from app.domains.agent_studio.custom_agent_runtime import (
    CustomAgentRuntime,
    _DRY_RUN,
    _DRY_RUN_WOULD_DO,
)
from lia_agents_core.tool_adapter import ToolContract


# ----------------------------------------------------------------------------
# Helpers — fake tools + runtime that loads ONLY our injected tools
# ----------------------------------------------------------------------------

# Module-level call recorders so the fake tool fns can register real invocation.
_REAL_SEND_CALLS: list = []
_REAL_SEARCH_CALLS: list = []


async def _fake_send_email(**kwargs):
    """Simulates a side-effecting WRITE tool (sends email for real)."""
    _REAL_SEND_CALLS.append(kwargs)
    return {"success": True, "sent": True}


async def _fake_search_candidates(**kwargs):
    """Simulates a READ tool (no side-effect)."""
    _REAL_SEARCH_CALLS.append(kwargs)
    return {"success": True, "candidates": ["cand-1", "cand-2"]}


def _make_send_contract() -> ToolContract:
    return ToolContract(
        name="send_email",
        description="Send an email to a candidate",
        function=_fake_send_email,
        side_effects=["send"],
    )


def _make_search_contract() -> ToolContract:
    return ToolContract(
        name="search_candidates",
        description="Search candidates",
        function=_fake_search_candidates,
        side_effects=["read"],
    )


def _make_runtime(allowed=("send_email", "search_candidates")) -> CustomAgentRuntime:
    rt = CustomAgentRuntime(
        agent_id="agent-dry-1",
        agent_name="DryRunTestAgent",
        system_prompt="You are a helpful assistant.",
        allowed_tools=list(allowed),
        domain="custom",
        company_id="company-uuid-1",
    )
    return rt


@pytest.fixture(autouse=True)
def _reset_state(monkeypatch):
    """Reset recorders + force _get_tools to load ONLY our injected fakes.

    Patches the autonomous/domain loaders to return nothing and injects the
    fakes via _get_all_enhanced_tools so we exercise the canonical
    _tenant_safe_wrapper path without pulling the real registries.
    """
    # Runtime __init__ initializes a langgraph checkpointer; in production-like
    # APP_ENV the lazy get_checkpointer() raises (needs async lifespan init).
    # checkpointer.py reads lia_config settings.APP_ENV (cached at import) — env
    # var alone is too late. Patch the settings attribute so MemorySaver fallback
    # is used. These are pure-unit tests of tool interception, no graph run.
    from lia_config.config import settings as _lia_settings
    monkeypatch.setattr(_lia_settings, "APP_ENV", "test", raising=False)
    _REAL_SEND_CALLS.clear()
    _REAL_SEARCH_CALLS.clear()

    # Avoid loading the (heavy/real) autonomous + domain tool pools.
    monkeypatch.setattr(
        CustomAgentRuntime,
        "_get_all_enhanced_tools",
        lambda self: [_make_send_contract(), _make_search_contract()],
        raising=True,
    )
    # Neutralize the autonomous registry import so all_tools stays empty.
    import sys
    fake_autonomous = MagicMock()
    fake_autonomous.get_autonomous_tools = lambda: []
    monkeypatch.setitem(
        sys.modules,
        "app.domains.autonomous.agents.autonomous_tool_registry",
        fake_autonomous,
    )
    yield


def _extract_coroutine(structured_tool):
    """Pull the async callable out of a LangChain StructuredTool."""
    # StructuredTool stores async impl on .coroutine; sync on .func.
    return getattr(structured_tool, "coroutine", None) or getattr(structured_tool, "func", None)


def _get_wrapped(runtime, tool_name):
    tools = runtime._get_tools()
    for t in tools:
        if getattr(t, "name", "") == tool_name:
            return _extract_coroutine(t)
    raise AssertionError(f"tool {tool_name} not found in _get_tools()")


# ----------------------------------------------------------------------------
# Signature contract
# ----------------------------------------------------------------------------

class TestSignature:
    def test_execute_accepts_dry_run_param(self):
        sig = inspect.signature(CustomAgentRuntime.execute)
        assert "dry_run" in sig.parameters
        assert sig.parameters["dry_run"].default is False

    def test_contextvars_exist_and_default_safe(self):
        # Fail-closed defaults: dry_run off, no buffer.
        assert _DRY_RUN.get(False) is False
        assert _DRY_RUN_WOULD_DO.get(None) is None


# ----------------------------------------------------------------------------
# Interception behavior
# ----------------------------------------------------------------------------

class TestWriteToolInterception:
    @pytest.mark.asyncio
    async def test_write_tool_intercepted_in_dry_run(self):
        rt = _make_runtime()
        send = _get_wrapped(rt, "send_email")

        _cid = car._CURRENT_COMPANY_ID.set("company-uuid-1")
        _dr = _DRY_RUN.set(True)
        buf: list = []
        _wd = _DRY_RUN_WOULD_DO.set(buf)
        try:
            result = await send(candidate_id="cand-1", body="Olá!", confirm=True)
        finally:
            car._CURRENT_COMPANY_ID.reset(_cid)
            _DRY_RUN.reset(_dr)
            _DRY_RUN_WOULD_DO.reset(_wd)

        # Real side-effect NOT executed.
        assert _REAL_SEND_CALLS == [], "send_email real fn must NOT run in dry_run"
        # Mock result flags simulation.
        assert isinstance(result, dict)
        assert result.get("dry_run") is True
        assert "SIMULAÇÃO" in result.get("message", "")
        # Would-do recorded with sanitized args (no confirm/company_id).
        assert len(buf) == 1
        assert buf[0]["tool"] == "_fake_send_email" or buf[0]["tool"].endswith("send_email")
        assert "candidate_id" in buf[0]["args"]
        assert "confirm" not in buf[0]["args"]
        assert "company_id" not in buf[0]["args"]

    @pytest.mark.asyncio
    async def test_write_tool_executes_when_not_dry_run(self):
        rt = _make_runtime()
        send = _get_wrapped(rt, "send_email")

        _cid = car._CURRENT_COMPANY_ID.set("company-uuid-1")
        try:
            # confirm=True passes the AUD-4 HITL gate so the real fn runs.
            result = await send(candidate_id="cand-1", body="Olá!", confirm=True)
        finally:
            car._CURRENT_COMPANY_ID.reset(_cid)

        assert len(_REAL_SEND_CALLS) == 1, "real send must run when not dry_run"
        assert result.get("sent") is True

    @pytest.mark.asyncio
    async def test_read_tool_runs_in_dry_run(self):
        rt = _make_runtime()
        search = _get_wrapped(rt, "search_candidates")

        _cid = car._CURRENT_COMPANY_ID.set("company-uuid-1")
        _dr = _DRY_RUN.set(True)
        buf: list = []
        _wd = _DRY_RUN_WOULD_DO.set(buf)
        try:
            result = await search(query="dev")
        finally:
            car._CURRENT_COMPANY_ID.reset(_cid)
            _DRY_RUN.reset(_dr)
            _DRY_RUN_WOULD_DO.reset(_wd)

        # Read tool ran for real (recruiter wants real reasoning over real data).
        assert len(_REAL_SEARCH_CALLS) == 1
        assert "candidates" in result
        # Read tools never appear in would-do.
        assert buf == []

    @pytest.mark.asyncio
    async def test_company_id_injected_even_in_dry_run(self):
        """Multi-tenancy fail-closed: read tools still get company_id from CtxVar."""
        rt = _make_runtime()
        search = _get_wrapped(rt, "search_candidates")

        _cid = car._CURRENT_COMPANY_ID.set("company-uuid-1")
        _dr = _DRY_RUN.set(True)
        _wd = _DRY_RUN_WOULD_DO.set([])
        try:
            await search(query="dev")
        finally:
            car._CURRENT_COMPANY_ID.reset(_cid)
            _DRY_RUN.reset(_dr)
            _DRY_RUN_WOULD_DO.reset(_wd)

        assert _REAL_SEARCH_CALLS[0].get("company_id") == "company-uuid-1"


# ----------------------------------------------------------------------------
# Output surfacing
# ----------------------------------------------------------------------------

class TestOutputMetadata:
    def test_state_to_output_surfaces_dry_run_flag(self):
        from lia_agents_core.agent_interface import AgentInput

        rt = _make_runtime()
        agent_input = AgentInput(
            message="hi", user_id="u1", company_id="company-uuid-1",
            session_id="s1", context={},
        )
        # Empty state → no tool messages; just verify metadata plumbing.
        _dr = _DRY_RUN.set(True)
        buf = [{"tool": "send_email", "args": {"candidate_id": "cand-1"}}]
        _wd = _DRY_RUN_WOULD_DO.set(buf)
        try:
            out = rt._state_to_output({"messages": []}, agent_input)
        finally:
            _DRY_RUN.reset(_dr)
            _DRY_RUN_WOULD_DO.reset(_wd)

        assert out.metadata["dry_run"] is True
        assert out.metadata["would_do_actions"] == buf

    def test_state_to_output_defaults_not_dry_run(self):
        from lia_agents_core.agent_interface import AgentInput

        rt = _make_runtime()
        agent_input = AgentInput(
            message="hi", user_id="u1", company_id="company-uuid-1",
            session_id="s1", context={},
        )
        out = rt._state_to_output({"messages": []}, agent_input)
        assert out.metadata["dry_run"] is False
        assert out.metadata["would_do_actions"] == []
