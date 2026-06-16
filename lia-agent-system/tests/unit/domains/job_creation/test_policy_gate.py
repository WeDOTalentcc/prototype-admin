"""Unit tests for ``app.domains.job_creation.policy_gate``.

Covers the three canonical decisions (ALLOW / HITL_REQUIRED / DENY), the
feature flag, the confidence-driven HITL split (M-06), the fail-safe
behaviour when the underlying ``PolicyGateService`` raises or is missing,
and the audit-friendly serialisation of the result.
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_gate(*, allowed: bool, requires_approval: bool = False, reason: str = "") -> MagicMock:
    """Build a fake ``PolicyGateService`` whose ``validate`` coroutine
    returns a ``PolicyResult``-shaped object so the wizard policy gate can
    consume it without touching the real engine.
    """
    from app.orchestrator.services.policy_gate_service import PolicyResult

    async def _validate(*, intent: str, user_id: str, context):
        return PolicyResult(
            allowed=allowed,
            reason=reason,
            constraints={"requires_approval": requires_approval} if requires_approval else {},
            intent=intent,
            user_id=user_id,
        )

    gate = MagicMock()
    gate.validate = _validate
    return gate


@pytest.fixture(autouse=True)
def _reset_default_gate_for_tests():
    from app.domains.job_creation import policy_gate

    policy_gate._reset_default_gate_for_tests()
    yield
    policy_gate._reset_default_gate_for_tests()


@pytest.fixture(autouse=True)
def _ensure_flag_on(monkeypatch):
    monkeypatch.setenv("LIA_WIZARD_POLICY_GATE_ENABLED", "true")
    yield


# ---------------------------------------------------------------------------
# Confidence band
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "score,expected_band",
    [
        (0.95, "high"),
        (0.85, "high"),
        (0.80, "medium"),
        (0.70, "medium"),
        (0.55, "low"),
        (0.50, "low"),
        (0.30, "very_low"),
        (None, "n/a"),
        ("not-a-number", "n/a"),
    ],
)
def test_confidence_band_buckets(score, expected_band):
    from app.domains.job_creation.policy_gate import _confidence_band

    assert _confidence_band(score) == expected_band


# ---------------------------------------------------------------------------
# Feature flag
# ---------------------------------------------------------------------------

def test_disabled_flag_returns_allow_without_invoking_gate(monkeypatch):
    """When the rollback flag is OFF, evaluate must short-circuit ALLOW
    and never construct or call any gate service."""
    from app.domains.job_creation import policy_gate
    from app.domains.job_creation.policy_gate import (
        PolicyDecision, WizardIntent, evaluate,
    )

    monkeypatch.setenv("LIA_WIZARD_POLICY_GATE_ENABLED", "false")
    sentinel_gate = MagicMock()  # would explode if called
    sentinel_gate.validate.side_effect = AssertionError("must not be called")

    result = evaluate(
        WizardIntent.PUBLISH_JOB,
        state={"workspace_id": 1, "user_id": "u1"},
        gate_service=sentinel_gate,
    )
    assert result.decision == PolicyDecision.ALLOW
    assert "feature flag" in result.rationale
    sentinel_gate.validate.assert_not_called()


def test_explicit_flag_override_wins_over_env(monkeypatch):
    from app.domains.job_creation.policy_gate import (
        PolicyDecision, WizardIntent, evaluate,
    )

    monkeypatch.setenv("LIA_WIZARD_POLICY_GATE_ENABLED", "true")
    result = evaluate(
        WizardIntent.GENERATE_WSI,
        state={"workspace_id": 1},
        gate_service=_make_gate(allowed=False, reason="forbidden"),
        flag_override=False,
    )
    assert result.decision == PolicyDecision.ALLOW


# ---------------------------------------------------------------------------
# ALLOW / DENY / HITL paths
# ---------------------------------------------------------------------------

def test_evaluate_returns_allow_when_gate_permits():
    from app.domains.job_creation.policy_gate import (
        PolicyDecision, WizardIntent, evaluate,
    )

    result = evaluate(
        WizardIntent.PUBLISH_JOB,
        state={"workspace_id": 42, "user_id": "u1"},
        gate_service=_make_gate(allowed=True),
    )
    assert result.decision == PolicyDecision.ALLOW
    assert result.intent == WizardIntent.PUBLISH_JOB
    assert result.requires_human_confirmation is False


def test_evaluate_returns_deny_when_gate_refuses():
    from app.domains.job_creation.policy_gate import (
        PolicyDecision, WizardIntent, evaluate,
    )

    result = evaluate(
        WizardIntent.SET_PROTECTED_CRITERIA,
        state={"workspace_id": 42, "user_id": "u1"},
        gate_service=_make_gate(allowed=False, reason="quota exceeded"),
    )
    assert result.decision == PolicyDecision.DENY
    assert result.rationale == "quota exceeded"
    assert result.confidence_band == "n/a"


def test_evaluate_returns_hitl_when_constraint_requires_approval():
    """Allowed but `requires_approval=True` ⇒ HITL_REQUIRED."""
    from app.domains.job_creation.policy_gate import (
        PolicyDecision, WizardIntent, evaluate,
    )

    result = evaluate(
        WizardIntent.PUBLISH_JOB,
        state={"workspace_id": 42, "user_id": "u1"},
        gate_service=_make_gate(allowed=True, requires_approval=True, reason="needs HR sign-off"),
    )
    assert result.decision == PolicyDecision.HITL_REQUIRED
    assert result.requires_human_confirmation is True
    assert result.rationale == "needs HR sign-off"


# ---------------------------------------------------------------------------
# ConfidencePolicyService split (M-06)
# ---------------------------------------------------------------------------

def test_high_confidence_keeps_silent_hitl():
    """Score >= 0.85 must NOT trigger recruiter confirmation by itself."""
    from app.domains.job_creation.policy_gate import (
        PolicyDecision, WizardIntent, evaluate,
    )

    result = evaluate(
        WizardIntent.GENERATE_WSI,
        state={"workspace_id": 1, "user_id": "u1"},
        gate_service=_make_gate(allowed=True),
        score=0.92,
    )
    assert result.decision == PolicyDecision.ALLOW
    assert result.confidence_band == "high"


def test_zero_confidence_score_is_treated_as_low_not_missing():
    """Regression: ``jd_quality_score == 0.0`` is a *valid* score (means
    "no quality at all"), not a missing value. The gate must derive the
    ``very_low`` band and force recruiter confirmation, not silently
    skip the confidence-driven HITL escalation as if score were ``None``."""
    from app.domains.job_creation.policy_gate import (
        PolicyDecision, WizardIntent, evaluate,
    )

    result = evaluate(
        WizardIntent.PUBLISH_JOB,
        state={"workspace_id": 1, "user_id": "u1"},
        gate_service=_make_gate(allowed=True),
        score=0.0,
    )
    assert result.confidence_band == "very_low"
    assert result.decision == PolicyDecision.HITL_REQUIRED
    assert result.requires_human_confirmation is True


def test_low_confidence_forces_hitl_required_via_confidence_service():
    """Score below `APPLY_NOTIFY` threshold must lift ALLOW into
    HITL_REQUIRED because the recruiter must explicitly confirm."""
    from app.domains.job_creation.policy_gate import (
        PolicyDecision, WizardIntent, evaluate,
    )

    result = evaluate(
        WizardIntent.GENERATE_WSI,
        state={"workspace_id": 1, "user_id": "u1"},
        gate_service=_make_gate(allowed=True),
        score=0.55,
    )
    assert result.decision == PolicyDecision.HITL_REQUIRED
    assert result.confidence_band == "low"
    assert "confidence=" in result.rationale


# ---------------------------------------------------------------------------
# Fail-safe behaviour
# ---------------------------------------------------------------------------

def test_validate_exception_results_in_deny():
    """If the gate raises, we fail closed (DENY) with the exception type
    in the rationale so the audit row makes the cause traceable."""
    from app.domains.job_creation.policy_gate import (
        PolicyDecision, WizardIntent, evaluate,
    )

    async def _boom(**kwargs):
        raise RuntimeError("policy DB unreachable")

    gate = MagicMock()
    gate.validate = _boom

    result = evaluate(
        WizardIntent.PUBLISH_JOB,
        state={"workspace_id": 42, "user_id": "u1"},
        gate_service=gate,
    )
    assert result.decision == PolicyDecision.DENY
    assert "RuntimeError" in result.rationale
    assert result.raw_constraints == {"error": True}


def test_missing_gate_service_fails_open_in_dev(monkeypatch):
    """In dev/test environments (no production env vars), a missing gate
    must fail OPEN so CI runs without an orchestrator stay useful, but
    the rationale must clearly mark the bypass for the audit row."""
    from app.domains.job_creation import policy_gate
    from app.domains.job_creation.policy_gate import (
        PolicyDecision, WizardIntent, evaluate,
    )

    for key in ("LIA_ENV", "ENVIRONMENT", "RAILS_ENV", "PYTHON_ENV"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(policy_gate, "_get_default_gate", lambda: None)

    result = evaluate(
        WizardIntent.PUBLISH_JOB,
        state={"workspace_id": 42, "user_id": "u1"},
    )
    assert result.decision == PolicyDecision.ALLOW
    assert "unavailable" in result.rationale
    assert "non-prod" in result.rationale


@pytest.mark.parametrize(
    "env_key,env_val",
    [
        ("LIA_ENV", "production"),
        ("ENVIRONMENT", "production"),
        ("RAILS_ENV", "production"),
        ("LIA_ENV", "staging"),
    ],
)
def test_missing_gate_service_fails_closed_in_production(monkeypatch, env_key, env_val):
    """In production-like envs the bypass branch is forbidden. A missing
    gate must DENY the protected wizard action so we cannot accidentally
    publish without policy validation. Treats staging as production for
    the safer side."""
    from app.domains.job_creation import policy_gate
    from app.domains.job_creation.policy_gate import (
        PolicyDecision, WizardIntent, evaluate,
    )

    for key in ("LIA_ENV", "ENVIRONMENT", "RAILS_ENV", "PYTHON_ENV"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv(env_key, env_val)
    monkeypatch.setattr(policy_gate, "_get_default_gate", lambda: None)

    result = evaluate(
        WizardIntent.PUBLISH_JOB,
        state={"workspace_id": 42, "user_id": "u1"},
    )
    assert result.decision == PolicyDecision.DENY
    assert "fail-closed" in result.rationale
    assert result.raw_constraints.get("fail_closed") is True


# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------

def test_record_decision_appends_audit_dict_to_state():
    from app.domains.job_creation.policy_gate import (
        PolicyDecision, WizardIntent, WizardPolicyResult,
        record_decision_in_state,
    )

    state: dict = {}
    decision = WizardPolicyResult(
        decision=PolicyDecision.HITL_REQUIRED,
        rationale="needs HR sign-off",
        confidence_band="medium",
        intent=WizardIntent.PUBLISH_JOB,
        requires_human_confirmation=True,
    )
    record_decision_in_state(state, decision, stage="publish")
    history = state["policy_decisions"]
    assert len(history) == 1
    entry = history[0]
    assert entry["stage"] == "publish"
    assert entry["intent"] == WizardIntent.PUBLISH_JOB
    assert entry["policy_decision"] == "hitl_required"
    assert entry["confidence_band"] == "medium"
    assert entry["rationale"] == "needs HR sign-off"
    assert entry["requires_human_confirmation"] is True


def test_record_decision_preserves_previous_history():
    from app.domains.job_creation.policy_gate import (
        PolicyDecision, WizardIntent, WizardPolicyResult,
        record_decision_in_state,
    )

    state: dict = {"policy_decisions": [{"stage": "bigfive", "policy_decision": "allow"}]}
    decision = WizardPolicyResult(
        decision=PolicyDecision.ALLOW,
        rationale="allowed",
        intent=WizardIntent.GENERATE_WSI,
    )
    record_decision_in_state(state, decision, stage="wsi_questions")
    assert [d.get("stage") for d in state["policy_decisions"]] == ["bigfive", "wsi_questions"]


# ---------------------------------------------------------------------------
# Tenant + user resolution
# ---------------------------------------------------------------------------

def test_evaluate_resolves_company_id_from_workspace_id():
    """The wizard state stores the tenant under `workspace_id`; the gate
    must coerce it into the `company_id` context key the engine expects."""
    from app.domains.job_creation.policy_gate import WizardIntent, evaluate

    captured: dict = {}

    async def _validate(*, intent: str, user_id: str, context):
        captured["intent"] = intent
        captured["user_id"] = user_id
        captured["context"] = dict(context)
        from app.orchestrator.services.policy_gate_service import PolicyResult
        return PolicyResult(allowed=True, intent=intent, user_id=user_id)

    gate = MagicMock()
    gate.validate = _validate

    evaluate(
        WizardIntent.PUBLISH_JOB,
        state={"workspace_id": 4242, "user_id": "recruiter-1"},
        gate_service=gate,
    )
    assert captured["user_id"] == "recruiter-1"
    assert captured["context"]["company_id"] == "4242"
    assert captured["context"]["tenant_id"] == "4242"
