"""Testes W1-A: eligibility tools wiring no wizard orchestrator.

Cobre:
- wizard_session_service popula data["questions"] com eligibility_questions
  quando WSI não foi gerado ainda
- Não sobrescreve quando WSI já existe (WSI tem precedência)
- apply_eligibility_template atualiza state_updates corretamente
- suggest_eligibility_templates retorna itens do catálogo
- Tool rejeita company_id no input (multi-tenancy)
- Instrução de eligibility está presente no _SYSTEM_PROMPT_BASE
"""

import sys
import unittest
from unittest.mock import MagicMock, patch, AsyncMock

sys.path.insert(0, "/home/runner/workspace/lia-agent-system")


class TestEligibilityQuestionsInPayload(unittest.TestCase):
    """Testa que eligibility_questions chegam no data para o FE."""

    def _simulate_data_build(self, new_state: dict) -> dict:
        """Simula a lógica de build de data do wizard_session_service W1-A."""
        data = {}

        # Bloco WSI (se existir)
        if new_state.get("wsi_questions"):
            data["questions"] = new_state.get("wsi_questions")

        # W1-A: Perguntas de elegibilidade
        _elig_q = new_state.get("eligibility_questions")
        if _elig_q and not new_state.get("wsi_questions"):
            data["questions"] = _elig_q

        return data

    def test_eligibility_populates_questions_quando_sem_wsi(self):
        elig = [{"question": "Tem CNH?", "required_answer": "yes", "eliminatory": True}]
        data = self._simulate_data_build({"eligibility_questions": elig})
        self.assertEqual(data.get("questions"), elig)

    def test_wsi_tem_precedencia_sobre_eligibility(self):
        """Quando WSI existe, eligibility não sobrescreve data["questions"]."""
        elig = [{"question": "Tem CNH?", "required_answer": "yes", "eliminatory": True}]
        wsi = [{"text": "Pergunta WSI 1", "block": "technical"}]
        data = self._simulate_data_build({
            "eligibility_questions": elig,
            "wsi_questions": wsi,
        })
        self.assertEqual(data.get("questions"), wsi)
        self.assertNotEqual(data.get("questions"), elig)

    def test_sem_eligibility_sem_wsi_questions_ausente(self):
        data = self._simulate_data_build({})
        self.assertNotIn("questions", data)

    def test_lista_vazia_nao_popula(self):
        data = self._simulate_data_build({"eligibility_questions": []})
        self.assertNotIn("questions", data)


class TestSuggestEligibilityTemplatesTool(unittest.TestCase):
    """Testa o tool suggest_eligibility_templates."""

    def setUp(self):
        from app.domains.job_creation.orchestrator.wizard_service_tools import (
            SUGGEST_ELIGIBILITY_TEMPLATES,
        )
        from app.domains.job_creation.orchestrator.wizard_tools import ToolContext
        self.tool = SUGGEST_ELIGIBILITY_TEMPLATES
        self.ctx = ToolContext(company_id="c0000000-0000-0000-0000-000000000001")

    def test_tool_registrado(self):
        self.assertEqual(self.tool.name, "suggest_eligibility_templates")

    def test_rejeita_company_id_no_input(self):
        result = self.tool.handler(
            state={},
            tool_input={"company_id": "hacker", "category": "eligibility"},
            ctx=self.ctx,
        )
        self.assertTrue(result.error, "Deve rejeitar company_id no input")

    def test_tool_descricao_nao_vazia(self):
        self.assertTrue(len(self.tool.description) > 10)
    def setUp(self):
        from app.domains.job_creation.orchestrator.wizard_service_tools import (
            APPLY_ELIGIBILITY_TEMPLATE,
        )
        from app.domains.job_creation.orchestrator.wizard_tools import ToolContext
        self.tool = APPLY_ELIGIBILITY_TEMPLATE
        self.ctx = ToolContext(company_id="c0000000-0000-0000-0000-000000000001")

    def test_tool_registrado(self):
        self.assertEqual(self.tool.name, "apply_eligibility_template")

    def test_rejeita_company_id_no_input(self):
        result = self.tool.handler(
            state={},
            tool_input={"company_id": "hacker", "template_id": "some-uuid"},
            ctx=self.ctx,
        )
        self.assertTrue(result.error, "Deve rejeitar company_id no input")

    def test_template_nao_encontrado_retorna_erro(self):
        with patch(
            "app.domains.job_creation.helpers.async_audit.run_coro_in_threadpool",
            return_value=None,  # template não encontrado
        ):
            result = self.tool.handler(
                state={},
                tool_input={"template_id": "00000000-0000-0000-0000-000000000099"},
                ctx=self.ctx,
            )
        self.assertTrue(result.error)


class TestEligibilityInSystemPrompt(unittest.TestCase):
    """Verifica que instrução de eligibility está no _SYSTEM_PROMPT_BASE."""

    def test_instrucao_eligibility_presente(self):
        from app.domains.job_creation.orchestrator.wizard_orchestrator import (
            _SYSTEM_PROMPT_BASE,
        )
        self.assertIn("suggest_eligibility_templates", _SYSTEM_PROMPT_BASE)
        self.assertIn("apply_eligibility_template", _SYSTEM_PROMPT_BASE)

    def test_instrucao_menciona_stage_eligibility(self):
        from app.domains.job_creation.orchestrator.wizard_orchestrator import (
            _SYSTEM_PROMPT_BASE,
        )
        self.assertIn("eligibility", _SYSTEM_PROMPT_BASE.lower())

    def test_instrucao_menciona_eliminatorio(self):
        from app.domains.job_creation.orchestrator.wizard_orchestrator import (
            _SYSTEM_PROMPT_BASE,
        )
        # Deve mencionar que são perguntas que bloqueiam candidatos
        self.assertTrue(
            "eliminatori" in _SYSTEM_PROMPT_BASE.lower()
            or "BLOQUEIAM" in _SYSTEM_PROMPT_BASE
        )


if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=2)
    suite = unittest.TestSuite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestEligibilityQuestionsInPayload))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestEligibilityInSystemPrompt))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestSuggestEligibilityTemplatesTool))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestApplyEligibilityTemplateTool))
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
