"""intake_gate permission classification via LLM (Paulo 2026-05-30).

Raiz do "fluxo robotico": o intake_gate aprovava permissao por REGEX, e
"acho que vamos trabalhar com salario de 15.000" casava "vamos" → falso
approve → wizard pulava pro jd_enrichment → "cole a JD" → colapso.

Fix canonical: classificacao via wizard_gate_classifier (Haiku), stage
intake_permission, com intent provide_field_data que INGERE o dado em vez
de aprovar. Regex vira fallback fail-open.

Sentinelas (LLM mockado — deterministico):
  T1 — provide_field_data (salario) NAO aprova; ingere salary_min/max; re-pergunta.
  T2 — approve → intake_approved=True.
  T3 — select_compact → screening_mode=compact + aprovado.
  T4 — confidence<0.7 → nao aprova (re-pergunta).
  T5 — provide_field_data (gestor+email) ingere parsed_manager_*.
  T6 — fallback regex quando o classifier levanta excecao.
"""
from __future__ import annotations

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


def _fake_output(intent, confidence=0.95, extracted=None, reply="ok"):
    return types.SimpleNamespace(
        intent=intent,
        confidence=confidence,
        extracted_data=extracted or {},
        conversational_reply=reply,
    )


def _state_substate3(user_query):
    return {
        "user_query": user_query,
        "raw_input": "quero criar uma vaga de dev python senior",
        "parsed_title": "Desenvolvedor Python Sênior",
        "parsed_seniority": "Sênior",
        "parsed_model": "hibrido",
        "intake_approved": None,
        "intake_salary_suggested": True,  # ja sugerido → vai pro sub-estado 3
        "intake_gate_seen_user_query": "modelo hibrido de trabalho",  # != user_query
        "current_stage": "intake",
        "workspace_id": "co", "company_id": "co",
    }


def _run_with_classifier(state, fake_out=None, raise_exc=False):
    """Roda intake_gate_node com o LLM classifier mockado."""
    node_mod = importlib.import_module("app.domains.job_creation.nodes.intake_gate")
    fake_classifier = mock.Mock()

    async def _classify(**kwargs):
        if raise_exc:
            raise RuntimeError("LLM down")
        return fake_out

    fake_classifier.classify = _classify

    with mock.patch(
        "app.domains.job_creation.nodes.intake_gate._in_graph_runtime",
        return_value=False,
    ), mock.patch(
        "app.domains.job_creation.services.wizard_gate_classifier.get_wizard_gate_classifier",
        return_value=fake_classifier,
    ), mock.patch(
        "app.domains.job_creation.nodes.intake_gate._safe_fetch_salary",
        return_value={"min": 14000, "max": 26000, "currency": "BRL"},
    ), mock.patch(
        "app.domains.job_creation.nodes.intake_gate._resolve_confirmed_competencies",
        return_value=([], [], None),
    ):
        return node_mod.intake_gate_node(state)


class T1_SalaryNotApprove(unittest.TestCase):
    def test_vamos_salario_does_not_approve(self):
        state = _state_substate3("acho que vamos trabalhar com salario de 15.000,00")
        out = _fake_output(
            "provide_field_data",
            extracted={"salary_min": 15000, "salary_max": 15000},
            reply="Anotei o salário de R$ 15.000. Compacto ou Completo?",
        )
        result = _run_with_classifier(state, out)
        # NAO pode aprovar (era o bug do "vamos")
        self.assertIsNot(result.get("intake_approved"), True)
        self.assertTrue(result.get("requires_approval"))
        # Ingeriu o salario
        self.assertEqual(result.get("salary_min"), 15000)
        self.assertEqual(result.get("salary_max"), 15000)
        # Re-pergunta com a fala do LLM
        msg = ((result.get("ws_stage_payload") or {}).get("data") or {}).get("message", "")
        self.assertIn("Compacto", msg)


class T2_Approve(unittest.TestCase):
    def test_approve_sets_approved(self):
        state = _state_substate3("pode criar")
        out = _fake_output("approve", reply="Criando a vaga.")
        result = _run_with_classifier(state, out)
        self.assertIs(result.get("intake_approved"), True)
        self.assertFalse(result.get("requires_approval"))


class T3_SelectCompact(unittest.TestCase):
    def test_select_compact_sets_mode(self):
        state = _state_substate3("compacto")
        out = _fake_output("select_compact", extracted={"mode": "compact"})
        result = _run_with_classifier(state, out)
        self.assertIs(result.get("intake_approved"), True)
        self.assertEqual(result.get("screening_mode"), "compact")


class T4_LowConfidence(unittest.TestCase):
    def test_low_confidence_does_not_approve(self):
        state = _state_substate3("hmm sei la")
        out = _fake_output("approve", confidence=0.4)  # baixa confianca
        result = _run_with_classifier(state, out)
        self.assertIsNot(result.get("intake_approved"), True)
        self.assertTrue(result.get("requires_approval"))


class T5_ProvideManager(unittest.TestCase):
    def test_manager_ingested(self):
        state = _state_substate3("o gestor é a Ana, ana@empresa.com")
        out = _fake_output(
            "provide_field_data",
            extracted={"parsed_manager_name": "Ana", "parsed_manager_email": "ana@empresa.com"},
            reply="Anotei a gestora Ana. Compacto ou Completo?",
        )
        result = _run_with_classifier(state, out)
        self.assertIsNot(result.get("intake_approved"), True)
        self.assertEqual(result.get("parsed_manager_name"), "Ana")
        self.assertEqual(result.get("parsed_manager_email"), "ana@empresa.com")


class T6_RegexFallback(unittest.TestCase):
    def test_classifier_exception_falls_back_to_regex(self):
        # LLM levanta → cai no regex. "compacto" deve aprovar via regex.
        state = _state_substate3("compacto")
        result = _run_with_classifier(state, fake_out=None, raise_exc=True)
        self.assertIs(result.get("intake_approved"), True)
        self.assertEqual(result.get("screening_mode"), "compact")


if __name__ == "__main__":
    unittest.main(verbosity=2)
