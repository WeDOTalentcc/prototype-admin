"""Assertion tests: every wizard graph node emits a span with required attrs.

Closes N-07 (wizard observability gap). Each node is invoked directly with a
minimal state — services that hit LLMs/HTTP are bypassed by checking
short-circuit branches in the node code (e.g., empty enriched JD makes
`bigfive_node` skip the LLM and return synthesized empty data).

Reference: ADR-019 §Promotion Gate #8, task #861.
"""
from __future__ import annotations

from typing import Any, Iterable

import pytest

from app.orchestrator.observability._observability import WIZARD_SPANS
from app.shared.observability import tracing as _tracing
from app.shared.observability.span_validation import (
    WIZARD_REQUIRED_SPAN_ATTRS,
    validate_span_attributes,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _clear_completed_spans():
    """Each test starts with an empty trace buffer."""
    _tracing._completed_spans.clear()
    _tracing._active_spans.clear()
    yield
    _tracing._completed_spans.clear()
    _tracing._active_spans.clear()


def _seed_state(**overrides: Any) -> dict:
    """Minimal wizard state with the multi-tenant fields populated."""
    base = {
        "session_id": "session-123",
        "user_id": "recruiter-77",
        "workspace_id": 42,
        "raw_input": "Backend pleno em São Paulo, R$ 10-15k.",
        "user_query": "Backend pleno em São Paulo, R$ 10-15k.",
        "current_stage": "intake",
    }
    base.update(overrides)
    return base


def _spans_named(names: Iterable[str]) -> list[dict]:
    """Return all spans whose name matches any in `names`."""
    target = set(names)
    return [s for s in _tracing._completed_spans if s.get("name") in target]


# ---------------------------------------------------------------------------
# Per-node assertions
# ---------------------------------------------------------------------------

def test_intake_node_emits_span_with_required_attributes(monkeypatch):
    # Stub the IntakeExtractor so the test stays hermetic
    from app.domains.job_creation import graph as g

    class _FakeExtractor:
        def extract(self, *_a, **_kw):
            from app.domains.job_creation.services.intake_extractor import JobIntakePayload
            return JobIntakePayload()

        def extract_from_sources(self, *_a, **_kw):
            from app.domains.job_creation.services.intake_extractor import JobIntakePayload
            return JobIntakePayload()

    monkeypatch.setattr(g, "get_intake_extractor", lambda: _FakeExtractor())
    g.intake_node(_seed_state())

    spans = _spans_named([WIZARD_SPANS.JOB_CREATION_INTAKE])
    assert spans, "intake_node should emit wizard.job_creation.intake span"
    result = validate_span_attributes(spans[-1])
    assert result.is_valid, result.reason()
    assert spans[-1]["attributes"]["wizard.stage"] == "intake"


def test_salary_node_emits_span_with_required_attributes():
    """salary_node has no LLM calls — invoke directly."""
    from app.domains.job_creation.graph import salary_node

    salary_node(_seed_state(current_stage="salary"))
    spans = _spans_named([WIZARD_SPANS.JOB_CREATION_SALARY])
    assert spans, "salary_node should emit wizard.job_creation.salary span"
    result = validate_span_attributes(spans[-1])
    assert result.is_valid, result.reason()


def test_eligibility_node_emits_span_with_required_attributes():
    from app.domains.job_creation.graph import eligibility_node

    eligibility_node(_seed_state(current_stage="eligibility", eligibility_questions=[]))
    spans = _spans_named([WIZARD_SPANS.JOB_CREATION_ELIGIBILITY])
    assert spans
    result = validate_span_attributes(spans[-1])
    assert result.is_valid, result.reason()



def test_node_error_marks_span_status(monkeypatch):
    """When a node raises, its span must still be emitted with status=error."""
    from app.domains.job_creation import graph as g

    def _boom(*_a, **_kw):
        raise RuntimeError("intake fault")

    class _BoomExtractor:
        extract = _boom
        extract_from_sources = _boom

    monkeypatch.setattr(g, "get_intake_extractor", lambda: _BoomExtractor())

    with pytest.raises(RuntimeError):
        g.intake_node(_seed_state())

    spans = _spans_named([WIZARD_SPANS.JOB_CREATION_INTAKE])
    assert spans
    assert spans[-1]["status"] == "error"
    assert "intake fault" in (spans[-1].get("error") or "")
    # Even on error, mandatory tenant attributes must remain populated.
    result = validate_span_attributes(spans[-1])
    assert result.is_valid, result.reason()


# ---------------------------------------------------------------------------
# Tenant context propagation through the WS dispatcher
# ---------------------------------------------------------------------------

def test_get_agent_emits_span_with_tenant_context(monkeypatch):
    from app.api.v1 import chat_shared as agent_chat_ws

    # Bypass the registry — we only care about the span instrumentation.
    monkeypatch.setattr(agent_chat_ws, "_ensure_agents_loaded", lambda: None)

    class _FakeRegistry:
        def get_or_fallback(self, _domain, fallback_id="talent"):
            return object()

    import sys
    fake_module = type("M", (), {"AgentRegistry": lambda: _FakeRegistry()})()
    monkeypatch.setitem(sys.modules, "app.shared.agents.agent_registry", fake_module)

    agent_chat_ws._get_agent(
        "talent",
        company_id="42",
        session_id="session-abc",
        user_id="user-77",
    )
    spans = _spans_named([WIZARD_SPANS.AGENT_CHAT_GET_AGENT])
    assert spans
    result = validate_span_attributes(spans[-1])
    assert result.is_valid, result.reason()
    assert spans[-1]["attributes"]["domain"] == "talent"


def test_get_agent_without_context_fails_validation(monkeypatch):
    """Sanity check: a caller forgetting to pass tenant context produces a
    span the CI gate flags. This is the safety net the audit asked for."""
    from app.api.v1 import chat_shared as agent_chat_ws

    monkeypatch.setattr(agent_chat_ws, "_ensure_agents_loaded", lambda: None)

    class _FakeRegistry:
        def get_or_fallback(self, _domain, fallback_id="talent"):
            return object()

    import sys
    fake_module = type("M", (), {"AgentRegistry": lambda: _FakeRegistry()})()
    monkeypatch.setitem(sys.modules, "app.shared.agents.agent_registry", fake_module)

    agent_chat_ws._get_agent("talent")  # no tenant context — bad
    spans = _spans_named([WIZARD_SPANS.AGENT_CHAT_GET_AGENT])
    assert spans
    result = validate_span_attributes(spans[-1])
    assert not result.is_valid
    assert "tenant.company_id" in result.empty
