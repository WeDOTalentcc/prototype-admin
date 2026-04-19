"""
Tests for the persona-diagnostic routing audit.

These tests verify two things:

1. The pure audit logic correctly classifies matched / mismatched / unknown
   routings and computes the match rate against the 0.9 threshold.
2. If a real consolidated report exists under `runs/`, the most recent one
   meets the ≥ 90% routing threshold for agent-specific (J.1–J.6) probes.
   When no run is available the check is skipped — we don't want CI to fail
   simply because nobody has produced a capture yet, but the moment a real
   run lands the assertion kicks in.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
RUNNER_DIR = HERE.parent
sys.path.insert(0, str(RUNNER_DIR))

from routing_audit import audit, is_agent_specific, normalise_observed  # noqa: E402

RUNS_DIR = RUNNER_DIR.parent / "runs"


def _probe(probe_id: str, agent: str, observed, *, category: str | None = None) -> dict:
    return {
        "id": probe_id,
        "category": category or f"J.x {agent}",
        "agent": agent,
        "agent_observed": observed,
        "prompt": f"prompt for {probe_id}",
    }


# ── normalise_observed ──────────────────────────────────────────────────────

@pytest.mark.parametrize("raw,expected", [
    ("WSI", "WSI"),
    ("wsi", "WSI"),
    ("wsi_evaluator", "WSI"),
    ("wsi_question_generator", "WSI"),
    ("rubric_evaluation_module", "WSI"),
    ("job_creation_wizard", "JOB"),
    ("sourcing_pipeline_service", "SRC"),
    ("candidate_search", "SRC"),
    ("screening_module", "CVS"),
    ("interviewer", "INT"),
    ("orchestrator", "ORC"),
    ("lia_agent", "LIA"),
    ("", None),
    (None, None),
    ("totally_unknown_thing_42", None),
])
def test_normalise_observed(raw, expected):
    assert normalise_observed(raw) == expected


# ── is_agent_specific ───────────────────────────────────────────────────────

def test_is_agent_specific_includes_J_categories():
    assert is_agent_specific({"agent": "WSI", "category": "J.5 WSI Evaluator"})
    assert is_agent_specific({"agent": "JOB", "category": "J.1 Job Planner"})


def test_is_agent_specific_excludes_LIA_persona_categories():
    assert not is_agent_specific({"agent": "LIA", "category": "A. Identidade"})
    assert not is_agent_specific({"agent": "LIA", "category": "G. Jailbreak"})


def test_is_agent_specific_includes_non_LIA_targets_outside_J():
    # Some persona probes target a specialist via context (e.g. J-prefixed
    # wouldn't apply but agent='WSI' is set) — those still count.
    assert is_agent_specific({"agent": "WSI", "category": "B. Capacidades"})


# ── audit ──────────────────────────────────────────────────────────────────

def test_audit_all_matched_passes_threshold():
    results = [
        _probe("WSI-1", "WSI", "wsi_evaluator"),
        _probe("WSI-2", "WSI", "wsi_question_generator"),
        _probe("JOB-1", "JOB", "job_creation_wizard"),
    ]
    a = audit(results)
    assert a["summary"]["matched"] == 3
    assert a["summary"]["mismatched"] == 0
    assert a["summary"]["match_rate"] == 1.0
    assert a["summary"]["pass"] is True
    assert a["mismatches"] == []


def test_audit_flags_mismatched_probes():
    results = [
        _probe("WSI-1", "WSI", "lia_agent"),
        _probe("WSI-2", "WSI", "wsi_evaluator"),
    ]
    a = audit(results)
    assert a["summary"]["matched"] == 1
    assert a["summary"]["mismatched"] == 1
    assert a["summary"]["match_rate"] == 0.5
    assert a["summary"]["pass"] is False
    assert len(a["mismatches"]) == 1
    m = a["mismatches"][0]
    assert m["id"] == "WSI-1"
    assert m["agent"] == "WSI"
    assert m["agent_observed_code"] == "LIA"
    assert m["kind"] == "mismatched"


def test_audit_unknown_agent_observed_does_not_count_against_match_rate():
    # match_rate is matched / (matched + mismatched); unknowns are tracked
    # separately so we don't punish probes whose backend simply doesn't echo
    # `agent` in the response payload.
    results = [
        _probe("WSI-1", "WSI", "wsi_evaluator"),
        _probe("WSI-2", "WSI", None),
    ]
    a = audit(results)
    assert a["summary"]["matched"] == 1
    assert a["summary"]["mismatched"] == 0
    assert a["summary"]["unknown"] == 1
    assert a["summary"]["match_rate"] == 1.0
    # Unknowns still show up in the mismatches list so they're visible.
    assert any(m["kind"] == "unknown" for m in a["mismatches"])


def test_audit_pass_requires_decided_observations():
    results = [_probe("WSI-1", "WSI", None)]
    a = audit(results)
    # match_rate is 0 because there are no decided observations, and pass
    # must be False — we can't claim routing works with zero evidence.
    assert a["summary"]["pass"] is False


def test_audit_meets_90_percent_threshold():
    # 9 matched + 1 mismatched = 90% exactly.
    results = [_probe(f"WSI-{i}", "WSI", "wsi_evaluator") for i in range(9)]
    results.append(_probe("WSI-X", "WSI", "lia_agent"))
    a = audit(results)
    assert a["summary"]["match_rate"] == 0.9
    assert a["summary"]["pass"] is True


# ── live-run sanity check ───────────────────────────────────────────────────

def _latest_report() -> dict | None:
    if not RUNS_DIR.exists():
        return None
    candidates = sorted(RUNS_DIR.glob("report-*.json"))
    if not candidates:
        # Fall back to a hand-named consolidated file if present.
        candidates = sorted(RUNS_DIR.glob("diagnostico-consolidado-*.json"))
    if not candidates:
        return None
    try:
        data = json.loads(candidates[-1].read_text(encoding="utf-8"))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def test_latest_run_routes_specialist_probes_correctly():
    report = _latest_report()
    if report is None:
        pytest.skip("No persona-diagnostic run available under runs/.")
    # Older reports predate the routing audit — recompute on demand from the
    # `probes` array so we still catch regressions.
    ra = report.get("routing_audit")
    if not ra:
        probes = report.get("probes") or []
        if not probes:
            pytest.skip("Latest report has no per-probe data to audit.")
        ra = audit(probes)
    summary = ra["summary"]
    if summary["matched"] + summary["mismatched"] == 0:
        pytest.skip(
            "Latest run did not capture `agent_observed` for any specialist "
            "probe, so the 90% routing assertion can't be evaluated."
        )
    assert summary["match_rate"] >= 0.9, (
        f"Only {summary['match_rate'] * 100:.1f}% of agent-specific probes "
        f"reached the intended specialist (matched={summary['matched']}, "
        f"mismatched={summary['mismatched']}, unknown={summary['unknown']})."
    )
