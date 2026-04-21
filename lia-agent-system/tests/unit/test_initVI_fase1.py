"""Onda 2.2 Init VI Fase 1 — Golden set expansion + CI workflow.

Tests:
- eval_cases.yaml now covers FIX 20-32 scenarios
- CI workflow present + valid YAML
- All new cases have required fields
"""
from __future__ import annotations

from pathlib import Path

import yaml


def _root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "eval" / "eval_cases.yaml").exists():
            return parent
    raise RuntimeError("eval/eval_cases.yaml not found")


def test_eval_cases_expanded() -> None:
    """VI.1: golden set must grow beyond original 99 cases."""
    data = yaml.safe_load((_root() / "eval/eval_cases.yaml").read_text(encoding="utf-8"))
    cases = data["cases"]
    assert len(cases) >= 125, (
        f"VI.1: expected >=125 cases after Onda 2.2 expansion (got {len(cases)})"
    )


def test_new_fix_categories_present() -> None:
    """VI.1: FIX 20-32 categories must be represented in golden set."""
    data = yaml.safe_load((_root() / "eval/eval_cases.yaml").read_text(encoding="utf-8"))
    cases = data["cases"]
    categories = {c.get("category") for c in cases}

    required_new = {"FIX20", "FIX21", "FIX22", "FIX23", "FIX26", "FIX28", "FIX31", "G5", "INITIB"}
    missing = required_new - categories
    assert not missing, (
        f"VI.1: golden set missing category coverage for {missing}. "
        f"Present: {sorted(categories)}"
    )


def test_every_case_has_required_fields() -> None:
    """VI.1: each case must have id/category/severity/title/prompt."""
    data = yaml.safe_load((_root() / "eval/eval_cases.yaml").read_text(encoding="utf-8"))
    required = {"id", "category", "severity", "title", "prompt"}
    offences = []
    for case in data["cases"]:
        missing = required - set(case.keys())
        if missing:
            offences.append(f"{case.get('id', '?')}: missing {sorted(missing)}")
    assert not offences, "VI.1: shape errors:\n  " + "\n  ".join(offences[:10])


def test_no_duplicate_ids() -> None:
    """VI.1: all case IDs unique (merge with original 99 didn't collide)."""
    data = yaml.safe_load((_root() / "eval/eval_cases.yaml").read_text(encoding="utf-8"))
    ids = [c["id"] for c in data["cases"]]
    duplicates = {i for i in ids if ids.count(i) > 1}
    assert not duplicates, f"VI.1: duplicate IDs: {duplicates}"


def test_ci_workflow_present() -> None:
    """VI.1: .github/workflows/lia-eval.yml must exist + parse."""
    wf_path = _root().parent / ".github/workflows/lia-eval.yml"
    assert wf_path.exists(), "VI.1: .github/workflows/lia-eval.yml must exist"
    data = yaml.safe_load(wf_path.read_text(encoding="utf-8"))
    # YAML 'on' key is parsed as bool True in some versions due to YAML 1.1
    on_key = data.get("on") or data.get(True)
    assert on_key is not None, "VI.1: workflow must have 'on' triggers"
    assert "jobs" in data, "VI.1: workflow must have jobs"
    assert "eval" in data["jobs"]


def test_ci_workflow_triggers_include_pr_and_schedule() -> None:
    """VI.1: sample-per-PR + nightly schedule strategy."""
    wf_path = _root().parent / ".github/workflows/lia-eval.yml"
    data = yaml.safe_load(wf_path.read_text(encoding="utf-8"))
    on_triggers = data.get("on") or data.get(True) or {}
    assert "pull_request" in on_triggers, "VI.1: must trigger on PR"
    assert "schedule" in on_triggers, "VI.1: must trigger on schedule (nightly)"


def test_ci_workflow_has_cost_caps() -> None:
    """VI.1: workflow must enforce cost caps (EVAL_MAX_CASES_PR / _NIGHTLY)."""
    wf_path = _root().parent / ".github/workflows/lia-eval.yml"
    text = wf_path.read_text(encoding="utf-8")
    assert "EVAL_MAX_CASES_PR" in text
    assert "EVAL_MAX_CASES_NIGHTLY" in text


def test_fix22_coverage_orcamento() -> None:
    """VI.1 spot-check: FIX22 case covering orçamento PT→EN exists."""
    data = yaml.safe_load((_root() / "eval/eval_cases.yaml").read_text(encoding="utf-8"))
    fix22 = [c for c in data["cases"] if c.get("category") == "FIX22"]
    assert any("orçamento" in c.get("prompt", "") for c in fix22), (
        "VI.1: no FIX22 case tests 'orçamento' PT input"
    )
