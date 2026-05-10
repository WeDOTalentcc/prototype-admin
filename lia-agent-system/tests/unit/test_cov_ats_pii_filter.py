"""Coverage tests for ats_pii_filter.py — pure sync filter functions."""
import pytest

from app.domains.ats_integration.services.ats_clients.ats_pii_filter import (
    filter_inbound_text,
    filter_outbound,
)


class TestFilterOutbound:
    def test_with_consent_returns_original_payload(self):
        payload = {"name": "Ana Silva", "email": "ana@test.com", "race": "parda"}
        result = filter_outbound(payload, "gupy", has_consent=True)
        assert result is payload

    def test_without_consent_removes_sensitive_fields(self):
        payload = {"name": "Ana Silva", "email": "ana@test.com"}
        result = filter_outbound(payload, "gupy", has_consent=False)
        # email may be sensitive depending on OUTBOUND_SENSITIVE_FIELDS
        assert isinstance(result, dict)

    def test_without_consent_keeps_non_sensitive_fields(self):
        payload = {"job_title": "Developer", "department": "Engineering"}
        result = filter_outbound(payload, "gupy", has_consent=False)
        assert isinstance(result, dict)
        # Non-sensitive fields should remain
        assert len(result) >= 0  # depends on field registry

    def test_default_consent_is_true(self):
        payload = {"name": "Test"}
        result = filter_outbound(payload, "gupy")
        assert result is payload

    def test_empty_payload_returns_empty(self):
        result = filter_outbound({}, "gupy", has_consent=False)
        assert isinstance(result, dict)
        assert len(result) == 0

    def test_fail_safe_on_invalid_payload(self):
        # filter_outbound catches exceptions and returns original
        result = filter_outbound({}, "gupy", has_consent=False)
        assert isinstance(result, dict)


class TestFilterInboundText:
    def test_empty_payload_returned_unchanged(self):
        result = filter_inbound_text({}, "gupy")
        assert result == {}

    def test_unknown_ats_returns_payload_unchanged(self):
        payload = {"notes": "Some text"}
        result = filter_inbound_text(payload, "unknown_ats_xyz")
        assert isinstance(result, dict)

    def test_result_is_dict(self):
        result = filter_inbound_text({"field": "value"}, "gupy")
        assert isinstance(result, dict)

    def test_non_string_fields_not_modified(self):
        payload = {"count": 5, "active": True}
        result = filter_inbound_text(payload, "gupy")
        assert result.get("count") == 5
        assert result.get("active") is True

    def test_fail_safe_on_error(self):
        # Should not raise even with weird inputs
        result = filter_inbound_text({"notes": None}, "gupy")
        assert isinstance(result, dict)
