"""Sensor TDD — salary_node consome right_panel_form (refinamento Fase 5).

Pina: quando right_panel_form.salary_min/max estão presentes (recrutador
ajustou via painel), o nó usa esses valores em vez de re-derivar do benchmark.
salary_range como {min, max, currency} também é honrado.

Canonical: mesmo padrão de right_panel_form que intake_gate.py:215.
"""
import pytest
from unittest.mock import MagicMock, patch


def _base_state(**kwargs):
    return {
        "parsed_title": "Engenheiro de Software",
        "parsed_seniority": "senior",
        "workspace_id": "cid-test",
        "salary_benchmark": {"min": 10000, "max": 20000, "p50": 15000, "currency": "BRL"},
        **kwargs,
    }


class TestSalaryNodeRightPanelForm:
    """salary_node lê right_panel_form com precedência sobre benchmark."""

    def _call_node(self, state):
        from app.domains.job_creation.nodes.salary import salary_node
        with patch("app.domains.job_creation.nodes.salary.run_coro_in_threadpool", return_value=None), \
             patch("app.domains.job_creation.graph._emit_fallback_telemetry", return_value=None), \
             patch("app.domains.job_creation.graph._emit_wizard_fallback_metric"):
            return salary_node(state)

    def test_right_panel_salary_min_max_wins_over_benchmark(self):
        """Edição do recrutador via painel vence — não sobrescrever com benchmark."""
        state = _base_state(
            salary_min=None,
            salary_max=None,
            right_panel_form={
                "salary_min": 12000,
                "salary_max": 18000,
            },
        )
        result = self._call_node(state)
        assert result["salary_min"] == 12000, "right_panel_form.salary_min deve vencer"
        assert result["salary_max"] == 18000, "right_panel_form.salary_max deve vencer"

    def test_right_panel_salary_range_object_honored(self):
        """salary_range {min, max} do painel também é honrado."""
        state = _base_state(
            salary_min=None,
            salary_max=None,
            right_panel_form={
                "salary_range": {"min": 11000, "max": 17000, "currency": "BRL"},
            },
        )
        result = self._call_node(state)
        assert result["salary_min"] == 11000
        assert result["salary_max"] == 17000

    def test_right_panel_zero_salary_not_applied(self):
        """Valor 0 do painel não sobrescreve — 0 é ausência de input."""
        state = _base_state(
            salary_min=None,
            salary_max=None,
            right_panel_form={"salary_min": 0, "salary_max": 0},
        )
        result = self._call_node(state)
        # Deve usar benchmark (10000/20000), não os zeros do painel
        assert result.get("salary_min") != 0 or result.get("salary_min") is None

    def test_no_right_panel_uses_existing_state(self):
        """Sem right_panel_form, usa salary_min/max já no state."""
        state = _base_state(salary_min=9000, salary_max=16000)
        result = self._call_node(state)
        assert result["salary_min"] == 9000
        assert result["salary_max"] == 16000

    def test_ws_stage_payload_reflects_panel_values(self):
        """ws_stage_payload.data.salary_min/max reflete valores do painel."""
        state = _base_state(
            salary_min=None,
            salary_max=None,
            right_panel_form={"salary_min": 13000, "salary_max": 19000},
        )
        result = self._call_node(state)
        payload_data = result["ws_stage_payload"]["data"]
        assert payload_data["salary_min"] == 13000
        assert payload_data["salary_max"] == 19000

    def test_salary_confirmed_flag_set_when_panel_provides_range(self):
        """salary_confirmed=True no state quando painel forneceu a faixa."""
        state = _base_state(
            salary_min=None,
            salary_max=None,
            right_panel_form={"salary_min": 14000, "salary_max": 20000},
        )
        result = self._call_node(state)
        assert result.get("salary_confirmed") is True, (
            "salary_confirmed deve ser True quando recrutador confirmou via painel "
            "(sinal para SalaryPanel mostrar faixa como confirmada)"
        )

    def test_salary_confirmed_false_when_only_benchmark(self):
        """salary_confirmed=False quando faixa vem só do benchmark (não confirmada)."""
        state = _base_state(salary_min=None, salary_max=None)
        result = self._call_node(state)
        # benchmark preenche salary_min/max mas não confirma — recrutador ainda precisa revisar
        assert result.get("salary_confirmed") is not True
