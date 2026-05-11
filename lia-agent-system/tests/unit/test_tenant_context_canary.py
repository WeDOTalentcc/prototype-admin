"""Task #977 — Unit tests para canary status do TenantAwareAgentMixin."""
from __future__ import annotations

import time

import pytest

from app.shared.agents import tenant_aware_agent as taa


@pytest.fixture(autouse=True)
def _reset_canary():
    taa.reset_tenant_context_canary_events()
    yield
    taa.reset_tenant_context_canary_events()


def test_canary_status_ok_when_no_events():
    snap = taa.get_tenant_context_canary_status(window_seconds=60)
    assert snap["status"] == "ok"
    assert snap["fail_open_count"] == 0
    assert snap["fail_closed_count"] == 0
    assert snap["window_seconds"] == 60
    assert snap["threshold_fail_closed_per_min"] == 5


def test_canary_warning_on_single_fail_open():
    taa._record_canary_event("wizard", "fail_open")
    snap = taa.get_tenant_context_canary_status(window_seconds=60)
    assert snap["status"] == "warning"
    assert snap["fail_open_count"] == 1
    assert snap["fail_closed_count"] == 0
    assert "fail_open" in snap["reason"]
    assert snap["by_agent"]["wizard"]["fail_open"] == 1


def test_canary_critical_when_fail_closed_rate_exceeds_threshold():
    # 6 fail_closed na janela de 60s = 6/min > 5/min → critical
    for _ in range(6):
        taa._record_canary_event("jobs_mgmt", "fail_closed")
    snap = taa.get_tenant_context_canary_status(window_seconds=60)
    assert snap["status"] == "critical"
    assert snap["fail_closed_count"] == 6
    assert snap["fail_closed_per_min"] == 6.0


def test_canary_critical_takes_precedence_over_warning():
    taa._record_canary_event("wizard", "fail_open")
    for _ in range(6):
        taa._record_canary_event("jobs_mgmt", "fail_closed")
    snap = taa.get_tenant_context_canary_status(window_seconds=60)
    assert snap["status"] == "critical"


def test_canary_ignores_hit_and_miss_outcomes():
    # outcomes "saudáveis" não devem entrar na deque
    taa._record_canary_event("wizard", "hit")
    taa._record_canary_event("wizard", "miss")
    snap = taa.get_tenant_context_canary_status(window_seconds=60)
    assert snap["status"] == "ok"
    assert snap["fail_open_count"] == 0
    assert snap["fail_closed_count"] == 0


def test_canary_window_excludes_old_events(monkeypatch):
    # injeta evento com timestamp antigo direto
    old_ts = time.time() - 3600
    taa._CANARY_EVENTS.append((old_ts, "wizard", "fail_open"))
    snap = taa.get_tenant_context_canary_status(window_seconds=60)
    # evento fora da janela → status ok
    assert snap["status"] == "ok"


def test_record_metric_feeds_canary():
    # contrato canônico: _record_metric (chamado pelo mixin) também alimenta canary
    taa._record_metric("kanban", "fail_open")
    snap = taa.get_tenant_context_canary_status(window_seconds=60)
    assert snap["status"] == "warning"
    assert snap["by_agent"]["kanban"]["fail_open"] == 1


def test_canary_window_per_min_normalization():
    # 1 fail_closed em janela de 10s normaliza para 6/min → critical
    for _ in range(1):
        taa._record_canary_event("ats_integration", "fail_closed")
    snap = taa.get_tenant_context_canary_status(window_seconds=10)
    assert snap["fail_closed_per_min"] == 6.0
    assert snap["status"] == "critical"
