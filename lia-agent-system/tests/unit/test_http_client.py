"""Tests for the canonical HTTP client factory (GAP-08-007).

Validates timeout configuration, vendor presets, and reasonable bounds.
"""
import pytest
import httpx

from app.shared.http_client import (
    get_http_client,
    get_http_timeout,
    VENDOR_TIMEOUTS,
)


class TestGetHttpTimeout:
    def test_returns_httpx_timeout(self):
        t = get_http_timeout("google")
        assert isinstance(t, httpx.Timeout)

    def test_unknown_vendor_uses_default(self):
        t_unknown = get_http_timeout("this_vendor_does_not_exist")
        t_default = get_http_timeout("default")
        assert t_unknown == t_default

    def test_default_vendor_uses_default(self):
        t = get_http_timeout()  # no argument
        assert isinstance(t, httpx.Timeout)


class TestGetHttpClient:
    def test_default_client_has_timeout(self):
        """Client created without explicit vendor has non-None timeout."""
        client = get_http_client()
        assert client.timeout is not None
        # Must not be httpx.Timeout(None) (i.e. no timeout at all)
        assert client.timeout != httpx.Timeout(None)
        client.aclose  # just verify attribute exists (don't await in sync test)

    def test_vendor_timeout_applied(self):
        """Vendor-specific timeout is forwarded to the client."""
        client = get_http_client("twilio")
        expected = VENDOR_TIMEOUTS["twilio"]
        assert client.timeout == expected

    def test_unknown_vendor_uses_default(self):
        """Unknown vendor key falls back to the 'default' timeout."""
        client = get_http_client("vendor_that_does_not_exist")
        assert client.timeout == VENDOR_TIMEOUTS["default"]

    def test_explicit_timeout_kwarg_overrides_vendor(self):
        """Caller can override the vendor preset by passing timeout= explicitly."""
        custom = httpx.Timeout(99.0)
        client = get_http_client("google", timeout=custom)
        assert client.timeout == custom

    def test_returns_async_client_instance(self):
        client = get_http_client("mailgun")
        assert isinstance(client, httpx.AsyncClient)

    def test_extra_kwargs_forwarded(self):
        """Additional kwargs like follow_redirects are forwarded."""
        client = get_http_client("default", follow_redirects=True)
        assert client.follow_redirects is True


class TestVendorTimeoutBounds:
    """Sanity-check that all presets have reasonable values (prevent typos)."""

    @pytest.mark.parametrize("vendor,timeout", VENDOR_TIMEOUTS.items())
    def test_connect_timeout_reasonable(self, vendor: str, timeout: httpx.Timeout):
        """connect timeout must be > 0 and <= 15 s."""
        assert timeout.connect is not None, f"{vendor}: connect timeout is None"
        assert 0 < timeout.connect <= 15, (
            f"{vendor}: connect={timeout.connect} outside (0, 15]"
        )

    @pytest.mark.parametrize("vendor,timeout", VENDOR_TIMEOUTS.items())
    def test_read_timeout_reasonable(self, vendor: str, timeout: httpx.Timeout):
        """read timeout must be > 0 and <= 60 s."""
        assert timeout.read is not None, f"{vendor}: read timeout is None"
        assert 0 < timeout.read <= 60, (
            f"{vendor}: read={timeout.read} outside (0, 60]"
        )

    @pytest.mark.parametrize("vendor,timeout", VENDOR_TIMEOUTS.items())
    def test_write_timeout_reasonable(self, vendor: str, timeout: httpx.Timeout):
        """write timeout must be > 0 and <= 15 s."""
        assert timeout.write is not None, f"{vendor}: write timeout is None"
        assert 0 < timeout.write <= 15, (
            f"{vendor}: write={timeout.write} outside (0, 15]"
        )

    def test_llm_timeout_not_registered(self):
        """LLM (120 s) has its own client — should not appear here."""
        assert "anthropic" not in VENDOR_TIMEOUTS
        assert "claude" not in VENDOR_TIMEOUTS

    def test_all_known_vendors_present(self):
        expected_vendors = {"google", "microsoft", "twilio", "resend", "mailgun", "apify", "github", "ats", "workos", "default"}
        assert expected_vendors.issubset(VENDOR_TIMEOUTS.keys())
