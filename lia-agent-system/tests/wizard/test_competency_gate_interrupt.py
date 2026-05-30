"""Sprint F.2 sensor — pin self-loop interrupt() pattern on wizard HITL gates.

Background (bug Sprint F.2): when the LLM gate classifier returned a
non-terminal intent (``undecided`` / ``ask_question`` / ``low_confidence``),
the routing function returned ``"end"`` → graph completed cleanly →
``is_interrupted=False`` on next turn → ``WizardSessionService`` rebuilt
state from scratch and re-entered ``intake`` → wizard restarted, losing
JD enrichment + BigFive + competency progress.

Fix (canonical Option A): routing returns the gate's OWN name (self-loop)
when intent is non-terminal. The gate re-executes; ``gate_resume_message``
is empty (just cleared by previous pass) and ``gate_seen_user_query``
matches ``user_query`` so WS resume detection skips. Then
``if not msg and _in_graph_runtime(): interrupt(...)`` pauses the graph
canonically. Next user turn finds ``is_interrupted=True`` and
``aresume_with_message`` works as expected.

This sensor pins three guarantees:

  1. ``route_after_competency_gate`` returns ``"competency_gate"`` (self)
     when no terminal mode is set (mode not in {compact, full}) and not
     fairness-blocked. NEVER returns ``"end"`` for the non-terminal path
     post-classification — that would re-introduce the bug.

  2. Same for ``route_after_wsi_questions_gate`` (returns
     ``"wsi_questions_gate"`` on non-terminal) and ``route_after_gate``
     (returns ``"jd_gate"`` on ask_question / off_topic).

  3. The graph builder maps the self-loop labels to the corresponding
     nodes in ``add_conditional_edges``. Without this mapping the graph
     would raise ``ValueError: unknown route`` at runtime.

If any of these assertions fail, the harness has regressed and the
state-hydration bug is back.
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from app.domains.job_creation.graph import (
    route_after_competency_gate,
    route_after_gate,
    route_after_wsi_questions_gate,
)


# ---------------------------------------------------------------------------
# 1) Routing functions return self-loop on non-terminal intent
# ---------------------------------------------------------------------------

class TestCompetencyGateSelfLoop:
    """Sprint F.2 — competency_gate routing must self-loop on non-terminal."""

    @pytest.mark.parametrize("intent", ["ask_question", "undecided", None])
    def test_returns_self_when_no_mode_selected(self, intent):
        """No screening_mode + non-terminal intent → self-loop, NOT 'end'."""
        state = {
            "current_stage": "competency",
            "screening_mode": None,  # critical: no terminal mode set
            "gate_last_intent": intent,
            "fairness_blocked": False,
        }
        assert route_after_competency_gate(state) == "competency_gate", (
            f"Regression — non-terminal intent={intent!r} must self-loop "
            "to re-enter interrupt(). Returning 'end' breaks resume."
        )

    def test_returns_wsi_questions_when_mode_compact(self):
        state = {"screening_mode": "compact", "gate_last_intent": "select_compact"}
        assert route_after_competency_gate(state) == "wsi_questions"

    def test_returns_wsi_questions_when_mode_full(self):
        state = {"screening_mode": "full", "gate_last_intent": "select_full"}
        assert route_after_competency_gate(state) == "wsi_questions"

    def test_returns_end_when_fairness_blocked(self):
        """Fairness block IS terminal — END is correct here (block reason
        already surfaced to user; no further classification possible)."""
        state = {
            "fairness_blocked": True,
            "screening_mode": None,
            "gate_last_intent": "ask_question",
        }
        assert route_after_competency_gate(state) == "end"


class TestWsiQuestionsGateSelfLoop:
    """Sprint F.2 — wsi_questions_gate routing must self-loop on non-terminal."""

    @pytest.mark.parametrize("intent", ["ask_question", None])
    def test_returns_self_when_awaiting_decision(self, intent):
        state = {
            "current_stage": "wsi_questions",
            "questions_approved": None,  # critical: still pending
            "wsi_regenerate_pending": False,
            "gate_last_intent": intent,
            "fairness_blocked": False,
        }
        assert route_after_wsi_questions_gate(state) == "wsi_questions_gate", (
            f"Regression — non-terminal intent={intent!r} must self-loop."
        )

    def test_returns_eligibility_when_approved(self):
        state = {"questions_approved": True, "gate_last_intent": "approve_all"}
        assert route_after_wsi_questions_gate(state) == "eligibility"

    def test_returns_wsi_questions_when_regen_pending(self):
        state = {
            "wsi_regenerate_pending": True,
            "questions_approved": False,
            "gate_last_intent": "regenerate_all",
        }
        assert route_after_wsi_questions_gate(state) == "wsi_questions"

    def test_returns_end_when_fairness_blocked(self):
        state = {"fairness_blocked": True, "gate_last_intent": "ask_question"}
        assert route_after_wsi_questions_gate(state) == "end"


class TestJdGateSelfLoop:
    """Sprint F.2 — jd_gate routing must self-loop on ask_question /
    off_topic (latent bug — same class as competency/wsi)."""

    @pytest.mark.parametrize("intent", ["ask_question", "off_topic", None])
    def test_returns_self_when_no_approval_decision(self, intent):
        state = {
            "jd_fairness_blocked": False,
            "jd_approved": None,  # critical: no terminal approve/reject
            "gate_last_intent": intent,
        }
        assert route_after_gate(state) == "jd_gate", (
            f"Regression — non-terminal intent={intent!r} must self-loop."
        )

    def test_returns_intake_on_provide_new_content(self):
        state = {
            "jd_fairness_blocked": False,
            "jd_approved": False,
            "gate_last_intent": "provide_new_content",
        }
        assert route_after_gate(state) == "intake"

    def test_returns_bigfive_on_approved_high_quality(self, monkeypatch):
        monkeypatch.setenv("LIA_WIZARD_MIN_JD_QUALITY", "50")
        state = {
            "jd_fairness_blocked": False,
            "jd_approved": True,
            "jd_quality_score": 80.0,
            "gate_last_intent": "approve",
        }
        assert route_after_gate(state) == "bigfive"

    def test_returns_end_when_fairness_blocked(self):
        state = {"jd_fairness_blocked": True, "gate_last_intent": "approve"}
        assert route_after_gate(state) == "end"


# ---------------------------------------------------------------------------
# 2) Graph builder wires the self-loop edge mappings
# ---------------------------------------------------------------------------

def test_graph_builder_has_self_loop_mappings():
    """The conditional_edges mapping MUST include the self-loop labels
    or the graph raises ``ValueError: at node ... received unknown route
    '<gate_name>'`` at runtime when the routing function returns it.

    We don't introspect LangGraph internals (those are private); we
    grep the source file. Cheap, deterministic, exhibits intent.
    """
    import inspect

    import app.domains.job_creation.graph as graph_module

    src = inspect.getsource(graph_module)

    # Each gate must have its self-loop label mapped to its node name.
    assert '"jd_gate": "jd_gate"' in src, (
        "Regression — jd_gate self-loop mapping missing from "
        "add_conditional_edges. Routing returning 'jd_gate' will fail at "
        "runtime with ValueError: unknown route."
    )
    assert '"competency_gate": "competency_gate"' in src, (
        "Regression — competency_gate self-loop mapping missing."
    )
    assert '"wsi_questions_gate": "wsi_questions_gate"' in src, (
        "Regression — wsi_questions_gate self-loop mapping missing."
    )


# ---------------------------------------------------------------------------
# 3) Gate node calls interrupt() on the await branch (defense-in-depth)
# ---------------------------------------------------------------------------

class TestGateNodeCallsInterrupt:
    """When the gate runs with no resume message AND inside graph runtime,
    it MUST call ``langgraph.types.interrupt()`` to pause the graph.
    Without this, the self-loop edge would create an infinite loop
    (graph would re-enter the gate forever without yielding control)."""

    def _state(self, **overrides):
        base = {
            "current_stage": "competency",
            "screening_mode": None,
            "seniority_resolved": "pleno",
            "gate_resume_message": "",
            "user_query": "",  # empty -> no fresh turn detection
            "gate_seen_user_query": "",
            "workspace_id": "test-company",
            "user_id": "test-user",
        }
        base.update(overrides)
        return base

    def test_competency_gate_calls_interrupt_in_graph_runtime(self):
        """Inside graph runtime, no msg → interrupt() canonical pause."""
        from app.domains.job_creation.graph import competency_gate_node

        # langgraph's `interrupt` raises GraphInterrupt under the hood to
        # suspend execution. We patch it to a sentinel-raising mock so we
        # can assert it was called without actually needing the Pregel
        # runtime checkpoint plumbing.
        class _StopMarker(Exception):
            pass

        with patch(
            "app.domains.job_creation.nodes.competency_gate._in_graph_runtime",
            return_value=True,
        ), patch("langgraph.types.interrupt") as mock_interrupt:
            mock_interrupt.side_effect = _StopMarker("interrupt called")
            with pytest.raises(_StopMarker):
                competency_gate_node(self._state())
            assert mock_interrupt.called, (
                "Regression — competency_gate did not call interrupt() on "
                "the await branch. Self-loop without interrupt = infinite "
                "graph recursion (GraphRecursionError)."
            )
            # Payload sanity — must include stage marker so wizard service
            # can route the clarify message to the right UI panel.
            call_args = mock_interrupt.call_args
            payload = call_args[0][0] if call_args[0] else call_args[1].get("__arg__", {})
            assert isinstance(payload, dict), "interrupt payload must be dict"
            assert payload.get("stage") == "competency"

    def test_wsi_questions_gate_calls_interrupt_in_graph_runtime(self):
        from app.domains.job_creation.graph import wsi_questions_gate_node

        class _StopMarker(Exception):
            pass

        state = self._state(
            current_stage="wsi_questions",
            wsi_questions=[],  # empty -> no WS resume detection
            questions_approved=None,
        )
        with patch(
            "app.domains.job_creation.graph._in_graph_runtime",
            return_value=True,
        ), patch("langgraph.types.interrupt") as mock_interrupt:
            mock_interrupt.side_effect = _StopMarker("interrupt called")
            with pytest.raises(_StopMarker):
                wsi_questions_gate_node(state)
            assert mock_interrupt.called
            payload = mock_interrupt.call_args[0][0]
            assert payload.get("stage") == "wsi_questions"

    def test_competency_gate_no_interrupt_outside_graph_runtime(self):
        """Offline / sentinel calls (``_in_graph_runtime()=False``) must
        NOT call interrupt — that path is the legacy END no-op used by
        domain.py REST + offline tests. Preserves backwards compat."""
        from app.domains.job_creation.graph import competency_gate_node

        with patch(
            "app.domains.job_creation.graph._in_graph_runtime",
            return_value=False,
        ), patch("langgraph.types.interrupt") as mock_interrupt:
            result = competency_gate_node(self._state())
            assert not mock_interrupt.called, (
                "Outside graph runtime, interrupt() must NOT fire — "
                "offline path returns clean state without pause."
            )
            assert result.get("current_stage") == "competency"
