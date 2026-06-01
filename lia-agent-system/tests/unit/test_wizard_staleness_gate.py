"""Fix 2026-05-31: wizard abandonado não sequestra mensagens futuras (staleness TTL).

Bug: usuário começava uma vaga, abandonava no meio (stage não-terminal). O
checkpoint LangGraph nunca expirava → todo "oi" futuro reentrava no wizard stale
e abria o painel WSI. Fix: gate de staleness via created_at do checkpoint.
"""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from app.shared.sessions import thread_id as tid


def _fake_graph(snapshot):
    return SimpleNamespace(_graph=SimpleNamespace(get_state=lambda config: snapshot))


def _snap(stage, age_hours):
    ts = (datetime.now(timezone.utc) - timedelta(hours=age_hours)).isoformat()
    return SimpleNamespace(
        values={"current_stage": stage, "conversation_messages": [{"x": 1}]},
        created_at=ts,
        tasks=[],
    )


@pytest.mark.medium
@pytest.mark.asyncio
async def test_recent_wizard_is_active(monkeypatch):
    monkeypatch.setattr(tid, "_WIZARD_SESSION_TTL_HOURS", 2.0)
    monkeypatch.setattr(
        "app.domains.job_creation.graph.get_job_creation_graph",
        lambda: _fake_graph(_snap("wsi_questions", age_hours=0.1)),
    )
    assert await tid.is_wizard_session_active("comp-1", "sess-1") is True


@pytest.mark.medium
@pytest.mark.asyncio
async def test_stale_wizard_is_inactive(monkeypatch):
    # 3h > TTL 2h → abandonado → não sequestra o chat.
    monkeypatch.setattr(tid, "_WIZARD_SESSION_TTL_HOURS", 2.0)
    monkeypatch.setattr(
        "app.domains.job_creation.graph.get_job_creation_graph",
        lambda: _fake_graph(_snap("wsi_questions", age_hours=3.0)),
    )
    assert await tid.is_wizard_session_active("comp-1", "sess-1") is False


@pytest.mark.medium
@pytest.mark.asyncio
async def test_completed_wizard_is_inactive(monkeypatch):
    monkeypatch.setattr(tid, "_WIZARD_SESSION_TTL_HOURS", 2.0)
    monkeypatch.setattr(
        "app.domains.job_creation.graph.get_job_creation_graph",
        lambda: _fake_graph(_snap("completed", age_hours=0.1)),
    )
    assert await tid.is_wizard_session_active("comp-1", "sess-1") is False


@pytest.mark.medium
@pytest.mark.asyncio
async def test_ttl_zero_disables_gate(monkeypatch):
    # TTL=0 → comportamento legado (não expira por idade).
    monkeypatch.setattr(tid, "_WIZARD_SESSION_TTL_HOURS", 0.0)
    monkeypatch.setattr(
        "app.domains.job_creation.graph.get_job_creation_graph",
        lambda: _fake_graph(_snap("wsi_questions", age_hours=99.0)),
    )
    assert await tid.is_wizard_session_active("comp-1", "sess-1") is True


@pytest.mark.medium
@pytest.mark.asyncio
async def test_no_snapshot_inactive(monkeypatch):
    monkeypatch.setattr(
        "app.domains.job_creation.graph.get_job_creation_graph",
        lambda: _fake_graph(None),
    )
    assert await tid.is_wizard_session_active("comp-1", "sess-1") is False
