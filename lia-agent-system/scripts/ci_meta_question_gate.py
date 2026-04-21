"""CI regression gate for the meta-question detector (Task #730).

Loads every ``MQ-*`` case from ``eval/eval_cases.yaml``, runs each prompt
through ``detect_meta_capability_question`` and verifies the outcome
against the case's ``meta_expected`` annotation:

- ``intercept``  -> detector MUST return a ``MetaQuestionResult``
- ``passthrough`` -> detector MUST return ``None``

Cases without an explicit ``meta_expected`` are derived from
``expected_tools`` (empty list -> intercept, otherwise passthrough), which
keeps the original MQ-001..MQ-009 cases working without edits.

The script computes precision & recall with ``intercept`` as the positive
class and exits non-zero if either drops below the configured threshold
(default 0.95). Designed to be run from CI:

    python3 scripts/ci_meta_question_gate.py
    python3 scripts/ci_meta_question_gate.py --min-precision 0.9 --min-recall 0.9

Exit codes:
- 0 — thresholds met
- 1 — threshold violated (regression)
- 2 — script setup failure (yaml/import error)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parent.parent
CASES_PATH = ROOT / "eval" / "eval_cases.yaml"


def _load_mq_cases() -> list[dict]:
    sys.path.insert(0, str(ROOT))
    try:
        import yaml  # noqa: WPS433 — runtime dep
    except ImportError as exc:  # pragma: no cover — env smoke
        print(f"[ci_meta_question_gate] PyYAML required: {exc}", file=sys.stderr)
        raise SystemExit(2)
    data = yaml.safe_load(CASES_PATH.read_text(encoding="utf-8"))
    return [c for c in data.get("cases", []) if c.get("category") == "MQ"]


def _expected_label(case: dict) -> str:
    explicit = case.get("meta_expected")
    if explicit in {"intercept", "passthrough"}:
        return explicit
    tools = case.get("expected_tools") or []
    return "intercept" if not tools else "passthrough"


def _run(min_precision: float, min_recall: float) -> int:
    sys.path.insert(0, str(ROOT))
    try:
        from app.orchestrator.meta_question_detector import (
            detect_meta_capability_question,
        )
    except Exception as exc:  # pragma: no cover — env smoke
        print(f"[ci_meta_question_gate] import failure: {exc}", file=sys.stderr)
        return 2

    cases = _load_mq_cases()
    if not cases:
        print("[ci_meta_question_gate] no MQ-* cases found", file=sys.stderr)
        return 2

    tp = fp = tn = fn = 0
    failures: list[tuple[str, str, str]] = []
    for case in cases:
        prompt = case.get("prompt", "")
        expected = _expected_label(case)
        actual = "intercept" if detect_meta_capability_question(prompt) else "passthrough"
        if expected == "intercept" and actual == "intercept":
            tp += 1
        elif expected == "passthrough" and actual == "passthrough":
            tn += 1
        elif expected == "intercept" and actual == "passthrough":
            fn += 1
            failures.append((case["id"], "false_negative", prompt))
        else:
            fp += 1
            failures.append((case["id"], "false_positive", prompt))

    precision = tp / (tp + fp) if (tp + fp) else 1.0
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    total = tp + fp + tn + fn
    correct = tp + tn

    print(
        f"[ci_meta_question_gate] cases={total} correct={correct} "
        f"precision={precision:.3f} recall={recall:.3f} "
        f"(min precision={min_precision}, min recall={min_recall})"
    )
    for case_id, kind, prompt in failures:
        print(f"  - {case_id} {kind}: {prompt!r}")

    if precision < min_precision or recall < min_recall:
        print("[ci_meta_question_gate] FAIL — threshold violated", file=sys.stderr)
        return 1
    print("[ci_meta_question_gate] OK")
    return 0


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--min-precision", type=float, default=0.95)
    parser.add_argument("--min-recall", type=float, default=0.95)
    args = parser.parse_args(list(argv) if argv is not None else None)
    return _run(args.min_precision, args.min_recall)


if __name__ == "__main__":
    raise SystemExit(main())
