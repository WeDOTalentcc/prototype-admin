"""
Frente C — Testes de robustez do ProactiveDetectorService no APScheduler.
SSH-safe: usa leitura de arquivo + mocks, sem importar SQLAlchemy pesado.
"""
import re
import pathlib
import unittest

ROOT = pathlib.Path("/home/runner/workspace/lia-agent-system")
SCHEDULER_FILE = ROOT / "app/domains/automation/services/automation_scheduler.py"


class TestFrenteCSchedulerWiring(unittest.TestCase):
    """Verifica que o job proactive_detection está wirado no AutomationScheduler."""

    def test_run_proactive_detection_method_exists(self):
        """AutomationScheduler deve ter método run_proactive_detection."""
        src = SCHEDULER_FILE.read_text()
        self.assertIn(
            "async def run_proactive_detection",
            src,
            "Método run_proactive_detection não encontrado no AutomationScheduler",
        )

    def test_job_id_registered(self):
        """Job 'proactive_detection' deve estar registrado via add_job."""
        src = SCHEDULER_FILE.read_text()
        self.assertIn(
            '"proactive_detection"',
            src,
            "Job id 'proactive_detection' não encontrado no add_job do scheduler",
        )

    def test_interval_trigger_hourly(self):
        """Job proactive_detection deve usar IntervalTrigger(hours=1)."""
        src = SCHEDULER_FILE.read_text()
        idx = src.find('"proactive_detection"')
        snippet = src[max(0, idx - 300): idx + 300]
        self.assertIn(
            "IntervalTrigger",
            snippet,
            "IntervalTrigger não encontrado perto do job proactive_detection",
        )

    def test_select_active_company_ids_helper_exists(self):
        """_select_active_company_ids deve existir como método estático."""
        src = SCHEDULER_FILE.read_text()
        self.assertIn(
            "_select_active_company_ids",
            src,
            "_select_active_company_ids não encontrado no AutomationScheduler",
        )

    def test_per_company_rollback_on_error(self):
        """run_proactive_detection deve fazer rollback por empresa em caso de erro."""
        src = SCHEDULER_FILE.read_text()
        match = re.search(
            r"async def run_proactive_detection\(.*?(?=\nasync def |\nclass |\Z)",
            src,
            re.DOTALL,
        )
        self.assertIsNotNone(match, "Método run_proactive_detection não encontrado")
        method_body = match.group(0)
        self.assertIn(
            "db.rollback()",
            method_body,
            "db.rollback() não encontrado dentro de run_proactive_detection",
        )

    def test_run_for_company_called(self):
        """run_proactive_detection deve chamar run_for_company no loop."""
        src = SCHEDULER_FILE.read_text()
        match = re.search(
            r"async def run_proactive_detection\(.*?(?=\nasync def |\nclass |\Z)",
            src,
            re.DOTALL,
        )
        method_body = match.group(0)
        self.assertIn(
            "run_for_company",
            method_body,
            "run_for_company não encontrado em run_proactive_detection",
        )


class TestFrenteCIsolamento(unittest.TestCase):
    """Verifica que um detector/empresa falhando não derruba os outros."""

    def test_per_company_inner_try_except(self):
        """Deve haver try/except interno por empresa em run_proactive_detection."""
        src = SCHEDULER_FILE.read_text()
        match = re.search(
            r"async def run_proactive_detection\(.*?(?=\nasync def |\nclass |\Z)",
            src,
            re.DOTALL,
        )
        method_body = match.group(0)
        try_count = method_body.count("try:")
        self.assertGreaterEqual(
            try_count,
            2,
            f"Esperado >= 2 blocos try em run_proactive_detection (outer+inner), encontrado {try_count}",
        )


if __name__ == "__main__":
    unittest.main()
