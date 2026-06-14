"""
TDD test — FIX 3: pipeline_monitor.py table name.

O nome correto da tabela e communication_logs (plural).
communication_log (singular) nao existe no schema => relation does not exist.
"""
import re
import inspect
import unittest


class TestPipelineMonitorTableName(unittest.TestCase):

    def _get_module_source(self):
        import sys
        sys.path.insert(0, "/home/runner/workspace/lia-agent-system")
        from app.domains.automation.services import pipeline_monitor
        return inspect.getsource(pipeline_monitor)

    def test_no_bare_communication_log_table(self):
        """
        'FROM communication_log ' (singular, sem 's') NAO deve aparecer no source.
        Causa: relation 'communication_log' does not exist no PostgreSQL.
        """
        source = self._get_module_source()
        # Procura FROM communication_log seguido de espaco, alias, newline ou fim
        # Evita matchear communication_logs (plural)
        invalid = re.compile(r"FROM communication_log(?!s)\b")
        self.assertIsNone(
            invalid.search(source),
            "Bug: 'FROM communication_log' (singular) encontrado. "
            "A tabela correta e 'communication_logs' (plural). "
            "Fix: trocar communication_log por communication_logs"
        )

    def test_communication_logs_plural_present(self):
        """
        'FROM communication_logs' (plural) deve aparecer na query.
        """
        source = self._get_module_source()
        valid = re.compile(r"FROM communication_logs\b")
        self.assertIsNotNone(
            valid.search(source),
            "Nao encontrado 'FROM communication_logs' (plural). "
            "Esperado apos o fix do nome da tabela."
        )


if __name__ == "__main__":
    unittest.main()
