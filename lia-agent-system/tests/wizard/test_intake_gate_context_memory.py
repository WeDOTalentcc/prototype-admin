"""
Bug #1+#4 — intake_gate não passa last_turns ao WizardGateClassifier.

Task #1123 já implementou last_turns no WizardGateClassifier.classify(), mas
_classify_permission() nunca passa esse parâmetro → LLM gera respostas sem
histórico → "esquecer" título, modelo, gestor entre turnos.

RED: classify() chamado SEM last_turns quando conversation_messages existe.
GREEN: _classify_permission extrai last_turns do state e passa ao classifier.

Sentinelas:
  T1 — classify recebe last_turns não-vazio quando state tem conversation_messages
  T2 — last_turns ≤ 6 msgs (não vaza histórico inteiro)
  T3 — last_turns=None quando conversation_messages vazio (fail-open)
  T4 — gestor mencionado em turno anterior aparece em last_turns
"""
from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path
from unittest import mock

_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))


def _fake_output(intent="off_topic", confidence=0.9, reply="vamos continuar"):
    return types.SimpleNamespace(
        intent=intent,
        confidence=confidence,
        extracted_data={},
        conversational_reply=reply,
    )


def _make_state(n_turns: int = 4, *, manager: bool = False):
    msgs = []
    for i in range(n_turns):
        role = "human" if i % 2 == 0 else "assistant"
        msgs.append({"role": role, "content": f"mensagem {i + 1}"})
    if manager:
        msgs.append({"role": "human", "content": "o gestor é jose.moreira@empresa.com"})
    s = {
        "user_query": "me pergunte quando abrir outra vaga",
        "raw_input": "quero criar uma vaga de diretor de rh",  # original input ≠ current query → _is_initial=False
        "parsed_title": "Diretor de RH",
        "parsed_seniority": "Senior",
        "parsed_model": "hibrido",
        "intake_approved": None,
        "intake_salary_suggested": True,
        "intake_gate_seen_user_query": "titulo dado",
        "current_stage": "intake",
        "workspace_id": "co",
        "company_id": "co",
        "conversation_messages": msgs,
    }
    if manager:
        s["parsed_manager_email"] = "jose.moreira@empresa.com"
        s["parsed_manager_name"] = "Jose"
    return s


def _run_capture(state, fake_out):
    node_mod = importlib.import_module("app.domains.job_creation.nodes.intake_gate")
    captured: dict = {}

    async def _classify(**kwargs):
        captured.update(kwargs)
        return fake_out

    fake_classifier = mock.Mock()
    fake_classifier.classify = _classify

    with mock.patch(
        "app.domains.job_creation.nodes.intake_gate._in_graph_runtime",
        return_value=False,
    ), mock.patch(
        "app.domains.job_creation.services.wizard_gate_classifier.get_wizard_gate_classifier",
        return_value=fake_classifier,
    ), mock.patch(
        "app.domains.job_creation.nodes.intake_gate._safe_fetch_salary",
        return_value=None,
    ), mock.patch(
        "app.domains.job_creation.nodes.intake_gate._resolve_confirmed_competencies",
        return_value=([], [], None),
    ):
        node_mod.intake_gate_node(state)

    return captured


class TestLastTurnsPassedWhenHistoryExists:
    def test_classify_receives_nonempty_last_turns(self):
        state = _make_state(n_turns=4)
        kwargs = _run_capture(state, _fake_output())
        last_turns = kwargs.get("last_turns")
        assert last_turns is not None, (
            "classify() chamado SEM last_turns — histórico da conversa não está "
            "sendo passado. Bug: recrutador menciona título no turno 1, LIA "
            "esquece no turno 4. Fix: extrair conversation_messages[-6:] em "
            "_classify_permission e passar como last_turns=."
        )
        assert len(last_turns) > 0, "last_turns vazio — nenhuma msg foi extraída do state"


class TestLastTurnsTruncatedAtSix:
    def test_at_most_six_turns_forwarded(self):
        state = _make_state(n_turns=10)
        kwargs = _run_capture(state, _fake_output())
        last_turns = kwargs.get("last_turns") or []
        assert len(last_turns) <= 6, (
            f"last_turns tem {len(last_turns)} entradas — limite é 6 "
            "(classifier trunca a 3 internamente; produzir mais que 6 é custo "
            "desnecessário de tokens)."
        )


class TestLastTurnsFailOpenWhenEmpty:
    def test_no_history_passes_none_or_empty(self):
        state = _make_state(n_turns=0)
        state["conversation_messages"] = []
        kwargs = _run_capture(state, _fake_output())
        last_turns = kwargs.get("last_turns")
        # Fail-open: None ou lista vazia são ambos corretos
        assert last_turns is None or last_turns == [], (
            "Com conversation_messages vazio, last_turns deve ser None ou [] — "
            "não vazar estado stale."
        )


class TestManagerEmailVisibleInLastTurns:
    def test_manager_email_from_prior_turn_in_context(self):
        state = _make_state(n_turns=0, manager=True)
        state["conversation_messages"] = [
            {"role": "human", "content": "o gestor é jose.moreira@empresa.com"},
            {"role": "assistant", "content": "Anotado! Prosseguindo."},
        ]
        kwargs = _run_capture(state, _fake_output())
        last_turns = kwargs.get("last_turns") or []
        full_ctx = " ".join(str(t) for t in last_turns)
        assert "jose.moreira@empresa.com" in full_ctx or "jose" in full_ctx.lower(), (
            "Email do gestor não está em last_turns — o LLM não verá o contexto "
            "do gestor no próximo turno e vai esquecer/perguntar de novo."
        )
