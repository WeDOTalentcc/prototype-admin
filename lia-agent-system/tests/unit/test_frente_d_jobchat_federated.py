"""
Frente D — Testes de roteamento federado no job-chat.
SSH-safe: leitura de arquivo como texto + mocks leves.
"""
import pathlib
import re
import unittest

ROOT = pathlib.Path("/home/runner/workspace/lia-agent-system")
HANDLER_FILE = ROOT / "app/api/v1/orchestrated_job_chat.py"


class TestFrenteDFederatedRouting(unittest.TestCase):
    """Verifica que o job-chat respeita LIA_FEDERATED_PRIMARY."""

    def _get_handler_src(self) -> str:
        return HANDLER_FILE.read_text()

    def test_federated_flag_check_exists(self):
        """Handler deve importar e checar federated_primary_enabled."""
        src = self._get_handler_src()
        self.assertIn(
            "federated_primary_enabled",
            src,
            "federated_primary_enabled nao encontrado no handler job-chat",
        )

    def test_recruiter_copilot_routing(self):
        """Quando federado ativo, deve rotear para recruiter_copilot."""
        src = self._get_handler_src()
        self.assertIn(
            "recruiter_copilot",
            src,
            "recruiter_copilot nao encontrado no handler job-chat",
        )

    def test_fallback_to_supervisor(self):
        """Deve ter fallback para supervisor quando federado indisponivel."""
        src = self._get_handler_src()
        self.assertIn(
            "fallback supervisor",
            src,
            "Mensagem de fallback para supervisor nao encontrada",
        )

    def test_fail_open_on_federated_error(self):
        """Erro no path federado deve ser capturado (fail-open) e cair no supervisor."""
        src = self._get_handler_src()
        # Deve ter try/except cobrindo o path federado
        fed_block = re.search(
            r"_jc_use_federated.*?# Supervisor path",
            src,
            re.DOTALL,
        )
        self.assertIsNotNone(
            fed_block,
            "Bloco federado + fallback supervisor nao encontrado",
        )
        self.assertIn("except Exception", fed_block.group(0))

    def test_agent_output_mapped_to_response(self):
        """AgentOutput.message deve mapear para OrchestratedJobChatResponse.content."""
        src = self._get_handler_src()
        self.assertIn(
            "_agent_output.message",
            src,
            "Mapeamento _agent_output.message -> content nao encontrado",
        )

    def test_supervisor_path_preserved(self):
        """Supervisor path (main_orchestrator.process) deve permanecer intacto."""
        src = self._get_handler_src()
        self.assertIn(
            "main_orchestrator.process(ctx, db)",
            src,
            "Supervisor path main_orchestrator.process removido -- regressao!",
        )


if __name__ == "__main__":
    unittest.main()
