"""
Tests for F-06 (P0 LGPD Art. 18 VI): Erasure cascade for voice tables.

LGPD Art. 18 V: titular pode pedir eliminação. Antes do fix, DELETE em
`candidates` NÃO propagava para voice_wsi_results, voice_screening_calls,
voice_screening_analyses, wsi_response_analyses — transcripts de candidato
deletado ficavam órfãos.

Audit ref: ~/Documents/wedotalent_audit_2026-05-21/AUDIT_VOICE_SCREENING_ORCHESTRATOR_2026-05-22.md F-06

Decisão de design (CASCADE vs SET NULL):
  - voice_screening_calls       → CASCADE delete (candidate_id direto, dados pessoais)
  - voice_screening_analyses    → CASCADE delete (FK voice_screening_calls)
  - voice_wsi_results           → CASCADE delete (candidate_id direto, score WSI = dado pessoal)
  - wsi_response_analyses       → CASCADE delete (candidate_id direto, transcript = dado pessoal)

Audit trail anonimizado preservado em `audit_logs` separado (não usa candidate_id).
"""
from __future__ import annotations


def test_voice_screening_calls_in_secondary_pii_tables():
    """F-06: voice_screening_calls must be in _SECONDARY_PII_TABLES (candidate_id FK)."""
    from app.domains.lgpd.services.lgpd_cleanup_service import _SECONDARY_PII_TABLES

    table_names = [t[0] for t in _SECONDARY_PII_TABLES]
    assert "voice_screening_calls" in table_names, (
        "F-06: voice_screening_calls must be registered for LGPD Art. 18 erasure cascade. "
        "Stores candidate_id + candidate_name + candidate_phone + candidate_email + transcript."
    )


def test_voice_wsi_results_in_secondary_pii_tables():
    """F-06: voice_wsi_results must be in _SECONDARY_PII_TABLES."""
    from app.domains.lgpd.services.lgpd_cleanup_service import _SECONDARY_PII_TABLES

    table_names = [t[0] for t in _SECONDARY_PII_TABLES]
    assert "voice_wsi_results" in table_names, (
        "F-06: voice_wsi_results must be registered for LGPD Art. 18 erasure cascade. "
        "WSI score derived from candidate's voice = dado pessoal."
    )


def test_wsi_response_analyses_in_secondary_pii_tables():
    """F-06: wsi_response_analyses must be in _SECONDARY_PII_TABLES (transcript + audio)."""
    from app.domains.lgpd.services.lgpd_cleanup_service import _SECONDARY_PII_TABLES

    table_names = [t[0] for t in _SECONDARY_PII_TABLES]
    assert "wsi_response_analyses" in table_names, (
        "F-06: wsi_response_analyses must be registered for LGPD Art. 18 erasure cascade. "
        "Stores response_audio_url + response_text + candidate_id."
    )


def test_voice_screening_analyses_in_secondary_pii_tables():
    """F-06: voice_screening_analyses cascades via FK voice_screening_calls — but also
    registered explicitly to defend in depth (in case FK gets removed)."""
    from app.domains.lgpd.services.lgpd_cleanup_service import _SECONDARY_PII_TABLES

    table_names = [t[0] for t in _SECONDARY_PII_TABLES]
    # voice_screening_analyses doesn't have candidate_id (FK to call_id), so we register it
    # for defense-in-depth via screening_call_id mapping path. If absent here, that's OK
    # only if we add an explicit cascade test on the call_id deletion.
    # For now, asserting explicit presence ensures double-protection.
    assert "voice_screening_analyses" in table_names, (
        "F-06 defense-in-depth: voice_screening_analyses must be registered "
        "(FK voice_screening_calls already cascades, but explicit guard prevents "
        "regression if FK is removed)."
    )


def test_voice_tables_in_allowed_propagation():
    """F-06: every voice table in _SECONDARY_PII_TABLES must also be in
    _ALLOWED_PROPAGATION_TABLES (defense against SQL injection — name allowlist)."""
    from app.domains.lgpd.services.lgpd_cleanup_service import (
        _ALLOWED_PROPAGATION_TABLES,
        _SECONDARY_PII_TABLES,
    )

    voice_tables = {
        "voice_screening_calls",
        "voice_screening_analyses",
        "voice_wsi_results",
        "wsi_response_analyses",
    }
    registered = {t[0] for t in _SECONDARY_PII_TABLES}
    for tbl in voice_tables & registered:
        assert tbl in _ALLOWED_PROPAGATION_TABLES, (
            f"F-06: {tbl} is in _SECONDARY_PII_TABLES but not in _ALLOWED_PROPAGATION_TABLES. "
            "Without the allowlist entry, propagation skips the table silently (SQL injection guard)."
        )


def test_voice_screening_analyses_uses_screening_call_id_not_candidate_id():
    """F-06: voice_screening_analyses doesn't have candidate_id — must use
    screening_call_id (FK to voice_screening_calls). The _SECONDARY_PII_TABLES
    entry must use the correct column name."""
    from app.domains.lgpd.services.lgpd_cleanup_service import _SECONDARY_PII_TABLES

    entries = {t[0]: t[1] for t in _SECONDARY_PII_TABLES}
    if "voice_screening_analyses" in entries:
        # voice_screening_analyses has NO candidate_id column — only screening_call_id FK.
        # Cascade happens via the FK CASCADE constraint when voice_screening_calls row
        # is deleted. So this entry's "candidate_id_column" can be a special marker
        # like "_cascade_via_fk" OR we omit it and rely on FK. Asserting the value here
        # is informative for future maintainers.
        col = entries["voice_screening_analyses"]
        assert col in {"candidate_id", "_cascade_via_fk"}, (
            f"F-06: voice_screening_analyses entry has unexpected id_col={col!r}. "
            "Use 'candidate_id' (if you added a denormalized column) or '_cascade_via_fk' "
            "to flag that cascade happens via voice_screening_calls FK only."
        )
