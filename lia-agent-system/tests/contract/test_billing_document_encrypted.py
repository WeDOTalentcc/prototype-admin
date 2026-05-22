"""Wave 4 audit 2026-05-22 — P1 LGPD sensor: CPF/CNPJ encryption canonical.

Pins the contract that:
1. ``encrypt_pii`` round-trips correctly via Fernet.
2. ``decrypt_pii`` rejects empty/None.
3. Empty/whitespace input -> None on encrypt (no garbage ciphertext).
4. ``mask_document_for_log`` never returns plaintext segments large enough
   to identify the holder (LGPD-safe logging helper).

Pure unit test — no DB. Verifies the helper itself; the model integration
is exercised by the migration backfill (operational verification).
"""
from __future__ import annotations

import os

import pytest

from app.shared.services.pii_crypto import (
    PIIEncryptionError,
    decrypt_pii,
    encrypt_pii,
    mask_document_for_log,
)


@pytest.fixture(autouse=True)
def _ensure_dev_key(monkeypatch):
    """Use IS_DEVELOPMENT=true so encrypt_value works without FIELD_ENCRYPTION_KEY."""
    if not os.environ.get("FIELD_ENCRYPTION_KEY"):
        monkeypatch.setenv("IS_DEVELOPMENT", "true")
    yield


class TestEncryptDecryptRoundtrip:
    def test_cpf_roundtrip(self):
        cpf = "123.456.789-00"
        cipher = encrypt_pii(cpf)
        assert cipher is not None
        assert cipher != cpf  # MUST be transformed
        assert decrypt_pii(cipher) == cpf

    def test_cnpj_roundtrip(self):
        cnpj = "12.345.678/0001-90"
        cipher = encrypt_pii(cnpj)
        assert cipher is not None
        assert cipher != cnpj
        assert decrypt_pii(cipher) == cnpj

    def test_unformatted_cpf_roundtrip(self):
        cpf = "12345678900"
        cipher = encrypt_pii(cpf)
        assert decrypt_pii(cipher) == cpf


class TestEdgeCases:
    def test_none_input_returns_none(self):
        assert encrypt_pii(None) is None
        assert decrypt_pii(None) is None

    def test_empty_string_returns_none(self):
        assert encrypt_pii("") is None
        assert encrypt_pii("   ") is None  # whitespace-only

    def test_decrypt_empty_returns_none(self):
        assert decrypt_pii("") is None

    def test_decrypt_garbage_raises(self):
        with pytest.raises(PIIEncryptionError):
            decrypt_pii("not-a-valid-fernet-token")


class TestMaskingForLogs:
    def test_masks_cpf_safely(self):
        masked = mask_document_for_log("12345678900")
        assert "12345678900" not in masked
        # First 3 + last 2 masked
        assert masked.startswith("***")
        assert masked.endswith("**")

    def test_masks_formatted_cpf(self):
        masked = mask_document_for_log("123.456.789-00")
        assert "123" not in masked
        # last 2 chars ("00") masked
        assert "-00" not in masked

    def test_none_returns_triple_star(self):
        assert mask_document_for_log(None) == "***"
        assert mask_document_for_log("") == "***"

    def test_short_value_redacted(self):
        # Too short to safely mask — refuse partial leak
        assert mask_document_for_log("123") == "***"
