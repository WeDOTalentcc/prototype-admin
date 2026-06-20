"""
tests/wizard/test_derive_wizard_stage_calibration.py

Testa _derive_wizard_stage para garantia "não-preso" do Bug 13.
Função de módulo pura — sem mock, sem __new__, import direto.
"""
from __future__ import annotations
import pytest
from app.domains.job_creation.services.wizard_session_service import (
    _derive_wizard_stage,
)

_BASE_CANDIDATES = [
    {"id": "cand-aaa", "name": "Ana Lima",   "score": 0.88, "decision": None},
    {"id": "cand-bbb", "name": "Bruno Melo", "score": 0.75, "decision": None},
]


class TestDeriveWizardStageCalibration:
    """Bug 13 — stage derivation para fluxo de calibração."""

    def test_calibration_state_returns_calibration(self):
        """State com calibration_candidates + job_id sem flag → stage=calibration."""
        state = {
            "job_id": "job-test-001",
            "calibration_candidates": _BASE_CANDIDATES,
            # calibration_complete ausente
        }
        assert _derive_wizard_stage(state) == "calibration", (
            "Esperado 'calibration' quando calibration_candidates presente, "
            "job_id presente, calibration_complete ausente."
        )

    def test_calibration_complete_exits_to_handoff(self):
        """calibration_complete=True → stage sai de 'calibration' para 'handoff'."""
        state = {
            "job_id": "job-test-001",
            "calibration_candidates": _BASE_CANDIDATES,
            "calibration_complete": True,
        }
        stage = _derive_wizard_stage(state)
        assert stage != "calibration", (
            "BUG: wizard preso em 'calibration' mesmo com calibration_complete=True. "
            f"Retornou: {stage!r}"
        )
        assert stage == "handoff", (
            f"Esperado 'handoff' após calibration_complete=True, got {stage!r}"
        )

    def test_job_id_without_calibration_candidates_is_handoff(self):
        """job_id sem calibration_candidates → 'handoff' (comportamento antigo preservado)."""
        state = {
            "job_id": "job-test-001",
            # calibration_candidates ausente
        }
        assert _derive_wizard_stage(state) == "handoff", (
            "job_id sem calibration_candidates deve continuar retornando 'handoff' "
            "(não deve quebrar fluxo existente)."
        )
