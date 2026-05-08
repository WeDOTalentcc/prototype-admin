"""
R-001 — Fail-fast guard for REDIS_ENCRYPTION_KEY in production/staging.

Without REDIS_ENCRYPTION_KEY, RedisCrypto silently falls back to plaintext
storage (FAIL-OPEN by design for dev). In production this would store PII
(candidate data, sessions, voting cache) in plaintext. The lifespan startup
guard MUST refuse to boot in production/staging when key is empty.

Mirrors the existing pattern for LLM provider keys and OPENMIC_ALLOW_UNSIGNED_WEBHOOK
in app/main.py:lifespan.
"""
from __future__ import annotations

import pytest

from app.main import _validate_redis_encryption_key


class TestRedisEncryptionFailFast:
    """Matrix: APP_ENV × REDIS_ENCRYPTION_KEY presence."""

    def test_production_without_key_raises(self, monkeypatch):
        """production + empty key → RuntimeError with security-explicit message."""
        monkeypatch.setenv("APP_ENV", "production")
        monkeypatch.setenv("REDIS_ENCRYPTION_KEY", "")
        with pytest.raises(RuntimeError, match="REDIS_ENCRYPTION_KEY"):
            _validate_redis_encryption_key()

    def test_prod_alias_without_key_raises(self, monkeypatch):
        """prod (alias) + empty key → RuntimeError."""
        monkeypatch.setenv("APP_ENV", "prod")
        monkeypatch.setenv("REDIS_ENCRYPTION_KEY", "")
        with pytest.raises(RuntimeError, match="REDIS_ENCRYPTION_KEY"):
            _validate_redis_encryption_key()

    def test_staging_without_key_raises(self, monkeypatch):
        """staging + empty key → RuntimeError (staging shares prod posture)."""
        monkeypatch.setenv("APP_ENV", "staging")
        monkeypatch.setenv("REDIS_ENCRYPTION_KEY", "")
        with pytest.raises(RuntimeError, match="REDIS_ENCRYPTION_KEY"):
            _validate_redis_encryption_key()

    def test_production_with_whitespace_only_key_raises(self, monkeypatch):
        """production + whitespace key → still empty after strip → RuntimeError."""
        monkeypatch.setenv("APP_ENV", "production")
        monkeypatch.setenv("REDIS_ENCRYPTION_KEY", "   ")
        with pytest.raises(RuntimeError, match="REDIS_ENCRYPTION_KEY"):
            _validate_redis_encryption_key()

    def test_development_without_key_warns_only(self, monkeypatch, caplog):
        """development + empty key → warning, no raise (preserve fail-OPEN dev posture)."""
        import logging
        monkeypatch.setenv("APP_ENV", "development")
        monkeypatch.setenv("REDIS_ENCRYPTION_KEY", "")
        with caplog.at_level(logging.WARNING, logger="app.main"):
            _validate_redis_encryption_key()  # must not raise
        # Optional: confirm warning emitted
        assert any("REDIS_ENCRYPTION_KEY" in rec.message for rec in caplog.records)

    def test_dev_default_when_app_env_unset_warns_only(self, monkeypatch):
        """APP_ENV unset → defaults to development → no raise."""
        monkeypatch.delenv("APP_ENV", raising=False)
        monkeypatch.setenv("REDIS_ENCRYPTION_KEY", "")
        _validate_redis_encryption_key()  # must not raise

    def test_production_with_valid_fernet_key_ok(self, monkeypatch):
        """production + valid Fernet key → no raise, no warning at critical level."""
        from cryptography.fernet import Fernet
        valid_key = Fernet.generate_key().decode()
        monkeypatch.setenv("APP_ENV", "production")
        monkeypatch.setenv("REDIS_ENCRYPTION_KEY", valid_key)
        _validate_redis_encryption_key()  # must not raise
