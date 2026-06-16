"""Contract sensor — WSI minimum-distribution gate on the LIVE orchestrator path
(registrado 2026-06-02).

Pina o gate AUTORITATIVO server-side implementado em
``_handle_approve_wsi_questions`` + o helper DRY ``_wsi_distribution_status``
(app/domains/job_creation/orchestrator/wizard_service_tools.py).

Contexto: a metodologia WSI exige um mínimo de perguntas técnicas E
comportamentais por (screening_mode, seniority) — tabela canonical em
``_get_question_distribution`` (graph.py). Esse mínimo só era validado no
FRONTEND (bypassável). Este gate é o ponto autoritativo no caminho live do
orquestrador: recusa a aprovação fail-closed quando abaixo do mínimo.

Invariantes cobertas:
  1. Distribuição completa (compact/pleno = 5 téc + 2 comp) → approve sucesso.
  2. Técnicas abaixo do mínimo → approve error=True citando o que falta.
  3. Comportamentais abaixo do mínimo → approve error=True.
  4. Sem perguntas → error=True (comportamento existente preservado).
  5. ``_wsi_distribution_status``: gap None no mínimo exato; gap populado abaixo.
  6. Fail-open: ``_get_question_distribution`` indisponível → gap None, sem raise.

Se a forma do gap, o critério de bloco, ou a semântica fail-open mudar no
produtor, este sensor deve ser atualizado em lockstep — é o ponto de regressão.
"""

from typing import Any, Dict, List
from unittest.mock import patch

import pytest

from app.domains.job_creation.orchestrator.wizard_service_tools import (
    _handle_approve_wsi_questions,
    _wsi_distribution_status,
)
from app.domains.job_creation.orchestrator.wizard_tools import ToolContext


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _q(block: str) -> Dict[str, Any]:
    """Pergunta no shape do painel (igual a _wsi_question_to_panel)."""
    return {"id": None, "question": "...", "block": block}


def _make_questions(n_tech: int, n_behav: int) -> List[Dict[str, Any]]:
    return [_q("technical") for _ in range(n_tech)] + [
        _q("behavioral") for _ in range(n_behav)
    ]


def _state(n_tech: int, n_behav: int, *, mode="compact", seniority="pleno") -> dict:
    return {
        "wsi_questions": _make_questions(n_tech, n_behav),
        "screening_mode": mode,
        "seniority_resolved": seniority,
    }


_CTX = ToolContext(company_id="11111111-1111-1111-1111-111111111111")


# ---------------------------------------------------------------------------
# 1. Distribuição completa → approve sucesso
# ---------------------------------------------------------------------------
def test_approve_succeeds_when_distribution_complete():
    # compact/pleno = 5 técnicas + 2 comportamentais (tabela canonical)
    res = _handle_approve_wsi_questions(_state(5, 2), {}, _CTX)
    assert res.error is False
    assert res.state_updates.get("questions_approved") is True


def test_approve_succeeds_when_above_minimum():
    res = _handle_approve_wsi_questions(_state(6, 3), {}, _CTX)
    assert res.error is False
    assert res.state_updates.get("questions_approved") is True


# ---------------------------------------------------------------------------
# 2. Técnicas abaixo do mínimo → error
# ---------------------------------------------------------------------------
def test_approve_blocked_when_technical_below_minimum():
    res = _handle_approve_wsi_questions(_state(3, 2), {}, _CTX)
    assert res.error is True
    assert res.state_updates.get("questions_approved") is not True
    # cita quantas técnicas faltam (5 - 3 = 2)
    assert "técnica" in res.llm_message.lower()
    assert "2" in res.llm_message


# ---------------------------------------------------------------------------
# 3. Comportamentais abaixo do mínimo → error
# ---------------------------------------------------------------------------
def test_approve_blocked_when_behavioral_below_minimum():
    res = _handle_approve_wsi_questions(_state(5, 0), {}, _CTX)
    assert res.error is True
    assert res.state_updates.get("questions_approved") is not True
    assert "comportamental" in res.llm_message.lower()


# ---------------------------------------------------------------------------
# 4. Sem perguntas → error (comportamento existente preservado)
# ---------------------------------------------------------------------------
def test_approve_blocked_when_no_questions():
    res = _handle_approve_wsi_questions({"wsi_questions": []}, {}, _CTX)
    assert res.error is True
    assert "Gere primeiro" in res.llm_message or "gere primeiro" in res.llm_message.lower()


# ---------------------------------------------------------------------------
# 5. _wsi_distribution_status — gap None no mínimo exato; populado abaixo
# ---------------------------------------------------------------------------
def test_status_gap_none_at_exact_minimum():
    st = _wsi_distribution_status(_state(5, 2))
    assert st["gap"] is None
    assert st["tech_count"] == 5
    assert st["behavioral_count"] == 2
    assert st["min_tech"] == 5
    assert st["min_behavioral"] == 2


def test_status_gap_populated_when_below():
    st = _wsi_distribution_status(_state(3, 1))
    assert st["gap"] is not None
    assert st["gap"]["tech"] == {"current": 3, "required": 5}
    assert st["gap"]["behavioral"] == {"current": 1, "required": 2}


def test_status_counts_behavioral_as_complement():
    # behavioral = total - tech; perguntas sem block contam como não-técnicas.
    st = _wsi_distribution_status(
        {
            "wsi_questions": _make_questions(5, 0) + [{"block": None}, {"block": None}],
            "screening_mode": "compact",
            "seniority_resolved": "pleno",
        }
    )
    assert st["tech_count"] == 5
    assert st["behavioral_count"] == 2  # 2 sem block tratadas como comportamentais
    assert st["gap"] is None


# ---------------------------------------------------------------------------
# 6. Fail-open — _get_question_distribution indisponível → gap None, sem raise
# ---------------------------------------------------------------------------
def test_status_fail_open_when_distribution_raises():
    with patch(
        "app.domains.job_creation.graph._get_question_distribution",
        side_effect=RuntimeError("table unavailable"),
    ):
        st = _wsi_distribution_status(_state(0, 0))
    assert st["gap"] is None
    assert st["min_tech"] == 0
    assert st["min_behavioral"] == 0


def test_approve_fail_open_does_not_block(monkeypatch):
    # Se a tabela falhar, o gate não deve travar a aprovação (mínimos = 0).
    with patch(
        "app.domains.job_creation.graph._get_question_distribution",
        side_effect=RuntimeError("table unavailable"),
    ):
        res = _handle_approve_wsi_questions(_state(1, 0), {}, _CTX)
    assert res.error is False
    assert res.state_updates.get("questions_approved") is True


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
