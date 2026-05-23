"""Unit tests for `validate_span_attributes` (N-08 follow-up).

Reference: ADR-019 §Promotion Gate #8, task #861.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from app.shared.observability.span_validation import (
    SpanValidationResult,
    WIZARD_REQUIRED_SPAN_ATTRS,
    validate_span_attributes,
)


@dataclass
class _FakeSpan:
    """Minimal duck-type for the LightweightTracer Span used by tests."""
    name: str
    attributes: dict = field(default_factory=dict)


def _good_attrs(**overrides: Any) -> dict:
    """Return a baseline attribute dict that satisfies every required key."""
    base = {
        "service.name": "wizard",
        "wizard.graph": "job_creation",
        "wizard.stage": "intake",
        "tenant.company_id": "42",
        "user.id": "user-77",
        "conversation.id": "session-abc",
        "orchestrator.version": "wizard",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# 1. Happy path
# ---------------------------------------------------------------------------
def test_all_required_attributes_present_returns_valid():
    span = _FakeSpan(name="wizard.job_creation.intake", attributes=_good_attrs())
    result = validate_span_attributes(span)
    assert isinstance(result, SpanValidationResult)
    assert result.is_valid
    assert result.missing == []
    assert result.empty == []
    assert result.forbidden == []


# ---------------------------------------------------------------------------
# 2. Missing attribute
# ---------------------------------------------------------------------------
def test_missing_required_attribute_is_flagged():
    attrs = _good_attrs()
    del attrs["tenant.company_id"]
    span = _FakeSpan(name="wizard.job_creation.intake", attributes=attrs)
    result = validate_span_attributes(span)
    assert not result.is_valid
    assert "tenant.company_id" in result.missing
    assert result.empty == []


# ---------------------------------------------------------------------------
# 3. None-valued attribute treated as empty
# ---------------------------------------------------------------------------
def test_none_value_treated_as_missing():
    span = _FakeSpan(
        name="wizard.job_creation.intake",
        attributes=_good_attrs(**{"user.id": None}),
    )
    result = validate_span_attributes(span)
    assert not result.is_valid
    assert "user.id" in result.empty
    assert "user.id" not in result.missing  # key existed, just empty


# ---------------------------------------------------------------------------
# 4. Empty string treated as empty
# ---------------------------------------------------------------------------
def test_empty_string_value_treated_as_empty():
    span = _FakeSpan(
        name="wizard.job_creation.intake",
        attributes=_good_attrs(**{"conversation.id": ""}),
    )
    result = validate_span_attributes(span)
    assert not result.is_valid
    assert "conversation.id" in result.empty


# ---------------------------------------------------------------------------
# 5. Tenant zero ("0") treated as empty (sentinel "no tenant")
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("zero_value", ["0", 0, "0.0", 0.0, "None", "null"])
def test_tenant_zero_treated_as_empty(zero_value):
    span = _FakeSpan(
        name="wizard.job_creation.intake",
        attributes=_good_attrs(**{"tenant.company_id": zero_value}),
    )
    result = validate_span_attributes(span)
    assert not result.is_valid
    assert "tenant.company_id" in result.empty


# ---------------------------------------------------------------------------
# 6. raise_on_missing=True raises ValueError
# ---------------------------------------------------------------------------
def test_raise_on_missing_raises_value_error():
    span = _FakeSpan(name="wizard.x", attributes={"service.name": "wizard"})
    with pytest.raises(ValueError) as excinfo:
        validate_span_attributes(span, raise_on_missing=True)
    msg = str(excinfo.value)
    assert "wizard.x" in msg
    assert "tenant.company_id" in msg


# ---------------------------------------------------------------------------
# 7. Extra (non-required) attributes do not cause failure
# ---------------------------------------------------------------------------
def test_extra_attributes_do_not_invalidate():
    attrs = _good_attrs(**{"custom.tag": "anything", "agent.resolved_id": "TalentAgent"})
    span = _FakeSpan(name="wizard.agent_chat.get_agent", attributes=attrs)
    result = validate_span_attributes(span)
    assert result.is_valid
    assert result.forbidden == []


# ---------------------------------------------------------------------------
# 8. Forbidden LGPD attribute is flagged
# ---------------------------------------------------------------------------
def test_forbidden_lgpd_attribute_is_flagged():
    attrs = _good_attrs(**{"candidate.race": "anything"})
    span = _FakeSpan(name="wizard.job_creation.publish", attributes=attrs)
    result = validate_span_attributes(span)
    assert not result.is_valid
    assert "candidate.race" in result.forbidden


# ---------------------------------------------------------------------------
# 9. Plain mapping accepted (no Span object required)
# ---------------------------------------------------------------------------
def test_plain_mapping_accepted():
    span_dict = {"name": "wizard.job_creation.review", "attributes": _good_attrs()}
    result = validate_span_attributes(span_dict)
    assert result.is_valid
    assert result.span_name == "wizard.job_creation.review"


# ---------------------------------------------------------------------------
# 10. Bare attribute mapping accepted with default name
# ---------------------------------------------------------------------------
def test_bare_attribute_mapping_accepted():
    result = validate_span_attributes(_good_attrs())
    assert result.is_valid
    assert result.span_name == "<unknown>"


# ---------------------------------------------------------------------------
# 11. Custom required list works (e.g., orchestrator-only attrs)
# ---------------------------------------------------------------------------
def test_custom_required_list():
    span = _FakeSpan(
        name="orchestrator.v2.process",
        attributes={
            "tenant.company_id": "42",
            "user.id": "user-1",
            "conversation.id": "conv-1",
            "orchestrator.version": "v2",
        },
    )
    # Default WIZARD list includes wizard.stage which the orchestrator span
    # doesn't carry — caller passes the leaner orchestrator-only list.
    from app.shared.observability.span_validation import REQUIRED_SPAN_ATTRS

    result = validate_span_attributes(span, required=REQUIRED_SPAN_ATTRS)
    assert result.is_valid


# ---------------------------------------------------------------------------
# 12. Forbidden token detection is case-insensitive and tokenized
# ---------------------------------------------------------------------------
def test_forbidden_detection_is_case_insensitive_and_tokenized():
    # `traceback` should NOT match (substring "race" inside a single token).
    safe_attrs = _good_attrs(**{"error.traceback": "stack..."})
    safe_span = _FakeSpan(name="wizard.job_creation.publish", attributes=safe_attrs)
    safe_result = validate_span_attributes(safe_span)
    assert safe_result.is_valid
    assert safe_result.forbidden == []

    # But `Candidate.Race` SHOULD match (case-insensitive token match).
    bad_attrs = _good_attrs(**{"Candidate.Race": "x"})
    bad_span = _FakeSpan(name="wizard.job_creation.publish", attributes=bad_attrs)
    bad_result = validate_span_attributes(bad_span)
    assert not bad_result.is_valid
    assert "Candidate.Race" in bad_result.forbidden


# ---------------------------------------------------------------------------
# Sanity helpers — keep the canonical list in a known shape
# ---------------------------------------------------------------------------
def test_wizard_required_attrs_is_a_tuple_of_strings():
    assert isinstance(WIZARD_REQUIRED_SPAN_ATTRS, tuple)
    assert all(isinstance(x, str) for x in WIZARD_REQUIRED_SPAN_ATTRS)
    assert "tenant.company_id" in WIZARD_REQUIRED_SPAN_ATTRS
    assert "wizard.stage" in WIZARD_REQUIRED_SPAN_ATTRS


def test_unsupported_span_type_raises_typeerror():
    with pytest.raises(TypeError):
        validate_span_attributes(object())


def test_inlined_constants_match_orchestrator_canonical_values():
    """Drift guard: span_validation inlines REQUIRED_SPAN_ATTRS and
    FORBIDDEN_SPAN_ATTR_PATTERNS to avoid the heavy `app.orchestrator`
    package import. This test fails the moment the two copies drift,
    so the duplication stays a pure performance optimisation rather
    than a maintenance hazard.

    Code review follow-up (task #861).
    """
    from app.orchestrator.observability._observability import (
        FORBIDDEN_SPAN_ATTR_PATTERNS as canonical_forbidden,
        REQUIRED_SPAN_ATTRS as canonical_required,
    )
    from app.shared.observability.span_validation import (
        FORBIDDEN_SPAN_ATTR_PATTERNS as inlined_forbidden,
        REQUIRED_SPAN_ATTRS as inlined_required,
    )

    assert tuple(inlined_required) == tuple(canonical_required), (
        "span_validation.REQUIRED_SPAN_ATTRS drifted from "
        "app.orchestrator.observability._observability.REQUIRED_SPAN_ATTRS. Either update "
        "both, or remove the inline copy in span_validation.py."
    )
    assert set(inlined_forbidden) == set(canonical_forbidden), (
        "span_validation.FORBIDDEN_SPAN_ATTR_PATTERNS drifted from "
        "app.orchestrator.observability._observability.FORBIDDEN_SPAN_ATTR_PATTERNS. "
        "Either update both, or remove the inline copy in span_validation.py."
    )
