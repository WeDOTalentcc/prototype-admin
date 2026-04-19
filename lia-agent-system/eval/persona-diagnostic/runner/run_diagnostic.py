#!/usr/bin/env python3
"""
Persona Diagnostic — single command entry point.

Loads probes.yaml, runs them against a live LIA backend, judges every reply
with the rubric (LLM-as-judge), and writes a consolidated JSON + Markdown
report under runs/. Exits non-zero if any critical failure is detected.

Usage:
    python lia-agent-system/eval/persona-diagnostic/runner/run_diagnostic.py
    python ... --categories "A. Identidade,D. Fairness"
    python ... --ids ID-001,ID-002
    python ... --skip-judge        # capture only (no rubric scoring)
    python ... --no-baseline       # don't diff against any prior report
    python ... --baseline runs/foo.json
    python ... --url http://localhost:8001
    python ... --run-id my-run-2026-04-19
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from probe_loader import load_probes  # noqa: E402
from runner import DEFAULT_URL, run_probes, save_capture, make_recruiter_token  # noqa: E402
from judge import judge_all  # noqa: E402
from report import build_report, write_report, load_baseline_report  # noqa: E402

PERSONA_DIR = HERE.parent
RUNS_DIR = PERSONA_DIR / "runs"
DEFAULT_BASELINE = RUNS_DIR / "diagnostico-consolidado-2026-04-19.json"


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def main() -> int:
    p = argparse.ArgumentParser(description="LIA Persona Diagnostic — automated")
    p.add_argument("--url", default=DEFAULT_URL, help="LIA backend base URL")
    p.add_argument("--ids", help="Comma-separated probe IDs")
    p.add_argument("--categories", help="Comma-separated categories or prefixes (e.g. 'A,D')")
    p.add_argument("--agents", help="Comma-separated agent codes (LIA,JOB,SRC,…)")
    p.add_argument("--run-id", default=f"run-{_ts()}", help="Run identifier (used in filenames)")
    p.add_argument("--skip-judge", action="store_true", help="Skip the LLM-as-judge stage")
    p.add_argument("--baseline", help="Path to a prior consolidated report (.json) to diff against")
    p.add_argument("--no-baseline", action="store_true", help="Skip baseline diff entirely")
    p.add_argument("--timeout", type=float, default=60.0)
    p.add_argument("--allow-critical", action="store_true",
                   help="Always exit 0 even when critical failures are detected.")
    args = p.parse_args()

    only_ids = [x.strip() for x in args.ids.split(",")] if args.ids else None
    only_cats = [x.strip() for x in args.categories.split(",")] if args.categories else None
    only_agents = [x.strip() for x in args.agents.split(",")] if args.agents else None

    meta, probes = load_probes(only_ids, only_cats, only_agents)
    if not probes:
        print("ERROR: no probes match the given filters.", file=sys.stderr)
        return 2

    print("=" * 72)
    print(f" LIA Persona Diagnostic — {args.run_id}")
    print(f" Backend: {args.url}")
    print(f" Probes : {len(probes)} (of {meta.get('total_probes', '?')})")
    print(f" Judge  : {'SKIPPED' if args.skip_judge else 'enabled (Claude Haiku, rubric)'}")
    print("=" * 72)

    # 1) auth + capture
    try:
        token = make_recruiter_token()
    except Exception as exc:
        print(f"ERROR getting recruiter token: {exc}", file=sys.stderr)
        return 3

    capture_path = RUNS_DIR / f"capture-{args.run_id}.json"
    capture_meta = {
        "run_id": args.run_id,
        "url": args.url,
        "started_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "filters": {"ids": only_ids, "categories": only_cats, "agents": only_agents},
    }

    def _checkpoint(_entry, all_results):
        save_capture(all_results, capture_meta, capture_path)

    print("\n[1/3] Capturing responses from live LIA …")
    results = asyncio.run(run_probes(
        probes, base_url=args.url, token=token, timeout=args.timeout, on_result=_checkpoint,
    ))
    save_capture(results, capture_meta, capture_path)
    print(f"  → capture saved: {capture_path}")

    if args.skip_judge:
        # Stub judgment so the report still renders
        for r in results:
            r["judgment"] = {
                "score": 0,
                "critical_failure": False,
                "critical_trigger": None,
                "critical_trigger_name": None,
                "violated_anti_patterns": [],
                "reasoning": "Judge skipped (--skip-judge).",
                "language_detected": "unknown",
                "judge_model": "skipped",
            }
        judged = results
    else:
        if not os.getenv("ANTHROPIC_API_KEY"):
            print(
                "ERROR: ANTHROPIC_API_KEY is not set. The LLM-as-judge cannot run, "
                "and silently scoring every probe 0 would hide the failure. "
                "Set ANTHROPIC_API_KEY, or pass --skip-judge if you only want to "
                "capture responses.",
                file=sys.stderr,
            )
            return 4
        try:
            import anthropic  # type: ignore  # noqa: F401
        except ImportError:
            print(
                "ERROR: the `anthropic` package is not installed in this env. "
                "Install it or pass --skip-judge.",
                file=sys.stderr,
            )
            return 4
        print("\n[2/3] Judging responses against rubric …")
        judged = judge_all(results)

    # 3) report + baseline diff
    print("\n[3/3] Building consolidated report …")
    baseline = None
    if not args.no_baseline:
        baseline_path = Path(args.baseline) if args.baseline else DEFAULT_BASELINE
        baseline = load_baseline_report(baseline_path)
        if baseline is None and args.baseline:
            print(f"  ⚠ Baseline at {baseline_path} is not a consolidated report — skipping diff.")

    report = build_report(judged, baseline=baseline)
    json_out = RUNS_DIR / f"report-{args.run_id}.json"
    md_out = RUNS_DIR / f"report-{args.run_id}.md"
    write_report(report, json_out, md_out)

    s = report["summary"]
    print()
    print(f"  Overall avg     : {s['overall_avg_score']} / 3")
    print(f"  Weighted avg    : {s['weighted_avg_score']} / 3")
    print(f"  Critical fails  : {s['critical_failures_count']}")
    print(f"  Categories pass : {s['categories_passing']} / {s['categories_total']}")
    print(f"  Release blocked : {'YES' if s['release_blocked'] else 'no'}")
    print()
    print(f"  JSON report : {json_out}")
    print(f"  MD   report : {md_out}")
    print()

    if s["critical_failures_count"] > 0 and not args.allow_critical:
        print(f"❌ {s['critical_failures_count']} critical failure(s) — exiting non-zero.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
