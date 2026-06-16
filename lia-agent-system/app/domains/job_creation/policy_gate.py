"""
Wizard Policy Gate — bridges JobCreationGraph with PolicyGateService +
ConfidencePolicyService.

Resolves audit findings **N-09** ("`JobCreationGraph` does not consult any
central policy gate") and **M-06** ("`ConfidencePolicyService` is wired
nowhere in the wizard"). Every sensitive wizard operation funnels through
``evaluate(...)`` here, which returns a single canonical decision in one of
three values:

  * ``ALLOW``         — proceed silently with the operation.
  * ``HITL_REQUIRED`` — recruiter must explicitly confirm before the
    wizard advances. For *suggestion-style* nodes (Big Five extraction,
    WSI question generation) the underlying LLM call still runs so the
    recruiter has something concrete to review/approve via the existing
    ``requires_approval`` gate. For *side-effecting* nodes
    (``publish_node`` → Rails API) the irreversible action MUST be
    skipped — the wizard pauses with ``pending_human_confirmation`` and
    only resumes after the recruiter explicitly confirms (a separate
    confirm turn re-enters publish with policy override).
  * ``DENY``          — short-circuit the node: do not perform the LLM /
    API call, surface an error to the recruiter and let the existing
    routing terminate the wizard turn.

Two collaborators are wrapped:

  * :class:`app.orchestrator.services.policy_gate_service.PolicyGateService`
    — canonical async ``validate(intent, user_id, context)`` API.
  * :class:`app.domains.cv_screening.services.confidence_policy_service.ConfidencePolicyService`
    — converts a confidence score into a HITL action (silent vs. recruiter
    confirmation).

The wizard nodes are sync, so we run the async ``validate`` call on a
worker thread with a fresh event loop. Failures and timeouts default to a
``DENY`` (fail-closed for high-risk for employment flows). The single
exception is when the gate cannot be constructed at all (e.g., dev/test
environments without a configured ``PolicyEngine``) — in that case we
fail-open with a ``rationale`` that makes the bypass auditable.

A feature flag ``LIA_WIZARD_POLICY_GATE_ENABLED`` (default ``true``)
controls whether the gate runs in the first place. Setting it to ``false``
returns ``ALLOW`` immediately and is intended **only** for the rollback
plan documented in the task definition.
"""

from __future__ import annotations

import asyncio
import logging
import os
import threading
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Canonical wizard intents — kept here so the graph never invents new strings.
# ---------------------------------------------------------------------------

class WizardIntent(StrEnum):
    """Intents the wizard sends to the policy gate.

    These names are stable contract: ``PolicyEngine`` may grow tenant-level
    rules keyed by exactly these intents. Renaming any of these is a
    breaking change for the audit trail.
    """

    SET_PROTECTED_CRITERIA = "wizard.set_protected_criteria"
    GENERATE_WSI = "wizard.generate_wsi"
    PUBLISH_JOB = "wizard.publish_job"


class PolicyDecision(StrEnum):
    """Three-valued result for any wizard policy evaluation."""

    ALLOW = "allow"
    HITL_REQUIRED = "hitl_required"
    DENY = "deny"


# ---------------------------------------------------------------------------
# Feature flag — defaults to ON so EU AI Act high-risk flows always have the gate.
# ---------------------------------------------------------------------------

_FLAG_ENV = "LIA_WIZARD_POLICY_GATE_ENABLED"
_PROD_ENV_KEYS = ("LIA_ENV", "ENVIRONMENT", "RAILS_ENV", "PYTHON_ENV")
_PROD_VALUES = {"production", "prod", "live", "staging"}


def _flag_enabled() -> bool:
    raw = (os.environ.get(_FLAG_ENV) or "true").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def _is_production_env() -> bool:
    """Detect a production-like environment so we can flip the
    "gate unavailable" branch from fail-open (dev/test) to fail-closed
    (prod). Treats staging as production for the safer side."""
    for key in _PROD_ENV_KEYS:
        val = (os.environ.get(key) or "").strip().lower()
        if val in _PROD_VALUES:
            return True
    return False


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class WizardPolicyResult:
    """Canonical decision returned by the wizard policy gate.

    Attributes:
        decision: One of ``ALLOW`` / ``HITL_REQUIRED`` / ``DENY``.
        rationale: Human-readable explanation surfaced both to the recruiter
            (when applicable) and to the audit row.
        confidence_band: Coarse band derived from ``score``:
            ``high`` (>=0.85), ``medium`` (0.70..0.85), ``low`` (0.50..0.70),
            ``very_low`` (<0.50), or ``n/a`` when no score was provided.
        intent: The intent that was evaluated.
        requires_human_confirmation: Convenience boolean — ``True`` iff the
            decision is ``HITL_REQUIRED``.
        raw_constraints: Constraints returned by the underlying
            ``PolicyResult`` (forwarded for downstream use).
    """

    decision: PolicyDecision
    rationale: str
    confidence_band: str = "n/a"
    intent: str = ""
    requires_human_confirmation: bool = False
    raw_constraints: Dict[str, Any] = field(default_factory=dict)

    def to_audit_dict(self, *, stage: str) -> Dict[str, Any]:
        """Serialise the decision for the wizard audit row."""
        return {
            "stage": stage,
            "intent": self.intent,
            "policy_decision": self.decision.value,
            "confidence_band": self.confidence_band,
            "rationale": self.rationale,
            "requires_human_confirmation": self.requires_human_confirmation,
        }


# ---------------------------------------------------------------------------
# Async-from-sync runner
# ---------------------------------------------------------------------------

def _run_coro_sync(coro, *, timeout: float = 5.0) -> Any:
    """Execute an async coroutine from sync context with a fresh event loop
    on a worker thread. Used because wizard nodes are sync and
    ``PolicyGateService.validate`` is async.

    Raises ``TimeoutError`` if the coroutine doesn't complete in time;
    re-raises whatever the coroutine raised otherwise.
    """
    result_box: Dict[str, Any] = {"value": None, "error": None}

    def _runner() -> None:
        try:
            result_box["value"] = asyncio.run(coro)
        except BaseException as exc:  # pragma: no cover — re-raised below
            result_box["error"] = exc

    t = threading.Thread(target=_runner, daemon=True)
    t.start()
    t.join(timeout=timeout)
    if t.is_alive():
        raise TimeoutError(
            f"PolicyGateService.validate timed out after {timeout:.1f}s"
        )
    if result_box["error"] is not None:
        raise result_box["error"]
    return result_box["value"]


# ---------------------------------------------------------------------------
# Confidence band + HITL split
# ---------------------------------------------------------------------------

def _confidence_band(score: Optional[float]) -> str:
    if score is None:
        return "n/a"
    try:
        s = float(score)
    except (TypeError, ValueError):
        return "n/a"
    if s >= 0.85:
        return "high"
    if s >= 0.70:
        return "medium"
    if s >= 0.50:
        return "low"
    return "very_low"


def _silent_or_confirm_from_score(score: Optional[float]) -> bool:
    """Return ``True`` if the recruiter must explicitly confirm before the
    wizard advances, ``False`` if the HITL can be silent (auto-confirm).

    Delegates to ``ConfidencePolicyService.get_action_for_confidence``:
      * ``APPLY_SILENT`` / ``APPLY_NOTIFY`` → silent HITL → ``False``
      * ``ASK_USER`` / ``ALERT_CONFLICT``  → confirmation HITL → ``True``

    When ``score is None`` we default to confirmation HITL — the safer
    side for a high-risk for employment flow.
    """
    if score is None:
        return True
    try:
        from app.domains.cv_screening.services.confidence_policy_service import (
            ConfidenceAction, confidence_policy_service,
        )

        action = confidence_policy_service.get_action_for_confidence(float(score))
        return action not in {
            ConfidenceAction.APPLY_SILENT,
            ConfidenceAction.APPLY_NOTIFY,
        }
    except Exception as exc:  # pragma: no cover — defensive
        logger.warning(
            "[WizardPolicyGate] ConfidencePolicyService unavailable; "
            "defaulting to recruiter confirmation: %s", exc,
        )
        return True


# ---------------------------------------------------------------------------
# Default gate construction (lazy singleton)
# ---------------------------------------------------------------------------

_default_gate: Any = None


def _build_default_gate() -> Any:
    """Construct a default ``PolicyGateService`` for callers that don't
    inject one. Returns ``None`` if construction fails (e.g., test envs
    without a wired orchestrator). The caller decides what to do then.
    """
    # WT-2022 P3.1 (2026-05-21): migrated V1 PolicyEngine -> V2 PolicyEngineService
    # via PolicyGateService(policy_engine=...). PolicyGateService auto-detects
    # engine_version="v2" pelo metodo canonical .evaluate.
    try:
        from app.domains.policy.services.policy_engine_service import (
            PolicyEngineService,
        )
        from app.orchestrator.services.policy_gate_service import PolicyGateService

        return PolicyGateService(policy_engine=PolicyEngineService())
    except Exception as exc:  # pragma: no cover — defensive
        logger.warning(
            "[WizardPolicyGate] Failed to build default PolicyGateService: %s", exc,
        )
        return None


def _get_default_gate() -> Any:
    global _default_gate
    if _default_gate is None:
        _default_gate = _build_default_gate()
    return _default_gate


def _reset_default_gate_for_tests() -> None:
    """Test hook — never call from production code."""
    global _default_gate
    _default_gate = None


# ---------------------------------------------------------------------------
# Tenant + user resolution from wizard state
# ---------------------------------------------------------------------------

def _resolve_company_id(state: Dict[str, Any]) -> str:
    raw = state.get("company_id") or state.get("workspace_id") or ""
    return str(raw) if raw else ""


def _resolve_user_id(state: Dict[str, Any]) -> str:
    raw = state.get("user_id") or state.get("recruiter_id") or "system"
    return str(raw)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def evaluate(
    intent: str,
    state: Dict[str, Any],
    *,
    score: Optional[float] = None,
    gate_service: Any = None,
    flag_override: Optional[bool] = None,
) -> WizardPolicyResult:
    """Evaluate one wizard operation against the canonical policy gate.

    Args:
        intent: Canonical wizard intent (see :class:`WizardIntent`).
        state: Current ``JobCreationState`` (used to extract tenant + user).
        score: Optional confidence score in ``[0.0, 1.0]``. When provided,
            ``ConfidencePolicyService`` decides whether HITL must be
            confirmed by the recruiter or can be silent.
        gate_service: Override ``PolicyGateService`` (tests).
        flag_override: Force the feature flag for this call (tests).

    Returns:
        :class:`WizardPolicyResult` — never raises. Failures map to
        ``DENY`` (fail-closed) with the exception type in the rationale,
        except when the gate cannot be constructed at all (which maps to
        ``ALLOW`` with an explicit rationale so the bypass is auditable).
    """
    enabled = flag_override if flag_override is not None else _flag_enabled()
    band = _confidence_band(score)

    if not enabled:
        return WizardPolicyResult(
            decision=PolicyDecision.ALLOW,
            rationale="policy gate disabled by feature flag",
            confidence_band=band,
            intent=intent,
        )

    gate = gate_service if gate_service is not None else _get_default_gate()
    if gate is None:
        # In production-like environments (LIA_ENV/ENVIRONMENT/RAILS_ENV =
        # production|staging) we MUST fail-closed (DENY) — bypassing the
        # central policy gate in a high-risk for employment flow violates
        # the EU AI Act audit contract and is non-negotiable. In dev/test
        # we fail-open with a clearly-marked rationale so CI runs without
        # an orchestrator wired remain useful.
        if _is_production_env():
            logger.error(
                "[WizardPolicyGate] PolicyGateService unavailable in "
                "production-like env — failing CLOSED (DENY).",
            )
            return WizardPolicyResult(
                decision=PolicyDecision.DENY,
                rationale=(
                    "policy gate service unavailable in production "
                    "(fail-closed) — refusing protected wizard action"
                ),
                confidence_band=band,
                intent=intent,
                raw_constraints={"error": True, "fail_closed": True},
            )
        return WizardPolicyResult(
            decision=PolicyDecision.ALLOW,
            rationale="policy gate service unavailable (fail-open, non-prod)",
            confidence_band=band,
            intent=intent,
        )

    company_id = _resolve_company_id(state)
    user_id = _resolve_user_id(state)
    context: Dict[str, Any] = {
        "company_id": company_id,
        "tenant_id": company_id,
    }

    try:
        validate_result = _run_coro_sync(
            gate.validate(intent=intent, user_id=user_id, context=context)
        )
    except Exception as exc:
        logger.warning(
            "[WizardPolicyGate] validate raised; defaulting to DENY: %s", exc,
        )
        return WizardPolicyResult(
            decision=PolicyDecision.DENY,
            rationale=f"policy gate error: {type(exc).__name__}: {exc}",
            confidence_band=band,
            intent=intent,
            raw_constraints={"error": True},
        )

    if not getattr(validate_result, "allowed", False):
        return WizardPolicyResult(
            decision=PolicyDecision.DENY,
            rationale=getattr(validate_result, "reason", "") or "policy denied",
            confidence_band=band,
            intent=intent,
            raw_constraints=dict(getattr(validate_result, "constraints", {}) or {}),
        )

    # Allowed — but maybe HITL is required because of an explicit constraint
    # OR because the LLM confidence sits below the silent-apply threshold.
    constraint_requires = bool(getattr(validate_result, "requires_approval", False))
    score_requires = _silent_or_confirm_from_score(score) if score is not None else False
    requires_approval = constraint_requires or score_requires

    if requires_approval:
        rationale = getattr(validate_result, "reason", "") or (
            f"confidence={float(score):.2f} band={band} requires recruiter confirmation"
            if score is not None
            else "policy requires approval"
        )
        return WizardPolicyResult(
            decision=PolicyDecision.HITL_REQUIRED,
            rationale=rationale,
            confidence_band=band,
            intent=intent,
            requires_human_confirmation=True,
            raw_constraints=dict(getattr(validate_result, "constraints", {}) or {}),
        )

    return WizardPolicyResult(
        decision=PolicyDecision.ALLOW,
        rationale=getattr(validate_result, "reason", "") or "allowed",
        confidence_band=band,
        intent=intent,
        raw_constraints=dict(getattr(validate_result, "constraints", {}) or {}),
    )


# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------

def record_decision_in_state(
    state: Dict[str, Any],
    decision: WizardPolicyResult,
    *,
    stage: str,
) -> None:
    """Append the gate decision to ``state["policy_decisions"]`` so the
    audit emission at handoff captures the per-turn rationale.

    Mutates ``state`` in place — the wizard nodes read the current state
    object as a dict to extend it, which mirrors how the rest of the
    compliance helpers work.
    """
    history: List[Dict[str, Any]] = list(state.get("policy_decisions") or [])
    history.append(decision.to_audit_dict(stage=stage))
    state["policy_decisions"] = history
