"""Regression gate around the MQ-* eval cases (Task #730).

Runs the same logic as ``scripts/ci_meta_question_gate.py`` from inside
pytest so the threshold is enforced on every test run, not only in the
dedicated CI workflow.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from app.orchestrator.meta_question_detector import (
    detect_meta_capability_question,
    reset_meta_question_stats,
)

CASES_PATH = (
    Path(__file__).resolve().parents[2] / "eval" / "eval_cases.yaml"
)

MIN_PRECISION = 0.95
MIN_RECALL = 0.95


def _load_mq_cases() -> list[dict]:
    data = yaml.safe_load(CASES_PATH.read_text(encoding="utf-8"))
    return [c for c in data.get("cases", []) if c.get("category") == "MQ"]


def _expected(case: dict) -> str:
    explicit = case.get("meta_expected")
    if explicit in {"intercept", "passthrough"}:
        return explicit
    return "intercept" if not (case.get("expected_tools") or []) else "passthrough"


@pytest.fixture(autouse=True)
def _reset_stats():
    reset_meta_question_stats()
    yield
    reset_meta_question_stats()


def test_mq_corpus_size_matches_task_730() -> None:
    """Task #730 requires at least 15 new MQ cases on top of MQ-001..009."""
    cases = _load_mq_cases()
    assert len(cases) >= 24, (
        f"expected >=24 MQ-* cases (9 baseline + 15 new), found {len(cases)}"
    )


def test_meta_question_detector_meets_precision_recall_threshold() -> None:
    cases = _load_mq_cases()
    tp = fp = tn = fn = 0
    failures: list[str] = []
    for case in cases:
        prompt = case.get("prompt", "")
        expected = _expected(case)
        actual = "intercept" if detect_meta_capability_question(prompt) else "passthrough"
        if expected == "intercept" and actual == "intercept":
            tp += 1
        elif expected == "passthrough" and actual == "passthrough":
            tn += 1
        elif expected == "intercept" and actual == "passthrough":
            fn += 1
            failures.append(f"FN {case['id']}: {prompt!r}")
        else:
            fp += 1
            failures.append(f"FP {case['id']}: {prompt!r}")

    precision = tp / (tp + fp) if (tp + fp) else 1.0
    recall = tp / (tp + fn) if (tp + fn) else 1.0

    assert precision >= MIN_PRECISION, (
        f"precision {precision:.3f} below threshold {MIN_PRECISION}; "
        f"failures=\n  " + "\n  ".join(failures)
    )
    assert recall >= MIN_RECALL, (
        f"recall {recall:.3f} below threshold {MIN_RECALL}; "
        f"failures=\n  " + "\n  ".join(failures)
    )
