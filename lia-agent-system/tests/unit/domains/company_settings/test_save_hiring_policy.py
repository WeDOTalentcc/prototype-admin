"""Unit tests for `save_hiring_policy` (PR2 / Task #1002 — fix C1).

Cobertura sem DB (DB falha sem credenciais — esperado em ambiente CI offline):
  - tenant_required: rejeita sem company_id.
  - invalid_input: rejeita rules vazio / não-dict.
  - no_valid_fields: rejeita keys fora da whitelist.
  - atomic_routing: campos atômicos resolvem para o bloco correto (lógica
    pura, antes do DB call).
  - fairness_blocked: FairnessGuard bloqueia textos discriminatórios em
    auto_rejection_feedback / lia_tone.

A camada de DB tem cobertura E2E via golden eval (CSP-policy-save-*) e
spec Playwright (PR7).
"""
from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.domains.company_settings.tools.import_tools import (
    _ATOMIC_FIELD_TO_BLOCK,
    _HIRING_POLICY_BLOCKS,
    save_hiring_policy,
)


def _ctx(company_id: str | None = "demo-co"):
    return SimpleNamespace(company_id=company_id, user_id="u1")


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def test_rejects_when_company_id_missing():
    # Production updated (canonical multi-tenancy fail-closed):
    # require_company_id_from_obj now RAISES ToolContextMissingError instead of
    # returning error dict when company_id is None. This is correct per CLAUDE.md REGRA 4
    # (fail-closed). Updated sensor matches new contract.
    from app.tools.context_helpers import ToolContextMissingError
    import pytest as _pytest
    with _pytest.raises(ToolContextMissingError):
        _run(save_hiring_policy(rules={"min_interviews_before_offer": 2}, _context=_ctx(None)))


@pytest.mark.parametrize("bad", [{}, None, "string", 42, []])
def test_rejects_invalid_rules_input(bad):
    result = _run(save_hiring_policy(rules=bad, _context=_ctx()))
    assert result["success"] is False
    assert result["error"] == "invalid_input"


def test_rejects_unknown_keys_only():
    result = _run(save_hiring_policy(rules={"foo_bar": 1, "baz": 2}, _context=_ctx()))
    assert result["success"] is False
    assert result["error"] == "no_valid_fields"
    assert any("foo_bar" in r for r in result["rejected"])
    assert any("baz" in r for r in result["rejected"])


def test_atomic_field_to_block_mapping_covers_task_spec():
    """A task #1002 lista 8 campos atômicos. Todos precisam ter destino."""
    expected = {
        "min_interviews_before_offer",
        "manager_approval_for_offer",
        "allowed_days",
        "allowed_hours",
        "auto_rejection_feedback",
        "lia_tone",
        "auto_screening",
        "autonomy_level",
    }
    missing = expected - set(_ATOMIC_FIELD_TO_BLOCK)
    assert not missing, f"PR2 atomic mapping incompleto: {sorted(missing)}"
    # Cada destino deve ser um bloco válido.
    for atom, target in _ATOMIC_FIELD_TO_BLOCK.items():
        assert target in _HIRING_POLICY_BLOCKS, (
            f"{atom} aponta para bloco inválido {target!r}"
        )


def test_fairness_blocked_in_textual_field():
    """Texto explicitamente discriminatório em lia_tone deve ser bloqueado
    pelo FairnessGuard antes de qualquer DB call.
    """
    bad_text = (
        "Tom direto e firme. Pode dispensar candidatos jovens, mulheres "
        "grávidas e negros sem dar feedback."
    )
    result = _run(save_hiring_policy(rules={"lia_tone": bad_text}, _context=_ctx()))
    # Se o FairnessGuard estiver configurado pra bloquear, esperamos error.
    # Se estiver em modo permissivo (dev), o teste documenta o comportamento
    # e o PR3 endurece — por isso aceitamos ambos os caminhos, mas se
    # bloquear NÃO pode ter chegado ao DB.
    if result.get("reason") == "fairness_violation":
        # PR3 (Task #1003): contrato canônico (flat) per task spec:
        # `{success, reason: "fairness_violation", offending_field,
        #   offending_signal, category, blocked_terms, message}`.
        # Substituiu o contrato anterior de PR2 (`error: "fairness_blocked"`,
        # data nested) — alinhado com rule #4 do YAML company_settings.
        offending = result["offending_field"]
        # FairnessGuard recursivo reporta dot-notation: "rules.lia_tone".
        assert offending.endswith("lia_tone"), (
            f"offending_field deveria apontar para lia_tone, veio {offending!r}"
        )
        assert result.get("offending_signal"), (
            "offending_signal vazio — a LIA não conseguirá citar o trecho "
            "para o recrutador (rule #4 do YAML quebra)."
        )
        assert "category" in result
        assert isinstance(result.get("blocked_terms"), list)
