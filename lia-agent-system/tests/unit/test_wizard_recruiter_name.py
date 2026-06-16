"""Tests for wizard recruiter name injection — Bug 1 fix.

Validates:
1. _build_wizard_state_summary includes "nome do recrutador" in field_map.
2. _build_system_prompt injects recruiter name block when name is present.
3. _build_system_prompt omits the block when name is absent.
"""
import pytest
from unittest.mock import patch


# ---------------------------------------------------------------------------
# Fix 1 — utils._build_wizard_state_summary
# ---------------------------------------------------------------------------

def test_state_summary_includes_recruiter_name():
    """Recruiter name appears in filled-fields output."""
    from app.domains.job_creation.internal.utils import _build_wizard_state_summary

    result = _build_wizard_state_summary({
        "parsed_recruiter_name": "Paulo Moraes",
        "parsed_title": "Engenheiro de Software",
    })
    assert "Paulo Moraes" in result, (
        f"Expected Paulo Moraes in state summary, got:\n{result}"
    )


def test_state_summary_missing_recruiter_name():
    """When recruiter name is absent it appears in the faltantes list."""
    from app.domains.job_creation.internal.utils import _build_wizard_state_summary

    result = _build_wizard_state_summary({})
    # The key should be reported as missing
    assert "nome do recrutador" in result, (
        f"Expected nome do recrutador in missing fields, got:\n{result}"
    )


# ---------------------------------------------------------------------------
# Fix 2 — wizard_orchestrator._build_system_prompt
# ---------------------------------------------------------------------------

def test_system_prompt_includes_recruiter_block():
    """System prompt contains recruiter identity block when name is set."""
    from app.domains.job_creation.orchestrator.wizard_orchestrator import WizardOrchestrator

    orch = WizardOrchestrator.__new__(WizardOrchestrator)
    # Minimal state with recruiter name
    state = {
        "parsed_recruiter_name": "Paulo Moraes",
        "current_stage": "intake",
    }
    with patch(
        "app.domains.job_creation.internal.utils._build_wizard_state_summary",
        return_value="(mock ficha)",
    ):
        prompt = orch._build_system_prompt(state)

    assert "Paulo Moraes" in prompt, (
        f"Expected recruiter name in system prompt, got:\n{prompt[:400]}"
    )
    assert "Recrutador desta sessão" in prompt, (
        f"Expected Recrutador desta sessão section in system prompt, got:\n{prompt[:400]}"
    )


def test_system_prompt_no_recruiter_block_when_name_absent():
    """System prompt does NOT include recruiter block when name is missing."""
    from app.domains.job_creation.orchestrator.wizard_orchestrator import WizardOrchestrator

    orch = WizardOrchestrator.__new__(WizardOrchestrator)
    state = {"current_stage": "intake"}
    with patch(
        "app.domains.job_creation.internal.utils._build_wizard_state_summary",
        return_value="(mock ficha)",
    ):
        prompt = orch._build_system_prompt(state)

    assert "Recrutador desta sessão" not in prompt, (
        "Recruiter block should be absent when parsed_recruiter_name is not set"
    )
