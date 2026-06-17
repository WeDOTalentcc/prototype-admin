"""TDD Fase 1 — modo de triagem no intake + SCREENING_MODE_CONFIG canonical.

Testa:
  1. SCREENING_MODE_CONFIG: compact=7q, full=12q, tem estimated_minutes
  2. _classify_mode_and_permission: extrai modo e permissão de resposta do recrutador
  3. intake_gate_node: mensagem inclui opções de modo; captura modo da resposta
  4. competency_gate_node: retorna cedo quando screening_mode já está setado

Run standalone:
    python lia-agent-system/tests/wizard/test_wizard_intake_screening_mode_fase1.py
"""
from __future__ import annotations
import sys
import importlib
import unittest
from pathlib import Path
from unittest import mock

_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[2]  # worktree/lia-agent-system -> worktree -> repo
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))


# ── 1. SCREENING_MODE_CONFIG ─────────────────────────────────────────────────

class TestScreeningModeConfig(unittest.TestCase):
    def test_compact_total_questions_is_7(self):
        from app.domains.job_creation.helpers.screening_mode_config import SCREENING_MODE_CONFIG
        self.assertEqual(SCREENING_MODE_CONFIG["compact"]["total_questions"], 7)

    def test_full_total_questions_is_12(self):
        from app.domains.job_creation.helpers.screening_mode_config import SCREENING_MODE_CONFIG
        self.assertEqual(SCREENING_MODE_CONFIG["full"]["total_questions"], 12)

    def test_both_modes_have_estimated_minutes(self):
        from app.domains.job_creation.helpers.screening_mode_config import SCREENING_MODE_CONFIG
        self.assertIn("estimated_minutes", SCREENING_MODE_CONFIG["compact"])
        self.assertIn("estimated_minutes", SCREENING_MODE_CONFIG["full"])
        self.assertGreater(SCREENING_MODE_CONFIG["compact"]["estimated_minutes"], 0)
        self.assertGreater(SCREENING_MODE_CONFIG["full"]["estimated_minutes"], 0)

    def test_full_has_more_minutes_than_compact(self):
        from app.domains.job_creation.helpers.screening_mode_config import SCREENING_MODE_CONFIG
        self.assertGreater(
            SCREENING_MODE_CONFIG["full"]["estimated_minutes"],
            SCREENING_MODE_CONFIG["compact"]["estimated_minutes"],
        )


# ── 2. _classify_mode_and_permission ─────────────────────────────────────────

class TestClassifyModeAndPermission(unittest.TestCase):
    def _fn(self):
        return importlib.import_module(
            "app.domains.job_creation.nodes.intake_gate"
        )._classify_mode_and_permission

    def test_compact_keyword_extracts_compact(self):
        fn = self._fn()
        mode, _ = fn("quero compacto")
        self.assertEqual(mode, "compact")

    def test_compacto_accent_variant(self):
        fn = self._fn()
        mode, _ = fn("modo compacto por favor")
        self.assertEqual(mode, "compact")

    def test_full_keyword_extracts_full(self):
        fn = self._fn()
        mode, _ = fn("prefiro completo")
        self.assertEqual(mode, "full")

    def test_12q_keyword_extracts_full(self):
        fn = self._fn()
        mode, _ = fn("12 perguntas")
        self.assertEqual(mode, "full")

    def test_7q_keyword_extracts_compact(self):
        fn = self._fn()
        mode, _ = fn("7 perguntas")
        self.assertEqual(mode, "compact")

    def test_mode_selection_implies_approval(self):
        fn = self._fn()
        _, approved = fn("compacto")
        self.assertTrue(approved, "Selecionar modo implica aprovação")

    def test_combined_mode_and_explicit_approval(self):
        fn = self._fn()
        mode, approved = fn("sim, compacto, pode criar")
        self.assertEqual(mode, "compact")
        self.assertTrue(approved)

    def test_approval_without_mode(self):
        fn = self._fn()
        mode, approved = fn("pode criar")
        self.assertIsNone(mode)
        self.assertTrue(approved)

    def test_no_approval_no_mode(self):
        fn = self._fn()
        mode, approved = fn("preciso pensar ainda")
        self.assertIsNone(mode)
        self.assertFalse(approved)

    def test_full_combined(self):
        fn = self._fn()
        mode, approved = fn("pode criar, completo")
        self.assertEqual(mode, "full")
        self.assertTrue(approved)


# ── 3. intake_gate_node — mensagem inclui opções de modo ─────────────────────

def _base_salary_state(**overrides):
    base = {
        "parsed_title": "Engenheiro de Software",
        "parsed_seniority": "senior",
        "parsed_model": "remoto",
        "intake_salary_suggested": None,
        "intake_approved": None,
        "screening_mode": None,
        "user_query": "quero criar uma vaga de engenheiro senior remoto",
        "raw_input": "quero criar uma vaga de engenheiro senior remoto",
        "intake_gate_seen_user_query": None,
        "current_stage": "intake",
        "workspace_id": "cid-test",
        "company_id": "cid-test",
    }
    base.update(overrides)
    return base


class TestIntakeGatePermissionMessage(unittest.TestCase):
    """Garante que a mensagem de permissão inclui opções de modo."""

    def _build_msg(self, benchmark=None):
        node_mod = importlib.import_module("app.domains.job_creation.nodes.intake_gate")
        return node_mod._build_permission_message(
            benchmark=benchmark or {"min": 15000, "max": 20000},
            title="Dev Python",
            seniority="senior",
            model="remoto",
        )

    def test_message_includes_compact_option(self):
        txt = self._build_msg()
        self.assertTrue(
            "ompacto" in txt or "compact" in txt.lower(),
            f"Mensagem deve mencionar Compacto. Got: {txt!r}",
        )

    def test_message_includes_full_option(self):
        txt = self._build_msg()
        self.assertTrue(
            "ompleto" in txt or "full" in txt.lower(),
            f"Mensagem deve mencionar Completo. Got: {txt!r}",
        )

    def test_message_includes_question_counts(self):
        from app.domains.job_creation.helpers.screening_mode_config import SCREENING_MODE_CONFIG
        txt = self._build_msg()
        compact_q = str(SCREENING_MODE_CONFIG["compact"]["total_questions"])
        full_q = str(SCREENING_MODE_CONFIG["full"]["total_questions"])
        self.assertIn(compact_q, txt, f"Mensagem deve conter '{compact_q}' (compact questions). Got: {txt!r}")
        self.assertIn(full_q, txt, f"Mensagem deve conter '{full_q}' (full questions). Got: {txt!r}")

    def test_fallback_message_also_includes_mode_options(self):
        node_mod = importlib.import_module("app.domains.job_creation.nodes.intake_gate")
        txt = node_mod._build_permission_message(
            benchmark=None,  # no benchmark data
            title="Dev",
            seniority="pleno",
            model="híbrido",
        )
        self.assertTrue("ompacto" in txt or "compact" in txt.lower(), f"Fallback também deve ter Compacto. Got: {txt!r}")
        self.assertTrue("ompleto" in txt or "full" in txt.lower(), f"Fallback também deve ter Completo. Got: {txt!r}")


class TestIntakeGateCapturesMode(unittest.TestCase):
    """intake_gate_node captura modo da resposta do recrutador."""

    def _run(self, user_query, **overrides):
        node_mod = importlib.import_module("app.domains.job_creation.nodes.intake_gate")
        state = _base_salary_state(
            intake_salary_suggested=True,
            user_query=user_query,
            raw_input="quero criar vaga engenheiro senior remoto",
            intake_gate_seen_user_query="quero criar vaga engenheiro senior remoto",
            **overrides,
        )
        with mock.patch("app.domains.job_creation.nodes.intake_gate._in_graph_runtime", return_value=False), \
             mock.patch("app.domains.job_creation.nodes.intake_gate._safe_fetch_salary", return_value={"min": 10000, "max": 15000}):
            return node_mod.intake_gate_node(state)

    def test_compact_response_sets_screening_mode(self):
        result = self._run("compacto, pode criar")
        self.assertEqual(result.get("screening_mode"), "compact",
                         f"screening_mode deve ser 'compact'. Got: {result.get('screening_mode')!r}")

    def test_compact_sets_intake_approved(self):
        result = self._run("compacto, pode criar")
        self.assertTrue(result.get("intake_approved") is True,
                        f"intake_approved deve ser True. Got: {result.get('intake_approved')!r}")

    def test_full_response_sets_screening_mode(self):
        result = self._run("pode criar, completo")
        self.assertEqual(result.get("screening_mode"), "full",
                         f"screening_mode deve ser 'full'. Got: {result.get('screening_mode')!r}")

    def test_approval_only_no_mode_preserved(self):
        """'pode criar' sem modo → aprovado mas screening_mode=None (cai no competency_gate)."""
        result = self._run("pode criar")
        self.assertTrue(result.get("intake_approved") is True,
                        f"intake_approved deve ser True. Got: {result.get('intake_approved')!r}")
        self.assertIsNone(result.get("screening_mode"),
                          f"screening_mode deve ser None quando não especificado. Got: {result.get('screening_mode')!r}")

    def test_mode_only_also_approves(self):
        """Somente 'compacto' (sem 'pode criar') deve também aprovar."""
        result = self._run("compacto")
        self.assertEqual(result.get("screening_mode"), "compact")
        self.assertTrue(result.get("intake_approved") is True)


# ── 4. competency_gate_node — retorna cedo quando modo já setado ──────────────

class TestCompetencyGateEarlyReturn(unittest.TestCase):
    def _run_with_mode(self, mode):
        node_mod = importlib.import_module("app.domains.job_creation.nodes.competency_gate")
        state = {
            "screening_mode": mode,
            "current_stage": "competency",
            "seniority_resolved": "senior",
            "competency_recommendation": None,
            "gate_resume_message": "",
            "user_query": "",
            "gate_seen_user_query": "",
            "gate_last_intent": None,
            "fairness_blocked": None,
        }
        # In non-runtime, just call directly (no interrupt fires)
        with mock.patch("app.domains.job_creation.nodes.competency_gate._in_graph_runtime", return_value=False):
            return node_mod.competency_gate_node(state)

    def test_compact_mode_already_set_preserves_mode(self):
        result = self._run_with_mode("compact")
        self.assertEqual(result.get("screening_mode"), "compact",
                         "screening_mode deve ser preservado")

    def test_full_mode_already_set_preserves_mode(self):
        result = self._run_with_mode("full")
        self.assertEqual(result.get("screening_mode"), "full",
                         "screening_mode deve ser preservado")

    def test_compact_mode_sets_terminal_intent(self):
        result = self._run_with_mode("compact")
        self.assertEqual(result.get("gate_last_intent"), "select_compact",
                         "gate_last_intent deve indicar modo selecionado")

    def test_full_mode_sets_terminal_intent(self):
        result = self._run_with_mode("full")
        self.assertEqual(result.get("gate_last_intent"), "select_full",
                         "gate_last_intent deve indicar modo selecionado")

    def test_compact_gate_clarify_message_set(self):
        result = self._run_with_mode("compact")
        clarify = result.get("gate_clarify_message") or ""
        self.assertGreater(len(clarify), 5,
                           "gate_clarify_message deve ter conteúdo para o UI")
        self.assertTrue("ompacto" in clarify or "7" in clarify,
                        f"clarify deve mencionar Compacto ou 7. Got: {clarify!r}")

    def test_no_llm_called_when_mode_set(self):
        """LLM não deve ser chamado quando modo já está definido."""
        node_mod = importlib.import_module("app.domains.job_creation.nodes.competency_gate")
        state = {
            "screening_mode": "compact",
            "current_stage": "competency",
            "seniority_resolved": "senior",
            "gate_resume_message": "",
            "user_query": "qualquer mensagem aqui",
            "gate_seen_user_query": "",
            "gate_last_intent": None,
            "fairness_blocked": None,
        }
        # If early-return works, LLM helpers in graph.py are never reached
        # We patch _extract_last_turns as a proxy (only called if LLM path is taken)
        with mock.patch("app.domains.job_creation.nodes.competency_gate._in_graph_runtime", return_value=False):
            with mock.patch(
                "app.domains.job_creation.graph._extract_last_turns"
            ) as mock_extract:
                result = node_mod.competency_gate_node(state)

        mock_extract.assert_not_called()
        self.assertEqual(result.get("screening_mode"), "compact")


if __name__ == "__main__":
    unittest.main(verbosity=2)
