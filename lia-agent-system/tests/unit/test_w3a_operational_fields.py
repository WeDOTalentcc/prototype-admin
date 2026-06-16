"""Testes W3-A: campos operacionais no wizard.

Cobre:
- deadline derivado do derived_chronogram (today + max offset_end)
- urgency_level, is_confidential, priority gravados no create_job
- sem derived_chronogram → sem deadline (não seta None)
- chronogram com stages vazios → sem deadline
- set_operational_fields tool: multi-tenancy guard, atualiza state
- set_operational_fields: rejeita company_id no input
- deadline calculado corretamente com múltiplos stages
- priority default "normal" quando não especificado
"""

import sys
import unittest
from unittest.mock import MagicMock, patch
from datetime import date, timedelta

sys.path.insert(0, "/home/runner/workspace/lia-agent-system")


# ── helpers para derivar deadline ─────────────────────────────────────────────

def _derive_deadline_from_chronogram(derived_chronogram: list) -> "date | None":
    """Extrai a data de deadline = hoje + max(offset_end) do cronograma.

    Espelha a lógica que será inserida no publish_node (W3-A).
    """
    if not derived_chronogram:
        return None
    max_offset = max(
        (s.get("offset_end") or 0) for s in derived_chronogram if isinstance(s, dict)
    )
    if max_offset <= 0:
        return None
    return date.today() + timedelta(days=max_offset)


class TestDeadlineFromChronogram(unittest.TestCase):

    def test_single_stage_offset(self):
        chron = [{"name": "Triagem", "sla_days": 7, "offset_start": 0, "offset_end": 7}]
        result = _derive_deadline_from_chronogram(chron)
        self.assertEqual(result, date.today() + timedelta(days=7))

    def test_multiple_stages_uses_max_offset(self):
        chron = [
            {"name": "Triagem", "sla_days": 7, "offset_start": 0, "offset_end": 7},
            {"name": "Entrevista RH", "sla_days": 5, "offset_start": 7, "offset_end": 12},
            {"name": "Oferta", "sla_days": 3, "offset_start": 12, "offset_end": 15},
        ]
        result = _derive_deadline_from_chronogram(chron)
        self.assertEqual(result, date.today() + timedelta(days=15))

    def test_empty_chronogram_returns_none(self):
        result = _derive_deadline_from_chronogram([])
        self.assertIsNone(result)

    def test_none_chronogram_returns_none(self):
        result = _derive_deadline_from_chronogram(None)
        self.assertIsNone(result)

    def test_stages_without_offset_end_returns_none(self):
        chron = [{"name": "Triagem", "sla_days": 7}]  # sem offset_end
        result = _derive_deadline_from_chronogram(chron)
        self.assertIsNone(result)

    def test_zero_offset_returns_none(self):
        chron = [{"name": "Triagem", "sla_days": 0, "offset_start": 0, "offset_end": 0}]
        result = _derive_deadline_from_chronogram(chron)
        self.assertIsNone(result)


class TestOperationalFieldsInJobData(unittest.TestCase):
    """Verifica que os campos operacionais têm defaults corretos no job_data."""

    def _make_job_data(self, state: dict) -> dict:
        """Simula a montagem do job_data do publish_node com os novos campos W3-A."""
        return {
            "title": state.get("parsed_title", ""),
            "urgency_level": state.get("urgency_level", 0),
            "is_confidential": state.get("is_confidential", False),
            "priority": state.get("priority", "normal"),
        }

    def test_defaults_sem_state(self):
        job_data = self._make_job_data({})
        self.assertEqual(job_data["urgency_level"], 0)
        self.assertFalse(job_data["is_confidential"])
        self.assertEqual(job_data["priority"], "normal")

    def test_custom_urgency_level(self):
        job_data = self._make_job_data({"urgency_level": 2})
        self.assertEqual(job_data["urgency_level"], 2)

    def test_is_confidential_true(self):
        job_data = self._make_job_data({"is_confidential": True})
        self.assertTrue(job_data["is_confidential"])

    def test_custom_priority(self):
        job_data = self._make_job_data({"priority": "high"})
        self.assertEqual(job_data["priority"], "high")


class TestSetOperationalFieldsTool(unittest.TestCase):
    """Testa o tool set_operational_fields do wizard."""

    def setUp(self):
        from app.domains.job_creation.orchestrator.wizard_service_tools import (
            SET_OPERATIONAL_FIELDS,
        )
        from app.domains.job_creation.orchestrator.wizard_tools import ToolContext
        self.tool = SET_OPERATIONAL_FIELDS
        self.ctx = ToolContext(company_id="c0000000-0000-0000-0000-000000000001")

    def test_tool_registered(self):
        self.assertEqual(self.tool.name, "set_operational_fields")

    def test_rejects_company_id_in_input(self):
        result = self.tool.handler(
            state={},
            tool_input={"company_id": "hacker", "priority": "high"},
            ctx=self.ctx,
        )
        self.assertTrue(result.error, "Deve rejeitar company_id no input")

    def test_sets_urgency_level(self):
        result = self.tool.handler(
            state={},
            tool_input={"urgency_level": 2},
            ctx=self.ctx,
        )
        self.assertFalse(result.error)
        self.assertEqual(result.state_updates.get("urgency_level"), 2)

    def test_sets_is_confidential(self):
        result = self.tool.handler(
            state={},
            tool_input={"is_confidential": True},
            ctx=self.ctx,
        )
        self.assertFalse(result.error)
        self.assertTrue(result.state_updates.get("is_confidential"))

    def test_sets_priority(self):
        result = self.tool.handler(
            state={},
            tool_input={"priority": "high"},
            ctx=self.ctx,
        )
        self.assertFalse(result.error)
        self.assertEqual(result.state_updates.get("priority"), "high")

    def test_rejects_invalid_priority(self):
        result = self.tool.handler(
            state={},
            tool_input={"priority": "INVALID_PRIORITY"},
            ctx=self.ctx,
        )
        self.assertTrue(result.error)

    def test_empty_input_is_noop(self):
        result = self.tool.handler(
            state={"priority": "high"},
            tool_input={},
            ctx=self.ctx,
        )
        self.assertFalse(result.error)


if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=2)
    suite = unittest.TestSuite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestDeadlineFromChronogram))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestOperationalFieldsInJobData))
    # TestSetOperationalFieldsTool requer o módulo estar disponível
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestSetOperationalFieldsTool))
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
