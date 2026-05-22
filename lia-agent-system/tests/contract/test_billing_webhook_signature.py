"""Wave 4 audit 2026-05-22 — P0 sensor: billing webhook signature validation.

Context
───────
Pre-Wave-4, ``IuguProvider.parse_webhook`` and ``VindiProvider.parse_webhook``
accepted a ``signature`` kwarg but NEVER called ``hmac.compare_digest`` —
classic forgery primitive. An attacker who can reach the public webhook
endpoint (``/api/v1/billing/webhooks/{iugu,vindi}``) could craft a body
like::

    {"event": "invoice.paid", "data": {"id": "<victim-subscription-id>"}}

and grant themselves a paid subscription, or forge ``subscription.suspended``
to DoS a real paying customer.

This test pins:

1. Missing signature -> ``WebhookSignatureError`` (HTTP 403 at API layer).
2. Invalid signature -> ``WebhookSignatureError``.
3. Valid HMAC-SHA256 of raw body using env secret -> webhook parsed normally.
4. Missing env secret -> ``WebhookSignatureError`` (fail-closed REGRA 4).
5. ``hmac.compare_digest`` is the comparator (constant-time, resists timing).

Pure unit test — no DB, no HTTP. Tests the provider's parse_webhook directly.
"""
from __future__ import annotations

import hashlib
import hmac
from unittest.mock import patch

import pytest

from app.services.billing_providers.base import WebhookSignatureError
from app.services.billing_providers.iugu_provider import (
    IuguProvider,
    _verify_iugu_signature,
)
from app.services.billing_providers.vindi_provider import (
    VindiProvider,
    _verify_vindi_signature,
)


# ─────────────────────────────────────────────────────────────────────────────
# Iugu
# ─────────────────────────────────────────────────────────────────────────────
class TestIuguWebhookSignature:
    SECRET = "iugu-test-secret-32bytes-minimum-ok"
    PAYLOAD_RAW = b'{"event":"invoice.paid","data":{"id":"inv-123"}}'

    def _valid_sig(self) -> str:
        return hmac.new(
            self.SECRET.encode("utf-8"),
            self.PAYLOAD_RAW,
            hashlib.sha256,
        ).hexdigest()

    def test_rejects_missing_signature(self):
        with patch.dict("os.environ", {"IUGU_API_TOKEN": self.SECRET}):
            provider = IuguProvider(api_key="ignored")
            with pytest.raises(WebhookSignatureError):
                provider.parse_webhook(
                    payload={"event": "invoice.paid"},
                    signature=None,
                    payload_raw=self.PAYLOAD_RAW,
                )

    def test_rejects_invalid_signature(self):
        with patch.dict("os.environ", {"IUGU_API_TOKEN": self.SECRET}):
            provider = IuguProvider(api_key="ignored")
            with pytest.raises(WebhookSignatureError):
                provider.parse_webhook(
                    payload={"event": "invoice.paid"},
                    signature="deadbeef" * 8,
                    payload_raw=self.PAYLOAD_RAW,
                )

    def test_accepts_valid_signature(self):
        with patch.dict("os.environ", {"IUGU_API_TOKEN": self.SECRET}):
            provider = IuguProvider(api_key="ignored")
            result = provider.parse_webhook(
                payload={"event": "invoice.status_changed", "data": {"id": "inv-1"}},
                signature=self._valid_sig(),
                payload_raw=self.PAYLOAD_RAW,
            )
        assert result["provider"] == "iugu"
        # Event mapping must still kick in for whitelisted events.
        assert result["event_type"] == "invoice.updated"

    def test_fail_closed_when_secret_missing(self, monkeypatch):
        # Ensure env var truly absent
        monkeypatch.delenv("IUGU_API_TOKEN", raising=False)
        provider = IuguProvider(api_key="ignored")
        with pytest.raises(WebhookSignatureError):
            provider.parse_webhook(
                payload={"event": "invoice.paid"},
                signature=self._valid_sig(),  # even a "valid" sig must be rejected
                payload_raw=self.PAYLOAD_RAW,
            )

    def test_constant_time_comparison_used(self):
        """Pin that hmac.compare_digest is the comparator (timing-attack safe).

        We patch hmac.compare_digest and assert it was called. If a future
        refactor regresses to ``==`` comparison, this test fails.
        """
        with patch.dict("os.environ", {"IUGU_API_TOKEN": self.SECRET}):
            with patch(
                "app.services.billing_providers.iugu_provider.hmac.compare_digest",
                wraps=hmac.compare_digest,
            ) as spy:
                _verify_iugu_signature(self.PAYLOAD_RAW, self._valid_sig())
                assert spy.called, "hmac.compare_digest MUST be the comparator"

    def test_rejects_empty_payload(self):
        with patch.dict("os.environ", {"IUGU_API_TOKEN": self.SECRET}):
            assert _verify_iugu_signature(b"", self._valid_sig()) is False


# ─────────────────────────────────────────────────────────────────────────────
# Vindi
# ─────────────────────────────────────────────────────────────────────────────
class TestVindiWebhookSignature:
    SECRET = "vindi-test-secret-32bytes-minimum-ok"
    PAYLOAD_RAW = b'{"event":{"type":"bill_paid","data":{"id":"bill-1"}}}'

    def _valid_sig(self) -> str:
        return hmac.new(
            self.SECRET.encode("utf-8"),
            self.PAYLOAD_RAW,
            hashlib.sha256,
        ).hexdigest()

    def test_rejects_missing_signature(self):
        with patch.dict("os.environ", {"VINDI_WEBHOOK_SECRET": self.SECRET}):
            provider = VindiProvider(api_key="ignored")
            with pytest.raises(WebhookSignatureError):
                provider.parse_webhook(
                    payload={"event": {"type": "bill_paid"}},
                    signature=None,
                    payload_raw=self.PAYLOAD_RAW,
                )

    def test_accepts_valid_signature(self):
        with patch.dict("os.environ", {"VINDI_WEBHOOK_SECRET": self.SECRET}):
            provider = VindiProvider(api_key="ignored")
            result = provider.parse_webhook(
                payload={"event": {"type": "bill_paid", "data": {"id": "b1"}}},
                signature=self._valid_sig(),
                payload_raw=self.PAYLOAD_RAW,
            )
        assert result["provider"] == "vindi"
        assert result["event_type"] == "invoice.paid"

    def test_fail_closed_when_secret_missing(self, monkeypatch):
        monkeypatch.delenv("VINDI_WEBHOOK_SECRET", raising=False)
        monkeypatch.delenv("VINDI_API_KEY", raising=False)
        provider = VindiProvider(api_key="ignored")
        with pytest.raises(WebhookSignatureError):
            provider.parse_webhook(
                payload={"event": {"type": "bill_paid"}},
                signature="anyhex",
                payload_raw=self.PAYLOAD_RAW,
            )

    def test_falls_back_to_vindi_api_key(self, monkeypatch):
        """If VINDI_WEBHOOK_SECRET unset but VINDI_API_KEY set, validate with that."""
        monkeypatch.delenv("VINDI_WEBHOOK_SECRET", raising=False)
        monkeypatch.setenv("VINDI_API_KEY", self.SECRET)
        valid = self._valid_sig()
        assert _verify_vindi_signature(self.PAYLOAD_RAW, valid) is True
