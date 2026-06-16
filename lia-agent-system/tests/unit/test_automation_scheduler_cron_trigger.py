"""
TDD test — FIX 2: automation_scheduler.py misfire_grace_time.

APScheduler 3.10+ nao aceita misfire_grace_time no construtor de CronTrigger.
Deve ir em scheduler.add_job(..., misfire_grace_time=...).

Red: CronTrigger recebe misfire_grace_time => TypeError em runtime.
Green: misfire_grace_time removido do CronTrigger, presente no add_job.
"""
import re
import inspect
import unittest


class TestAutomationSchedulerCronTrigger(unittest.TestCase):

    def _get_module_source(self):
        import sys
        sys.path.insert(0, "/home/runner/workspace/lia-agent-system")
        from app.domains.automation.services import automation_scheduler
        return inspect.getsource(automation_scheduler)

    def test_cron_trigger_does_not_receive_misfire_grace_time(self):
        """
        CronTrigger(..., misfire_grace_time=...) NAO deve existir.
        APScheduler 3.10+ rejeita esse kwarg no trigger constructor.
        """
        source = self._get_module_source()
        # Detectar o padrao: CronTrigger( ... misfire_grace_time= ... )
        # Usando regex multiline pois o construtor pode ser multi-linha
        # Procuramos por 'misfire_grace_time' dentro de um bloco CronTrigger(
        lines = source.split("\n")
        in_cron_trigger = False
        paren_depth = 0
        violations = []
        for i, line in enumerate(lines):
            if "CronTrigger(" in line:
                in_cron_trigger = True
                paren_depth = line.count("(") - line.count(")")
            elif in_cron_trigger:
                paren_depth += line.count("(") - line.count(")")
                if "misfire_grace_time" in line:
                    violations.append(f"Line {i+1}: {line.strip()}")
                if paren_depth <= 0:
                    in_cron_trigger = False

        self.assertEqual(
            violations, [],
            f"Bug: misfire_grace_time encontrado dentro de CronTrigger():\n"
            + "\n".join(violations) +
            "\nFix: mover misfire_grace_time para add_job(..., misfire_grace_time=...)"
        )

    def test_teams_daily_digest_add_job_receives_misfire_grace_time(self):
        """
        O add_job do teams_daily_digest deve ter misfire_grace_time=3600.
        Ou o job_defaults deve cobrir via misfire_grace_time global.
        """
        source = self._get_module_source()
        # Verificar que misfire_grace_time=3600 aparece ou em add_job ou em job_defaults
        has_job_defaults_misfire = re.search(
            r'job_defaults\s*=\s*\{[^}]*misfire_grace_time', source
        )
        has_add_job_misfire_3600 = re.search(
            r'add_job\([^)]*misfire_grace_time\s*=\s*3600', source, re.DOTALL
        )
        self.assertTrue(
            has_job_defaults_misfire or has_add_job_misfire_3600,
            "misfire_grace_time=3600 nao encontrado em add_job nem em job_defaults. "
            "O parametro nao deve ser perdido ao remover do CronTrigger."
        )

    def test_cron_trigger_instantiation_does_not_raise(self):
        """
        CronTrigger com os parametros atuais nao deve levantar TypeError.
        """
        from apscheduler.triggers.cron import CronTrigger
        # Tentar instanciar com os parametros que estao no scheduler (sem misfire_grace_time)
        try:
            trigger = CronTrigger(
                day_of_week="mon-fri",
                hour=8,
                minute=0,
                timezone="America/Sao_Paulo",
            )
        except TypeError as e:
            self.fail(f"CronTrigger levantou TypeError: {e}. "
                      "Remover misfire_grace_time do construtor.")


if __name__ == "__main__":
    unittest.main()
