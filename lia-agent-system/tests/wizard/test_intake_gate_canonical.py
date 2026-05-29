"""intake_gate_node canonical — Frente 2 (2026-05-29).

TDD Red → Green para o gate conversacional de intake:
  T1 — "quero criar uma vaga" (sem campos) → gate interrupts, pede campos
  T2 — "Dev Senior Remoto" (todos os campos) → gate interrupts, sugere salário + pede permissão
  T3 — após permissão confirmada → intake_approved=True, rota jd_enrichment

Run standalone:
    python lia-agent-system/tests/wizard/test_intake_gate_canonical.py
"""
from __future__ import annotations

import importlib
import sys
import unittest
from pathlib import Path
from unittest import mock

_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))


def _make_minimal_state(**overrides) -> dict:
    base = {
        "user_query": "quero criar uma vaga",
        "raw_input": "quero criar uma vaga",
        "parsed_title": None,
        "parsed_seniority": None,
        "parsed_model": None,
        "intake_approved": None,
        "intake_salary_suggested": None,
        "intake_gate_seen_user_query": None,
        "current_stage": "intake",
        "workspace_id": "test-company-id",
        "company_id": "test-company-id",
    }
    base.update(overrides)
    return base


class T1_MissingFields(unittest.TestCase):
    """T1 — sem campos obrigatórios → gate deve interromper e perguntar."""

    def test_missing_all_fields_emits_ask_question(self):
        """Quando parsed_title/seniority/model ausentes → interrupt com ask_fields."""
        node_mod = importlib.import_module(
            "app.domains.job_creation.nodes.intake_gate"
        )
        intake_gate_node = node_mod.intake_gate_node

        state = _make_minimal_state()

        # Mock _in_graph_runtime=False (não-LangGraph → retorno síncrono)
        with mock.patch(
            "app.domains.job_creation.nodes.intake_gate._in_graph_runtime",
            return_value=False,
        ):
            result = intake_gate_node(state)

        # Deve retornar estado com mensagem pedindo campos
        self.assertIsNotNone(result)
        ws = result.get("ws_stage_payload") or {}
        data = ws.get("data") or {}
        msg = data.get("message") or ""
        self.assertTrue(
            len(msg) > 10,
            f"Esperava mensagem pedindo campos, got: {msg!r}",
        )
        # Deve indicar requires_approval
        self.assertTrue(result.get("requires_approval"), "requires_approval deve ser True")
        # NÃO deve ter intake_approved=True
        self.assertIsNot(result.get("intake_approved"), True)


class T2_AllFieldsPresent(unittest.TestCase):
    """T2 — todos os campos presentes → gate deve sugerir salário e pedir permissão."""

    def test_all_fields_present_emits_salary_suggestion(self):
        """Com parsed_title/seniority/model → interrupt com salary_suggestion + ask_permission."""
        node_mod = importlib.import_module(
            "app.domains.job_creation.nodes.intake_gate"
        )
        intake_gate_node = node_mod.intake_gate_node

        state = _make_minimal_state(
            parsed_title="Desenvolvedor Backend Senior",
            parsed_seniority="Sênior",
            parsed_model="Remoto",
            user_query="quero criar uma vaga de dev senior remoto",
            raw_input="quero criar uma vaga de dev senior remoto",
        )

        # Mock salary benchmark para retorno previsível
        mock_benchmark = {"min": 12000, "max": 18000, "currency": "BRL", "confidence": 0.8}

        with mock.patch(
            "app.domains.job_creation.nodes.intake_gate._in_graph_runtime",
            return_value=False,
        ), mock.patch(
            "app.domains.job_creation.nodes.intake_gate._safe_fetch_salary",
            return_value=mock_benchmark,
        ):
            result = intake_gate_node(state)

        self.assertIsNotNone(result)
        ws = result.get("ws_stage_payload") or {}
        data = ws.get("data") or {}
        msg = data.get("message") or ""
        # Deve conter menção ao salário
        self.assertTrue(
            "R$" in msg or "salário" in msg.lower() or "mercado" in msg.lower() or "faixa" in msg.lower(),
            f"Esperava mensagem de sugestão salarial, got: {msg!r}",
        )
        # Deve indicar requires_approval
        self.assertTrue(result.get("requires_approval"), "requires_approval deve ser True")
        # NÃO aprovado ainda
        self.assertIsNot(result.get("intake_approved"), True)


class T3_PermissionGranted(unittest.TestCase):
    """T3 — após permissão → intake_approved=True, rota jd_enrichment."""

    def test_permission_granted_sets_approved(self):
        """Com intake_salary_suggested=True e user_query='pode criar' → intake_approved=True."""
        node_mod = importlib.import_module(
            "app.domains.job_creation.nodes.intake_gate"
        )
        intake_gate_node = node_mod.intake_gate_node
        route_fn = node_mod.route_after_intake_gate

        state = _make_minimal_state(
            parsed_title="Desenvolvedor Backend Senior",
            parsed_seniority="Sênior",
            parsed_model="Remoto",
            user_query="pode criar",
            raw_input="quero criar uma vaga de dev senior remoto",
            intake_salary_suggested=True,
            intake_gate_seen_user_query="quero criar uma vaga de dev senior remoto",
        )

        with mock.patch(
            "app.domains.job_creation.nodes.intake_gate._in_graph_runtime",
            return_value=False,
        ), mock.patch(
            "app.domains.job_creation.nodes.intake_gate._safe_fetch_salary",
            return_value={"min": 12000, "max": 18000, "currency": "BRL"},
        ):
            result = intake_gate_node(state)

        self.assertIsNotNone(result)
        self.assertTrue(
            result.get("intake_approved") is True,
            f"Esperava intake_approved=True, got: {result.get('intake_approved')!r}",
        )
        self.assertFalse(result.get("requires_approval"), "requires_approval deve ser False")

        # Rota deve ir para jd_enrichment
        route = route_fn(result)
        self.assertEqual(
            route, "jd_enrichment",
            f"Esperava rota 'jd_enrichment', got: {route!r}",
        )

    def test_negative_response_does_not_approve(self):
        """Com resposta não-afirmativa → intake_approved permanece None."""
        node_mod = importlib.import_module(
            "app.domains.job_creation.nodes.intake_gate"
        )
        intake_gate_node = node_mod.intake_gate_node

        state = _make_minimal_state(
            parsed_title="Desenvolvedor Backend Senior",
            parsed_seniority="Sênior",
            parsed_model="Remoto",
            user_query="não tenho certeza ainda",
            raw_input="quero criar uma vaga de dev senior remoto",
            intake_salary_suggested=True,
            intake_gate_seen_user_query="quero criar uma vaga de dev senior remoto",
        )

        with mock.patch(
            "app.domains.job_creation.nodes.intake_gate._in_graph_runtime",
            return_value=False,
        ), mock.patch(
            "app.domains.job_creation.nodes.intake_gate._safe_fetch_salary",
            return_value={"min": 12000, "max": 18000, "currency": "BRL"},
        ):
            result = intake_gate_node(state)

        self.assertIsNotNone(result)
        self.assertIsNot(
            result.get("intake_approved"), True,
            "Resposta negativa NÃO deve setar intake_approved=True",
        )


class T4_RouteAfterIntakeGate(unittest.TestCase):
    """T4 — route_after_intake_gate retorna rota correta."""

    def test_approved_routes_to_jd_enrichment(self):
        node_mod = importlib.import_module(
            "app.domains.job_creation.nodes.intake_gate"
        )
        route_fn = node_mod.route_after_intake_gate
        state = {"intake_approved": True}
        self.assertEqual(route_fn(state), "jd_enrichment")

    def test_not_approved_routes_to_end(self):
        node_mod = importlib.import_module(
            "app.domains.job_creation.nodes.intake_gate"
        )
        route_fn = node_mod.route_after_intake_gate
        self.assertEqual(route_fn({"intake_approved": None}), "end")
        self.assertEqual(route_fn({"intake_approved": False}), "end")
        self.assertEqual(route_fn({}), "end")


if __name__ == "__main__":
    unittest.main(verbosity=2)
