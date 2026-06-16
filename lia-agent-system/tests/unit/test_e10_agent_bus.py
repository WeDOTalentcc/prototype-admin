"""
Tests for Sprint Y5 — E10: Agent-to-Agent Communication via AgentBus.

12 test cases covering AgentEvent, AgentBus, and EnhancedAgentMixin.emit().
All tests use unittest.mock and do NOT require a real Redis instance.
"""
from __future__ import annotations

import asyncio
import json
import sys
import types
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_event(**kwargs):
    from lia_agents_core.agent_bus import AgentEvent

    defaults = dict(
        from_agent="sourcing",
        to_agent="pipeline",
        event_type="candidate_imported",
        payload={"candidate_id": "cand-1", "job_id": "job-1"},
        company_id="co-abc",
    )
    defaults.update(kwargs)
    return AgentEvent(**defaults)


# ---------------------------------------------------------------------------
# AgentEvent tests
# ---------------------------------------------------------------------------


def test_agent_event_to_dict():
    """AgentEvent.to_dict() must contain all required keys."""
    from lia_agents_core.agent_bus import AgentEvent

    event = _make_event()
    d = event.to_dict()

    required_keys = {
        "from_agent", "to_agent", "event_type", "payload",
        "company_id", "event_id", "published_at",
    }
    assert required_keys.issubset(d.keys())
    assert d["from_agent"] == "sourcing"
    assert d["to_agent"] == "pipeline"
    assert d["event_type"] == "candidate_imported"
    assert d["company_id"] == "co-abc"
    assert d["payload"] == {"candidate_id": "cand-1", "job_id": "job-1"}
    assert d["event_id"]       # non-empty
    assert d["published_at"]   # non-empty


def test_agent_event_from_dict():
    """AgentEvent roundtrip: to_dict → from_dict preserves all fields."""
    from lia_agents_core.agent_bus import AgentEvent

    original = _make_event()
    d = original.to_dict()
    restored = AgentEvent.from_dict(d)

    assert restored.from_agent == original.from_agent
    assert restored.to_agent == original.to_agent
    assert restored.event_type == original.event_type
    assert restored.payload == original.payload
    assert restored.company_id == original.company_id
    assert restored.event_id == original.event_id
    assert restored.published_at == original.published_at


def test_agent_event_channel_format():
    """AgentBus.channel() must return lia:agent_bus:{company_id}:{to_agent}."""
    from lia_agents_core.agent_bus import AgentBus, CHANNEL_PREFIX

    bus = AgentBus()
    ch = bus.channel("co-xyz", "pipeline")
    assert ch == f"{CHANNEL_PREFIX}:co-xyz:pipeline"


# ---------------------------------------------------------------------------
# AgentBus.publish tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_publish_fail_open_on_redis_error():
    """publish() returns False when Redis raises — no exception propagates."""
    from lia_agents_core.agent_bus import AgentBus

    bus = AgentBus()

    mock_redis = AsyncMock()
    mock_redis.publish.side_effect = ConnectionError("Redis down")

    with patch("app.core.redis_client.get_redis", return_value=mock_redis, create=True):
        result = await bus.publish(
            from_agent="sourcing",
            to_agent="pipeline",
            event_type="candidate_imported",
            payload={},
            company_id="co-1",
        )

    assert result is False


@pytest.mark.asyncio
async def test_publish_success_returns_true():
    """publish() returns True when Redis.publish() succeeds."""
    from lia_agents_core.agent_bus import AgentBus

    bus = AgentBus()

    mock_redis = AsyncMock()
    mock_redis.publish = AsyncMock(return_value=1)

    with patch("app.core.redis_client.get_redis", AsyncMock(return_value=mock_redis), create=True):
        result = await bus.publish(
            from_agent="sourcing",
            to_agent="pipeline",
            event_type="candidate_imported",
            payload={"candidate_id": "c-1"},
            company_id="co-1",
        )

    assert result is True
    mock_redis.publish.assert_called_once()
    channel_arg, payload_arg = mock_redis.publish.call_args[0]
    assert "pipeline" in channel_arg
    assert "co-1" in channel_arg
    data = json.loads(payload_arg)
    assert data["event_type"] == "candidate_imported"


# ---------------------------------------------------------------------------
# AgentBus.subscribe / dispatch_local tests
# ---------------------------------------------------------------------------


def test_subscribe_registers_handler():
    """subscribe() adds handler to the internal subscribers dict."""
    from lia_agents_core.agent_bus import AgentBus

    bus = AgentBus()
    handler = AsyncMock()

    bus.subscribe("pipeline", handler)

    counts = bus.list_subscribers()
    assert counts.get("pipeline") == 1


@pytest.mark.asyncio
async def test_dispatch_local_calls_handler():
    """dispatch_local() calls the subscribed handler with the event."""
    from lia_agents_core.agent_bus import AgentBus

    bus = AgentBus()
    received: list = []

    async def handler(event):
        received.append(event)

    bus.subscribe("pipeline", handler)
    event = _make_event(to_agent="pipeline")
    await bus.dispatch_local(event)

    assert len(received) == 1
    assert received[0] is event


@pytest.mark.asyncio
async def test_dispatch_local_isolates_by_agent():
    """Handler registered for 'pipeline' is NOT called for event targeting 'sourcing'."""
    from lia_agents_core.agent_bus import AgentBus

    bus = AgentBus()
    pipeline_calls: list = []
    sourcing_calls: list = []

    async def pipeline_handler(event):
        pipeline_calls.append(event)

    async def sourcing_handler(event):
        sourcing_calls.append(event)

    bus.subscribe("pipeline", pipeline_handler)
    bus.subscribe("sourcing", sourcing_handler)

    event = _make_event(to_agent="sourcing")
    await bus.dispatch_local(event)

    assert len(pipeline_calls) == 0
    assert len(sourcing_calls) == 1


@pytest.mark.asyncio
async def test_dispatch_local_fail_open_handler_error():
    """If one handler raises, other handlers still get called (fail-open)."""
    from lia_agents_core.agent_bus import AgentBus

    bus = AgentBus()
    second_called: list = []

    async def bad_handler(event):
        raise RuntimeError("boom")

    async def good_handler(event):
        second_called.append(event)

    bus.subscribe("pipeline", bad_handler)
    bus.subscribe("pipeline", good_handler)

    event = _make_event(to_agent="pipeline")
    # Should not raise
    await bus.dispatch_local(event)

    assert len(second_called) == 1


# ---------------------------------------------------------------------------
# EnhancedAgentMixin.emit tests
# ---------------------------------------------------------------------------


def _make_mixin_instance() -> object:
    """Create a minimal EnhancedAgentMixin instance with _enhanced_domain set."""
    from libs.agents_core.lia_agents_core.enhanced_agent_mixin import EnhancedAgentMixin  # noqa: F401 — dynamic

    # We can't use the path above reliably in tests; import directly.
    import importlib
    mixin_mod = importlib.import_module("lia_agents_core.enhanced_agent_mixin")
    EnhancedAgentMixinCls = mixin_mod.EnhancedAgentMixin

    class _Stub(EnhancedAgentMixinCls):
        pass

    obj = object.__new__(_Stub)
    obj._enhanced_domain = "sourcing"
    return obj


@pytest.mark.asyncio
async def test_emit_mixin_method_calls_publish():
    """emit() delegates to agent_bus.publish() with correct arguments."""
    try:
        from lia_agents_core.enhanced_agent_mixin import EnhancedAgentMixin
    except ImportError:
        pytest.skip("EnhancedAgentMixin not importable in this environment")

    class _Stub(EnhancedAgentMixin):
        pass

    obj = object.__new__(_Stub)
    obj._enhanced_domain = "sourcing"

    mock_bus = MagicMock()
    mock_bus.publish = AsyncMock(return_value=True)

    with patch("lia_agents_core.agent_bus.agent_bus", mock_bus):
        result = await obj.emit(
            to_agent="pipeline",
            event_type="candidate_imported",
            payload={"candidate_id": "c-9"},
            company_id="co-2",
        )

    assert result is True
    mock_bus.publish.assert_called_once_with(
        from_agent="sourcing",
        to_agent="pipeline",
        event_type="candidate_imported",
        payload={"candidate_id": "c-9"},
        company_id="co-2",
    )


@pytest.mark.asyncio
async def test_emit_fail_open_on_error():
    """emit() returns False when agent_bus.publish raises — no exception propagates."""
    try:
        from lia_agents_core.enhanced_agent_mixin import EnhancedAgentMixin
    except ImportError:
        pytest.skip("EnhancedAgentMixin not importable in this environment")

    class _Stub(EnhancedAgentMixin):
        pass

    obj = object.__new__(_Stub)
    obj._enhanced_domain = "wizard"

    mock_bus = MagicMock()
    mock_bus.publish = AsyncMock(side_effect=RuntimeError("bus exploded"))

    with patch("lia_agents_core.agent_bus.agent_bus", mock_bus):
        result = await obj.emit(
            to_agent="jobs_management",
            event_type="job_creation_ready",
            payload={},
            company_id="co-3",
        )

    assert result is False


# ---------------------------------------------------------------------------
# list_subscribers
# ---------------------------------------------------------------------------


def test_list_subscribers_returns_counts():
    """list_subscribers() returns a dict mapping agent name → handler count."""
    from lia_agents_core.agent_bus import AgentBus

    bus = AgentBus()

    async def h1(e): pass
    async def h2(e): pass
    async def h3(e): pass

    bus.subscribe("pipeline", h1)
    bus.subscribe("pipeline", h2)
    bus.subscribe("sourcing", h3)

    counts = bus.list_subscribers()
    assert counts["pipeline"] == 2
    assert counts["sourcing"] == 1
