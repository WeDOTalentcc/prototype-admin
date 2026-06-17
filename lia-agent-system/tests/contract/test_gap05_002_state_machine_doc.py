"""
GAP-05-002 Sensor: validates that docs/state-machines.md matches the code.

Parses ALLOWED_STATUS_TRANSITIONS from _shared.py and TERMINAL_STAGES from
candidate_fsm.py, then verifies the Mermaid diagrams in the doc contain
every transition and terminal stage.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SHARED_PY = ROOT / "app" / "api" / "v1" / "job_vacancies" / "_shared.py"
FSM_PY = ROOT / "app" / "services" / "state_machines" / "candidate_fsm.py"
DOC_MD = ROOT / "docs" / "state-machines.md"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_allowed_transitions() -> dict[str, list[str]]:
    """Extract ALLOWED_STATUS_TRANSITIONS dict from _shared.py using AST."""
    source = SHARED_PY.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "ALLOWED_STATUS_TRANSITIONS":
                    return ast.literal_eval(node.value)
    raise AssertionError("ALLOWED_STATUS_TRANSITIONS not found in _shared.py")


def _parse_valid_statuses() -> list[str]:
    """Extract VALID_JOB_STATUSES list from _shared.py using AST."""
    source = SHARED_PY.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "VALID_JOB_STATUSES":
                    return ast.literal_eval(node.value)
    raise AssertionError("VALID_JOB_STATUSES not found in _shared.py")


def _parse_terminal_stages() -> frozenset[str]:
    """Extract TERMINAL_STAGES from candidate_fsm.py using AST.

    Handles both ``Assign`` (``TERMINAL_STAGES = frozenset({...})``) and
    ``AnnAssign`` (``TERMINAL_STAGES: frozenset[str] = frozenset({...})``).
    """
    source = FSM_PY.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        name: str | None = None
        value = None
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "TERMINAL_STAGES":
                    name = target.id
                    value = node.value
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.target.id == "TERMINAL_STAGES":
                name = node.target.id
                value = node.value

        if name and value:
            # frozenset({...}) — Call wrapping a Set literal
            if isinstance(value, ast.Call) and value.args:
                inner = value.args[0]
                if isinstance(inner, ast.Set):
                    return frozenset(
                        elt.value for elt in inner.elts if isinstance(elt, ast.Constant)
                    )
            # Plain set literal (unlikely but defensive)
            if isinstance(value, ast.Set):
                return frozenset(
                    elt.value for elt in value.elts if isinstance(elt, ast.Constant)
                )

    raise AssertionError("TERMINAL_STAGES not found in candidate_fsm.py")


def _read_doc() -> str:
    """Read the state-machines.md doc."""
    return DOC_MD.read_text(encoding="utf-8")


def _extract_mermaid_transitions(doc: str, section_marker: str) -> set[tuple[str, str]]:
    """Extract 'A --> B' transitions from a Mermaid block after a section marker."""
    idx = doc.find(section_marker)
    if idx == -1:
        return set()
    section = doc[idx:]
    match = re.search(r"```mermaid\s*\n(.*?)```", section, re.DOTALL)
    if not match:
        return set()
    mermaid = match.group(1)
    transitions = set()
    for line in mermaid.splitlines():
        m = re.match(r"\s+(\S+)\s+-->\s+(\S+)", line)
        if m:
            src, dst = m.group(1), m.group(2)
            if src != "[*]" and dst != "[*]":
                transitions.add((src, dst))
    return transitions


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestStateMachineDocExists:
    def test_doc_file_exists(self):
        assert DOC_MD.exists(), f"State machine doc missing: {DOC_MD}"

    def test_doc_has_job_vacancy_section(self):
        doc = _read_doc()
        assert "Job Vacancy Status Transitions" in doc

    def test_doc_has_candidate_section(self):
        doc = _read_doc()
        assert "Candidate Stage Transitions" in doc


class TestJobVacancyTransitionsMatchCode:
    """Verify every code transition appears in the Mermaid diagram."""

    def test_all_code_transitions_in_diagram(self):
        transitions = _parse_allowed_transitions()
        doc = _read_doc()
        mermaid_edges = _extract_mermaid_transitions(doc, "Job Vacancy Status Transitions")

        missing = []
        for src, targets in transitions.items():
            for tgt in targets:
                if (src, tgt) not in mermaid_edges:
                    missing.append(f"{src} --> {tgt}")

        assert not missing, (
            f"Transitions in code but missing from Mermaid diagram:\n"
            + "\n".join(f"  - {m}" for m in missing)
            + "\n\nFix: update docs/state-machines.md to match "
            "ALLOWED_STATUS_TRANSITIONS in _shared.py"
        )

    def test_no_extra_transitions_in_diagram(self):
        """Diagram should not invent transitions that don't exist in code."""
        transitions = _parse_allowed_transitions()
        doc = _read_doc()
        mermaid_edges = _extract_mermaid_transitions(doc, "Job Vacancy Status Transitions")

        code_edges = set()
        for src, targets in transitions.items():
            for tgt in targets:
                code_edges.add((src, tgt))

        extra = mermaid_edges - code_edges
        assert not extra, (
            f"Transitions in diagram but NOT in code:\n"
            + "\n".join(f"  - {s} --> {t}" for s, t in extra)
            + "\n\nFix: remove from docs/state-machines.md or add to "
            "ALLOWED_STATUS_TRANSITIONS in _shared.py"
        )

    def test_all_statuses_mentioned_in_doc(self):
        statuses = _parse_valid_statuses()
        doc = _read_doc()
        for status in statuses:
            assert status in doc, (
                f"Status '{status}' from VALID_JOB_STATUSES not found in doc. "
                "Fix: add to docs/state-machines.md"
            )

    def test_terminal_state_is_arquivada(self):
        """Arquivada must have empty transitions list in code."""
        transitions = _parse_allowed_transitions()
        assert transitions.get("Arquivada") == [], (
            "Arquivada should be terminal (empty transitions list)"
        )

    def test_doc_mentions_source_file(self):
        doc = _read_doc()
        assert "_shared.py" in doc, "Doc must reference source file _shared.py"


class TestCandidateFSMDocMatchesCode:
    """Verify the doc mentions all terminal stages from candidate_fsm.py."""

    def test_all_terminal_stages_in_doc(self):
        terminal = _parse_terminal_stages()
        doc = _read_doc()
        missing = [s for s in terminal if s not in doc]
        assert not missing, (
            f"Terminal stages in code but missing from doc:\n"
            + "\n".join(f"  - {s}" for s in missing)
            + "\n\nFix: update docs/state-machines.md to match "
            "TERMINAL_STAGES in candidate_fsm.py"
        )

    def test_doc_mentions_force_escape_hatch(self):
        doc = _read_doc()
        assert "force" in doc.lower(), (
            "Doc must mention force=True escape hatch (candidate FSM allows it)"
        )

    def test_doc_mentions_candidate_fsm_source(self):
        doc = _read_doc()
        assert "candidate_fsm" in doc, "Doc must reference source file candidate_fsm.py"
