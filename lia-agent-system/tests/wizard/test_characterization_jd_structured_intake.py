"""
Characterization tests — _has_structured_intake short-circuit.

Purpose: ensure Fase 8 does NOT port this short-circuit to the orchestrator.

Approach: source-based (reads .py as text), same pattern as
test_wizard_no_silent_fallback.py. Avoids the need to mock inline LLM calls
inside jd_enrichment_node (the LLM logic is not in a separate function).

Two invariants being locked:
  1. The short-circuit EXISTS in the legacy node (nodes/jd_enrichment.py).
  2. The short-circuit does NOT EXIST in the canonical orchestrator
     (orchestrator/wizard_service_tools.py).

NOTE for Fase 8: when nodes/jd_enrichment.py is deleted,
TestStructuredIntakeShortCircuitInLegacyNode must be removed (or it will
fail with FileNotFoundError). The orchestrator guard below is permanent.
"""
from __future__ import annotations
import os


_NODES_JD = os.path.normpath(
    os.path.join(
        os.path.dirname(__file__), "..", "..",
        "app", "domains", "job_creation", "nodes", "jd_enrichment.py",
    )
)
_ORCHESTRATOR_TOOLS = os.path.normpath(
    os.path.join(
        os.path.dirname(__file__), "..", "..",
        "app", "domains", "job_creation", "orchestrator", "wizard_service_tools.py",
    )
)


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


class TestStructuredIntakeShortCircuitInLegacyNode:
    """
    The short-circuit must be present in the LEGACY node.
    If it disappears without Fase 8 being completed, something broke.

    REMOVE this class when nodes/jd_enrichment.py is deleted (Fase 8).
    """

    def test_short_circuit_variable_present_in_legacy_node(self):
        src = _read(_NODES_JD)
        assert "_has_structured_intake" in src, (
            "Short-circuit _has_structured_intake not found in nodes/jd_enrichment.py. "
            "If deliberately removed: confirm Fase 8 migration is complete and the "
            "orchestrator guard below still passes."
        )

    def test_short_circuit_depends_on_correct_state_fields(self):
        """
        The short-circuit must gate on intake_approved AND parsed_title AND
        parsed_seniority — all three. If one is dropped, the gate changes semantics.
        """
        src = _read(_NODES_JD)
        block_start = src.find("_has_structured_intake")
        assert block_start != -1, "Short-circuit variable not found in jd_enrichment.py"

        # Extract ~400 chars around the variable definition
        context = src[block_start: block_start + 400]

        assert "intake_approved" in context, (
            "intake_approved missing from _has_structured_intake condition"
        )
        assert "parsed_title" in context, (
            "parsed_title missing from _has_structured_intake condition"
        )
        assert "parsed_seniority" in context, (
            "parsed_seniority missing from _has_structured_intake condition"
        )


class TestShortCircuitAbsentInCanonicalOrchestrator:
    """
    The short-circuit must NOT exist in the canonical orchestrator.
    This test turns RED if Fase 8 ports the short-circuit — the main protection goal.
    Permanent guard: keep even after Fase 8 completes.
    """

    def test_no_structured_intake_short_circuit_in_orchestrator(self):
        src = _read(_ORCHESTRATOR_TOOLS)
        assert "_has_structured_intake" not in src, (
            "REGRESSION: _has_structured_intake found in wizard_service_tools.py. "
            "Fase 8 must NOT port this short-circuit to the orchestrator. "
            "The orchestrator must always collect JD input from the recruiter."
        )

    def test_orchestrator_does_not_combine_intake_approved_with_parsed_title(self):
        """
        'intake_approved' may exist in the orchestrator for other reasons,
        but must not be combined with 'parsed_title' on the SAME line
        (that pattern marks the short-circuit gate).
        """
        src = _read(_ORCHESTRATOR_TOOLS)
        suspicious = [
            (i + 1, line.strip())
            for i, line in enumerate(src.splitlines())
            if "intake_approved" in line and "parsed_title" in line
        ]
        assert not suspicious, (
            "Found lines in wizard_service_tools.py combining intake_approved "
            f"and parsed_title (short-circuit pattern): {suspicious}"
        )
