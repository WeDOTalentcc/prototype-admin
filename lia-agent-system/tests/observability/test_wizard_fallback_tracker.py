"""Tests for the WizardFallbackTracker (Task #1070).

Cobertura:
- record_fallback retorna None enquanto a janela esta abaixo do threshold;
- ao cruzar SESSION_THRESHOLD, devolve snapshot ai_degraded_mode com scope
  "session" e reason_breakdown agregado;
- escopo "tenant" dispara independentemente quando varios session_ids do
  mesmo company_id excedem o limite;
- get_state respeita a janela deslizante e expira eventos antigos;
- alertas para o time de plataforma respeitam cooldown.
"""
from __future__ import annotations

import importlib
import time

import pytest


@pytest.fixture()
def tracker_module(monkeypatch):
    monkeypatch.setenv("LIA_WIZARD_FALLBACK_SESSION_WINDOW_S", "60")
    monkeypatch.setenv("LIA_WIZARD_FALLBACK_SESSION_THRESHOLD", "3")
    monkeypatch.setenv("LIA_WIZARD_FALLBACK_TENANT_WINDOW_S", "120")
    monkeypatch.setenv("LIA_WIZARD_FALLBACK_TENANT_THRESHOLD", "4")
    monkeypatch.setenv("LIA_WIZARD_FALLBACK_ALERT_COOLDOWN_S", "300")
    from app.shared.observability import wizard_fallback_tracker as mod

    importlib.reload(mod)
    yield mod


def _new_tracker(mod):
    return mod.WizardFallbackTracker()


def test_record_below_threshold_returns_none(tracker_module):
    t = _new_tracker(tracker_module)
    assert t.record_fallback(session_id="s", company_id="c", stage="jd", reason="timeout") is None
    assert t.record_fallback(session_id="s", company_id="c", stage="bf", reason="timeout") is None
    assert t.get_state(session_id="s", company_id="c") is None


def test_session_threshold_emits_snapshot(tracker_module):
    t = _new_tracker(tracker_module)
    t.record_fallback(session_id="s", company_id="c", stage="jd", reason="timeout")
    t.record_fallback(session_id="s", company_id="c", stage="bf", reason="timeout")
    snap = t.record_fallback(
        session_id="s", company_id="c", stage="wsi", reason="provider_error"
    )
    assert snap is not None
    assert snap["active"] is True
    assert snap["scope"] == "session"
    assert snap["count"] == 3
    assert snap["threshold"] == 3
    assert snap["reason_breakdown"] == {"timeout": 2, "provider_error": 1}
    again = t.get_state(session_id="s", company_id="c")
    assert again is not None and again["scope"] == "session"


def test_tenant_threshold_independent_of_session(tracker_module):
    t = _new_tracker(tracker_module)
    # 4 fallbacks from different sessions of the same tenant — only tenant trips.
    for i in range(4):
        snap = t.record_fallback(
            session_id=f"s{i}", company_id="acme", stage="jd", reason="provider_error"
        )
    assert snap is not None
    assert snap["scope"] == "tenant"
    assert snap["count"] == 4


def test_record_ignores_empty_reason(tracker_module):
    t = _new_tracker(tracker_module)
    for _ in range(5):
        assert (
            t.record_fallback(session_id="s", company_id="c", stage="jd", reason=None)
            is None
        )
    assert t.get_state(session_id="s", company_id="c") is None


def test_window_prunes_old_events(tracker_module, monkeypatch):
    t = _new_tracker(tracker_module)
    real_time = time.time
    base = real_time()
    # First two events at t=0, third event 70s later — outside the 60s window.
    monkeypatch.setattr(time, "time", lambda: base)
    t.record_fallback(session_id="s", company_id="c", stage="jd", reason="timeout")
    t.record_fallback(session_id="s", company_id="c", stage="bf", reason="timeout")
    monkeypatch.setattr(time, "time", lambda: base + 70.0)
    snap = t.record_fallback(
        session_id="s", company_id="c", stage="wsi", reason="exception"
    )
    # Only one event remains in the session window so threshold is not crossed.
    assert snap is None


def test_alert_cooldown_prevents_storm(tracker_module, monkeypatch):
    t = _new_tracker(tracker_module)
    calls: list[dict] = []

    def fake_emit(*, scope, session_id, company_id, snapshot):
        calls.append({"scope": scope, "snapshot": snapshot})

    monkeypatch.setattr(t, "_emit_alert", fake_emit)
    for i in range(5):
        t.record_fallback(
            session_id="s", company_id="c", stage=f"st{i}", reason="timeout"
        )
    # First alert at threshold cross; cooldown blocks subsequent ones in same window.
    assert len(calls) == 1
    assert calls[0]["scope"] == "session"
