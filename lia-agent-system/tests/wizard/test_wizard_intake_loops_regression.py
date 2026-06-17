"""Regression sentinel — Loop 1 + Loop 2 do intake_gate (2026-05-30).

Pina o fix canonical dos dois loops reportados por Paulo (screenshots):

  Loop 1 — "Pode me passar o título da vaga?" repetindo mesmo apos o usuario
           fornecer o titulo. Causa: apos interrupt() mid-node, o checkpoint
           contem ws_stage_payload stale do intake_node anterior;
           _post_process_result exibia a mensagem stale em vez da pergunta do
           interrupt.

  Loop 2 — "Para avançar, é só confirmar..." repetindo quando usuario diz "pode".
           Causa: modelo de trabalho (bloqueante por design) faltando — o gate
           pedia o modelo mas mostrava a mensagem stale, e o "pode" era tratado
           como resposta-de-modelo (que nao extrai modelo) → re-interrupt.

Fix canonical (NAO tornar modelo opcional — modelo e bloqueante per
.planning/funil-criacao-vaga-conversacional-plan.md FASE 5):
  - graph.JobCreationGraph.get_pending_interrupt_message() extrai a mensagem do
    interrupt pendente do snapshot do LangGraph.
  - wizard_session_service._post_process_result() honra _interrupt_msg_override
    com prioridade MAXIMA (acima de gate_clarify_message e ws_stage_payload).

Sentinelas:
  T1 — get_pending_interrupt_message extrai data.message do interrupt pendente.
  T2 — fail-open: sem tasks / snapshot None / value sem data.message → None.
  T3 — _post_process_result prefere _interrupt_msg_override sobre ws_stage_payload
       stale (o coração do fix dos dois loops).
  T4 — modelo de trabalho permanece BLOQUEANTE no intake_gate (anti-regressao do
       desvio Fix 2 que foi revertido).

Run standalone:
    python lia-agent-system/tests/wizard/test_wizard_intake_loops_regression.py
"""
from __future__ import annotations

import asyncio
import importlib
import sys
import types
import unittest
from pathlib import Path
from unittest import mock

_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))


def _make_interrupt(value):
    intr = types.SimpleNamespace()
    intr.value = value
    return intr


def _make_task(interrupts):
    task = types.SimpleNamespace()
    task.interrupts = interrupts
    return task


def _make_snapshot(tasks):
    snap = types.SimpleNamespace()
    snap.tasks = tasks
    return snap


class T1_GetPendingInterruptMessage(unittest.TestCase):
    """T1 — extrai data.message do primeiro interrupt pendente."""

    def _call(self, get_state_return):
        # JobCreationGraph.__new__ dispara get_checkpointer() (lazy-init), que
        # levanta em APP_ENV=production. Chamamos o metodo unbound com um self
        # falso pra isolar a logica de extracao do interrupt.
        graph_mod = importlib.import_module("app.domains.job_creation.graph")
        fn = graph_mod.JobCreationGraph.get_pending_interrupt_message
        fake = types.SimpleNamespace(_graph=mock.Mock())
        fake._graph.get_state.return_value = get_state_return
        return fn(fake, "thread-1")

    def test_extracts_message_from_pending_interrupt(self):
        ask = "Para Desenvolvedor Python Sênior, ainda preciso de: modelo de trabalho."
        snap = _make_snapshot([
            _make_task([
                _make_interrupt({
                    "type": "intake_fields",
                    "stage": "intake",
                    "data": {"message": ask, "missing_fields": ["modelo de trabalho"]},
                })
            ])
        ])
        self.assertEqual(self._call(snap), ask)

    def test_first_interrupt_with_message_wins(self):
        snap = _make_snapshot([
            _make_task([
                _make_interrupt({"data": {}}),  # sem message
                _make_interrupt({"data": {"message": "segunda"}}),
            ])
        ])
        self.assertEqual(self._call(snap), "segunda")


class T2_GetPendingInterruptFailOpen(unittest.TestCase):
    """T2 — fail-open: None em qualquer condicao anomala."""

    def _call(self, get_state_side):
        graph_mod = importlib.import_module("app.domains.job_creation.graph")
        fn = graph_mod.JobCreationGraph.get_pending_interrupt_message
        fake = types.SimpleNamespace(_graph=mock.Mock())
        if isinstance(get_state_side, Exception):
            fake._graph.get_state.side_effect = get_state_side
        else:
            fake._graph.get_state.return_value = get_state_side
        return fn(fake, "t")

    def test_snapshot_none(self):
        self.assertIsNone(self._call(None))

    def test_no_tasks(self):
        self.assertIsNone(self._call(_make_snapshot([])))

    def test_interrupt_value_without_message(self):
        snap = _make_snapshot([_make_task([_make_interrupt({"data": {}})])])
        self.assertIsNone(self._call(snap))

    def test_interrupt_value_not_dict(self):
        snap = _make_snapshot([_make_task([_make_interrupt("string-value")])])
        self.assertIsNone(self._call(snap))

    def test_get_state_raises(self):
        self.assertIsNone(self._call(RuntimeError("checkpointer down")))


class T3_InterruptOverridePrecedence(unittest.TestCase):
    """T3 — _post_process_result prefere _interrupt_msg_override sobre stale msg.

    Coração do fix dos dois loops: mesmo que ws_stage_payload.data.message
    contenha a mensagem stale ("Pode me passar o título..." / "Para avançar..."),
    o override do interrupt vence.
    """

    def test_override_beats_stale_ws_stage_payload(self):
        svc_mod = importlib.import_module(
            "app.domains.job_creation.services.wizard_session_service"
        )
        WizardSessionService = svc_mod.WizardSessionService

        correct = "Para Desenvolvedor Python Sênior, ainda preciso de: modelo de trabalho."
        stale = "Pode me passar o título da vaga ou colar a JD?"

        result = {
            "current_stage": "intake",
            "_interrupt_msg_override": correct,
            "ws_stage_payload": {"data": {"message": stale}},
        }

        message, _payload, _tok = asyncio.run(
            WizardSessionService._post_process_result(
                result=result,
                state={},
                prior_state=None,
                company_id=None,
                session_id="sess-1",
                thread_id="thread-1",
                tokens_emitted=0,
            )
        )
        self.assertEqual(message, correct)
        self.assertNotEqual(message, stale)


class T4_WorkModelStaysBlocking(unittest.TestCase):
    """T4 — anti-regressao: modelo de trabalho e BLOQUEANTE (Fix 2 revertido).

    Per .planning/funil-criacao-vaga-conversacional-plan.md FASE 5, modelo de
    trabalho e campo bloqueante. Com title+seniority mas SEM model, o gate NAO
    pode aprovar — deve continuar pedindo (nao avancar para permission/approved).
    """

    def test_missing_model_blocks_even_with_affirmative(self):
        node_mod = importlib.import_module(
            "app.domains.job_creation.nodes.intake_gate"
        )
        intake_gate_node = node_mod.intake_gate_node

        state = {
            "user_query": "pode criar",
            "raw_input": "quero criar uma vaga",
            "parsed_title": "Desenvolvedor Python Sênior",
            "parsed_seniority": "Sênior",
            "parsed_model": None,  # modelo FALTANDO — bloqueante
            "intake_approved": None,
            "intake_salary_suggested": True,  # ja sugerido (cenario do screenshot)
            "intake_gate_seen_user_query": "quero criar uma vaga",
            "current_stage": "intake",
            "workspace_id": "co",
            "company_id": "co",
        }

        with mock.patch(
            "app.domains.job_creation.nodes.intake_gate._in_graph_runtime",
            return_value=False,
        ), mock.patch(
            "app.domains.job_creation.nodes.intake_gate._safe_fetch_salary",
            return_value={"min": 12000, "max": 18000, "currency": "BRL"},
        ):
            result = intake_gate_node(state)

        # Modelo bloqueante: NAO pode aprovar sem modelo, mesmo com "pode criar".
        self.assertIsNot(
            result.get("intake_approved"), True,
            "Modelo de trabalho e bloqueante — nao deve aprovar sem ele",
        )
        # Deve continuar pedindo campos (requires_approval=True).
        self.assertTrue(result.get("requires_approval"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
