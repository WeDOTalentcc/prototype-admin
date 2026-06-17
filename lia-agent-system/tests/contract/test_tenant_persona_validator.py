"""
Contract sensor para ``app/domains/persona/services/tenant_persona_validator.py``.

Registrado 2026-05-21 (C6 — Admin WeDOTalent Integration Contract).

Garante que:
1. YAML syntax inválida produz error code estável (consumido pelo admin UI).
2. metadata.version ausente é rejeitado com mensagem actionable.
3. Cada ethics invariant (LGPD / fairness / EU AI Act) está enforced.
4. PII patterns aparecem como warning, não bloqueador (legacy behavior).
5. YAML válido com todos os anchors passa limpo.

Qualquer release que mudar shape de error/warning estrutura quebra
este sensor — força coordenação com time admin WeDOTalent (mismatch
de contract-version major).
"""
from __future__ import annotations

import pytest

from app.domains.persona.services.tenant_persona_validator import (
    ETHICS_INVARIANTS,
    ValidationResult,
    validate_tenant_persona_override,
)


# ----------------------------------------------------------------------------
# YAML syntax + metadata
# ----------------------------------------------------------------------------

def test_invalid_yaml_returns_structured_error():
    """Bash-style syntax erro deve gerar error code estável (não exception)."""
    out = validate_tenant_persona_override("metadata: [unclosed")
    assert out.is_valid is False
    codes = {e["code"] for e in out.errors}
    assert "yaml_syntax_error" in codes


def test_non_dict_root_is_rejected():
    """Top-level deve ser objeto. Lista no topo é error code dedicado."""
    out = validate_tenant_persona_override("- just\n- a\n- list")
    assert out.is_valid is False
    codes = {e["code"] for e in out.errors}
    assert "yaml_not_object" in codes


def test_metadata_missing_is_rejected():
    """Bloco metadata é obrigatório (T-05)."""
    out = validate_tenant_persona_override("prompts:\n  foo: bar")
    assert out.is_valid is False
    codes = {e["code"] for e in out.errors}
    assert "metadata_missing" in codes


def test_version_missing_is_rejected():
    """metadata.version é semver-like obrigatório (T-05)."""
    out = validate_tenant_persona_override(
        "metadata:\n  description: 'no version'"
    )
    assert out.is_valid is False
    codes = {e["code"] for e in out.errors}
    assert "version_missing" in codes


# ----------------------------------------------------------------------------
# Ethics invariants — CADA invariant é pin individual
# ----------------------------------------------------------------------------

ALL_ANCHORS_TEMPLATE = """metadata:
  version: "1.0-test"
prompts:
  lia_persona: |
    Diretrizes Éticas — bloco crítico.
    Lista de fatores proibidos: IGNORE COMPLETAMENTE nome, idade, foto.
    Linguagem inclusiva — usar termos neutros.
    Transparência — documentar critérios.
"""


def test_full_yaml_with_all_anchors_validates_ok():
    """Sanity baseline: YAML que contém todos os anchors passa limpo."""
    out = validate_tenant_persona_override(ALL_ANCHORS_TEMPLATE)
    assert out.is_valid is True, f"Errors: {out.errors}"
    assert out.version == "1.0-test"
    assert out.errors == []


@pytest.mark.parametrize("invariant", ETHICS_INVARIANTS, ids=lambda i: i.anchor)
def test_removing_any_single_ethics_anchor_is_rejected(invariant):
    """Quando o staff remove UM anchor (mantendo todos os outros), o
    validator deve apontar exatamente esse anchor faltando — não soltar
    um genérico ``something wrong``.

    Pin individual permite o admin UI mostrar mensagem actionable: "você
    removeu X, restaure-o".
    """
    # Surgically strip the anchor from the canonical template.
    content = ALL_ANCHORS_TEMPLATE.replace(invariant.anchor, "<removed>")
    out = validate_tenant_persona_override(content)
    assert out.is_valid is False
    anchors_missing = [
        e.get("anchor") for e in out.errors
        if e.get("code") == "ethics_invariant_missing"
    ]
    assert invariant.anchor in anchors_missing, (
        f"Expected anchor '{invariant.anchor}' to be flagged as missing; "
        f"got {anchors_missing}."
    )


# ----------------------------------------------------------------------------
# PII scan — warnings, não bloqueia
# ----------------------------------------------------------------------------

def test_pii_match_is_warning_not_error():
    """Override com email no texto: 200 ok + warning, NÃO 422."""
    content = ALL_ANCHORS_TEMPLATE + "\n# author: jose@example.com\n"
    out = validate_tenant_persona_override(content)
    assert out.is_valid is True  # PII is warning-only
    codes = {w["code"] for w in out.warnings}
    assert any(c.startswith("pii_") for c in codes), (
        f"Expected at least one pii_* warning; got {codes}"
    )


def test_no_pii_in_clean_template_means_no_warnings():
    """Sanity: o template canonical é PII-free."""
    out = validate_tenant_persona_override(ALL_ANCHORS_TEMPLATE)
    assert out.warnings == []


# ----------------------------------------------------------------------------
# Output shape stability (pin pro admin UI consumir)
# ----------------------------------------------------------------------------

def test_validation_result_has_canonical_fields():
    """Admin UI vai destructurar esses campos. Renomear é breaking
    change (major bump em contract-version)."""
    out = validate_tenant_persona_override("metadata:\n  version: 'x'")
    assert hasattr(out, "is_valid")
    assert hasattr(out, "parsed_yaml")
    assert hasattr(out, "version")
    assert hasattr(out, "errors")
    assert hasattr(out, "warnings")
    # Errors are dicts (not custom objects) — JSON-serializable for HTTP.
    for e in out.errors:
        assert isinstance(e, dict)
        assert "code" in e and "message" in e
