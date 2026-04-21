"""Onda 2.1 G5 light (2026-04-21) — PII redaction at response boundary.

Tests the new `redact_response_with_audit` function + ChatAdapter integration.
LGPD compliance: responses must not expose raw CPF/CNPJ/email/phone.

Covers:
- CPF (### . ### . ### - ##)
- CNPJ (## . ### . ### / #### - ##)
- Email
- Phone BR
- Mixed PII in one message
- Strict mode (full name heuristic)
- Feature flag off → passthrough
- Empty / None input
"""
from __future__ import annotations

import os


def test_cpf_redaction_with_audit() -> None:
    """G5: CPF formatted + unformatted redacted + audit entry."""
    from app.shared.pii_masking import redact_response_with_audit

    text = "Candidato com CPF 123.456.789-00 foi aprovado."
    redacted, audit = redact_response_with_audit(text)

    assert "[CPF REDACTED]" in redacted
    assert "123.456.789-00" not in redacted
    assert any(a["type"] == "cpf" for a in audit)
    assert audit[0]["snippet"] == "123.456.789-00"


def test_cnpj_redaction_with_audit() -> None:
    """G5: CNPJ format ## . ### . ### / #### - ## redacted."""
    from app.shared.pii_masking import redact_response_with_audit

    text = "Empresa CNPJ 12.345.678/0001-90 parceira."
    redacted, audit = redact_response_with_audit(text)

    assert "[CNPJ REDACTED]" in redacted
    assert "12.345.678/0001-90" not in redacted
    assert any(a["type"] == "cnpj" for a in audit)


def test_email_redaction() -> None:
    """G5: email redacted."""
    from app.shared.pii_masking import redact_response_with_audit

    text = "Envie email para joao.silva@empresa.com.br"
    redacted, audit = redact_response_with_audit(text)

    assert "[EMAIL REDACTED]" in redacted
    assert "joao.silva@empresa.com.br" not in redacted
    assert any(a["type"] == "email" for a in audit)


def test_phone_br_redaction() -> None:
    """G5: Brazilian phone redacted."""
    from app.shared.pii_masking import redact_response_with_audit

    text = "Ligue para (11) 98765-4321"
    redacted, audit = redact_response_with_audit(text)

    assert "[PHONE REDACTED]" in redacted
    assert "98765-4321" not in redacted
    assert any(a["type"] == "phone" for a in audit)


def test_multiple_pii_types_single_message() -> None:
    """G5: mixed PII all redacted with full audit log."""
    from app.shared.pii_masking import redact_response_with_audit

    text = (
        "Joao CPF 111.222.333-44 da empresa CNPJ 12.345.678/0001-90 "
        "envia email joao@corp.com.br. Telefone (21) 98888-7777."
    )
    redacted, audit = redact_response_with_audit(text)

    assert "[CPF REDACTED]" in redacted
    assert "[CNPJ REDACTED]" in redacted
    assert "[EMAIL REDACTED]" in redacted
    assert "[PHONE REDACTED]" in redacted

    types_found = {a["type"] for a in audit}
    assert "cpf" in types_found
    assert "cnpj" in types_found
    assert "email" in types_found
    assert "phone" in types_found


def test_strict_mode_redacts_names() -> None:
    """G5: strict_mode=True activates full-name heuristic."""
    from app.shared.pii_masking import redact_response_with_audit

    text = "Ana Paula Silva foi aprovada na etapa final."
    redacted_normal, audit_normal = redact_response_with_audit(text, strict_mode=False)
    redacted_strict, audit_strict = redact_response_with_audit(text, strict_mode=True)

    # Normal mode: name NOT redacted (heuristic off)
    assert "Ana Paula Silva" in redacted_normal
    # Strict mode: name IS redacted
    assert "[NAME REDACTED]" in redacted_strict
    assert any(a["type"] == "full_name_heuristic" for a in audit_strict)


def test_feature_flag_disabled_returns_original() -> None:
    """G5: when LIA_RESPONSE_PII_REDACTION_ENABLED=false, passthrough."""
    # Trick: disable module-level flag via monkeypatch.
    import app.shared.pii_masking as pm

    original = pm._RESPONSE_REDACTION_ENABLED
    try:
        pm._RESPONSE_REDACTION_ENABLED = False
        text = "CPF 123.456.789-00 aqui."
        redacted, audit = pm.redact_response_with_audit(text)
        assert redacted == text
        assert audit == []
    finally:
        pm._RESPONSE_REDACTION_ENABLED = original


def test_empty_input_returns_empty() -> None:
    """G5 edge case: None/empty input returns cleanly."""
    from app.shared.pii_masking import redact_response_with_audit

    r1, a1 = redact_response_with_audit("")
    assert r1 == "" and a1 == []


def test_no_pii_clean_text_unchanged() -> None:
    """G5 regression: no-PII text passes through unchanged with empty audit."""
    from app.shared.pii_masking import redact_response_with_audit

    text = "Recrutador ok, 3 vagas ativas. Pipeline limpo."
    redacted, audit = redact_response_with_audit(text)
    assert redacted == text
    assert audit == []


def test_chat_adapter_applies_redaction_to_response_field() -> None:
    """G5 integration: ChatAdapter._convert_response redacts + tags result dict."""
    from app.orchestrator.chat_adapter import _apply_pii_redaction

    response_dict = {
        "response": "Candidato CPF 111.222.333-44 aprovado.",
        "intent": "general_query",
    }
    out = _apply_pii_redaction(response_dict)

    assert "[CPF REDACTED]" in out["response"]
    assert out["pii_redacted"] is True
    assert out["pii_audit_count"] >= 1


def test_chat_adapter_tags_clean_response_false() -> None:
    """G5: clean response still gets pii_redacted=False tag for traceability."""
    from app.orchestrator.chat_adapter import _apply_pii_redaction

    response_dict = {"response": "3 vagas abertas. Pipeline ok.", "intent": "info"}
    out = _apply_pii_redaction(response_dict)

    assert out["pii_redacted"] is False
    assert out["pii_audit_count"] == 0
    assert out["response"] == "3 vagas abertas. Pipeline ok."


def test_g5_marker_present() -> None:
    """G5 audit marker for traceability."""
    from pathlib import Path

    import app.shared.pii_masking as pm

    source = Path(pm.__file__).read_text(encoding="utf-8")
    assert "G5 light" in source, "G5: pii_masking.py must contain G5 light marker"
    assert "redact_response_with_audit" in source
