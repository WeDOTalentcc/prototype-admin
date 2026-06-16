"""Sentinel tests for Task #1068 — wizard fallback observability.

Each of the 4 wizard nodes that may fall back to deterministic mode
(`jd_enrichment`, `bigfive`, `salary`, `wsi_questions` — Tasks #1062 + #1065)
MUST call `_emit_wizard_fallback_metric(...)` with `node` + `state` + `reason`
when the LLM/benchmark times out or raises. Without this telemetry we cannot
tell which node is the worst offender or justify raising timeouts.

These tests force a timeout (or exception) on each node and assert the metric
helper was called with the canonical `node` name and a low-cardinality `reason`
tag. They also lock down that the helper itself is fail-open and emits a
structured log + Sentry breadcrumb.
"""

from __future__ import annotations

import logging
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helper itself: fail-open + log/sentry shape
# ---------------------------------------------------------------------------

def test_emit_wizard_fallback_metric_logs_structured_extras(caplog):
    from app.domains.job_creation import graph as job_graph

    with caplog.at_level(logging.WARNING, logger=job_graph.logger.name):
        job_graph._emit_wizard_fallback_metric(
            node="jd_enrichment",
            state={"workspace_id": "tenant-xyz", "session_id": "sess-1"},
            reason="llm_timeout",
            timeout_s=12.0,
            elapsed_ms=12345.0,
        )

    matching = [r for r in caplog.records if "wizard fallback fired" in r.getMessage()]
    assert matching, "expected a structured wizard-fallback warning log"
    rec = matching[-1]
    assert getattr(rec, "tenant_id", None) == "tenant-xyz"
    extra = getattr(rec, "extra_data", None)
    assert extra is not None
    assert extra["metric"] == "wizard_fallback"
    assert extra["node"] == "jd_enrichment"
    assert extra["reason"] == "llm_timeout"
    assert extra["timeout_s"] == 12.0
    assert extra["tenant_id"] == "tenant-xyz"


def test_emit_wizard_fallback_metric_is_fail_open_when_sentry_missing():
    """If sentry_sdk import or capture fails, the helper must NOT raise."""
    from app.domains.job_creation import graph as job_graph

    # No sentry available — helper still returns cleanly.
    with patch.dict("sys.modules", {"sentry_sdk": None}):
        job_graph._emit_wizard_fallback_metric(
            node="bigfive", state={}, reason="llm_timeout",
        )


def test_emit_wizard_fallback_metric_calls_sentry_when_available():
    from app.domains.job_creation import graph as job_graph

    fake_sentry = MagicMock()
    fake_scope = MagicMock()
    fake_sentry.push_scope.return_value.__enter__ = lambda *_: fake_scope
    fake_sentry.push_scope.return_value.__exit__ = lambda *_: False

    with patch.dict("sys.modules", {"sentry_sdk": fake_sentry}):
        job_graph._emit_wizard_fallback_metric(
            node="salary",
            state={"company_id": "tenant-7"},
            reason="benchmark_timeout",
            timeout_s=10.0,
        )

    fake_sentry.add_breadcrumb.assert_called_once()
    crumb = fake_sentry.add_breadcrumb.call_args.kwargs
    assert crumb["category"] == "wizard.fallback"
    assert crumb["level"] == "warning"
    assert crumb["data"]["node"] == "salary"
    assert crumb["data"]["reason"] == "benchmark_timeout"
    assert crumb["data"]["tenant_id"] == "tenant-7"

    fake_sentry.capture_message.assert_called_once()
    msg = fake_sentry.capture_message.call_args
    assert "salary" in msg.args[0]
    assert msg.kwargs["level"] == "warning"

    # Tags allow grouping in Sentry without leaking high-cardinality data.
    set_tag_calls = {c.args[0]: c.args[1] for c in fake_scope.set_tag.call_args_list}
    assert set_tag_calls.get("wizard.node") == "salary"
    assert set_tag_calls.get("wizard.fallback_reason") == "benchmark_timeout"
    assert set_tag_calls.get("tenant_id") == "tenant-7"


# ---------------------------------------------------------------------------
# Per-node call-site sentinels (Task #1068)
# ---------------------------------------------------------------------------

@pytest.fixture()
def _spy_emit():
    from app.domains.job_creation import graph as job_graph

    with patch.object(job_graph, "_emit_wizard_fallback_metric") as spy:
        yield spy


def _enriched_state() -> dict:
    return {
        "workspace_id": "tenant-1",
        "session_id": "sess-A",
        "raw_input": "Vaga de Engenheiro Backend",
        "user_query": "Vaga de Engenheiro Backend",
        "parsed_title": "Engenheiro Backend",
        "parsed_seniority": "senior",
        "parsed_department": "engenharia",
        "screening_mode": "compact",
        "question_distribution": {"technical": 1, "behavioral": 1},
        "trait_rankings": [],
        "jd_enriched": {
            "about_role": "Liderar squad de produto.",
            "responsabilidades": ["Mentor"],
            "skills_obrigatorias": [],
            "titulo_padronizado": "PM",
        },
        "stage_history": [],
    }


def _assert_called_with_node(spy, node: str, reason_substring: str | None = None) -> None:
    nodes_called = [c.kwargs.get("node") for c in spy.call_args_list]
    assert node in nodes_called, (
        f"expected _emit_wizard_fallback_metric(node={node!r}) — "
        f"got nodes={nodes_called}"
    )
    if reason_substring:
        reasons = [
            c.kwargs.get("reason", "")
            for c in spy.call_args_list
            if c.kwargs.get("node") == node
        ]
        assert any(reason_substring in r for r in reasons), (
            f"expected reason like {reason_substring!r} for node={node!r} — got {reasons}"
        )


def test_jd_enrichment_node_emits_metric_on_timeout(_spy_emit):
    import concurrent.futures as _cf
    from app.domains.job_creation import graph as job_graph

    fake_service = MagicMock()
    fake_service._fallback_enrichment.return_value = SimpleNamespace(
        wsi_quality_warnings=[],
        model_dump=lambda: {
            "titulo_padronizado": "Eng Backend",
            "about_role": "trabalho",
            "responsabilidades": [],
            "skills_obrigatorias": [],
        },
    )

    class _FakeFut:
        def result(self, timeout):
            raise _cf.TimeoutError()

    class _FakeExec:
        def __init__(self, *_a, **_kw): pass
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def submit(self, *a, **kw): return _FakeFut()

    with patch.object(job_graph, "_get_jd_service", return_value=fake_service), \
         patch.object(_cf, "ThreadPoolExecutor", _FakeExec), \
         patch(
             "app.domains.job_creation.services.jd_enrichment.calculate_quality_score",
             return_value=(50.0, []),
         ):
        state = _enriched_state()
        # Force re-enrichment path. right_panel_form bypassa o input-thin
        # guard (Task #1096/#1123): com raw curto + jd_enriched=None ele
        # retornaria "ask for JD" antes de chegar no path de timeout.
        state["jd_enriched"] = None
        state["jd_approved"] = None
        state["right_panel_form"] = {"title": "Eng Backend"}
        result = job_graph.jd_enrichment_node(state)

    assert result["ws_stage_payload"]["data"]["jd_enrichment_used_fallback"] is True
    _assert_called_with_node(_spy_emit, "jd_enrichment", reason_substring="timeout")


def test_jd_enrichment_node_emits_metric_on_exception(_spy_emit):
    import concurrent.futures as _cf
    from app.domains.job_creation import graph as job_graph

    fake_service = MagicMock()
    fake_service._fallback_enrichment.return_value = SimpleNamespace(
        wsi_quality_warnings=[],
        model_dump=lambda: {
            "titulo_padronizado": "X",
            "about_role": "y",
            "responsabilidades": [],
            "skills_obrigatorias": [],
        },
    )

    class _FakeFut:
        def result(self, timeout):
            raise RuntimeError("LLM exploded")

    class _FakeExec:
        def __init__(self, *_a, **_kw): pass
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def submit(self, *a, **kw): return _FakeFut()

    with patch.object(job_graph, "_get_jd_service", return_value=fake_service), \
         patch.object(_cf, "ThreadPoolExecutor", _FakeExec), \
         patch(
             "app.domains.job_creation.services.jd_enrichment.calculate_quality_score",
             return_value=(40.0, []),
         ):
        state = _enriched_state()
        state["jd_enriched"] = None
        state["jd_approved"] = None
        state["right_panel_form"] = {"title": "Eng Backend"}
        job_graph.jd_enrichment_node(state)

    _assert_called_with_node(_spy_emit, "jd_enrichment", reason_substring="exception")


def test_bigfive_node_emits_metric_on_timeout(_spy_emit):
    import concurrent.futures as _cf
    from app.domains.job_creation import graph as job_graph

    class _FakeFut:
        def result(self, timeout):
            raise _cf.TimeoutError()

    class _FakeExec:
        def __init__(self, *_a, **_kw): pass
        def submit(self, *a, **kw): return _FakeFut()
        def shutdown(self, **kw): pass

    fake_gen = MagicMock()

    with patch.object(job_graph, "_get_wsi_generator", return_value=fake_gen), \
         patch.object(job_graph, "evaluate_wizard_policy",
                      return_value=SimpleNamespace(
                          decision="allow", rationale="ok",
                          requires_human_confirmation=False,
                      )), \
         patch.object(_cf, "ThreadPoolExecutor", _FakeExec):
        result = job_graph.bigfive_node(_enriched_state())

    payload = result["ws_stage_payload"]["data"]
    assert payload.get("bigfive_used_fallback") is True
    _assert_called_with_node(_spy_emit, "bigfive", reason_substring="timeout")


def test_salary_node_emits_metric_on_benchmark_timeout(_spy_emit):
    import concurrent.futures as _cf
    from app.domains.job_creation import graph as job_graph

    def _raise_timeout(*_a, **_kw):
        raise _cf.TimeoutError()

    state = _enriched_state()
    state["salary_benchmark"] = None

    # PR-14 (2026-05-26): salary_node usa run_coro_in_threadpool(), não
    # ThreadPoolExecutor inline — patchar o helper canonical simula o timeout.
    with patch(
        "app.domains.job_creation.nodes.salary.run_coro_in_threadpool",
        side_effect=_raise_timeout,
    ):
        result = job_graph.salary_node(state)

    assert result["ws_stage_payload"]["data"].get("salary_used_fallback") is True
    _assert_called_with_node(_spy_emit, "salary", reason_substring="timeout")


def test_wsi_questions_node_emits_metric_on_timeout(_spy_emit):
    import concurrent.futures as _cf
    from app.domains.job_creation import graph as job_graph

    fake_q = SimpleNamespace(model_dump=lambda: {"question": "fallback Q"})
    fake_gen = MagicMock()
    fake_gen._fallback_questions.return_value = [fake_q]

    class _FakeFut:
        def result(self, timeout):
            raise _cf.TimeoutError()

    class _FakeExec:
        def __init__(self, *_a, **_kw): pass
        def submit(self, *a, **kw): return _FakeFut()
        def shutdown(self, **kw): pass

    with patch.object(job_graph, "_get_wsi_generator", return_value=fake_gen), \
         patch.object(job_graph, "evaluate_wizard_policy",
                      return_value=SimpleNamespace(
                          decision="allow", rationale="ok",
                          requires_human_confirmation=False,
                      )), \
         patch.object(_cf, "ThreadPoolExecutor", _FakeExec):
        result = job_graph.wsi_questions_node(_enriched_state())

    assert result["ws_stage_payload"]["data"].get("wsi_questions_used_fallback") is True
    _assert_called_with_node(_spy_emit, "wsi_questions", reason_substring="timeout")
