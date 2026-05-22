"""
Tests for F-07 (P0 LGPD Art. 11): Phone number masking in voice_session_state JSONB.

LGPD Art. 11 trata número de telefone como dado pessoal. Antes do fix,
voice_session_state JSONB persistia phone_number em plaintext. Em audit ANPD
ou backup leak, telefones de candidatos vazavam mesmo com transcripts protegidos.

Audit ref: ~/Documents/wedotalent_audit_2026-05-21/AUDIT_VOICE_SCREENING_ORCHESTRATOR_2026-05-22.md F-07

Decisão de design (preserve tail vs full mask):
  Mascarar com "+55 11 9****-1234" (preserva country code + DDD + last 4 digits)
  permite debug e suporte ao candidato sem expor o número completo. Trade-off
  com full mask "***PHONE***": fairness em UI de suporte.
"""
from __future__ import annotations

from datetime import datetime


def test_mask_phone_preserve_tail_canonical_helper_exists():
    """F-07: helper canonical mask_phone_preserve_tail exists in pii_masking."""
    from app.shared.pii_masking import mask_phone_preserve_tail

    assert callable(mask_phone_preserve_tail)


def test_mask_phone_preserves_last_4_digits():
    """F-07: 11 9XXXX-1234 → 11 9****-1234 (last 4 visible)."""
    from app.shared.pii_masking import mask_phone_preserve_tail

    result = mask_phone_preserve_tail("11999991234")
    assert result.endswith("1234"), f"last 4 digits must remain visible: {result!r}"
    # Most middle digits replaced with masking char
    assert "*" in result
    assert "9999" not in result  # middle digits should NOT appear


def test_mask_phone_preserves_country_code_and_ddd():
    """F-07: +55 (11) 99999-1234 → +55 11 *****-1234 (country + DDD visible)."""
    from app.shared.pii_masking import mask_phone_preserve_tail

    result = mask_phone_preserve_tail("+5511999991234")
    assert "55" in result, "country code 55 must remain visible"
    assert "11" in result, "DDD 11 must remain visible"
    assert result.endswith("1234"), "last 4 digits must remain visible"


def test_mask_phone_handles_short_numbers_safely():
    """F-07: ≤4 digit input returns *** (can't preserve tail without exposing whole)."""
    from app.shared.pii_masking import mask_phone_preserve_tail

    assert "*" in mask_phone_preserve_tail("1234")
    assert mask_phone_preserve_tail("") == ""
    assert mask_phone_preserve_tail(None) is None


def test_session_to_state_masks_phone_at_rest():
    """F-07: VoiceScreeningOrchestrator._session_to_state persists masked phone."""
    from app.domains.voice.services.voice_screening_orchestrator import (
        VoiceScreeningOrchestrator,
        VoiceScreeningSession,
    )

    orch = VoiceScreeningOrchestrator()
    session = VoiceScreeningSession(
        session_id="sess-1",
        candidate_id="cand-1",
        candidate_name="Carlos",
        job_title="Dev",
        company_id="comp-1",
        phone_number="+5511999991234",
        started_at=datetime.utcnow(),
    )

    state = orch._session_to_state(session)
    # F-07: persisted phone MUST be masked
    assert state["phone_number"] != "+5511999991234", (
        "F-07: phone_number persisted IN PLAINTEXT in JSONB — LGPD Art. 11 violation."
    )
    assert "9999" not in state["phone_number"], "middle digits leaked into JSONB"
    # last 4 digits remain (debug-friendly)
    assert "1234" in state["phone_number"]


def test_state_to_session_handles_masked_phone_correctly():
    """F-07: round-trip via state -> session preserves masked phone consistently
    (no double-masking, no crash on already-masked input)."""
    from app.domains.voice.services.voice_screening_orchestrator import (
        VoiceScreeningOrchestrator,
        VoiceScreeningSession,
    )

    orch = VoiceScreeningOrchestrator()
    session = VoiceScreeningSession(
        session_id="sess-2",
        candidate_id="cand-2",
        candidate_name="Ana",
        job_title="QA",
        company_id="comp-2",
        phone_number="+5511988887777",
        started_at=datetime.utcnow(),
    )

    state = orch._session_to_state(session)
    restored = orch._state_to_session(state)
    # restored phone is the MASKED value (we can never recover plaintext from JSONB)
    assert restored.phone_number == state["phone_number"]
    # Sanity: end-to-end stays masked
    assert "8888" not in restored.phone_number
    assert "7777" in restored.phone_number


def test_full_phone_not_in_session_state_json_serialization():
    """F-07 sensor: dump the full state dict; raw phone digits cannot appear anywhere."""
    import json

    from app.domains.voice.services.voice_screening_orchestrator import (
        VoiceScreeningOrchestrator,
        VoiceScreeningSession,
    )

    orch = VoiceScreeningOrchestrator()
    session = VoiceScreeningSession(
        session_id="sess-3",
        candidate_id="cand-3",
        candidate_name="X",
        job_title="Y",
        company_id="comp-3",
        phone_number="+5511955554321",
        started_at=datetime.utcnow(),
    )
    state = orch._session_to_state(session)
    payload = json.dumps(state, default=str)
    # The middle digits 5555 must not appear; last 4 (4321) may.
    assert "5555" not in payload, "F-07: full phone leaked in serialized JSONB"
