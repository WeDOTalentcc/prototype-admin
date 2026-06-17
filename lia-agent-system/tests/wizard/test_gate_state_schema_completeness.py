"""Sensor (Sprint F.2 root cause fix, 2026-05-20):
   JobCreationState MUST declare every dynamic key written by graph.py gate nodes.

LangGraph filters undeclared keys during state merge (precedent: company_id
Sprint F.3 fix, state.py:105-108). When gate fields are not declared, they
are silently stripped between node invocations. The gate's self-loop
re-entry then sees gate_seen_user_query="" → _is_fresh_turn=True every
iteration → classifier loops forever until GraphRecursionError aborts
the turn (observed in lia-backend log 2026-05-20: 46 self-loops in 60s).

This sensor pins the schema contract. If a future commit removes one of
these fields from JobCreationState without also removing all writers in
graph.py, the test fails with a clear message.
"""
from __future__ import annotations
import re
from pathlib import Path

import pytest

from app.domains.job_creation.state import JobCreationState

GRAPH_PY = Path(__file__).resolve().parent.parent.parent / "app/domains/job_creation/graph.py"


# Keys that nodes set as part of normal gate flow. Each MUST be in JobCreationState.
REQUIRED_GATE_KEYS = {
    "gate_seen_user_query",
    "gate_last_intent",
    "gate_last_confidence",
    "gate_clarify_message",
    "gate_resume_message",
    "fairness_blocked",
    "fairness_block_reason",
    "jd_fairness_blocked",
    "jd_approved",
    "jd_rejection_feedback",
    "wsi_regenerate_pending",
    "wsi_questions_pending_edit",
    "wsi_questions_pending_add",
}


def test_all_required_gate_keys_declared_in_state():
    """Every gate-related dynamic key written by graph.py must be in the
    JobCreationState TypedDict — otherwise LangGraph strips it and the
    gate self-loop never terminates."""
    declared = set(JobCreationState.__annotations__.keys())
    missing = REQUIRED_GATE_KEYS - declared
    assert not missing, (
        f"JobCreationState is missing gate field(s) {sorted(missing)}. "
        "LangGraph filters undeclared keys; without these, gate self-loop "
        "will recurse until GraphRecursionError (Sprint F.2 bug). "
        "Add the field(s) to app/domains/job_creation/state.py. "
        "Precedent: company_id Sprint F.3 fix (state.py:105-108)."
    )


def test_graph_py_writers_do_not_introduce_new_undeclared_gate_keys():
    """Catch new undeclared keys introduced by future commits."""
    src = GRAPH_PY.read_text()
    # Find all "gate_*" / "fairness_*" keys written as dict literals.
    writers = set(re.findall(r'"(gate_[a-z_]+|fairness_[a-z_]+)"', src))
    declared = set(JobCreationState.__annotations__.keys())
    leaked = writers - declared
    # Allow keys that are intentionally consumed only in-flight (none today).
    assert not leaked, (
        f"graph.py writes undeclared key(s) {sorted(leaked)}. "
        "Add to JobCreationState or the value will be dropped by LangGraph. "
        "See Sprint F.2 fix 2026-05-20 in state.py docstring."
    )
