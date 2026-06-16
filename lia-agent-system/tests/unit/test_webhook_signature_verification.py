"""
TDD tests for app.shared.security.webhook_verification.

Covers:
- verify_webhook_signature: valid/invalid/missing/tampered/timing-safe
- require_webhook_signature: HMAC path, legacy bearer fallback, rejection
"""
from __future__ import annotations

import hashlib
import hmac
import os
from unittest.mock import AsyncMock, patch

import pytest

from app.shared.security.webhook_verification import (
    verify_webhook_signature,
    require_webhook_signature,
)


# ── verify_webhook_signature unit tests ────────────────────────────────────


class TestVerifyWebhookSignature:
    """Pure function HMAC-SHA256 verification."""

    SECRET = "test-secret-key-32chars-minimum!"
    PAYLOAD = b'{"event": "candidate_created", "id": "123"}'

    def _make_signature(self, payload: bytes | None = None, secret: str | None = None) -> str:
        _payload = self.PAYLOAD if payload is None else payload
        _secret = self.SECRET if secret is None else secret
        return hmac.new(_secret.encode("utf-8"), _payload, hashlib.sha256).hexdigest()

    def test_valid_signature_passes(self):
        sig = self._make_signature()
        assert verify_webhook_signature(self.PAYLOAD, sig, self.SECRET, platform="test") is True

    def test_valid_signature_with_sha256_prefix_passes(self):
        sig = f"sha256={self._make_signature()}"
        assert verify_webhook_signature(self.PAYLOAD, sig, self.SECRET, platform="test") is True

    def test_tampered_payload_fails(self):
        sig = self._make_signature()
        tampered = b'{"event": "candidate_created", "id": "HACKED"}'
        assert verify_webhook_signature(tampered, sig, self.SECRET, platform="test") is False

    def test_wrong_secret_fails(self):
        sig = self._make_signature(secret="wrong-secret")
        assert verify_webhook_signature(self.PAYLOAD, sig, self.SECRET, platform="test") is False

    def test_missing_signature_rejects(self):
        assert verify_webhook_signature(self.PAYLOAD, "", self.SECRET, platform="test") is False

    def test_missing_secret_rejects(self):
        sig = self._make_signature()
        assert verify_webhook_signature(self.PAYLOAD, sig, "", platform="test") is False

    def test_none_secret_rejects(self):
        """Explicitly empty secret must reject, not crash."""
        sig = self._make_signature()
        assert verify_webhook_signature(self.PAYLOAD, sig, "", platform="test") is False

    def test_timing_safe_comparison_used(self):
        """Verify that hmac.compare_digest is used (not ==)."""
        sig = self._make_signature()
        with patch("app.shared.security.webhook_verification.hmac.compare_digest", return_value=True) as mock_cd:
            result = verify_webhook_signature(self.PAYLOAD, sig, self.SECRET, platform="test")
            assert result is True
            mock_cd.assert_called_once()

    def test_empty_payload_with_valid_signature(self):
        """Edge case: empty body is valid if signature matches."""
        empty_payload = b""
        sig = self._make_signature(payload=empty_payload)
        assert verify_webhook_signature(empty_payload, sig, self.SECRET, platform="test") is True

    def test_binary_payload(self):
        """Non-UTF8 payload bytes should still verify correctly."""
        binary_payload = bytes(range(256))
        sig = self._make_signature(payload=binary_payload)
        assert verify_webhook_signature(binary_payload, sig, self.SECRET, platform="test") is True


# ── require_webhook_signature dependency tests ─────────────────────────────


class TestRequireWebhookSignature:
    """FastAPI dependency factory for HMAC + optional legacy bearer."""

    SECRET = "dep-test-secret-key-32chars!!!!!"
    BEARER_SECRET = "legacy-bearer-token-for-migration"
    PAYLOAD = b'{"test": true}'

    def _make_hmac(self, payload: bytes | None = None) -> str:
        _payload = self.PAYLOAD if payload is None else payload
        return hmac.new(self.SECRET.encode("utf-8"), _payload, hashlib.sha256).hexdigest()

    def _mock_request(
        self,
        body: bytes | None = None,
        signature: str | None = None,
        authorization: str | None = None,
        header_name: str = "X-Webhook-Signature",
    ) -> AsyncMock:
        req = AsyncMock()
        req.body.return_value = body or self.PAYLOAD
        headers = {}
        if signature is not None:
            headers[header_name] = signature
        if authorization is not None:
            headers["Authorization"] = authorization
        req.headers = headers
        return req

    @pytest.mark.asyncio
    async def test_hmac_valid_passes(self):
        dep = require_webhook_signature("TEST_PROVIDER", secret_env_var="TEST_HMAC_SECRET")
        sig = self._make_hmac()
        request = self._mock_request(signature=sig)
        with patch.dict(os.environ, {"TEST_HMAC_SECRET": self.SECRET}):
            await dep(request)  # should not raise

    @pytest.mark.asyncio
    async def test_hmac_invalid_raises_401(self):
        dep = require_webhook_signature("TEST_PROVIDER", secret_env_var="TEST_HMAC_SECRET")
        request = self._mock_request(signature="bad-signature")
        with patch.dict(os.environ, {"TEST_HMAC_SECRET": self.SECRET}):
            from fastapi import HTTPException
            with pytest.raises(HTTPException) as exc_info:
                await dep(request)
            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_no_secret_configured_raises_503(self):
        dep = require_webhook_signature("TEST_PROVIDER", secret_env_var="TEST_HMAC_SECRET")
        request = self._mock_request(signature="some-sig")
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("TEST_HMAC_SECRET", None)
            from fastapi import HTTPException
            with pytest.raises(HTTPException) as exc_info:
                await dep(request)
            assert exc_info.value.status_code == 503

    @pytest.mark.asyncio
    async def test_no_signature_no_bearer_raises_401(self):
        dep = require_webhook_signature("TEST_PROVIDER", secret_env_var="TEST_HMAC_SECRET")
        request = self._mock_request()  # no signature, no auth
        with patch.dict(os.environ, {"TEST_HMAC_SECRET": self.SECRET}):
            from fastapi import HTTPException
            with pytest.raises(HTTPException) as exc_info:
                await dep(request)
            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_legacy_bearer_fallback_accepted_with_deprecation(self):
        dep = require_webhook_signature(
            "TEST_PROVIDER",
            secret_env_var="TEST_HMAC_SECRET",
            legacy_bearer_env_var="TEST_BEARER_SECRET",
        )
        request = self._mock_request(authorization=f"Bearer {self.BEARER_SECRET}")
        with patch.dict(os.environ, {
            "TEST_HMAC_SECRET": self.SECRET,
            "TEST_BEARER_SECRET": self.BEARER_SECRET,
        }):
            await dep(request)  # should not raise -- bearer accepted

    @pytest.mark.asyncio
    async def test_legacy_bearer_invalid_raises_401(self):
        dep = require_webhook_signature(
            "TEST_PROVIDER",
            secret_env_var="TEST_HMAC_SECRET",
            legacy_bearer_env_var="TEST_BEARER_SECRET",
        )
        request = self._mock_request(authorization="Bearer wrong-token")
        with patch.dict(os.environ, {
            "TEST_HMAC_SECRET": self.SECRET,
            "TEST_BEARER_SECRET": self.BEARER_SECRET,
        }):
            from fastapi import HTTPException
            with pytest.raises(HTTPException) as exc_info:
                await dep(request)
            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_hmac_takes_precedence_over_bearer(self):
        """When both HMAC signature and bearer are present, HMAC wins."""
        dep = require_webhook_signature(
            "TEST_PROVIDER",
            secret_env_var="TEST_HMAC_SECRET",
            legacy_bearer_env_var="TEST_BEARER_SECRET",
        )
        sig = self._make_hmac()
        request = self._mock_request(
            signature=sig,
            authorization=f"Bearer {self.BEARER_SECRET}",
        )
        with patch.dict(os.environ, {
            "TEST_HMAC_SECRET": self.SECRET,
            "TEST_BEARER_SECRET": self.BEARER_SECRET,
        }):
            await dep(request)  # HMAC path taken, bearer ignored
