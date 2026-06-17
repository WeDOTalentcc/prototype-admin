"""R-003 — criteria_used no AuditService precisa ser payload estruturado.

Sprint 1 Quick Wins — REMEDIATION_BRIEF Wave 0.
Cobre criterio de aceite F-209 / R-003.

LGPD Art.20 (right to explanation): cada decisao critica logada precisa ter
contexto extraivel sob demanda. criteria_used=[] viola esse direito.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TARGET = REPO_ROOT / "app" / "shared" / "compliance" / "audit_service.py"


def _read_target() -> str:
    return TARGET.read_text(encoding="utf-8")


def test_audit_service_no_empty_criteria_used_in_critical_paths() -> None:
    """R-003: nenhum AuditLog em audit_service.py pode ser criado com criteria_used=[].

    Permitido: chamadas downstream (delegacao para outras tabelas) que ainda
    estao em outros arquivos — esses ficam como debito Sprint 2.
    """
    src = _read_target()
    # Aceita lista_with_items: 'criteria_used=[\n    f"...":' ou 'criteria_used=[\n    "..."'
    # Bloqueia: 'criteria_used=[]' (lista literal vazia, nao continuacao multilinha)
    lines = src.splitlines()
    offenders = []
    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped == "criteria_used=[]," or stripped == "criteria_used=[],":
            offenders.append(f"  line {i}: {stripped}")
        # multi-line vazio: criteria_used=[\n    ],
        if stripped == "criteria_used=[":
            # checa proxima linha nao trivial
            for j in range(i, min(i + 3, len(lines))):
                if lines[j].strip() in ("],", "]"):
                    offenders.append(f"  line {i}: criteria_used=[ ... ] vazio (multi-line)")
                    break
                if lines[j].strip().startswith("#") or not lines[j].strip():
                    continue
                break
    assert not offenders, (
        "R-003: encontradas chamadas com criteria_used=[] em audit_service.py:\n"
        + "\n".join(offenders)
        + "\nLGPD Art.20 exige payload estruturado (mesmo simples) para explainability."
    )


def test_log_conversational_output_has_enriched_criteria() -> None:
    """R-003: log_conversational_output enriquece com agent + action + decision_type."""
    src = _read_target()
    # Heuristica: trecho com decision_type="conversational_output" deve ter
    # criteria_used contendo 'agent:' ou 'action:' ou 'decision_type:'
    block = src[
        src.find('decision_type="conversational_output"') : src.find('decision_type="conversational_output"') + 1500
    ]
    assert "criteria_used=[" in block
    assert any(
        token in block for token in ('"agent:', '"action:', '"decision_type:')
    ), "R-003: log_conversational_output deve ter criteria_used com tokens de contexto."


def test_log_action_has_enriched_criteria() -> None:
    """R-003: log_action enriquece com actor + action_type + target_type."""
    src = _read_target()
    needle = 'decision="executed"'
    pos = src.find(needle)
    assert pos > 0, "Pre-requisito: log_action body presente"
    block = src[pos : pos + 1200]
    assert "criteria_used=[" in block
    assert any(token in block for token in ('"actor:', '"action_type:', '"target_type:'))


def test_log_compliance_check_has_enriched_criteria() -> None:
    """R-003: log_compliance_check enriquece com check_type + result + has_details."""
    src = _read_target()
    needle = 'agent_name="compliance_check"'
    pos = src.find(needle)
    assert pos > 0, "Pre-requisito: log_compliance_check body presente"
    block = src[pos : pos + 1500]
    assert "criteria_used=[" in block
    assert any(token in block for token in ('"check_type:', '"result:', '"has_details:'))


def test_log_error_has_enriched_criteria() -> None:
    """R-003: log_error enriquece com error_type + agent + has_metadata."""
    src = _read_target()
    needle = 'decision_type="error"'
    pos = src.find(needle)
    assert pos > 0, "Pre-requisito: log_error body presente"
    block = src[pos : pos + 1200]
    assert "criteria_used=[" in block
    assert any(token in block for token in ('"error_type:', '"agent:', '"has_metadata:'))
