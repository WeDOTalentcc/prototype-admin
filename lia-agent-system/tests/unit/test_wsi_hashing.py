"""Unit tests for app.shared.security.wsi_hashing (Task #511)."""
from app.shared.security.wsi_hashing import (
    EU_AI_ACT_DISCLAIMER,
    hash_response,
    normalize_text,
)


def test_normalize_lowercases_and_collapses_whitespace():
    assert normalize_text("  Hello   WORLD\n\tfoo ") == "hello world foo"


def test_normalize_handles_none_and_empty():
    assert normalize_text(None) == ""
    assert normalize_text("") == ""
    assert normalize_text("   ") == ""


def test_hash_is_deterministic_and_64_hex():
    h1 = hash_response("Resposta do candidato", "sess-1", "q-1")
    h2 = hash_response("Resposta do candidato", "sess-1", "q-1")
    assert h1 == h2
    assert len(h1) == 64
    assert all(c in "0123456789abcdef" for c in h1)


def test_hash_idempotent_under_normalization():
    h1 = hash_response("Resposta do CANDIDATO", "s", "q")
    h2 = hash_response("  resposta do  candidato  ", "s", "q")
    assert h1 == h2


def test_hash_differs_by_session_or_question():
    base = hash_response("texto", "s1", "q1")
    assert hash_response("texto", "s2", "q1") != base
    assert hash_response("texto", "s1", "q2") != base


def test_hash_differs_for_different_text():
    h1 = hash_response("alpha", "s", "q")
    h2 = hash_response("beta", "s", "q")
    assert h1 != h2


def test_disclaimer_mentions_eu_ai_act_and_lgpd():
    assert "EU AI Act" in EU_AI_ACT_DISCLAIMER
    assert "LGPD" in EU_AI_ACT_DISCLAIMER
    assert "/api/v1/wsi/reports/audit/" in EU_AI_ACT_DISCLAIMER
