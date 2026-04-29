"""Integration tests for the wizard policy gate inside JobCreationGraph.

Each gated node (``bigfive_node``, ``wsi_questions_node``, ``publish_node``)
is exercised through the three canonical decisions ``ALLOW`` /
``HITL_REQUIRED`` / ``DENY`` so we lock down:

  * the early-return contract on ``DENY`` (no LLM/API call, error set);
  * the ``pending_human_confirmation`` mark on ``HITL_REQUIRED``;
  * the silent ``ALLOW`` path that preserves existing wizard behaviour;
  * propagation of the decision into ``state['policy_decisions']``.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _allow():
    from app.domains.job_creation.policy_gate import PolicyDecision, WizardPolicyResult
    return WizardPolicyResult(
        decision=PolicyDecision.ALLOW,
        rationale="allowed",
        confidence_band="high",
    )


def _hitl():
    from app.domains.job_creation.policy_gate import PolicyDecision, WizardPolicyResult
    return WizardPolicyResult(
        decision=PolicyDecision.HITL_REQUIRED,
        rationale="needs HR sign-off",
        confidence_band="medium",
        requires_human_confirmation=True,
    )


def _deny(reason: str = "policy denied"):
    from app.domains.job_creation.policy_gate import PolicyDecision, WizardPolicyResult
    return WizardPolicyResult(
        decision=PolicyDecision.DENY,
        rationale=reason,
        confidence_band="low",
    )


def _enriched_state() -> dict:
    return {
        "workspace_id": 42,
        "user_id": "recruiter-1",
        "jd_quality_score": 88.0,
        "seniority_resolved": "senior",
        "parsed_seniority": "senior",
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


# ---------------------------------------------------------------------------
# bigfive_node
# ---------------------------------------------------------------------------

def test_bigfive_node_allow_proceeds_and_records_decision():
    from app.domains.job_creation import graph as job_graph

    fake_bigfive = SimpleNamespace(
        model_dump=lambda: {"openness": {"score": 4, "evidence": "neutral"}}
    )
    fake_gen = MagicMock()
    fake_gen.extract_bigfive.return_value = fake_bigfive
    fake_gen.rank_traits.return_value = []

    with patch.object(job_graph, "_get_wsi_generator", return_value=fake_gen), \
         patch.object(job_graph, "evaluate_wizard_policy", return_value=_allow()):
        result = job_graph.bigfive_node(_enriched_state())

    fake_gen.extract_bigfive.assert_called_once()
    assert result["bigfive_profile"] is not None
    assert result["pending_human_confirmation"] is False
    assert result["requires_approval"] is False
    history = result["policy_decisions"]
    assert len(history) == 1
    assert history[0]["stage"] == "bigfive"
    assert history[0]["policy_decision"] == "allow"


def test_bigfive_node_hitl_proceeds_but_marks_pending_confirmation():
    from app.domains.job_creation import graph as job_graph

    fake_bigfive = SimpleNamespace(
        model_dump=lambda: {"openness": {"score": 3, "evidence": "neutral"}}
    )
    fake_gen = MagicMock()
    fake_gen.extract_bigfive.return_value = fake_bigfive
    fake_gen.rank_traits.return_value = []

    with patch.object(job_graph, "_get_wsi_generator", return_value=fake_gen), \
         patch.object(job_graph, "evaluate_wizard_policy", return_value=_hitl()):
        result = job_graph.bigfive_node(_enriched_state())

    fake_gen.extract_bigfive.assert_called_once()
    assert result["pending_human_confirmation"] is True
    assert result["requires_approval"] is True
    payload = result["ws_stage_payload"]["data"]
    assert payload["policy_decision"]["policy_decision"] == "hitl_required"


def test_bigfive_node_deny_short_circuits_without_calling_llm():
    from app.domains.job_creation import graph as job_graph

    fake_gen = MagicMock()  # would raise if called

    with patch.object(job_graph, "_get_wsi_generator", return_value=fake_gen), \
         patch.object(job_graph, "evaluate_wizard_policy", return_value=_deny("tenant blocked")):
        result = job_graph.bigfive_node(_enriched_state())

    fake_gen.extract_bigfive.assert_not_called()
    fake_gen.rank_traits.assert_not_called()
    assert "Big Five bloqueado" in result["error"]
    assert result["requires_approval"] is False
    payload = result["ws_stage_payload"]["data"]
    assert payload["policy_blocked"] is True
    assert payload["policy_decision"]["policy_decision"] == "deny"
    assert payload["policy_decision"]["rationale"] == "tenant blocked"


# ---------------------------------------------------------------------------
# wsi_questions_node
# ---------------------------------------------------------------------------

def test_wsi_questions_node_allow_invokes_generator():
    from app.domains.job_creation import graph as job_graph

    fake_q = SimpleNamespace(model_dump=lambda: {"question": "Tell me about a project"})
    fake_gen = MagicMock()
    fake_gen.generate_questions.return_value = [fake_q]

    with patch.object(job_graph, "_get_wsi_generator", return_value=fake_gen), \
         patch.object(job_graph, "evaluate_wizard_policy", return_value=_allow()):
        result = job_graph.wsi_questions_node(_enriched_state())

    fake_gen.generate_questions.assert_called_once()
    assert result["pending_human_confirmation"] is False
    history = result["policy_decisions"]
    assert history[-1]["stage"] == "wsi_questions"
    assert history[-1]["policy_decision"] == "allow"


def test_wsi_questions_node_hitl_marks_pending_confirmation():
    from app.domains.job_creation import graph as job_graph

    fake_q = SimpleNamespace(model_dump=lambda: {"question": "Tell me about a project"})
    fake_gen = MagicMock()
    fake_gen.generate_questions.return_value = [fake_q]

    with patch.object(job_graph, "_get_wsi_generator", return_value=fake_gen), \
         patch.object(job_graph, "evaluate_wizard_policy", return_value=_hitl()):
        result = job_graph.wsi_questions_node(_enriched_state())

    assert result["pending_human_confirmation"] is True
    payload = result["ws_stage_payload"]["data"]
    assert payload["policy_decision"]["policy_decision"] == "hitl_required"


def test_wsi_questions_node_deny_short_circuits_and_skips_generator():
    from app.domains.job_creation import graph as job_graph

    fake_gen = MagicMock()

    with patch.object(job_graph, "_get_wsi_generator", return_value=fake_gen), \
         patch.object(job_graph, "evaluate_wizard_policy", return_value=_deny("WSI gen blocked")):
        result = job_graph.wsi_questions_node(_enriched_state())

    fake_gen.generate_questions.assert_not_called()
    assert result["wsi_questions"] == []
    assert "WSI gen blocked" in result["error"]
    payload = result["ws_stage_payload"]["data"]
    assert payload["policy_blocked"] is True
    assert payload["policy_decision"]["policy_decision"] == "deny"


# ---------------------------------------------------------------------------
# publish_node
# ---------------------------------------------------------------------------

def _publish_state() -> dict:
    return {
        "workspace_id": 42,
        "user_id": "recruiter-1",
        "jd_quality_score": 90.0,
        "screening_mode": "compact",
        "publish_platforms": ["website"],
        "sourcing_mode": "local",
        "wsi_questions": [{"question": "q1"}],
        "eligibility_questions": [],
        "jd_enriched": {
            "titulo_padronizado": "PM",
            "about_role": "Liderar squad",
        },
        "stage_history": [],
    }


def _fake_api():
    from app.domains.job_creation.api_client import APIResponse

    api = MagicMock()
    api.create_job.return_value = APIResponse(
        success=True, data={"data": {"id": 999, "uid": "job-uid-999"}}
    )
    api.save_screening_config.return_value = APIResponse(success=True, data={})
    api.publish_job.return_value = APIResponse(success=True, data={})
    api.get_share_link.return_value = APIResponse(
        success=True, data={"share_link": "https://lia.example/jobs/999"}
    )
    return api


def test_publish_node_allow_calls_rails_api():
    from app.domains.job_creation import graph as job_graph

    api = _fake_api()
    with patch.object(job_graph, "_get_api_client", return_value=api), \
         patch.object(job_graph, "evaluate_wizard_policy", return_value=_allow()):
        result = job_graph.publish_node(_publish_state())

    api.create_job.assert_called_once()
    api.publish_job.assert_called_once()
    assert result["job_id"] == 999
    assert result["pending_human_confirmation"] is False
    history = result["policy_decisions"]
    assert history[-1]["stage"] == "publish"
    assert history[-1]["policy_decision"] == "allow"


def test_publish_node_hitl_pauses_without_calling_rails_api():
    """HITL_REQUIRED is a side-effect gate for publish: the wizard must
    pause WITHOUT calling Rails so no job is created or made public until
    the recruiter explicitly confirms on a later turn."""
    from app.domains.job_creation import graph as job_graph

    api = _fake_api()
    with patch.object(job_graph, "_get_api_client", return_value=api), \
         patch.object(job_graph, "evaluate_wizard_policy", return_value=_hitl()):
        result = job_graph.publish_node(_publish_state())

    api.create_job.assert_not_called()
    api.save_screening_config.assert_not_called()
    api.publish_job.assert_not_called()
    api.get_share_link.assert_not_called()
    assert result.get("job_id") is None
    assert result["pending_human_confirmation"] is True
    assert result["requires_approval"] is True
    payload = result["ws_stage_payload"]["data"]
    assert payload["policy_decision"]["policy_decision"] == "hitl_required"
    assert payload["policy_pending_confirmation"] is True


def test_publish_node_hitl_with_explicit_confirmation_proceeds():
    """Once the recruiter explicitly confirms (``policy_confirmed_publish``),
    the wizard re-enters publish and the Rails calls fire."""
    from app.domains.job_creation import graph as job_graph

    api = _fake_api()
    state = _publish_state()
    state["policy_confirmed_publish"] = True
    with patch.object(job_graph, "_get_api_client", return_value=api), \
         patch.object(job_graph, "evaluate_wizard_policy", return_value=_hitl()):
        result = job_graph.publish_node(state)

    api.create_job.assert_called_once()
    api.publish_job.assert_called_once()
    assert result["job_id"] == 999
    history = result["policy_decisions"]
    assert history[-1]["policy_decision"] == "hitl_required"


def test_publish_node_deny_does_not_call_rails_api():
    from app.domains.job_creation import graph as job_graph

    api = _fake_api()
    with patch.object(job_graph, "_get_api_client", return_value=api), \
         patch.object(job_graph, "evaluate_wizard_policy", return_value=_deny("publish blocked by policy")):
        result = job_graph.publish_node(_publish_state())

    api.create_job.assert_not_called()
    api.publish_job.assert_not_called()
    assert "publish blocked by policy" in result["error"]
    payload = result["ws_stage_payload"]["data"]
    assert payload["policy_blocked"] is True


# ---------------------------------------------------------------------------
# Audit emission picks up the policy_decisions blob
# ---------------------------------------------------------------------------

def test_publish_node_deny_emits_policy_block_audit_row():
    """A DENY at publish must emit a per-turn audit row immediately
    (the wizard never reaches `handoff_node` to emit the summary one)."""
    from app.domains.job_creation import graph as job_graph

    api = _fake_api()
    with patch.object(job_graph, "_get_api_client", return_value=api), \
         patch.object(job_graph, "evaluate_wizard_policy", return_value=_deny("publish blocked")), \
         patch.object(job_graph, "emit_policy_block_audit") as emit:
        job_graph.publish_node(_publish_state())

    assert emit.call_count == 1
    kwargs = emit.call_args.kwargs
    assert kwargs["stage"] == "publish"
    assert kwargs["decision"].decision.value == "deny"


def test_bigfive_node_deny_emits_policy_block_audit_row():
    from app.domains.job_creation import graph as job_graph

    fake_gen = MagicMock()
    with patch.object(job_graph, "_get_wsi_generator", return_value=fake_gen), \
         patch.object(job_graph, "evaluate_wizard_policy", return_value=_deny("bf blocked")), \
         patch.object(job_graph, "emit_policy_block_audit") as emit:
        job_graph.bigfive_node(_enriched_state())

    assert emit.call_count == 1
    assert emit.call_args.kwargs["stage"] == "bigfive"
    assert emit.call_args.kwargs["decision"].decision.value == "deny"


def test_wsi_questions_node_deny_emits_policy_block_audit_row():
    from app.domains.job_creation import graph as job_graph

    fake_gen = MagicMock()
    with patch.object(job_graph, "_get_wsi_generator", return_value=fake_gen), \
         patch.object(job_graph, "evaluate_wizard_policy", return_value=_deny("wsi blocked")), \
         patch.object(job_graph, "emit_policy_block_audit") as emit:
        job_graph.wsi_questions_node(_enriched_state())

    assert emit.call_count == 1
    assert emit.call_args.kwargs["stage"] == "wsi_questions"


def test_publish_node_hitl_pause_emits_policy_block_audit_row():
    """The HITL pause on publish (no Rails called) must also emit an
    audit row so AI Governance can replay why the wizard stalled."""
    from app.domains.job_creation import graph as job_graph

    api = _fake_api()
    with patch.object(job_graph, "_get_api_client", return_value=api), \
         patch.object(job_graph, "evaluate_wizard_policy", return_value=_hitl()), \
         patch.object(job_graph, "emit_policy_block_audit") as emit:
        job_graph.publish_node(_publish_state())

    assert emit.call_count == 1
    assert emit.call_args.kwargs["stage"] == "publish"
    assert emit.call_args.kwargs["decision"].decision.value == "hitl_required"


def test_publish_node_zero_quality_score_still_passes_score_to_gate():
    """Regression: a state with `jd_quality_score=0.0` must derive a real
    confidence score (0.0) and pass it to the gate so confidence-driven
    HITL kicks in. Truthiness check would silently coerce 0.0 to None."""
    from app.domains.job_creation import graph as job_graph

    api = _fake_api()
    captured = {}

    def _capture_decision(intent, state, *, score=None):
        captured["score"] = score
        return _allow()

    state = _publish_state()
    state["jd_quality_score"] = 0.0
    with patch.object(job_graph, "_get_api_client", return_value=api), \
         patch.object(job_graph, "evaluate_wizard_policy", side_effect=_capture_decision):
        job_graph.publish_node(state)

    assert captured["score"] == 0.0


def test_publish_node_with_real_policy_gate_service_pauses_then_publishes():
    """End-to-end at the routing layer:
    a real ``PolicyGateService`` (backed by an in-memory engine that
    requires approval) pauses publish on turn 1 and lets it through on
    turn 2 once the recruiter has confirmed. Proves HITL is enforced
    without any direct mock of ``evaluate_wizard_policy``.
    """
    from app.domains.job_creation import graph as job_graph
    from app.domains.job_creation import policy_gate as pg
    from app.orchestrator.services.policy_gate_service import (
        PolicyGateService, PolicyResult,
    )

    class _StubEngine:
        async def validate_request(self, *, intent, user_id, context):
            # Simulate a policy that allows publish but with mandatory
            # human approval — i.e. the canonical HITL_REQUIRED path.
            return {
                "allowed": True,
                "reason": "publish requires HR approval per tenant policy",
                "constraints": {"requires_approval": True},
            }

    real_gate = PolicyGateService(policy_engine=_StubEngine())

    api = _fake_api()
    state = _publish_state()

    pg._reset_default_gate_for_tests()
    with patch.object(job_graph, "_get_api_client", return_value=api), \
         patch.object(pg, "_get_default_gate", return_value=real_gate):
        # --- Turn 1: gate returns HITL → wizard pauses, no Rails ---
        result_pause = job_graph.publish_node(state)

    api.create_job.assert_not_called()
    api.publish_job.assert_not_called()
    assert result_pause["pending_human_confirmation"] is True
    assert result_pause["requires_approval"] is True
    assert result_pause.get("job_id") is None
    last_decision = result_pause["policy_decisions"][-1]
    assert last_decision["policy_decision"] == "hitl_required"
    assert "HR approval" in last_decision["rationale"]

    # --- Turn 2: recruiter confirms → wizard re-enters publish, Rails fires ---
    confirmed_state = {**state, "policy_confirmed_publish": True}
    with patch.object(job_graph, "_get_api_client", return_value=api), \
         patch.object(pg, "_get_default_gate", return_value=real_gate):
        result_publish = job_graph.publish_node(confirmed_state)

    api.create_job.assert_called_once()
    api.publish_job.assert_called_once()
    assert result_publish["job_id"] == 999


def test_publish_node_with_real_policy_gate_service_denies_blocks_rails():
    """A real ``PolicyGateService`` whose engine returns ``allowed=False``
    must short-circuit the publish_node — no Rails calls, error surfaced,
    audit row records the deny."""
    from app.domains.job_creation import graph as job_graph
    from app.domains.job_creation import policy_gate as pg
    from app.orchestrator.services.policy_gate_service import PolicyGateService

    class _DenyEngine:
        async def validate_request(self, *, intent, user_id, context):
            return {
                "allowed": False,
                "reason": "tenant publish quota exhausted",
                "constraints": {},
            }

    real_gate = PolicyGateService(policy_engine=_DenyEngine())
    api = _fake_api()

    pg._reset_default_gate_for_tests()
    with patch.object(job_graph, "_get_api_client", return_value=api), \
         patch.object(pg, "_get_default_gate", return_value=real_gate):
        result = job_graph.publish_node(_publish_state())

    api.create_job.assert_not_called()
    api.publish_job.assert_not_called()
    assert "tenant publish quota exhausted" in result["error"]
    payload = result["ws_stage_payload"]["data"]
    assert payload["policy_blocked"] is True
    assert payload["policy_decision"]["policy_decision"] == "deny"


def test_emit_audit_includes_policy_decisions_blob():
    from app.domains.job_creation import compliance as comp
    from unittest.mock import AsyncMock

    log_mock = AsyncMock()
    state = {
        "workspace_id": 42,
        "raw_input": "Quero um PM senior",
        "jd_enriched": {"about_role": "PM senior"},
        "wsi_questions": [{"question": "q1"}],
        "seniority_resolved": "senior",
        "screening_mode": "compact",
        "jd_quality_score": 78.0,
        "job_id": 999,
        "stage_history": [],
        "policy_decisions": [
            {
                "stage": "bigfive",
                "intent": "wizard.set_protected_criteria",
                "policy_decision": "allow",
                "confidence_band": "high",
                "rationale": "allowed",
                "requires_human_confirmation": False,
            },
            {
                "stage": "publish",
                "intent": "wizard.publish_job",
                "policy_decision": "hitl_required",
                "confidence_band": "medium",
                "rationale": "needs HR sign-off",
                "requires_human_confirmation": True,
            },
        ],
    }

    with patch("app.shared.compliance.audit_service.AuditService") as svc_cls, \
         patch("app.domains.job_creation.compliance._run_async", lambda coro: coro.close()):
        svc_cls.return_value.log_decision = log_mock
        comp.emit_job_creation_audit(state)

    assert svc_cls.return_value.log_decision.call_count == 1
    kwargs = svc_cls.return_value.log_decision.call_args.kwargs
    reasoning = kwargs["reasoning"]
    blob = next(
        (r for r in reasoning if isinstance(r, dict) and "policy_decisions" in r),
        None,
    )
    assert blob is not None
    decisions = blob["policy_decisions"]
    assert {d["stage"] for d in decisions} == {"bigfive", "publish"}
    assert any(d["policy_decision"] == "hitl_required" for d in decisions)
