"""
Canonical span names for Orchestrator V1 + V2 tracing.

Sprint I-D scaffolding — defines span name constants to be applied via
@trace_span decorators in Sprint III (when V2 migration starts).

Why constants instead of decorators in Sprint I?
- Sprint I is sensor-only (no production code changes)
- Adding decorators changes V1/V2 behavior (call stack, async timing)
- Constants are zero-risk metadata that lock in observability schema
- Sprint III applies the decorators using these constants

Usage (Sprint III):
    from app.orchestrator._observability import V1_SPANS, V2_SPANS
    from app.shared.observability.tracing import trace_span

    class Orchestrator:
        @trace_span(V1_SPANS.PROCESS_REQUEST)
        async def process_request(...):
            ...

Reference: ADR-019 — Orchestrator V1→V2 Consolidation
Doc: Documents/Python/MIGRATION_REGRESSION_BASELINE.md (contracts to preserve)
"""
from __future__ import annotations

from typing import Final


# ─────────────────────────────────────────────────────────────────────────────
# V1 Span Names (legacy orchestrator — orchestrator.py)
# These spans are emitted while V1 still exists (Sprints I-IV).
# Will be removed in Sprint V along with V1 itself.
# ─────────────────────────────────────────────────────────────────────────────
class V1Spans:
    """Span names for the deprecated V1 Orchestrator class."""

    # Public API
    PROCESS_REQUEST: Final[str] = "orchestrator.v1.process_request"
    PROCESS_REQUEST_WITH_MEMORY: Final[str] = "orchestrator.v1.process_request_with_memory"
    EXECUTE_PLAN: Final[str] = "orchestrator.v1.execute_plan"
    PROCESS_ANALYTICS_REQUEST: Final[str] = "orchestrator.v1.process_analytics_request"

    # Internal — to be extracted in Sprint II
    HANDLE_DIRECTLY: Final[str] = "orchestrator.v1.handle_directly"  # LIA-A04 fallback
    HANDLE_CV_RUBRIC: Final[str] = "orchestrator.v1.handle_cv_screening_with_rubric"

    # Heuristics — Sprint II.3
    IS_TECHNICAL_RESPONSE: Final[str] = "orchestrator.v1.is_technical_response"
    IS_CV_MATCHING_REQUEST: Final[str] = "orchestrator.v1.is_cv_matching_request"


V1_SPANS = V1Spans()


# ─────────────────────────────────────────────────────────────────────────────
# V2 Span Names (canonical orchestrator — main_orchestrator.py)
# These are the spans that will remain after Sprint V.
# ─────────────────────────────────────────────────────────────────────────────
class V2Spans:
    """Span names for the canonical V2 MainOrchestrator class."""

    # Top-level entry point
    PROCESS: Final[str] = "orchestrator.v2.process"

    # Phases (from main_orchestrator.py architecture)
    PHASE_0_PENDING_ACTION: Final[str] = "orchestrator.v2.phase_0_pending_action"
    PHASE_1_ACTION_EXECUTOR: Final[str] = "orchestrator.v2.phase_1_action_executor"
    PHASE_1_5_AGENTIC_LOOP: Final[str] = "orchestrator.v2.phase_1_5_agentic_loop"
    PHASE_2_VIA_ORCHESTRATOR: Final[str] = "orchestrator.v2.phase_2_via_orchestrator"

    # Compliance gates (run BEFORE phases)
    SECURITY_PATTERNS_CHECK: Final[str] = "orchestrator.v2.security_patterns_check"
    FAIRNESS_GUARD_CHECK: Final[str] = "orchestrator.v2.fairness_guard_check"

    # Internal helpers
    SETUP_CONVERSATION_MEMORY: Final[str] = "orchestrator.v2.setup_conversation_memory"
    TRY_CACHE_LOOKUP: Final[str] = "orchestrator.v2.try_cache_lookup"
    ROUTE_WITH_TENANT_LLM: Final[str] = "orchestrator.v2.route_with_tenant_llm"
    PERSIST_RESPONSE: Final[str] = "orchestrator.v2.persist_response"
    AUDIT_OUTPUT: Final[str] = "orchestrator.v2.audit_output"

    # Services (Sprint II — extracted from V1)
    PLAN_DETECT: Final[str] = "orchestrator.v2.services.plan.detect"
    PLAN_EXECUTE: Final[str] = "orchestrator.v2.services.plan.execute"
    FALLBACK_REACT_HANDLE: Final[str] = "orchestrator.v2.services.fallback_react.handle"
    POLICY_GATE_VALIDATE: Final[str] = "orchestrator.v2.services.policy_gate.validate"


V2_SPANS = V2Spans()


# ─────────────────────────────────────────────────────────────────────────────
# Mandatory Span Attributes (P0 LGPD — applied in Sprint III)
# ─────────────────────────────────────────────────────────────────────────────
# Every orchestrator span MUST include these attributes for observability:
#
#   tenant.company_id      — multi-tenant isolation tracking (REQUIRED, P0)
#   user.id                — user accountability
#   conversation.id        — conversation correlation
#   orchestrator.version   — "v1" or "v2"
#   phase.name             — V2 only (phase_0, phase_1, etc.)
#
# FORBIDDEN attributes (LGPD — must NEVER appear in spans):
#   - candidate.race / .religion / .gender / .ethnicity / .marital_status / .health
#   - Any free-text content with PII (must be PII-masked first)
#   - Any LLM prompt content (logged separately via audit_service)
#
# These rules are enforced manually in Sprint III code review.
# A pre-commit hook to detect forbidden attribute names is a Sprint IV follow-up.
# ─────────────────────────────────────────────────────────────────────────────

REQUIRED_SPAN_ATTRS: Final[tuple[str, ...]] = (
    "tenant.company_id",
    "user.id",
    "conversation.id",
    "orchestrator.version",
)

FORBIDDEN_SPAN_ATTR_PATTERNS: Final[tuple[str, ...]] = (
    "race", "raca",
    "religion", "religiao",
    "gender", "genero",
    "ethnicity", "etnia",
    "marital_status", "estado_civil",
    "health", "saude",
    "sexual_orientation", "orientacao_sexual",
    "raw_message",  # full message body must NOT go to spans (use audit_service)
    "prompt_content",
)
