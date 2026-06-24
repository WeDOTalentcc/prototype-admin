"""Ficha viva builder — extracted from nodes/intake_gate.py (Fase 8 A1).

Builds the ws_stage_payload.data dict for the live vacancy card panel.
Used by both intake_gate_node (graph) and wizard_session_service (orchestrator).
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from app.domains.job_creation.state import JobCreationState


def build_ficha_data(
    state: JobCreationState,
    message: str,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build the cumulative ficha payload (Phase 5).

    Every intake_gate response carries parsed_* + screening_mode + salary
    (+ confirmed_* when present) in the SAME payload, because useWizardFlow
    (FE) replaces stageData wholesale — it does not merge.
    """
    data: Dict[str, Any] = {
        "message": message,
        "parsed_title": state.get("parsed_title"),
        "parsed_seniority": state.get("parsed_seniority"),
        "parsed_model": state.get("parsed_model"),
        "parsed_department": state.get("parsed_department"),
        "parsed_location": state.get("parsed_location"),
        "parsed_employment_type": state.get("parsed_employment_type"),
        "screening_mode": state.get("screening_mode"),
        "salary_min": state.get("salary_min"),
        "salary_max": state.get("salary_max"),
        "salary_range": state.get("salary_range"),
        "parsed_manager_email": state.get("parsed_manager_email"),
        "parsed_manager_name": state.get("parsed_manager_name"),
    }
    _ct = state.get("confirmed_technical_competencies")
    _cb = state.get("confirmed_behavioral_competencies")
    if _ct or _cb:
        data["confirmed_technical_competencies"] = _ct or []
        data["confirmed_behavioral_competencies"] = _cb or []
    if extra:
        data.update(extra)
    return data
