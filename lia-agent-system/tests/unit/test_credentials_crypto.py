"""Tests canonical para app.shared.services.credentials_crypto (P0.D Wave 3).

Cobre: round-trip, edge cases (None / empty), fail-loud em ciphertext invalido.
NUNCA loga conteudo de credentials (LGPD).
"""
from __future__ import annotations

import os

import pytest

os.environ.setdefault("IS_DEVELOPMENT", "true")

from app.shared.services.credentials_crypto import (  # noqa: E402
    CredentialsEncryptionError,
    decrypt_credentials,
    encrypt_credentials,
)


class TestEncryptCredentials:
    def test_round_trip_simple_dict(self):
        sample = {"api_key": "secret-abc-123"}
        enc = encrypt_credentials(sample)
        assert isinstance(enc, str)
        assert "secret-abc" not in enc  # ciphertext should not leak plaintext
        assert decrypt_credentials(enc) == sample

    def test_round_trip_multi_field(self):
        sample = {
            "api_key": "k1",
            "oauth_token": "t1",
            "refresh_token": "r1",
            "webhook_secret": "w1",
        }
        enc = encrypt_credentials(sample)
        assert decrypt_credentials(enc) == sample

    def test_round_trip_nested(self):
        sample = {
            "oauth": {"client_id": "abc", "client_secret": "shh"},
            "scopes": ["read", "write"],
        }
        enc = encrypt_credentials(sample)
        assert decrypt_credentials(enc) == sample

    def test_round_trip_unicode(self):
        sample = {"description": "Integração corporativa - Português"}
        enc = encrypt_credentials(sample)
        dec = decrypt_credentials(enc)
        assert dec == sample

    def test_empty_dict_returns_none(self):
        assert encrypt_credentials({}) is None

    def test_none_returns_none(self):
        assert encrypt_credentials(None) is None

    def test_non_serializable_raises(self):
        class NotSerializable:
            pass
        with pytest.raises(CredentialsEncryptionError):
            encrypt_credentials({"obj": NotSerializable()})


class TestDecryptCredentials:
    def test_none_returns_empty_dict(self):
        assert decrypt_credentials(None) == {}

    def test_empty_string_returns_empty_dict(self):
        assert decrypt_credentials("") == {}

    def test_invalid_ciphertext_raises_loud(self):
        with pytest.raises(CredentialsEncryptionError):
            decrypt_credentials("definitely-not-a-fernet-token")

    def test_garbled_ciphertext_raises_loud(self):
        # Build a valid-looking-but-corrupt ciphertext
        enc = encrypt_credentials({"a": "b"})
        corrupted = enc[:-5] + "AAAAA"
        with pytest.raises(CredentialsEncryptionError):
            decrypt_credentials(corrupted)


class TestNoPlaintextLeak:
    """LGPD: confirm helper never returns the plaintext when decryption fails."""

    def test_failure_does_not_return_ciphertext_as_plaintext(self):
        """REGRA 4: no silent fallback — must raise, not return garbage."""
        try:
            result = decrypt_credentials("garbage-input")
        except CredentialsEncryptionError:
            return  # expected path
        else:
            pytest.fail(
                f"decrypt_credentials silently returned {result!r} instead of "
                "raising on invalid ciphertext (LGPD violation risk)"
            )
